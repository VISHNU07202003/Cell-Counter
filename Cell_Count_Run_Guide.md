# 🔬 Cell Count Run Guide

This is a simple, step-by-step guide for lab technicians to start the Cell Counter software and process microscopy batches.

---

## 🚀 1. Starting the Server
Before you can use the web interface, you must start the backend server that powers the cell counting AI.

1. **Open your Terminal / Command Prompt** (or VS Code terminal).
2. Ensure you are in the project folder:
   ```bash
   cd "V:\MASTER'S\cell counter 2.0"
   ```
3. Run the start command:
   ```bash
   python server.py
   ```
4. You should see a message saying `* Running on http://127.0.0.1:5000`. Leave this terminal window open in the background!

---

## 🌐 2. Opening the Web App
1. Open your favorite web browser (Chrome, Edge, Safari).
2. Type the following address into the URL bar and hit Enter:
   ```
   http://localhost:5000
   ```
3. You will see the beautiful **Cell Counter** dashboard load instantly.

---

## 📁 3. Uploading & Counting Cells
1. **Prepare your images**: Ensure your images are saved in a folder on your computer. The software expects pairs of images (one Bright-field, one Fluorescence) with the same base name, for example:
   * `2_02_brightfield.png`
   * `2_02_fluorescence.png`
2. **Drag and Drop**: You can drag a massive folder (e.g., `New_Raw`) directly from your desktop into the dotted **Upload Box** on the website.
3. Click the **"Count Cells"** button.
4. The system will process them in small batches to prevent your computer from freezing. Wait for the progress bar to reach 100%.

---

## 📊 4. Viewing Results & Exporting
* **View Images**: Click the "View" button next to any sample to open the interactive viewer. You can toggle between the original image, the annotated image (cells circled), and the pure black-and-white mask.
* **Total vs. Live**: Bright-field detects "Total Cells". Fluorescence detects glowing "Live Cells". The software automatically pairs them and calculates your % Viability.
* **Download CSV**: Click "Download CSV" to get a clean spreadsheet of all your counts.
* **Download Images**: Click "Download All Images" to get a `.zip` file of all the annotated images for your lab notebook.

---

## 🧹 5. Starting a New Batch
* When you are finished and have downloaded your CSV, click the **"Clear / New Batch"** button.
* This wipes the dashboard clean so you can drop your next folder without accidentally mixing up the data!

---

> **Troubleshooting Note:**
> If you drop a folder and some files are separated into two rows instead of merging, ensure that the file names contain the words "bright" and "fluores". The system is smart enough to handle typos (like `Fluoresence`), but the words must be present!
