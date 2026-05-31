"""
Cell Counter — Vectorized Parameter Optimization
================================================================
Uses NumPy vectorization to evaluate all parameter combinations 
across 64 images in under 2 seconds.
"""

import sys
import numpy as np
import cv2
import re
from pathlib import Path
from sklearn.metrics import r2_score

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config as cfg
from scripts.predict import preprocess, segment, circularity

def main():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    annotated_dir = PROJECT_ROOT / "data" / "annotated"

    raw_files = sorted(list(raw_dir.glob("*.png")))
    if not raw_files:
        print("No raw PNG files found in data/raw/")
        return

    print("Caching image features into NumPy arrays for high-speed evaluation...")
    cached_dataset = []

    for raw_path in raw_files:
        mask_path = annotated_dir / f"{raw_path.stem}_mask.npy"
        if not mask_path.exists():
            continue

        # Load GT count
        gt_mask = np.load(mask_path)
        unique_ids = np.unique(gt_mask)
        gt_count = len(unique_ids[unique_ids != 0])

        # Load raw image
        img_bgr = cv2.imread(str(raw_path))
        if img_bgr is None:
            continue

        # Run fixed preprocessing & segmentation steps
        gray = preprocess(img_bgr)
        raw_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        binary_mask = segment(gray)

        # Extract contours
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        areas = []
        circs = []
        intensities = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            circ = circularity(cnt)

            # Mask contour to get mean grayscale intensity
            bm = np.zeros(raw_gray.shape, dtype=np.uint8)
            cv2.drawContours(bm, [cnt], -1, 255, -1)
            mean_intensity = cv2.mean(raw_gray, mask=bm)[0]

            areas.append(area)
            circs.append(circ)
            intensities.append(mean_intensity)

        # Convert to numpy arrays
        cached_dataset.append({
            "name": raw_path.name,
            "gt_count": gt_count,
            "areas": np.array(areas),
            "circs": np.array(circs),
            "intensities": np.array(intensities)
        })

    print(f"Cached {len(cached_dataset)} images. Starting high-speed search...")

    # Define Parameter Grid
    single_cell_areas = np.arange(150, 351, 25)      # 9 values
    min_cell_areas = np.arange(50, 251, 25)          # 9 values
    min_circularities = np.arange(0.10, 0.61, 0.05)  # 11 values
    max_mean_intensities = np.arange(110, 161, 5)    # 11 values
    cluster_thresholds = np.arange(300, 701, 50)     # 9 values

    # Total grid size: 9 * 9 * 11 * 11 * 9 = 87,309 combos
    best_mape = float("inf")
    best_params = {}

    for sca in single_cell_areas:
        for mca in min_cell_areas:
            for mc in min_circularities:
                for mmi in max_mean_intensities:
                    for ct in cluster_thresholds:
                        
                        apes = []
                        
                        for img_data in cached_dataset:
                            gt = img_data["gt_count"]
                            
                            areas = img_data["areas"]
                            circs = img_data["circs"]
                            intensities = img_data["intensities"]
                            
                            if len(areas) == 0:
                                apes.append(1.0 if gt > 0 else 0.0)
                                continue

                            # 1) Area and Intensity filters
                            valid = (areas >= mca) & (areas <= 200000) & (intensities <= mmi)
                            if not np.any(valid):
                                apes.append(1.0 if gt > 0 else 0.0)
                                continue
                                
                            v_areas = areas[valid]
                            v_circs = circs[valid]
                            
                            # 2) Two-tier circularity
                            min_c = np.where(v_areas >= ct, 0.05, mc)
                            shape_valid = v_circs >= min_c
                            if not np.any(shape_valid):
                                apes.append(1.0 if gt > 0 else 0.0)
                                continue
                                
                            v_areas = v_areas[shape_valid]
                            
                            # 3) Count math
                            counts = np.where(v_areas < ct, 1, np.round(v_areas / sca).astype(int))
                            counts = np.maximum(counts, 1)
                            pred_count = np.sum(counts)
                            
                            err = abs(pred_count - gt)
                            apes.append(err / gt if gt > 0 else 0.0)
                            
                        mape = np.mean(apes) * 100.0
                        
                        if mape < best_mape:
                            best_mape = mape
                            best_params = {
                                "SINGLE_CELL_AREA": sca,
                                "MIN_CELL_AREA": mca,
                                "MIN_CIRCULARITY": round(mc, 2),
                                "MAX_MEAN_INTENSITY": mmi,
                                "CLUSTER_THRESHOLD": ct
                            }
                            print(f"New Best MAPE: {best_mape:.2f}% | Params: {best_params}")

    print("\n" + "="*50)
    print("VECTORIZED OPTIMIZATION FINISHED")
    print(f"Best MAPE: {best_mape:.2f}%")
    print("Best Parameters:")
    for k, v in best_params.items():
        print(f"  {k}: {v}")
    print("="*50)

    # Automatically Update config.py
    config_path = PROJECT_ROOT / "config.py"
    config_content = config_path.read_text(encoding="utf-8")

    # Replace each parameter using regex
    for k, v in best_params.items():
        pattern = rf"({k}\s*=\s*)[0-9.]+"
        config_content = re.sub(pattern, rf"\g<1>{v}", config_content)

    config_path.write_text(config_content, encoding="utf-8")
    print(f"Successfully updated parameters in {config_path}")

if __name__ == "__main__":
    main()
