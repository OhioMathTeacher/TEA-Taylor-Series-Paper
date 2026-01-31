
# pk_screen — deterministic transcript screening

This tool replaces the LLM-counting stage with a local, repeatable parser that follows the Appendix B rules as closely as possible without model variability.

## Install
- Python 3.10+
- Optional for `.docx`: `python3 -m pip install python-docx`

## Run
```bash
python3 pk_screen.py --input "Data Formatted to Analyze" --outdir screen_run1 --annotate
```
- `--annotate` writes `annotated/*.txt` with `[AI] / [STUDENT] / [UNK]` prefixes for review.
- Rerun with `--force` to overwrite an existing output folder.

Outputs:
- `screen_run1/summary.csv`  → one row per file (`student_words, ai_words, total, pct_student`)
- `screen_run1/pages.csv`    → per-page counts
- `screen_run1/log.txt`      → warnings, errors

## Compare runs
```bash
python3 compare_screen_runs.py --a screen_run1/summary.csv --b screen_run2/summary.csv --out compare_report.csv
```

## Notes on rules
- **CJK**: uninterrupted runs count as `ceil(length/2)`.
- **URLs/emails**: 1 token each.
- **Math**: we count alphanumeric groups and each math operator/symbol individually, approximating a spoken equivalent; parentheses count 1 each.
- **Preambles**: common AI “preamble” phrases at the start of a line are ignored.
- **Attribution**: explicit labels (`AI:` / `Student:`) win; otherwise heuristic; uncertain lines are marked `UNK` and flagged if >10% of tokens.

You can tune lists (labels, preambles) inside `pk_screen.py` if your transcripts use different tags.
