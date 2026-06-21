# PrusaToOrca

PrusaToOrca converts PrusaSlicer config bundle `.ini` files into OrcaSlicer
`.orca_printer` bundles.

The app is designed around a safe import flow: preview first, generate second.
Generated presets are prefixed by default so existing OrcaSlicer profiles are
not overwritten by matching names.

## Features

- Desktop GUI with drag-and-drop support when `tkinterdnd2` is installed.
- File mode and folder mode for batch conversion of `.ini` bundles.
- Safe import preview before writing any bundle.
- Prefixes generated presets with `PrusaToOrca -` by default.
- Adds explicit OrcaSlicer compatibility metadata for generated filament and
  process presets.
- Supports strict or loose compatibility modes.
- CLI mode for automation and testing.
- Conversion report with summary, bundle file list, advanced field details, and
  CSV export.

## Install

Python 3.10+ is recommended.

```bash
pip install -r requirements.txt
```

`tkinterdnd2` enables drag-and-drop. If it is missing, the app still works with
the file picker.

## Run The App

```bash
python app.py
```

Workflow:

1. Drop or choose a PrusaSlicer `.ini` config bundle, or choose a folder.
2. Review the safe import preview.
3. Choose strict or loose compatibility.
4. Generate the `.orca_printer` bundle.
5. Export the CSV report if needed.
6. Import the generated bundle in OrcaSlicer.

## CLI Usage

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

Use `--no-prefix` only if you are sure the generated preset names cannot collide
with existing OrcaSlicer presets.

## Build A Windows Executable

The easiest way on Windows is:

```powershell
$env:PYTHON="C:\Path\To\python.exe"
.\build_exe.ps1
```

The script installs nothing by itself. Install runtime and build dependencies
first:

```bash
pip install -r requirements.txt pyinstaller
```

Or run PyInstaller manually:

```bash
pyinstaller --onefile --windowed --name "PrusaToOrca" --icon "logo.ico" --add-data "assets;assets" --add-data "logo.png;." --add-data "logo.ico;." app.py
```

The executable will be created in `dist/`.

## Tests

```bash
python -m unittest discover -s tests -v
```

The test suite covers safe import behavior, filename sanitizing, strict/loose
compatibility, multi-printer bundles, dry-run behavior, and UTF-8 BOM parsing.

## Project Structure

```text
.
|-- app.py
|-- convert.py
|-- tests/
|-- logo.png
|-- logo.ico
|-- requirements.txt
`-- README.md
```

## License

See `LICENSE`.
