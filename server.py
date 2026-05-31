"""
Cell Counter — Web Server (Flask API)
======================================
Wraps the existing predict.py pipeline as a REST API.

Endpoints:
  POST /api/upload              Upload images and get cell counts
  GET  /api/results             Get all processed results
  GET  /api/images/<path>       Serve annotated/debug images
  GET  /api/download/csv        Download the counts CSV
  GET  /api/download/zip        Download all annotated images as ZIP
  POST /api/engine              Toggle between OpenCV and Cellpose engines
  POST /api/save_annotations    Save user corrections for active learning
  POST /api/insights            Generate LLM-powered batch insights
"""

import io
import json
import zipfile
import sys
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import config as cfg
from scripts.predict import predict, log_to_csv, set_engine, get_engine

# ── Flask App Setup ──────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="")

UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

# In-memory results store (reset on server restart)
session_results = []


# ── Routes ───────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main HTML page."""
    return send_from_directory("static", "index.html")


@app.route("/login")
def login():
    """Serve the login page."""
    return send_from_directory("static", "login.html")


@app.route("/api/upload", methods=["POST"])
def upload_and_process():
    """
    Accept one or more image files, run the prediction pipeline,
    and return the results as JSON.
    """
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        return jsonify({"error": "No files selected"}), 400

    # Group files by sample ID
    sample_groups = {}
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
            
        stem = Path(f.filename).stem.strip()
        lower_stem = stem.lower()
        
        # Robustly extract sample ID by finding the keyword and stripping
        if "fluores" in lower_stem:
            idx = lower_stem.find("fluores")
            sample_id = stem[:idx].strip("_ -")
        elif "bright" in lower_stem:
            idx = lower_stem.find("bright")
            sample_id = stem[:idx].strip("_ -")
        else:
            sample_id = stem
            
        if sample_id not in sample_groups:
            sample_groups[sample_id] = []
        sample_groups[sample_id].append(f)

    results = []
    for sample_id, sample_files in sample_groups.items():
        sample_result = {
            "sample_id": sample_id,
            "status": "done",
            "total_count": None,
            "live_count": None,
            "viability": None,
            "brightfield": None,
            "fluorescence": None,
            "error": None
        }
        
        for f in sample_files:
            safe_name = secure_filename(f.filename)
            save_path = UPLOAD_DIR / safe_name
            f.save(str(save_path))
            
            try:
                img_result = predict(save_path, save_annotated=True)
                log_to_csv(img_result)
                
                img_data = {
                    "filename": img_result["filename"],
                    "estimated_count": img_result["estimated_count"],
                    "annotated_url": f"/api/images/annotated_{Path(safe_name).stem}.png",
                    "debug_url": f"/api/images/debug_{Path(safe_name).stem}.png",
                    "original_url": f"/api/uploads/{safe_name}"
                }
                
                if "fluores" in img_result.get("image_type", ""):
                    sample_result["fluorescence"] = img_data
                    sample_result["live_count"] = img_result["estimated_count"]
                else:
                    sample_result["brightfield"] = img_data
                    sample_result["total_count"] = img_result["estimated_count"]
                    
            except Exception as e:
                sample_result["error"] = str(e)
                sample_result["status"] = "error"
        
        # Calculate viability
        if sample_result["total_count"] is not None and sample_result["live_count"] is not None:
            # Bright-field algorithms can sometimes miss cells that the fluorescent channel clearly detects
            if sample_result["live_count"] > sample_result["total_count"]:
                sample_result["total_count"] = sample_result["live_count"]
                if sample_result["brightfield"]:
                    sample_result["brightfield"]["estimated_count"] = sample_result["live_count"]
            
            if sample_result["total_count"] > 0:
                viab = (sample_result["live_count"] / sample_result["total_count"]) * 100
                sample_result["viability"] = round(viab, 1)
            else:
                sample_result["viability"] = 0.0
                
        results.append(sample_result)
        session_results.append(sample_result)

    return jsonify({"results": results})


@app.route("/api/results", methods=["GET"])
def get_results():
    """Return all session results."""
    return jsonify({"results": session_results})

@app.route("/api/results", methods=["DELETE"])
def clear_results():
    """Clear the current session results."""
    session_results.clear()
    return jsonify({"status": "cleared"})


