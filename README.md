# 🔬 Cell Counter 2.0 — Automated Microscopy Cell Counting

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red.svg)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A web-based automated cell counting application for yeast fermentation labs.**  
> Drag-and-drop microscope images, get instant cell counts, viability percentages, and annotated overlays — no manual counting, no parameter tuning, no training required.

![Cell Counter Dashboard](https://img.shields.io/badge/Status-Production-brightgreen)

---

## 🎯 What It Does

Cell Counter 2.0 replaces the traditional 4-hour manual hemocytometer workflow with a **2-minute automated pipeline**:

| Before (Manual) | After (Cell Counter 2.0) |
|-----------------|--------------------------|
| Hemocytometer + tally counter | Drag & drop a folder |
| 8-10 min per image in ImageJ | Batch process 42 images in 2 min |
| 15-20% operator variability | Consistent, reproducible counts |
| Separate bright-field & fluorescence protocols | Automatic image type detection |
| Manual Excel data entry | One-click CSV export |
| No visual verification | Annotated overlays + mask views |

---

## ✨ Key Features

- **🖱️ Drag & Drop Folders** — Upload entire experiment folders. The app recursively finds all images inside.
- **🔬 Dual-Mode Processing** — Automatically detects bright-field vs. fluorescence images from filenames and routes to the correct algorithm.
- **🧬 Smart Pairing** — Groups `2_01_brightfield.png` + `2_01_fluorescence.png` into a single sample with Total Cells, Live Cells, and Viability %.
- **📊 Live Dashboard** — Real-time metric cards, sortable results table, and progress bar.
- **🖼️ 6-View Image Viewer** — Toggle between Original, Annotated (cells circled), and Mask views for both BF and FL channels.
- **📥 One-Click Export** — Download CSV spreadsheet or ZIP of all annotated images.
- **🔐 Lab Login Portal** — Animated login page with pre-configured lab credentials and "Remember Me" functionality.
- **🧹 Batch Management** — Clear workspace between batches to keep data clean.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, Flask |
| **Computer Vision** | OpenCV (Otsu thresholding, contour analysis, watershed segmentation) |
| **Frontend** | Vanilla HTML/CSS/JS (no frameworks) |
| **Design** | Glassmorphism, Inter + JetBrains Mono fonts, violet accent theme |
| **Deep Learning** (planned) | PyTorch, Cellpose 4.1 |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/cell-counter-2.0.git
cd cell-counter-2.0

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python server.py
```

Open your browser to **http://localhost:5000**

- **Login page:** http://localhost:5000/login
- **Quick credentials:** `lab` / `lab`

---

## 📁 Project Structure

```
cell counter 2.0/
├── server.py                # Flask web server & API routes
├── config.py                # Pipeline parameters & thresholds
├── requirements.txt         # Python dependencies
├── Cell_Count_Run_Guide.md  # Lab technician quick-start guide
├── scripts/
│   ├── predict.py           # Core CV pipeline (BF + FL algorithms)
│   └── config.py            # Processing configuration
├── static/
│   ├── index.html           # Main dashboard page
│   ├── style.css            # Dashboard stylesheet
│   ├── app.js               # Dashboard logic (upload, batch, viewer)
│   ├── login.html           # Login page
│   ├── login.css            # Login stylesheet
│   └── login.js             # Login auth logic
├── UXD/
│   ├── D2_Heuristic_Evaluation.md  # Nielsen's 10 heuristics analysis
│   ├── D3_Interview_Guide.md       # User research interviews
│   └── D5_Design_Artifacts.md      # Personas, flows, storyboards
└── data/
    └── New_Raw/             # Sample microscope images (not in repo)
```

---

## 🔬 How the Pipeline Works

```
Image Upload → Filename Detection → Algorithm Routing
                                         │
                    ┌────────────────────┤────────────────────┐
                    │                                         │
              Bright-Field                              Fluorescence
           (Total Cell Count)                        (Live Cell Count)
                    │                                         │
          Otsu Threshold + Morph               Green Channel + Otsu
          Contour Detection                     Contour Detection
          Area-Based Splitting                   Direct Counting
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         │
                              Sample Pairing by ID
                              Viability = Live/Total × 100%
                                         │
                              Results Table + CSV Export
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main dashboard |
| `GET` | `/login` | Login page |
| `POST` | `/api/upload` | Upload & process images |
| `GET` | `/api/results` | Get all session results |
| `DELETE` | `/api/results` | Clear session / new batch |
| `GET` | `/api/download/csv` | Download results as CSV |
| `GET` | `/api/download/zip` | Download annotated images as ZIP |

---

## 📈 Roadmap

- [x] Phase 1 — Classical CV pipeline (Otsu + contour analysis)
- [x] Phase 2 — Parameter optimization & evaluation
- [x] Phase 3 — Web interface (Flask + vanilla JS)
- [x] Phase 3.5 — Fluorescence viability pipeline
- [x] Phase 4 — Folder upload & batch processing
- [x] Phase 5 — UX Design documentation & login page
- [ ] Phase 6 — Deep Learning (Cellpose) integration
- [ ] Phase 7 — Active Learning canvas (click-to-correct)
- [ ] Phase 8 — LLM-powered batch insights

---

## 🎓 Academic Context

This project was developed as part of a Master's thesis at the **University of Florida** (BlueberryLab UF), combining:
- **Computer Vision** — Automated image analysis for biological microscopy
- **User Experience Design** (CEN 5728) — Full UCD process including heuristic evaluation, user research, personas, and interaction design

---

## 👤 Author

**Vishnu Sai Padyala**  
M.S. Student, University of Florida  
Spring 2026

---

## 📄 License

This project is licensed under the MIT License.
