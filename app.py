#!/usr/bin/env python3
"""
PrusaToOrca desktop interface.

The UI is intentionally conservative: preview first, convert second. This keeps
the safe-import behavior visible instead of hiding it behind a single button.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from convert import ConversionLog, convert_ini_to_orca

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # pragma: no cover - optional desktop enhancement
    DND_FILES = None
    TkinterDnD = None


CREAM = "#f3f0e9"
INK = "#1a1a1a"
MUTED = "#5a5853"
LINE = "#1a1a1a"
GREEN = "#168a5b"
ORANGE = "#d97706"
RED = "#b91c1c"
PANEL = "#ebe6da"

UI_FONT = ("Courier New", 10)
UI_FONT_BOLD = ("Courier New", 10, "bold")
TITLE_FONT = ("Arial Black", 28)
SECTION_FONT = ("Courier New", 12, "bold")


class PrusaToOrcaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PrusaToOrca")
        self.root.geometry("1120x720")
        self.root.minsize(960, 620)
        self.root.configure(bg=CREAM)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar(value=str(Path.home() / "Desktop"))
        self.compatibility = tk.StringVar(value="strict")
        self.prefix_profiles = tk.BooleanVar(value=True)
        self.last_preview = None

        self._build()
        self._wire_drag_drop()

    def _build(self):
        shell = tk.Frame(self.root, bg=CREAM, padx=22, pady=18)
        shell.pack(fill="both", expand=True)

        self._build_topbar(shell)

        body = tk.Frame(shell, bg=CREAM)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0, minsize=360)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=CREAM)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        right = tk.Frame(body, bg=CREAM)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_import_panel(left)
        self._build_options_panel(left)
        self._build_actions(left)
        self._build_preview_panel(right)
        self._build_report_panel(right)

    def _build_topbar(self, parent):
        top = tk.Frame(parent, bg=CREAM)
        top.pack(fill="x", pady=(0, 18))
        top.grid_columnconfigure(1, weight=1)

        brand = tk.Frame(top, bg=CREAM)
        brand.grid(row=0, column=0, sticky="w")
        tk.Label(brand, text="PTO", font=TITLE_FONT, bg=CREAM, fg=INK).pack(anchor="w")
        tk.Label(
            brand,
            text="PrusaToOrca // safe profile importer",
            font=UI_FONT,
            bg=CREAM,
            fg=MUTED,
        ).pack(anchor="w", pady=(2, 0))

        stats = tk.Frame(top, bg=CREAM)
        stats.grid(row=0, column=1, sticky="e")
        for label, value in [
            ("mode", "safe"),
            ("prefix", "on"),
            ("compat", "strict"),
        ]:
            item = tk.Frame(stats, bg=CREAM, highlightbackground=LINE, highlightthickness=1)
            item.pack(side="left", padx=(8, 0))
            tk.Label(item, text=label, font=UI_FONT, bg=CREAM, fg=MUTED, padx=10, pady=5).pack(side="left")
            tk.Label(item, text=value, font=UI_FONT_BOLD, bg=INK, fg=CREAM, padx=10, pady=5).pack(side="left")

    def _panel(self, parent, title, subtitle=None):
        frame = tk.Frame(parent, bg=CREAM, highlightbackground=LINE, highlightthickness=1)
        frame.pack(fill="x", pady=(0, 14))
        header = tk.Frame(frame, bg=INK)
        header.pack(fill="x")
        tk.Label(header, text=title, font=SECTION_FONT, bg=INK, fg=CREAM, padx=14, pady=9).pack(side="left")
        if subtitle:
            tk.Label(header, text=subtitle, font=UI_FONT, bg=INK, fg=CREAM, padx=12).pack(side="right")
        content = tk.Frame(frame, bg=CREAM, padx=14, pady=14)
        content.pack(fill="both", expand=True)
        return content

    def _build_import_panel(self, parent):
        panel = self._panel(parent, "01 // source", "config bundle .ini")

        self.drop_zone = tk.Frame(panel, bg=PANEL, highlightbackground=LINE, highlightthickness=1, height=128)
        self.drop_zone.pack(fill="x")
        self.drop_zone.pack_propagate(False)
        tk.Label(
            self.drop_zone,
            text="DROP .INI HERE",
            font=("Arial Black", 18),
            bg=PANEL,
            fg=INK,
        ).pack(anchor="center", expand=True)
        tk.Label(
            panel,
            textvariable=self.input_path,
            font=UI_FONT,
            bg=CREAM,
            fg=MUTED,
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(10, 8))

        row = tk.Frame(panel, bg=CREAM)
        row.pack(fill="x")
        self._button(row, "Choose file", self.choose_input, variant="secondary").pack(side="left")
        self._button(row, "Clear", self.clear_input, variant="ghost").pack(side="left", padx=(8, 0))

    def _build_options_panel(self, parent):
        panel = self._panel(parent, "02 // output", "non destructive")

        tk.Label(panel, text="Output folder", font=UI_FONT_BOLD, bg=CREAM, fg=INK).pack(anchor="w")
        out_row = tk.Frame(panel, bg=CREAM)
        out_row.pack(fill="x", pady=(6, 12))
        tk.Entry(
            out_row,
            textvariable=self.output_path,
            font=UI_FONT,
            bg=CREAM,
            fg=INK,
            insertbackground=INK,
            relief="flat",
            highlightbackground=LINE,
            highlightthickness=1,
        ).pack(side="left", fill="x", expand=True, ipady=8)
        self._button(out_row, "...", self.choose_output, variant="secondary", width=4).pack(side="left", padx=(8, 0))

        tk.Label(panel, text="Compatibility", font=UI_FONT_BOLD, bg=CREAM, fg=INK).pack(anchor="w")
        chips = tk.Frame(panel, bg=CREAM)
        chips.pack(fill="x", pady=(6, 12))
        self._chip(chips, "Strict", "strict").pack(side="left")
        self._chip(chips, "Loose", "loose").pack(side="left", padx=(8, 0))

        check = tk.Checkbutton(
            panel,
            text="Prefix generated presets",
            variable=self.prefix_profiles,
            font=UI_FONT,
            bg=CREAM,
            fg=INK,
            activebackground=CREAM,
            activeforeground=INK,
            selectcolor=CREAM,
            anchor="w",
            command=self.refresh_preview_if_ready,
        )
        check.pack(anchor="w")

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=CREAM)
        actions.pack(fill="x", pady=(2, 0))
        self.preview_btn = self._button(actions, "Preview safe import", self.preview, variant="secondary")
        self.preview_btn.pack(fill="x", pady=(0, 8))
        self.convert_btn = self._button(actions, "Generate .orca_printer", self.convert, variant="primary")
        self.convert_btn.pack(fill="x")

    def _build_preview_panel(self, parent):
        header = tk.Frame(parent, bg=CREAM)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text="03 // preview", font=SECTION_FONT, bg=CREAM, fg=INK).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text="what will be added to OrcaSlicer",
            font=UI_FONT,
            bg=CREAM,
            fg=MUTED,
        ).grid(row=0, column=1, sticky="e")

    def _build_report_panel(self, parent):
        frame = tk.Frame(parent, bg=CREAM, highlightbackground=LINE, highlightthickness=1)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tabs = tk.Frame(frame, bg=CREAM)
        tabs.grid(row=0, column=0, sticky="ew")
        for text, active in [("Summary", True), ("Bundle files", False), ("Conversion log", False)]:
            tk.Label(
                tabs,
                text=text,
                font=UI_FONT_BOLD if active else UI_FONT,
                bg=INK if active else CREAM,
                fg=CREAM if active else MUTED,
                padx=14,
                pady=9,
                highlightbackground=LINE,
                highlightthickness=1,
            ).pack(side="left")

        self.report = tk.Text(
            frame,
            bg=CREAM,
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
            bg, fg, border = INK, CREAM, INK
        elif variant == "secondary":
            bg, fg, border = CREAM, INK, INK
        else:
            bg, fg, border = CREAM, MUTED, CREAM
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=UI_FONT_BOLD if variant == "primary" else UI_FONT,
            bg=bg,
            fg=fg,
            activebackground=INK,
            activeforeground=CREAM,
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
            bg=CREAM,
            fg=INK,
            activebackground=INK,
            activeforeground=CREAM,
            selectcolor=INK,
            relief="flat",
            borderwidth=0,
            highlightbackground=LINE,
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