@app.route("/api/images/<path:filename>")
def serve_output_image(filename):
    """Serve annotated or debug images from the outputs folder."""
    return send_from_directory(str(cfg.OUTPUT_DIR), filename)


@app.route("/api/uploads/<path:filename>")
def serve_uploaded_image(filename):
    """Serve original uploaded images."""
    return send_from_directory(str(UPLOAD_DIR), filename)


@app.route("/api/download/csv")
def download_csv():
    """Download the counts as a dynamically generated CSV for the current session only."""
    if not session_results:
        return jsonify({"error": "No results in current session"}), 404

    import csv
    
    # Create CSV in memory
    output = io.StringIO()
    fieldnames = ["sample_id", "total_count", "live_count", "viability", "status", "error"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for r in session_results:
        writer.writerow({k: r.get(k) for k in fieldnames})

    # Convert StringIO to BytesIO for sending
    buffer = io.BytesIO(output.getvalue().encode('utf-8'))
    
    return send_file(
        buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"cell_counts_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )


@app.route("/api/download/zip")
def download_zip():
    """Download all annotated images as a ZIP file."""
    if not session_results:
        return jsonify({"error": "No results yet"}), 404

    # Create ZIP in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in session_results:
            for img_type in ["brightfield", "fluorescence"]:
                if r.get(img_type):
                    # Add annotated image
                    ann_name = r[img_type]["annotated_url"].split("/")[-1]
                    ann_path = cfg.OUTPUT_DIR / ann_name
                    if ann_path.exists():
                        zf.write(str(ann_path), ann_name)

                    # Add debug image
                    dbg_name = r[img_type]["debug_url"].split("/")[-1]
                    dbg_path = cfg.OUTPUT_DIR / dbg_name
                    if dbg_path.exists():
                        zf.write(str(dbg_path), dbg_name)

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"cell_counter_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    )


# ── Phase 6: Engine Toggle ───────────────────────────────────────

@app.route("/api/engine", methods=["GET", "POST"])
def engine_toggle():
    """Get or set the prediction engine (opencv or cellpose)."""
    if request.method == "POST":
        data = request.get_json(force=True)
        engine = data.get("engine", "opencv")
        current = set_engine(engine)
        return jsonify({"engine": current, "message": f"Engine switched to {current}"})
    else:
        return jsonify({"engine": get_engine()})


# ── Phase 7: Active Learning — Save Annotations ─────────────────

TRAINING_DATA_DIR = PROJECT_ROOT / "data" / "training_data"
TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)

@app.route("/api/save_annotations", methods=["POST"])
def save_annotations():
    """
    Save user-corrected cell coordinates for active learning.
    Expects JSON: { sample_id, image_type, centroids: [{x, y}, ...], action_log: [...] }
    """
    data = request.get_json(force=True)
    sample_id = data.get("sample_id", "unknown")
    image_type = data.get("image_type", "brightfield")
    centroids = data.get("centroids", [])
    action_log = data.get("action_log", [])

    # Create a timestamped entry
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    entry = {
        "sample_id": sample_id,
        "image_type": image_type,
        "timestamp": ts,
        "corrected_count": len(centroids),
        "centroids": centroids,
        "action_log": action_log,
    }

    # Save JSON
    json_path = TRAINING_DATA_DIR / f"{sample_id}_{image_type}_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(entry, f, indent=2)

    # Copy the original image alongside the annotation if it exists in uploads
    for ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
        candidates = list(UPLOAD_DIR.glob(f"*{sample_id}*{image_type}*{ext}"))
        if not candidates:
            candidates = list(UPLOAD_DIR.glob(f"*{sample_id}*{ext}"))
        if candidates:
            import shutil
            dest = TRAINING_DATA_DIR / f"{sample_id}_{image_type}_{ts}{ext}"
            shutil.copy2(str(candidates[0]), str(dest))
            break

    return jsonify({
        "status": "saved",
        "path": str(json_path),
        "corrected_count": len(centroids)
    })


# ── Phase 8: LLM-Powered Batch Insights ──────────────────────────

@app.route("/api/insights", methods=["POST"])
def generate_insights():
    """
    Generate natural-language batch insights from the current results.
    Uses rule-based analysis (no external API key required).
    """
    if not session_results:
        return jsonify({"error": "No results to analyze"}), 404

    # Gather stats
    total_samples = len(session_results)
    viabilities = []
    total_counts = []
    live_counts = []
    low_viability = []
    high_viability = []
    zero_counts = []
    max_count_sample = None
    max_count = 0

    for r in session_results:
        if r.get("status") == "error":
            continue
        tc = r.get("total_count")
        lc = r.get("live_count")
        v = r.get("viability")

        if tc is not None:
            total_counts.append(tc)
            if tc > max_count:
                max_count = tc
                max_count_sample = r.get("sample_id")
            if tc == 0:
                zero_counts.append(r.get("sample_id"))

        if lc is not None:
            live_counts.append(lc)

        if v is not None:
            viabilities.append(v)
            if v < 50:
                low_viability.append({"id": r.get("sample_id"), "viability": v})
            elif v >= 90:
                high_viability.append({"id": r.get("sample_id"), "viability": v})

    # Build insights
    insights = []
    insights.append(f"## 📊 Batch Summary")
    insights.append(f"Processed **{total_samples}** samples in this batch.")
    insights.append("")

    if total_counts:
        avg_total = sum(total_counts) / len(total_counts)
        insights.append(f"### Cell Counts")
        insights.append(f"- **Average total cells:** {avg_total:.1f} per sample")
        insights.append(f"- **Range:** {min(total_counts)} — {max(total_counts)} cells")
        if max_count_sample:
            insights.append(f"- **Highest count:** {max_count} cells in sample **{max_count_sample}**")
        insights.append("")

    if viabilities:
        avg_v = sum(viabilities) / len(viabilities)
        insights.append(f"### Viability")
        insights.append(f"- **Average viability:** {avg_v:.1f}%")
        if avg_v >= 80:
            insights.append(f"- ✅ Overall viability is **healthy** (≥80%).")
        elif avg_v >= 60:
            insights.append(f"- ⚠️ Overall viability is **moderate** (60-80%). Monitor closely.")
        else:
            insights.append(f"- 🚨 Overall viability is **low** (<60%). Investigate immediately.")
        insights.append("")

    if low_viability:
        insights.append(f"### ⚠️ Low Viability Alerts")
        insights.append(f"The following {len(low_viability)} sample(s) showed viability below 50%:")
        for s in low_viability:
            insights.append(f"- **{s['id']}**: {s['viability']}%")
        insights.append("")
        insights.append("**Recommendation:** Check temperature, pH, and nutrient levels in the corresponding fermentation vessels. Low viability may indicate contamination, nutrient depletion, or thermal stress.")
        insights.append("")

    if high_viability:
        insights.append(f"### ✅ Healthy Samples")
        insights.append(f"{len(high_viability)} sample(s) showed excellent viability (≥90%):")
        for s in high_viability:
            insights.append(f"- **{s['id']}**: {s['viability']}%")
        insights.append("")

    if zero_counts:
        insights.append(f"### 🔍 Zero-Count Warnings")
        insights.append(f"The following sample(s) returned zero cells detected:")
        for sid in zero_counts:
            insights.append(f"- **{sid}**")
        insights.append("")
        insights.append("**Recommendation:** Re-examine image quality. Poor focus, incorrect exposure, or empty chambers can cause zero detections. Consider re-photographing these samples.")
        insights.append("")

    if live_counts and total_counts:
        total_all = sum(total_counts)
        live_all = sum(live_counts)
        if total_all > 0:
            batch_viability = (live_all / total_all) * 100
            insights.append(f"### 🧬 Batch-Level Metrics")
            insights.append(f"- **Total cells across all samples:** {total_all:,}")
            insights.append(f"- **Total live cells:** {live_all:,}")
            insights.append(f"- **Batch-wide viability:** {batch_viability:.1f}%")
            insights.append("")

    insights.append(f"---")
    insights.append(f"*Analysis generated by Cell Counter v2.0 · Engine: {get_engine().upper()} · {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return jsonify({
        "insights": "\n".join(insights),
        "stats": {
            "total_samples": total_samples,
            "avg_viability": round(sum(viabilities) / len(viabilities), 1) if viabilities else None,
            "avg_total_count": round(sum(total_counts) / len(total_counts), 1) if total_counts else None,
            "low_viability_count": len(low_viability),
            "engine": get_engine(),
        }
    })


# ── Entry Point ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  Cell Counter — Web Interface")
    print("=" * 50)
    print(f"  Open in browser: http://localhost:5000")
    print(f"  Output directory: {cfg.OUTPUT_DIR}")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
