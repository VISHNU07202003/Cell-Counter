"""
Cell Counter — Configuration
=============================================
All tunable constants in one place.
Derived from Cell_Area.xlsx (15 measurements, 1 px ≈ 1.75 µm).
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR     = PROJECT_ROOT / "data"
OUTPUT_DIR   = PROJECT_ROOT / "outputs"
CSV_PATH     = OUTPUT_DIR / "counts.csv"

# ── Cell geometry (from Cell_Area.xlsx) ────────────────
SINGLE_CELL_AREA   = 350    # px²  — calibrated against manual count (153-200 cells)
MIN_CELL_AREA      = 250    # px²  — raised: human annotation shows <250 are all debris
MAX_CELL_AREA      = 200000 # px²  — allow massive dense clusters
CLUSTER_THRESHOLD  = 600    # px²  — 2× single cell → apply cluster math

# ── Shape filters ──────────────────────────────────────
MIN_CIRCULARITY         = 0.4  # real cells are round; raised per human annotation
CLUSTER_MIN_CIRCULARITY = 0.05  # large dense clusters can be very irregular

# ── Intensity filter (darkness) ────────────────────────
# Real cells are DARK (brown/black). Debris is LIGHT (beige/green).
# Mean grayscale intensity inside contour must be BELOW this to be accepted.
MAX_MEAN_INTENSITY = 135  # 0=black, 255=white; cells typically < 120

# ── Preprocessing ──────────────────────────────────────
CLAHE_CLIP_LIMIT   = 3.0
CLAHE_TILE_SIZE    = (8, 8)
BLUR_KERNEL        = (5, 5)
PROCESSING_SIZE    = (512, 512)   # resize for uniform processing

# ── Otsu threshold tweaks ──────────────────────────────
MORPH_KERNEL_SIZE  = 3      # for morphological open/close cleanup
MORPH_ITERATIONS   = 1      # keep low to avoid fragmenting clusters

# ── Annotated output ───────────────────────────────────
CONTOUR_COLOR_CELL    = (0, 255, 0)    # green  — accepted cells
CONTOUR_COLOR_CLUSTER = (0, 165, 255)  # orange — clusters
CONTOUR_COLOR_REJECT  = (0, 0, 255)    # red    — rejected debris
CONTOUR_THICKNESS     = 1
FONT_SCALE            = 0.35
