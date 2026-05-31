/**
 * Cell Counter — Frontend Application
 * ====================================
 * Handles file upload, API communication, results display,
 * and image viewer interactions.
 */

// ── State ──────────────────────────────────────────────────────
const state = {
  files: [],
  results: [],
  processing: false,
};

// ── DOM Elements ───────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const uploadZone = $("#uploadZone");
const fileInput = $("#fileInput");
const fileStrip = $("#fileStrip");
const countBtn = $("#countBtn");
const progressSection = $("#progressSection");
const progressText = $("#progressText");
const progressFill = $("#progressFill");
const resultsSection = $("#resultsSection");
const resultsBody = $("#resultsBody");
const viewerSection = $("#viewerSection");
const statusIndicator = $("#statusIndicator");
const toastContainer = $("#toastContainer");

// ── Upload Zone Events ─────────────────────────────────────────

// Click to browse
uploadZone.addEventListener("click", () => {
  if (!state.processing) fileInput.click();
});

// File input change
fileInput.addEventListener("change", (e) => {
  addFiles(Array.from(e.target.files));
  fileInput.value = ""; // Reset so same file can be re-selected
});

// Drag & Drop
uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", async (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  
  const files = [];
  const items = e.dataTransfer.items;
  
  if (items) {
    const promises = [];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        if (entry) promises.push(traverseFileTree(entry, "", files));
      }
    }
    await Promise.all(promises);
  } else {
    // Fallback for older browsers
    Array.from(e.dataTransfer.files).forEach(f => files.push(f));
  }
  
  // Filter for valid images
  const validFiles = files.filter(f => f.type.startsWith("image/") || f.name.match(/\.(png|jpe?g|tiff?)$/i));
  
  if (validFiles.length === 0) {
    showToast("No valid image files found.", "error");
    return;
  }
  
  addFiles(validFiles);
});

// Helper to recursively read directories
function traverseFileTree(item, path = "", files = []) {
  return new Promise((resolve) => {
    if (item.isFile) {
      item.file((file) => {
        // Exclude hidden files like .DS_Store
        if (!file.name.startsWith(".")) {
          // Create a new File with the folder path prefixed to avoid duplicate names
          const newName = path ? `${path}${file.name}`.replace(/[\/\\]/g, '_') : file.name;
          const newFile = new File([file], newName, { type: file.type });
          files.push(newFile);
        }
        resolve();
      });
    } else if (item.isDirectory) {
      const dirReader = item.createReader();
      const readEntries = () => {
        dirReader.readEntries((entries) => {
          if (entries.length === 0) {
            resolve();
          } else {
            const promises = [];
            for (let i = 0; i < entries.length; i++) {
              // Append this directory's name to the path for its children
              promises.push(traverseFileTree(entries[i], path + item.name + "_", files));
            }
            Promise.all(promises).then(readEntries);
          }
        });
      };
      readEntries();
    } else {
      resolve();
    }
  });
}

// ── File Management ────────────────────────────────────────────

function addFiles(newFiles) {
  // Filter duplicates
  const existingNames = new Set(state.files.map((f) => f.name));
  const unique = newFiles.filter((f) => !existingNames.has(f.name));

  if (unique.length === 0) {
    showToast("These files are already added.", "error");
    return;
  }

  state.files.push(...unique);
  uploadZone.classList.add("has-files");
  countBtn.disabled = false;
  renderFileStrip();
  showToast(`${unique.length} image(s) added.`, "success");
}

function removeFile(index) {
  state.files.splice(index, 1);
  if (state.files.length === 0) {
    uploadZone.classList.remove("has-files");
    countBtn.disabled = true;
  }
  renderFileStrip();
}

