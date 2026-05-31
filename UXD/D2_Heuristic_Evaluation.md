# Cell Counter — UX Redesign Project
## D2 · Heuristic Evaluation
### Nielsen's 10 Usability Heuristics — Traditional Cell Counting Methods

**CEN 5728 · User Experience Design**
**University of Florida · Spring 2026**

**Student:** Vishnu Sai Padyala
**Interface:** Traditional Lab Cell Counting Workflow (Hemocytometer + ImageJ + Manual Tally)
**Platform:** Physical Lab Equipment + Desktop Software

---

## Evaluation Method

**Method:** Nielsen's 10 Usability Heuristics
**Goal:** Identify usability issues in the traditional cell counting workflow used by lab technicians at BlueberryLab UF before the automated Cell Counter application was developed.

**Focus Areas:**
- Sample preparation and hemocytometer loading
- Manual counting under the microscope
- Digital counting with ImageJ/FIJI
- Data recording and export
- Fluorescence viability assessment

---

## The "Before" State — How Lab Technicians Counted Cells

Before the Cell Counter application, lab technicians at BlueberryLab UF relied on a fragmented, multi-tool workflow to count yeast cells. The process typically involved:

1. **Hemocytometer + Manual Eye Counting:** Technicians loaded a diluted cell suspension onto a Neubauer hemocytometer chamber, placed it under a 40× bright-field microscope, and physically counted cells in each of the four corner squares by clicking a hand tally counter. They then averaged the four counts and multiplied by the dilution factor (×10⁴) to estimate cells/mL.

2. **ImageJ / FIJI (Desktop Software):** Some technicians captured microscope images and opened them in ImageJ, a free open-source image analysis tool. They manually adjusted threshold sliders, ran "Analyze Particles," and then manually reviewed false positives. Each image required 5-10 minutes of parameter tuning.

3. **Trypan Blue + Manual Viability:** For live/dead discrimination, technicians mixed the sample with Trypan Blue dye, loaded a fresh hemocytometer, and counted blue (dead) vs. clear (live) cells separately — effectively doubling the counting workload.

4. **Excel Spreadsheets:** All counts were hand-typed into Excel. Formulas for viability percentage were manually entered. Copy-paste errors and formula drift were common.

---

## H1 — Visibility of System Status

**Issue:** When counting cells manually through the eyepiece, there is absolutely no system feedback. The technician has no indication of how many cells they have counted, how many quadrants remain, or whether they accidentally double-counted a cell. The tally counter only shows a raw number with no context. In ImageJ, the "Analyze Particles" function runs silently and dumps a results table with no visual overlay until the user manually enables it.

**UX Concept:** Users need continuous, real-time feedback about the current state of the system to feel confident in their actions and progress.

**Impact:** Technicians frequently lose track of which quadrant they are counting, leading to recounts that waste 10-15 minutes per sample. In ImageJ, technicians cannot tell if the threshold was set correctly until after processing completes and they manually inspect every detected contour.

**Recommendation:** Provide a real-time progress indicator showing which sample and quadrant is being processed, with a live count overlay directly on the image. The Cell Counter app addresses this with an animated progress bar, live metric cards, and instant annotated image overlays showing exactly where each cell was detected.

---

## H2 — Match Between System and the Real World

**Issue:** ImageJ speaks the language of image processing engineers, not biologists. Menu items like "Process → Binary → Watershed," "Analyze → Set Measurements → Feret's Diameter," and threshold histograms with 256-bin displays do not match the mental model of a lab technician who simply wants to know "how many cells are in this image." The hemocytometer grid layout (with its nested sub-squares and ruling lines) requires memorizing which lines count as "in" vs. "out" boundaries — an arbitrary convention that varies between textbooks.

**UX Concept:** The system should speak the user's language, using familiar terms, concepts, and conventions rather than system-oriented jargon.

**Impact:** New technicians require 2-3 hours of training just to understand ImageJ's interface. Hemocytometer boundary rules cause systematic over- or under-counting by 10-15% among untrained users.

**Recommendation:** Use domain-specific but simple language: "Total Cells," "Live Cells," "Viability %." Hide all image processing parameters behind intelligent defaults. The Cell Counter app uses a single drag-and-drop interface with zero configuration — no thresholds, no particle size settings, no binary conversions.

---

## H3 — User Control and Freedom

**Issue:** In ImageJ, if a technician accidentally closes the results window, all counted data is lost with no undo. If they set the wrong threshold and run analysis, they must start the entire pipeline over — reopen the image, reconvert to 8-bit, reapply threshold, re-run watershed, re-analyze particles. There is no "back" button in the analysis pipeline. With the hemocytometer, if you lose count mid-quadrant, the only option is to start that quadrant from zero.

