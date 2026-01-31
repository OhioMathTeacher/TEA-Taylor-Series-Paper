
#!/usr/bin/env python3
"""
pk_screen_v2.py — Deterministic transcript screening (Phase 1), improved

Changes vs v1:
- Richer speaker tags: supports [AI]:, T:, S:, U:, "My answer:" blocks, and AI persona intros
- Smoothing: fills UNKNOWN by looking to nearest known speaker, then merges adjacent same-speaker lines
- Annotated output preserves raw text (no math/punct changes), with tags after smoothing
- Keeps UNKNOWN separate; percent uses only AI+Student totals

Outputs:
  outdir/summary.csv, outdir/pages.csv, outdir/annotated/*.txt, outdir/log.txt
"""

import argparse
import csv
import math
import re
import sys
import unicodedata
from pathlib import Path
from datetime import datetime

# Optional .docx
try:
    import docx  # python-docx
except Exception:
    docx = None

# Label hints (case-insensitive)
AI_LABELS = ["AI","Assistant","ChatGPT","Teacher","Tutor","Instructor","Bot","System","T","A","GPT"]
STUDENT_LABELS = ["Student","User","You","Learner","S","U","Me"]

# AI persona intros (line startswith → classify as AI)
AI_PERSONA_PREFIXES = [
    "hello! i'm", "hello, i'm", "hi! i'm", "hi, i'm",
    "as an ai", "i am your tutor", "i'm your tutor", "i am the teacher", "i'm the teacher",
    "let me explain", "i will explain", "here is an explanation", "here's an explanation"
]

# Common AI preambles to ignore from counts (start-of-line only)
AI_PREAMBLE_PREFIXES = [
    "Sure", "Certainly", "Of course", "Here is", "Here’s", "Let's", "Let’s",
    "As an AI", "I can help", "I can explain", "I will", "Great question",
    "Absolutely", "Happy to", "I'd be happy", "I’d be happy"
]

URL_RE   = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
EMAIL_RE = re.compile(r"(?i)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b")

# math-ish character class (escaped safely)
MATH_CHARS = "^_+-=*/%<>×÷=()[]{}≈≃≅≡∼∑∏√∞°·•→←≤≥±∫∂≔⟂⊥∥"
MATH_RE = re.compile("[" + re.escape(MATH_CHARS) + "]")

# CJK
CJK_RE = re.compile(
    "["
    "\u3400-\u4DBF"
    "\u4E00-\u9FFF"
    "\u3040-\u30FF"
    "\uAC00-\uD7AF"
    "]"
)

