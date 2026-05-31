import os
import sys
import time
import argparse
from pathlib import Path

import numpy as np
import cv2
from scipy.ndimage import center_of_mass

# Try to import PyTorch. If it fails, print a friendly error message for the GPU machine.
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import Dataset, DataLoader
except ImportError:
    print("CRITICAL ERROR: PyTorch is not installed.")
    print("Please install PyTorch on the GPU machine before running this script.")
    print("Command: pip install torch torchvision torchaudio")
    sys.exit(1)

# =============================================================================
# 1. Configuration & Paths
# =============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MASK_DIR = PROJECT_ROOT / "data" / "annotated"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "phase2_model"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_SIZE = (512, 512)
BATCH_SIZE = 4
EPOCHS = 50
LEARNING_RATE = 1e-4

# =============================================================================
# 2. Data Preparation: Density Map Generation
# =============================================================================
def generate_density_map(mask, target_size=(512, 512), sigma=10):
    """
    Converts an instance segmentation mask into a 2D Gaussian density map.
    The sum of the output density map equals the total cell count.
    """
    # 1. Extract centroids of all unique cell labels
    labels = np.unique(mask)
    centroids = []
    for l in labels:
        if l == 0: continue  # Skip background
        cy, cx = center_of_mass(mask == l)
        centroids.append((cx, cy))
        
    # 2. Scale centroids to target training size (512x512)
    h_orig, w_orig = mask.shape
    scale_x = target_size[0] / w_orig
    scale_y = target_size[1] / h_orig
    
    scaled_centroids = [(int(cx * scale_x), int(cy * scale_y)) for cx, cy in centroids]
    
    # 3. Generate Gaussian blobs at each centroid
    density = np.zeros((target_size[1], target_size[0]), dtype=np.float32)
    
    # Pre-compute a small gaussian grid to speed up map generation
    # Instead of computing over the whole image, we just add the blob around the point
    blob_size = int(sigma * 3)
    x = np.arange(-blob_size, blob_size + 1, 1, float)
    y = np.arange(-blob_size, blob_size + 1, 1, float)[:, np.newaxis]
    g_blob = np.exp(-(x**2 + y**2) / (2 * sigma**2))
    g_blob = g_blob / np.sum(g_blob) # Normalize so the sum is exactly 1.0 (1 cell)
    
    for cx, cy in scaled_centroids:
        # Define bounds for placing the blob
        x_min, x_max = max(0, cx - blob_size), min(target_size[0], cx + blob_size + 1)
        y_min, y_max = max(0, cy - blob_size), min(target_size[1], cy + blob_size + 1)
        
        # Define bounds in the gaussian blob array
        g_x_min = blob_size - (cx - x_min)
        g_x_max = blob_size + (x_max - cx)
        g_y_min = blob_size - (cy - y_min)
        g_y_max = blob_size + (y_max - cy)
        
        if x_min < x_max and y_min < y_max:
            density[y_min:y_max, x_min:x_max] += g_blob[g_y_min:g_y_max, g_x_min:g_x_max]
            
    return density

class CellDensityDataset(Dataset):
    def __init__(self, raw_dir, mask_dir, target_size=(512, 512)):
        self.raw_dir = Path(raw_dir)
        self.mask_dir = Path(mask_dir)
        self.target_size = target_size
        
        print("Scanning for image-mask pairs...")
        self.samples = []
        for raw_file in sorted(self.raw_dir.glob("*.png")):
            mask_file = self.mask_dir / f"{raw_file.stem}_mask.npy"
            if mask_file.exists():
                self.samples.append((raw_file, mask_file))
                
        print(f"Found {len(self.samples)} fully annotated training pairs.")
                
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        raw_path, mask_path = self.samples[idx]
        
        # --- Image Preprocessing ---
        img_bgr = cv2.imread(str(raw_path))
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # CLAHE exactly like Phase 1
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Resize and normalize
        img_resized = cv2.resize(enhanced, self.target_size)
        img_tensor = torch.from_numpy(img_resized).float().unsqueeze(0) / 255.0
        
        # --- Target Map Generation ---
        mask = np.load(str(mask_path))
        density_map = generate_density_map(mask, target_size=self.target_size)
        
        # Multiply by a scaling factor to make loss gradients healthier (e.g. x100)
        # We will divide by 100 during inference
        density_tensor = torch.from_numpy(density_map).float().unsqueeze(0) * 100.0
        
        # Ground truth exact count
        gt_count = len(np.unique(mask)) - 1
        
        return img_tensor, density_tensor, gt_count, raw_path.name

