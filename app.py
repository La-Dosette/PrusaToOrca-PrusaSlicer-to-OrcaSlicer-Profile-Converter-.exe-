#!/usr/bin/env python3
"""
PrusaToOrca desktop interface.

The UI is intentionally conservative: preview first, convert second. This keeps
the safe-import behavior visible instead of hiding it behind a single button.
"""

import threading
import tkinter as tk
import sys
from pathlib import Path
from tkinter import filedialog, messagebox

from convert import ConversionLog, convert_ini_to_orca

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # pragma: no cover - optional desktop enhancement
    DND_FILES = None
    TkinterDnD = None


APP_BG = "#f8f7f4"
PANEL_BG = "#ffffff"
PANEL_TINT = "#f2eee8"
INK = "#2b2825"
MUTED = "#6f6862"
LINE = "#2b2825"
TEAL = "#009aa6"
TEAL_DARK = "#00737d"
ORANGE = "#ff8a00"
ORANGE_DARK = "#de5f00"
RED_ORANGE = "#f04412"
CREAM = APP_BG

UI_FONT = ("Courier New", 10)
UI_FONT_BOLD = ("Courier New", 10, "bold")
TITLE_FONT = ("Arial Black", 28)
SECTION_FONT = ("Courier New", 12, "bold")


def resource_path(name):
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return Path(base) / name


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
        self.last_preview = None
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
        panel = self._panel(parent, "01 // source", "config bundle .ini")

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
        for text, active in [("Summary", True), ("Bundle files", False), ("Conversion log", False)]:
            tk.Label(
                tabs,
                text=text,
                font=UI_FONT_BOLD if active else UI_FONT,
                bg=TEAL_DARK if active else PANEL_BG,
                fg=PANEL_BG if active else MUTED,
                padx=14,
                pady=9,
                highlightbackground=LINE,
                highlightthickness=1,
            ).pack(side="left")

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
        self.report.insert(
            "1.0",
            "Choose a PrusaSlicer config bundle to preview the safe Orca import.\n\n"
            "No file is written during preview.\nExisting Orca presets are not touched by this app.\n",
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
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)

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

    def set_input(self, path):
        self.input_path.set(str(Path(path)))
        self.preview()

    def clear_input(self):
        self.input_path.set("")
        self.last_preview = None
        self.write_report("Choose a PrusaSlicer config bundle to preview the safe Orca import.\n")

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
            messagebox.showinfo("PrusaToOrca", "Choose a .ini file first.")
            return
        self.set_busy(True)
        threading.Thread(target=self._preview_worker, daemon=True).start()

    def _preview_worker(self):
        try:
            log = ConversionLog()
            preview = convert_ini_to_orca(
                self.input_path.get(),
                self.output_path.get(),
                log=log,
                dry_run=True,
                compatibility=self.compatibility.get(),
                prefix_profiles=self.prefix_profiles.get(),
            )
            text = self.format_preview(preview, log)
            self.last_preview = preview
            self.root.after(0, lambda: self.write_report(text))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Preview failed", str(exc)))
        finally:
            self.root.after(0, lambda: self.set_busy(False))

    def convert(self):
        if not self.input_path.get():
            messagebox.showinfo("PrusaToOrca", "Choose a .ini file first.")
            return
        self.set_busy(True)
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _convert_worker(self):
        try:
            log = ConversionLog()
            result = convert_ini_to_orca(
                self.input_path.get(),
                self.output_path.get(),
                log=log,
                dry_run=False,
                compatibility=self.compatibility.get(),
                prefix_profiles=self.prefix_profiles.get(),
            )
            text = self.format_done(result, log)
            self.root.after(0, lambda: self.write_report(text))
            self.root.after(0, lambda: messagebox.showinfo("Done", f"Bundle generated:\n{result}"))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Conversion failed", str(exc)))
        finally:
            self.root.after(0, lambda: self.set_busy(False))

    def format_preview(self, preview, log):
        bundle = preview["bundle"]
        files = preview["files"]
        printers = [n for n in files if n.startswith("printer/")]
        filaments = [n for n in files if n.startswith("filament/")]
        processes = [n for n in files if n.startswith("process/")]

        lines = [
            "SAFE IMPORT PREVIEW",
            "",
            f"Output: {preview['output_path']}",
            f"Mode: compatibility={self.compatibility.get()} / prefix={'on' if self.prefix_profiles.get() else 'off'}",
            "",
            "Will add:",
            f"  {len(printers)} printer preset(s)",
            f"  {len(filaments)} filament preset(s)",
            f"  {len(processes)} process preset(s)",
            "",
            "Safety checks:",
            "  OK generated names are prefixed" if self.prefix_profiles.get() else "  WARNING prefix disabled",
            "  OK existing Orca preset files are not modified by this converter",
            "  OK preview did not write a bundle",
            "",
            "Bundle files:",
        ]
        lines.extend(f"  {name}" for name in sorted(files))
        lines.extend(["", "Bundle id:", f"  {bundle['bundle_id']}", ""])
        lines.extend(self.format_log_lines(log))
        return "\n".join(lines)

    def format_done(self, result, log):
        lines = [
            "BUNDLE GENERATED",
            "",
            str(result),
            "",
            "Next step in OrcaSlicer:",
            "  File > Import > Import Config Bundle",
            "",
        ]
        lines.extend(self.format_log_lines(log))
        return "\n".join(lines)

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
    root_cls = TkinterDnD.Tk if TkinterDnD else tk.Tk
    root = root_cls()
    PrusaToOrcaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
