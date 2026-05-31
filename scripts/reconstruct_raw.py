"""
Cell Counter — Raw Image Reconstruction
======================================================
Reconstructs the original raw images by removing the blue contours
from *_GT_check.png using OpenCV inpainting.
"""

import cv2
import numpy as np
from pathlib import Path

def main():
    annotated_dir = Path("data/annotated")
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    gt_files = sorted(list(annotated_dir.glob("*_GT_check.png")))
    print(f"Found {len(gt_files)} GT check images to process.")

    reconstructed_count = 0

    for gt_path in gt_files:
        # Reconstructed raw filename mapping
        # E.g. 'csm1-12 (1)_GT_check.png' -> 'csm1-12 (1).png'
        raw_name = gt_path.name.replace("_GT_check.png", ".png")
        dest_path = raw_dir / raw_name

        # If it's already there (and we have the original raw), we can skip to preserve original
        if dest_path.exists() and gt_path.stem == "csm1-13 (24)_GT_check":
            print(f"Skipping {raw_name} (original raw file already exists)")
            continue

        # Load GT Check image
        img = cv2.imread(str(gt_path))
        if img is None:
            print(f"Error reading {gt_path.name}")
            continue

        # 1) Detect blue contour pixels
        # OpenCV reads BGR. Blue is index 0.
        blue_mask = (img[:, :, 0] > 200) & (img[:, :, 1] < 50) & (img[:, :, 2] < 50)
        mask_u8 = blue_mask.astype(np.uint8) * 255

        # 2) Dilate mask slightly to clean up border anti-aliasing
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated_mask = cv2.dilate(mask_u8, kernel)

        # 3) Inpaint the blue regions
        inpainted = cv2.inpaint(img, dilated_mask, 3, cv2.INPAINT_TELEA)

        # Write to outputs
        cv2.imwrite(str(dest_path), inpainted)
        reconstructed_count += 1
        if reconstructed_count % 10 == 0 or reconstructed_count == len(gt_files):
            print(f"Reconstructed {reconstructed_count}/{len(gt_files)} images...")

    print(f"Finished. Reconstructed {reconstructed_count} raw images inside {raw_dir}")

if __name__ == "__main__":
    main()
