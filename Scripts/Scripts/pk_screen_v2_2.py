
#!/usr/bin/env python3
"""
pk_screen_v2_1.py — Phase-1 screener with instruction-block handling and inline "My answer:" split.

Adds:
- Detects/ignores long instruction blocks at the start (e.g., "You are a ... THE ACTIVITY ... STEP 1:")
- Splits inline "My answer: ..." into AI prompt + STUDENT response on the same line
- Slightly broader AI preamble/prefix detection
"""

import argparse, csv, math, re, sys, unicodedata
from pathlib import Path
from datetime import datetime

# Optional .docx support
try:
    import docx  # python-docx
except Exception:
    docx = None
    
# optional model support
try:
    import joblib
except Exception:
    joblib = None
    
# ==== PATCH: preamble detection, tag stripping, word counting ====
import re, math

# Strings that uniquely identify the canned AI prompt/preamble you don't want to count (RB4)
PREAMBLE_PHRASES = [
    "you are a personality-based ai teacher generator",
    "step 1: personality test",
    "internal teacher profile",
    "the activity (to be revealed step by step)",
    "rule reminder:",
    "step 2 follow-up",
    "historical context (brief & structured)",
]

PREAMBLE_RE = re.compile("|".join(map(re.escape, PREAMBLE_PHRASES)), re.IGNORECASE)

# Leading bracket tags in annotated text, e.g. [AI], [STUDENT?], [UNK?]
TAG_RE = re.compile(r'^\s*\[(AI|STUDENT|UNK)(\?)?\]\s*', re.IGNORECASE)

# If a student line begins with "My answer:", drop that prefix before counting
MYANSWER_RE = re.compile(r'^\s*my\s+answer\s*:\s*', re.IGNORECASE)

# Tokenizer: words and simple hyphen/quote joins; ignores brackets/pure punctuation
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-’'][A-Za-z0-9]+)?")

def is_preamble_line(text: str) -> bool:
    return bool(PREAMBLE_RE.search(text or ""))

def strip_leading_tag(text: str):
    """Return (label, uncertain, rest_without_tag) if a leading [AI]/[STUDENT?]/[UNK?] is present."""
    m = TAG_RE.match(text or "")
    if not m:
        return (None, False, text or "")
    label = m.group(1).upper()
    uncertain = bool(m.group(2))
    rest = (text or "")[m.end():]
    return (label, uncertain, rest)

def split_my_answer(text: str) -> str:
    return MYANSWER_RE.sub("", text or "")

def count_words_no_tags(text: str) -> int:
    """Strip tag + 'My answer:' prefix; count words without counting bracket tokens."""
    _lbl, _unc, rest = strip_leading_tag(text or "")
    rest = split_my_answer(rest)
    return len(WORD_RE.findall(rest))
# ==== /PATCH helpers ====

AI_LABELS = ["AI","Assistant","ChatGPT","Teacher","Tutor","Instructor","Bot","System","T","A","GPT","D","DeepSeek"]
STUDENT_LABELS = ["Student","User","You","Learner","S","U","Me","P","Person","Q"]

AI_PERSONA_PREFIXES = [
    "hello! i'm","hello, i'm","hi! i'm","hi, i'm",
    "as an ai","i am your tutor","i'm your tutor","i am the teacher","i'm the teacher",
    "let me explain","i will explain","here is an explanation","here's an explanation",
    "hello! i'm an ai","hello! i'm a","i'm an ai", "i am an ai"
]

# Wide "instructions block" markers (case-insensitive; if these appear before any student content, ignore them)
INSTR_START = [
    r"^\s*you\s+are\s+a\b",
    r"^\s*you\s+are\s+an\b",
    r"^\s*your\s+goal\s+is\b",
    r"^\s*the\s+activity\b",
    r"^\s*step\s*1\s*:\s*personality\s*test\b",
    r"^\s*temporary\s+ai\s+profiler\b",
]
INSTR_START_RE = [re.compile(pat, re.IGNORECASE) for pat in INSTR_START]

# Keywords that indicate actual Taylor series content has begun (not boilerplate)
TAYLOR_CONTENT_KEYWORDS = [
    "taylor polynomial", "taylor series", "brook taylor", "taylor's",
    "maclaurin", "polynomial approximation",
    "1715", "1685",  # Historical dates when Taylor developed the concept
]

AI_PREAMBLE_PREFIXES = [
    "sure","certainly","of course","here is","here's","let's","let's",
    "as an ai","i can help","i can explain","i will","great question",
    "absolutely","happy to","i'd be happy","i'd be happy",
]

URL_RE   = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
EMAIL_RE = re.compile(r"(?i)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b")

