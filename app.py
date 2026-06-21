#!/usr/bin/env python3
"""
PrusaToOrca desktop interface.

The UI is intentionally conservative: preview first, convert second. This keeps
the safe-import behavior visible instead of hiding it behind a single button.
"""

import threading
import tkinter as tk
import sys
import ctypes
import csv
import html
import json
import os
import urllib.error
import urllib.request
import webbrowser
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from convert import ConversionLog, convert_ini_to_orca

APP_VERSION = "0.2.0"
APP_NAME = "PrusaToOrca"
SETTINGS_FILE = "settings.json"
CUSTOM_MAPPINGS_FILE = "custom_mappings.json"
GITHUB_RELEASES_API = (
    "https://api.github.com/repos/"
    "La-Dosette/PrusaToOrca-PrusaSlicer-to-OrcaSlicer-Profile-Converter-.exe-/releases/latest"
)
GITHUB_RELEASES_URL = (
    "https://github.com/"
    "La-Dosette/PrusaToOrca-PrusaSlicer-to-OrcaSlicer-Profile-Converter-.exe-/releases"
)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # pragma: no cover - optional desktop enhancement
    DND_FILES = None
    TkinterDnD = None


THEMES = {
    "day": {
        "APP_BG": "#f3f0e9",
        "PANEL_BG": "#f3f0e9",
        "PANEL_TINT": "#ece6da",
        "INK": "#2b2825",
        "MUTED": "#6f6862",
        "LINE": "#2b2825",
        "HEADER_BG": "#2b2825",
        "HEADER_FG": "#f3f0e9",
        "TEAL": "#009aa6",
        "TEAL_DARK": "#00737d",
        "ORANGE": "#ff8a00",
        "ORANGE_DARK": "#de5f00",
        "RED_ORANGE": "#f04412",
        "ADV_PROGRESS_BG": "#d8d2ca",
    },
    "night": {
        "APP_BG": "#0f1117",
        "PANEL_BG": "#151821",
        "PANEL_TINT": "#202634",
        "INK": "#f6efe4",
        "MUTED": "#b9afa3",
        "LINE": "#343947",
        "HEADER_BG": "#201d22",
        "HEADER_FG": "#f6efe4",
        "TEAL": "#00a6b2",
        "TEAL_DARK": "#20c8d2",
        "ORANGE": "#ff8a00",
        "ORANGE_DARK": "#ffb14f",
        "RED_ORANGE": "#ff5a2a",
        "ADV_PROGRESS_BG": "#2d3444",
    },
}

LANGUAGE_OPTIONS = [
    ("fr", "FR", "Français"),
    ("en", "EN", "English"),
    ("de", "DE", "Deutsch"),
    ("es", "ES", "Español"),
    ("it", "IT", "Italiano"),
    ("pt", "PT", "Português"),
    ("nl", "NL", "Nederlands"),
    ("pl", "PL", "Polski"),
]
LANGUAGE_CODES = {code for code, _short, _name in LANGUAGE_OPTIONS}

TRANSLATIONS = {
    "en": {
        "advanced_report": "Advanced report",
        "advanced_report_empty": "Preview a bundle to see the animated advanced report.",
        "advanced_report_open_first": "Preview or convert a bundle before opening the advanced report.",
        "advanced_report_title": "Advanced report",
        "all": "All",
        "app_subtitle": "PrusaToOrca // safe profile importer",
        "approx": "Approx",
        "approx_detail": "approximate fields",
        "bundle_files_empty": "No bundle preview yet.",
        "bundle_files_tab": "Files",
        "cancel": "Close",
        "check_updates": "Check updates",
        "choose_file": "Choose file",
        "choose_file_first": "Choose a .ini file or folder first.",
        "choose_folder": "Choose folder",
        "choose_output_folder": "Choose output folder",
        "clear": "Clear",
        "compat_loose": "LOOSE",
        "compat_strict": "STRICT",
        "converted": "Converted",
        "converted_detail": "mapped fields",
        "copy_debug_info": "Copy debug info",
        "csv": "CSV",
        "day": "DAY",
        "drop_subtitle": "preview before writing",
        "drop_title": "DROP .INI HERE",
        "export_html": "HTML",
        "export_pdf": "PDF",
        "folder": "Folder",
        "generate": "Generate .orca_printer",
        "history": "History",
        "info_tab": "Info",
        "ignored": "Ignored",
        "ignored_detail": "not converted",
        "language": "Language",
        "language_intro": "Choose the interface language. Technical Prusa/Orca keys keep their original names.",
        "mapping_editor": "Mapping editor",
        "night": "NIGHT",
        "open": "Open",
        "open_detailed_view": "Open detailed view",
        "output_folder": "Output folder",
        "output_subtitle": "non destructive",
        "preview_button": "Preview safe import",
        "preview_header": "03 // preview",
        "preview_subtitle": "what will be added to OrcaSlicer",
        "prefix_off": "PREFIX OFF",
        "prefix_on": "PREFIX ON",
        "risk": "Risk",
        "risk_waiting": "Risk: waiting for preview",
        "safe": "SAFE",
        "simple_empty": "Choose a PrusaSlicer bundle to get a plain-language import summary.",
        "simple_summary_empty": "Choose a bundle to see a non-technical import summary.",
        "summary_empty": "Choose a PrusaSlicer config bundle or folder to preview the safe Orca import.\n\nPreview writes no files.\nExisting Orca presets are not touched by this app.",
        "simple_tab": "Simple",
        "source_subtitle": ".ini file or folder",
        "source_title": "01 // source",
        "technical_tab": "Technical",
        "tools": "Tools",
        "tools_description": "Support and maintenance actions. The main workflow stays on the left panel.",
        "what_this_means": "What this means",
    },
    "fr": {
        "advanced_report": "Rapport avancé",
        "advanced_report_empty": "Prévisualise un bundle pour voir le rapport avancé animé.",
        "advanced_report_open_first": "Prévisualise ou génère un bundle avant d’ouvrir le rapport avancé.",
        "advanced_report_title": "Rapport avancé",
        "all": "Tous",
        "app_subtitle": "PrusaToOrca // importateur de profils sécurisé",
        "approx": "Approx",
        "approx_detail": "champs approximatifs",
        "bundle_files_empty": "Aucun aperçu de bundle pour le moment.",
        "bundle_files_tab": "Fichiers",
        "cancel": "Fermer",
        "check_updates": "Vérifier les mises à jour",
        "choose_file": "Choisir fichier",
        "choose_file_first": "Choisis d’abord un fichier .ini ou un dossier.",
        "choose_folder": "Choisir dossier",
        "choose_output_folder": "Choisir le dossier de sortie",
        "clear": "Effacer",
        "compat_loose": "SOUPLE",
        "compat_strict": "STRICT",
        "converted": "Convertis",
        "converted_detail": "champs mappés",
        "copy_debug_info": "Copier infos debug",
        "csv": "CSV",
        "day": "JOUR",
        "drop_subtitle": "aperçu avant écriture",
        "drop_title": "DÉPOSE LE .INI ICI",
        "export_html": "HTML",
        "export_pdf": "PDF",
        "folder": "Dossier",
        "generate": "Générer .orca_printer",
        "history": "Historique",
        "info_tab": "Aide",
        "ignored": "Ignorés",
        "ignored_detail": "non convertis",
        "language": "Langue",
        "language_intro": "Choisis la langue de l’interface. Les clés techniques Prusa/Orca gardent leur nom réel.",
        "mapping_editor": "Éditeur de mapping",
        "night": "NUIT",
        "open": "Ouvrir",
        "open_detailed_view": "Ouvrir la vue détaillée",
        "output_folder": "Dossier de sortie",
        "output_subtitle": "non destructif",
        "preview_button": "Prévisualiser l’import sûr",
        "preview_header": "03 // aperçu",
        "preview_subtitle": "ce qui sera ajouté à OrcaSlicer",
        "prefix_off": "PRÉFIXE OFF",
        "prefix_on": "PRÉFIXE ON",
        "risk": "Risque",
        "risk_waiting": "Risque : en attente d’aperçu",
        "safe": "SAFE",
        "simple_empty": "Choisis un bundle PrusaSlicer pour obtenir un résumé en langage simple.",
        "simple_summary_empty": "Choisis un bundle pour voir un résumé non technique.",
        "summary_empty": "Choisis un bundle PrusaSlicer ou un dossier pour prévisualiser l’import Orca sécurisé.\n\nL’aperçu n’écrit aucun fichier.\nLes profils Orca existants ne sont pas touchés par cette app.",
        "simple_tab": "Simple",
        "source_subtitle": "fichier .ini ou dossier",
        "source_title": "01 // source",
        "technical_tab": "Technique",
        "tools": "Outils",
        "tools_description": "Actions de support et de maintenance. Le flux principal reste dans le panneau de gauche.",
        "what_this_means": "Ce que ça veut dire",
    },
    "de": {
        "advanced_report": "Erweiterter Bericht", "all": "Alle", "app_subtitle": "PrusaToOrca // sicherer Profilimport", "approx": "Näherung",
        "bundle_files_tab": "Dateien", "cancel": "Schließen", "choose_file": "Datei wählen", "choose_folder": "Ordner wählen",
        "clear": "Leeren", "converted": "Konvertiert", "csv": "CSV", "day": "TAG", "drop_title": ".INI HIER ABLEGEN",
        "export_html": "HTML", "export_pdf": "PDF", "folder": "Ordner", "generate": ".orca_printer erzeugen", "history": "Verlauf",
        "ignored": "Ignoriert", "language": "Sprache", "mapping_editor": "Mapping-Editor", "night": "NACHT", "open": "Öffnen",
        "output_folder": "Ausgabeordner", "preview_button": "Sicheren Import prüfen", "prefix_off": "PRÄFIX AUS", "prefix_on": "PRÄFIX AN",
        "risk": "Risiko", "simple_tab": "Einfach", "technical_tab": "Technisch", "tools": "Werkzeuge", "what_this_means": "Bedeutung",
    },
    "es": {
        "advanced_report": "Informe avanzado", "all": "Todos", "app_subtitle": "PrusaToOrca // importador seguro de perfiles", "approx": "Aprox",
        "bundle_files_tab": "Archivos", "cancel": "Cerrar", "choose_file": "Elegir archivo", "choose_folder": "Elegir carpeta",
        "clear": "Limpiar", "converted": "Convertidos", "csv": "CSV", "day": "DÍA", "drop_title": "SUELTA EL .INI AQUÍ",
        "export_html": "HTML", "export_pdf": "PDF", "folder": "Carpeta", "generate": "Generar .orca_printer", "history": "Historial",
        "ignored": "Ignorados", "language": "Idioma", "mapping_editor": "Editor de mapeo", "night": "NOCHE", "open": "Abrir",
        "output_folder": "Carpeta de salida", "preview_button": "Previsualizar importación segura", "prefix_off": "PREFIJO OFF", "prefix_on": "PREFIJO ON",
        "risk": "Riesgo", "simple_tab": "Simple", "technical_tab": "Técnico", "tools": "Herramientas", "what_this_means": "Qué significa",
    },
    "it": {
        "advanced_report": "Rapporto avanzato", "all": "Tutti", "app_subtitle": "PrusaToOrca // import sicuro dei profili", "approx": "Approx",
        "bundle_files_tab": "File", "cancel": "Chiudi", "choose_file": "Scegli file", "choose_folder": "Scegli cartella",
        "clear": "Pulisci", "converted": "Convertiti", "csv": "CSV", "day": "GIORNO", "drop_title": "TRASCINA .INI QUI",
        "export_html": "HTML", "export_pdf": "PDF", "folder": "Cartella", "generate": "Genera .orca_printer", "history": "Cronologia",
        "ignored": "Ignorati", "language": "Lingua", "mapping_editor": "Editor mapping", "night": "NOTTE", "open": "Apri",
        "output_folder": "Cartella output", "preview_button": "Anteprima import sicuro", "prefix_off": "PREFISSO OFF", "prefix_on": "PREFISSO ON",
        "risk": "Rischio", "simple_tab": "Semplice", "technical_tab": "Tecnico", "tools": "Strumenti", "what_this_means": "Cosa significa",
    },
    "pt": {
        "advanced_report": "Relatório avançado", "all": "Todos", "app_subtitle": "PrusaToOrca // importador seguro de perfis", "approx": "Aprox",
        "bundle_files_tab": "Ficheiros", "cancel": "Fechar", "choose_file": "Escolher ficheiro", "choose_folder": "Escolher pasta",
        "clear": "Limpar", "converted": "Convertidos", "csv": "CSV", "day": "DIA", "drop_title": "SOLTA O .INI AQUI",
        "export_html": "HTML", "export_pdf": "PDF", "folder": "Pasta", "generate": "Gerar .orca_printer", "history": "Histórico",
        "ignored": "Ignorados", "language": "Idioma", "mapping_editor": "Editor de mapeamento", "night": "NOITE", "open": "Abrir",
        "output_folder": "Pasta de saída", "preview_button": "Pré-visualizar importação segura", "prefix_off": "PREFIXO OFF", "prefix_on": "PREFIXO ON",
        "risk": "Risco", "simple_tab": "Simples", "technical_tab": "Técnico", "tools": "Ferramentas", "what_this_means": "O que significa",
    },
    "nl": {
        "advanced_report": "Geavanceerd rapport", "all": "Alles", "app_subtitle": "PrusaToOrca // veilige profielimport", "approx": "Benadering",
        "bundle_files_tab": "Bestanden", "cancel": "Sluiten", "choose_file": "Kies bestand", "choose_folder": "Kies map",
        "clear": "Wissen", "converted": "Omgezet", "csv": "CSV", "day": "DAG", "drop_title": "ZET .INI HIER",
        "export_html": "HTML", "export_pdf": "PDF", "folder": "Map", "generate": ".orca_printer maken", "history": "Geschiedenis",
        "ignored": "Genegeerd", "language": "Taal", "mapping_editor": "Mapping-editor", "night": "NACHT", "open": "Openen",
        "output_folder": "Uitvoermap", "preview_button": "Veilige import bekijken", "prefix_off": "PREFIX UIT", "prefix_on": "PREFIX AAN",
        "risk": "Risico", "simple_tab": "Simpel", "technical_tab": "Technisch", "tools": "Tools", "what_this_means": "Wat dit betekent",
    },
    "pl": {
        "advanced_report": "Raport zaawansowany", "all": "Wszystko", "app_subtitle": "PrusaToOrca // bezpieczny importer profili", "approx": "Przybliż.",
        "bundle_files_tab": "Pliki", "cancel": "Zamknij", "choose_file": "Wybierz plik", "choose_folder": "Wybierz folder",
        "clear": "Wyczyść", "converted": "Przekonwert.", "csv": "CSV", "day": "DZIEŃ", "drop_title": "UPUŚĆ .INI TUTAJ",
        "export_html": "HTML", "export_pdf": "PDF", "folder": "Folder", "generate": "Utwórz .orca_printer", "history": "Historia",
        "ignored": "Pominięte", "language": "Język", "mapping_editor": "Edytor mapowania", "night": "NOC", "open": "Otwórz",
        "output_folder": "Folder wyjściowy", "preview_button": "Podgląd bezpiecznego importu", "prefix_off": "PREFIKS OFF", "prefix_on": "PREFIKS ON",
        "risk": "Ryzyko", "simple_tab": "Prosty", "technical_tab": "Techniczny", "tools": "Narzędzia", "what_this_means": "Co to znaczy",
    },
}

TRANSLATIONS["en"].update({
    "advanced_no_section": "No section for this filter.",
    "bug_report": "Bug report",
    "bug_report_exported": "Bug report generated:\n{path}",
    "copy_file_path": "Copy file path",
    "debug_copied": "Debug info copied to clipboard.",
    "export_before_csv": "Preview or convert a bundle before exporting CSV.",
    "export_before_html": "Preview or convert a bundle before exporting HTML.",
    "export_before_pdf": "Preview or convert a bundle before exporting PDF.",
    "export_csv_done": "CSV report exported:\n{path}",
    "export_html_done": "HTML report exported:\n{path}",
    "export_pdf_done": "PDF report exported:\n{path}",
    "generated_bundle_file": "Generated bundle file",
    "generated_bundle_paths": "Generated bundle path(s)",
    "history_select_first": "Select a conversion first.",
    "import_assistant": "Import assistant",
    "import_assistant_intro": "Your bundle was generated. Follow these steps in OrcaSlicer.",
    "import_assistant_need_generate": "Generate the .orca_printer bundle first.",
    "import_into_orca": "Import into OrcaSlicer",
    "mapping_intro": "Choose an ignored PrusaSlicer key, map it to an OrcaSlicer key, then preview again.",
    "next_step": "Next step",
    "open_orca_guide": "Open Orca guide",
    "open_output_folder": "Open output folder",
    "orca_target_key": "OrcaSlicer target key",
    "info_title": "How to read this screen",
    "info_intro": "This app never imports directly into OrcaSlicer. It prepares a safe bundle, then you import that bundle yourself in Orca.",
    "info_flow_title": "Recommended flow",
    "info_flow_body": "Choose a .ini file or folder, run Preview, read Simple or Advanced, then Generate the .orca_printer bundle.",
    "info_safe_title": "Safe mode",
    "info_safe_body": "Preview writes nothing. Generate only writes new bundle files in the output folder. Existing OrcaSlicer presets are not edited.",
    "info_prefix_title": "Prefix",
    "info_prefix_body": "Prefix ON adds PrusaToOrca to generated preset names. Keep it on to reduce name collision risk.",
    "info_compat_title": "Strict / loose",
    "info_compat_body": "Strict keeps imported filament and process presets tied to imported printers. Loose makes them easier to reuse, but less isolated.",
    "info_reports_title": "Reports",
    "info_reports_body": "Simple is for normal users. Technical shows generated bundles. Advanced shows exact, approximate, and ignored fields.",
    "info_mapping_title": "Mapping editor",
    "info_mapping_body": "If a key is ignored and matters to you, map it to an OrcaSlicer key, then preview again before generating.",
    "preview_again": "Preview again",
    "remove": "Remove",
    "save_mapping": "Save mapping",
    "saved_mappings": "Saved mappings",
    "select_ignored": "Select an ignored key.",
    "store_as_list": "Store value as Orca list",
    "mapping_need_preview": "Preview a bundle before editing ignored-key mappings.",
    "mapping_no_ignored": "No ignored keys in the current report.",
    "mapping_need_target": "Select an ignored key and enter an Orca target key.",
    "mapping_saved": "Mapping saved. Run Preview again to apply it.",
    "bug_report_need_preview": "Preview or convert a bundle before generating a bug report.",
    "history_no_snapshot": "This older history item has no saved report snapshot.",
    "reopen_report": "Reopen report",
    "refresh": "Refresh",
})

