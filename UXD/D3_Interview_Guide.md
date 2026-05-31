# Cell Counter — UX Redesign Project
## D3 · User Research — Hear Phase
### Interview Guide & Responses

**CEN 5728 · User Experience Design**
**University of Florida · Spring 2026**

**Student:** Vishnu Sai Padyala
**Interface:** Cell Counter Web Application (BlueberryLab UF)
**Platform:** Web (Desktop Browser) — localhost:5000

---

## Interface Goal

The goal of the Cell Counter application is to allow lab technicians to upload microscope images (bright-field and fluorescence), automatically count total cells and live cells, calculate viability percentages, and export clean data — replacing the manual hemocytometer and ImageJ workflow entirely.

## Design Challenge

Evaluate and improve the cell counting workflow for yeast fermentation labs by designing an automated, web-based tool that eliminates manual counting, reduces human error, and provides instant visual verification of results.

## User Research Focus Statement

We want to understand how lab technicians currently perform cell counting tasks, what pain points they experience with existing tools (hemocytometer, ImageJ, Excel), and what features they need in an automated system — in order to design a cell counting interface that is fast, accurate, and requires zero training.

---

## Interview Goals

1. Technicians' current cell counting habits and daily workflow
2. How technicians interact with the hemocytometer and microscope during counting
3. How technicians use ImageJ or other software for image-based counting
4. What data recording and export practices technicians follow
5. Problems, frustrations, and time sinks experienced during counting
6. How technicians perform live/dead viability assessments with fluorescence
7. What an ideal cell counting tool would look like from the technician's perspective
8. How the existing workflow compares to automated alternatives they have seen or heard about

**Total Participants:** 4 lab workers (2 senior technicians + 1 graduate researcher + 1 lab manager)

---

## Interview Guide

### Section 1 — Warm-Up / Background
**Purpose:** Build rapport and understand the participant's role in the lab.

- What is your role in the lab, and how long have you been working here?
- How often do you perform cell counting tasks — daily, weekly, or only during specific experiments?
- Can you briefly describe a typical day in the lab when cell counting is involved?

### Section 2 — Current Cell Counting Methods
**Purpose:** Understand baseline workflow and tool usage.

- Walk me through the last time you counted cells. What was the process from start to finish?
  - What tools did you use? (hemocytometer, microscope, ImageJ, tally counter, etc.)
  - How long did the entire process take?
  - Did you count alone or with a colleague?
- How do you typically prepare the sample before counting? (dilution, staining, etc.)
- Do you use the same method every time, or does it change depending on the experiment?

### Section 3 — Pain Points & Frustrations
**Purpose:** Surface usability issues and emotional responses to the current workflow.

- What is the most frustrating part of counting cells?
  - Can you describe a specific time when something went wrong?
- Have you ever had to redo a count? What caused it?
- Do you trust the accuracy of your manual counts? Why or why not?
- Is there a part of the process where you feel you waste the most time?

### Section 4 — Data Recording & Export
**Purpose:** Identify issues in how results are documented and shared.

- After you finish counting, how do you record the results? (notebook, Excel, shared drive, etc.)
- Have you ever made a data entry error? How did you discover it?
- How do you share results with your supervisor or PI?
- What format do you wish the final data was in?

### Section 5 — Image Analysis Experience
**Purpose:** Gauge familiarity and comfort with software-based counting.

- Have you used ImageJ or FIJI for cell counting? If yes, describe your experience.
  - How long does it take to process one image?
  - What settings do you typically adjust? (threshold, particle size, etc.)
- Have you tried any other automated counting tools? What was your experience?
- What would make software-based counting easier for you?

### Section 6 — Fluorescence & Viability Workflow
**Purpose:** Understand the live/dead counting process and its challenges.

- Do you perform viability assessments? How often?
- Walk me through how you distinguish live cells from dead cells.
  - What dye or staining method do you use? (Trypan Blue, fluorescent dyes, etc.)
  - Do you count live and dead cells at the same time, or separately?
- How do you calculate viability percentage? (mental math, Excel formula, etc.)
- What is the hardest part of viability counting?

