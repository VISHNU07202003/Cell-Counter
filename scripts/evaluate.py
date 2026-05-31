"""
Cell Counter — Evaluation Framework
===================================================
Benchmarks current prediction pipeline against 64 ground-truth annotations.
"""

import sys
import numpy as np
import cv2
from pathlib import Path
from sklearn.metrics import r2_score

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config as cfg
from scripts.predict import predict

def run_evaluation(verbose=True):
    raw_dir = PROJECT_ROOT / "data" / "raw"
    annotated_dir = PROJECT_ROOT / "data" / "annotated"

    raw_files = sorted(list(raw_dir.glob("*.png")))
    
    if not raw_files:
        print("No raw PNG files found in data/raw/")
        return None

    y_true = []
    y_pred = []
    results = []

    for raw_path in raw_files:
        mask_path = annotated_dir / f"{raw_path.stem}_mask.npy"
        if not mask_path.exists():
            # Try mapping back matching names
            continue
        
        # Load mask and get GT count
        mask = np.load(mask_path)
        unique_ids = np.unique(mask)
        gt_count = len(unique_ids[unique_ids != 0])
        
        # Run prediction pipeline (skip writing annotation files to speed up)
        try:
            pred_res = predict(raw_path, save_annotated=False)
            pred_count = pred_res["estimated_count"]
        except Exception as e:
            print(f"Error predicting {raw_path.name}: {e}")
            continue

        error = pred_count - gt_count
        ape = abs(error) / gt_count if gt_count > 0 else 0.0

        y_true.append(gt_count)
        y_pred.append(pred_count)
        
        results.append({
            "name": raw_path.name,
            "pred": pred_count,
            "gt": gt_count,
            "error": error,
            "ape": ape
        })

    if not y_true:
        print("No matching ground-truth mask files found.")
        return None

    # Compute metrics
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    mae = np.mean(np.abs(y_true - y_pred))
    mape = np.mean(np.abs(y_true - y_pred) / y_true) * 100.0 if np.any(y_true > 0) else 0.0
    r2 = r2_score(y_true, y_pred)

    if verbose:
        print(f"\n{'Image Name':35s} | {'Predicted':>9s} | {'Ground Truth':>12s} | {'Error':>6s} | {'APE':>6s}")
        print("-" * 78)
        for r in results:
            print(f"{r['name']:35s} | {r['pred']:9d} | {r['gt']:12d} | {r['error']:+6d} | {r['ape']*100.5:.1f}%")
        print("-" * 78)
        print(f"Overall Metrics (N = {len(y_true)}):")
        print(f"  Mean Absolute Error (MAE): {mae:.2f} cells")
        print(f"  Mean Absolute Percentage Error (MAPE): {mape:.2f}%")
        print(f"  R² Score: {r2:.4f}")

    return {
        "mae": mae,
        "mape": mape,
        "r2": r2,
        "y_true": y_true,
        "y_pred": y_pred
    }

if __name__ == "__main__":
    run_evaluation(verbose=True)
