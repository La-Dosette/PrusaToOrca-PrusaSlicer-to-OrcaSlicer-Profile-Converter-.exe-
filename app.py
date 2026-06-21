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
from pathlib import Path
from tkinter import filedialog, messagebox

from convert import ConversionLog, convert_ini_to_orca

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # pragma: no cover - optional desktop enhancement
    DND_FILES = None
    TkinterDnD = None


APP_BG = "#f3f0e9"
PANEL_BG = "#f3f0e9"
PANEL_TINT = "#ece6da"
INK = "#2b2825"
MUTED = "#6f6862"
LINE = "#2b2825"
TEAL = "#009aa6"
TEAL_DARK = "#00737d"
ORANGE = "#ff8a00"
ORANGE_DARK = "#de5f00"
RED_ORANGE = "#f04412"
CREAM = APP_BG

UI_FONT = ("Space Mono", 10)
UI_FONT_BOLD = ("Space Mono", 10, "bold")
TITLE_FONT = ("Archivo Black", 28)
SECTION_FONT = ("Space Mono", 12, "bold")

STAR = "\u2605"
TRIANGLE = "\u25b3"
CROSS = "\u00d7"
CHECK = "\u2611"

ADV_BG = "#0f0d1d"
ADV_PANEL = "#191730"
ADV_PANEL_ALT = "#22203e"
ADV_LINE = "#343154"
ADV_TEXT = "#f6f2ff"
ADV_MUTED = "#aaa3c9"
ADV_GREEN = "#00e08a"


