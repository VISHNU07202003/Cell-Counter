"""
Cell Counter — Prediction Pipeline
====================================================
Phase 1: Classical CV (OpenCV) — no training required.

Usage:
    python scripts/predict.py path/to/image.png
    python scripts/predict.py path/to/folder/       # batch mode
"""

import sys
import csv
import math
import argparse
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np

# Add project root to path so config is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg


# ── Preprocessing ──────────────────────────────────────────────────────
def preprocess(img_bgr):
    """Raw BGR → preprocessed grayscale ready for thresholding."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=cfg.CLAHE_CLIP_LIMIT,
        tileGridSize=cfg.CLAHE_TILE_SIZE,
    )
    enhanced = clahe.apply(gray)

    # Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(enhanced, cfg.BLUR_KERNEL, 0)

    return blurred


# ── Segmentation ──────────────────────────────────────────────────────
def segment(gray):
    """Grayscale → binary mask via Otsu threshold + morphological cleanup."""
    # Otsu auto-threshold (cells dark, background light → invert)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Morphological open to remove tiny specks
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (cfg.MORPH_KERNEL_SIZE, cfg.MORPH_KERNEL_SIZE),
    )
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=cfg.MORPH_ITERATIONS)

    # Morphological close to fill small holes inside cells
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=1)

    return cleaned


# ── Contour analysis ──────────────────────────────────────────────────
def circularity(contour):
    """4π·area / perimeter² — perfect circle = 1.0."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0.0
    return (4.0 * math.pi * area) / (perimeter * perimeter)