# =============================================================================
# 3. Model Architecture (Lightweight CSRNet-style CNN)
# =============================================================================
class DensityCNN(nn.Module):
    def __init__(self):
        super(DensityCNN, self).__init__()
        
        # Frontend: Feature Extraction
        self.frontend = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1), nn.ReLU(inplace=True),
            nn.MaxPool2d(2), # 256x256
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1), nn.ReLU(inplace=True),
            nn.MaxPool2d(2), # 128x128
            nn.Conv2d(128, 256, kernel_size=3, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1), nn.ReLU(inplace=True),
            nn.MaxPool2d(2)  # 64x64
        )
        
        # Backend: Dilated Convolutions to build density map while keeping spatial resolution
        self.backend = nn.Sequential(
            nn.Conv2d(256, 256, kernel_size=3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(256, 128, kernel_size=3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(128, 64, kernel_size=3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(64, 1, kernel_size=1)
        )

    def forward(self, x):
        x = self.frontend(x)
        x = self.backend(x)
        # Upsample back to 512x512 to match the generated ground-truth density map
        x = F.interpolate(x, scale_factor=8, mode='bilinear', align_corners=False)
        return x

# =============================================================================
# 4. Master Training Loop
# =============================================================================
def main():
    print("==================================================")
    print("Cell Counter — Phase 2 GPU Master Script")
    print("==================================================")
    
    # 1. Device Setup
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"[OK] GPU Detected: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device('cpu')
        print("[WARNING] No GPU detected! Training on CPU will be extremely slow.")
        
    # 2. Data Loading
    dataset = CellDensityDataset(RAW_DIR, MASK_DIR, TARGET_SIZE)
    if len(dataset) == 0:
        print("ERROR: No annotated data found. Make sure you run this script inside the project root.")
        return
        
    # Standard 80/20 train/val split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    print(f"Data split: {len(train_dataset)} Train | {len(val_dataset)} Validation")
    
    # 3. Model & Optimizer
    model = DensityCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()
    
    best_val_mae = float('inf')
    best_model_path = OUTPUT_DIR / "best_density_cnn.pth"
    
    print(f"\nStarting training for {EPOCHS} epochs...")
    print("--------------------------------------------------")
    
    for epoch in range(1, EPOCHS + 1):
        start_time = time.time()
        
        # --- TRAIN ---
        model.train()
        train_loss = 0.0
        
        for imgs, density_maps, _, _ in train_loader:
            imgs = imgs.to(device)
            density_maps = density_maps.to(device)
            
            optimizer.zero_grad()
            preds = model(imgs)
            loss = criterion(preds, density_maps)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * imgs.size(0)
            
        train_loss /= len(train_loader.dataset)
        
        # --- VALIDATE ---
        model.eval()
        val_loss = 0.0
        mae = 0.0
        
        with torch.no_grad():
            for imgs, density_maps, gt_counts, _ in val_loader:
                imgs = imgs.to(device)
                density_maps = density_maps.to(device)
                
                preds = model(imgs)
                loss = criterion(preds, density_maps)
                val_loss += loss.item() * imgs.size(0)
                
                # Calculate counting MAE
                for i in range(imgs.size(0)):
                    # Divide by 100 because we multiplied GT by 100 during loading
                    pred_count = torch.sum(preds[i]).item() / 100.0
                    mae += abs(pred_count - float(gt_counts[i]))
                    
        val_loss /= len(val_loader.dataset)
        mae /= len(val_loader.dataset)
        
        epoch_time = time.time() - start_time
        
        print(f"Epoch {epoch:03d}/{EPOCHS} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Count MAE: {mae:.2f} cells | Time: {epoch_time:.1f}s")
        
        # Save best model based on MAE
        if mae < best_val_mae:
            best_val_mae = mae
            torch.save(model.state_dict(), best_model_path)
            print(f"   [+] New best model saved (MAE: {mae:.2f})")
            
    print("--------------------------------------------------")
    print(f"Training complete! Best model saved to: {best_model_path}")
    print(f"Best Validation MAE achieved: {best_val_mae:.2f} cells per image")
    
if __name__ == "__main__":
    main()
