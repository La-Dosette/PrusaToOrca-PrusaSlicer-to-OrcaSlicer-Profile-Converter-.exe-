# GitHub Update Copy

## Repository Short Description

Windows GUI tool to convert PrusaSlicer `.ini` config bundles into safer OrcaSlicer `.orca_printer` import bundles.

## README Header / Project Intro

# PrusaToOrca

**PrusaSlicer to OrcaSlicer profile converter**

PrusaToOrca is a Windows desktop app that converts PrusaSlicer config bundles (`.ini`) into OrcaSlicer import bundles (`.orca_printer`).

The app is designed around a safer workflow:

**Preview first -> Generate second -> Import manually into OrcaSlicer**

PrusaToOrca does not directly edit existing OrcaSlicer preset files. It generates a new bundle that you can review before importing.

Always back up your OrcaSlicer profiles before importing converted profiles.

## GitHub Release Title

PrusaToOrca v0.2.0 - Safer imports, improved UI, reports, mapping, and multilingual support

## GitHub Release Notes

## 🔄 PrusaToOrca v0.2.0

This release focuses on safety, clarity, and a cleaner user experience.

The main workflow is now:

**Preview first → Generate second → Import manually into OrcaSlicer**

PrusaToOrca does not directly edit existing OrcaSlicer preset files. It creates a new `.orca_printer` bundle that can be reviewed and imported manually through OrcaSlicer.

### 🛡️ Safety and import behavior

- Added safer non-destructive conversion workflow
- Added preview before generating files
- Added prefixing by default to reduce preset name collisions
- Added strict / loose compatibility modes
- Added risk scoring for possible OrcaSlicer preset name collisions
- Existing OrcaSlicer preset files are not edited by the app

### 📊 Reports and review tools

- Added Simple Summary tab for normal users
- Improved Advanced Report
- Added filters for converted, approximate, and ignored settings
- Added per-section coverage information
- Added CSV report export
- Added HTML report export
- Added simple PDF report export
- Added anonymized bug report export

### 🧩 Mapping and troubleshooting

- Added Mapping editor for ignored PrusaSlicer keys
- Added conversion history with report snapshots
- Added copy debug/version info
- Added GitHub release update check
- Added Info / Help tab explaining the main settings

### 🐳 OrcaSlicer workflow

- Added OrcaSlicer import assistant after generation
- Added copy generated file path action
- Added open output folder action
- Clearer recommended import flow:
  1. Back up OrcaSlicer profiles
  2. Preview conversion
  3. Generate `.orca_printer`
  4. Import manually in OrcaSlicer

### 🌍 Interface and usability

- Added day / night theme
- Added interface languages: FR, EN, DE, ES, IT, PT, NL, PL
- Improved window sizing and centering on Windows
- Improved layout behavior on smaller screens
- Cleaned up the toolbar
- Moved support actions into a Tools window
- Fixed source panel button clipping in translated UI

### 📦 Windows build

- Rebuilt the Windows executable
- Release file:

`PrusaToOrca-v0.2.0.exe`

### Notes

This project is still young, and slicer profile conversion can be complex. Some settings convert exactly, some are approximate, and some may need manual review.

Please back up your OrcaSlicer profiles before importing converted profiles.

If something does not convert correctly, please export a report or generate an anonymized bug report from the app.

## GitHub Pinned Issue / Discussion Post

## PrusaToOrca v0.2.0 update

This update makes the app safer and easier to understand.

The converter now follows a preview-first workflow and generates a new `.orca_printer` bundle instead of editing existing OrcaSlicer preset files directly.

Main additions:

- 🛡️ safer non-destructive workflow
- 👀 preview before generating files
- 📊 improved reports
- 🧾 simple summary tab
- 🧩 mapping editor
- 🐳 OrcaSlicer import assistant
- 🕘 conversion history
- 🌍 FR / EN / DE / ES / IT / PT / NL / PL interface
- 🌗 day / night theme
- ℹ️ Info / Help tab
- 🪟 improved Windows layout and centering

Backups are still recommended before importing converted profiles.
