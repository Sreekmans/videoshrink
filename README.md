# VideoShrink

> Convert any video to a compact, high-quality MP4 — no setup, no choices, just shrink.

![Python](https://img.shields.io/badge/Python-3.7+-blue?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What it does

VideoShrink converts any video file to an optimized MP4 using H.264 encoding. The goal is simple: **smallest possible file, best possible quality** — with no complicated settings.

- Input: any video format (MP4, MKV, AVI, MOV, WMV, WebM, FLV, TS, MPG, and more)
- Output: always **MP4** — no other options, by design
- Resolution: **1080p** or **720p** — auto up/downscales while preserving aspect ratio
- Quality: one slider — that's it

---

## Download

👉 [Download VideoShrink.exe](../../releases/latest)

No installation needed. No Python. No FFmpeg. Just download and run.

---

## Screenshot

<img width="530" height="448" alt="videoshrink" src="https://github.com/user-attachments/assets/bf22575d-c159-4269-8a3d-636c4a88e704" />

---

## How to use

1. Run `VideoShrink.exe`
2. Click **Browse** and select your video file
3. Choose a resolution: **1080p** or **720p**
4. Adjust the **quality slider** (higher = better quality, larger file)
5. Click **Convert**

The output file is saved in the same folder as your input, named `filename_1080p.mp4` or `filename_720p.mp4`.

---

## Quality slider explained

| Slider | Best for |
|--------|----------|
| 90–100 | Archiving, minimal quality loss |
| 60–89  | Sharing, streaming, good balance |
| 1–59   | Maximum compression, smaller files |

---

## Technical details

| Setting | Value |
|---------|-------|
| Video codec | H.264 (libx264) |
| Encoding preset | `slow` (best compression ratio) |
| Audio codec | AAC |
| Audio bitrate | 128 kbps |
| Container | MP4 (faststart) |
| FFmpeg | Bundled inside the exe |

---

## Building from source

**Requirements**
- Python 3.7+
- PyInstaller (`pip install pyinstaller`)

**Run without building**
```bash
python videoshrink.py
```

> Note: requires FFmpeg in PATH or placed next to the script as `ffmpeg.exe`.

**Build the exe**
```bash
pyinstaller --onefile --windowed --name VideoShrink --add-binary "path\to\ffmpeg.exe;." videoshrink.py
```

The exe will be in the `dist\` folder.

---

## License

GNU GENERAL PUBLIC LICENSE
