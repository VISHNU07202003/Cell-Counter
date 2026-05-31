import sys
import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import r2_score

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config as cfg
from scripts.predict import preprocess, segment, circularity, predict

def generate_performance_plots():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    annotated_dir = PROJECT_ROOT / "data" / "annotated"
    output_dir = PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(list(raw_dir.glob("*.png")))
    if not raw_files:
        print("No raw PNG files found.")
        return

    print("Computing metrics and generating plots across 64 images...")
    
    y_true = []
    y_pred = []
    
    # Object detection metrics (TP, FP, FN)
    cohorts = {"csm": {"TP": 0, "FP": 0, "FN": 0}, "Project": {"TP": 0, "FP": 0, "FN": 0}}
    image_results = []

    for idx, raw_path in enumerate(raw_files):
        mask_path = annotated_dir / f"{raw_path.stem}_mask.npy"
        if not mask_path.exists():
            continue
            
        # Load ground truth mask
        gt_mask = np.load(mask_path)
        unique_labels = np.unique(gt_mask)
        gt_cell_ids = set(unique_labels[unique_labels != 0])
        gt_count = len(gt_cell_ids)
        
        # Load raw image and run segmentation
        img_bgr = cv2.imread(str(raw_path))
        gray = preprocess(img_bgr)
        raw_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        binary_mask = segment(gray)
        
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Determine cohort
        cohort_name = "csm" if raw_path.name.startswith("csm") else "Project"
        
        # Run count prediction
        try:
            pred_res = predict(raw_path, save_annotated=False)
            pred_count = pred_res["estimated_count"]
        except Exception as e:
            print(f"Error predicting {raw_path.name}: {e}")
            continue

        y_true.append(gt_count)
        y_pred.append(pred_count)
        
        # Calculate TP, FP, FN at object level
        detected_cell_ids = set()
        tp_count = 0
        fp_count = 0
        
        # Parameters used in prediction
        sca = cfg.SINGLE_CELL_AREA
        mca = cfg.MIN_CELL_AREA
        mc = cfg.MIN_CIRCULARITY
        mmi = cfg.MAX_MEAN_INTENSITY
        ct = cfg.CLUSTER_THRESHOLD
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            circ = circularity(cnt)
            
            if area < mca or area > 200000:
                continue
                
            min_circ = cfg.CLUSTER_MIN_CIRCULARITY if area >= ct else mc
            if circ < min_circ:
                continue
                
            bm = np.zeros(raw_gray.shape, dtype=np.uint8)
            cv2.drawContours(bm, [cnt], -1, 255, -1)
            mean_intensity = cv2.mean(raw_gray, mask=bm)[0]
            
            if mean_intensity > mmi:
                continue
                
            # Check overlap with ground truth mask
            overlapping_pixels = gt_mask[bm == 255]
            overlap_labels, overlap_counts = np.unique(overlapping_pixels, return_counts=True)
            
            # Exclude background (ID 0)
            bg_idx = np.where(overlap_labels == 0)[0]
            if len(bg_idx) > 0:
                overlap_labels = np.delete(overlap_labels, bg_idx)
                overlap_counts = np.delete(overlap_counts, bg_idx)
                
            if len(overlap_labels) > 0:
                # Find label with max overlap
                best_label_idx = np.argmax(overlap_counts)
                best_label = overlap_labels[best_label_idx]
                overlap_size = overlap_counts[best_label_idx]
                
                # Minimum overlap threshold (10 px)
                if overlap_size >= 10:
                    detected_cell_ids.add(best_label)
                    tp_count += 1
                else:
                    fp_count += 1
            else:
                fp_count += 1
                
        # False negatives are ground-truth cell IDs that were never detected
        fn_count = len(gt_cell_ids - detected_cell_ids)
        
        cohorts[cohort_name]["TP"] += tp_count
        cohorts[cohort_name]["FP"] += fp_count
        cohorts[cohort_name]["FN"] += fn_count
        
        err = pred_count - gt_count
        ape = abs(err) / gt_count if gt_count > 0 else 0.0
        
        image_results.append({
            "name": raw_path.name,
            "gt": gt_count,
            "pred": pred_count,
            "error": err,
            "ape": ape,
            "cohort": cohort_name
        })

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # ── 1. Scatter Plot (Correlation) ──
    plt.figure(figsize=(8, 6))
    plt.style.use("seaborn-v0_8-whitegrid")
    
    # Split by cohort for coloring
    gt_csm = [r["gt"] for r in image_results if r["cohort"] == "csm"]
    pred_csm = [r["pred"] for r in image_results if r["cohort"] == "csm"]
    gt_proj = [r["gt"] for r in image_results if r["cohort"] == "Project"]
    pred_proj = [r["pred"] for r in image_results if r["cohort"] == "Project"]
    
    plt.scatter(gt_csm, pred_csm, color="#4e79a7", alpha=0.8, label="csm Cohort (Small Cells)", edgecolors="k", s=50)
    plt.scatter(gt_proj, pred_proj, color="#f28e2b", alpha=0.8, label="Project Cohort (Large Cells)", edgecolors="k", s=50)
    
    # Diagonal line
    max_val = max(max(y_true), max(y_pred))
    plt.plot([0, max_val], [0, max_val], color="red", linestyle="--", linewidth=1.5, label="Perfect Agreement (y = x)")
    
    r2 = r2_score(y_true, y_pred)
    mae = np.mean(np.abs(y_true - y_pred))
    mape = np.mean(np.abs(y_true - y_pred) / y_true) * 100.0
    
    plt.title(f"Yeast Cell Count Correlation (R² = {r2:.4f})", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Ground Truth Cell Count", fontsize=12)
    plt.ylabel("Model Predicted Cell Count", fontsize=12)
    plt.xlim(0, max_val + 50)
    plt.ylim(0, max_val + 50)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(output_dir / "evaluation_correlation.png", dpi=150)
    plt.close()

    # ── 2. Error Distribution (Residuals) ──
    plt.figure(figsize=(8, 6))
    errors = y_pred - y_true
    plt.hist(errors, bins=15, color="#59a14f", edgecolor="black", alpha=0.8)
    plt.axvline(0, color="red", linestyle="--", linewidth=1.5, label="Zero Error")
    plt.title("Distribution of Counting Errors (Residuals)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Error (Predicted - Ground Truth)", fontsize=12)
    plt.ylabel("Number of Images", fontsize=12)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(output_dir / "error_distribution.png", dpi=150)
    plt.close()

    # ── 3. Precision, Recall, F1 Cohort Metrics ──
    # Calculate Precision, Recall, F1 for both cohorts
    plt.figure(figsize=(8, 6))
    
    labels = ["csm Cohort", "Project Cohort", "Dataset-Wide"]
    precisions = []
    recalls = []
    f1s = []
    
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for c_name in ["csm", "Project"]:
        tp = cohorts[c_name]["TP"]
        fp = cohorts[c_name]["FP"]
        fn = cohorts[c_name]["FN"]
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        
        precisions.append(prec * 100.0)
        recalls.append(rec * 100.0)
        f1s.append(f1 * 100.0)
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
    # Overall
    prec_all = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    rec_all = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1_all = 2 * prec_all * rec_all / (prec_all + rec_all) if (prec_all + rec_all) > 0 else 0
    
    precisions.append(prec_all * 100.0)
    recalls.append(rec_all * 100.0)
    f1s.append(f1_all * 100.0)

    x = np.arange(len(labels))
    width = 0.25

    plt.bar(x - width, precisions, width, label="Precision", color="#4e79a7", edgecolor="black")
    plt.bar(x, recalls, width, label="Recall (Sensitivity)", color="#f28e2b", edgecolor="black")
    plt.bar(x + width, f1s, width, label="F1-Score", color="#e15759", edgecolor="black")

    plt.title("Object-Level Detection Metrics by Cohort", fontsize=14, fontweight="bold", pad=15)
    plt.xticks(x, labels, fontsize=11)
    plt.ylabel("Score (%)", fontsize=12)
    plt.ylim(0, 110)
    
    # Annotate value labels on top of the bars
    for i in range(len(labels)):
        plt.text(i - width, precisions[i] + 1.5, f"{precisions[i]:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
        plt.text(i, recalls[i] + 1.5, f"{recalls[i]:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
        plt.text(i + width, f1s[i] + 1.5, f"{f1s[i]:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.legend(fontsize=10, loc="lower right")
    plt.tight_layout()
    plt.savefig(output_dir / "detection_metrics.png", dpi=150)
    plt.close()

    print("\n" + "="*50)
    print("PERFORMANCE METRICS REPORT")
    print("="*50)
    print(f"Overall Dataset Metrics:")
    print(f"  MAE (Mean Absolute Error):                  {mae:.2f} cells")
    print(f"  MAPE (Mean Absolute Percentage Error):      {mape:.2f}%")
    print(f"  R² Score (Correlation Fit):                 {r2:.4f}")
    print(f"  Object-Level Precision:                     {prec_all*100.0:.2f}%")
    print(f"  Object-Level Recall:                        {rec_all*100.0:.2f}%")
    print(f"  Object-Level F1-Score:                      {f1_all*100.0:.2f}%")
    print("-" * 50)
    for idx, c_name in enumerate(["csm", "Project"]):
        print(f"{c_name} Cohort Metrics:")
        print(f"  Object-Level Precision:                     {precisions[idx]:.2f}%")
        print(f"  Object-Level Recall:                        {recalls[idx]:.2f}%")
        print(f"  Object-Level F1-Score:                      {f1s[idx]:.2f}%")
    print("="*50)
    print(f"Graphs saved successfully inside: {output_dir}")

if __name__ == "__main__":
    generate_performance_plots()
