#!/usr/bin/env python3
import os, re, csv, math, argparse, glob

# ---------- Configurable phrases to hard-ignore (RB4) ----------
PREAMBLE_PHRASES = [
    "you are a personality-based ai teacher generator",
    "step 1: personality test",
    "internal teacher profile",
    "the activity (to be revealed step by step)",
    "rule reminder:",
    "step 2 follow-up",
    "historical context (brief & structured)",
]

# ---------- Compiled regex helpers ----------
PREAMBLE_RE = re.compile("|".join(map(re.escape, PREAMBLE_PHRASES)), re.IGNORECASE)
# Leading bracket tag e.g. [AI], [STUDENT?], [UNK?]
TAG_RE = re.compile(r'^\s*\[(AI|STUDENT|UNK)(\?)?\]\s*', re.IGNORECASE)
# If a student line begins with "My answer:", drop that prefix before counting
MYANSWER_RE = re.compile(r'^\s*my\s+answer\s*:\s*', re.IGNORECASE)
# Tokenizer: ignore brackets/pure punctuation. Counts words like “don't”, “x^2”, “idk”.
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
    """Strip tag + 'My answer:' prefix; count words (never counts bracket tokens)."""
    _lbl, _unc, rest = strip_leading_tag(text or "")
    rest = split_my_answer(rest)
    return len(WORD_RE.findall(rest))

def recount_file(annot_path: str, uncertain_weight: float = 0.5):
    """Recompute totals from a single __annotated.txt file.
       - RB4 preamble ignored regardless of tag
       - [AI?]/[STUDENT?] weighted by uncertain_weight
       - unknown does not enter the %Student denominator
       Returns dict with filename, student_words, ai_words, unknown_words, total, pct_student
    """
    st = ai = unk = 0.0
    with open(annot_path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line:
                continue
            if is_preamble_line(line):
                # hard ignore the canned template/preamble
                continue
            label, tag_uncertain, rest = strip_leading_tag(line)
            n = count_words_no_tags(rest)
            if n == 0:
                continue
            if label == "STUDENT":
                w = 1.0 if not tag_uncertain else uncertain_weight
                st += w * n
            elif label == "AI":
                w = 1.0 if not tag_uncertain else uncertain_weight
                ai += w * n
            else:
                unk += n

    st_i = int(round(st))
    ai_i = int(round(ai))
    unk_i = int(round(unk))
    den = st_i + ai_i
    pct_st = round(100.0 * st_i / den, 1) if den > 0 else ""

    base = os.path.basename(annot_path)
    # turn Pxx-...__annotated.txt -> Pxx-....
    fname = base.replace("__annotated.txt", "")
    return {
        "filename": fname,
        "student_words": st_i,
        "ai_words": ai_i,
        "total": st_i + ai_i,        # unknown excluded from total used for %
        "pct_student": pct_st,
        "unknown_words": unk_i,
        "status": "ok" if den > 0 else "needs_review",
        "note": "" if den > 0 else "no countable AI/Student lines",
    }

def main():
    ap = argparse.ArgumentParser(description="Recount totals from __annotated.txt files with RB4 + uncertain weighting.")
    ap.add_argument("--outdir", required=True, help="Existing run folder that contains annotated/ and summary.csv")
    ap.add_argument("--uncertain-weight", type=float, default=0.5, help="Weight for [AI?]/[STUDENT?] lines (0 to drop).")
    ap.add_argument("--save", default="summary_fixed.csv", help="Output CSV filename (inside --outdir).")
    args = ap.parse_args()

    annot_dir = os.path.join(args.outdir, "annotated")
    if not os.path.isdir(annot_dir):
        raise SystemExit(f"[abort] {annot_dir} not found (expected a folder with __annotated.txt files).")

    files = sorted(glob.glob(os.path.join(annot_dir, "*__annotated.txt")))
    if not files:
        raise SystemExit(f"[abort] No __annotated.txt files in {annot_dir}")

    print(f"Found {len(files)} annotated files. Recounting with uncertain_weight={args.uncertain_weight} …")
    rows = []
    for i, p in enumerate(files, 1):
        try:
            rec = recount_file(p, uncertain_weight=args.uncertain_weight)
            rows.append(rec)
            print(f"[{i}/{len(files)}] {rec['filename']:<30} → %Student {str(rec['pct_student']).rjust(5)}  ({rec['status']})")
        except Exception as e:
            base = os.path.basename(p).replace("__annotated.txt", "")
            rows.append({
                "filename": base, "student_words": "", "ai_words": "",
                "total": "", "pct_student": "", "unknown_words": "",
                "status": "error", "note": f"{type(e).__name__}: {e}"
            })
            print(f"[{i}/{len(files)}] {base:<30} → error: {e}")

    out_csv = os.path.join(args.outdir, args.save)
    with open(out_csv, "w", newline="", encoding="utf-8") as g:
        w = csv.DictWriter(g, fieldnames=["filename","student_words","ai_words","total","pct_student","unknown_words","status","note"])
        w.writeheader()
        for r in rows: w.writerow(r)

    print("\nDone.")
    print(f"  Summary (fixed): {out_csv}")
    print("  Use this for Phase I ranking (sort by pct_student). Unknown does not affect the denominator.")

if __name__ == "__main__":
    main()
