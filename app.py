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
        self.current_report_tab = "Summary"
        self.tab_buttons = {}
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
        logo_path = resource_path("logo.png")
        if logo_path.exists():
            try:
                self.logo_image = tk.PhotoImage(file=str(logo_path)).subsample(12, 12)
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

        stats = tk.Frame(top, bg=APP_BG)
        stats.grid(row=0, column=1, sticky="e")
        for label, value in [
            ("mode", "safe"),
            ("prefix", "on"),
            ("compat", "strict"),
        ]:
            item = tk.Frame(stats, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1)
            item.pack(side="left", padx=(8, 0))
            tk.Label(item, text=label, font=UI_FONT, bg=PANEL_BG, fg=MUTED, padx=10, pady=5).pack(side="left")
            tk.Label(item, text=value, font=UI_FONT_BOLD, bg=TEAL if label == "compat" else INK, fg=PANEL_BG, padx=10, pady=5).pack(side="left")

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
        for text in ["Summary", "Bundle files", "Conversion log"]:
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
                "Conversion log": "No conversion log yet.\n",
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
            command=self.refresh_preview_if_ready,
        )
        return btn

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
        self.set_report_views(
            {
                "Summary": "Choose a PrusaSlicer config bundle or a folder to preview the safe Orca import.\n",
                "Bundle files": "No bundle preview yet.\n",
                "Conversion log": "No conversion log yet.\n",
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
            views, rows = self.build_report_views(previews, done=False)
            self.last_preview = previews
            self.root.after(0, lambda: self.set_report_views(views, rows))
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
            views, rows = self.build_report_views(results, done=True)
            self.last_preview = results
            self.root.after(0, lambda: self.set_report_views(views, rows))
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
        log_lines = [
            "Conversion log",
            "",
        ]

        for index, (preview, log) in enumerate(entries, 1):
            files = preview["files"]
            printers = [n for n in files if n.startswith("printer/")]
            filaments = [n for n in files if n.startswith("filament/")]
            processes = [n for n in files if n.startswith("process/")]
            total_printers += len(printers)
            total_filaments += len(filaments)
            total_processes += len(processes)

            source = preview.get("source_path", "")
            summary.extend(
                [
                    f"  {index}. {Path(source).name if source else 'bundle'}",
                    f"     output: {preview['output_path']}",
                    f"     presets: {len(printers)} printer / {len(filaments)} filament / {len(processes)} process",
                ]
            )

            bundle_lines.extend(
                [
                    f"Bundle {index}: {Path(source).name if source else 'bundle'}",
                    f"Output: {preview['output_path']}",
                    f"Bundle id: {preview['bundle']['bundle_id']}",
                    "",
                ]
            )
            bundle_lines.extend(f"  {name}" for name in sorted(files))
            bundle_lines.append("")

            log_lines.extend(
                [
                    f"Bundle {index}: {Path(source).name if source else 'bundle'}",
                    f"Converted: {log.total_mapped} | Approx: {log.total_approx} | Ignored: {log.total_skipped}",
                ]
            )
            if log.warnings:
                log_lines.append("Warnings:")
                log_lines.extend(f"  {warning}" for warning in log.warnings)
            for section in log.sections:
                log_lines.append(
                    f"  [{section.type}] {section.name} "
                    f"ok={section.n_mapped} approx={section.n_approx} ignored={section.n_skipped}"
                )
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
            log_lines.append("")

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
                "Conversion log": "\n".join(log_lines).strip() + "\n",
            },
            rows,
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

    def set_report_views(self, views, rows):
        self.report_views = views
        self.report_rows = rows
        self.show_report_tab(self.current_report_tab if self.current_report_tab in views else "Summary")

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