MATH_CHARS = "^_+-=*/%<>×÷=()[]{}≈≃≅≡∼∑∏√∞°·•→←≤≥±∫∂≔⟂⊥∥"
MATH_RE = re.compile("[" + re.escape(MATH_CHARS) + "]")

CJK_RE = re.compile("[" "\u3400-\u4DBF" "\u4E00-\u9FFF" "\u3040-\u30FF" "\uAC00-\uD7AF" "]")

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
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\r\n","\n").replace("\r","\n")
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
    m = re.match(r"^\s*\[?(?P<label>[A-Za-z ]{1,20})\]?\s*[:\-]\s*(?P<rest>.*)$", line)
    if not m:
        return None
    return m.group("label").strip(), m.group("rest").strip()

def _is_instruction_line(s: str) -> bool:
    return any(pat.search(s) for pat in INSTR_START_RE)

def _split_my_answer_inline(s: str):
    """If 'my answer:' appears inline, split -> (left, right) else (None, None)."""
    m = re.search(r"(?i)\bmy\s*answer\s*:", s)
    if not m:
        return None, None
    cut = m.end()
    left = s[:m.start()].rstrip(" -*:")
    right = s[cut:].strip()
    return (left if left.strip() else None), (right if right.strip() else None)

def classify_line_initial(raw: str, prev_speaker: str|None, in_student_block: bool) -> tuple[str,str,bool,bool]:
    line = raw.strip()
    if not line:
        return ("unknown","",False,False)

    line_wo = re.sub(r"^[\s>*-]+", "", line)

    # My answer: block header (solo line)
    if re.match(r"(?i)^\s*(my\s+answer|student\s+answer)\s*[:\-]?\s*$", line_wo):
        return ("student","",False,True)

    # Inline "My answer:" split
    left, right = _split_my_answer_inline(line_wo)
    if right is not None:
        # left is AI lead-in (optional), right is student content
        if left is not None:
            return ("ai", left.strip(), True, False), ("student", right.strip(), False, False)

    tag = _explicit_tag(line_wo)
    if tag:
        label, rest = tag
        lab_low = label.lower()
        if lab_low in {"t","a"}:   return ("ai", rest, False, False)
        if lab_low in {"s","u","me"}: return ("student", rest, False, False)
        if lab_low in {x.lower() for x in AI_LABELS}:      return ("ai", rest, False, False)
        if lab_low in {x.lower() for x in STUDENT_LABELS}: return ("student", rest, False, False)

    for pref in AI_PERSONA_PREFIXES:
        if line_wo.lower().startswith(pref):
            return ("ai", line_wo, True, False)

    for lab in AI_LABELS:
        if re.match(fr"(?i)^{re.escape(lab)}\b[:\-]?", line_wo):
            rest = re.sub(fr"(?i)^{re.escape(lab)}\b[:\-]?", "", line_wo).strip()
            return ("ai", rest, False, False)
    for lab in STUDENT_LABELS:
        if re.match(fr"(?i)^{re.escape(lab)}\b[:\-]?", line_wo):
            rest = re.sub(fr"(?i)^{re.escape(lab)}\b[:\-]?", "", line_wo).strip()
            return ("student", rest, False, False)

    if re.match(r"(?i)^Q\s*[:\-]", line_wo):
        return ("student", re.sub(r"(?i)^Q\s*[:\-]", "", line_wo).strip(), True, False)
    if re.match(r"(?i)^A\s*[:\-]", line_wo):
        return ("ai", re.sub(r"(?i)^A\s*[:\-]", "", line_wo).strip(), True, False)

    if in_student_block and line_wo:
        return ("student", line_wo, True, False)

    if prev_speaker in {"ai","student"} and line_wo:
        return (prev_speaker, line_wo, True, False)

    return ("unknown", line_wo, True, False)

def smooth_assign(entries):
    n = len(entries)
    last = None
    for i in range(n):
        if entries[i]["speaker"] in {"ai","student"}:
            last = entries[i]["speaker"]
        elif entries[i]["speaker"] == "unknown" and last:
            entries[i]["speaker"] = last
            entries[i]["uncertain"] = True
    nxt = None
    for i in range(n-1, -1, -1):
        if entries[i]["speaker"] in {"ai","student"}:
            nxt = entries[i]["speaker"]
        elif entries[i]["speaker"] == "unknown" and nxt:
            entries[i]["speaker"] = nxt
            entries[i]["uncertain"] = True
    return entries

def merge_runs(entries):
    merged = []
    for e in entries:
        if isinstance(e, tuple):
            # classify_line_initial may return two tuples when splitting inline "My answer:"
            e = {"speaker": e[0], "text": e[1], "uncertain": e[2] if len(e)>2 else True}
        spk, txt, unc = e["speaker"], e["text"], e["uncertain"]
        if not txt: continue
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

