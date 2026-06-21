# PrusaToOrca Patch Notes

## Cleanup Pass

This pass focuses on making the app feel cleaner, less noisy, and more reliable
without removing core functionality.

### Interface Cleanup

- Removed duplicate top-bar shortcuts for Advanced Report and Debug Info.
- Kept the top bar focused on live state: Safe, Prefix, Compatibility, Theme,
  Language, and History.
- Replaced four secondary buttons with a compact Tools window.
- Renamed the output-folder button from Open to Folder for clarity.
- Kept Mapping visible because it is part of the conversion workflow.
- Reordered the left panel so Preview and Generate are visible in the first
  viewport at the default window size.
- Removed duplicated compatibility/prefix controls from the Output panel because
  those states already live in the top toolbar.
- Added a visible language selector with FR, EN, DE, ES, IT, PT, NL, and PL.
- Localized the main workflow, report tabs, advanced report controls, assistant,
  mapping editor, tools, history, and export messages.
- Added shared window sizing/centering so the main app and secondary windows open
  in a sensible position on the active Windows screen.
- Added a scrollable left workflow column so small screen heights do not hide
  the Preview, Generate, or Output controls.
- Completed translation key coverage for supported languages to avoid accidental
  English fallbacks in visible controls and messages.

### Tools Window

- Added one place for support and maintenance actions:
  - OrcaSlicer guide
  - Check updates
  - Bug report export
  - Copy debug info

### Bug Fixes

- Fixed history snapshots so they store the exact report data from the current
  conversion, instead of depending on UI timing.
- Removed unused imports and a dead report-formatting method.
- Verified theme rebuild still closes and recreates secondary windows cleanly.

### Validation

- Python compilation passed.
- Unit tests passed.
- Translation key coverage check passed for FR, EN, DE, ES, IT, PT, NL, and PL.
- Tkinter smoke test passed for Simple Summary, Import Assistant, and Tools.
- Tkinter window smoke test passed for main and child window sizing/centering.
- Windows executable was rebuilt successfully.