TRANSLATIONS["fr"].update({
    "advanced_no_section": "Aucune section pour ce filtre.",
    "bug_report": "Rapport de bug",
    "bug_report_exported": "Rapport de bug généré :\n{path}",
    "copy_file_path": "Copier le chemin",
    "debug_copied": "Infos debug copiées dans le presse-papiers.",
    "export_before_csv": "Prévisualise ou génère un bundle avant d’exporter le CSV.",
    "export_before_html": "Prévisualise ou génère un bundle avant d’exporter le HTML.",
    "export_before_pdf": "Prévisualise ou génère un bundle avant d’exporter le PDF.",
    "export_csv_done": "Rapport CSV exporté :\n{path}",
    "export_html_done": "Rapport HTML exporté :\n{path}",
    "export_pdf_done": "Rapport PDF exporté :\n{path}",
    "generated_bundle_file": "Fichier bundle généré",
    "generated_bundle_paths": "Chemin(s) du bundle généré",
    "history_select_first": "Sélectionne d’abord une conversion.",
    "import_assistant": "Assistant d’import",
    "import_assistant_intro": "Ton bundle a été généré. Suis ces étapes dans OrcaSlicer.",
    "import_assistant_need_generate": "Génère d’abord le bundle .orca_printer.",
    "import_into_orca": "Importer dans OrcaSlicer",
    "mapping_intro": "Choisis une clé PrusaSlicer ignorée, associe-la à une clé OrcaSlicer, puis relance l’aperçu.",
    "next_step": "Prochaine étape",
    "open_orca_guide": "Ouvrir le guide Orca",
    "open_output_folder": "Ouvrir le dossier de sortie",
    "orca_target_key": "Clé cible OrcaSlicer",
    "info_title": "Comprendre cet écran",
    "info_intro": "L’app n’importe jamais directement dans OrcaSlicer. Elle prépare un bundle sûr, puis tu l’importes toi-même dans Orca.",
    "info_flow_title": "Flux recommandé",
    "info_flow_body": "Choisis un fichier .ini ou un dossier, lance l’aperçu, lis Simple ou Avancé, puis génère le bundle .orca_printer.",
    "info_safe_title": "Mode safe",
    "info_safe_body": "L’aperçu n’écrit rien. La génération écrit uniquement de nouveaux bundles dans le dossier de sortie. Les profils Orca existants ne sont pas modifiés.",
    "info_prefix_title": "Préfixe",
    "info_prefix_body": "Préfixe ON ajoute PrusaToOrca aux noms générés. Garde-le activé pour réduire le risque de collision de noms.",
    "info_compat_title": "Strict / souple",
    "info_compat_body": "Strict lie les filaments et process importés aux imprimantes importées. Souple les rend plus réutilisables, mais moins isolés.",
    "info_reports_title": "Rapports",
    "info_reports_body": "Simple sert aux utilisateurs normaux. Technique montre les bundles générés. Avancé montre les champs exacts, approximatifs et ignorés.",
    "info_mapping_title": "Éditeur de mapping",
    "info_mapping_body": "Si une clé ignorée est importante, associe-la à une clé OrcaSlicer, puis relance l’aperçu avant de générer.",
    "preview_again": "Relancer l’aperçu",
    "remove": "Retirer",
    "save_mapping": "Sauver mapping",
    "saved_mappings": "Mappings sauvegardés",
    "select_ignored": "Sélectionne une clé ignorée.",
    "store_as_list": "Stocker la valeur comme liste Orca",
    "mapping_need_preview": "Prévisualise un bundle avant de modifier les mappings de clés ignorées.",
    "mapping_no_ignored": "Aucune clé ignorée dans le rapport actuel.",
    "mapping_need_target": "Sélectionne une clé ignorée et indique une clé Orca cible.",
    "mapping_saved": "Mapping sauvegardé. Relance l’aperçu pour l’appliquer.",
    "bug_report_need_preview": "Prévisualise ou génère un bundle avant de créer un rapport de bug.",
    "history_no_snapshot": "Cet ancien historique n’a pas de rapport sauvegardé.",
    "reopen_report": "Rouvrir rapport",
    "refresh": "Actualiser",
})

TRANSLATIONS["de"].update({
    "advanced_no_section": "Kein Bereich für diesen Filter.",
    "advanced_report_empty": "Zeige eine Vorschau an, um den animierten erweiterten Bericht zu sehen.",
    "advanced_report_open_first": "Zeige zuerst eine Vorschau an oder erzeuge ein Bundle.",
    "advanced_report_title": "Erweiterter Bericht",
    "approx_detail": "ungefähre Felder",
    "bug_report": "Fehlerbericht",
    "bug_report_exported": "Fehlerbericht erstellt:\n{path}",
    "bundle_files_empty": "Noch keine Bundle-Vorschau.",
    "check_updates": "Nach Updates suchen",
    "choose_file_first": "Wähle zuerst eine .ini-Datei oder einen Ordner.",
    "choose_output_folder": "Ausgabeordner wählen",
    "compat_loose": "LOCKER",
    "compat_strict": "STRENG",
    "converted_detail": "zugeordnete Felder",
    "copy_debug_info": "Debug-Infos kopieren",
    "copy_file_path": "Dateipfad kopieren",
    "debug_copied": "Debug-Infos wurden in die Zwischenablage kopiert.",
    "drop_subtitle": "Vorschau, bevor etwas geschrieben wird",
    "export_before_csv": "Zeige zuerst eine Vorschau an oder erzeuge ein Bundle.",
    "export_before_html": "Zeige zuerst eine Vorschau an oder erzeuge ein Bundle.",
    "export_before_pdf": "Zeige zuerst eine Vorschau an oder erzeuge ein Bundle.",
    "export_csv_done": "CSV-Bericht exportiert:\n{path}",
    "export_html_done": "HTML-Bericht exportiert:\n{path}",
    "export_pdf_done": "PDF-Bericht exportiert:\n{path}",
    "generated_bundle_file": "Erzeugte Bundle-Datei",
    "generated_bundle_paths": "Pfad(e) zum erzeugten Bundle",
    "history_select_first": "Wähle zuerst eine Konvertierung.",
    "ignored_detail": "nicht konvertiert",
    "import_assistant": "Importassistent",
    "import_assistant_intro": "Dein Bundle wurde erzeugt. Folge diesen Schritten in OrcaSlicer.",
    "import_assistant_need_generate": "Erzeuge zuerst das .orca_printer-Bundle.",
    "import_into_orca": "In OrcaSlicer importieren",
    "language_intro": "Wähle die Sprache der Oberfläche. Technische Prusa/Orca-Schlüssel bleiben unverändert.",
    "mapping_intro": "Wähle einen ignorierten PrusaSlicer-Schlüssel, ordne ihn einem OrcaSlicer-Schlüssel zu und starte die Vorschau erneut.",
    "next_step": "Nächster Schritt",
    "open_detailed_view": "Detailansicht öffnen",
    "open_orca_guide": "Orca-Anleitung öffnen",
    "open_output_folder": "Ausgabeordner öffnen",
    "orca_target_key": "OrcaSlicer-Zielschlüssel",
    "output_subtitle": "nicht destruktiv",
    "preview_again": "Vorschau erneut starten",
    "preview_header": "03 // Vorschau",
    "preview_subtitle": "was zu OrcaSlicer hinzugefügt wird",
    "remove": "Entfernen",
    "risk_waiting": "Risiko: wartet auf Vorschau",
    "safe": "SICHER",
    "save_mapping": "Mapping speichern",
    "saved_mappings": "Gespeicherte Mappings",
    "select_ignored": "Wähle einen ignorierten Schlüssel.",
    "simple_empty": "Wähle ein PrusaSlicer-Bundle für eine verständliche Import-Zusammenfassung.",
    "simple_summary_empty": "Wähle ein Bundle für eine nicht technische Zusammenfassung.",
    "summary_empty": "Wähle ein PrusaSlicer-Bundle oder einen Ordner, um den sicheren Orca-Import vorzuschauen.\n\nDie Vorschau schreibt keine Dateien.\nBestehende Orca-Profile werden nicht berührt.",
    "source_subtitle": ".ini-Datei oder Ordner",
    "source_title": "01 // Quelle",
    "store_as_list": "Wert als Orca-Liste speichern",
    "tools_description": "Support- und Wartungsaktionen. Der Hauptablauf bleibt links.",
})

TRANSLATIONS["es"].update({
    "advanced_no_section": "No hay sección para este filtro.",
    "advanced_report_empty": "Previsualiza un bundle para ver el informe avanzado animado.",
    "advanced_report_open_first": "Previsualiza o genera un bundle antes de abrir el informe avanzado.",
    "advanced_report_title": "Informe avanzado",
    "approx_detail": "campos aproximados",
    "bug_report": "Informe de error",
    "bug_report_exported": "Informe de error generado:\n{path}",
    "bundle_files_empty": "Todavía no hay vista previa del bundle.",
    "check_updates": "Buscar actualizaciones",
    "choose_file_first": "Elige primero un archivo .ini o una carpeta.",
    "choose_output_folder": "Elegir carpeta de salida",
    "compat_loose": "FLEXIBLE",
    "compat_strict": "ESTRICTO",
    "converted_detail": "campos mapeados",
    "copy_debug_info": "Copiar info de depuración",
    "copy_file_path": "Copiar ruta del archivo",
    "debug_copied": "Info de depuración copiada al portapapeles.",
    "drop_subtitle": "previsualiza antes de escribir nada",
    "export_before_csv": "Previsualiza o genera un bundle antes de exportar CSV.",
    "export_before_html": "Previsualiza o genera un bundle antes de exportar HTML.",
    "export_before_pdf": "Previsualiza o genera un bundle antes de exportar PDF.",
    "export_csv_done": "Informe CSV exportado:\n{path}",
    "export_html_done": "Informe HTML exportado:\n{path}",
    "export_pdf_done": "Informe PDF exportado:\n{path}",
    "generated_bundle_file": "Archivo bundle generado",
    "generated_bundle_paths": "Ruta(s) del bundle generado",
    "history_select_first": "Selecciona primero una conversión.",
    "ignored_detail": "no convertidos",
    "import_assistant": "Asistente de importación",
    "import_assistant_intro": "Tu bundle se ha generado. Sigue estos pasos en OrcaSlicer.",
    "import_assistant_need_generate": "Genera primero el bundle .orca_printer.",
    "import_into_orca": "Importar en OrcaSlicer",
    "language_intro": "Elige el idioma de la interfaz. Las claves técnicas Prusa/Orca mantienen su nombre real.",
    "mapping_intro": "Elige una clave PrusaSlicer ignorada, asígnala a una clave OrcaSlicer y vuelve a previsualizar.",
    "next_step": "Siguiente paso",
    "open_detailed_view": "Abrir vista detallada",
    "open_orca_guide": "Abrir guía Orca",
    "open_output_folder": "Abrir carpeta de salida",
    "orca_target_key": "Clave destino OrcaSlicer",
    "output_subtitle": "no destructivo",
    "preview_again": "Previsualizar otra vez",
    "preview_header": "03 // vista previa",
    "preview_subtitle": "lo que se añadirá a OrcaSlicer",
    "remove": "Eliminar",
    "risk_waiting": "Riesgo: esperando vista previa",
    "safe": "SEGURO",
    "save_mapping": "Guardar mapeo",
    "saved_mappings": "Mapeos guardados",
    "select_ignored": "Selecciona una clave ignorada.",
    "simple_empty": "Elige un bundle PrusaSlicer para obtener un resumen claro de importación.",
    "simple_summary_empty": "Elige un bundle para ver un resumen no técnico.",
    "summary_empty": "Elige un bundle PrusaSlicer o una carpeta para previsualizar la importación segura a Orca.\n\nLa vista previa no escribe archivos.\nLos perfiles Orca existentes no se modifican.",
    "source_subtitle": "archivo .ini o carpeta",
    "source_title": "01 // origen",
    "store_as_list": "Guardar valor como lista Orca",
    "tools_description": "Acciones de soporte y mantenimiento. El flujo principal queda en el panel izquierdo.",
})

TRANSLATIONS["it"].update({
    "advanced_no_section": "Nessuna sezione per questo filtro.",
    "advanced_report_empty": "Visualizza l'anteprima di un bundle per vedere il rapporto avanzato animato.",
    "advanced_report_open_first": "Visualizza l'anteprima o genera un bundle prima di aprire il rapporto avanzato.",
    "advanced_report_title": "Rapporto avanzato",
    "approx_detail": "campi approssimati",
    "bug_report": "Segnalazione bug",
    "bug_report_exported": "Segnalazione bug generata:\n{path}",
    "bundle_files_empty": "Nessuna anteprima bundle disponibile.",
    "check_updates": "Controlla aggiornamenti",
    "choose_file_first": "Scegli prima un file .ini o una cartella.",
    "choose_output_folder": "Scegli cartella di output",
    "compat_loose": "FLESSIBILE",
    "compat_strict": "RIGIDO",
    "converted_detail": "campi mappati",
    "copy_debug_info": "Copia info debug",
    "copy_file_path": "Copia percorso file",
    "debug_copied": "Info debug copiate negli appunti.",
    "drop_subtitle": "anteprima prima di scrivere qualsiasi cosa",
    "export_before_csv": "Visualizza l'anteprima o genera un bundle prima di esportare CSV.",
    "export_before_html": "Visualizza l'anteprima o genera un bundle prima di esportare HTML.",
    "export_before_pdf": "Visualizza l'anteprima o genera un bundle prima di esportare PDF.",
    "export_csv_done": "Rapporto CSV esportato:\n{path}",
    "export_html_done": "Rapporto HTML esportato:\n{path}",
    "export_pdf_done": "Rapporto PDF esportato:\n{path}",
    "generated_bundle_file": "File bundle generato",
    "generated_bundle_paths": "Percorso/i del bundle generato",
    "history_select_first": "Seleziona prima una conversione.",
    "ignored_detail": "non convertiti",
    "import_assistant": "Assistente import",
    "import_assistant_intro": "Il bundle è stato generato. Segui questi passaggi in OrcaSlicer.",
    "import_assistant_need_generate": "Genera prima il bundle .orca_printer.",
    "import_into_orca": "Importa in OrcaSlicer",
    "language_intro": "Scegli la lingua dell'interfaccia. Le chiavi tecniche Prusa/Orca mantengono il nome reale.",
    "mapping_intro": "Scegli una chiave PrusaSlicer ignorata, associala a una chiave OrcaSlicer e rilancia l'anteprima.",
    "next_step": "Prossimo passo",
    "open_detailed_view": "Apri vista dettagliata",
    "open_orca_guide": "Apri guida Orca",
    "open_output_folder": "Apri cartella output",
    "orca_target_key": "Chiave destinazione OrcaSlicer",
    "output_subtitle": "non distruttivo",
    "preview_again": "Rilancia anteprima",
    "preview_header": "03 // anteprima",
    "preview_subtitle": "cosa verrà aggiunto a OrcaSlicer",
    "remove": "Rimuovi",
    "risk_waiting": "Rischio: in attesa di anteprima",
    "safe": "SICURO",
    "save_mapping": "Salva mapping",
    "saved_mappings": "Mapping salvati",
    "select_ignored": "Seleziona una chiave ignorata.",
    "simple_empty": "Scegli un bundle PrusaSlicer per ottenere un riepilogo semplice dell'import.",
    "simple_summary_empty": "Scegli un bundle per vedere un riepilogo non tecnico.",
    "summary_empty": "Scegli un bundle PrusaSlicer o una cartella per visualizzare l'anteprima dell'import sicuro in Orca.\n\nL'anteprima non scrive file.\nI profili Orca esistenti non vengono toccati.",
    "source_subtitle": "file .ini o cartella",
    "source_title": "01 // sorgente",
    "store_as_list": "Salva valore come lista Orca",
    "tools_description": "Azioni di supporto e manutenzione. Il flusso principale resta nel pannello sinistro.",
})

TRANSLATIONS["pt"].update({
    "advanced_no_section": "Nenhuma secção para este filtro.",
    "advanced_report_empty": "Pré-visualiza um bundle para ver o relatório avançado animado.",
    "advanced_report_open_first": "Pré-visualiza ou gera um bundle antes de abrir o relatório avançado.",
    "advanced_report_title": "Relatório avançado",
    "approx_detail": "campos aproximados",
    "bug_report": "Relatório de erro",
    "bug_report_exported": "Relatório de erro gerado:\n{path}",
    "bundle_files_empty": "Ainda não há pré-visualização do bundle.",
    "check_updates": "Procurar atualizações",
    "choose_file_first": "Escolhe primeiro um ficheiro .ini ou uma pasta.",
    "choose_output_folder": "Escolher pasta de saída",
    "compat_loose": "FLEXÍVEL",
    "compat_strict": "ESTRITO",
    "converted_detail": "campos mapeados",
    "copy_debug_info": "Copiar info de debug",
    "copy_file_path": "Copiar caminho do ficheiro",
    "debug_copied": "Info de debug copiada para a área de transferência.",
    "drop_subtitle": "pré-visualiza antes de escrever qualquer coisa",
    "export_before_csv": "Pré-visualiza ou gera um bundle antes de exportar CSV.",
    "export_before_html": "Pré-visualiza ou gera um bundle antes de exportar HTML.",
    "export_before_pdf": "Pré-visualiza ou gera um bundle antes de exportar PDF.",
    "export_csv_done": "Relatório CSV exportado:\n{path}",
    "export_html_done": "Relatório HTML exportado:\n{path}",
    "export_pdf_done": "Relatório PDF exportado:\n{path}",
    "generated_bundle_file": "Ficheiro bundle gerado",
    "generated_bundle_paths": "Caminho(s) do bundle gerado",
    "history_select_first": "Seleciona primeiro uma conversão.",
    "ignored_detail": "não convertidos",
    "import_assistant": "Assistente de importação",
    "import_assistant_intro": "O teu bundle foi gerado. Segue estes passos no OrcaSlicer.",
    "import_assistant_need_generate": "Gera primeiro o bundle .orca_printer.",
    "import_into_orca": "Importar no OrcaSlicer",
    "language_intro": "Escolhe o idioma da interface. As chaves técnicas Prusa/Orca mantêm o nome real.",
    "mapping_intro": "Escolhe uma chave PrusaSlicer ignorada, associa-a a uma chave OrcaSlicer e volta a pré-visualizar.",
    "next_step": "Próximo passo",
    "open_detailed_view": "Abrir vista detalhada",
    "open_orca_guide": "Abrir guia Orca",
    "open_output_folder": "Abrir pasta de saída",
    "orca_target_key": "Chave destino OrcaSlicer",
    "output_subtitle": "não destrutivo",
    "preview_again": "Pré-visualizar novamente",
    "preview_header": "03 // pré-visualização",
    "preview_subtitle": "o que será adicionado ao OrcaSlicer",
    "remove": "Remover",
    "risk_waiting": "Risco: à espera de pré-visualização",
    "safe": "SEGURO",
    "save_mapping": "Guardar mapeamento",
    "saved_mappings": "Mapeamentos guardados",
    "select_ignored": "Seleciona uma chave ignorada.",
    "simple_empty": "Escolhe um bundle PrusaSlicer para obter um resumo simples da importação.",
    "simple_summary_empty": "Escolhe um bundle para ver um resumo não técnico.",
    "summary_empty": "Escolhe um bundle PrusaSlicer ou uma pasta para pré-visualizar a importação segura para o Orca.\n\nA pré-visualização não escreve ficheiros.\nOs perfis Orca existentes não são alterados.",
    "source_subtitle": "ficheiro .ini ou pasta",
    "source_title": "01 // origem",
    "store_as_list": "Guardar valor como lista Orca",
    "tools_description": "Ações de suporte e manutenção. O fluxo principal fica no painel esquerdo.",
})

TRANSLATIONS["nl"].update({
    "advanced_no_section": "Geen sectie voor dit filter.",
    "advanced_report_empty": "Bekijk eerst een bundelvoorbeeld om het geanimeerde geavanceerde rapport te zien.",
    "advanced_report_open_first": "Bekijk of genereer eerst een bundel voordat je het geavanceerde rapport opent.",
    "advanced_report_title": "Geavanceerd rapport",
    "approx_detail": "benaderde velden",
    "bug_report": "Bugrapport",
    "bug_report_exported": "Bugrapport gemaakt:\n{path}",
    "bundle_files_empty": "Nog geen bundelvoorbeeld.",
    "check_updates": "Updates controleren",
    "choose_file_first": "Kies eerst een .ini-bestand of map.",
    "choose_output_folder": "Uitvoermap kiezen",
    "compat_loose": "SOEPEL",
    "compat_strict": "STRIKT",
    "converted_detail": "gekoppelde velden",
    "copy_debug_info": "Debug-info kopiëren",
    "copy_file_path": "Bestandspad kopiëren",
    "debug_copied": "Debug-info gekopieerd naar het klembord.",
    "drop_subtitle": "bekijk eerst een voorbeeld voordat er iets wordt geschreven",
    "export_before_csv": "Bekijk of genereer eerst een bundel voordat je CSV exporteert.",
    "export_before_html": "Bekijk of genereer eerst een bundel voordat je HTML exporteert.",
    "export_before_pdf": "Bekijk of genereer eerst een bundel voordat je PDF exporteert.",
    "export_csv_done": "CSV-rapport geëxporteerd:\n{path}",
    "export_html_done": "HTML-rapport geëxporteerd:\n{path}",
    "export_pdf_done": "PDF-rapport geëxporteerd:\n{path}",
    "generated_bundle_file": "Gegenereerd bundelbestand",
    "generated_bundle_paths": "Pad(en) van gegenereerde bundel",
    "history_select_first": "Selecteer eerst een conversie.",
    "ignored_detail": "niet omgezet",
    "import_assistant": "Importassistent",
    "import_assistant_intro": "Je bundel is gegenereerd. Volg deze stappen in OrcaSlicer.",
    "import_assistant_need_generate": "Genereer eerst de .orca_printer-bundel.",
    "import_into_orca": "Importeren in OrcaSlicer",
    "language_intro": "Kies de interfacetaal. Technische Prusa/Orca-sleutels behouden hun echte naam.",
    "mapping_intro": "Kies een genegeerde PrusaSlicer-sleutel, koppel die aan een OrcaSlicer-sleutel en bekijk opnieuw een voorbeeld.",
    "next_step": "Volgende stap",
    "open_detailed_view": "Detailweergave openen",
    "open_orca_guide": "Orca-handleiding openen",
    "open_output_folder": "Uitvoermap openen",
    "orca_target_key": "OrcaSlicer-doelsleutel",
    "output_subtitle": "niet-destructief",
    "preview_again": "Opnieuw bekijken",
    "preview_header": "03 // voorbeeld",
    "preview_subtitle": "wat aan OrcaSlicer wordt toegevoegd",
    "remove": "Verwijderen",
    "risk_waiting": "Risico: wacht op voorbeeld",
    "safe": "VEILIG",
    "save_mapping": "Mapping opslaan",
    "saved_mappings": "Opgeslagen mappings",
    "select_ignored": "Selecteer een genegeerde sleutel.",
    "simple_empty": "Kies een PrusaSlicer-bundel voor een duidelijke importsamenvatting.",
    "simple_summary_empty": "Kies een bundel voor een niet-technische samenvatting.",
    "summary_empty": "Kies een PrusaSlicer-bundel of map om de veilige Orca-import te bekijken.\n\nVoorbeeld schrijft geen bestanden.\nBestaande Orca-profielen worden niet aangepast.",
    "source_subtitle": ".ini-bestand of map",
    "source_title": "01 // bron",
    "store_as_list": "Waarde opslaan als Orca-lijst",
    "tools_description": "Support- en onderhoudsacties. De hoofdworkflow blijft links.",
})

