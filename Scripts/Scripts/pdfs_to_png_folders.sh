#!/bin/bash
# Batch convert all PDFs in a directory to PNGs in their own folders.
# Usage:
#   ./pdfs_to_png_folders.sh           # Uses current directory
#   ./pdfs_to_png_folders.sh /path/to/pdfs  # Uses given directory

DENSITY=200

# Use argument as directory, or current directory if none given
TARGET_DIR="${1:-.}"

# Expand relative path
cd "$TARGET_DIR" || { echo "Cannot cd to $TARGET_DIR"; exit 1; }

for pdf in *.pdf; do
  [ -e "$pdf" ] || continue
  base="${pdf%.pdf}"
  mkdir -p "$base"
  magick -density $DENSITY "$pdf" -quality 90 "$base/${base}_page_%02d.png"
  echo "Processed: $pdf"
done

echo "All done in $TARGET_DIR!"