def line_token_count(text: str, simple_mode: bool = False) -> int:
    if not text: return 0
    
    # Simple mode: whitespace-based splitting (matches LibreOffice word count)
    if simple_mode:
        return len(text.split())
    
    # Comprehensive mode: CJK/math/URL tokenization per Appendix B
    if not re.search(r"[\w]", text) and not CJK_RE.search(text):
        return 0
    cjk_count, rest = count_cjk_runs(text)
    math_count = tokenize_mathish(rest)
    rest_wo_math = re.sub(MATH_RE, " ", rest)
    basic = tokenize_basic_english(rest_wo_math)
    return cjk_count + math_count + basic

def detect_boilerplate_end(all_lines, max_lines=100):
    """
    Scan the first max_lines to find where boilerplate ends and Taylor content begins.
    Returns line_number (0-indexed) where actual content starts, or 0 if no boilerplate detected.
    
    Strategy:
    1. Look for personality test/profiler sections
    2. Taylor content starts when we see historical context phrases (1715, 1685, Brook Taylor)
       AFTER the personality test section ends
    3. Don't count student instructions/prompts that mention Taylor
    """
    in_personality_test = False
    personality_end_line = 0
    
    for i, line in enumerate(all_lines[:max_lines]):
        lower = line.lower()
        
        # Detect personality test/profiler section
        if any(marker in lower for marker in [
            "personality test", "personality-based", "ai profiler",
            "internal teacher profile", "teacher profile built",
            "step 1: personality", "step 2: internal"
        ]):
            in_personality_test = True
            personality_end_line = i + 1
            continue
        
        # If we're past the personality test and see historical Taylor content, that's where content starts
        if in_personality_test or personality_end_line > 0:
            if any(phrase in lower for phrase in [
                "1715", "1685", "brook taylor",
                "let's rewind to 1715", "taylor, a british mathematician",
                "rewind to 1715", "early 1700s"
            ]):
                return i  # Content starts at this historical context line
                
    return personality_end_line if personality_end_line > 0 else 0


def detect_instruction_block(lines):
    """
    Returns the index of the first non-instruction line if an instruction block is detected at the top.
    We mark those ignored (do not count) but still annotate as [AI].
    """
    i = 0
    seen_instr = False
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            i = idx + 1
            continue
        if _is_instruction_line(s):
            seen_instr = True
            i = idx + 1
            continue
        # inline "My answer:" means real student content begins
        if re.search(r"(?i)\bmy\s*answer\s*:", s):
            return (i, True) if seen_instr else (0, False)
        # any explicit student label indicates end of instruction block
        if re.match(r"(?i)^\s*(student|s|user|me)\b[:\-]?", s):
            return (i, True) if seen_instr else (0, False)
        # once we hit non-instruction text, stop
        break
    return (i if seen_instr else 0, seen_instr)