**UX Concept:** Users frequently choose system functions by mistake and need a clearly marked "emergency exit" to leave the unwanted state without having to go through an extended dialogue.

**Impact:** A single mistake in ImageJ can cost 5-10 minutes of rework. Technicians report losing entire analysis sessions because of accidental window closures. This is especially frustrating during time-sensitive fermentation monitoring where dozens of samples must be processed quickly.

**Recommendation:** Provide non-destructive processing with the ability to re-view, re-export, and clear results at any time. The Cell Counter app stores all results in-session, allows re-viewing any sample via the "View" button, and provides a deliberate "Clear / New Batch" button that only resets when the user explicitly chooses to.

---

## H4 — Consistency and Standards

**Issue:** The traditional workflow uses three completely different interfaces: a physical hemocytometer viewed through an eyepiece, ImageJ on a desktop computer, and Excel for data recording. Each tool has its own interaction paradigm, its own way of displaying numbers, and its own export format. Even within ImageJ, the particle analyzer settings dialog uses different units (pixels vs. microns) depending on whether calibration was set — and there is no indication of which unit is active. Technicians switching between bright-field counting and fluorescence viability counting must use entirely different protocols with different dyes, different microscope settings, and different Excel templates.

**UX Concept:** Users should not have to wonder whether different words, situations, or actions mean the same thing. Follow platform conventions.

**Impact:** Technicians maintain separate SOPs (Standard Operating Procedures) for bright-field vs. fluorescence counting, leading to confusion, protocol mix-ups, and inconsistent data formats across lab notebooks.

**Recommendation:** Unify the entire workflow into a single, consistent interface where both bright-field and fluorescence images are processed through the same drag-and-drop upload, the same results table, and the same CSV export. The Cell Counter app automatically detects image type from the filename and routes to the appropriate algorithm — the technician never needs to switch modes.

---

## H5 — Error Prevention

**Issue:** The hemocytometer workflow is error-prone by design: technicians must mentally track boundary rules, remember dilution factors, and perform arithmetic (count × 10⁴ ÷ dilution) by hand or in Excel. There is no safeguard against entering the wrong dilution factor, miscounting a quadrant, or loading a contaminated chamber. In ImageJ, it is trivially easy to analyze the wrong image file (especially when filenames are cryptic like `IMG_20260315_142356.tif`) or apply the bright-field threshold to a fluorescence image.

**UX Concept:** Even better than good error messages is a careful design which prevents a problem from occurring in the first place.

**Impact:** Published studies estimate that manual hemocytometer counting has a coefficient of variation (CV) of 15-20% between operators. In a fermentation lab processing 20+ samples per day, this error propagation can lead to incorrect pitch rates and batch failures costing thousands of dollars.

**Recommendation:** Eliminate manual arithmetic entirely. Auto-detect image type from filename conventions. Prevent mismatched processing by automatically pairing bright-field and fluorescence images by sample ID. The Cell Counter app does all of this — the technician simply drops a folder and clicks one button.

---

## H6 — Recognition Rather Than Recall

**Issue:** ImageJ requires users to remember optimal threshold values, minimum particle sizes, and circularity ranges from previous sessions. These parameters are not saved between sessions and must be re-entered each time. With the hemocytometer, technicians must recall the counting protocol from memory: which squares to count, which boundary rule to apply, and what dilution factor was used — often hours after the sample was prepared. There is no visual reminder of the protocol steps.

**UX Concept:** Minimize the user's memory load by making objects, actions, and options visible. The user should not have to remember information from one part of the dialogue to another.

**Impact:** Technicians who have not counted in several weeks frequently make protocol errors. New lab members require a printed protocol card taped to the microscope bench — which inevitably gets stained, torn, or lost.

**Recommendation:** Eliminate all parameters that require memorization. Use intelligent defaults calibrated to the specific microscope and camera setup. Display all results inline with visual confirmation (annotated images showing exactly what was counted). The Cell Counter app requires zero parameter recall — every processing decision is automatic and visually verifiable.

---

## H7 — Flexibility and Efficiency of Use

**Issue:** The traditional workflow offers no shortcuts for experienced users. Whether a technician has counted 10 samples or 10,000 samples, the process is identical: load chamber → focus microscope → count four quadrants → record numbers → calculate. There is no batch processing capability. ImageJ technically supports macros, but writing ImageJ macros requires Java-like scripting knowledge that no lab technician possesses. Processing 20 images in ImageJ means opening each one individually, 20 separate times.

**UX Concept:** Accelerators — unseen by the novice user — may often speed up the interaction for the expert user such that the system can cater to both inexperienced and experienced users.

**Impact:** A trained technician processing a 21-sample fermentation batch spends approximately 3-4 hours on manual counting alone. This is time that could be spent on higher-value analytical work.

