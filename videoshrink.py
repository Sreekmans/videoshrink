"""
VideoShrink - Convert any video to optimized MP4
Output: always MP4, H.264, chosen resolution, quality-controlled
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import re
import sys
import shutil

APP_TITLE = "VideoShrink"
APP_BG = "#1e1e2e"
PANEL_BG = "#2a2a3e"
ACCENT = "#7c3aed"
ACCENT_HOVER = "#6d28d9"
TEXT = "#e2e8f0"
TEXT_DIM = "#94a3b8"
SUCCESS = "#22c55e"
ERROR = "#ef4444"
BORDER = "#3d3d5c"


def find_ffmpeg():
    """Locate ffmpeg executable."""
    # When frozen by PyInstaller, bundled files are in sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        bundled = os.path.join(sys._MEIPASS, "ffmpeg.exe")
        if os.path.isfile(bundled):
            return bundled
    # Check PATH
    found = shutil.which("ffmpeg")
    if found:
        return found
    # Common Windows install paths
    candidates = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def parse_duration(stderr_line):
    """Extract total duration in seconds from ffmpeg output."""
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr_line)
    if m:
        h, mn, s, cs = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return h * 3600 + mn * 60 + s + cs / 100
    return None


def parse_time(stderr_line):
    """Extract current time position from ffmpeg progress output."""
    m = re.search(r"time=(\d+):(\d+):(\d+)\.(\d+)", stderr_line)
    if m:
        h, mn, s, cs = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return h * 3600 + mn * 60 + s + cs / 100
    return None


class VideoShrink(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self.configure(bg=APP_BG)

        self.ffmpeg_path = find_ffmpeg()
        self.input_path = tk.StringVar()
        self.resolution = tk.StringVar(value="1080")
        self.quality = tk.IntVar(value=75)
        self.process = None
        self._converting = False

        self._build_ui()
        self._center_window()

        if not self.ffmpeg_path:
            self.after(200, self._warn_no_ffmpeg)

    def _build_ui(self):
        pad = {"padx": 20, "pady": 10}

        # Title bar
        title_frame = tk.Frame(self, bg=ACCENT, height=52)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        tk.Label(
            title_frame, text="  VideoShrink",
            font=("Segoe UI", 16, "bold"), bg=ACCENT, fg="white", anchor="w"
        ).pack(side="left", padx=16)
        tk.Label(
            title_frame, text="mp4 · smallest size · best quality",
            font=("Segoe UI", 9), bg=ACCENT, fg="#c4b5fd", anchor="e"
        ).pack(side="right", padx=16)

        # Main content
        main = tk.Frame(self, bg=APP_BG, padx=24, pady=20)
        main.pack(fill="both")

        # Input file
        self._section_label(main, "INPUT FILE")
        file_row = tk.Frame(main, bg=APP_BG)
        file_row.pack(fill="x", pady=(4, 12))
        self.file_entry = tk.Entry(
            file_row, textvariable=self.input_path,
            font=("Segoe UI", 10), bg=PANEL_BG, fg=TEXT,
            insertbackground=TEXT, relief="flat",
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT, width=46
        )
        self.file_entry.pack(side="left", ipady=6, padx=(0, 8))
        self._btn(file_row, "Browse", self._browse, small=True).pack(side="left")

        # Resolution
        self._section_label(main, "RESOLUTION")
        res_row = tk.Frame(main, bg=APP_BG)
        res_row.pack(fill="x", pady=(4, 12))
        for label, val in [("1080p  (Full HD)", "1080"), ("720p  (HD)", "720")]:
            rb = tk.Radiobutton(
                res_row, text=label, variable=self.resolution, value=val,
                font=("Segoe UI", 10), bg=APP_BG, fg=TEXT,
                selectcolor=ACCENT, activebackground=APP_BG,
                activeforeground=TEXT, indicatoron=False,
                relief="flat", padx=16, pady=6,
                highlightthickness=1, highlightbackground=BORDER,
                cursor="hand2"
            )
            rb.pack(side="left", padx=(0, 8))
            rb.bind("<Enter>", lambda e, w=rb: w.config(highlightbackground=ACCENT))
            rb.bind("<Leave>", lambda e, w=rb: w.config(
                highlightbackground=ACCENT if self.resolution.get() == w.cget("value") else BORDER
            ))

        # Quality slider
        self._section_label(main, "QUALITY")
        slider_frame = tk.Frame(main, bg=APP_BG)
        slider_frame.pack(fill="x", pady=(4, 12))
        tk.Label(slider_frame, text="Small", font=("Segoe UI", 9),
                 bg=APP_BG, fg=TEXT_DIM).pack(side="left")
        self.slider = ttk.Scale(
            slider_frame, from_=1, to=100,
            variable=self.quality, orient="horizontal", length=320,
            command=self._update_quality_label
        )
        self.slider.pack(side="left", padx=8)
        tk.Label(slider_frame, text="Best", font=("Segoe UI", 9),
                 bg=APP_BG, fg=TEXT_DIM).pack(side="left")
        self.quality_label = tk.Label(
            slider_frame, text="75", font=("Segoe UI", 10, "bold"),
            bg=APP_BG, fg=ACCENT, width=4
        )
        self.quality_label.pack(side="left", padx=(8, 0))

        # Divider
        tk.Frame(main, bg=BORDER, height=1).pack(fill="x", pady=8)

        # Convert button
        self.convert_btn = self._btn(main, "Convert", self._start_convert, big=True)
        self.convert_btn.pack(pady=(8, 4))

        # Progress
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main, variable=self.progress_var, maximum=100, length=480
        )
        self.progress_bar.pack(fill="x", pady=(8, 0))

        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            main, textvariable=self.status_var,
            font=("Segoe UI", 9), bg=APP_BG, fg=TEXT_DIM, anchor="w"
        )
        self.status_label.pack(fill="x", pady=(4, 0))

        # Output path hint
        self.output_label = tk.Label(
            main, text="", font=("Segoe UI", 8),
            bg=APP_BG, fg=TEXT_DIM, anchor="w", wraplength=480
        )
        self.output_label.pack(fill="x")

        self.input_path.trace_add("write", self._update_output_hint)

        # Style sliders
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScale", background=APP_BG, troughcolor=PANEL_BG, sliderlength=18)
        style.configure("TProgressbar", troughcolor=PANEL_BG, background=ACCENT, thickness=8)

    def _section_label(self, parent, text):
        tk.Label(
            parent, text=text, font=("Segoe UI", 8, "bold"),
            bg=APP_BG, fg=TEXT_DIM, anchor="w"
        ).pack(fill="x")

    def _btn(self, parent, text, command, small=False, big=False):
        font_size = 9 if small else (12 if big else 10)
        px = 10 if small else (32 if big else 16)
        py = 4 if small else (8 if big else 6)
        btn = tk.Button(
            parent, text=text, command=command,
            font=("Segoe UI", font_size, "bold"),
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            activeforeground="white", relief="flat", cursor="hand2",
            padx=px, pady=py, bd=0
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT))
        return btn

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _update_quality_label(self, val=None):
        self.quality_label.config(text=str(int(float(val or self.quality.get()))))

    def _update_output_hint(self, *_):
        path = self.input_path.get()
        if path and os.path.isfile(path):
            out = self._build_output_path(path)
            self.output_label.config(text=f"Output: {out}")
        else:
            self.output_label.config(text="")

    def _build_output_path(self, input_path):
        folder = os.path.dirname(input_path)
        base = os.path.splitext(os.path.basename(input_path))[0]
        res = self.resolution.get()
        return os.path.join(folder, f"{base}_{res}p.mp4")

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.ts *.mts *.mpg *.mpeg *.3gp *.ogv"),
                ("All files", "*.*"),
            ]
        )
        if path:
            self.input_path.set(path)

    def _warn_no_ffmpeg(self):
        messagebox.showwarning(
            "FFmpeg not found",
            "FFmpeg was not found on your system.\n\n"
            "VideoShrink requires FFmpeg to convert videos.\n\n"
            "Install it with:\n"
            "  winget install Gyan.FFmpeg\n\n"
            "Or download from: https://ffmpeg.org/download.html\n\n"
            "After installing, restart VideoShrink.\n\n"
            "Alternatively, place ffmpeg.exe in the same folder as this script."
        )

    def _quality_to_crf(self, q):
        """Map quality slider (1-100) to H.264 CRF (28=small → 18=quality)."""
        return int(round(28 - (q - 1) / 99 * 10))

    def _start_convert(self):
        if self._converting:
            self._cancel()
            return

        if not self.ffmpeg_path:
            self._warn_no_ffmpeg()
            return

        input_path = self.input_path.get().strip()
        if not input_path or not os.path.isfile(input_path):
            messagebox.showerror("No file", "Please select a valid input video file.")
            return

        output_path = self._build_output_path(input_path)
        if os.path.exists(output_path):
            if not messagebox.askyesno("Overwrite?", f"Output file already exists:\n{output_path}\n\nOverwrite?"):
                return

        res = self.resolution.get()
        crf = self._quality_to_crf(self.quality.get())
        scale = f"scale=-2:{res}"  # -2 keeps aspect ratio, divisible by 2

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-vf", scale,
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", "slow",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        self._converting = True
        self.convert_btn.config(text="Cancel", bg="#dc2626")
        self.progress_var.set(0)
        self.status_label.config(fg=TEXT_DIM)
        self._set_status("Starting conversion...")

        threading.Thread(target=self._run_ffmpeg, args=(cmd, output_path), daemon=True).start()

    def _run_ffmpeg(self, cmd, output_path):
        duration = None
        try:
            self.process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            for line in self.process.stderr:
                if duration is None:
                    d = parse_duration(line)
                    if d:
                        duration = d
                t = parse_time(line)
                if t is not None and duration:
                    pct = min(t / duration * 100, 99)
                    self.after(0, self._update_progress, pct, f"Converting... {pct:.0f}%")

            self.process.wait()
            rc = self.process.returncode

            if rc == 0:
                size = os.path.getsize(output_path) / (1024 * 1024)
                self.after(0, self._done, True, output_path, size)
            else:
                self.after(0, self._done, False, None, None)

        except Exception as e:
            self.after(0, self._done, False, None, None, str(e))
        finally:
            self.process = None

    def _cancel(self):
        if self.process:
            self.process.terminate()
        self._reset_ui()
        self._set_status("Cancelled.")

    def _update_progress(self, pct, status):
        self.progress_var.set(pct)
        self._set_status(status)

    def _done(self, success, output_path, size_mb, error=None):
        self.progress_var.set(100 if success else 0)
        self._reset_ui()
        if success:
            self.status_label.config(fg=SUCCESS)
            self._set_status(f"Done!  {size_mb:.1f} MB  →  {os.path.basename(output_path)}")
        else:
            self.status_label.config(fg=ERROR)
            self._set_status(f"Failed. {error or 'Check that the file is a valid video.'}")

    def _reset_ui(self):
        self._converting = False
        self.convert_btn.config(text="Convert", bg=ACCENT)

    def _set_status(self, msg):
        self.status_var.set(msg)


if __name__ == "__main__":
    app = VideoShrink()
    app.mainloop()