TRANSLATIONS["pl"].update({
    "advanced_no_section": "Brak sekcji dla tego filtra.",
    "advanced_report_empty": "Podejrzyj pakiet, aby zobaczyć animowany raport zaawansowany.",
    "advanced_report_open_first": "Podejrzyj lub wygeneruj pakiet przed otwarciem raportu zaawansowanego.",
    "advanced_report_title": "Raport zaawansowany",
    "approx_detail": "pola przybliżone",
    "bug_report": "Raport błędu",
    "bug_report_exported": "Raport błędu wygenerowany:\n{path}",
    "bundle_files_empty": "Brak podglądu pakietu.",
    "check_updates": "Sprawdź aktualizacje",
    "choose_file_first": "Najpierw wybierz plik .ini lub folder.",
    "choose_output_folder": "Wybierz folder wyjściowy",
    "compat_loose": "LUŹNY",
    "compat_strict": "ŚCISŁY",
    "converted_detail": "zmapowane pola",
    "copy_debug_info": "Kopiuj info debug",
    "copy_file_path": "Kopiuj ścieżkę pliku",
    "debug_copied": "Info debug skopiowane do schowka.",
    "drop_subtitle": "podejrzyj, zanim cokolwiek zostanie zapisane",
    "export_before_csv": "Podejrzyj lub wygeneruj pakiet przed eksportem CSV.",
    "export_before_html": "Podejrzyj lub wygeneruj pakiet przed eksportem HTML.",
    "export_before_pdf": "Podejrzyj lub wygeneruj pakiet przed eksportem PDF.",
    "export_csv_done": "Raport CSV wyeksportowany:\n{path}",
    "export_html_done": "Raport HTML wyeksportowany:\n{path}",
    "export_pdf_done": "Raport PDF wyeksportowany:\n{path}",
    "generated_bundle_file": "Wygenerowany plik pakietu",
    "generated_bundle_paths": "Ścieżka/i wygenerowanego pakietu",
    "history_select_first": "Najpierw wybierz konwersję.",
    "ignored_detail": "nieprzekonwertowane",
    "import_assistant": "Asystent importu",
    "import_assistant_intro": "Pakiet został wygenerowany. Wykonaj te kroki w OrcaSlicer.",
    "import_assistant_need_generate": "Najpierw wygeneruj pakiet .orca_printer.",
    "import_into_orca": "Importuj do OrcaSlicer",
    "language_intro": "Wybierz język interfejsu. Techniczne klucze Prusa/Orca zachowują oryginalne nazwy.",
    "mapping_intro": "Wybierz pominięty klucz PrusaSlicer, przypisz go do klucza OrcaSlicer i uruchom podgląd ponownie.",
    "next_step": "Następny krok",
    "open_detailed_view": "Otwórz widok szczegółowy",
    "open_orca_guide": "Otwórz poradnik Orca",
    "open_output_folder": "Otwórz folder wyjściowy",
    "orca_target_key": "Klucz docelowy OrcaSlicer",
    "output_subtitle": "nieniszczący",
    "preview_again": "Podgląd ponownie",
    "preview_header": "03 // podgląd",
    "preview_subtitle": "co zostanie dodane do OrcaSlicer",
    "remove": "Usuń",
    "risk_waiting": "Ryzyko: oczekiwanie na podgląd",
    "safe": "BEZPIECZNIE",
    "save_mapping": "Zapisz mapowanie",
    "saved_mappings": "Zapisane mapowania",
    "select_ignored": "Wybierz pominięty klucz.",
    "simple_empty": "Wybierz pakiet PrusaSlicer, aby zobaczyć prosty opis importu.",
    "simple_summary_empty": "Wybierz pakiet, aby zobaczyć nietechniczne podsumowanie.",
    "summary_empty": "Wybierz pakiet PrusaSlicer lub folder, aby podejrzeć bezpieczny import do Orca.\n\nPodgląd nie zapisuje plików.\nIstniejące profile Orca nie są zmieniane.",
    "source_subtitle": "plik .ini lub folder",
    "source_title": "01 // źródło",
    "store_as_list": "Zapisz wartość jako listę Orca",
    "tools_description": "Akcje wsparcia i konserwacji. Główny przepływ zostaje w lewym panelu.",
})

TRANSLATIONS["de"].update({
    "mapping_need_preview": "Zeige ein Bundle in der Vorschau an, bevor du ignorierte Schlüssel bearbeitest.",
    "mapping_no_ignored": "Im aktuellen Bericht gibt es keine ignorierten Schlüssel.",
    "mapping_need_target": "Wähle einen ignorierten Schlüssel und gib einen Orca-Zielschlüssel ein.",
    "mapping_saved": "Mapping gespeichert. Starte die Vorschau erneut, um es anzuwenden.",
    "bug_report_need_preview": "Zeige zuerst eine Vorschau an oder erzeuge ein Bundle, bevor du einen Fehlerbericht erstellst.",
    "history_no_snapshot": "Dieser ältere Verlaufseintrag hat keinen gespeicherten Bericht.",
    "info_tab": "Info",
    "info_title": "Diesen Bildschirm verstehen",
    "info_intro": "Die App importiert nie direkt in OrcaSlicer. Sie erstellt ein sicheres Bundle, das du danach selbst in Orca importierst.",
    "info_flow_title": "Empfohlener Ablauf",
    "info_flow_body": "Wähle eine .ini-Datei oder einen Ordner, starte die Vorschau, lies Einfach oder Erweitert und erzeuge dann das .orca_printer-Bundle.",
    "info_safe_title": "Sicherer Modus",
    "info_safe_body": "Die Vorschau schreibt nichts. Erzeugen schreibt nur neue Bundle-Dateien in den Ausgabeordner. Bestehende Orca-Profile werden nicht geändert.",
    "info_prefix_title": "Präfix",
    "info_prefix_body": "Präfix AN ergänzt PrusaToOrca in generierten Profilnamen. Lass es aktiv, um Namenskollisionen zu reduzieren.",
    "info_compat_title": "Streng / locker",
    "info_compat_body": "Streng bindet importierte Filament- und Prozessprofile an importierte Drucker. Locker macht sie wiederverwendbarer, aber weniger isoliert.",
    "info_reports_title": "Berichte",
    "info_reports_body": "Einfach ist für normale Nutzer. Technisch zeigt erzeugte Bundles. Erweitert zeigt exakte, ungefähre und ignorierte Felder.",
    "info_mapping_title": "Mapping-Editor",
    "info_mapping_body": "Wenn ein ignorierter Schlüssel wichtig ist, ordne ihn einem OrcaSlicer-Schlüssel zu und starte vor dem Erzeugen erneut die Vorschau.",
    "reopen_report": "Bericht erneut öffnen",
    "refresh": "Aktualisieren",
})

TRANSLATIONS["es"].update({
    "mapping_need_preview": "Previsualiza un bundle antes de editar mapeos de claves ignoradas.",
    "mapping_no_ignored": "No hay claves ignoradas en el informe actual.",
    "mapping_need_target": "Selecciona una clave ignorada e introduce una clave Orca de destino.",
    "mapping_saved": "Mapeo guardado. Vuelve a previsualizar para aplicarlo.",
    "bug_report_need_preview": "Previsualiza o genera un bundle antes de crear un informe de error.",
    "history_no_snapshot": "Este elemento antiguo del historial no tiene informe guardado.",
    "info_tab": "Ayuda",
    "info_title": "Entender esta pantalla",
    "info_intro": "La app nunca importa directamente en OrcaSlicer. Prepara un bundle seguro y luego lo importas tú en Orca.",
    "info_flow_title": "Flujo recomendado",
    "info_flow_body": "Elige un archivo .ini o una carpeta, ejecuta la vista previa, lee Simple o Avanzado y genera el bundle .orca_printer.",
    "info_safe_title": "Modo seguro",
    "info_safe_body": "La vista previa no escribe nada. Generar solo escribe nuevos bundles en la carpeta de salida. Los perfiles Orca existentes no se modifican.",
    "info_prefix_title": "Prefijo",
    "info_prefix_body": "Prefijo ON añade PrusaToOrca a los nombres generados. Déjalo activado para reducir colisiones de nombres.",
    "info_compat_title": "Estricto / flexible",
    "info_compat_body": "Estricto vincula filamentos y procesos importados a las impresoras importadas. Flexible los hace más reutilizables, pero menos aislados.",
    "info_reports_title": "Informes",
    "info_reports_body": "Simple es para usuarios normales. Técnico muestra bundles generados. Avanzado muestra campos exactos, aproximados e ignorados.",
    "info_mapping_title": "Editor de mapeo",
    "info_mapping_body": "Si una clave ignorada importa, asígnala a una clave OrcaSlicer y vuelve a previsualizar antes de generar.",
    "reopen_report": "Reabrir informe",
    "refresh": "Actualizar",
})

TRANSLATIONS["it"].update({
    "mapping_need_preview": "Visualizza l'anteprima di un bundle prima di modificare i mapping delle chiavi ignorate.",
    "mapping_no_ignored": "Nessuna chiave ignorata nel rapporto attuale.",
    "mapping_need_target": "Seleziona una chiave ignorata e inserisci una chiave Orca di destinazione.",
    "mapping_saved": "Mapping salvato. Rilancia l'anteprima per applicarlo.",
    "bug_report_need_preview": "Visualizza l'anteprima o genera un bundle prima di creare una segnalazione bug.",
    "history_no_snapshot": "Questo elemento storico non ha un rapporto salvato.",
    "info_tab": "Aiuto",
    "info_title": "Capire questa schermata",
    "info_intro": "L'app non importa mai direttamente in OrcaSlicer. Prepara un bundle sicuro, poi lo importi tu in Orca.",
    "info_flow_title": "Flusso consigliato",
    "info_flow_body": "Scegli un file .ini o una cartella, avvia l'anteprima, leggi Semplice o Avanzato e genera il bundle .orca_printer.",
    "info_safe_title": "Modalità sicura",
    "info_safe_body": "L'anteprima non scrive nulla. Genera scrive solo nuovi bundle nella cartella output. I profili Orca esistenti non vengono modificati.",
    "info_prefix_title": "Prefisso",
    "info_prefix_body": "Prefisso ON aggiunge PrusaToOrca ai nomi generati. Tienilo attivo per ridurre il rischio di collisioni.",
    "info_compat_title": "Rigido / flessibile",
    "info_compat_body": "Rigido lega filamenti e processi importati alle stampanti importate. Flessibile li rende più riutilizzabili, ma meno isolati.",
    "info_reports_title": "Rapporti",
    "info_reports_body": "Semplice è per utenti normali. Tecnico mostra i bundle generati. Avanzato mostra campi esatti, approssimati e ignorati.",
    "info_mapping_title": "Editor mapping",
    "info_mapping_body": "Se una chiave ignorata è importante, associala a una chiave OrcaSlicer e rilancia l'anteprima prima di generare.",
    "reopen_report": "Riapri rapporto",
    "refresh": "Aggiorna",
})

TRANSLATIONS["pt"].update({
    "mapping_need_preview": "Pré-visualiza um bundle antes de editar mapeamentos de chaves ignoradas.",
    "mapping_no_ignored": "Não há chaves ignoradas no relatório atual.",
    "mapping_need_target": "Seleciona uma chave ignorada e introduz uma chave Orca de destino.",
    "mapping_saved": "Mapeamento guardado. Volta a pré-visualizar para o aplicar.",
    "bug_report_need_preview": "Pré-visualiza ou gera um bundle antes de criar um relatório de erro.",
    "history_no_snapshot": "Este item antigo do histórico não tem relatório guardado.",
    "info_tab": "Ajuda",
    "info_title": "Compreender este ecrã",
    "info_intro": "A app nunca importa diretamente no OrcaSlicer. Prepara um bundle seguro e depois importas esse bundle no Orca.",
    "info_flow_title": "Fluxo recomendado",
    "info_flow_body": "Escolhe um ficheiro .ini ou uma pasta, executa a pré-visualização, lê Simples ou Avançado e gera o bundle .orca_printer.",
    "info_safe_title": "Modo seguro",
    "info_safe_body": "A pré-visualização não escreve nada. Gerar só escreve novos bundles na pasta de saída. Os perfis Orca existentes não são modificados.",
    "info_prefix_title": "Prefixo",
    "info_prefix_body": "Prefixo ON adiciona PrusaToOrca aos nomes gerados. Mantém ativo para reduzir colisões de nomes.",
    "info_compat_title": "Estrito / flexível",
    "info_compat_body": "Estrito liga filamentos e processos importados às impressoras importadas. Flexível torna-os mais reutilizáveis, mas menos isolados.",
    "info_reports_title": "Relatórios",
    "info_reports_body": "Simples é para utilizadores normais. Técnico mostra bundles gerados. Avançado mostra campos exatos, aproximados e ignorados.",
    "info_mapping_title": "Editor de mapeamento",
    "info_mapping_body": "Se uma chave ignorada for importante, associa-a a uma chave OrcaSlicer e volta a pré-visualizar antes de gerar.",
    "reopen_report": "Reabrir relatório",
    "refresh": "Atualizar",
})

TRANSLATIONS["nl"].update({
    "mapping_need_preview": "Bekijk eerst een bundelvoorbeeld voordat je mappings voor genegeerde sleutels bewerkt.",
    "mapping_no_ignored": "Geen genegeerde sleutels in het huidige rapport.",
    "mapping_need_target": "Selecteer een genegeerde sleutel en voer een Orca-doelsleutel in.",
    "mapping_saved": "Mapping opgeslagen. Bekijk opnieuw een voorbeeld om dit toe te passen.",
    "bug_report_need_preview": "Bekijk of genereer eerst een bundel voordat je een bugrapport maakt.",
    "history_no_snapshot": "Dit oudere geschiedenisitem heeft geen opgeslagen rapport.",
    "info_tab": "Info",
    "info_title": "Dit scherm begrijpen",
    "info_intro": "De app importeert nooit rechtstreeks in OrcaSlicer. Hij maakt een veilige bundel die je daarna zelf in Orca importeert.",
    "info_flow_title": "Aanbevolen workflow",
    "info_flow_body": "Kies een .ini-bestand of map, draai Voorbeeld, lees Simpel of Geavanceerd en maak daarna de .orca_printer-bundel.",
    "info_safe_title": "Veilige modus",
    "info_safe_body": "Voorbeeld schrijft niets. Genereren schrijft alleen nieuwe bundels in de uitvoermap. Bestaande Orca-profielen worden niet gewijzigd.",
    "info_prefix_title": "Prefix",
    "info_prefix_body": "Prefix AAN voegt PrusaToOrca toe aan gegenereerde profielnamen. Laat dit aan om naamconflicten te beperken.",
    "info_compat_title": "Strikt / soepel",
    "info_compat_body": "Strikt koppelt geïmporteerde filament- en procesprofielen aan geïmporteerde printers. Soepel maakt ze herbruikbaarder, maar minder geïsoleerd.",
    "info_reports_title": "Rapporten",
    "info_reports_body": "Simpel is voor normale gebruikers. Technisch toont gegenereerde bundels. Geavanceerd toont exacte, benaderde en genegeerde velden.",
    "info_mapping_title": "Mapping-editor",
    "info_mapping_body": "Als een genegeerde sleutel belangrijk is, koppel die aan een OrcaSlicer-sleutel en bekijk opnieuw een voorbeeld voor het genereren.",
    "reopen_report": "Rapport opnieuw openen",
    "refresh": "Vernieuwen",
})

TRANSLATIONS["pl"].update({
    "mapping_need_preview": "Podejrzyj pakiet przed edycją mapowania pominiętych kluczy.",
    "mapping_no_ignored": "W bieżącym raporcie nie ma pominiętych kluczy.",
    "mapping_need_target": "Wybierz pominięty klucz i wpisz docelowy klucz Orca.",
    "mapping_saved": "Mapowanie zapisane. Uruchom podgląd ponownie, aby je zastosować.",
    "bug_report_need_preview": "Podejrzyj lub wygeneruj pakiet przed utworzeniem raportu błędu.",
    "history_no_snapshot": "Ten starszy wpis historii nie ma zapisanego raportu.",
    "info_tab": "Pomoc",
    "info_title": "Jak czytać ten ekran",
    "info_intro": "Aplikacja nigdy nie importuje bezpośrednio do OrcaSlicer. Przygotowuje bezpieczny pakiet, który potem importujesz samodzielnie w Orca.",
    "info_flow_title": "Zalecany przepływ",
    "info_flow_body": "Wybierz plik .ini lub folder, uruchom podgląd, przeczytaj Prosty lub Zaawansowany, a potem wygeneruj pakiet .orca_printer.",
    "info_safe_title": "Tryb bezpieczny",
    "info_safe_body": "Podgląd niczego nie zapisuje. Generowanie zapisuje tylko nowe pakiety w folderze wyjściowym. Istniejące profile Orca nie są zmieniane.",
    "info_prefix_title": "Prefiks",
    "info_prefix_body": "Prefiks ON dodaje PrusaToOrca do nazw generowanych profili. Zostaw go włączonego, aby ograniczyć kolizje nazw.",
    "info_compat_title": "Ścisły / luźny",
    "info_compat_body": "Ścisły wiąże importowane filamenty i procesy z importowanymi drukarkami. Luźny ułatwia ponowne użycie, ale daje mniejszą izolację.",
    "info_reports_title": "Raporty",
    "info_reports_body": "Prosty jest dla zwykłych użytkowników. Techniczny pokazuje wygenerowane pakiety. Zaawansowany pokazuje pola dokładne, przybliżone i pominięte.",
    "info_mapping_title": "Edytor mapowania",
    "info_mapping_body": "Jeśli pominięty klucz jest ważny, przypisz go do klucza OrcaSlicer i uruchom podgląd ponownie przed generowaniem.",
    "reopen_report": "Otwórz raport ponownie",
    "refresh": "Odśwież",
})

APP_BG = PANEL_BG = PANEL_TINT = INK = MUTED = LINE = ""
HEADER_BG = HEADER_FG = TEAL = TEAL_DARK = ORANGE = ORANGE_DARK = RED_ORANGE = CREAM = ""
ADV_PROGRESS_BG = ""


