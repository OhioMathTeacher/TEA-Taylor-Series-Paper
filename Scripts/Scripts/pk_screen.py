
#!/usr/bin/env python3
"""
pk_screen.py — Deterministic transcript screening (Phase 1)

What it does
------------
- Loads .txt or .docx transcripts from an input folder
- Splits into pages (formfeed, "Page N" markers, or whole file)
- Attributes each line to AI vs Student via explicit tags + simple heuristics
- Tokenizes deterministically with special handling for URLs, emails, CJK runs, and math-ish tokens
- Produces per-file summary CSV (ai_words, student_words, total, % student) and optional per-page CSV
- (Optional) Writes an annotated transcript with speaker tags for human audit

This is a local, repeatable baseline. No LLM calls, no randomness.

Install (if needed)
-------------------
python3 -m pip install python-docx

Usage
-----
python3 pk_screen.py --input "Data Formatted to Analyze" \
  --outdir screen_run1 --annotate

Key outputs
-----------
screen_run1/summary.csv        # one-row-per-file counts
screen_run1/pages.csv          # per-page counts
screen_run1/annotated/*.txt    # optional, side-by-side attribution
screen_run1/log.txt            # run log (files processed, warnings)
"""

import argparse
import csv
import math
import re
import sys
import unicodedata
from pathlib import Path
from datetime import datetime

# Optional docx import
try:
    import docx  # python-docx
except Exception:
    docx = None


AI_LABELS = [
    r"AI", r"Assistant", r"ChatGPT", r"Teacher", r"Tutor", r"Instructor", r"Bot", r"System"
]
STUDENT_LABELS = [
    r"Student", r"User", r"You", r"Learner", r"S"
]

# common AI preambles to ignore (these add zero tokens if matched at the line start)
AI_PREAMBLE_PREFIXES = [
    "Sure", "Certainly", "Of course", "Here is", "Here’s", "Let's", "Let’s",
    "As an AI", "I can help", "I can explain", "I will", "Great question",
    "Absolutely", "Happy to", "I'd be happy", "I’d be happy"
]

URL_RE = re.compile(r"(?i)\\b(?:https?://|www\\.)\\S+")
EMAIL_RE = re.compile(r"(?i)\\b[\\w.+-]+@[\\w.-]+\\.[a-z]{2,}\\b")

# crude "math-ish" span: tokens containing operator-like chars
MATH_CHARS = r"\\^_+\\-=*/%<>×÷=()\\[\\]{}≈≃≅≡∼∑∏√∞°·•→←≤≥±∫∂≔⟂⊥∥"
MATH_RE = re.compile(fr"[{MATH_CHARS}]")

# Basic CJK ranges (CJK Unified Ideographs, Extension A; Hiragana/Katakana; Hangul)
CJK_RE = re.compile(
    "["
    "\\u3400-\\u4DBF"
    "\\u4E00-\\u9FFF"
    "\\u3040-\\u30FF"
    "\\uAC00-\\uD7AF"
    "]"
)

PAGE_MARKERS = [
    re.compile(r"^\\s*[-=]{2,}\\s*Page\\s*\\d+\\s*[-=]{2,}\\s*$", re.I),
    re.compile(r"^\\s*Page\\s*\\d+\\s*$", re.I),
]


def load_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".docx":
        if docx is None:
            raise RuntimeError("python-docx not installed. `pip install python-docx`. ")
        d = docx.Document(str(path))
        return "\n".join(p.text for p in d.paragraphs)
    raise ValueError(f"Unsupported file type: {path}")


def normalize_text(s: str) -> str:
    # normalize unicode & whitespace; standardize smart quotes
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s


def split_pages(text: str) -> list[str]:
    # If formfeed present, split on it
    if "\f" in text:
        return [p for p in text.split("\f")]
    # Otherwise attempt to split on explicit page markers
    lines = text.split("\n")
    pages = []
    current = []
    for ln in lines:
        if any(pat.match(ln) for pat in PAGE_MARKERS):
            if current:
                pages.append("\n".join(current).strip())
                current = []
            continue  # do not include the marker itself
        current.append(ln)
    if current:
        pages.append("\n".join(current).strip())
    # Fallback: if still empty, single page
    if not pages:
        pages = [text.strip()]
    return pages