function renderFileStrip() {
  fileStrip.innerHTML = "";
  state.files.forEach((file, i) => {
    const chip = document.createElement("div");
    chip.className = "file-chip";

    const thumb = document.createElement("img");
    thumb.className = "file-thumb";
    thumb.src = URL.createObjectURL(file);
    thumb.alt = file.name;

    const name = document.createElement("span");
    name.className = "file-name";
    name.textContent =
      file.name.length > 12 ? file.name.slice(0, 10) + "..." : file.name;

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.textContent = "×";
    removeBtn.onclick = (e) => {
      e.stopPropagation();
      removeFile(i);
    };

    chip.appendChild(thumb);
    chip.appendChild(name);
    chip.appendChild(removeBtn);
    fileStrip.appendChild(chip);
  });
}

// ── Processing ─────────────────────────────────────────────────

countBtn.addEventListener("click", () => {
  if (state.files.length === 0 || state.processing) return;
  processImages();
});

async function processImages() {
  state.processing = true;
  state.results = [];
  countBtn.disabled = true;
  if (statusIndicator) {
    statusIndicator.textContent = "Processing...";
    statusIndicator.classList.add("processing");
  }

  // Show progress
  progressSection.classList.remove("section-hidden");
  progressSection.classList.add("section-visible");
  resultsSection.classList.add("section-hidden");
  resultsSection.classList.remove("section-visible");
  viewerSection.classList.add("section-hidden");
  viewerSection.classList.remove("section-visible");

  const total = state.files.length;
  
  // Group files by sample ID on the client side to prevent splitting pairs across batches
  const groupedFiles = new Map();
  state.files.forEach(f => {
    let name = f.name;
    let lowerName = name.toLowerCase();
    let sampleId = name;
    
    if (lowerName.includes("fluores")) {
      sampleId = name.substring(0, lowerName.indexOf("fluores")).replace(/[_ -]+$/, "");
    } else if (lowerName.includes("bright")) {
      sampleId = name.substring(0, lowerName.indexOf("bright")).replace(/[_ -]+$/, "");
    }
    
    if (!groupedFiles.has(sampleId)) groupedFiles.set(sampleId, []);
    groupedFiles.get(sampleId).push(f);
  });

  const batches = [];
  const MAX_FILES_PER_BATCH = 4;
  let currentBatch = [];
  
  for (const group of groupedFiles.values()) {
    if (currentBatch.length + group.length > MAX_FILES_PER_BATCH && currentBatch.length > 0) {
      batches.push(currentBatch);
      currentBatch = [];
    }
    currentBatch.push(...group);
  }
  if (currentBatch.length > 0) {
    batches.push(currentBatch);
  }

  let processedCount = 0;
  for (let i = 0; i < batches.length; i++) {
    const batch = batches[i];
    const formData = new FormData();
    batch.forEach((f) => formData.append("files", f));

    updateProgress(processedCount, total);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      state.results.push(...data.results);
    } catch (err) {
      showToast(`Error processing batch: ${err.message}`, "error");
      batch.forEach((f) => {
        state.results.push({
          sample_id: f.name,
          error: err.message,
          status: "error",
        });
      });
    }
    processedCount += batch.length;
  }

  updateProgress(total, total);

  // Small delay for visual satisfaction
  setTimeout(() => {
    state.processing = false;
    if (statusIndicator) {
      statusIndicator.textContent = "Complete";
      statusIndicator.classList.remove("processing");
    }
    progressSection.classList.add("section-hidden");
    progressSection.classList.remove("section-visible");
    renderResults();
    showToast(`Done! ${state.results.length} images processed.`, "success");
  }, 500);
}

function updateProgress(current, total) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;
  progressFill.style.width = `${pct}%`;
  progressText.textContent = `Processing ${current}/${total} images...`;
}

// ── Results Rendering ──────────────────────────────────────────