def screen_file(path, annotate_dir, units="words", approx=6.0,
                model=None, cls_idx=None, thresh=0.65, uncertain_weight=0.5, 
                simple_words=False, skip_boilerplate=False):
    raw = load_text(path)
    text = normalize_text(raw)
    pages = split_pages(text)
    
    # Skip boilerplate if requested
    boilerplate_lines_skipped = 0
    if skip_boilerplate and pages:
        # Combine all pages to find boilerplate boundary
        all_lines = text.split("\n")
        content_start = detect_boilerplate_end(all_lines)
        if content_start > 0:
            boilerplate_lines_skipped = content_start
            # Recreate text without boilerplate
            text = "\n".join(all_lines[content_start:])
            pages = split_pages(text)

    ai_total = st_total = unk_total = 0
    page_rows = []
    ann_lines_all = []
    
    if skip_boilerplate and boilerplate_lines_skipped > 0:
        ann_lines_all.append(f"[BOILERPLATE SKIPPED: {boilerplate_lines_skipped} lines]")
        ann_lines_all.append("")

    for p_idx, page in enumerate(pages, 1):
        lines = page.split("\n")

        # Detect & ignore a top instruction block on this page
        start_idx, had_instr = detect_instruction_block(lines)
        instr_lines = lines[:start_idx] if had_instr else []

        entries = []
        prev = None
        student_block = False

        # annotate instruction block (ignored from counts)
        if annotate_dir is not None and instr_lines:
            for ln in instr_lines:
                if ln.strip():
                    ann_lines_all.append("[AI][IGNORED] " + ln.strip())
            ann_lines_all.append("")

        # classify remaining lines
        i = start_idx
        while i < len(lines):
            ln = lines[i]
            res = classify_line_initial(ln, prev, student_block)
            # If inline split happened, classify_line_initial returns a tuple-of-tuples pattern. Handle both.
            if isinstance(res, tuple) and len(res)==4 and isinstance(res[0], str):
                spk, content, unc, start_student_block = res
                if start_student_block:
                    student_block = True
                    prev = "student"
                    i += 1
                    continue
                if spk in {"ai","student"}:
                    prev = spk
                    # strip AI preambles at start of line
                    if spk == "ai":
                        for pref in AI_PREAMBLE_PREFIXES:
                            if content.lower().startswith(pref):
                                content = ""
                                break
                entries.append({"speaker": spk, "text": content, "uncertain": unc})
            else:
                # res is actually two tuples from inline split
                ai_part, st_part = res
                # ai_part may be None if no left text
                if ai_part:
                    spk, content, *_ = ai_part
                    entries.append({"speaker": spk, "text": content, "uncertain": True})
                    prev = "ai"
                if st_part:
                    spk, content, *_ = st_part
                    entries.append({"speaker": spk, "text": content, "uncertain": False})
                    prev = "student"
            i += 1

        entries = smooth_assign(entries)
        merged = merge_runs(entries)
        
        # Model relabel: only for unknown or uncertain segments; never override hard labels
        if model is not None:
            for seg in merged:
                if not seg["text"].strip():
                    continue
                if seg["speaker"] == "unknown" or seg["uncertain"]:
                    try:
                        proba = model.predict_proba([seg["text"]])[0]
                        p_ai = proba[cls_idx["AI"]]
                        p_st = proba[cls_idx["STUDENT"]]
                        if max(p_ai, p_st) >= thresh:
                            seg["speaker"] = "student" if p_st >= p_ai else "ai"
                            seg["uncertain"] = False
                    except Exception:
                        pass

        # annotated (post-smoothing)
        if annotate_dir is not None:
            for seg in merged:
                tag = "AI" if seg["speaker"]=="ai" else ("STUDENT" if seg["speaker"]=="student" else "UNK")
                q = "?" if seg["uncertain"] else ""
                ann_lines_all.append(f"[{tag}{q}] {seg['text']}")
            ann_lines_all.append("")

        ai_p = st_p = unk_p = 0
        for seg in merged:
            n = line_token_count(seg["text"], simple_mode=simple_words)
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
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="screen_run")
    ap.add_argument("--annotate", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", help="Path to a joblib model (optional)")
    ap.add_argument("--model-thresh", type=float, default=0.65,
                    help="Min probability to relabel uncertain/UNK (default 0.65)")
    
    ap.add_argument(
        "--units",
        choices=["words", "chars", "both"],
        default="words",
        help="Count words, characters, or both (default: words)"
    )
    
    ap.add_argument(
        "--simple-words",
        action="store_true",
        help="Use simple whitespace word splitting (matches LibreOffice word count, used for manual calibration validation)"
    )

    ap.add_argument(
        "--approx-words-from-chars",
        type=float,
        default=6.0,
        help="If units includes chars, also estimate words as ceil(chars / C). Default C=6.0"
    )
    
    ap.add_argument(
        "--uncertain-weight",
        type=float,
        default=0.5,  # set 0.0 to drop uncertain lines entirely
        help="Weight for [AI?]/[STUDENT?] lines when counting words (0.5 recommended; 0 to ignore)."
    )
    
    ap.add_argument(
        "--skip-boilerplate",
        action="store_true",
        help="Skip initial AI personality test/teacher profile boilerplate before Taylor content begins."
    )
    
    args = ap.parse_args()
    uncertain_weight = float(getattr(args, "uncertain_weight", 0.5))
    approx_c = float(getattr(args, "approx_words_from_chars", 6.0))
    
    model = None
    cls_idx = {}
    if args.model:
        if joblib is None:
            raise SystemExit("joblib not installed. Run: pip3 install joblib")
        model = joblib.load(args.model)
        # figure out label indices
        try:
            classes = list(model.named_steps["clf"].classes_)
        except Exception:
            classes = list(getattr(model, "classes_", []))
        for lab in ("AI", "STUDENT"):
            if lab in classes:
                cls_idx[lab] = classes.index(lab)
        if "AI" not in cls_idx or "STUDENT" not in cls_idx:
            raise SystemExit("Model must have classes_ containing 'AI' and 'STUDENT'.")

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

        flog.write(f"pk_screen_v2_1.py run at {datetime.now().isoformat()}\n")
        flog.write(f"Input dir: {in_dir}\n\n")

        for i, path in enumerate(files, 1):
            try:
                rec = screen_file(
                    path,
                    (out_dir / "annotated") if args.annotate else None,
                    args.units,
                    args.approx_words_from_chars,   # <— now exists
                    model=model, cls_idx=cls_idx, thresh=args.model_thresh, uncertain_weight=uncertain_weight,
                    simple_words=getattr(args, 'simple_words', False),
                    skip_boilerplate=getattr(args, 'skip_boilerplate', False),
                )

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
