# PrusaToOrcaSlicer

<p align="center">
  <img width="96" height="96" alt="logo_header" src="https://github.com/user-attachments/assets/f4105d2d-c46b-4e49-8309-bb7b00396e9c" />
</p>

<p align="center">
  <b>PrusaSlicer &rarr; OrcaSlicer Profile Converter</b><br/>
  Drag and drop your <code>.ini</code> PrusaSlicer file and get a ready-to-import <code>.orca_printer</code>.
</p>

<p align="center">
  <a href="../../releases/latest">Download latest release</a>
  &nbsp;|&nbsp;
  <a href="CHANGELOG.md">Changelog</a>
  &nbsp;|&nbsp;
  <a href="PATCH_NOTES.md">Patch notes</a>
</p>

---

## &#128260; Update - v0.2.0

This update focuses on safety, clarity, and a cleaner interface.

The main workflow is now:

**Preview first &rarr; Generate second &rarr; Import manually into OrcaSlicer**

PrusaToOrca does not directly edit existing OrcaSlicer preset files. It generates a new `.orca_printer` bundle that can be reviewed before importing.

> Always back up your OrcaSlicer profiles before importing converted profiles.

### Main changes

- &#128737;&#65039; Safer non-destructive conversion workflow
- &#128064; Preview before generating files
- &#127991;&#65039; Prefix enabled by default to reduce name collisions
- &#128279; Strict / loose compatibility modes
- &#9888;&#65039; Risk scoring for possible OrcaSlicer preset name collisions
- &#129534; Simple summary tab
- &#128202; Improved advanced report
- &#128269; Filters for converted, approximate, and ignored settings
- &#129513; Mapping editor for ignored PrusaSlicer keys
- &#128051; OrcaSlicer import assistant
- &#128344; Conversion history
- &#128228; CSV, HTML, and PDF report exports
- &#128030; Anonymized bug report export
- &#127767; Day / night theme
- &#127757; Interface languages: FR, EN, DE, ES, IT, PT, NL, PL
- &#8505;&#65039; Info / Help tab
- &#129695; Improved window sizing, centering, and responsive layout

---

## &#10024; Features

- &#128433;&#65039; Drag and drop a PrusaSlicer `.ini` file directly into the app
- &#128193; Browse for a single file or an entire folder
- &#128230; Batch conversion support
- &#128424;&#65039; Converts printer, filament, and print process profiles
- &#128051; Generates ready-to-import `.orca_printer` bundles
- &#128064; Safe preview before writing files
- &#127991;&#65039; Prefixes generated presets with `PrusaToOrca -` by default
- &#128279; Strict / loose compatibility modes
- &#128260; GitHub release update check from the app

---

## &#128202; Reports

PrusaToOrca includes several report views to help understand what was converted.

- &#129534; Simple summary for normal users
- &#128295; Technical summary for generated bundles
- &#128202; Advanced report with exact, approximate, and ignored settings
- &#128200; Per-section conversion coverage
- &#128269; Filters for converted, approximate, and ignored fields
- &#128228; CSV export
- &#127760; HTML export
- &#128196; Simple PDF export
- &#128030; Anonymized bug report export

---

## &#10024; Extra tools

- &#127767; Light and dark theme
- &#127757; Interface languages: French, English, German, Spanish, Italian, Portuguese, Dutch, and Polish
- &#128051; OrcaSlicer import assistant after generation
- &#129513; Mapping editor for ignored PrusaSlicer keys
- &#128344; Conversion history with report snapshots
- &#128193; Open output folder button
- &#129514; Copy debug/version info
- &#8505;&#65039; Info / Help tab explaining the main settings
- &#129695; Centered and resizable Windows interface

---

## &#128230; Download

Download the latest Windows executable from:

[Latest release](../../releases/latest)

Look for:

```text
PrusaToOrca-v0.2.0.exe
```

No Python installation is required when using the `.exe`.

---

## &#129517; Recommended workflow

1. Back up your OrcaSlicer profiles.
2. Export a PrusaSlicer config bundle as `.ini`.
3. Open PrusaToOrca.
4. Drop the `.ini` file into the app, or choose a folder.
5. Click **Preview safe import**.
6. Review the summary or advanced report.
7. If needed, use Mapping to map ignored keys.
8. Generate the `.orca_printer` bundle.
9. In OrcaSlicer, go to **File > Import > Import Config Bundle**.
10. Select the generated `.orca_printer` file.

---

## &#128221; What gets converted?

PrusaToOrca converts many common slicer profile settings, including:

- Layer heights
- Speeds
- Temperatures
- Infill settings
- Retraction
- Cooling
- Supports
- Bed dimensions
- Machine limits
- Start / end G-code blocks
- Printer, filament, and process presets

Some PrusaSlicer-specific settings do not have a direct OrcaSlicer equivalent. These are reported as ignored or approximate so they can be reviewed manually.

---

## &#128736;&#65039; Run from source

### Requirements

- Python 3.10+
- Dependencies:

```bash
pip install -r requirements.txt
```

`tkinterdnd2` enables drag and drop. If it is missing, the file picker still works.

### Run the app

```bash
python app.py
```

---

## &#128296; Build the executable

The easiest way on Windows is:

```powershell
$env:PYTHON="C:\Path\To\python.exe"
.\build_exe.ps1
```

Or run PyInstaller manually:

```bash
pyinstaller --onefile --windowed --name "PrusaToOrca" --icon "logo.ico" --add-data "assets;assets" --add-data "logo.png;." --add-data "logo.ico;." app.py
```

The executable will be created in `dist/`.

---

## &#128295; Command-line usage

```bash
python convert.py profiles.ini
python convert.py profiles.ini --output ./output/
python convert.py profiles.ini --dry-run
python convert.py profiles.ini --compatibility strict
python convert.py profiles.ini --compatibility loose
python convert.py profiles.ini --no-prefix
```

Default behavior is intentionally conservative:

- `--compatibility strict`
- profile prefix enabled
- output name based on the generated printer preset

Use `--no-prefix` only if you are sure the generated preset names cannot collide with existing OrcaSlicer presets.

---

## &#129514; Tests

```bash
python -m unittest discover -s tests -v
```

The test suite covers safe import behavior, filename sanitizing, strict / loose compatibility, multi-printer bundles, dry-run behavior, UTF-8 BOM parsing, and custom ignored-key mappings.

---

## &#128193; Project structure

```text
.
|-- app.py              # Desktop GUI
|-- convert.py          # Conversion engine
|-- build_exe.ps1       # Windows build helper
|-- assets/             # Logo and fonts
|-- tests/              # Unit tests
|-- release/            # Prepared release files
|-- logo.png            # Source logo
|-- logo.ico            # Windows icon
`-- requirements.txt
```

---

## &#129309; Contributing

Pull requests are welcome.

If you find unmapped fields or conversion issues:

1. Fork the repository.
2. Create a branch.
3. Add or update tests when possible.
4. Open a pull request with a short explanation.

Reports exported from the app are very helpful when debugging mapping issues.

---

## &#128196; License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

### Permissions

- Commercial use
- Modification
- Distribution
- Private use

### Conditions

- Source code must be disclosed
- License and copyright notices must be included
- The same GPL-3.0 license must be used for derived work

### Limitations

- No liability
- No warranty

See the full license here:

https://www.gnu.org/licenses/gpl-3.0.html