def resource_path(name):
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return Path(base) / name


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
        self.root.geometry("1120x720")
        self.root.minsize(960, 620)
        self.root.configure(bg=APP_BG)
        try:
            self.root.iconbitmap(resource_path("logo.ico"))
        except Exception:
            pass

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
        self.current_report_tab = "Summary"
        self.tab_buttons = {}
        self.quick_buttons = {}
        self.logo_image = None

        self._build()
        self._wire_drag_drop()

    def _build(self):
        shell = tk.Frame(self.root, bg=APP_BG, padx=22, pady=18)
        shell.pack(fill="both", expand=True)

        self._build_topbar(shell)

        body = tk.Frame(shell, bg=APP_BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0, minsize=360)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=APP_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        right = tk.Frame(body, bg=APP_BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_import_panel(left)
        self._build_options_panel(left)
        self._build_actions(left)
        self._build_preview_panel(right)
        self._build_report_panel(right)

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
            text="PrusaToOrca // safe profile importer",
            font=UI_FONT,
            bg=APP_BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(2, 0))

        quick_actions = tk.Frame(top, bg=APP_BG)
        quick_actions.grid(row=0, column=1, sticky="e")
        for key, text, command in [
            ("safe", "SAFE MODE", self.show_safety_info),
            ("prefix", "PREFIX ON", self.toggle_prefix),
            ("compat", "STRICT", self.toggle_compatibility),
            ("advanced", "ADVANCED REPORT", self.open_advanced_report),
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
        frame.pack(fill="x", pady=(0, 14))
        header = tk.Frame(frame, bg=INK)
        header.pack(fill="x")
        tk.Frame(header, bg=ORANGE, width=6).pack(side="left", fill="y")
        tk.Label(header, text=title, font=SECTION_FONT, bg=INK, fg=PANEL_BG, padx=14, pady=9).pack(side="left")
        if subtitle:
            tk.Label(header, text=subtitle, font=UI_FONT, bg=INK, fg="#d8d2ca", padx=12).pack(side="right")
        content = tk.Frame(frame, bg=PANEL_BG, padx=14, pady=14)
        content.pack(fill="both", expand=True)
        return content

    def _build_import_panel(self, parent):
        panel = self._panel(parent, "01 // source", ".ini file or folder")

        self.drop_zone = tk.Frame(panel, bg=PANEL_TINT, highlightbackground=ORANGE, highlightthickness=2, height=128)
        self.drop_zone.pack(fill="x")
        self.drop_zone.pack_propagate(False)
        drop_accent = tk.Frame(self.drop_zone, bg=TEAL, width=8)
        drop_accent.pack(side="left", fill="y")
        drop_copy = tk.Frame(self.drop_zone, bg=PANEL_TINT)
        drop_copy.pack(side="left", fill="both", expand=True)
        tk.Label(
            drop_copy,
            text="DROP .INI HERE",
            font=("Arial Black", 18),
            bg=PANEL_TINT,
            fg=INK,
        ).pack(anchor="center", expand=True, pady=(18, 0))
        tk.Label(
            drop_copy,
            text="preview before writing anything",
            font=UI_FONT_BOLD,
            bg=PANEL_TINT,
            fg=ORANGE_DARK,
        ).pack(anchor="center", pady=(0, 18))
        tk.Label(
            panel,
            textvariable=self.input_path,
            font=UI_FONT,
            bg=PANEL_BG,
            fg=MUTED,
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(10, 8))

        row = tk.Frame(panel, bg=PANEL_BG)
        row.pack(fill="x")
        self._button(row, "Choose file", self.choose_input, variant="secondary").pack(side="left")
        self._button(row, "Choose folder", self.choose_folder, variant="secondary").pack(side="left", padx=(8, 0))
        self._button(row, "Clear", self.clear_input, variant="ghost").pack(side="left", padx=(8, 0))

    def _build_options_panel(self, parent):
        panel = self._panel(parent, "02 // output", "non destructive")

        tk.Label(panel, text="Output folder", font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK).pack(anchor="w")
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

        tk.Label(panel, text="Compatibility", font=UI_FONT_BOLD, bg=PANEL_BG, fg=INK).pack(anchor="w")
        chips = tk.Frame(panel, bg=PANEL_BG)
        chips.pack(fill="x", pady=(6, 12))
        self._chip(chips, "Strict", "strict").pack(side="left")
        self._chip(chips, "Loose", "loose").pack(side="left", padx=(8, 0))

        check = tk.Checkbutton(
            panel,
            text="Prefix generated presets",
            variable=self.prefix_profiles,
            font=UI_FONT,
            bg=PANEL_BG,
            fg=INK,
            activebackground=PANEL_BG,
            activeforeground=INK,
            selectcolor=PANEL_BG,
            anchor="w",
            command=self.refresh_preview_if_ready,
        )
        check.pack(anchor="w")

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=APP_BG)
        actions.pack(fill="x", pady=(2, 0))
        self.preview_btn = self._button(actions, "Preview safe import", self.preview, variant="secondary")
        self.preview_btn.pack(fill="x", pady=(0, 8))
        self.convert_btn = self._button(actions, "Generate .orca_printer", self.convert, variant="primary")
        self.convert_btn.pack(fill="x")

    def _build_preview_panel(self, parent):
        header = tk.Frame(parent, bg=APP_BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text="03 // preview", font=SECTION_FONT, bg=APP_BG, fg=INK).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text="what will be added to OrcaSlicer",
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
        tabs.grid_columnconfigure(3, weight=1)
        for text in ["Summary", "Bundle files", "Advanced report"]:
            btn = tk.Button(
                tabs,
                text=text,
                command=lambda name=text: self.show_report_tab(name),
                font=UI_FONT_BOLD,
                bg=TEAL_DARK if text == self.current_report_tab else PANEL_BG,
                fg=PANEL_BG if text == self.current_report_tab else MUTED,
                padx=14,
                pady=9,
                relief="flat",
                borderwidth=0,
                highlightbackground=LINE,
                highlightthickness=1,
                cursor="hand2",
            )
            btn.pack(side="left")
            self.tab_buttons[text] = btn
        self.export_btn = self._button(tabs, "Export CSV", self.export_csv, variant="secondary")
        self.export_btn.pack(side="right", padx=(8, 0))

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
        self.set_report_views(
            {
                "Summary": (
                    "Choose a PrusaSlicer config bundle or a folder to preview the safe Orca import.\n\n"
                    "No file is written during preview.\nExisting Orca presets are not touched by this app.\n"
                ),
                "Bundle files": "No bundle preview yet.\n",
                "Advanced report": "No advanced report yet.\n",
            },
            [],
        )
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
            activebackground=INK,
            activeforeground=PANEL_BG,
            relief="flat",
            borderwidth=0,
            highlightbackground=LINE,
            highlightthickness=1,
            padx=12,
            pady=8,
            cursor="hand2",
        )

    def _chip(self, parent, text, value):
        btn = tk.Radiobutton(
            parent,
            text=text,
            value=value,
            variable=self.compatibility,
            indicatoron=False,
            font=UI_FONT_BOLD,
            bg=PANEL_BG,
            fg=INK,
            activebackground=TEAL,
            activeforeground=PANEL_BG,
            selectcolor=TEAL,
            relief="flat",
            borderwidth=0,
            highlightbackground=TEAL if value == "strict" else ORANGE,
            highlightthickness=1,
            padx=12,
            pady=7,
            command=self.on_option_changed,
        )
        return btn

    def on_option_changed(self):
        self.update_quick_actions()
        self.refresh_preview_if_ready()

    def show_safety_info(self):
        messagebox.showinfo(
            "Safe mode",
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

    def update_quick_actions(self):
        prefix = "PREFIX ON" if self.prefix_profiles.get() else "PREFIX OFF"
        compat = self.compatibility.get().upper()
        if "prefix" in self.quick_buttons:
            self.quick_buttons["prefix"].configure(
                text=prefix,
                bg=INK if self.prefix_profiles.get() else PANEL_BG,
                fg=PANEL_BG if self.prefix_profiles.get() else INK,
            )
        if "compat" in self.quick_buttons:
            self.quick_buttons["compat"].configure(
                text=compat,
                bg=TEAL if self.compatibility.get() == "strict" else ORANGE,
                fg=PANEL_BG,
            )
        if "safe" in self.quick_buttons:
            self.quick_buttons["safe"].configure(bg=PANEL_BG, fg=INK)
        if "advanced" in self.quick_buttons:
            self.quick_buttons["advanced"].configure(bg=PANEL_BG, fg=INK)

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
        self.set_report_views(
            {
                "Summary": "Choose a PrusaSlicer config bundle or a folder to preview the safe Orca import.\n",
                "Bundle files": "No bundle preview yet.\n",
                "Advanced report": "No advanced report yet.\n",
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
            messagebox.showinfo("PrusaToOrca", "Choose a .ini file or folder first.")
            return
        self.set_busy(True)
        threading.Thread(target=self._preview_worker, daemon=True).start()

    def _preview_worker(self):
        try:
            previews = []
            used_outputs = set()
            for ini_path in self.source_files():
                log = ConversionLog()
                preview = convert_ini_to_orca(
                    ini_path,
                    self.output_path.get(),
                    log=log,
                    dry_run=True,
                    compatibility=self.compatibility.get(),
                    prefix_profiles=self.prefix_profiles.get(),
                )
                preview["source_path"] = ini_path
                preview["output_path"] = self.unique_output_path(preview["output_path"], used_outputs)
                previews.append((preview, log))
            if not previews:
                raise FileNotFoundError("No .ini files found in the selected folder.")
            views, rows, advanced_model = self.build_report_views(previews, done=False)
            self.last_preview = previews
            self.root.after(0, lambda: self.set_report_views(views, rows, advanced_model))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Preview failed", str(exc)))
        finally:
            self.root.after(0, lambda: self.set_busy(False))

    def convert(self):
        if not self.input_path.get():
            messagebox.showinfo("PrusaToOrca", "Choose a .ini file or folder first.")
            return
        self.set_busy(True)
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _convert_worker(self):
        try:
            results = []
            used_outputs = set()
            for ini_path in self.source_files():
                dry_log = ConversionLog()
                preview = convert_ini_to_orca(
                    ini_path,
                    self.output_path.get(),
                    log=dry_log,
                    dry_run=True,
                    compatibility=self.compatibility.get(),
                    prefix_profiles=self.prefix_profiles.get(),
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
                )
                preview["source_path"] = ini_path
                preview["output_path"] = result
                results.append((preview, log))
            if not results:
                raise FileNotFoundError("No .ini files found in the selected folder.")
            views, rows, advanced_model = self.build_report_views(results, done=True)
            self.last_preview = results
            self.root.after(0, lambda: self.set_report_views(views, rows, advanced_model))
            self.root.after(0, lambda: messagebox.showinfo("Done", f"Generated {len(results)} bundle(s)."))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Conversion failed", str(exc)))
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

    def build_report_views(self, entries, done=False):
        total_printers = total_filaments = total_processes = 0
        rows = []
        summary = [
            "BUNDLE GENERATED" if done else "SAFE IMPORT PREVIEW",
            "",
            f"Source mode: {self.source_mode.get()}",
            f"Input: {self.input_path.get()}",
            f"Output folder: {self.output_path.get()}",
            f"Mode: compatibility={self.compatibility.get()} / prefix={'on' if self.prefix_profiles.get() else 'off'}",
            "",
            f"{'Generated' if done else 'Will generate'} {len(entries)} bundle(s):",
        ]
        bundle_lines = []
        advanced_lines = [
            "ADVANCED REPORT",
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

        return (
            {
                "Summary": "\n".join(summary),
                "Bundle files": "\n".join(bundle_lines).strip() + "\n",
                "Advanced report": "\n".join(advanced_lines).strip() + "\n",
            },
            rows,
            advanced_model,
        )

    def format_log_lines(self, log):
        lines = [
            "Conversion report:",
            f"  converted: {log.total_mapped}",
            f"  approximate: {log.total_approx}",
            f"  ignored: {log.total_skipped}",
        ]
        if log.warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(f"  {warning}" for warning in log.warnings)
        lines.append("")
        lines.append("Sections:")
        for section in log.sections:
            lines.append(
                f"  {section.type:<8} {section.name} "
                f"ok={section.n_mapped} approx={section.n_approx} ignored={section.n_skipped}"
            )
        return lines

    def open_advanced_report(self):
        if not self.advanced_model or not self.advanced_model.get("sections"):
            messagebox.showinfo("PrusaToOrca", "Preview or convert a bundle before opening the advanced report.")
            return
        if self.advanced_window and self.advanced_window.winfo_exists():
            self.advanced_window.lift()
            self.advanced_window.focus_force()
            return

        source = Path(self.advanced_model.get("source") or "bundle").name
        self.advanced_window = tk.Toplevel(self.root)
        self.advanced_window.title(f"Rapport avanc\u00e9 - {source}")
        self.advanced_window.geometry("1120x720")
        self.advanced_window.minsize(920, 600)
        self.advanced_window.configure(bg=ADV_BG)
        try:
            self.advanced_window.iconbitmap(resource_path("logo.ico"))
        except Exception:
            pass

        shell = tk.Frame(self.advanced_window, bg=ADV_BG, padx=16, pady=14)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = tk.Frame(shell, bg=ADV_BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(
            header,
            text="Rapport avanc\u00e9",
            font=("Archivo Black", 18),
            bg=ADV_BG,
            fg=ADV_TEXT,
        ).grid(row=0, column=0, sticky="w")

        stats = tk.Frame(header, bg=ADV_BG)
        stats.grid(row=0, column=2, sticky="e")
        totals = self.advanced_model["totals"]
        self._advanced_stat(stats, f"{CROSS} {totals['ignored']} ignor\u00e9s", "#ff4b4b")
        self._advanced_stat(stats, f"{TRIANGLE} {totals['approx']} approx", ORANGE)
        self._advanced_stat(stats, f"{STAR} {totals['converted']} convertis", "#00e08a")

        sidebar_shell = tk.Frame(shell, bg=ADV_PANEL, highlightbackground=ADV_LINE, highlightthickness=1)
        sidebar_shell.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        sidebar_shell.grid_rowconfigure(1, weight=1)
        tk.Label(
            sidebar_shell,
            text="Sections",
            font=UI_FONT_BOLD,
            bg=ADV_PANEL,
            fg=ADV_MUTED,
            pady=10,
        ).grid(row=0, column=0, sticky="ew")

        side_canvas = tk.Canvas(sidebar_shell, bg=ADV_PANEL, highlightthickness=0, width=230)
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
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_row.grid_columnconfigure(1, weight=1)
        tk.Label(search_row, text="Search", font=UI_FONT_BOLD, bg=ADV_BG, fg=ADV_MUTED).grid(row=0, column=0, padx=(0, 8))
        self.advanced_search = tk.StringVar()
        search = tk.Entry(
            search_row,
            textvariable=self.advanced_search,
            font=UI_FONT,
            bg=ADV_PANEL_ALT,
            fg=ADV_TEXT,
            insertbackground=ADV_TEXT,
            relief="flat",
            highlightbackground=ADV_LINE,
            highlightthickness=1,
        )
        search.grid(row=0, column=1, sticky="ew")
        self.advanced_search.trace_add("write", lambda *_args: self._advanced_render_summary())

        content = tk.Frame(main, bg=ADV_PANEL, highlightbackground=ADV_LINE, highlightthickness=1)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        canvas = tk.Canvas(content, bg=ADV_PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        self.advanced_body = tk.Frame(canvas, bg=ADV_PANEL, padx=16, pady=16)
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
            text="Fermer",
            command=self.advanced_window.destroy,
            font=UI_FONT,
            bg=ADV_BG,
            fg=ADV_MUTED,
            activebackground=ADV_PANEL_ALT,
            activeforeground=ADV_TEXT,
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=8,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            footer,
            text="Exporter CSV",
            command=self.export_csv,
            font=UI_FONT_BOLD,
            bg="#6c5cff",
            fg=ADV_TEXT,
            activebackground=TEAL,
            activeforeground=ADV_TEXT,
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=8,
            cursor="hand2",
        ).pack(side="left")

        self._advanced_render_sidebar()
        self._advanced_render_summary()

    def _advanced_stat(self, parent, text, color):
        tk.Label(
            parent,
            text=text,
            font=UI_FONT_BOLD,
            bg=ADV_PANEL_ALT,
            fg=color,
            padx=12,
            pady=7,
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
            font=UI_FONT_BOLD if active else UI_FONT,
            bg=ADV_PANEL_ALT if active else ADV_PANEL,
            fg=ADV_TEXT,
            activebackground=ADV_PANEL_ALT,
            activeforeground=ADV_TEXT,
            relief="flat",
            borderwidth=0,
            anchor="w",
            padx=12,
            pady=8,
            wraplength=190,
            cursor="hand2",
        )
        btn.pack(fill="x")

    def _advanced_query(self):
        if not self.advanced_search:
            return ""
        return self.advanced_search.get().strip().lower()

    def _advanced_filter_sections(self):
        query = self._advanced_query()
        sections = self.advanced_model.get("sections", [])
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
        sections = self._advanced_filter_sections()
        title = "R\u00e9sum\u00e9 par section"
        if self._advanced_query():
            title += f" - {len(sections)} r\u00e9sultat(s)"
        tk.Label(
            self.advanced_body,
            text=title,
            font=("Archivo Black", 16),
            bg=ADV_PANEL,
            fg=ADV_TEXT,
        ).pack(anchor="w", pady=(0, 14))

        if not sections:
            tk.Label(
                self.advanced_body,
                text="Aucune section ne correspond \u00e0 la recherche.",
                font=UI_FONT,
                bg=ADV_PANEL,
                fg=ADV_MUTED,
            ).pack(anchor="w")
            return

        for section in sections:
            self._advanced_section_card(section)

    def _advanced_section_card(self, section):
        card = tk.Frame(self.advanced_body, bg=ADV_PANEL_ALT, highlightbackground=ADV_LINE, highlightthickness=1, padx=14, pady=12)
        card.pack(fill="x", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)

        top = tk.Frame(card, bg=ADV_PANEL_ALT)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        title = f"{self._advanced_icon(section['type'])}  {section['name']}"
        tk.Label(top, text=title, font=UI_FONT_BOLD, bg=ADV_PANEL_ALT, fg=ADV_TEXT).grid(row=0, column=0, sticky="w")
        stats = tk.Frame(top, bg=ADV_PANEL_ALT)
        stats.grid(row=0, column=1, sticky="e")
        for text, color in [
            (f"{STAR} {section['converted']}", "#00e08a"),
            (f"{TRIANGLE} {section['approx']}", ORANGE),
            (f"{CROSS} {section['ignored']}", "#ff4b4b"),
            (f"{section['coverage']}% couverture", "#7d75ff"),
        ]:
            tk.Label(stats, text=text, font=UI_FONT_BOLD, bg=ADV_PANEL_ALT, fg=color, padx=8).pack(side="left")

        bar = tk.Frame(card, bg="#2f2c4d", height=7)
        bar.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        bar.grid_propagate(False)
        fill = tk.Frame(bar, bg=TEAL)
        fill.place(relx=0, rely=0, relwidth=max(0.01, section["coverage"] / 100), relheight=1)
        if section["coverage"] < 100:
            warn = tk.Frame(bar, bg=ORANGE)
            warn.place(relx=0, rely=0, relwidth=max(0.01, (100 - section["coverage"]) / 100), relheight=1)
            fill.lift()

        for widget in (card, top, bar):
            widget.bind("<Button-1>", lambda _event, s=section: self._advanced_render_detail(s))
            widget.configure(cursor="hand2")

    def _advanced_render_detail(self, section):
        if not self.advanced_body:
            return
        self._advanced_clear(self.advanced_body)
        tk.Label(
            self.advanced_body,
            text=f"{self._advanced_icon(section['type'])} {section['name']}",
            font=("Archivo Black", 16),
            bg=ADV_PANEL,
            fg=ADV_TEXT,
        ).pack(anchor="w")
        tk.Label(
            self.advanced_body,
            text=f"{section['source_name']} / {section['type']} / {section['coverage']}% couverture",
            font=UI_FONT,
            bg=ADV_PANEL,
            fg=ADV_MUTED,
        ).pack(anchor="w", pady=(4, 12))

        stats = tk.Frame(self.advanced_body, bg=ADV_PANEL)
        stats.pack(anchor="w", pady=(0, 16))
        for text, color in [
            (f"{STAR} {section['converted']} convertis", "#00e08a"),
            (f"{TRIANGLE} {section['approx']} approx", ORANGE),
            (f"{CROSS} {section['ignored']} ignor\u00e9s", "#ff4b4b"),
        ]:
            tk.Label(stats, text=text, font=UI_FONT_BOLD, bg=ADV_PANEL_ALT, fg=color, padx=10, pady=6).pack(side="left", padx=(0, 8))

        self._advanced_table_header(["Cl\u00e9 PrusaSlicer", "Cl\u00e9 OrcaSlicer", "Valeur", "Statut"])
        for prusa_key, orca_key, value, note, approx in section["mapped"]:
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
            font=("Archivo Black", 16),
            bg=ADV_PANEL,
            fg=ADV_TEXT,
        ).pack(anchor="w", pady=(0, 14))
        if not ignored:
            tk.Label(
                self.advanced_body,
                text="Aucun champ ignor\u00e9 pour ce filtre.",
                font=UI_FONT,
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
                font=UI_FONT_BOLD,
                bg=ADV_PANEL_ALT,
                fg=ADV_MUTED,
                anchor="w",
                padx=8,
                pady=7,
            ).grid(row=0, column=index, sticky="ew")

    def _advanced_table_row(self, columns, approx=False, ignored=False, status_index=None):
        row_bg = "#111021" if ignored else "#141326"
        status_color = "#ff4b4b" if ignored else ORANGE if approx else ADV_GREEN
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
                font=UI_FONT,
                bg=row_bg,
                fg=status_color,
                anchor="w",
                padx=8,
                pady=6,
                wraplength=520 if index == status_index else 340,
                justify="left",
            ).grid(row=0, column=index, sticky="ew")

    def set_report_views(self, views, rows, advanced_model=None):
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
        self.write_report(self.report_views.get(name, "No report yet.\n"))

    def export_csv(self):
        if not self.report_rows:
            messagebox.showinfo("PrusaToOrca", "Preview or convert a bundle before exporting CSV.")
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
        messagebox.showinfo("PrusaToOrca", f"CSV report exported:\n{path}")

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
