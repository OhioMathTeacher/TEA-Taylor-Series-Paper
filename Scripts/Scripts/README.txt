# PDFsToPNGs Batch Converter

This tool lets you quickly convert every page of every PDF in a folder into high-quality PNG images, with **each PDF’s pages stored in its own subfolder**.

## 📦 What’s Included

- `pdfs_to_png_tk.py` — The graphical app (Python/Tkinter) you run.
- `pdfs_to_png_folders.sh` — The shell script that does the batch conversion.
- (This `README.md`)

## 💻 Requirements

- Mac (tested on macOS 13+)
- Python 3 (most Macs have this pre-installed)
- [ImageMagick](https://imagemagick.org/) and [Ghostscript](https://ghostscript.com/) installed (`brew install imagemagick ghostscript`).
    - **Tip:** If you already used Homebrew for PDF processing, you likely have these!

## 🚀 How to Use

1. **Unzip** this folder anywhere on your Mac.

2. **Open Terminal** and `cd` into this folder:
   ```bash
   cd /path/to/PDFsToPNGs
