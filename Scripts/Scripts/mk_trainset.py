#!/usr/bin/env python3
"""
mk_trainset.py — build a labeled CSV from annotated transcripts

Usage:
  python3 mk_trainset.py --annot screen_run4/annotated --out train_lines.csv [--include-unk]

It expects lines like:
  [AI] ...text...
  [STUDENT] ...text...
  [AI?] ...text...       (uncertain tags are allowed)
  [AI][IGNORED] ...      (ignored from training)
  [UNK] ...              (dropped unless --include-unk)

Outputs CSV with: filename, line_idx, label, text, uncertain
"""
import argparse, csv, re
from pathlib import Path

def parse_line(line: str):
    line = line.rstrip("\n")
    if not line.strip():
        return None
    # skip instruction lines like [AI][IGNORED] ...
    if line.startswith("[AI][IGNORED]"):
        return None
    # core pattern: [AI], [STUDENT], [UNK] with optional ? for uncertain
    m = re.match(r"^\[(AI|STUDENT|UNK)(\?)?\]\s*(.*)$", line)
    if not m:
        return None
    label = m.group(1)
    uncertain = bool(m.group(2))
    text = m.group(3).strip()
    if not text:
        return None
    return label, uncertain, text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annot", required=True, help="Folder with __annotated.txt files")
    ap.add_argument("--out", required=True, help="Output CSV path, e.g., train_lines.csv")
    ap.add_argument("--include-unk", action="store_true", help="Include [UNK] lines in the dataset")
    args = ap.parse_args()

    annot_dir = Path(args.annot).expanduser().resolve()
    out_csv = Path(args.out).expanduser().resolve()

    files = sorted([p for p in annot_dir.iterdir()
                    if p.suffix.lower()==".txt" and p.name.endswith("__annotated.txt")])
    if not files:
        raise SystemExit(f"No annotated files found in {annot_dir}")

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filename","line_idx","label","text","uncertain"])
        w.writeheader()
        total = 0
        for fp in files:
            with open(fp, "r", encoding="utf-8") as fh:
                for i, ln in enumerate(fh, 1):
                    rec = parse_line(ln)
                    if rec is None:
                        continue
                    label, uncertain, text = rec
                    if label == "UNK" and not args.include_unk:
                        continue
                    w.writerow({
                        "filename": fp.name,
                        "line_idx": i,
                        "label": label,
                        "text": text,
                        "uncertain": int(uncertain)
                    })
                    total += 1
    print(f"Wrote {total} labeled lines to {out_csv}")

if __name__ == "__main__":
    main()
