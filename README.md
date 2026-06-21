# PrusaToOrca

<p align="center">
  <img width="96" height="96" alt="PrusaToOrca logo" src="assets/logo_header.png" />
</p>

<p align="center">
  <b>PrusaSlicer &rarr; OrcaSlicer Profile Converter</b><br/>
  Convert PrusaSlicer <code>.ini</code> config bundles into OrcaSlicer <code>.orca_printer</code> import bundles.
</p>

<p align="center">
  <a href="../../releases/latest">Download latest release</a>
  &nbsp;|&nbsp;
  <a href="CHANGELOG.md">Changelog</a>
  &nbsp;|&nbsp;
  <a href="PATCH_NOTES.md">Patch notes</a>
</p>

---

## Update - v0.2.0

This update focuses on safety, clarity, and a cleaner interface.

The main workflow is now:

**Preview first &rarr; Generate second &rarr; Import manually into OrcaSlicer**

PrusaToOrca does not directly edit existing OrcaSlicer preset files. It generates a new `.orca_printer` bundle that can be reviewed before importing.

> Always back up your OrcaSlicer profiles before importing converted profiles.

### Main changes

- Safer non-destructive conversion workflow
- Preview before generating files
- Prefix enabled by default to reduce name collisions
- Strict / loose compatibility modes
- Risk scoring for possible OrcaSlicer preset name collisions
- Simple summary tab
- Improved advanced report
- Filters for converted, approximate, and ignored settings
- Mapping editor for ignored PrusaSlicer keys
- OrcaSlicer import assistant
- Conversion history
- CSV, HTML, and PDF report exports
- Anonymized bug report export
- Day / night theme
- Interface languages: FR, EN, DE, ES, IT, PT, NL, PL
- Info / Help tab
- Improved window sizing, centering, and responsive layout

---

## Features

- Drag and drop a PrusaSlicer `.ini` file directly into the app
- Browse for a single file or an entire folder
- Batch conversion support
- Converts printer, filament, and print process profiles
- Generates ready-to-import `.orca_printer` bundles
- Safe preview before writing files
- Prefixes generated presets with `PrusaToOrca -` by default
- Strict / loose compatibility modes
- GitHub release update check from the app

---

## Reports

PrusaToOrca includes several report views to help understand what was converted.

- Simple summary for normal users
- Technical summary for generated bundles
- Advanced report with exact, approximate, and ignored settings
- Per-section conversion coverage
- Filters for converted, approximate, and ignored fields
- CSV export
- HTML export
- Simple PDF export
- Anonymized bug report export

---

## Extra tools

- Light and dark theme
- Interface languages: French, English, German, Spanish, Italian, Portuguese, Dutch, and Polish
- OrcaSlicer import assistant after generation
- Mapping editor for ignored PrusaSlicer keys
- Conversion history with report snapshots
- Open output folder button
- Copy debug/version info
- Info / Help tab explaining the main settings
- Centered and resizable Windows interface

---

## Download

Download the latest Windows executable from:

[Latest release](../../releases/latest)

Look for:

```text
PrusaToOrca-v0.2.0.exe
```

No Python installation is required when using the `.exe`.

---

## Recommended workflow

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

## What gets converted?

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

## Run from source

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

## Build the executable

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

## Command-line usage

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

## Tests

```bash
python -m unittest discover -s tests -v
```

The test suite covers safe import behavior, filename sanitizing, strict / loose compatibility, multi-printer bundles, dry-run behavior, UTF-8 BOM parsing, and custom ignored-key mappings.

---

## Project structure

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

## Contributing

Pull requests are welcome.

If you find unmapped fields or conversion issues:

1. Fork the repository.
2. Create a branch.
3. Add or update tests when possible.
4. Open a pull request with a short explanation.

Reports exported from the app are very helpful when debugging mapping issues.

---

## License

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
