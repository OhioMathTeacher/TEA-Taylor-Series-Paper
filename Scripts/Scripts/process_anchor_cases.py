#!/usr/bin/env python3
"""
Process all 30 anchor cases through PK-WAP analyzer.
Finds transcript files in Original Data and runs batch analysis.
"""

import os
import subprocess
from pathlib import Path
import csv

# Read anchor case list
anchor_ids = []
with open('anchor_cases_list.txt', 'r') as f:
    anchor_ids = [line.strip() for line in f]

print(f"Processing {len(anchor_ids)} anchor cases...")

# Find transcript files
data_dir = Path("../Data Formatted to Analyze")
transcript_files = {}

for anchor_id in anchor_ids:
    # Extract group and section from ID (e.g., P110-GX-SX -> GX, SX)
    # Try to find the file
    found = False
    
    # Search recursively in Data Formatted to Analyze
    for txt_file in data_dir.rglob(f"{anchor_id}.txt"):
        transcript_files[anchor_id] = txt_file
        found = True
        break
    
    if not found:
        for docx_file in data_dir.rglob(f"{anchor_id}.docx"):
            transcript_files[anchor_id] = docx_file
            found = True
            break
    
    if not found:
        print(f"  WARNING: Could not find transcript for {anchor_id}")

print(f"\nFound {len(transcript_files)} out of {len(anchor_ids)} transcripts")

# Create a temporary directory with copies/symlinks for batch processing
batch_dir = Path("anchor_transcripts_batch")
batch_dir.mkdir(exist_ok=True)

for anchor_id, source_file in transcript_files.items():
    # Copy file to batch directory
    dest_file = batch_dir / source_file.name
    if not dest_file.exists():
        # Create symlink instead of copy to save space
        dest_file.symlink_to(source_file.absolute())

print(f"\nPrepared {len(list(batch_dir.iterdir()))} files in {batch_dir}")

# Run PK-WAP analyzer
print("\n" + "="*60)
print("Running PK-WAP Analyzer...")
print("="*60)

cmd = [
    "python3", "pkwap_analyzer.py",
    "--batch", str(batch_dir),
    "--output", "PK-WAP Memos",
    "--template", "Generating Analytic Memos/P00-G00-S0 PK-WAP TEMPLATE.md"
]

print(f"Command: {' '.join(cmd)}\n")
subprocess.run(cmd)

print("\n" + "="*60)
print("PK-WAP analysis complete!")
print(f"Memos saved to: PK-WAP Memos/")
print("="*60)