def classify_line(raw: str, prev_speaker: str | None) -> tuple[str, str, bool]:
    """
    Return (speaker, content, is_uncertain)
    speaker ∈ {"ai","student","unknown"}
    """
    line = raw.strip()
    if not line:
        return ("unknown", "", False)

    # strip leading bullet markers / numbering
    line = re.sub(r"^[\\s>*-]+", "", line)

    # explicit tags like "AI:" / "Student -"
    tag_match = re.match(r"^(?P<label>[A-Za-z ]{1,20})\\s*[:\\-]\\s*(.*)$", line)
    if tag_match:
        label = tag_match.group("label").strip().lower()
        rest = line[tag_match.end():] if tag_match.end() < len(line) else ""
        if any(label == x.lower() for x in [*AI_LABELS, *[l.lower()+':' for l in AI_LABELS]]):
            return ("ai", rest.strip(), False)
        if any(label == x.lower() for x in [*STUDENT_LABELS, *[l.lower()+':' for l in STUDENT_LABELS]]):
            return ("student", rest.strip(), False)

    # soft tags (single token)
    for lab in AI_LABELS:
        if re.match(fr"^(?i){lab}\\b[:\\-]?", line):
            return ("ai", re.sub(fr"^(?i){lab}\\b[:\\-]?", "", line).strip(), False)
    for lab in STUDENT_LABELS:
        if re.match(fr"^(?i){lab}\\b[:\\-]?", line):
            return ("student", re.sub(fr"^(?i){lab}\\b[:\\-]?", "", line).strip(), False)

    # Q: / A: heuristic
    if re.match(r"^(?i)Q\\s*[:\\-]", line):
        return ("student", re.sub(r"^(?i)Q\\s*[:\\-]", "", line).strip(), True)
    if re.match(r"^(?i)A\\s*[:\\-]", line):
        return ("ai", re.sub(r"^(?i)A\\s*[:\\-]", "", line).strip(), True)

    # fallback to previous speaker if exists
    if prev_speaker in {"ai","student"}:
        return (prev_speaker, line, True)

    return ("unknown", line, True)


def count_cjk_runs(s: str) -> tuple[int, str]:
    """
    Count CJK runs as ceil(len/2) per uninterrupted run.
    Return (count, text_without_cjk)
    """
    count = 0
    out = []
    i = 0
    while i < len(s):
        if CJK_RE.match(s[i]):
            j = i
            while j < len(s) and CJK_RE.match(s[j]):
                j += 1
            run_len = j - i
            count += math.ceil(run_len / 2.0)
            i = j
        else:
            out.append(s[i])
            i += 1
    return count, "".join(out)


def tokenize_mathish(s: str) -> int:
    """
    "Spoken-equivalent" rough count:
    - sequences of letters/digits count as 1 per group (e.g., '3x' -> 1)
    - each operator/symbol in MATH_CHARS counts as 1
    - parentheses/brackets also count as 1 each
    """
    if not MATH_RE.search(s):
        return 0
    # split into tokens: alnum groups OR single math char
    tokens = []
    i = 0
    while i < len(s):
        ch = s[i]
        if re.match(r"[A-Za-z0-9]", ch):
            j = i + 1
            while j < len(s) and re.match(r"[A-Za-z0-9]", s[j]):
                j += 1
            tokens.append(s[i:j])
            i = j
        elif MATH_RE.match(ch):
            tokens.append(ch)
            i += 1
        else:
            i += 1
    return len(tokens)


def tokenize_basic_english(s: str) -> int:
    # URLs / emails: count as 1 each and remove
    urls = len(URL_RE.findall(s))
    s = URL_RE.sub(" ", s)
    emails = len(EMAIL_RE.findall(s))
    s = EMAIL_RE.sub(" ", s)

    # remove punctuation-only tokens; keep words/numbers with apostrophes
    # treat hyphenated as one if alnum on both sides
    # use regex to find word-like tokens
    word_tokens = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?(?:-[A-Za-z0-9]+)?", s)

    return urls + emails + len(word_tokens)


def line_token_count(text: str) -> int:
    if not text:
        return 0
    # quick ignore: pure punctuation
    if not re.search(r"[\\w]", text) and not CJK_RE.search(text):
        return 0

    cjk_count, rest = count_cjk_runs(text)
    math_count = tokenize_mathish(rest)
    # remove math-ish chars so they aren't double counted as words
    rest_wo_math = re.sub(MATH_RE, " ", rest)
    basic = tokenize_basic_english(rest_wo_math)
    return cjk_count + math_count + basic