**Recommendation:** Support batch processing — upload an entire folder of 42 images (21 bright-field + 21 fluorescence pairs) and process them all in a single click. The Cell Counter app processes a full batch in under 2 minutes, reducing a 4-hour task to a coffee break.

---

## H8 — Aesthetic and Minimalist Design

**Issue:** ImageJ's interface is notoriously cluttered. The main toolbar contains 36 small, cryptic icons. The menu bar has 9 top-level menus containing hundreds of sub-options, the vast majority of which are irrelevant to cell counting. The "Analyze Particles" dialog alone has 12 input fields. The hemocytometer, while physically elegant, provides no visual hierarchy — all grid lines look identical, making it difficult to distinguish counting squares from structural lines under the microscope.

**UX Concept:** Dialogues should not contain information which is irrelevant or rarely needed. Every extra unit of information competes with the relevant units of information and diminishes their relative visibility.

**Impact:** Technicians report feeling "overwhelmed" when first opening ImageJ. The cognitive load of filtering relevant from irrelevant options slows down even experienced users and increases the probability of selecting the wrong menu item.

**Recommendation:** Present only what the technician needs: an upload zone, a count button, a results table, and a download button. Hide all image processing complexity behind the scenes. The Cell Counter app has exactly 4 interface elements visible at any time, compared to ImageJ's 100+.

---

## H9 — Help Users Recognize, Diagnose, and Recover from Errors

**Issue:** When ImageJ's particle analyzer produces an obviously wrong count (e.g., 3 cells when there are clearly 50+), the error message is nonexistent. The system simply reports the wrong number with full confidence. There is no diagnostic information about why the count is low (threshold too high? minimum area too large? image not converted to binary?). With the hemocytometer, if a technician realizes their count seems wrong, there is no way to diagnose the error — they must simply recount from scratch.

**UX Concept:** Error messages should be expressed in plain language (no codes), precisely indicate the problem, and constructively suggest a solution.

**Impact:** Technicians often do not realize a count is wrong until it is compared with other samples days later during data analysis. By then, the original sample may have been discarded, making recounting impossible.

**Recommendation:** Provide visual verification alongside every count — annotated images with circles drawn around every detected cell, plus debug mask views showing exactly what the algorithm "sees." The Cell Counter app provides three views per image (Original, Annotated, Mask) so technicians can instantly verify accuracy.

---

## H10 — Help and Documentation

**Issue:** ImageJ documentation exists as a sprawling wiki with thousands of pages written for developers and advanced researchers, not lab technicians. Finding "how to count cells" requires navigating through pages about Java plugins, macro syntax, and image processing theory. The hemocytometer has no built-in documentation — users rely on YouTube videos and lab protocol binders that may be outdated or specific to a different model of counting chamber.

**UX Concept:** Even though it is better if the system can be used without documentation, it may be necessary to provide help and documentation. Any such information should be easy to search, focused on the user's task, list concrete steps, and not be too large.

**Impact:** New lab members spend 2-3 days learning the counting workflow through trial and error, peer mentoring, and outdated protocol documents. This onboarding cost is repeated every time a new student joins the lab.

**Recommendation:** Design the system to be self-explanatory with no documentation required. For edge cases, provide a simple one-page run guide. The Cell Counter app includes a [Cell Count Run Guide](file:///v:/MASTER'S/cell%20counter%202.0/Cell_Count_Run_Guide.md) that covers the entire workflow in 5 numbered steps that can be read in under 2 minutes.

---

## Conclusion

### Key Usability Issues Identified
- **No system feedback** during manual counting or ImageJ processing
- **Jargon-heavy interfaces** that do not match the technician's mental model
- **No undo/recovery** for lost counts or wrong parameters
- **Fragmented workflow** across 3-4 separate tools with inconsistent paradigms
- **Zero error prevention** — manual arithmetic, wrong thresholds, and mismatched files are all trivially easy
- **No batch processing** capability, forcing repetitive 1-by-1 workflows
- **Cluttered interfaces** (ImageJ) competing with critical information
- **No visual verification** of counting accuracy

### Overall Impact
- 15-20% coefficient of variation between operators
- 3-4 hours per batch of 21 samples
- 2-3 days onboarding time for new lab members
- Frequent data entry errors in Excel spreadsheets
- Inconsistent protocols between bright-field and fluorescence workflows

### Final Recommendations
1. Unify the entire workflow into a single web-based interface
2. Automate all image processing with intelligent defaults
3. Provide instant visual verification with annotated overlays
4. Support batch processing with automatic image pairing
5. Export clean, error-free CSV files with zero manual data entry
6. Design for zero-configuration — no thresholds, no parameters, no training required

**Goal:** Transform a fragmented, error-prone, 4-hour manual process into a 2-minute automated workflow that any lab technician can operate on their first day.