### Section 7 — Ideal Tool Features
**Purpose:** Capture user-driven ideas for the redesigned system.

- If you could design the perfect cell counting tool, what would it do?
- What features would save you the most time?
- Would you prefer a desktop application, a web app, or a physical device?
- How important is it to see the annotated image showing where each cell was detected?

### Section 8 — Closing
**Purpose:** Give the participant space to add anything not covered.

- Is there anything else about your cell counting experience that you would like to share?
- Are there any questions you expected me to ask that I did not?

*Interviewer: "Thank you for your time. We really appreciate your help."*

---

---

## Completed Interview Responses

### Participant 1 — Maria (Senior Lab Technician, 4 years experience)

**Background:** Maria is a senior technician at BlueberryLab UF who processes 15-25 samples per day during active fermentation experiments. She has been counting cells manually since her first day in the lab.

**Current Method:** "I use the hemocytometer every single day. I load the chamber, put it under the microscope at 40×, and count all four corner squares. I click the tally counter for each cell. Then I average the four counts, multiply by 10,000, and multiply by my dilution factor. I type everything into Excel at the end of the day."

**Pain Points:** "The worst part is when I lose count in the middle of a quadrant. If someone talks to me or I sneeze, I have to start that entire quadrant over. And with 20 samples, that happens at least 3-4 times a day. I also hate the arithmetic — I've caught myself entering wrong dilution factors in Excel at least twice this semester."

**Data Recording:** "I write counts in my lab notebook first, then type them into a shared Excel sheet on the lab drive. Last month I accidentally typed 1.2 × 10⁶ instead of 1.2 × 10⁷ — off by a factor of 10. My PI caught it a week later when the growth curve looked weird."

**ImageJ Experience:** "I tried ImageJ once during my training. The instructor showed me how to set thresholds and run 'Analyze Particles.' But when I tried it on my own images, the threshold was completely different because the lighting was different. I spent 45 minutes trying to get it to work and then gave up and went back to manual counting."

**Viability:** "For viability, I mix the sample with Trypan Blue, load a fresh chamber, and count blue cells separately from clear cells. It literally doubles my counting time. And sometimes it's hard to tell if a cell is light blue or actually clear — the color is very subjective."

**Ideal Tool:** "I want to drag a folder of images in, press one button, and get a CSV with all my counts. I don't want to touch any settings. And I want to see the image with circles around the cells so I can check if it's right."

---

### Participant 2 — James (Graduate Researcher, 2 years experience)

**Background:** James is a second-year master's student researching yeast fermentation kinetics. He counts cells 2-3 times per week as part of his growth curve experiments.

**Current Method:** "I capture images on the microscope camera and then try to process them in ImageJ. I convert to 8-bit, adjust the threshold manually until the cells look right, apply watershed to separate clusters, then run Analyze Particles. Each image takes about 8-10 minutes."

**Pain Points:** "The threshold is different for literally every image. Even images from the same batch — if the microscope light shifts slightly, the entire threshold is wrong. I've had batches where half the images needed completely different settings. And ImageJ's watershed algorithm absolutely destroys my images when cells are overlapping — it splits one cell into three pieces. I've also lost entire analysis sessions because I accidentally closed the results window and there's no undo."

**Data Recording:** "I save the ImageJ results as a CSV, then copy-paste into my master Excel workbook. The column names from ImageJ are things like 'Area' and 'Circ.' which I have to rename every time. I've definitely had paste-alignment errors where counts shifted one row."

**Fluorescence:** "I use a green fluorescent stain for viability. The problem is ImageJ's threshold is even worse on fluorescence images — the background is completely black except for the glowing dots, so the threshold slider is super sensitive. One pixel of adjustment changes the count by 20-30 cells."

**Ideal Tool:** "Honestly, I just want something that automatically knows the difference between a bright-field image and a fluorescence image and processes them correctly without me configuring anything. And batch processing — I should be able to drop 40 images and come back to a finished table."

---

### Participant 3 — Priya (Lab Technician, 1 year experience)

