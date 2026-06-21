# Printables Update Post

Model page:
https://www.printables.com/model/1650340-prusatoorca-prusaslicer-to-orcaslicer-profile-conv

## Suggested Update Title

Major safety and UI update - PrusaToOrca v0.2.0

## Suggested Model Description Add-On

### Update - v0.2.0

PrusaToOrca has received a major safety and usability update.

The workflow is now intentionally conservative: **Preview first, Generate second**. The app does not directly modify existing OrcaSlicer preset files. It generates a new `.orca_printer` bundle that you can review and manually import into OrcaSlicer.

Please still back up your OrcaSlicer profiles before importing converted profiles. This tool is designed to make the process safer and easier to understand, but slicer profiles are important user data.

Highlights:

- Safer non-destructive conversion flow
- Simple summary for normal users
- Advanced report for technical review
- Mapping editor for ignored keys
- OrcaSlicer import assistant
- Conversion history
- CSV, HTML, and PDF report export
- Day / night mode
- Interface languages: FR, EN, DE, ES, IT, PT, NL, PL
- Better Windows window sizing and layout
- New Info / Help tab explaining the settings

If something does not convert correctly, please share the generated report or use the anonymized bug report export. That makes it much easier to improve mappings safely.

## Short Comment Version

Hi everyone,

New update for the PrusaToOrca model page:
https://www.printables.com/model/1650340-prusatoorca-prusaslicer-to-orcaslicer-profile-conv

PrusaToOrca has received a major cleanup and safety update.

The app is now built around a safer workflow: **Preview first, Generate second**. It does **not** directly modify existing OrcaSlicer preset files. Instead, it generates a new `.orca_printer` bundle that you can manually import into OrcaSlicer.

Main changes:

- Safer non-destructive import flow
- Prefix enabled by default to reduce preset name collisions
- Strict / loose compatibility modes
- Simple summary for normal users
- Advanced report with converted / approximate / ignored settings
- Mapping editor for ignored keys
- OrcaSlicer import assistant
- Conversion history
- Export reports as CSV, HTML, or PDF
- Day / night mode
- Interface languages: FR, EN, DE, ES, IT, PT, NL, PL
- Better window sizing, centering, and layout cleanup
- New Info / Help tab explaining the settings

I also rebuilt the Windows executable and updated the release files.

Please still back up your OrcaSlicer profiles before importing any converted profile. This tool is meant to make conversion safer, but slicer profiles are important user data and backups are always recommended.

Thanks for the feedback. It genuinely helped push the project in a much cleaner direction.

## Full Update / Patch Notes Version

Hi everyone,

Thanks for the feedback on the first version of PrusaToOrca. I took the concerns seriously and made a larger update focused on safety, clarity, and a cleaner user experience.

### Important safety change

The app is now designed around a safer workflow:

1. Choose a PrusaSlicer `.ini` config bundle or a folder.
2. Run **Preview** first.
3. Review what will be converted.
4. Generate a new `.orca_printer` bundle.
5. Import that generated bundle manually in OrcaSlicer.

PrusaToOrca does **not** directly edit existing OrcaSlicer preset files. The goal is to avoid touching existing user profiles and keep the conversion process more transparent.

I still strongly recommend making a backup before importing any converted profile. Slicer profiles are important, and backups are always the safest path.

### What changed

- Added a safer preview-first workflow.
- Generated presets are prefixed by default to reduce name collision risk.
- Added strict and loose compatibility modes.
- Added risk scoring for possible OrcaSlicer preset name collisions.
- Added a non-technical **Simple Summary** tab.
- Added a detailed **Advanced Report** with converted, approximate, and ignored fields.
- Added report filters.
- Added a **Mapping editor** so ignored PrusaSlicer keys can be manually mapped to OrcaSlicer keys.
- Added an OrcaSlicer import assistant after generation.
- Added conversion history with report snapshots.
- Added CSV, HTML, and simple PDF report exports.
- Added anonymized bug report export.
- Added copy debug info.
- Added update checking from GitHub Releases.
- Added day / night theme.
- Added interface languages: French, English, German, Spanish, Italian, Portuguese, Dutch, and Polish.
- Added an Info / Help tab explaining safe mode, prefix, strict / loose compatibility, reports, and mapping.
- Improved window sizing and centering on Windows.
- Improved layout responsiveness for smaller screens.
- Fixed source panel button clipping in translated UI.
- Cleaned up the main toolbar and moved support actions into a Tools window.

### Current release

The Windows executable has been rebuilt as:

`PrusaToOrca-v0.2.0.exe`

### Note

This project is still young, and PrusaSlicer / OrcaSlicer profiles can be complex. Some settings may be exact matches, some may be approximate, and some may be ignored. The new report views are meant to make that clear before you import anything.

If something does not convert correctly, please share the report or generate an anonymized bug report from the app. That will make it much easier to improve the mapping safely.

Thanks again for testing and for the honest feedback.
