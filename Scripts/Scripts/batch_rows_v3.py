#!/usr/bin/env python3
"""
Batch runner v3
- Deterministic (TEMPERATURE=0.0)
- Timestamped output dir by default (--outdir to override)
- Optional --annotate to save JSONL / annotated.txt / HTML per transcript
"""

import argparse, csv, json, sys, time
from pathlib import Path
from typing import List, Tuple, Optional

# Optional dependency for .docx
try:
    from docx import Document
except Exception:
    Document = None

from datetime import datetime
from openai import OpenAI

# -------- Defaults --------
MODEL = "gpt-4o"
TEMPERATURE = 0.0
MAX_TOKENS = 800
BATCH_SLEEP = 1.0

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def read_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".docx":
        if Document is None:
            raise RuntimeError("python-docx not installed. `python3 -m pip install python-docx`.")
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {path.suffix}")

def load_prompt(prompt_path: Path) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")

# ---------- LaTeX row helpers ----------
def is_probably_a_row(text: str) -> bool:
    cols = text.split("&")
    return len(cols) == 6 and text.rstrip().endswith("\\\\")

def extract_row(text: str) -> Tuple[str, str]:
    candidates = []
    for line in text.splitlines():
        s = line.strip()
        if s and "&" in s and s.endswith("\\\\"):
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

def parse_numbers_from_row(row: str) -> Optional[tuple]:
    parts = [p.strip() for p in row.rstrip("\\").split("&")]
    if len(parts) != 6:
        return None
    student = parts[0]
    try:
        ai_words = float(parts[1]); student_words = float(parts[2])
        total = float(parts[3]); pct_ai = float(parts[4]); pct_student = float(parts[5])
    except ValueError:
        return None
    return (student, ai_words, student_words, total, pct_ai, pct_student)

def row_looks_valid(row: str, expected_student: str) -> bool:
    parsed = parse_numbers_from_row(row)
    if not parsed:
        return False
    student, ai, st, tot, p_ai, p_st = parsed
    if student != expected_student: return False
    if tot <= 0 or (ai + st) <= 0: return False
    if abs(tot - (ai + st)) > 1: return False
    if abs((p_ai + p_st) - 100.0) > 0.2: return False
    return True

# ---------- OpenAI call ----------
client = OpenAI()  # reads OPENAI_API_KEY from env

def call_openai(messages: List[dict], model: str, temperature: float, max_tokens: int) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )
    return resp.choices[0].message.content.strip()

# ---------- Annotation ----------
def build_html(records: List[dict]) -> str:
    css = """
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; line-height: 1.4; padding: 1rem; }
      .page { margin: 1rem 0; }
      .badge { display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;background:#eee;margin:8px 0; }
      .ai { background:#fff3cd;padding:6px 8px;border-radius:8px;margin:4px 0; }
      .student { background:#d1e7dd;padding:6px 8px;border-radius:8px;margin:4px 0; }
      .speaker { font-weight:600;margin-right:6px; }
      .line { white-space:pre-wrap; }
    </style>
    """
    html = ["<html><head>", css, "</head><body>"]
    current_page = None
    for r in records:
        page = r.get("page")
        sp = r.get("speaker")
        tx = r.get("text","")
        if page != current_page:
            if current_page is not None:
                html.append("</div>")
            html.append(f'<div class="page"><div class="badge">Page {page}</div>')
            current_page = page
        cls = "ai" if sp == "AI" else "student"
        html.append(f'<div class="{cls}"><span class="speaker">[{sp}]</span><span class="line">{tx}</span></div>')
    if current_page is not None:
        html.append("</div>")
    html.append("</body></html>")
    return "".join(html)

def annotate_transcript(student_id: str, transcript: str, base_prompt: str, model: str, out_dir: Path):
    messages = [
        {"role": "system",
         "content": ("You label transcript lines by speaker using Appendix B rules. "
                     "Return ONLY JSON Lines (no code fences, no preamble). "
                     "Each line must be a JSON object: "
                     '{"page": int, "speaker": "AI"|"Student", "text": string}. '
                     "Use the original text for 'text' without rewriting.")},
        {"role": "user",
         "content": (base_prompt + "\nEnsure you respect page markers (B.2)."
                     "\n---\nTRANSCRIPT FOLLOWS\n---\n" + transcript)}
    ]
    raw = call_openai(messages, model=model, temperature=TEMPERATURE, max_tokens=4096)

    records = []
    for line in raw.splitlines():
        line = line.strip()
        if not line: continue
        try:
            obj = json.loads(line)
            if {"page","speaker","text"} <= obj.keys() and obj["speaker"] in {"AI","Student"}:
                records.append({"page": int(obj["page"]), "speaker": obj["speaker"], "text": obj["text"]})
        except Exception:
            pass

    (out_dir / f"{student_id}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8"
    )
    # annotated.txt
    with (out_dir / f"{student_id}.annotated.txt").open("w", encoding="utf-8") as f:
        current = None
        for r in records:
            if r["page"] != current:
                current = r["page"]
                f.write(f"\n-- PAGE {current} --\n")
            f.write(f"[{r['speaker']}] {r['text']}\n")
    # html
    (out_dir / f"{student_id}.html").write_text(build_html(records), encoding="utf-8")

