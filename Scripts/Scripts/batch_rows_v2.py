#!/usr/bin/env python3
"""
Batch runner to convert transcripts (.txt/.docx) into single LaTeX table rows
using your Appendix B prompt. Enforces Student ID in col 1, validates numbers,
and retries once on bad output.

Usage:
  python3 batch_rows.py --input "." --limit 10 --force --model gpt-4o
"""

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

# Optional dependency for .docx
try:
    from docx import Document  # python-docx
except Exception:
    Document = None

# ---------- Defaults (can be overridden via CLI) ----------
INPUT_DIR = Path("./transcripts")
OUT_DIR = Path("./out_rows")
RAW_DIR = OUT_DIR / "responses_raw"
PROMPT_PATH = Path("./appendix_b_prompt.txt")
MODEL = "gpt-4o"
TEMPERATURE = 0.1
MAX_TOKENS = 800
BATCH_SLEEP = 1.0  # seconds between calls

def is_probably_a_row(text: str) -> bool:
    """Heuristic: exactly six columns separated by '&' and ending with '\\\\'."""
    cols = text.split("&")
    if len(cols) != 6:
        return False
    return text.rstrip().endswith("\\\\")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".docx":
        if Document is None:
            raise RuntimeError("python-docx not installed. `python3 -m pip install python-docx`. ")
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def load_prompt(prompt_path: Path) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def call_openai(messages: List[dict], model: str, temperature: float, max_tokens: int) -> str:
    """Minimal OpenAI chat call. Requires OPENAI_API_KEY env var."""
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("Please `python3 -m pip install openai` (>=1.0) to use this script") from e

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )
    return resp.choices[0].message.content.strip()


def extract_row(text: str) -> Tuple[str, str]:
    """
    Return (row, status). We try to find a single LaTeX row.
    Ignore header-like lines that mention \\textbf or '% Student'.
    """
    candidates = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if "&" in s and s.endswith("\\\\"):
            candidates.append(s)

    if not candidates:
        return text, "needs_review"

    def looks_like_data_row(s: str) -> bool:
        if s.count("&") != 5:
            return False
        lowered = s.lower()
        if "\\textbf" in lowered or "% student" in lowered or "\\% student" in lowered:
            return False
        return True

    data_rows = [c for c in candidates if looks_like_data_row(c)]
    if data_rows:
        row = min(data_rows, key=len)
        return row, ("ok" if is_probably_a_row(row) else "needs_review")

    row = min(candidates, key=len)
    return row, ("ok" if is_probably_a_row(row) else "needs_review")


# ---------- Row validation helpers ----------
def parse_numbers_from_row(row: str) -> Optional[tuple]:
    parts = [p.strip() for p in row.rstrip("\\").split("&")]
    if len(parts) != 6:
        return None
    student = parts[0]
    try:
        ai_words = float(parts[1])
        student_words = float(parts[2])
        total = float(parts[3])
        pct_ai = float(parts[4])
        pct_student = float(parts[5])
    except ValueError:
        return None
    return (student, ai_words, student_words, total, pct_ai, pct_student)


def row_looks_valid(row: str, expected_student: str) -> bool:
    parsed = parse_numbers_from_row(row)
    if not parsed:
        return False
    student, ai, st, tot, p_ai, p_st = parsed
    if student != expected_student:
        return False
    if tot <= 0 or (ai + st) <= 0:
        return False
    if abs(tot - (ai + st)) > 1:  # allow small rounding
        return False
    if abs((p_ai + p_st) - 100.0) > 0.2:
        return False
    return True