def screen_file(path: Path, annotate_dir: Path | None):
    raw = load_text(path)
    text = normalize_text(raw)
    pages = split_pages(text)

    ai_total = 0
    st_total = 0
    unknown_total = 0
    page_rows = []
    annotated_lines = []

    for p_index, page in enumerate(pages, 1):
        ai_p = st_p = un_p = 0
        prev = None
        for rawline in page.split("\n"):
            speaker, content, uncertain = classify_line(rawline, prev)
            # Remove common AI preambles (leading phrases only)
            if speaker == "ai":
                for pref in AI_PREAMBLE_PREFIXES:
                    if content.startswith(pref):
                        content = ""  # ignore
                        break
            n = line_token_count(content)

            if speaker == "ai":
                ai_p += n
            elif speaker == "student":
                st_p += n
            else:
                un_p += n

            prev = speaker if speaker != "unknown" else prev

            if annotate_dir is not None:
                tag = "AI" if speaker=="ai" else ("STUDENT" if speaker=="student" else "UNK")
                uflag = "?" if uncertain else ""
                annotated_lines.append(f"[{tag}{uflag}] {content}")

        page_rows.append((p_index, st_p, ai_p, un_p))
        ai_total += ai_p
        st_total += st_p
        unknown_total += un_p

    total = ai_total + st_total
    pct_st = round((st_total / total * 100.0), 1) if total > 0 else 0.0
    status = "ok"
    note = ""

    # flag questionable cases
    if total == 0:
        status = "needs_review"
        note = "zero_total"
    elif unknown_total > 0.1 * (total + unknown_total):
        status = "needs_review"
        note = f"unknown>{unknown_total}"
    elif pct_st == 0.0 or pct_st == 100.0:
        status = "needs_review"
        note = "extreme_pct"

    # write annotation
    if annotate_dir is not None:
        ann_path = annotate_dir / f"{path.stem}__annotated.txt"
        ann_path.write_text("\n".join(annotated_lines), encoding="utf-8")

    return {
        "filename": path.name,
        "pages": page_rows,
        "ai_words": ai_total,
        "student_words": st_total,
        "unknown_words": unknown_total,
        "total": total,
        "pct_student": pct_st,
        "status": status,
        "note": note,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Folder with .txt/.docx transcripts")
    ap.add_argument("--outdir", default="screen_run", help="Output folder")
    ap.add_argument("--annotate", action="store_true", help="Write annotated transcripts")
    ap.add_argument("--force", action="store_true", help="Overwrite outputs if they exist")
    args = ap.parse_args()

    in_dir = Path(args.input).expanduser().resolve()
    out_dir = Path(args.outdir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "annotated").mkdir(exist_ok=True)

    summary_path = out_dir / "summary.csv"
    pages_path = out_dir / "pages.csv"
    log_path = out_dir / "log.txt"

    if summary_path.exists() and not args.force:
        print(f"[abort] {summary_path} exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(2)

    files = sorted([p for p in in_dir.iterdir() if p.suffix.lower() in {".txt",".docx"}])
    if not files:
        print(f"[error] no transcripts found in {in_dir}", file=sys.stderr)
        sys.exit(1)

    with open(summary_path, "w", newline="", encoding="utf-8") as fsum, \
         open(pages_path, "w", newline="", encoding="utf-8") as fpages, \
         open(log_path, "w", encoding="utf-8") as flog:

        sum_writer = csv.DictWriter(fsum, fieldnames=[
            "filename","student_words","ai_words","total","pct_student","unknown_words","status","note"
        ])
        sum_writer.writeheader()

        pages_writer = csv.writer(fpages)
        pages_writer.writerow(["filename","page","student_words","ai_words","unknown_words"])

        flog.write(f"pk_screen.py run at {datetime.now().isoformat()}\n")
        flog.write(f"Input dir: {in_dir}\n\n")

        for i, path in enumerate(files, 1):
            try:
                rec = screen_file(path, (out_dir / "annotated") if args.annotate else None)
                sum_writer.writerow({
                    "filename": rec["filename"],
                    "student_words": rec["student_words"],
                    "ai_words": rec["ai_words"],
                    "total": rec["total"],
                    "pct_student": rec["pct_student"],
                    "unknown_words": rec["unknown_words"],
                    "status": rec["status"],
                    "note": rec["note"],
                })
                for (pg, st, ai, un) in rec["pages"]:
                    pages_writer.writerow([rec["filename"], pg, st, ai, un])
                print(f"[{i}/{len(files)}] {path.name}  →  %Student {rec['pct_student']}  ({rec['status']})")
            except Exception as e:
                print(f"[{i}/{len(files)}] {path.name}  →  ERROR: {type(e).__name__}: {e}")
                flog.write(f"ERROR {path.name}: {type(e).__name__}: {e}\n")

    print("\nDone.")
    print(f"  Summary: {summary_path}")
    print(f"  Pages:   {pages_path}")
    if args.annotate:
        print(f"  Annot:   {out_dir/'annotated'}")

if __name__ == "__main__":
    main()