# ---------- Core per-file ----------
def process_file(path: Path, base_prompt: str, model: str, out_raw_dir: Path,
                 do_annotate: bool, annotate_dir: Path) -> Tuple[str, str, str, str]:
    transcript = read_text(path)
    student_id = path.stem
    messages = [
        {"role": "system",
         "content": ("You are a meticulous research assistant. Follow the Appendix B rules. "
                     "Return ONLY a single LaTeX table row in the exact requested column order. "
                     "Do not echo the header. Values must be plain numbers where applicable, "
                     "and the line must end with '\\\\'.")},
        {"role": "user",
         "content": (base_prompt
                     + f"\n\nStudent ID for the first column: {student_id}\n"
                       "Your row MUST start with that exact Student ID.\n"
                       "Column order:\n"
                       "\\textbf{Student} & \\textbf{AI Words} & \\textbf{Student Words} & "
                       "\\textbf{Total} & \\textbf{\\% AI} & \\textbf{\\% Student} \\\\\n"
                       "Return only that single row. No commentary.\n"
                     + "\n---\nTRANSCRIPT FOLLOWS\n---\n" + transcript)}
    ]
    raw = call_openai(messages, model=model, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
    row, status = extract_row(raw)

    if not row_looks_valid(row, student_id):
        messages.append({"role": "assistant",
                         "content": "Your previous answer was invalid (zeros, wrong ID, or inconsistent totals). Recount carefully."})
        messages.append({"role": "user",
                         "content": (f"Return ONLY one row starting with: {student_id}\n"
                                     "Ensure AI+Student=Total and %AI+%Student=100.0 (±0.1). "
                                     "Use nonzero counts where appropriate. No extra text.")})
        raw = call_openai(messages, model=model, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
        row, status = extract_row(raw)

    # Save raw (final)
    (out_raw_dir / f"{path.name}.txt").write_text(raw, encoding="utf-8")

    if do_annotate:
        annotate_transcript(student_id, transcript, base_prompt, model, annotate_dir)

    return path.name, row, status, raw

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, default=".", help="Folder of .txt/.docx transcripts")
    ap.add_argument("--outdir", type=str, default=None, help="Output dir name (default: out_rows_YYYYMMDD_HHMM)")
    ap.add_argument("--prompt", type=str, default="appendix_b_prompt.txt")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", type=str, default=MODEL)
    ap.add_argument("--annotate", action="store_true")
    ap.add_argument("--annotate_dir", type=str, default=None)
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.outdir or f"out_rows_{now_stamp()}")
    out_raw_dir = out_dir / "responses_raw"
    ensure_dir(out_dir); ensure_dir(out_raw_dir)

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

    annotate_dir = Path(args.annotate_dir) if args.annotate_dir else (out_dir / "annotations")
    if args.annotate:
        ensure_dir(annotate_dir)

    with csv_path.open("a", newline="", encoding="utf-8") as fcsv, tex_path.open("a", encoding="utf-8") as ftex:
        writer = csv.DictWriter(fcsv, fieldnames=["filename", "row", "status"])
        if write_header:
            writer.writeheader()

        apply_all = "yes" if args.force else None

        for i, path in enumerate(files, 1):
            if path.name in processed and not args.force:
                if apply_all == "yes":
                    pass
                else:
                    print(f"[skip] {path.name}")
                    continue

            try:
                print(f"[{i}/{len(files)}] Processing {path.name}…")
                filename, row, status, raw = process_file(
                    path, base_prompt, model=args.model,
                    out_raw_dir=out_raw_dir, do_annotate=args.annotate, annotate_dir=annotate_dir
                )

                student_id = path.stem
                if not row_looks_valid(row, student_id):
                    status = "needs_review"

                writer.writerow({"filename": filename, "row": row, "status": status})
                ftex.write(row + "\n")

                parsed = parse_numbers_from_row(row)
                student_pct = f"{parsed[5]:.1f}" if parsed else "?"
                print(f"  → {status}, % Student Talk: {student_pct}")

            except Exception as e:
                err = f"ERROR: {type(e).__name__}: {e}"
                writer.writerow({"filename": path.name, "row": err, "status": "error"})
                print("  → error", err)

            time.sleep(BATCH_SLEEP)

    print("\nDone. Outputs:")
    print(f"  CSV: {csv_path}")
    print(f"  TEX: {tex_path}")
    print(f"  RAW: {out_raw_dir}")
    if args.annotate:
        print(f"  Annotations: {annotate_dir}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