**Background:** Priya joined the lab last year and was trained on the hemocytometer by Maria. She primarily handles the daily quality control samples.

**Current Method:** "Maria trained me on the hemocytometer. I have a printed protocol card taped to the microscope bench. I follow it step by step: load 10 µL, focus at 40×, count the 4 corner squares, write down each number, calculate the average, multiply by 10⁴ and by the dilution. But honestly, I still get confused about the boundary rule — which cells on the line count and which don't."

**Pain Points:** "The boundary rule is my biggest confusion. My protocol card says 'count cells touching the top and left lines, skip cells touching the bottom and right lines.' But under the microscope, it's really hard to tell if a cell is touching a line or just very close to it. I've compared my counts with Maria's on the same sample, and we're sometimes 20% apart."

**Data Recording:** "I write everything in my lab notebook and then Maria enters it into Excel because she's faster with the formulas. I feel bad about that — I wish I could just generate the spreadsheet myself."

**ImageJ Experience:** "I've never used ImageJ. Maria said it was too complicated and not worth learning for our workflow. But I've seen James use it and it looks intimidating — there are so many menus."

**Viability:** "I've only done viability counting a few times. It takes me almost twice as long as regular counting because I have to keep track of two separate numbers — blue and clear — and I get confused which tally counter is for which."

**Ideal Tool:** "Something simple. Like, really simple. I should be able to use it on my first day without anyone teaching me. Just upload images and get numbers. No complicated settings, no formulas, no arithmetic."

---

### Participant 4 — Dr. Chen (Lab Manager / PI, 12 years experience)

**Background:** Dr. Chen oversees the fermentation lab. He does not count cells himself but reviews all data submitted by technicians and makes process decisions based on the counts.

**Current Method:** "I review the Excel spreadsheets my technicians submit. I look at growth curves, viability trends, and pitch rates. I occasionally spot-check a count by looking at an annotated image if one is available."

**Pain Points:** "My biggest problem is data inconsistency. When Maria counts, she consistently gets numbers about 10% higher than Priya on the same samples. James's ImageJ counts are in a completely different range — sometimes higher, sometimes lower, with no pattern. I've spent hours trying to normalize between operators. The other issue is timeliness — by the time I get the Excel file, the fermentation may have progressed past the decision point. I need counts within 30 minutes of sampling, not 4 hours later."

**Data Recording:** "I get an Excel file at the end of each day. The format varies depending on who filled it out. Maria's sheets have different column headers than James's ImageJ exports. I've asked them all to use a standard template, but it never sticks."

**Fluorescence:** "Viability data is critical for my decisions, but it arrives even later than total counts because it's a separate protocol. I need total and viability in a single report, not two separate spreadsheets."

**Ideal Tool:** "I want one system that all my technicians use, so I get consistent data regardless of who is operating it. The system should eliminate operator variability entirely. And I want a single CSV with sample ID, total count, live count, and viability — all in one file, not scattered across notebooks and spreadsheets. Oh, and if I could see the annotated images to spot-check, that would eliminate 90% of my data trust issues."

---

## Key Themes from Interviews

| Theme | Evidence |
|-------|----------|
| **Time sink** | Maria: 3-4 hours for 20 samples; James: 8-10 min per image in ImageJ |
| **Operator variability** | Dr. Chen: 10% systematic difference between Maria and Priya |
| **Error-prone arithmetic** | Maria: entered wrong dilution factor; Priya: confused by boundary rules |
| **Tool fragmentation** | 4 separate tools (hemocytometer, microscope, ImageJ/Excel) with no integration |
| **ImageJ complexity** | James: threshold varies per image; Priya: "too intimidating" |
| **Viability doubles workload** | Maria: separate chamber, separate count, separate calculation |
| **Data format inconsistency** | Dr. Chen: different column headers per operator |
| **Zero batch processing** | All: 1-by-1 processing, no folder upload capability |
| **Need for visual verification** | Maria: "I want to see circles around the cells"; Dr. Chen: "spot-check annotated images" |
| **Zero-training requirement** | Priya: "I should be able to use it on my first day" |