function renderResults() {
  // Calculate metrics
  const successful = state.results.filter((r) => r.status === "done");
  const totalCells = successful.reduce((sum, r) => sum + (r.total_count || 0), 0);
  const liveCells = successful.reduce((sum, r) => sum + (r.live_count || 0), 0);
  
  const viableSamples = successful.filter(r => r.viability !== null);
  const avgViab = viableSamples.length > 0 
    ? Math.round(viableSamples.reduce((sum, r) => sum + r.viability, 0) / viableSamples.length) 
    : 0;

  // Animate metric counts
  animateCount("totalCount", totalCells);
  animateCount("liveCount", liveCells);
  animateCount("avgViability", avgViab, "%");

  // Build table rows
  resultsBody.innerHTML = "";
  state.results.forEach((r, i) => {
    const tr = document.createElement("tr");
    tr.className = `stagger-${(i % 6) + 1}`;
    tr.style.animation = `fadeInUp 0.4s ease ${i * 50}ms both`;

    if (r.status === "error") {
      tr.innerHTML = `
        <td><div class="thumb-placeholder">⚠️</div></td>
        <td>${escapeHtml(r.sample_id)}</td>
        <td colspan="4" class="text-coral">${escapeHtml(r.error)}</td>
        <td><span class="status-badge warning">Error</span></td>
      `;
    } else {
      const thumbUrl = r.fluorescence ? r.fluorescence.annotated_url : (r.brightfield ? r.brightfield.annotated_url : "");
      const totalText = r.total_count !== null ? r.total_count : "—";
      const liveText = r.live_count !== null ? r.live_count : "—";
      const viabText = r.viability !== null ? r.viability + "%" : "—";

      tr.innerHTML = `
        <td><img class="thumb-img" src="${thumbUrl}" alt="${escapeHtml(r.sample_id)}" loading="lazy"></td>
        <td class="filename-cell">${escapeHtml(r.sample_id)}</td>
        <td><span class="cell-count">${totalText}</span></td>
        <td><span class="cell-count text-teal">${liveText}</span></td>
        <td><span class="cell-count">${viabText}</span></td>
        <td><span class="status-badge done">Done</span></td>
        <td><button class="btn-view" onclick="openViewer(${i})">👁️ View</button></td>
      `;
    }

    resultsBody.appendChild(tr);
  });

  // Show results section
  resultsSection.classList.remove("section-hidden");
  resultsSection.classList.add("section-visible");

  // Re-enable upload for more images
  countBtn.disabled = false;
}

