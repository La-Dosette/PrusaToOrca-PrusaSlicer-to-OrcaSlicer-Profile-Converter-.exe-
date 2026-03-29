PrusaToOrcaSlicer
<p align="center"> <img src="logo.png" width="120" alt="Logo"/> </p> <p align="center"> <b>PrusaSlicer → OrcaSlicer Profile Converter</b><br/> Drag and drop your <code>.ini</code> PrusaSlicer file and get a ready-to-use <code>.orca_printer</code>. </p>
✨ Features
🖱️ Drag & Drop — drop your .ini directly into the app
🗂️ Folder mode — convert all profiles in a folder at once
📊 Conversion report — stats by section (mapped / approximated / ignored)
🔍 Advanced report — field-by-field details with CSV export
🌙 Dark / Light theme
🌍 4 languages — French, English, German, Spanish
📦 Download

👉 Latest version (Releases)
 — download PrusaToOrca.exe, no Python installation required.

🛠️ Run from source
Requirements
Python 3.10+
Install dependencies:
pip install -r requirements.txt
Run the app
python app.py
Build the executable
pyinstaller --onefile --windowed --name "PrusaToOrca" --icon "logo.ico" --add-data "convert.py;." --add-data "logo.png;." --add-data "logo.ico;." app.py

The executable will be located at dist/PrusaToOrca.exe.

🔧 Command-line usage
python convert.py profiles.ini
python convert.py profiles.ini --output ./output/
📁 Project structure
.
├── app.py          # GUI (tkinter + tkinterdnd2)
├── convert.py      # PrusaSlicer → OrcaSlicer conversion engine
├── logo.png        # Application logo
├── logo.ico        # Windows icon
└── requirements.txt
🤝 Contributing

Pull Requests are welcome! If you find unmapped fields or bugs:

Fork the repository
Create a branch (git checkout -b feature/my-improvement)
Commit your changes (git commit -m 'Add ...')
Push and open a Pull Request
📄 License

MIT — do whatever you want with it.
