
#!/usr/bin/env python3
"""
compare_screen_runs.py — Compare two or three pk_screen.py runs

Usage:
  python3 compare_screen_runs.py --a screen_run1/summary.csv --b screen_run2/summary.csv [--c screen_run3/summary.csv]

Outputs:
  compare_report.csv — per-file diffs and flags
  prints a small summary to stdout
"""
import argparse, csv, math
from pathlib import Path

def load(path):
    rows = {}
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            rows[row['filename']] = {
                'student': int(row['student_words']),
                'ai': int(row['ai_words']),
                'total': int(row['total']),
                'pct': float(row['pct_student']),
                'status': row.get('status',''),
            }
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--c")
    ap.add_argument("--out", default="compare_report.csv")
    args = ap.parse_args()

    A = load(args.a)
    B = load(args.b)
    C = load(args.c) if args.c else None

    files = sorted(set(A) | set(B) | (set(C) if C else set()))
    outp = Path(args.out)
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = ["filename",
                  "pct_a","pct_b","absdiff_ab",
                  "pct_c","absdiff_ac","absdiff_bc",
                  "counts_equal_ab","counts_equal_ac","counts_equal_bc"]
        w.writerow(header)
        diffs = []
        exact = 0
        for fn in files:
            a = A.get(fn); b = B.get(fn); c = C.get(fn) if C else None
            def cnt(x): 
                return (x['student'], x['ai'], x['total']) if x else None
            eq_ab = cnt(a)==cnt(b) if a and b else False
            eq_ac = cnt(a)==cnt(c) if (a and c) else False
            eq_bc = cnt(b)==cnt(c) if (b and c) else False
            p_a = a['pct'] if a else ""
            p_b = b['pct'] if b else ""
            p_c = c['pct'] if c else ""
            d_ab = abs(p_a-p_b) if (a and b) else ""
            d_ac = abs(p_a-p_c) if (a and c) else ""
            d_bc = abs(p_b-p_c) if (b and c) else ""
            if a and b and eq_ab: exact += 1
            w.writerow([fn, p_a, p_b, d_ab, p_c, d_ac, d_bc, eq_ab, eq_ac, eq_bc])
            if isinstance(d_ab, float):
                diffs.append(d_ab)

    if diffs:
        import statistics as st
        print(f"N files: {len(files)}")
        print(f"Exact counts match (A vs B): {exact}")
        print(f"Mean |Δ%| (A vs B): {st.mean(diffs):.2f}  Median: {st.median(diffs):.2f}  Max: {max(diffs):.2f}")
    print(f"Report: {outp}")

if __name__ == "__main__":
    main()