function animateCount(elementId, target, suffix = "") {
  const el = document.getElementById(elementId);
  if (!el) return;
  const duration = 1000;
  const start = performance.now();
  const startVal = 0;

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(startVal + (target - startVal) * eased);
    el.textContent = current.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

// ── Image Viewer ───────────────────────────────────────────────

function openViewer(index) {
  const r = state.results[index];
  if (!r || r.status === "error") return;

  const viewerTitle = $("#viewerTitle");
  const viewerOriginal = $("#viewerOriginal");
  const viewerProcessed = $("#viewerProcessed");
  const viewerRightLabel = $("#viewerRightLabel");
  const viewerStats = $("#viewerStats");
  const viewerToggle = $("#viewerToggle");

  viewerTitle.textContent = "Sample: " + r.sample_id;

  // Build stats
  viewerStats.innerHTML = `
    <div class="stat-item">
      <span class="stat-value text-mono">${r.total_count !== null ? r.total_count : "—"}</span>
      <span class="stat-label">Total Cells</span>
    </div>
    <div class="stat-item">
      <span class="stat-value text-mono text-teal">${r.live_count !== null ? r.live_count : "—"}</span>
      <span class="stat-label">Live Cells</span>
    </div>
    <div class="stat-item">
      <span class="stat-value text-mono">${r.viability !== null ? r.viability + "%" : "—"}</span>
      <span class="stat-label">Viability</span>
    </div>
  `;

  // Determine initial state
  let currentType = r.brightfield ? "brightfield" : "fluorescence";
  let currentView = "annotated";

  // Build toggle buttons dynamically
  let toggleHtml = "";
  if (r.brightfield) {
    toggleHtml += `<button class="toggle-btn" data-type="brightfield" data-view="original">BF Original</button>`;
    toggleHtml += `<button class="toggle-btn" data-type="brightfield" data-view="annotated">BF Annotated</button>`;
    toggleHtml += `<button class="toggle-btn" data-type="brightfield" data-view="debug">BF Mask</button>`;
  }
  if (r.fluorescence) {
    toggleHtml += `<button class="toggle-btn" data-type="fluorescence" data-view="original">FL Original</button>`;
    toggleHtml += `<button class="toggle-btn" data-type="fluorescence" data-view="annotated">FL Annotated</button>`;
    toggleHtml += `<button class="toggle-btn" data-type="fluorescence" data-view="debug">FL Mask</button>`;
  }
  viewerToggle.innerHTML = toggleHtml;

  const toggleBtns = $$(".toggle-btn");

  function updateViewerImage() {
    const imgData = r[currentType];
    if (!imgData) return;

    viewerOriginal.src = imgData.original_url;

    if (currentView === "original") {
      viewerProcessed.src = imgData.original_url;
      viewerRightLabel.textContent = currentType === "brightfield" ? "Bright-Field (Original)" : "Fluorescence (Original)";
    } else if (currentView === "annotated") {
      viewerProcessed.src = imgData.annotated_url;
      viewerRightLabel.textContent = currentType === "brightfield" ? "Bright-Field (Annotated)" : "Fluorescence (Annotated)";
    } else if (currentView === "debug") {
      viewerProcessed.src = imgData.debug_url;
      viewerRightLabel.textContent = currentType === "brightfield" ? "Bright-Field (Mask)" : "Fluorescence (Mask)";
    }

    toggleBtns.forEach(btn => {
      if (btn.dataset.type === currentType && btn.dataset.view === currentView) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  // Bind clicks
  toggleBtns.forEach((btn) => {
    btn.onclick = () => {
      currentType = btn.dataset.type;
      currentView = btn.dataset.view;
      updateViewerImage();
    };
  });

  // Set initial state
  updateViewerImage();

  // Show viewer
  viewerSection.classList.remove("section-hidden");
  viewerSection.classList.add("section-visible");
  viewerSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Close viewer
$("#viewerClose").addEventListener("click", () => {
  viewerSection.classList.add("section-hidden");
  viewerSection.classList.remove("section-visible");
});

// ── Downloads ──────────────────────────────────────────────────

$("#downloadCsvBtn").addEventListener("click", () => {
  if (state.results.length === 0) {
    showToast("No results to download.", "error");
    return;
  }
  window.location.href = "/api/download/csv";
  showToast("CSV download started.", "success");
});

$("#downloadZipBtn").addEventListener("click", () => {
  if (state.results.length === 0) {
    showToast("No results to download.", "error");
    return;
  }
  window.location.href = "/api/download/zip";
  showToast("ZIP download started.", "success");
});

$("#clearBtn").addEventListener("click", async () => {
  if (!confirm("Are you sure you want to clear the current batch? Make sure you downloaded your results first!")) return;
  
  try {
    await fetch("/api/results", { method: "DELETE" });
    
    state.files = [];
    state.results = [];
    
    // Reset UI
    uploadZone.classList.remove("has-files");
    countBtn.disabled = true;
    renderFileStrip();
    resultsSection.classList.add("section-hidden");
    resultsSection.classList.remove("section-visible");
    
    showToast("Workspace cleared for new batch.", "success");
  } catch (err) {
    showToast("Error clearing workspace.", "error");
  }
});

// ── Toast Notifications ────────────────────────────────────────

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.style.animation = "slideOutRight 0.3s ease forwards";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── Utilities ──────────────────────────────────────────────────

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ── Keyboard Shortcuts ─────────────────────────────────────────
document.addEventListener("keydown", (e) => {
  // Escape closes viewer
  if (e.key === "Escape") {
    viewerSection.classList.add("section-hidden");
    viewerSection.classList.remove("section-visible");
  }
});