# Page markers
PAGE_MARKERS = [
    re.compile(r"(?i)^\s*[-=]{2,}\s*Page\s*\d+\s*[-=]{2,}\s*$"),
    re.compile(r"(?i)^\s*Page\s*\d+\s*$"),
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
    # Keep TeX-like content intact: use NFC (not NFKC)
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s

def split_pages(text: str):
    if "\f" in text:
        return [p for p in text.split("\f")]
    lines = text.split("\n")
    pages, cur = [], []
    for ln in lines:
        if any(pat.match(ln) for pat in PAGE_MARKERS):
            if cur:
                pages.append("\n".join(cur).strip())
                cur = []
            continue
        cur.append(ln)
    if cur:
        pages.append("\n".join(cur).strip())
    if not pages:
        pages = [text.strip()]
    return pages

def _explicit_tag(line: str):
    """Return (label, rest) if like [Label]: rest or Label - rest, else None."""
    m = re.match(r"^\s*\[?(?P<label>[A-Za-z ]{1,20})\]?\s*[:\-]\s*(?P<rest>.*)$", line)
    if not m:
        return None
    return m.group("label").strip(), m.group("rest").strip()

def classify_line_initial(raw: str, prev_speaker: str|None, in_student_block: bool) -> tuple[str,str,bool,bool]:
    """
    Initial pass classification.
    Returns: (speaker, content, uncertain, student_block_toggle)
    """
    line = raw.strip()
    if not line:
        return ("unknown","",False,False)

    # bullets/quotes
    line_wo = re.sub(r"^[\s>*-]+", "", line)

    # My answer: start a student block
    if re.match(r"(?i)^\s*(my\s+answer|student\s+answer)\s*[:\-]?\s*$", line_wo):
        return ("student","",False,True)

    # explicit tags
    tag = _explicit_tag(line_wo)
    if tag:
        label, rest = tag
        lab_low = label.lower()
        # normalize one-letter aliases
        if lab_low in {"t","a"}:
            return ("ai", rest, False, False)
        if lab_low in {"s","u","me"}:
            return ("student", rest, False, False)
        if lab_low in {x.lower() for x in AI_LABELS}:
            return ("ai", rest, False, False)
        if lab_low in {x.lower() for x in STUDENT_LABELS}:
            return ("student", rest, False, False)

    # soft tags
    for lab in AI_LABELS:
        if re.match(fr"(?i)^{re.escape(lab)}\b[:\-]?", line_wo):
            rest = re.sub(fr"(?i)^{re.escape(lab)}\b[:\-]?", "", line_wo).strip()
            return ("ai", rest, False, False)
    for lab in STUDENT_LABELS:
        if re.match(fr"(?i)^{re.escape(lab)}\b[:\-]?", line_wo):
            rest = re.sub(fr"(?i)^{re.escape(lab)}\b[:\-]?", "", line_wo).strip()
            return ("student", rest, False, False)

    # Q/A heuristic
    if re.match(r"(?i)^Q\s*[:\-]", line_wo):
        return ("student", re.sub(r"(?i)^Q\s*[:\-]", "", line_wo).strip(), True, False)
    if re.match(r"(?i)^A\s*[:\-]", line_wo):
        return ("ai", re.sub(r"(?i)^A\s*[:\-]", "", line_wo).strip(), True, False)

    # student block continuation
    if in_student_block and line_wo:
        return ("student", line_wo, True, False)

    # AI persona intros
    for pref in AI_PERSONA_PREFIXES:
        if line_wo.lower().startswith(pref):
            return ("ai", line_wo, True, False)

    # fallback
    if prev_speaker in {"ai","student"} and line_wo:
        return (prev_speaker, line_wo, True, False)

    return ("unknown", line_wo, True, False)

def smooth_assign(entries):
    """
    entries: list of dicts with keys: speaker, text, uncertain
    Fills UNKNOWN by looking ahead/back to nearest known speaker.
    """
    n = len(entries)
    # forward fill
    last = None
    for i in range(n):
        if entries[i]["speaker"] in {"ai","student"}:
            last = entries[i]["speaker"]
        elif entries[i]["speaker"] == "unknown" and last:
            entries[i]["speaker"] = last
            entries[i]["uncertain"] = True
    # backward fill
    nxt = None
    for i in range(n-1, -1, -1):
        if entries[i]["speaker"] in {"ai","student"}:
            nxt = entries[i]["speaker"]
        elif entries[i]["speaker"] == "unknown" and nxt:
            entries[i]["speaker"] = nxt
            entries[i]["uncertain"] = True
    return entries

def merge_runs(entries):
    """Merge adjacent same-speaker lines into segments to reduce fragmentation."""
    merged = []
    for e in entries:
        spk, txt, unc = e["speaker"], e["text"], e["uncertain"]
        if not txt:
            continue
        if merged and merged[-1]["speaker"] == spk:
            merged[-1]["text"] += (" " if merged[-1]["text"] else "") + txt
            merged[-1]["uncertain"] = merged[-1]["uncertain"] or unc
        else:
            merged.append({"speaker": spk, "text": txt, "uncertain": unc})
    return merged

def count_cjk_runs(s: str):
    count = 0; out = []; i = 0
    while i < len(s):
        if CJK_RE.match(s[i]):
            j = i
            while j < len(s) and CJK_RE.match(s[j]):
                j += 1
            count += math.ceil((j-i)/2.0)
            i = j
        else:
            out.append(s[i]); i += 1
    return count, "".join(out)

def tokenize_mathish(s: str) -> int:
    if not MATH_RE.search(s):
        return 0
    tokens = []
    i = 0
    while i < len(s):
        ch = s[i]
        if re.match(r"[A-Za-z0-9]", ch):
            j = i+1
            while j < len(s) and re.match(r"[A-Za-z0-9]", s[j]):
                j += 1
            tokens.append(s[i:j]); i = j
        elif MATH_RE.match(ch):
            tokens.append(ch); i += 1
        else:
            i += 1
    return len(tokens)

def tokenize_basic_english(s: str) -> int:
    urls = len(URL_RE.findall(s)); s = URL_RE.sub(" ", s)
    emails = len(EMAIL_RE.findall(s)); s = EMAIL_RE.sub(" ", s)
    word_tokens = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?(?:-[A-Za-z0-9]+)?", s)
    return urls + emails + len(word_tokens)

def line_token_count(text: str) -> int:
    if not text:
        return 0
    if not re.search(r"[\w]", text) and not CJK_RE.search(text):
        return 0
    cjk_count, rest = count_cjk_runs(text)
    math_count = tokenize_mathish(rest)
    rest_wo_math = re.sub(MATH_RE, " ", rest)  # don't double-count math symbols
    basic = tokenize_basic_english(rest_wo_math)
    return cjk_count + math_count + basic

def screen_file(path: Path, annotate_dir: Path|None):
    raw = load_text(path)
    text = normalize_text(raw)
    pages = split_pages(text)

    ai_total = st_total = unk_total = 0
    page_rows = []
    ann_lines_all = []

    for p_idx, page in enumerate(pages, 1):
        lines = page.split("\n")
        entries = []
        prev = None
        student_block = False
        for ln in lines:
            spk, content, unc, start_student_block = classify_line_initial(ln, prev, student_block)
            if start_student_block:
                student_block = True
                prev = "student"
                continue  # the marker line itself carries no content
            if spk in {"ai","student"}:
                prev = spk
                # strip AI preambles at start
                if spk == "ai":
                    for pref in AI_PREAMBLE_PREFIXES:
                        if content.startswith(pref):
                            content = ""  # ignore the whole line content
                            break
            entries.append({"speaker": spk, "text": content, "uncertain": unc})
        # smoothing and merging
        entries = smooth_assign(entries)
        merged = merge_runs(entries)

        # annotate (per merged segment for readability)
        if annotate_dir is not None:
            for seg in merged:
                tag = "AI" if seg["speaker"]=="ai" else ("STUDENT" if seg["speaker"]=="student" else "UNK")
                q = "?" if seg["uncertain"] else ""
                ann_lines_all.append(f"[{tag}{q}] {seg['text']}")
            ann_lines_all.append("")  # blank between pages

        # count tokens
        ai_p = st_p = unk_p = 0
        for seg in merged:
            n = line_token_count(seg["text"])
            if seg["speaker"] == "ai":
                ai_p += n
            elif seg["speaker"] == "student":
                st_p += n
            else:
                unk_p += n

        page_rows.append((p_idx, st_p, ai_p, unk_p))
        ai_total += ai_p; st_total += st_p; unk_total += unk_p

    total = ai_total + st_total
    pct_st = round((st_total / total * 100.0), 1) if total > 0 else 0.0
    status = "ok"; note = ""
    if total == 0:
        status, note = "needs_review", "zero_total"
    elif unk_total > 0.1 * (total + unk_total):
        status, note = "needs_review", f"unknown>{unk_total}"
    elif pct_st in (0.0, 100.0):
        status, note = "needs_review", "extreme_pct"

    if annotate_dir is not None:
        ann_path = annotate_dir / f"{path.stem}__annotated.txt"
        ann_path.write_text("\n".join(ann_lines_all), encoding="utf-8")

    return {
        "filename": path.name,
        "pages": page_rows,
        "ai_words": ai_total,
        "student_words": st_total,
        "unknown_words": unk_total,
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

        flog.write(f"pk_screen_v2.py run at {datetime.now().isoformat()}\n")
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