def process_file(path: Path, base_prompt: str, model: str, temperature: float, max_tokens: int) -> Tuple[str, str, str, str]:
    transcript = read_text(path)
    student_id = path.stem  # e.g., P01-G8-S4
    messages = [
        {
            "role": "system",
            "content": (
                "You are a meticulous research assistant. Follow the Appendix B rules. "
                "Return ONLY a single LaTeX table row in the exact requested column order. "
                "Do not echo the header. Values must be plain numbers where applicable, end the line with '\\\\'."
            ),
        },
        {
            "role": "user",
            "content": (
                base_prompt
                + f"\n\nStudent ID for the first column: {student_id}\n"
                  "Your row MUST start with that exact Student ID.\n"
                  "Column order:\n"
                  "\\textbf{Student} & \\textbf{AI Words} & \\textbf{Student Words} & "
                  "\\textbf{Total} & \\textbf{\\% AI} & \\textbf{\\% Student} \\\\\n"
                  "Return only that single row. No commentary.\n"
                + "\n---\nTRANSCRIPT FOLLOWS\n---\n"
                + transcript
            ),
        },
    ]

    raw = call_openai(messages, model=model, temperature=temperature, max_tokens=max_tokens)
    row, status = extract_row(raw)

    # Validate; if bad, retry once with a corrective nudge
    if not row_looks_valid(row, student_id):
        messages.append({
            "role": "assistant",
            "content": "Your previous answer was invalid (zeros, wrong ID, or inconsistent totals). Recount carefully."
        })
        messages.append({
            "role": "user",
            "content": (
                f"Return ONLY one row starting with: {student_id}\n"
                "Ensure AI+Student=Total and %AI+%Student=100.0 (±0.1). "
                "Use nonzero counts where appropriate. No extra text."
            ),
        })
        raw = call_openai(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        row, status = extract_row(raw)

    return path.name, row, status, raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, default=str(INPUT_DIR), help="Folder of .txt/.docx transcripts")
    ap.add_argument("--out", type=str, default=str(OUT_DIR), help="Output folder")
    ap.add_argument("--prompt", type=str, default=str(PROMPT_PATH), help="Path to the finalized prompt text")
    ap.add_argument("--limit", type=int, default=None, help="Max files to process (e.g., 10, 25, 50)")
    ap.add_argument("--force", action="store_true", help="Re-process even if results already exist for a file")
    ap.add_argument("--model", type=str, default=MODEL, help="Model name (e.g., gpt-4o)")
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.out)
    raw_dir = RAW_DIR if RAW_DIR.is_absolute() else out_dir / RAW_DIR.name
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    base_prompt = load_prompt(Path(args.prompt))

    files = [p for p in sorted(in_dir.iterdir()) if p.suffix.lower() in {".txt", ".docx"}]
    if args.limit is not None:
        files = files[: args.limit]

    csv_path = out_dir / "rows.csv"
    tex_path = out_dir / "rows.tex"

    processed = set()
    if csv_path.exists() and not args.force:
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                processed.add(row["filename"])  # type: ignore

    write_header = not csv_path.exists() or args.force
    if args.force and csv_path.exists():
        csv_path.unlink()
        tex_path.unlink(missing_ok=True)

    with csv_path.open("a", newline="", encoding="utf-8") as fcsv, tex_path.open("a", encoding="utf-8") as ftex:
        writer = csv.DictWriter(fcsv, fieldnames=["filename", "row", "status"])
        if write_header:
            writer.writeheader()

        # If --force, re-run without prompting; else ask about previously processed files
        apply_all = "yes" if args.force else None  # None | "yes" | "skip"

        for i, path in enumerate(files, 1):
            if path.name in processed and not args.force:
                if apply_all == "yes":
                    pass  # re-run without asking
                elif apply_all == "skip":
                    print(f"[skip] {path.name}")
                    continue
                else:
                    choice = input(
                        f"[skip?] {path.name} is already processed. Re-run it? "
                        "(y/N, A=all yes, S=all skip): "
                    ).strip().lower()

                    if choice == "a":
                        apply_all = "yes"   # re-run all remaining
                    elif choice == "s":
                        apply_all = "skip"  # skip all remaining
                        print(f"[skip] {path.name}")
                        continue
                    elif choice != "y":     # default: skip this one
                        print(f"[skip] {path.name}")
                        continue

            try:
                print(f"[{i}/{len(files)}] Processing {path.name}…")
                filename, row, status, raw = process_file(
                    path, base_prompt, model=args.model, temperature=TEMPERATURE, max_tokens=MAX_TOKENS
                )

                # Save raw response
                (raw_dir / f"{filename}.txt").write_text(raw, encoding="utf-8")

                # Validate row; downgrade status if it still looks bad
                student_id = path.stem
                if not row_looks_valid(row, student_id):
                    status = "needs_review"

                # Append outputs
                writer.writerow({"filename": filename, "row": row, "status": status})
                ftex.write(row + "\n")

                # Progress: print last column (% Student), if parseable
                try:
                    parsed = parse_numbers_from_row(row)
                    student_pct = f"{parsed[5]:.1f}" if parsed else "?"
                except Exception:
                    student_pct = "?"
                print(f"  → {status}, % Student Talk: {student_pct}")

            except Exception as e:
                err = f"ERROR: {type(e).__name__}: {e}"
                writer.writerow({"filename": path.name, "row": err, "status": "error"})
                print("  → error", err)

            time.sleep(BATCH_SLEEP)

    print("\nDone. Outputs:")
    print(f"  CSV: {csv_path}")
    print(f"  TEX: {tex_path}")
    print(f"  RAW: {raw_dir}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