def count_cells(mask, gray):
    """
    Analyze contours in binary mask -> estimated cell count.

    Filters:
      1. Area range (MIN_CELL_AREA .. MAX_CELL_AREA)
      2. Two-tier circularity (stricter for small blobs, relaxed for clusters)
      3. Intensity — real cells are DARK; debris is lighter

    Args:
        mask : binary mask from segmentation
        gray : raw grayscale image (for intensity measurement)

    Returns:
        total_count : int          -- estimated total cells
        details     : list[dict]   -- per-blob breakdown
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    details = []
    total_count = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        circ = circularity(cnt)

        # ── Reject: too small or too large ──
        if area < cfg.MIN_CELL_AREA or area > cfg.MAX_CELL_AREA:
            details.append({
                "area": area, "circularity": round(circ, 3),
                "status": "rejected_area", "cells": 0,
            })
            continue

        # ── Two-tier circularity filter ──
        min_circ = (cfg.CLUSTER_MIN_CIRCULARITY
                    if area >= cfg.CLUSTER_THRESHOLD
                    else cfg.MIN_CIRCULARITY)

        if circ < min_circ:
            details.append({
                "area": area, "circularity": round(circ, 3),
                "status": "rejected_shape", "cells": 0,
            })
            continue

        # ── Intensity filter: cells are DARK, debris is LIGHT ──
        blob_mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(blob_mask, [cnt], -1, 255, -1)
        mean_intensity = cv2.mean(gray, mask=blob_mask)[0]

        if mean_intensity > cfg.MAX_MEAN_INTENSITY:
            details.append({
                "area": area, "circularity": round(circ, 3),
                "mean_intensity": round(mean_intensity, 1),
                "status": "rejected_light", "cells": 0,
            })
            continue

        # ── Accept: single cell or cluster ──
        if area < cfg.CLUSTER_THRESHOLD:
            cells_in_blob = 1
            status = "single_cell"
        else:
            cells_in_blob = max(1, round(area / cfg.SINGLE_CELL_AREA))
            status = "cluster"

        total_count += cells_in_blob
        details.append({
            "area": area, "circularity": round(circ, 3),
            "mean_intensity": round(mean_intensity, 1),
            "status": status, "cells": cells_in_blob,
        })

    return total_count, details


# ── Annotated visualization ───────────────────────────────────────────
def annotate_image(img_bgr, mask, details):
    """Draw contours + cell counts on a copy of the original image."""
    annotated = img_bgr.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Match contours to details by index
    detail_idx = 0
    for cnt in contours:
        if detail_idx >= len(details):
            break

        d = details[detail_idx]
        detail_idx += 1

        if d["status"] == "rejected_area" or d["status"] == "rejected_shape":
            color = cfg.CONTOUR_COLOR_REJECT
        elif d["status"] == "cluster":
            color = cfg.CONTOUR_COLOR_CLUSTER
        else:
            color = cfg.CONTOUR_COLOR_CELL

        cv2.drawContours(annotated, [cnt], -1, color, cfg.CONTOUR_THICKNESS)

        # Label clusters with estimated count
        if d["cells"] > 1:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(
                    annotated, str(d["cells"]),
                    (cx - 5, cy + 3),
                    cv2.FONT_HERSHEY_SIMPLEX, cfg.FONT_SCALE,
                    (255, 255, 255), 1, cv2.LINE_AA,
                )

    return annotated


# ── Fluorescent pipeline ──────────────────────────────────────────────
def predict_fluorescence(image_path, save_annotated=True):
    """
    Highly efficient pipeline for fluorescent images (green on black).
    """
    image_path = Path(image_path)
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    original_h, original_w = img_bgr.shape[:2]

    # Extract green channel
    green = img_bgr[:, :, 1]

    # Global Otsu threshold
    _, binary = cv2.threshold(green, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological opening to remove tiny noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    details = []
    total_count = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 10:  # Ignore very tiny noise
            continue

        if area < cfg.CLUSTER_THRESHOLD:
            cells_in_blob = 1
            status = "single_cell"
        else:
            cells_in_blob = max(1, round(area / cfg.SINGLE_CELL_AREA))
            status = "cluster"

        total_count += cells_in_blob
        details.append({
            "area": area, "circularity": round(circularity(cnt), 3),
            "mean_intensity": 0, "status": status, "cells": cells_in_blob,
        })

    result = {
        "filename": image_path.name,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "estimated_count": total_count,
        "original_size": f"{original_w}x{original_h}",
        "singles": sum(1 for d in details if d["status"] == "single_cell"),
        "clusters": sum(1 for d in details if d["status"] == "cluster"),
        "rejected": 0,
        "details": details,
        "image_type": "fluorescence",
    }

    if save_annotated:
        annotated = annotate_image(img_bgr, mask, details)

        display_w = 512
        scale = display_w / original_w
        display_h = int(original_h * scale)
        disp_orig = cv2.resize(img_bgr, (display_w, display_h))
        disp_ann = cv2.resize(annotated, (display_w, display_h))
        disp_mask = cv2.resize(mask, (display_w, display_h))
        disp_mask_bgr = cv2.cvtColor(disp_mask, cv2.COLOR_GRAY2BGR)
        debug = np.hstack([disp_orig, disp_ann, disp_mask_bgr])

        cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = cfg.OUTPUT_DIR / f"annotated_{image_path.stem}.png"
        debug_path = cfg.OUTPUT_DIR / f"debug_{image_path.stem}.png"
        cv2.imwrite(str(out_path), annotated)
        cv2.imwrite(str(debug_path), debug)
        result["annotated_path"] = str(out_path)
        result["debug_path"] = str(debug_path)

    return result


# ── Full pipeline ─────────────────────────────────────────────────────
def predict_brightfield(image_path, save_annotated=True):
    """
    Run the full estimation pipeline on a single image.

    NOTE: Processing at original resolution because Cell_Area.xlsx
    thresholds (470 px², 279 px² min) were measured at native 1536×1024.

    Returns:
        dict with keys: filename, timestamp, estimated_count, details
    """
    image_path = Path(image_path)
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    original_h, original_w = img_bgr.shape[:2]

    # 1) Preprocess at ORIGINAL resolution (thresholds calibrated here)
    gray = preprocess(img_bgr)

    # Raw grayscale (no CLAHE) for intensity measurement
    raw_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 2) Segment
    mask = segment(gray)

    # 3) Count (pass raw_gray for intensity filter)
    estimated_count, details = count_cells(mask, raw_gray)

    # 4) Build result
    result = {
        "filename": image_path.name,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "estimated_count": estimated_count,
        "original_size": f"{original_w}x{original_h}",
        "singles": sum(1 for d in details if d["status"] == "single_cell"),
        "clusters": sum(1 for d in details if d["status"] == "cluster"),
        "rejected": sum(1 for d in details if "rejected" in d["status"]),
        "details": details,
        "image_type": "brightfield",
    }

    if save_annotated:
        annotated = annotate_image(img_bgr, mask, details)

        # Create a debug view: resize all to a reasonable display width
        display_w = 512
        scale = display_w / original_w
        display_h = int(original_h * scale)
        disp_orig = cv2.resize(img_bgr, (display_w, display_h))
        disp_ann = cv2.resize(annotated, (display_w, display_h))
        disp_mask = cv2.resize(mask, (display_w, display_h))
        disp_mask_bgr = cv2.cvtColor(disp_mask, cv2.COLOR_GRAY2BGR)
        debug = np.hstack([disp_orig, disp_ann, disp_mask_bgr])

        cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = cfg.OUTPUT_DIR / f"annotated_{image_path.stem}.png"
        debug_path = cfg.OUTPUT_DIR / f"debug_{image_path.stem}.png"
        cv2.imwrite(str(out_path), annotated)
        cv2.imwrite(str(debug_path), debug)
        result["annotated_path"] = str(out_path)
        result["debug_path"] = str(debug_path)

    return result

def predict(image_path, save_annotated=True):
    """Router: routes to brightfield or fluorescence based on filename."""
    image_path = Path(image_path)
    if "fluores" in image_path.name.lower():
        return predict_fluorescence(image_path, save_annotated)
    else:
        return predict_brightfield(image_path, save_annotated)

# ── CSV logging ───────────────────────────────────────────────────────
def log_to_csv(result):
    """Append result to the counts CSV."""
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_exists = cfg.CSV_PATH.exists()

    fieldnames = ["filename", "timestamp", "estimated_count",
                  "original_size", "singles", "clusters", "rejected"]

    with open(cfg.CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: result[k] for k in fieldnames})


# ── CLI ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Cell Counter — Phase 1 (Classical CV)"
    )
    parser.add_argument("input", help="Path to a PNG image or a folder of PNGs")
    parser.add_argument("--no-annotate", action="store_true",
                        help="Skip saving annotated images")
    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_dir():
        images = sorted(input_path.glob("*.png"))
        if not images:
            print(f"No PNG files found in {input_path}")
            return
    else:
        images = [input_path]

    print(f"Processing {len(images)} image(s)...\n")

    for img_path in images:
        try:
            result = predict(img_path, save_annotated=not args.no_annotate)
            log_to_csv(result)
            print(f"  {result['filename']:30s}  ->  {result['estimated_count']:>5d} cells  "
                  f"({result['singles']} single, {result['clusters']} clusters, "
                  f"{result['rejected']} rejected)")
        except Exception as e:
            print(f"  {img_path.name:30s}  ->  ERROR: {e}")

    print(f"\nResults saved to {cfg.CSV_PATH}")


if __name__ == "__main__":
    main()
