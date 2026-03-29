# PrusaToOrcaSlicer

<p align="center">
  <img src="logo.png" width="120" alt="Logo"/>
</p>

<p align="center">
  <b>Convertisseur de profils PrusaSlicer → OrcaSlicer</b><br/>
  Glisse-dépose ton fichier <code>.ini</code> PrusaSlicer et obtiens un <code>.orca_printer</code> prêt à l'emploi.
</p>

---

## ✨ Fonctionnalités

- 🖱️ **Drag & Drop** — glisse ton `.ini` directement dans l'app
- 🗂️ **Mode dossier** — convertis tous les profils d'un dossier en une fois
- 📊 **Rapport de conversion** — stats par section (mappés / approx / ignorés)
- 🔍 **Rapport avancé** — détail champ par champ avec export CSV
- 🌙 **Thème sombre / clair**
- 🌍 **4 langues** — Français, English, Deutsch, Español

## 📦 Télécharger

👉 [Dernière version (Releases)](../../releases/latest) — télécharge `PrusaToOrca.exe`, pas besoin d'installer Python.

---

## 🛠️ Lancer depuis le code source

### Prérequis

- Python 3.10+
- Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Lancer l'app

```bash
python app.py
```

### Construire l'exe

```bash
pyinstaller --onefile --windowed --name "PrusaToOrca" --icon "logo.ico" --add-data "convert.py;." --add-data "logo.png;." --add-data "logo.ico;." app.py
```

L'exe se trouve dans `dist/PrusaToOrca.exe`.

---

## 🔧 Utilisation en ligne de commande

```bash
python convert.py profils.ini
python convert.py profils.ini --output ./output/
```

---

## 📁 Structure du projet

```
.
├── app.py          # Interface graphique (tkinter + tkinterdnd2)
├── convert.py      # Moteur de conversion PrusaSlicer → OrcaSlicer
├── logo.png        # Logo de l'application
├── logo.ico        # Icône Windows
└── requirements.txt
```

---

## 🤝 Contribuer

Les PRs sont les bienvenues ! Si tu trouves des champs non mappés ou des bugs :

1. Fork le repo
2. Crée une branche (`git checkout -b feature/mon-amélioration`)
3. Commit tes changements (`git commit -m 'Ajout de ...'`)
4. Push et ouvre une Pull Request

---

## 📄 Licence

MIT — fais-en ce que tu veux.