def apply_theme(mode):
    global APP_BG, PANEL_BG, PANEL_TINT, INK, MUTED, LINE, HEADER_BG, HEADER_FG
    global TEAL, TEAL_DARK, ORANGE, ORANGE_DARK, RED_ORANGE, CREAM, ADV_PROGRESS_BG
    global ADV_BG, ADV_PANEL, ADV_PANEL_ALT, ADV_LINE, ADV_TEXT, ADV_MUTED, ADV_GREEN, ADV_RED, ADV_BLUE

    palette = THEMES.get(mode, THEMES["day"])
    APP_BG = palette["APP_BG"]
    PANEL_BG = palette["PANEL_BG"]
    PANEL_TINT = palette["PANEL_TINT"]
    INK = palette["INK"]
    MUTED = palette["MUTED"]
    LINE = palette["LINE"]
    HEADER_BG = palette["HEADER_BG"]
    HEADER_FG = palette["HEADER_FG"]
    TEAL = palette["TEAL"]
    TEAL_DARK = palette["TEAL_DARK"]
    ORANGE = palette["ORANGE"]
    ORANGE_DARK = palette["ORANGE_DARK"]
    RED_ORANGE = palette["RED_ORANGE"]
    ADV_PROGRESS_BG = palette["ADV_PROGRESS_BG"]
    CREAM = APP_BG

    ADV_BG = APP_BG
    ADV_PANEL = PANEL_BG
    ADV_PANEL_ALT = PANEL_TINT
    ADV_LINE = LINE
    ADV_TEXT = INK
    ADV_MUTED = MUTED
    ADV_GREEN = TEAL_DARK
    ADV_RED = RED_ORANGE
    ADV_BLUE = TEAL

UI_FONT = ("Space Mono", 10)
UI_FONT_BOLD = ("Space Mono", 10, "bold")
TITLE_FONT = ("Archivo Black", 28)
SECTION_FONT = ("Space Mono", 12, "bold")

STAR = "\u2605"
TRIANGLE = "\u25b3"
CROSS = "\u00d7"
CHECK = "\u2611"

apply_theme("day")
ADV_FONT = ("Segoe UI", 9)
ADV_FONT_BOLD = ("Segoe UI", 9, "bold")
ADV_TITLE_FONT = ("Segoe UI", 15, "bold")
ADV_SECTION_FONT = ("Segoe UI", 12, "bold")
ADV_TABLE_FONT = ("Consolas", 8)


def resource_path(name):
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return Path(base) / name


def app_root():
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        return exe_dir.parent if exe_dir.name.lower() == "dist" else exe_dir
    return Path(__file__).resolve().parent


def app_file(name):
    return app_root() / name


def load_settings():
    path = app_file(SETTINGS_FILE)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(settings):
    path = app_file(SETTINGS_FILE)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def load_theme_preference():
    return load_settings().get("theme", "day")


def save_theme_preference(mode):
    settings = load_settings()
    settings["theme"] = mode
    save_settings(settings)


def load_language_preference():
    language = load_settings().get("language", "fr")
    return language if language in LANGUAGE_CODES else "fr"


def save_language_preference(language):
    settings = load_settings()
    settings["language"] = language if language in LANGUAGE_CODES else "fr"
    save_settings(settings)


def translate(language, key, **kwargs):
    text = TRANSLATIONS.get(language, {}).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text


def compare_versions(left, right):
    def parts(value):
        clean = str(value).strip().lstrip("vV")
        numbers = []
        for item in clean.split("."):
            digits = "".join(ch for ch in item if ch.isdigit())
            numbers.append(int(digits or 0))
        return (numbers + [0, 0, 0])[:3]

    a = parts(left)
    b = parts(right)
    return (a > b) - (a < b)


def load_embedded_fonts():
    if sys.platform != "win32":
        return
    font_dir = resource_path("assets") / "fonts"
    if not font_dir.exists():
        return
    add_font_private = 0x10
    for font_path in font_dir.glob("*.ttf"):
        try:
            ctypes.windll.gdi32.AddFontResourceExW(str(font_path), add_font_private, 0)
        except Exception:
            pass


class PrusaToOrcaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PrusaToOrca")
        self.theme_mode = tk.StringVar(value=load_theme_preference())
        self.language = tk.StringVar(value=load_language_preference())
        apply_theme(self.theme_mode.get())
        self.root.configure(bg=APP_BG)
        self.apply_window_icon(self.root)
        self.configure_main_window()

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar(value=str(Path.home() / "Desktop"))
        self.compatibility = tk.StringVar(value="strict")
        self.prefix_profiles = tk.BooleanVar(value=True)
        self.source_mode = tk.StringVar(value="file")
        self.last_preview = None
        self.report_views = {}
        self.report_rows = []
        self.advanced_model = None
        self.advanced_window = None
        self.advanced_body = None
        self.advanced_sidebar = None
        self.advanced_search = None
        self.advanced_filter = tk.StringVar(value="all")
        self.simple_tab = None
        self.advanced_tab = None
        self.advanced_tab_bars = []
        self.advanced_tab_counter_jobs = []
        self.advanced_window_bars = []
        self.import_wizard = None
        self.tools_window = None
        self.history = self.load_history()
        self.custom_mappings = self.load_custom_mappings()
        self.last_output_folder = None
        self.risk_label = tk.StringVar(value=self.tr("risk_waiting"))
        self.progress_label = tk.StringVar(value="")
        self.current_report_tab = "Simple summary"
        self.tab_buttons = {}
        self.quick_buttons = {}
        self.logo_image = None

        self._build()
        self._wire_drag_drop()

    def tr(self, key, **kwargs):
        return translate(self.language.get(), key, **kwargs)

    def apply_window_icon(self, window):
        try:
            window.iconbitmap(resource_path("logo.ico"))
        except Exception:
            pass

    def screen_size(self):
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def fitted_window_size(self, width, height, min_width, min_height, width_ratio=0.9, height_ratio=0.88):
        screen_w, screen_h = self.screen_size()
        usable_w = max(720, screen_w - 80)
        usable_h = max(520, screen_h - 100)
        min_width = min(min_width, usable_w)
        min_height = min(min_height, usable_h)
        fitted_w = min(width, int(screen_w * width_ratio), usable_w)
        fitted_h = min(height, int(screen_h * height_ratio), usable_h)
        return max(min_width, fitted_w), max(min_height, fitted_h), min_width, min_height

    def center_window(self, window, width=None, height=None, parent=None):
        window.update_idletasks()
        screen_w, screen_h = self.screen_size()
        width = width or window.winfo_width() or window.winfo_reqwidth()
        height = height or window.winfo_height() or window.winfo_reqheight()
        if parent and parent.winfo_exists() and parent.winfo_viewable():
            parent.update_idletasks()
            base_x = parent.winfo_rootx()
            base_y = parent.winfo_rooty()
            base_w = max(parent.winfo_width(), 1)
            base_h = max(parent.winfo_height(), 1)
            x = base_x + (base_w - width) // 2
            y = base_y + (base_h - height) // 2
        else:
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
        x = max(0, min(x, max(0, screen_w - width)))
        y = max(0, min(y, max(0, screen_h - height)))
        window.geometry(f"{int(width)}x{int(height)}+{int(x)}+{int(y)}")

    def configure_main_window(self):
        width, height, min_width, min_height = self.fitted_window_size(1180, 760, 960, 620)
        self.root.minsize(min_width, min_height)
        self.center_window(self.root, width, height)

    def configure_child_window(self, window, title, width, height, min_width, min_height, bg=None, parent=None):
        width, height, min_width, min_height = self.fitted_window_size(width, height, min_width, min_height)
        window.title(title)
        window.minsize(min_width, min_height)
        window.configure(bg=bg or APP_BG)
        window.resizable(True, True)
        self.apply_window_icon(window)
        if parent and window is not parent:
            window.transient(parent)
        self.center_window(window, width, height, parent or self.root)
        return window

    def make_child_window(self, title, width, height, min_width, min_height, bg=None, parent=None):
        window = tk.Toplevel(parent or self.root)
        return self.configure_child_window(window, title, width, height, min_width, min_height, bg=bg, parent=parent or self.root)

    def _build(self):
        shell = tk.Frame(self.root, bg=APP_BG, padx=22, pady=18)
        shell.pack(fill="both", expand=True)

        self._build_topbar(shell)

        body = tk.Frame(shell, bg=APP_BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0, minsize=360)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left_shell = tk.Frame(body, bg=APP_BG)
        left_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left_shell.grid_rowconfigure(0, weight=1)
        left_shell.grid_columnconfigure(0, weight=1)
        left_canvas = tk.Canvas(left_shell, bg=APP_BG, highlightthickness=0, width=380)
        left_scroll = tk.Scrollbar(left_shell, orient="vertical", command=left_canvas.yview)
        left = tk.Frame(left_canvas, bg=APP_BG)
        left_window = left_canvas.create_window((0, 0), window=left, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_canvas.grid(row=0, column=0, sticky="nsew")
        left_scroll.grid(row=0, column=1, sticky="ns")
        left.bind("<Configure>", lambda _event: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.bind("<Configure>", lambda event: left_canvas.itemconfigure(left_window, width=event.width))
        left_canvas.bind("<Enter>", lambda _event: left_canvas.bind_all("<MouseWheel>", lambda event, canvas=left_canvas: self._on_canvas_mousewheel(canvas, event)))
        left_canvas.bind("<Leave>", lambda _event: left_canvas.unbind_all("<MouseWheel>"))

        right = tk.Frame(body, bg=APP_BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_import_panel(left)
        self._build_actions(left)
        self._build_options_panel(left)
        self._build_preview_panel(right)
        self._build_report_panel(right)

    def _on_canvas_mousewheel(self, canvas, event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_topbar(self, parent):
        top = tk.Frame(parent, bg=APP_BG)
        top.pack(fill="x", pady=(0, 18))
        top.grid_columnconfigure(1, weight=1)

        brand = tk.Frame(top, bg=APP_BG)
        brand.grid(row=0, column=0, sticky="w")
        logo_path = resource_path("assets/logo_header.png")
        if logo_path.exists():
            try:
                self.logo_image = tk.PhotoImage(file=str(logo_path))
                tk.Label(brand, image=self.logo_image, bg=APP_BG).pack(side="left", padx=(0, 12))
            except Exception:
                self.logo_image = None

        brand_text = tk.Frame(brand, bg=APP_BG)
        brand_text.pack(side="left", anchor="w")
        tk.Label(brand_text, text="PrusaToOrca", font=TITLE_FONT, bg=APP_BG, fg=INK).pack(anchor="w")
        tk.Label(
            brand_text,
            text=self.tr("app_subtitle"),
            font=UI_FONT,
            bg=APP_BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(2, 0))

        quick_actions = tk.Frame(top, bg=APP_BG)
        quick_actions.grid(row=0, column=1, sticky="e")
        for key, text, command in [
            ("safe", self.tr("safe"), self.show_safety_info),
            ("prefix", self.tr("prefix_on"), self.toggle_prefix),
            ("compat", self.tr("compat_strict"), self.toggle_compatibility),
            ("theme", self.tr("night"), self.toggle_theme),
            ("language", self.language.get().upper(), self.open_language_selector),
            ("history", self.tr("history").upper(), self.open_history),
            ("tools", self.tr("tools").upper(), self.open_tools),
        ]:
            btn = self._top_button(quick_actions, text, command)
            btn.pack(side="left", padx=(8, 0))
            self.quick_buttons[key] = btn
        self.update_quick_actions()

        accent = tk.Frame(parent, bg=APP_BG, height=6)
        accent.pack(fill="x", pady=(0, 18))
        accent.pack_propagate(False)
        for color, weight in [(INK, 4), (ORANGE, 3), (RED_ORANGE, 2), (TEAL, 3)]:
            tk.Frame(accent, bg=color).pack(side="left", fill="both", expand=True)

    def _panel(self, parent, title, subtitle=None):
        frame = tk.Frame(parent, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1)
        frame.pack(fill="x", pady=(0, 10))
        header = tk.Frame(frame, bg=HEADER_BG)
        header.pack(fill="x")
        tk.Frame(header, bg=ORANGE, width=6).pack(side="left", fill="y")
        tk.Label(header, text=title, font=SECTION_FONT, bg=HEADER_BG, fg=HEADER_FG, padx=14, pady=9).pack(side="left")
        if subtitle:
            tk.Label(header, text=subtitle, font=UI_FONT, bg=HEADER_BG, fg=MUTED, padx=12).pack(side="right")
        content = tk.Frame(frame, bg=PANEL_BG, padx=14, pady=10)
        content.pack(fill="both", expand=True)
        return content

    def _build_import_panel(self, parent):
        panel = self._panel(parent, self.tr("source_title"), self.tr("source_subtitle"))

        self.drop_zone = tk.Frame(panel, bg=PANEL_TINT, highlightbackground=ORANGE, highlightthickness=2, height=104)
        self.drop_zone.pack(fill="x")
        self.drop_zone.pack_propagate(False)
        drop_accent = tk.Frame(self.drop_zone, bg=TEAL, width=8)
        drop_accent.pack(side="left", fill="y")
        drop_copy = tk.Frame(self.drop_zone, bg=PANEL_TINT)
        drop_copy.pack(side="left", fill="both", expand=True)
        tk.Label(
            drop_copy,
            text=self.tr("drop_title"),
            font=("Arial Black", 16),
            bg=PANEL_TINT,
            fg=INK,
        ).pack(anchor="center", expand=True, pady=(12, 0))
        tk.Label(
            drop_copy,
            text=self.tr("drop_subtitle"),
            font=UI_FONT_BOLD,
            bg=PANEL_TINT,
            fg=ORANGE_DARK,
            wraplength=280,
            justify="center",
        ).pack(anchor="center", pady=(0, 12), padx=8)
        tk.Label(
            panel,
            textvariable=self.input_path,
            font=UI_FONT,
            bg=PANEL_BG,
            fg=MUTED,
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(8, 6))

        row = tk.Frame(panel, bg=PANEL_BG)
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1, uniform="source_actions")
        row.grid_columnconfigure(1, weight=1, uniform="source_actions")
        choose_file_btn = self._button(row, self.tr("choose_file"), self.choose_input, variant="secondary")
        choose_file_btn.configure(padx=8, pady=8)
        choose_file_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        choose_folder_btn = self._button(row, self.tr("choose_folder"), self.choose_folder, variant="secondary")
        choose_folder_btn.configure(padx=8, pady=8)
        choose_folder_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        clear_btn = self._button(row, self.tr("clear"), self.clear_input, variant="ghost")
        clear_btn.configure(padx=8, pady=7)
        clear_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _build_options_panel(self, parent):
        panel = self._panel(parent, "02 // output", self.tr("output_subtitle"))

        tk.Label(panel, text=self.tr("output_folder"), font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK).pack(anchor="w")
        out_row = tk.Frame(panel, bg=PANEL_BG)
        out_row.pack(fill="x", pady=(6, 12))
        tk.Entry(
            out_row,
            textvariable=self.output_path,
            font=UI_FONT,
            bg=PANEL_BG,
            fg=INK,
            insertbackground=INK,
            relief="flat",
            highlightbackground=LINE,
            highlightthickness=1,
        ).pack(side="left", fill="x", expand=True, ipady=8)
        self._button(out_row, "...", self.choose_output, variant="secondary", width=4).pack(side="left", padx=(8, 0))
        self._button(out_row, self.tr("folder"), self.open_output_folder, variant="secondary", width=7).pack(side="left", padx=(8, 0))

        tk.Label(panel, textvariable=self.risk_label, font=UI_FONT_BOLD, bg=PANEL_BG, fg=TEAL_DARK).pack(anchor="w", pady=(0, 8))

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=APP_BG)
        actions.pack(fill="x", pady=(2, 0))
        self.preview_btn = self._button(actions, self.tr("preview_button"), self.preview, variant="secondary")
        self.preview_btn.pack(fill="x", pady=(0, 8))
        self.convert_btn = self._button(actions, self.tr("generate"), self.convert, variant="primary")
        self.convert_btn.pack(fill="x")
        self.progress_canvas = tk.Canvas(actions, height=10, bg=PANEL_TINT, highlightthickness=1, highlightbackground=LINE)
        self.progress_canvas.pack(fill="x", pady=(10, 4))
        self.progress_fill = self.progress_canvas.create_rectangle(0, 0, 0, 10, fill=TEAL, outline="")
        tk.Label(actions, textvariable=self.progress_label, font=UI_FONT, bg=APP_BG, fg=MUTED).pack(anchor="w")

    def _build_preview_panel(self, parent):
        header = tk.Frame(parent, bg=APP_BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text=self.tr("preview_header"), font=SECTION_FONT, bg=APP_BG, fg=INK).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text=self.tr("preview_subtitle"),
            font=UI_FONT,
            bg=APP_BG,
            fg=MUTED,
        ).grid(row=0, column=1, sticky="e")

    def _build_report_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tabs = tk.Frame(frame, bg=PANEL_BG)
        tabs.grid(row=0, column=0, sticky="ew")
        tabs.grid_columnconfigure(5, weight=1)
        for label, name in [
            (self.tr("simple_tab"), "Simple summary"),
            (self.tr("technical_tab"), "Summary"),
            (self.tr("bundle_files_tab"), "Bundle files"),
            (self.tr("advanced_report"), "Advanced report"),
            (self.tr("info_tab"), "Info"),
        ]:
            btn = tk.Button(
                tabs,
                text=label,
                command=lambda tab_name=name: self.show_report_tab(tab_name),
                font=UI_FONT_BOLD,
                bg=TEAL_DARK if name == self.current_report_tab else PANEL_BG,
                fg=PANEL_BG if name == self.current_report_tab else MUTED,
                padx=12,
                pady=9,
                relief="flat",
                borderwidth=0,
                highlightbackground=LINE,
                highlightthickness=1,
                cursor="hand2",
            )
            btn.pack(side="left")
            self.tab_buttons[name] = btn
        self.export_btn = self._button(tabs, self.tr("csv"), self.export_csv, variant="secondary")
        self.export_btn.pack(side="right", padx=(8, 0))
        self._button(tabs, self.tr("export_html"), self.export_html, variant="secondary").pack(side="right", padx=(8, 0))
        self._button(tabs, self.tr("export_pdf"), self.export_pdf, variant="secondary").pack(side="right", padx=(8, 0))

        self.report = tk.Text(
            frame,
            bg=PANEL_BG,
            fg=INK,
            insertbackground=INK,
            relief="flat",
            borderwidth=0,
            font=UI_FONT,
            wrap="word",
            padx=18,
            pady=16,
        )
        self.report.grid(row=1, column=0, sticky="nsew")

        self.simple_tab = tk.Frame(frame, bg=PANEL_BG, padx=18, pady=16)
        self.simple_tab.grid(row=1, column=0, sticky="nsew")
        self.simple_tab.grid_remove()

        self.advanced_tab = tk.Frame(frame, bg=PANEL_BG, padx=18, pady=16)
        self.advanced_tab.grid(row=1, column=0, sticky="nsew")
        self.advanced_tab.grid_remove()

        default_views = {
            "Simple summary": self.tr("simple_summary_empty") + "\n",
            "Summary": self.tr("summary_empty") + "\n",
            "Bundle files": self.tr("bundle_files_empty") + "\n",
            "Advanced report": self.tr("advanced_report_empty") + "\n",
            "Info": self.build_info_text(),
        }
        self.set_report_views(self.report_views or default_views, self.report_rows, self.advanced_model)
        self.report.configure(state="disabled")

    def _button(self, parent, text, command, variant="primary", width=None):
        if variant == "primary":
            bg, fg, border, active_bg = ORANGE, PANEL_BG, ORANGE_DARK, RED_ORANGE
        elif variant == "secondary":
            bg, fg, border, active_bg = PANEL_BG, INK, TEAL, TEAL
        else:
            bg, fg, border, active_bg = APP_BG, MUTED, APP_BG, PANEL_TINT
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=UI_FONT_BOLD if variant == "primary" else UI_FONT,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=PANEL_BG if variant != "ghost" else INK,
            relief="flat",
            borderwidth=0,
            highlightbackground=border,
            highlightthickness=1,
            padx=16,
            pady=10,
            width=width,
            cursor="hand2",
        )

    def _top_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=UI_FONT_BOLD,
            bg=PANEL_BG,
            fg=INK,
            activebackground=HEADER_BG,
            activeforeground=HEADER_FG,
            relief="flat",
            borderwidth=0,
            highlightbackground=LINE,
            highlightthickness=1,
            padx=10,
            pady=8,
            cursor="hand2",
        )

    def show_safety_info(self):
        messagebox.showinfo(
            self.tr("safe"),
            "Safe mode is always on.\n\n"
            "- Preview does not write files\n"
            "- Generated presets are prefixed by default\n"
            "- Existing OrcaSlicer preset files are not edited by PrusaToOrca\n"
            "- Strict compatibility keeps imported presets tied to imported printers",
        )

    def toggle_prefix(self):
        self.prefix_profiles.set(not self.prefix_profiles.get())
        self.update_quick_actions()
        self.refresh_preview_if_ready()

    def toggle_compatibility(self):
        self.compatibility.set("loose" if self.compatibility.get() == "strict" else "strict")
        self.update_quick_actions()
        self.refresh_preview_if_ready()

    def toggle_theme(self):
        next_mode = "night" if self.theme_mode.get() == "day" else "day"
        self.theme_mode.set(next_mode)
        save_theme_preference(next_mode)
        apply_theme(next_mode)
        self.rebuild_ui()

    def open_language_selector(self):
        win = self.make_child_window(self.tr("language"), 520, 420, 460, 360)

        shell = tk.Frame(win, bg=APP_BG, padx=18, pady=16)
        shell.pack(fill="both", expand=True)
        tk.Label(shell, text=self.tr("language"), font=SECTION_FONT, bg=APP_BG, fg=INK).pack(anchor="w")
        tk.Label(
            shell,
            text=self.tr("language_intro"),
            font=UI_FONT,
            bg=APP_BG,
            fg=MUTED,
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(4, 14))

        grid = tk.Frame(shell, bg=APP_BG)
        grid.pack(fill="both", expand=True)
        for index, (code, short, name) in enumerate(LANGUAGE_OPTIONS):
            active = code == self.language.get()
            btn = tk.Button(
                grid,
                text=f"{short}  {name}",
                command=lambda lang=code, window=win: self.set_language(lang, window),
                font=UI_FONT_BOLD if active else UI_FONT,
                bg=TEAL if active else PANEL_BG,
                fg=PANEL_BG if active else INK,
                activebackground=TEAL,
                activeforeground=PANEL_BG,
                relief="flat",
                borderwidth=0,
                highlightbackground=LINE,
                highlightthickness=1,
                padx=12,
                pady=10,
                anchor="w",
                cursor="hand2",
            )
            btn.grid(row=index // 2, column=index % 2, sticky="ew", padx=(0, 8), pady=(0, 8))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        self._button(shell, self.tr("cancel"), win.destroy, variant="ghost").pack(anchor="e", pady=(8, 0))

    def set_language(self, language, window=None):
        if language not in LANGUAGE_CODES:
            return
        self.language.set(language)
        save_language_preference(language)
        self.refresh_report_language()
        if window and window.winfo_exists():
            window.destroy()
        self.rebuild_ui()

    def refresh_report_language(self):
        if not self.last_preview:
            return
        done = bool(self.advanced_model and self.advanced_model.get("done"))
        views, rows, advanced_model = self.build_report_views(self.last_preview, done=done)
        self.report_views = views
        self.report_rows = rows
        self.advanced_model = advanced_model

    def rebuild_ui(self):
        for job in self.advanced_tab_counter_jobs:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
        self.advanced_tab_counter_jobs = []
        reopen_advanced = bool(self.advanced_window and self.advanced_window.winfo_exists())
        if reopen_advanced:
            self.advanced_window.destroy()
        if self.import_wizard and self.import_wizard.winfo_exists():
            self.import_wizard.destroy()
        if self.tools_window and self.tools_window.winfo_exists():
            self.tools_window.destroy()
        self.advanced_window = None
        self.advanced_body = None
        self.advanced_sidebar = None
        self.advanced_search = None
        self.simple_tab = None
        self.advanced_tab = None
        self.advanced_tab_bars = []
        self.import_wizard = None
        self.tools_window = None
        self.tab_buttons = {}
        self.quick_buttons = {}
        self.logo_image = None
        self.root.configure(bg=APP_BG)
        for child in self.root.winfo_children():
            child.destroy()
        self._build()
        self._wire_drag_drop()
        if reopen_advanced and self.advanced_model and self.advanced_model.get("sections"):
            self.open_advanced_report()

    def update_quick_actions(self):
        prefix = self.tr("prefix_on") if self.prefix_profiles.get() else self.tr("prefix_off")
        compat = self.tr("compat_strict") if self.compatibility.get() == "strict" else self.tr("compat_loose")
        if "prefix" in self.quick_buttons:
            self.quick_buttons["prefix"].configure(
                text=prefix,
                bg=HEADER_BG if self.prefix_profiles.get() else PANEL_BG,
                fg=HEADER_FG if self.prefix_profiles.get() else INK,
            )
        if "compat" in self.quick_buttons:
            self.quick_buttons["compat"].configure(
                text=compat,
                bg=TEAL if self.compatibility.get() == "strict" else ORANGE,
                fg=PANEL_BG,
            )
        if "safe" in self.quick_buttons:
            self.quick_buttons["safe"].configure(text=self.tr("safe"), bg=PANEL_BG, fg=INK)
        if "theme" in self.quick_buttons:
            night = self.theme_mode.get() == "night"
            self.quick_buttons["theme"].configure(
                text=self.tr("day") if night else self.tr("night"),
                bg=HEADER_BG if night else PANEL_BG,
                fg=HEADER_FG if night else INK,
                activebackground=TEAL,
                activeforeground=PANEL_BG,
            )
        if "language" in self.quick_buttons:
            self.quick_buttons["language"].configure(text=self.language.get().upper(), bg=PANEL_BG, fg=INK)
        if "history" in self.quick_buttons:
            self.quick_buttons["history"].configure(text=self.tr("history").upper(), bg=PANEL_BG, fg=INK)
        if "tools" in self.quick_buttons:
            self.quick_buttons["tools"].configure(text=self.tr("tools").upper(), bg=PANEL_BG, fg=INK)

    def _wire_drag_drop(self):
        if not DND_FILES or not hasattr(self.drop_zone, "drop_target_register"):
            return
        try:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)
        except tk.TclError:
            # Drag-and-drop is an enhancement; the file/folder pickers remain available.
            return

    def _on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        if paths:
            self.set_input(paths[0])

    def choose_input(self):
        path = filedialog.askopenfilename(
            title="Choose PrusaSlicer config bundle",
            filetypes=[("PrusaSlicer config", "*.ini"), ("All files", "*.*")],
        )
        if path:
            self.set_input(path)

    def choose_folder(self):
        path = filedialog.askdirectory(title="Choose folder containing PrusaSlicer .ini files")
        if path:
            self.set_input(path)

    def set_input(self, path):
        source = Path(path)
        self.source_mode.set("folder" if source.is_dir() else "file")
        self.input_path.set(str(source))
        self.preview()

    def clear_input(self):
        self.input_path.set("")
        self.source_mode.set("file")
        self.last_preview = None
        self.advanced_model = None
        self.risk_label.set(self.tr("risk_waiting"))
        self.set_report_views(
            {
                "Simple summary": self.tr("simple_summary_empty") + "\n",
                "Summary": self.tr("summary_empty") + "\n",
                "Bundle files": self.tr("bundle_files_empty") + "\n",
                "Advanced report": self.tr("advanced_report_empty") + "\n",
            },
            [],
        )

    def choose_output(self):
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_path.set(path)
            self.refresh_preview_if_ready()

    def refresh_preview_if_ready(self):
        if self.input_path.get():
            self.preview()

    def preview(self):
        if not self.input_path.get():
            messagebox.showinfo("PrusaToOrca", self.tr("choose_file_first"))
            return
        self.set_busy(True)
        self.set_progress(0, "Preview started")
        threading.Thread(target=self._preview_worker, daemon=True).start()

    def _preview_worker(self):
        try:
            previews = []
            used_outputs = set()
            files = self.source_files()
            total_files = len(files)
            for position, ini_path in enumerate(files, 1):
                self.root.after(0, lambda p=position, t=total_files: self.set_progress((p - 1) / max(t, 1), f"Preview {p}/{t}"))
                log = ConversionLog()
                preview = convert_ini_to_orca(
                    ini_path,
                    self.output_path.get(),
                    log=log,
                    dry_run=True,
                    compatibility=self.compatibility.get(),
                    prefix_profiles=self.prefix_profiles.get(),
                    custom_mappings=self.custom_mappings,
                )
                preview["source_path"] = ini_path
                preview["output_path"] = self.unique_output_path(preview["output_path"], used_outputs)
                previews.append((preview, log))
            if not previews:
                raise FileNotFoundError("No .ini files found in the selected folder.")
            views, rows, advanced_model = self.build_report_views(previews, done=False)
            self.last_preview = previews
            self.root.after(0, lambda: self.set_report_views(views, rows, advanced_model))
            self.root.after(0, lambda: self.set_progress(1, f"Preview ready: {len(previews)} bundle(s)"))
        except Exception as exc:
            error = str(exc)
            self.root.after(0, lambda: messagebox.showerror("Preview failed", error))
            self.root.after(0, lambda: self.set_progress(0, "Preview failed"))
        finally:
            self.root.after(0, lambda: self.set_busy(False))

    def convert(self):
        if not self.input_path.get():
            messagebox.showinfo("PrusaToOrca", self.tr("choose_file_first"))
            return
        self.set_busy(True)
        self.set_progress(0, "Generation started")
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _convert_worker(self):
        try:
            results = []
            used_outputs = set()
            files = self.source_files()
            total_files = len(files)
            for position, ini_path in enumerate(files, 1):
                self.root.after(0, lambda p=position, t=total_files: self.set_progress((p - 1) / max(t, 1), f"Generate {p}/{t}"))
                dry_log = ConversionLog()
                preview = convert_ini_to_orca(
                    ini_path,
                    self.output_path.get(),
                    log=dry_log,
                    dry_run=True,
                    compatibility=self.compatibility.get(),
                    prefix_profiles=self.prefix_profiles.get(),
                    custom_mappings=self.custom_mappings,
                )
                target = self.unique_output_path(preview["output_path"], used_outputs)
                log = ConversionLog()
                result = convert_ini_to_orca(
                    ini_path,
                    target,
                    log=log,
                    dry_run=False,
                    compatibility=self.compatibility.get(),
                    prefix_profiles=self.prefix_profiles.get(),
                    custom_mappings=self.custom_mappings,
                )
                preview["source_path"] = ini_path
                preview["output_path"] = result
                results.append((preview, log))
            if not results:
                raise FileNotFoundError("No .ini files found in the selected folder.")
            views, rows, advanced_model = self.build_report_views(results, done=True)
            self.last_preview = results
            self.last_output_folder = self.output_path.get()
            self.root.after(0, lambda: self.set_report_views(views, rows, advanced_model))
            self.root.after(0, lambda v=views, r=rows, m=advanced_model: self.record_history(results, m, v, r))
            self.root.after(0, lambda: self.set_progress(1, f"Generated {len(results)} bundle(s)"))
            self.root.after(0, lambda r=results: self.open_import_wizard(r))
        except Exception as exc:
            error = str(exc)
            self.root.after(0, lambda: messagebox.showerror("Conversion failed", error))
            self.root.after(0, lambda: self.set_progress(0, "Generation failed"))
        finally:
            self.root.after(0, lambda: self.set_busy(False))

    def source_files(self):
        source = Path(self.input_path.get())
        if source.is_dir():
            return sorted(path for path in source.rglob("*.ini") if path.is_file())
        return [source]

    def unique_output_path(self, output_path, used_outputs):
        output_path = Path(output_path)
        candidate = output_path
        index = 2
        while str(candidate).lower() in used_outputs:
            candidate = output_path.with_name(f"{output_path.stem} ({index}){output_path.suffix}")
            index += 1
        used_outputs.add(str(candidate).lower())
        return candidate

    def existing_orca_names(self):
        roots = []
        appdata = os.environ.get("APPDATA")
        if appdata:
            roots.extend(
                [
                    Path(appdata) / "OrcaSlicer" / "user",
                    Path(appdata) / "OrcaSlicer" / "system",
                ]
            )
        names = set()
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".json", ".ini"}:
                    names.add(path.stem.lower())
        return names

    def assess_risk(self, entries):
        existing = self.existing_orca_names()
        generated = []
        for preview, _log in entries:
            for data in preview.get("files", {}).values():
                name = data.get("name") if isinstance(data, dict) else None
                if name:
                    generated.append(str(name))
        collisions = sorted({name for name in generated if name.lower() in existing})
        if collisions:
            return {
                "level": "HIGH",
                "message": f"Risk: HIGH - {len(collisions)} possible Orca name collision(s)",
                "collisions": collisions,
            }
        if not self.prefix_profiles.get():
            return {"level": "MEDIUM", "message": "Risk: MEDIUM - prefix disabled", "collisions": []}
        return {"level": "LOW", "message": "Risk: LOW - no Orca name collisions detected", "collisions": []}

    def set_progress(self, fraction, message=""):
        fraction = max(0, min(1, float(fraction)))
        if hasattr(self, "progress_canvas"):
            width = max(self.progress_canvas.winfo_width(), 1)
            self.progress_canvas.coords(self.progress_fill, 0, 0, int(width * fraction), 10)
        self.progress_label.set(message)

    def history_path(self):
        return app_file("conversion_history.json")

    def load_history(self):
        path = self.history_path()
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def save_history(self):
        path = self.history_path()
        path.write_text(json.dumps(self.history[-100:], indent=2, ensure_ascii=False), encoding="utf-8")

    def mapping_path(self):
        return app_file(CUSTOM_MAPPINGS_FILE)

    def load_custom_mappings(self):
        defaults = {"printer": {}, "filament": {}, "process": {}}
        path = self.mapping_path()
        if not path.exists():
            return defaults
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return defaults
        for key in defaults:
            if isinstance(loaded.get(key), dict):
                defaults[key].update(loaded[key])
        return defaults

    def save_custom_mappings(self):
        self.mapping_path().write_text(
            json.dumps(self.custom_mappings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def orca_key_catalog(self, section_type=None):
        keys = set()
        if self.advanced_model:
            for section in self.advanced_model.get("sections", []):
                if section_type and section["type"] != section_type:
                    continue
                keys.update(row[1] for row in section.get("mapped", []) if row[1] and row[1] != "-")
        fallback = {
            "printer": [
                "printer_notes", "printable_height", "nozzle_diameter", "machine_start_gcode",
                "machine_end_gcode", "retraction_length", "z_hop",
            ],
            "filament": [
                "filament_notes", "filament_type", "filament_vendor", "filament_density",
                "filament_cost", "filament_max_volumetric_speed", "filament_flow_ratio",
            ],
            "process": [
                "notes", "layer_height", "wall_loops", "sparse_infill_density",
                "sparse_infill_speed", "travel_speed", "seam_gap",
            ],
        }
        if section_type:
            keys.update(fallback.get(section_type, []))
        else:
            for values in fallback.values():
                keys.update(values)
        return sorted(keys)

    def record_history(self, results, model, views=None, rows=None):
        item = {
            "date": datetime.now().isoformat(timespec="seconds"),
            "source": self.input_path.get(),
            "output_folder": self.output_path.get(),
            "bundles": len(results),
            "risk": model.get("risk", {}).get("level", "UNKNOWN"),
            "converted": model["totals"]["converted"],
            "approx": model["totals"]["approx"],
            "ignored": model["totals"]["ignored"],
            "report_snapshot": {
                "views": views if views is not None else self.report_views,
                "rows": rows if rows is not None else self.report_rows,
                "advanced_model": model,
            },
        }
        self.history.append(item)
        self.save_history()

    def build_report_views(self, entries, done=False):
        total_printers = total_filaments = total_processes = 0
        rows = []
        summary = [
            "BUNDLE GENERATED" if done else "SAFE IMPORT PREVIEW",
            "",
            f"Source mode: {self.source_mode.get()}",
            f"Input: {self.input_path.get()}",
            f"{self.tr('output_folder')}: {self.output_path.get()}",
            f"Mode: compatibility={self.compatibility.get()} / prefix={'on' if self.prefix_profiles.get() else 'off'}",
            "",
            f"{'Generated' if done else 'Will generate'} {len(entries)} bundle(s):",
        ]
        bundle_lines = []
        advanced_lines = [
            self.tr("advanced_report").upper(),
            "",
        ]
        total_mapped = sum(log.total_mapped for _, log in entries)
        total_approx = sum(log.total_approx for _, log in entries)
        total_ignored = sum(log.total_skipped for _, log in entries)
        advanced_model = {
            "done": done,
            "source": self.input_path.get(),
            "output": self.output_path.get(),
            "mode": self.compatibility.get(),
            "prefix": self.prefix_profiles.get(),
            "outputs": [],
            "totals": {
                "converted": total_mapped,
                "approx": total_approx,
                "ignored": total_ignored,
            },
            "preset_totals": {"printer": 0, "filament": 0, "process": 0},
            "sections": [],
            "ignored": [],
            "warnings": [],
        }
        risk = self.assess_risk(entries)
        advanced_model["risk"] = risk
        self.root.after(0, lambda msg=risk["message"]: self.risk_label.set(msg))
        summary.extend(
            [
                "",
                "User summary:",
                f"  {self.tr('risk')}: {risk['level']}",
                f"  {self.tr('converted')}: {total_mapped}",
                f"  {self.tr('approx')}: {total_approx}",
                f"  {self.tr('ignored')}: {total_ignored}",
            ]
        )
        if risk["collisions"]:
            summary.append(f"  Possible name collisions: {len(risk['collisions'])}")
        advanced_lines.extend(
            [
                f"{STAR} {total_mapped} converted    {TRIANGLE} {total_approx} approximate    {CROSS} {total_ignored} ignored",
                "",
            ]
        )

        for index, (preview, log) in enumerate(entries, 1):
            files = preview["files"]
            printers = [n for n in files if n.startswith("printer/")]
            filaments = [n for n in files if n.startswith("filament/")]
            processes = [n for n in files if n.startswith("process/")]
            total_printers += len(printers)
            total_filaments += len(filaments)
            total_processes += len(processes)
            advanced_model["preset_totals"]["printer"] += len(printers)
            advanced_model["preset_totals"]["filament"] += len(filaments)
            advanced_model["preset_totals"]["process"] += len(processes)

            source = preview.get("source_path", "")
            source_name = Path(source).name if source else "bundle"
            advanced_model["outputs"].append(str(preview["output_path"]))
            summary.extend(
                [
                    f"  {index}. {source_name}",
                    f"     output: {preview['output_path']}",
                    f"     presets: {len(printers)} printer / {len(filaments)} filament / {len(processes)} process",
                ]
            )

            bundle_lines.extend(
                [
                    f"Bundle {index}: {source_name}",
                    f"Output: {preview['output_path']}",
                    f"Bundle id: {preview['bundle']['bundle_id']}",
                    "",
                ]
            )
            bundle_lines.extend(f"  {name}" for name in sorted(files))
            bundle_lines.append("")

            advanced_lines.extend(
                [
                    f"Bundle {index}: {source_name}",
                    f"{STAR} {log.total_mapped} converted | {TRIANGLE} {log.total_approx} approximate | {CROSS} {log.total_skipped} ignored",
                ]
            )
            if log.warnings:
                advanced_lines.append("Warnings:")
                advanced_lines.extend(f"  {warning}" for warning in log.warnings)
                advanced_model["warnings"].extend(
                    {"bundle": index, "source": str(source), "warning": warning}
                    for warning in log.warnings
                )
            for section in log.sections:
                coverage = 0
                total = section.n_mapped + section.n_skipped
                if total:
                    coverage = int(round(section.n_mapped / total * 100))
                section_model = {
                    "bundle": index,
                    "source": str(source),
                    "source_name": source_name,
                    "type": section.type,
                    "name": section.name,
                    "converted": section.n_mapped,
                    "approx": section.n_approx,
                    "ignored": section.n_skipped,
                    "coverage": coverage,
                    "mapped": list(section.mapped),
                    "skipped": list(section.skipped),
                }
                advanced_model["sections"].append(section_model)
                advanced_model["ignored"].extend(
                    {
                        "bundle": index,
                        "source": str(source),
                        "source_name": source_name,
                        "section_type": section.type,
                        "section_name": section.name,
                        "key": prusa_key,
                        "value": value,
                    }
                    for prusa_key, value in section.skipped
                )
                advanced_lines.append(
                    f"  [{section.type}] {section.name} "
                    f"{STAR} {section.n_mapped} {TRIANGLE} {section.n_approx} {CROSS} {section.n_skipped} | {coverage}% coverage"
                )
                for prusa_key, orca_key, value, note, approx in section.mapped[:8]:
                    marker = TRIANGLE if approx else STAR
                    suffix = f" ({note})" if note else ""
                    advanced_lines.append(f"      {marker} {prusa_key} -> {orca_key}: {value}{suffix}")
                if len(section.mapped) > 8:
                    advanced_lines.append(f"      ... {len(section.mapped) - 8} more converted fields")
                for prusa_key, value in section.skipped[:5]:
                    advanced_lines.append(f"      {CROSS} {prusa_key}: {value}")
                if len(section.skipped) > 5:
                    advanced_lines.append(f"      ... {len(section.skipped) - 5} more ignored fields")
                rows.append(
                    {
                        "bundle": index,
                        "source": str(source),
                        "section_type": section.type,
                        "section_name": section.name,
                        "status": "summary",
                        "prusa_key": "",
                        "orca_key": "",
                        "value": "",
                        "note": f"ok={section.n_mapped}; approx={section.n_approx}; ignored={section.n_skipped}",
                        "approx": "",
                    }
                )
                for prusa_key, orca_key, value, note, approx in section.mapped:
                    rows.append(
                        {
                            "bundle": index,
                            "source": str(source),
                            "section_type": section.type,
                            "section_name": section.name,
                            "status": "mapped",
                            "prusa_key": prusa_key,
                            "orca_key": orca_key,
                            "value": value,
                            "note": note,
                            "approx": str(bool(approx)),
                        }
                    )
                for prusa_key, value in section.skipped:
                    rows.append(
                        {
                            "bundle": index,
                            "source": str(source),
                            "section_type": section.type,
                            "section_name": section.name,
                            "status": "ignored",
                            "prusa_key": prusa_key,
                            "orca_key": "",
                            "value": value,
                            "note": "",
                            "approx": "False",
                        }
                    )
            advanced_lines.append("")

        summary.extend(
            [
                "",
                "Total presets:",
                f"  {total_printers} printer preset(s)",
                f"  {total_filaments} filament preset(s)",
                f"  {total_processes} process preset(s)",
                "",
                "Safety checks:",
                "  OK generated names are prefixed" if self.prefix_profiles.get() else "  WARNING prefix disabled",
                "  OK existing Orca preset files are not modified by this converter",
                "  OK preview does not write a bundle" if not done else "  OK only generated bundle files were written",
            ]
        )
        if done:
            summary.extend(["", "Next step in OrcaSlicer:", "  File > Import > Import Config Bundle"])
        simple_summary = self.build_simple_summary_text(advanced_model)

        return (
            {
                "Simple summary": simple_summary,
                "Summary": "\n".join(summary),
                "Bundle files": "\n".join(bundle_lines).strip() + "\n",
                "Advanced report": "\n".join(advanced_lines).strip() + "\n",
            },
            rows,
            advanced_model,
        )

    def build_simple_summary_text(self, model):
        totals = model.get("totals", {})
        presets = model.get("preset_totals", {})
        risk = model.get("risk", {})
        outputs = model.get("outputs", [])
        done = model.get("done", False)
        ignored = int(totals.get("ignored", 0) or 0)
        approx = int(totals.get("approx", 0) or 0)
        collisions = len(risk.get("collisions", []))

        if collisions:
            status = "PAUSE AND REVIEW"
            meaning = "Some generated names may collide with existing OrcaSlicer presets."
        elif ignored:
            status = "OK TO IMPORT, WITH REVIEW"
            meaning = "The bundle can be imported, but a few source settings were not converted."
        elif approx:
            status = "OK TO IMPORT, CHECK APPROXIMATIONS"
            meaning = "All important presets were generated, with a few approximate field translations."
        else:
            status = "OK TO IMPORT"
            meaning = "The generated bundle looks clean for a safe OrcaSlicer import."

        lines = [
            "SIMPLE IMPORT SUMMARY",
            "",
            status,
            meaning,
            "",
            f"Bundles: {len(outputs)}",
            f"Presets: {presets.get('printer', 0)} printer / {presets.get('filament', 0)} filament / {presets.get('process', 0)} process",
            f"Fields: {totals.get('converted', 0)} converted / {approx} approximate / {ignored} ignored",
            f"Risk: {risk.get('level', 'UNKNOWN')}",
            "",
            "What this means:",
        ]
        if collisions:
            lines.append("- Keep the prefix enabled or rename the generated presets before importing.")
        if approx:
            lines.append("- Approximate fields were converted to the closest OrcaSlicer setting.")
        if ignored:
            lines.append("- Ignored fields were not written to OrcaSlicer. Use Mapping if one matters.")
        if not any([collisions, approx, ignored]):
            lines.append("- No obvious manual cleanup is needed before import.")

        lines.extend(["", "Next step:"])
        if done:
            lines.append("- Open the import assistant and choose the generated .orca_printer file in OrcaSlicer.")
        else:
            lines.append("- Click Generate .orca_printer, then follow the import assistant.")
        if outputs:
            lines.extend(["", "Generated bundle path(s):"])
            lines.extend(f"- {path}" for path in outputs)
        return "\n".join(lines)

    def open_advanced_report(self):
        if not self.advanced_model or not self.advanced_model.get("sections"):
            messagebox.showinfo("PrusaToOrca", self.tr("advanced_report_open_first"))
            return
        if self.advanced_window and self.advanced_window.winfo_exists():
            self.advanced_window.lift()
            self.advanced_window.focus_force()
            return

        source = Path(self.advanced_model.get("source") or "bundle").name
        self.advanced_window = self.make_child_window(
            f"{self.tr('advanced_report_title')} - {source}",
            1160,
            740,
            920,
            600,
            bg=ADV_BG,
        )
        self.advanced_window_bars = []

        shell = tk.Frame(self.advanced_window, bg=ADV_BG, padx=14, pady=10)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = tk.Frame(shell, bg=ADV_BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(
            header,
            text=f"\u2315  {self.tr('advanced_report_title')}",
            font=ADV_TITLE_FONT,
            bg=ADV_BG,
            fg=ADV_TEXT,
        ).grid(row=0, column=0, sticky="w")

        stats = tk.Frame(header, bg=ADV_BG)
        stats.grid(row=0, column=2, sticky="e")
        totals = self.advanced_model["totals"]
        self._advanced_stat(stats, f"{CROSS} {totals['ignored']} {self.tr('ignored').lower()}", ADV_RED)
        self._advanced_stat(stats, f"{TRIANGLE} {totals['approx']} {self.tr('approx').lower()}", ORANGE)
        self._advanced_stat(stats, f"{STAR} {totals['converted']} {self.tr('converted').lower()}", ADV_GREEN)

        sidebar_shell = tk.Frame(shell, bg=ADV_PANEL, highlightbackground=ADV_LINE, highlightthickness=1)
        sidebar_shell.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        sidebar_shell.grid_rowconfigure(1, weight=1)
        tk.Label(
            sidebar_shell,
            text="Sections",
            font=ADV_FONT_BOLD,
            bg=ADV_PANEL,
            fg=ADV_MUTED,
            pady=8,
        ).grid(row=0, column=0, sticky="ew")

        side_canvas = tk.Canvas(sidebar_shell, bg=ADV_PANEL, highlightthickness=0, width=208)
        side_scroll = tk.Scrollbar(sidebar_shell, orient="vertical", command=side_canvas.yview)
        self.advanced_sidebar = tk.Frame(side_canvas, bg=ADV_PANEL)
        side_window = side_canvas.create_window((0, 0), window=self.advanced_sidebar, anchor="nw")
        side_canvas.configure(yscrollcommand=side_scroll.set)
        side_canvas.grid(row=1, column=0, sticky="nsew")
        side_scroll.grid(row=1, column=1, sticky="ns")
        self.advanced_sidebar.bind(
            "<Configure>",
            lambda _event: side_canvas.configure(scrollregion=side_canvas.bbox("all")),
        )
        side_canvas.bind("<Configure>", lambda event: side_canvas.itemconfigure(side_window, width=event.width))

        main = tk.Frame(shell, bg=ADV_BG)
        main.grid(row=1, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        search_row = tk.Frame(main, bg=ADV_BG)
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 9))
        search_row.grid_columnconfigure(1, weight=1)
        tk.Label(search_row, text="\U0001f50e", font=ADV_FONT, bg=ADV_BG, fg=ADV_MUTED).grid(row=0, column=0, padx=(0, 8))
        self.advanced_search = tk.StringVar()
        search = tk.Entry(
            search_row,
            textvariable=self.advanced_search,
            font=ADV_FONT,
            bg=ADV_PANEL_ALT,
            fg=ADV_TEXT,
            insertbackground=ADV_TEXT,
            relief="flat",
            highlightbackground=ADV_LINE,
            highlightthickness=1,
        )
        search.grid(row=0, column=1, sticky="ew")
        self.advanced_search.trace_add("write", lambda *_args: self._advanced_render_summary())
        filters = tk.Frame(search_row, bg=ADV_BG)
        filters.grid(row=0, column=2, sticky="e", padx=(10, 0))
        for label, value in [(self.tr("all"), "all"), (self.tr("converted"), "mapped"), (self.tr("approx"), "approx"), (self.tr("ignored"), "ignored")]:
            tk.Radiobutton(
                filters,
                text=label,
                value=value,
                variable=self.advanced_filter,
                indicatoron=False,
                command=self._advanced_render_summary,
                font=ADV_FONT_BOLD,
                bg=ADV_PANEL_ALT,
                fg=ADV_TEXT,
                selectcolor=TEAL,
                activebackground=TEAL,
                activeforeground=PANEL_BG,
                padx=7,
                pady=3,
                relief="flat",
                borderwidth=0,
            ).pack(side="left", padx=(0, 4))

        content = tk.Frame(main, bg=ADV_PANEL, highlightbackground=ADV_LINE, highlightthickness=1)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        canvas = tk.Canvas(content, bg=ADV_PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        self.advanced_body = tk.Frame(canvas, bg=ADV_PANEL, padx=12, pady=11)
        body_window = canvas.create_window((0, 0), window=self.advanced_body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.advanced_body.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(body_window, width=event.width))

        footer = tk.Frame(shell, bg=ADV_BG)
        footer.grid(row=2, column=1, sticky="e", pady=(12, 0))
        tk.Button(
            footer,
            text=self.tr("cancel"),
            command=self.advanced_window.destroy,
            font=ADV_FONT,
            bg=ADV_BG,
            fg=ADV_MUTED,
            activebackground=ADV_PANEL_ALT,
            activeforeground=ADV_TEXT,
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            footer,
            text=self.tr("csv"),
            command=self.export_csv,
            font=ADV_FONT_BOLD,
            bg=ORANGE,
            fg=PANEL_BG,
            activebackground=RED_ORANGE,
            activeforeground=PANEL_BG,
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=7,
            cursor="hand2",
        ).pack(side="left")
        tk.Button(
            footer,
            text="Mapping",
            command=self.open_mapping_editor,
            font=ADV_FONT_BOLD,
            bg=PANEL_BG,
            fg=INK,
            activebackground=TEAL,
            activeforeground=PANEL_BG,
            relief="flat",
            borderwidth=0,
            highlightbackground=LINE,
            highlightthickness=1,
            padx=12,
            pady=7,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            footer,
            text="HTML",
            command=self.export_html,
            font=ADV_FONT_BOLD,
            bg=PANEL_BG,
            fg=INK,
            activebackground=TEAL,
            activeforeground=PANEL_BG,
            relief="flat",
            borderwidth=0,
            highlightbackground=LINE,
            highlightthickness=1,
            padx=12,
            pady=7,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            footer,
            text="PDF",
            command=self.export_pdf,
            font=ADV_FONT_BOLD,
            bg=PANEL_BG,
            fg=INK,
            activebackground=TEAL,
            activeforeground=PANEL_BG,
            relief="flat",
            borderwidth=0,
            highlightbackground=LINE,
            highlightthickness=1,
            padx=12,
            pady=7,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))

        self._advanced_render_sidebar()
        self._advanced_render_summary()

    def _advanced_stat(self, parent, text, color):
        tk.Label(
            parent,
            text=text,
            font=ADV_FONT_BOLD,
            bg=ADV_PANEL_ALT,
            fg=color,
            padx=9,
            pady=4,
        ).pack(side="left", padx=(8, 0))

    def _advanced_icon(self, section_type):
        return {
            "printer": "\u25a3",
            "filament": "\u25d2",
            "process": "\u2699",
        }.get(section_type, "\u25a1")

    def _advanced_clear(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def _advanced_render_sidebar(self):
        if not self.advanced_sidebar:
            return
        self._advanced_clear(self.advanced_sidebar)
        self._advanced_side_button("R\u00e9sum\u00e9 global", self._advanced_render_summary, active=True)
        for section in self.advanced_model.get("sections", []):
            label = f"{self._advanced_icon(section['type'])} {section['name']}"
            self._advanced_side_button(label, lambda s=section: self._advanced_render_detail(s))
        ignored_count = len(self.advanced_model.get("ignored", []))
        self._advanced_side_button(f"{TRIANGLE} Ignor\u00e9s ({ignored_count})", self._advanced_render_ignored)

    def _advanced_side_button(self, text, command, active=False):
        btn = tk.Button(
            self.advanced_sidebar,
            text=text,
            command=command,
            font=ADV_FONT_BOLD if active else ADV_FONT,
            bg=ADV_PANEL_ALT if active else ADV_PANEL,
            fg=ADV_TEXT,
            activebackground=ADV_PANEL_ALT,
            activeforeground=ADV_TEXT,
            relief="flat",
            borderwidth=0,
            anchor="w",
            padx=11,
            pady=7,
            wraplength=174,
            cursor="hand2",
        )
        btn.pack(fill="x")

    def _advanced_query(self):
        if not self.advanced_search:
            return ""
        return self.advanced_search.get().strip().lower()

    def _advanced_filter_sections(self):
        query = self._advanced_query()
        mode = self.advanced_filter.get()
        sections = self.advanced_model.get("sections", [])
        if mode == "approx":
            sections = [section for section in sections if section["approx"]]
        elif mode == "ignored":
            sections = [section for section in sections if section["ignored"]]
        elif mode == "mapped":
            sections = [section for section in sections if section["converted"]]
        if not query:
            return sections
        filtered = []
        for section in sections:
            haystack = " ".join(
                [
                    section["type"],
                    section["name"],
                    section["source_name"],
                    " ".join(str(item) for item in section["mapped"][:20]),
                    " ".join(str(item) for item in section["skipped"][:20]),
                ]
            ).lower()
            if query in haystack:
                filtered.append(section)
        return filtered

    def _advanced_render_summary(self):
        if not self.advanced_body:
            return
        self._advanced_clear(self.advanced_body)
        self.advanced_window_bars = []
        sections = self._advanced_filter_sections()
        title = "R\u00e9sum\u00e9 par section"
        if self._advanced_query():
            title += f" - {len(sections)} r\u00e9sultat(s)"
        tk.Label(
            self.advanced_body,
            text=title,
            font=ADV_SECTION_FONT,
            bg=ADV_PANEL,
            fg=ADV_TEXT,
        ).pack(anchor="w", pady=(0, 14))

        if not sections:
            tk.Label(
                self.advanced_body,
                text="Aucune section ne correspond \u00e0 la recherche.",
                font=ADV_FONT,
                bg=ADV_PANEL,
                fg=ADV_MUTED,
            ).pack(anchor="w")
            return

        for section in sections:
            self._advanced_section_card(section)
        self.root.after(80, self.animate_advanced_window_bars)

    def _advanced_section_card(self, section):
        card = tk.Frame(self.advanced_body, bg=ADV_PANEL_ALT, highlightbackground=ADV_LINE, highlightthickness=1, padx=13, pady=9)
        card.pack(fill="x", pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)

        top = tk.Frame(card, bg=ADV_PANEL_ALT)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        title = f"{self._advanced_icon(section['type'])}  {section['name']}"
        tk.Label(top, text=title, font=ADV_FONT_BOLD, bg=ADV_PANEL_ALT, fg=ADV_TEXT).grid(row=0, column=0, sticky="w")
        stats = tk.Frame(top, bg=ADV_PANEL_ALT)
        stats.grid(row=0, column=1, sticky="e")
        for text, color in [
            (f"{STAR} {section['converted']}", ADV_GREEN),
            (f"{TRIANGLE} {section['approx']}", ORANGE),
            (f"{CROSS} {section['ignored']}", ADV_RED),
            (f"{section['coverage']}% couverture", ADV_BLUE),
        ]:
            tk.Label(stats, text=text, font=ADV_FONT_BOLD, bg=ADV_PANEL_ALT, fg=color, padx=6).pack(side="left")

        bar = tk.Canvas(card, bg=ADV_PROGRESS_BG, height=7, highlightthickness=0)
        bar.grid(row=1, column=0, sticky="ew", pady=(9, 0))
        warn = bar.create_rectangle(0, 0, 0, 7, fill=ORANGE, outline="")
        fill = bar.create_rectangle(0, 0, 0, 7, fill=TEAL, outline="")
        self.advanced_window_bars.append((bar, fill, warn, section["coverage"] / 100))

        for widget in (card, top, bar):
            widget.bind("<Button-1>", lambda _event, s=section: self._advanced_render_detail(s))
            widget.configure(cursor="hand2")

        def hover(_event, active):
            card.configure(bg=PANEL_TINT if active else ADV_PANEL_ALT)
            top.configure(bg=PANEL_TINT if active else ADV_PANEL_ALT)

        card.bind("<Enter>", lambda event: hover(event, True))
        card.bind("<Leave>", lambda event: hover(event, False))

    def animate_advanced_window_bars(self, step=0):
        steps = 18
        for bar, fill, warn, target in self.advanced_window_bars:
            width = max(bar.winfo_width(), 1)
            bar.coords(warn, 0, 0, width, 7)
            bar.coords(fill, 0, 0, int(width * target * step / steps), 7)
        if step < steps and self.advanced_window and self.advanced_window.winfo_exists():
            self.root.after(16, lambda: self.animate_advanced_window_bars(step + 1))

    def _advanced_render_detail(self, section):
        if not self.advanced_body:
            return
        self._advanced_clear(self.advanced_body)
        self._advanced_table_header(["Cl\u00e9 PrusaSlicer", "Cl\u00e9 OrcaSlicer", "Valeur", "Statut"])
        mode = self.advanced_filter.get()
        for prusa_key, orca_key, value, note, approx in section["mapped"]:
            if mode == "ignored" or (mode == "approx" and not approx):
                continue
            if approx:
                status = f"{TRIANGLE} approx"
                if note:
                    status += f" {note}"
            else:
                status = f"{CHECK} exact"
                if note:
                    status += f" {note}"
            self._advanced_table_row([prusa_key, orca_key, value, status], approx=approx, status_index=3)
        for prusa_key, value in section["skipped"]:
            if mode in {"mapped", "approx"}:
                continue
            self._advanced_table_row([prusa_key, "-", value, f"{CROSS} ignor\u00e9"], ignored=True, status_index=3)

    def _advanced_render_ignored(self):
        if not self.advanced_body:
            return
        self._advanced_clear(self.advanced_body)
        ignored = self.advanced_model.get("ignored", [])
        query = self._advanced_query()
        if query:
            ignored = [
                row
                for row in ignored
                if query
                in " ".join(
                    [
                        row["source_name"],
                        row["section_type"],
                        row["section_name"],
                        row["key"],
                        row["value"],
                    ]
                ).lower()
            ]
        tk.Label(
            self.advanced_body,
            text=f"Ignor\u00e9s ({len(ignored)})",
            font=ADV_SECTION_FONT,
            bg=ADV_PANEL,
            fg=ADV_TEXT,
        ).pack(anchor="w", pady=(0, 14))
        if not ignored:
            tk.Label(
                self.advanced_body,
                text="Aucun champ ignor\u00e9 pour ce filtre.",
                font=ADV_FONT,
                bg=ADV_PANEL,
                fg=ADV_MUTED,
            ).pack(anchor="w")
            return
        self._advanced_table_header(["Bundle", "Section", "Cl\u00e9 PrusaSlicer", "Valeur"])
        for row in ignored:
            self._advanced_table_row(
                [
                    row["source_name"],
                    f"{row['section_type']} / {row['section_name']}",
                    row["key"],
                    row["value"],
                ],
                ignored=True,
            )

    def _advanced_table_header(self, columns):
        row = tk.Frame(self.advanced_body, bg=ADV_PANEL_ALT)
        row.pack(fill="x", pady=(0, 2))
        weights = [3, 3, 2, 2]
        for index, text in enumerate(columns):
            row.grid_columnconfigure(index, weight=weights[index] if index < len(weights) else 1, uniform="advanced_table")
            tk.Label(
                row,
                text=text,
                font=ADV_FONT_BOLD,
                bg=ADV_PANEL_ALT,
                fg=ADV_MUTED,
                anchor="w",
                padx=8,
                pady=5,
            ).grid(row=0, column=index, sticky="ew")

    def _advanced_table_row(self, columns, approx=False, ignored=False, status_index=None):
        row_bg = PANEL_TINT if ignored else PANEL_BG
        status_color = ADV_RED if ignored else ORANGE if approx else ADV_GREEN
        row = tk.Frame(self.advanced_body, bg=row_bg)
        row.pack(fill="x")
        weights = [3, 3, 2, 2]
        if status_index is None:
            status_index = len(columns) - 1
        for index, text in enumerate(columns):
            row.grid_columnconfigure(index, weight=weights[index] if index < len(weights) else 1, uniform="advanced_table")
            tk.Label(
                row,
                text=str(text),
                font=ADV_TABLE_FONT,
                bg=row_bg,
                fg=status_color,
                anchor="w",
                padx=8,
                pady=5,
                wraplength=520 if index == status_index else 340,
                justify="left",
            ).grid(row=0, column=index, sticky="ew")

    def build_info_text(self):
        sections = [
            ("info_flow_title", "info_flow_body"),
            ("info_safe_title", "info_safe_body"),
            ("info_prefix_title", "info_prefix_body"),
            ("info_compat_title", "info_compat_body"),
            ("info_reports_title", "info_reports_body"),
            ("info_mapping_title", "info_mapping_body"),
        ]
        lines = [
            self.tr("info_title").upper(),
            "",
            self.tr("info_intro"),
            "",
        ]
        for index, (title_key, body_key) in enumerate(sections, 1):
            lines.extend(
                [
                    f"{index:02d} // {self.tr(title_key)}",
                    self.tr(body_key),
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def set_report_views(self, views, rows, advanced_model=None):
        views = dict(views)
        views["Info"] = self.build_info_text()
        self.report_views = views
        self.report_rows = rows
        self.advanced_model = advanced_model
        self.show_report_tab(self.current_report_tab if self.current_report_tab in views else "Summary")
        if self.advanced_window and self.advanced_window.winfo_exists():
            self._advanced_render_sidebar()
            self._advanced_render_summary()

    def show_report_tab(self, name):
        self.current_report_tab = name
        for tab_name, btn in self.tab_buttons.items():
            active = tab_name == name
            btn.configure(
                bg=TEAL_DARK if active else PANEL_BG,
                fg=PANEL_BG if active else MUTED,
                font=UI_FONT_BOLD if active else UI_FONT,
            )
        if name == "Simple summary":
            self.report.grid_remove()
            self.advanced_tab.grid_remove()
            self.simple_tab.grid()
            self.render_simple_summary_tab()
        elif name == "Advanced report":
            self.report.grid_remove()
            self.simple_tab.grid_remove()
            self.advanced_tab.grid()
            self.render_advanced_tab()
        else:
            self.simple_tab.grid_remove()
            self.advanced_tab.grid_remove()
            self.report.grid()
            self.write_report(self.report_views.get(name, "No report yet.\n"))

    def clear_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def render_simple_summary_tab(self):
        self.clear_frame(self.simple_tab)
        if not self.advanced_model:
            tk.Label(
                self.simple_tab,
                text=self.tr("simple_empty"),
                font=SECTION_FONT,
                bg=PANEL_BG,
                fg=INK,
                wraplength=720,
                justify="left",
            ).pack(anchor="w")
            return

        model = self.advanced_model
        totals = model.get("totals", {})
        presets = model.get("preset_totals", {})
        risk = model.get("risk", {})
        ignored = int(totals.get("ignored", 0) or 0)
        approx = int(totals.get("approx", 0) or 0)
        collisions = len(risk.get("collisions", []))
        if collisions:
            status, status_color = "PAUSE AND REVIEW", RED_ORANGE
            message = "Possible OrcaSlicer name collisions were detected."
        elif ignored:
            status, status_color = "OK TO IMPORT, WITH REVIEW", ORANGE
            message = "Some settings were ignored. The bundle is safe, but check what matters."
        elif approx:
            status, status_color = "OK TO IMPORT, CHECK APPROXIMATIONS", ORANGE
            message = "Some fields were translated to the closest OrcaSlicer equivalent."
        else:
            status, status_color = "OK TO IMPORT", TEAL_DARK
            message = "No obvious manual cleanup is needed before import."

        header = tk.Frame(self.simple_tab, bg=PANEL_BG)
        header.pack(fill="x", pady=(0, 14))
        tk.Label(header, text=status, font=SECTION_FONT, bg=PANEL_BG, fg=status_color).pack(anchor="w")
        tk.Label(header, text=message, font=UI_FONT, bg=PANEL_BG, fg=INK, wraplength=760, justify="left").pack(anchor="w", pady=(4, 0))

        cards = tk.Frame(self.simple_tab, bg=PANEL_BG)
        cards.pack(fill="x", pady=(0, 14))
        self.simple_card(cards, "Bundles", len(model.get("outputs", [])), "orca_printer files", TEAL_DARK)
        self.simple_card(cards, "Presets", sum(int(v or 0) for v in presets.values()), "printer / filament / process", TEAL_DARK)
        self.simple_card(cards, self.tr("approx"), approx, "worth checking", ORANGE if approx else TEAL_DARK)
        self.simple_card(cards, self.tr("ignored"), ignored, "not written", RED_ORANGE if ignored else TEAL_DARK)

        columns = tk.Frame(self.simple_tab, bg=PANEL_BG)
        columns.pack(fill="both", expand=True)
        columns.grid_columnconfigure(0, weight=1)
        columns.grid_columnconfigure(1, weight=1)

        meaning = tk.Frame(columns, bg=PANEL_TINT, highlightbackground=LINE, highlightthickness=1, padx=14, pady=12)
        meaning.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(meaning, text=self.tr("what_this_means"), font=UI_FONT_BOLD, bg=PANEL_TINT, fg=INK).pack(anchor="w")
        notes = []
        if collisions:
            notes.append("Keep the prefix enabled or rename generated presets before importing.")
        if approx:
            notes.append("Approximate fields use the closest OrcaSlicer setting.")
        if ignored:
            notes.append("Ignored fields were not imported. Use Mapping if a field matters.")
        if not notes:
            notes.append("The generated bundle is ready for the normal OrcaSlicer import flow.")
        for note in notes:
            tk.Label(meaning, text=f"- {note}", font=UI_FONT, bg=PANEL_TINT, fg=INK, wraplength=300, justify="left").pack(anchor="w", pady=(8, 0))

        next_box = tk.Frame(columns, bg=PANEL_TINT, highlightbackground=LINE, highlightthickness=1, padx=14, pady=12)
        next_box.grid(row=0, column=1, sticky="nsew")
        tk.Label(next_box, text=self.tr("next_step"), font=UI_FONT_BOLD, bg=PANEL_TINT, fg=INK).pack(anchor="w")
        if model.get("done"):
            next_text = "Open OrcaSlicer, import the generated Config Bundle, then select the imported printer."
        else:
            next_text = "Generate the .orca_printer bundle first. The import assistant opens after generation."
        tk.Label(next_box, text=next_text, font=UI_FONT, bg=PANEL_TINT, fg=INK, wraplength=300, justify="left").pack(anchor="w", pady=(8, 12))
        self._button(next_box, self.tr("import_assistant"), self.open_import_wizard, variant="primary").pack(anchor="w")
        self._button(next_box, self.tr("mapping_editor"), self.open_mapping_editor, variant="secondary").pack(anchor="w", pady=(8, 0))

        outputs = model.get("outputs", [])
        if outputs:
            paths = tk.Frame(self.simple_tab, bg=PANEL_BG)
            paths.pack(fill="x", pady=(14, 0))
            tk.Label(paths, text=self.tr("generated_bundle_paths"), font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK).pack(anchor="w")
            for path in outputs[:3]:
                tk.Label(paths, text=path, font=UI_FONT, bg=PANEL_BG, fg=MUTED, wraplength=820, justify="left").pack(anchor="w", pady=(4, 0))

    def simple_card(self, parent, label, value, detail, color):
        card = tk.Frame(parent, bg=PANEL_TINT, highlightbackground=LINE, highlightthickness=1, padx=12, pady=10)
        card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(card, text=label, font=UI_FONT_BOLD, bg=PANEL_TINT, fg=MUTED).pack(anchor="w")
        tk.Label(card, text=str(value), font=("Arial Black", 18), bg=PANEL_TINT, fg=color).pack(anchor="w")
        tk.Label(card, text=detail, font=UI_FONT, bg=PANEL_TINT, fg=INK, wraplength=160, justify="left").pack(anchor="w")

    def render_advanced_tab(self):
        self.clear_frame(self.advanced_tab)
        self.advanced_tab_bars = []
        if not self.advanced_model:
            tk.Label(
                self.advanced_tab,
                text=self.tr("advanced_report_empty"),
                font=SECTION_FONT,
                bg=PANEL_BG,
                fg=INK,
            ).pack(anchor="w")
            return

        model = self.advanced_model
        risk = model.get("risk", {})
        header = tk.Frame(self.advanced_tab, bg=PANEL_BG)
        header.pack(fill="x", pady=(0, 14))
        tk.Label(header, text=self.tr("advanced_report"), font=SECTION_FONT, bg=PANEL_BG, fg=INK).pack(side="left")
        tk.Button(
            header,
            text=self.tr("mapping_editor"),
            command=self.open_mapping_editor,
            font=UI_FONT_BOLD,
            bg=PANEL_BG,
            fg=INK,
            activebackground=TEAL,
            activeforeground=PANEL_BG,
            relief="flat",
            borderwidth=0,
            highlightbackground=LINE,
            highlightthickness=1,
            padx=12,
            pady=7,
            cursor="hand2",
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            header,
            text=self.tr("open_detailed_view"),
            command=self.open_advanced_report,
            font=UI_FONT_BOLD,
            bg=HEADER_BG,
            fg=HEADER_FG,
            activebackground=TEAL,
            activeforeground=HEADER_FG,
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=7,
            cursor="hand2",
        ).pack(side="right")

        cards = tk.Frame(self.advanced_tab, bg=PANEL_BG)
        cards.pack(fill="x", pady=(0, 14))
        self.animated_card(cards, self.tr("risk"), risk.get("level", "N/A"), risk.get("message", ""), TEAL_DARK if risk.get("level") == "LOW" else ORANGE if risk.get("level") == "MEDIUM" else RED_ORANGE)
        self.animated_card(cards, self.tr("converted"), model["totals"]["converted"], self.tr("converted_detail"), TEAL_DARK)
        self.animated_card(cards, self.tr("approx"), model["totals"]["approx"], self.tr("approx_detail"), ORANGE)
        self.animated_card(cards, self.tr("ignored"), model["totals"]["ignored"], self.tr("ignored_detail"), RED_ORANGE)

        filters = tk.Frame(self.advanced_tab, bg=PANEL_BG)
        filters.pack(fill="x", pady=(0, 12))
        for label, value in [(self.tr("all"), "all"), (self.tr("converted"), "mapped"), (self.tr("approx"), "approx"), (self.tr("ignored"), "ignored")]:
            tk.Radiobutton(
                filters,
                text=label,
                value=value,
                variable=self.advanced_filter,
                indicatoron=False,
                command=self.render_advanced_tab,
                font=UI_FONT_BOLD,
                bg=PANEL_TINT,
                fg=INK,
                selectcolor=TEAL,
                activebackground=TEAL,
                activeforeground=PANEL_BG,
                padx=10,
                pady=6,
                relief="flat",
                borderwidth=0,
            ).pack(side="left", padx=(0, 8))

        body = tk.Frame(self.advanced_tab, bg=PANEL_BG)
        body.pack(fill="both", expand=True)
        sections = self._advanced_filter_sections()
        if not sections:
            tk.Label(body, text=self.tr("advanced_no_section"), font=UI_FONT, bg=PANEL_BG, fg=MUTED).pack(anchor="w")
            return

        for section in sections[:9]:
            self.advanced_dashboard_row(body, section)
        self.root.after(80, self.animate_advanced_tab_bars)

    def animated_card(self, parent, label, value, detail, color):
        card = tk.Frame(parent, bg=PANEL_TINT, highlightbackground=LINE, highlightthickness=1, padx=12, pady=10)
        card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(card, text=label, font=UI_FONT_BOLD, bg=PANEL_TINT, fg=MUTED).pack(anchor="w")
        value_label = tk.Label(card, text="0" if isinstance(value, int) else str(value), font=("Arial Black", 18), bg=PANEL_TINT, fg=color)
        value_label.pack(anchor="w")
        tk.Label(card, text=detail, font=UI_FONT, bg=PANEL_TINT, fg=INK, wraplength=160, justify="left").pack(anchor="w")
        if isinstance(value, int):
            self.animate_counter(value_label, value, color)

    def animate_counter(self, label, target, color, step=0):
        steps = 16
        value = int(round(target * step / steps))
        label.configure(text=str(value), fg=color)
        if step < steps:
            job = self.root.after(18, lambda: self.animate_counter(label, target, color, step + 1))
            self.advanced_tab_counter_jobs.append(job)

    def advanced_dashboard_row(self, parent, section):
        row = tk.Frame(parent, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1, padx=12, pady=9)
        row.pack(fill="x", pady=(0, 8))
        top = tk.Frame(row, bg=PANEL_BG)
        top.pack(fill="x")
        tk.Label(top, text=f"{self._advanced_icon(section['type'])} {section['name']}", font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK).pack(side="left")
        stat = f"{STAR} {section['converted']}   {TRIANGLE} {section['approx']}   {CROSS} {section['ignored']}   {section['coverage']}%"
        tk.Label(top, text=stat, font=UI_FONT_BOLD, bg=PANEL_BG, fg=TEAL_DARK).pack(side="right")
        bar = tk.Canvas(row, height=8, bg=ADV_PROGRESS_BG, highlightthickness=0)
        bar.pack(fill="x", pady=(8, 0))
        fill = bar.create_rectangle(0, 0, 0, 8, fill=TEAL, outline="")
        self.advanced_tab_bars.append((bar, fill, section["coverage"] / 100))
        row.bind("<Button-1>", lambda _event, s=section: self.open_advanced_detail_from_tab(s))
        row.configure(cursor="hand2")

    def open_advanced_detail_from_tab(self, section):
        self.open_advanced_report()
        if self.advanced_window and self.advanced_window.winfo_exists():
            self._advanced_render_detail(section)

    def animate_advanced_tab_bars(self, step=0):
        steps = 18
        for bar, fill, target in self.advanced_tab_bars:
            width = max(bar.winfo_width(), 1)
            bar.coords(fill, 0, 0, int(width * target * step / steps), 8)
        if step < steps:
            self.root.after(16, lambda: self.animate_advanced_tab_bars(step + 1))

    def export_csv(self):
        if not self.report_rows:
            messagebox.showinfo("PrusaToOrca", self.tr("export_before_csv"))
            return
        path = filedialog.asksaveasfilename(
            title="Export conversion report",
            defaultextension=".csv",
            filetypes=[("CSV report", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        fields = [
            "bundle",
            "source",
            "section_type",
            "section_name",
            "status",
            "prusa_key",
            "orca_key",
            "value",
            "note",
            "approx",
        ]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.report_rows)
        messagebox.showinfo("PrusaToOrca", self.tr("export_csv_done", path=path))

    def export_html(self):
        if not self.advanced_model:
            messagebox.showinfo("PrusaToOrca", self.tr("export_before_html"))
            return
        path = filedialog.asksaveasfilename(
            title="Export HTML report",
            defaultextension=".html",
            filetypes=[("HTML report", "*.html"), ("All files", "*.*")],
        )
        if not path:
            return
        Path(path).write_text(self.render_html_report(), encoding="utf-8")
        messagebox.showinfo("PrusaToOrca", self.tr("export_html_done", path=path))

    def export_pdf(self):
        if not self.advanced_model:
            messagebox.showinfo("PrusaToOrca", self.tr("export_before_pdf"))
            return
        path = filedialog.asksaveasfilename(
            title="Export PDF report",
            defaultextension=".pdf",
            filetypes=[("PDF report", "*.pdf"), ("All files", "*.*")],
        )
        if not path:
            return
        self.write_simple_pdf(path, self.report_views.get("Advanced report", "No report."))
        messagebox.showinfo("PrusaToOrca", self.tr("export_pdf_done", path=path))

    def render_html_report(self):
        model = self.advanced_model
        risk = model.get("risk", {})
        rows = []
        for row in self.report_rows:
            if row["status"] == "summary":
                continue
            rows.append(
                "<tr>"
                f"<td>{html.escape(row['section_type'])}</td>"
                f"<td>{html.escape(row['section_name'])}</td>"
                f"<td>{html.escape(row['status'])}</td>"
                f"<td>{html.escape(row['prusa_key'])}</td>"
                f"<td>{html.escape(row['orca_key'])}</td>"
                f"<td>{html.escape(row['value'])}</td>"
                f"<td>{html.escape(row['note'])}</td>"
                "</tr>"
            )
        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>PrusaToOrca report</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f3f0e9;color:#2b2825;margin:28px}}
h1{{font-size:26px}} .bar{{height:6px;background:#009aa6;margin:18px 0}}
.stats span{{display:inline-block;border:1px solid #2b2825;padding:8px 10px;margin-right:8px;background:#ece6da}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border:1px solid #2b2825;padding:6px;text-align:left}} th{{background:#ece6da}}
</style></head><body>
<h1>PrusaToOrca conversion report</h1><div class="bar"></div>
<p><b>Source:</b> {html.escape(model.get('source',''))}</p>
<p><b>Output:</b> {html.escape(model.get('output',''))}</p>
<p><b>Risk:</b> {html.escape(risk.get('level','UNKNOWN'))} - {html.escape(risk.get('message',''))}</p>
<div class="stats"><span>{STAR} {model['totals']['converted']} converted</span><span>{TRIANGLE} {model['totals']['approx']} approx</span><span>{CROSS} {model['totals']['ignored']} ignored</span></div>
<h2>Details</h2><table><thead><tr><th>Type</th><th>Section</th><th>Status</th><th>Prusa key</th><th>Orca key</th><th>Value</th><th>Note</th></tr></thead><tbody>
{''.join(rows)}
</tbody></table></body></html>"""

    def write_simple_pdf(self, path, text):
        lines = ["PrusaToOrca report", f"Version {APP_VERSION}", ""] + text.splitlines()
        lines = [line[:100] for line in lines[:55]]
        stream_lines = ["BT", "/F1 10 Tf", "50 790 Td"]
        for index, line in enumerate(lines):
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if index:
                stream_lines.append("0 -13 Td")
            stream_lines.append(f"({safe}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1", errors="replace")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        pdf = bytearray(b"%PDF-1.4\n")
        offsets = []
        for number, obj in enumerate(objects, 1):
            offsets.append(len(pdf))
            pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
        xref = len(pdf)
        pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
        for offset in offsets:
            pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
        Path(path).write_bytes(pdf)

    def open_output_folder(self):
        target = Path(self.last_output_folder or self.output_path.get())
        target.mkdir(parents=True, exist_ok=True)
        os.startfile(str(target))

    def generated_output_paths(self, results=None):
        if results:
            return [str(preview["output_path"]) for preview, _log in results]
        if self.advanced_model:
            return [str(path) for path in self.advanced_model.get("outputs", [])]
        if self.last_preview:
            return [str(preview["output_path"]) for preview, _log in self.last_preview]
        return []

    def open_import_wizard(self, results=None):
        if results is None and self.advanced_model and not self.advanced_model.get("done"):
            messagebox.showinfo(self.tr("import_assistant"), self.tr("import_assistant_need_generate"))
            return
        outputs = self.generated_output_paths(results)
        if not outputs:
            messagebox.showinfo(self.tr("import_assistant"), self.tr("import_assistant_need_generate"))
            return
        if self.import_wizard and self.import_wizard.winfo_exists():
            self.import_wizard.destroy()

        self.import_wizard = self.make_child_window(self.tr("import_assistant"), 780, 540, 680, 460)

        shell = tk.Frame(self.import_wizard, bg=APP_BG, padx=18, pady=16)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)

        tk.Label(shell, text=self.tr("import_into_orca"), font=SECTION_FONT, bg=APP_BG, fg=INK).grid(row=0, column=0, sticky="w")
        tk.Label(
            shell,
            text=self.tr("import_assistant_intro"),
            font=UI_FONT,
            bg=APP_BG,
            fg=MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        steps = tk.Frame(shell, bg=PANEL_TINT, highlightbackground=LINE, highlightthickness=1, padx=14, pady=12)
        steps.grid(row=2, column=0, sticky="nsew")
        steps.grid_columnconfigure(1, weight=1)
        step_texts = [
            ("01", "Open OrcaSlicer."),
            ("02", "Go to File > Import > Import Config Bundle."),
            ("03", "Select the generated .orca_printer file below."),
            ("04", "After import, pick the imported printer and check the filament/process presets."),
        ]
        for index, (number, text) in enumerate(step_texts):
            tk.Label(steps, text=number, font=UI_FONT_BOLD, bg=PANEL_TINT, fg=ORANGE).grid(row=index, column=0, sticky="nw", padx=(0, 12), pady=(0, 8))
            tk.Label(steps, text=text, font=UI_FONT, bg=PANEL_TINT, fg=INK, wraplength=600, justify="left").grid(row=index, column=1, sticky="w", pady=(0, 8))

        file_box = tk.Frame(shell, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1, padx=12, pady=12)
        file_box.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        file_box.grid_columnconfigure(0, weight=1)
        tk.Label(file_box, text=self.tr("generated_bundle_file"), font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK).grid(row=0, column=0, sticky="w")
        selected_path = tk.StringVar(value=outputs[0])
        listbox = tk.Listbox(
            file_box,
            bg=PANEL_TINT,
            fg=INK,
            selectbackground=TEAL,
            selectforeground=PANEL_BG,
            font=UI_FONT,
            height=min(4, max(1, len(outputs))),
            relief="flat",
            highlightbackground=LINE,
            highlightthickness=1,
        )
        listbox.grid(row=1, column=0, sticky="ew", pady=(8, 10))
        for path in outputs:
            listbox.insert("end", path)
        listbox.selection_set(0)

        def select_path(_event=None):
            selected = listbox.curselection()
            if selected:
                selected_path.set(outputs[selected[0]])

        def copy_path():
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_path.get())
            self.set_progress(1, "Import path copied")

        def open_selected_folder():
            target = Path(selected_path.get()).parent
            target.mkdir(parents=True, exist_ok=True)
            os.startfile(str(target))

        listbox.bind("<<ListboxSelect>>", select_path)
        tk.Label(file_box, textvariable=selected_path, font=UI_FONT, bg=PANEL_BG, fg=MUTED, wraplength=680, justify="left").grid(row=2, column=0, sticky="w")

        buttons = tk.Frame(shell, bg=APP_BG)
        buttons.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        self._button(buttons, self.tr("copy_file_path"), copy_path, variant="primary").pack(side="left")
        self._button(buttons, self.tr("open_output_folder"), open_selected_folder, variant="secondary").pack(side="left", padx=(8, 0))
        self._button(buttons, self.tr("open_orca_guide"), self.open_orca_guide, variant="secondary").pack(side="left", padx=(8, 0))
        self._button(buttons, self.tr("cancel"), self.import_wizard.destroy, variant="ghost").pack(side="right")

    def open_orca_guide(self):
        webbrowser.open("https://github.com/SoftFever/OrcaSlicer/wiki")

    def open_tools(self):
        if self.tools_window and self.tools_window.winfo_exists():
            self.tools_window.lift()
            self.tools_window.focus_force()
            return
        self.tools_window = self.make_child_window(self.tr("tools"), 620, 460, 500, 360)

        shell = tk.Frame(self.tools_window, bg=APP_BG, padx=18, pady=16)
        shell.pack(fill="both", expand=True)
        tk.Label(shell, text=self.tr("tools"), font=SECTION_FONT, bg=APP_BG, fg=INK).pack(anchor="w")
        tk.Label(
            shell,
            text=self.tr("tools_description"),
            font=UI_FONT,
            bg=APP_BG,
            fg=MUTED,
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(4, 14))

        for title, description, command in [
            ("OrcaSlicer guide", "Open the official OrcaSlicer wiki in your browser.", self.open_orca_guide),
            (self.tr("check_updates"), "Compare this app version with the latest GitHub release.", self.check_for_updates),
            ("Bug report", "Generate an anonymized zip report for support.", self.export_bug_report),
            (self.tr("copy_debug_info"), "Copy version, paths, and risk summary to clipboard.", self.copy_debug_info),
            (self.tr("language"), self.tr("language_intro"), self.open_language_selector),
        ]:
            row = tk.Frame(shell, bg=PANEL_TINT, highlightbackground=LINE, highlightthickness=1, padx=12, pady=10)
            row.pack(fill="x", pady=(0, 10))
            row.grid_columnconfigure(0, weight=1)
            tk.Label(row, text=title, font=UI_FONT_BOLD, bg=PANEL_TINT, fg=INK).grid(row=0, column=0, sticky="w")
            tk.Label(row, text=description, font=UI_FONT, bg=PANEL_TINT, fg=MUTED, wraplength=330, justify="left").grid(row=1, column=0, sticky="w", pady=(3, 0))
            self._button(row, self.tr("open"), command, variant="secondary").grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

    def check_for_updates(self):
        self.set_progress(0.15, "Checking GitHub releases...")

        def worker():
            try:
                request = urllib.request.Request(
                    GITHUB_RELEASES_API,
                    headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"},
                )
                with urllib.request.urlopen(request, timeout=10) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                latest = payload.get("tag_name", "").lstrip("vV") or payload.get("name", "")
                release_url = payload.get("html_url") or GITHUB_RELEASES_URL
                if not latest:
                    raise ValueError("No version tag found in the latest GitHub release.")
                self.root.after(0, lambda: self.show_update_result(latest, release_url))
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    message = "No GitHub release found yet for this repository."
                else:
                    message = f"GitHub update check failed: HTTP {exc.code}"
                self.root.after(0, lambda: messagebox.showinfo("Updates", message))
                self.root.after(0, lambda: self.set_progress(0, "Update check unavailable"))
            except Exception as exc:
                error = str(exc)
                self.root.after(0, lambda: messagebox.showerror("Updates", error))
                self.root.after(0, lambda: self.set_progress(0, "Update check failed"))

        threading.Thread(target=worker, daemon=True).start()

    def show_update_result(self, latest, release_url):
        self.set_progress(1, f"Latest release: {latest}")
        if compare_versions(latest, APP_VERSION) > 0:
            open_release = messagebox.askyesno(
                "Update available",
                f"A newer PrusaToOrca release is available.\n\n"
                f"Installed: {APP_VERSION}\nLatest: {latest}\n\nOpen GitHub Releases?",
            )
            if open_release:
                webbrowser.open(release_url)
        else:
            messagebox.showinfo("Updates", f"PrusaToOrca is up to date.\n\nInstalled: {APP_VERSION}\nLatest: {latest}")

    def configure_tree_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Prusa.Treeview",
            background=PANEL_BG,
            foreground=INK,
            fieldbackground=PANEL_BG,
            rowheight=28,
            bordercolor=LINE,
            font=UI_FONT,
        )
        style.configure(
            "Prusa.Treeview.Heading",
            background=HEADER_BG,
            foreground=HEADER_FG,
            relief="flat",
            font=UI_FONT_BOLD,
        )
        style.map("Prusa.Treeview", background=[("selected", TEAL)], foreground=[("selected", PANEL_BG)])

    def open_mapping_editor(self):
        if not self.advanced_model:
            messagebox.showinfo(self.tr("mapping_editor"), self.tr("mapping_need_preview"))
            return
        ignored_rows = self.advanced_model.get("ignored", [])
        if not ignored_rows:
            messagebox.showinfo(self.tr("mapping_editor"), self.tr("mapping_no_ignored"))
            return

        self.configure_tree_style()
        win = self.make_child_window(self.tr("mapping_editor"), 1080, 640, 900, 520)

        shell = tk.Frame(win, bg=APP_BG, padx=18, pady=16)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=3)
        shell.grid_columnconfigure(1, weight=2)
        shell.grid_rowconfigure(2, weight=1)

        tk.Label(shell, text=self.tr("mapping_editor"), font=SECTION_FONT, bg=APP_BG, fg=INK).grid(row=0, column=0, sticky="w")
        tk.Label(
            shell,
            text=self.tr("mapping_intro"),
            font=UI_FONT,
            bg=APP_BG,
            fg=MUTED,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 12))

        search_var = tk.StringVar()
        tk.Entry(
            shell,
            textvariable=search_var,
            font=UI_FONT,
            bg=PANEL_BG,
            fg=INK,
            insertbackground=INK,
            relief="flat",
            highlightbackground=LINE,
            highlightthickness=1,
        ).grid(row=0, column=1, sticky="ew", padx=(18, 0))

        table_frame = tk.Frame(shell, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 16))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(
            table_frame,
            style="Prusa.Treeview",
            columns=("type", "section", "key", "value"),
            show="headings",
            selectmode="browse",
        )
        for col, text, width in [
            ("type", "Type", 80),
            ("section", "Section", 220),
            ("key", "Prusa key", 210),
            ("value", "Value", 220),
        ]:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor="w")
        scroll = tk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        form = tk.Frame(shell, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1, padx=14, pady=14)
        form.grid(row=2, column=1, sticky="nsew")
        form.grid_columnconfigure(0, weight=1)

        selected_text = tk.StringVar(value=self.tr("select_ignored"))
        target_var = tk.StringVar()
        as_list_var = tk.BooleanVar(value=False)
        tk.Label(form, textvariable=selected_text, font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK, wraplength=360, justify="left").grid(row=0, column=0, sticky="ew")
        tk.Label(form, text=self.tr("orca_target_key"), font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK).grid(row=1, column=0, sticky="w", pady=(18, 6))
        target_combo = ttk.Combobox(form, textvariable=target_var, values=self.orca_key_catalog(), font=UI_FONT)
        target_combo.grid(row=2, column=0, sticky="ew")
        tk.Checkbutton(
            form,
            text=self.tr("store_as_list"),
            variable=as_list_var,
            font=UI_FONT,
            bg=PANEL_BG,
            fg=INK,
            activebackground=PANEL_BG,
            activeforeground=INK,
            selectcolor=PANEL_BG,
            anchor="w",
        ).grid(row=3, column=0, sticky="w", pady=(10, 18))

        saved_label = tk.Label(form, text=self.tr("saved_mappings"), font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK)
        saved_label.grid(row=5, column=0, sticky="w", pady=(18, 6))
        saved_box = tk.Listbox(
            form,
            bg=PANEL_TINT,
            fg=INK,
            selectbackground=TEAL,
            selectforeground=PANEL_BG,
            font=UI_FONT,
            relief="flat",
            highlightbackground=LINE,
            highlightthickness=1,
            height=7,
        )
        saved_box.grid(row=6, column=0, sticky="nsew")
        form.grid_rowconfigure(6, weight=1)

        visible_rows = []

        def mapping_spec(section_type, prusa_key):
            spec = self.custom_mappings.get(section_type, {}).get(prusa_key)
            if isinstance(spec, str):
                return spec, section_type == "filament"
            if isinstance(spec, dict):
                return spec.get("target") or spec.get("orca_key") or "", bool(spec.get("as_list"))
            return "", section_type == "filament"

        def render_saved():
            saved_box.delete(0, "end")
            for section_type in ("printer", "filament", "process"):
                for prusa_key, spec in sorted(self.custom_mappings.get(section_type, {}).items()):
                    target, as_list = mapping_spec(section_type, prusa_key)
                    suffix = "[]" if as_list else ""
                    saved_box.insert("end", f"{section_type}: {prusa_key} -> {target}{suffix}")

        def render_rows(*_args):
            for child in tree.get_children():
                tree.delete(child)
            visible_rows.clear()
            query = search_var.get().strip().lower()
            for row in ignored_rows:
                haystack = " ".join([row["section_type"], row["section_name"], row["key"], row["value"]]).lower()
                if query and query not in haystack:
                    continue
                visible_rows.append(row)
                tree.insert(
                    "",
                    "end",
                    iid=str(len(visible_rows) - 1),
                    values=(row["section_type"], row["section_name"], row["key"], row["value"]),
                )

        def current_row():
            selected = tree.selection()
            if not selected:
                return None
            index = int(selected[0])
            if index >= len(visible_rows):
                return None
            return visible_rows[index]

        def on_select(_event=None):
            row = current_row()
            if not row:
                return
            selected_text.set(f"{row['section_type']} / {row['section_name']}\n{row['key']} = {row['value']}")
            target, as_list = mapping_spec(row["section_type"], row["key"])
            target_var.set(target)
            as_list_var.set(as_list)
            target_combo.configure(values=self.orca_key_catalog(row["section_type"]))

        def save_mapping():
            row = current_row()
            target = target_var.get().strip()
            if not row or not target:
                messagebox.showinfo(self.tr("mapping_editor"), self.tr("mapping_need_target"))
                return
            section_type = row["section_type"]
            self.custom_mappings.setdefault(section_type, {})[row["key"]] = {
                "target": target,
                "as_list": bool(as_list_var.get()),
            }
            self.save_custom_mappings()
            render_saved()
            messagebox.showinfo(self.tr("mapping_editor"), self.tr("mapping_saved"))

        def remove_mapping():
            row = current_row()
            if not row:
                return
            section_type = row["section_type"]
            self.custom_mappings.get(section_type, {}).pop(row["key"], None)
            self.save_custom_mappings()
            target_var.set("")
            render_saved()

        buttons = tk.Frame(form, bg=PANEL_BG)
        buttons.grid(row=4, column=0, sticky="ew")
        self._button(buttons, self.tr("save_mapping"), save_mapping, variant="primary").pack(side="left")
        self._button(buttons, self.tr("remove"), remove_mapping, variant="secondary").pack(side="left", padx=(8, 0))
        self._button(buttons, self.tr("preview_again"), self.preview, variant="secondary").pack(side="left", padx=(8, 0))

        search_var.trace_add("write", render_rows)
        tree.bind("<<TreeviewSelect>>", on_select)
        render_rows()
        render_saved()
        if visible_rows:
            tree.selection_set("0")
            on_select()

    def anonymize_path(self, value):
        text = str(value)
        home = str(Path.home())
        return text.replace(home, "<USER_HOME>")

    def export_bug_report(self):
        if not self.advanced_model:
            messagebox.showinfo("PrusaToOrca", self.tr("bug_report_need_preview"))
            return
        reports_dir = app_file("bug_reports")
        reports_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = reports_dir / f"PrusaToOrca-bug-report-{stamp}.zip"
        payload = {
            "app": APP_NAME,
            "version": APP_VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source": self.anonymize_path(self.input_path.get()),
            "output": self.anonymize_path(self.output_path.get()),
            "risk": self.advanced_model.get("risk", {}),
            "totals": self.advanced_model.get("totals", {}),
            "rows": [
                {key: self.anonymize_path(value) if key in {"source", "value"} else value for key, value in row.items()}
                for row in self.report_rows
            ],
        }
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("report.json", json.dumps(payload, indent=2, ensure_ascii=False))
            zf.writestr("advanced_report.txt", self.report_views.get("Advanced report", ""))
        messagebox.showinfo("PrusaToOrca", self.tr("bug_report_exported", path=target))

    def copy_debug_info(self):
        info = (
            f"{APP_NAME} {APP_VERSION}\n"
            f"root={app_root()}\n"
            f"python={sys.version.split()[0]}\n"
            f"source={self.input_path.get()}\n"
            f"output={self.output_path.get()}\n"
            f"risk={self.advanced_model.get('risk', {}).get('level', 'N/A') if self.advanced_model else 'N/A'}"
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(info)
        messagebox.showinfo("PrusaToOrca", self.tr("debug_copied"))

    def open_history(self):
        self.configure_tree_style()
        win = self.make_child_window(self.tr("history"), 1080, 620, 860, 460)

        shell = tk.Frame(win, bg=APP_BG, padx=18, pady=16)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)

        header = tk.Frame(shell, bg=APP_BG)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text=self.tr("history"), font=SECTION_FONT, bg=APP_BG, fg=INK).grid(row=0, column=0, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(
            header,
            textvariable=search_var,
            font=UI_FONT,
            bg=PANEL_BG,
            fg=INK,
            insertbackground=INK,
            relief="flat",
            highlightbackground=LINE,
            highlightthickness=1,
        ).grid(row=0, column=1, sticky="ew", padx=(18, 0))

        toolbar = tk.Frame(shell, bg=APP_BG)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(12, 10))

        table_frame = tk.Frame(shell, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(
            table_frame,
            style="Prusa.Treeview",
            columns=("date", "risk", "bundles", "converted", "approx", "ignored", "source", "output"),
            show="headings",
            selectmode="browse",
        )
        columns = [
            ("date", "Date", 150),
            ("risk", "Risk", 80),
            ("bundles", "Bundles", 70),
            ("converted", "OK", 70),
            ("approx", "Approx", 70),
            ("ignored", "Ignored", 80),
            ("source", "Source", 260),
            ("output", "Output", 260),
        ]
        for col, text, width in columns:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor="w")
        scroll = tk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        visible_items = []

        def render_history(*_args):
            for child in tree.get_children():
                tree.delete(child)
            visible_items.clear()
            query = search_var.get().strip().lower()
            for item in reversed(self.history[-100:]):
                haystack = " ".join(str(item.get(key, "")) for key in ("date", "risk", "source", "output_folder")).lower()
                if query and query not in haystack:
                    continue
                visible_items.append(item)
                tree.insert(
                    "",
                    "end",
                    iid=str(len(visible_items) - 1),
                    values=(
                        item.get("date", ""),
                        item.get("risk", ""),
                        item.get("bundles", ""),
                        item.get("converted", ""),
                        item.get("approx", ""),
                        item.get("ignored", ""),
                        self.anonymize_path(item.get("source", "")),
                        self.anonymize_path(item.get("output_folder", "")),
                    ),
                )

        def selected_item():
            selected = tree.selection()
            if not selected:
                return None
            index = int(selected[0])
            return visible_items[index] if index < len(visible_items) else None

        def open_selected_output():
            item = selected_item()
            if not item:
                messagebox.showinfo(self.tr("history"), self.tr("history_select_first"))
                return
            target = Path(item.get("output_folder") or self.output_path.get())
            target.mkdir(parents=True, exist_ok=True)
            os.startfile(str(target))

        def reopen_selected_report():
            item = selected_item()
            if not item:
                messagebox.showinfo(self.tr("history"), self.tr("history_select_first"))
                return
            snapshot = item.get("report_snapshot")
            if not snapshot:
                messagebox.showinfo(self.tr("history"), self.tr("history_no_snapshot"))
                return
            self.input_path.set(item.get("source", ""))
            self.output_path.set(item.get("output_folder", self.output_path.get()))
            self.report_views = snapshot.get("views", {})
            self.report_rows = snapshot.get("rows", [])
            self.advanced_model = snapshot.get("advanced_model")
            self.set_report_views(self.report_views, self.report_rows, self.advanced_model)
            self.show_report_tab("Advanced report")
            self.open_advanced_report()

        self._button(toolbar, self.tr("open_output_folder"), open_selected_output, variant="secondary").pack(side="left")
        self._button(toolbar, self.tr("reopen_report"), reopen_selected_report, variant="primary").pack(side="left", padx=(8, 0))
        self._button(toolbar, self.tr("refresh"), render_history, variant="secondary").pack(side="left", padx=(8, 0))

        search_var.trace_add("write", render_history)
        render_history()
        if visible_items:
            tree.selection_set("0")

    def write_report(self, text):
        self.report.configure(state="normal")
        self.report.delete("1.0", "end")
        self.report.insert("1.0", text)
        self.report.configure(state="disabled")

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        self.preview_btn.configure(state=state)
        self.convert_btn.configure(state=state)


def main():
    load_embedded_fonts()
    root_cls = TkinterDnD.Tk if TkinterDnD else tk.Tk
    root = root_cls()
    PrusaToOrcaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
