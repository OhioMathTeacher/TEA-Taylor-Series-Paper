#!/usr/bin/env python3
"""
Test the word counting logic directly on annotated P79-G8-S5 file.
Compare against Eleanor (60.0%, 1826/1219/3045) and Zheng (57.8%, 1884/1375/3259).
"""

import re, math

# Copy the exact counting logic from recount_from_annot.py
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
TAG_RE = re.compile(r'^\s*\[(AI|STUDENT|UNK)(\?)?\]\s*', re.IGNORECASE)
MYANSWER_RE = re.compile(r'^\s*my\s+answer\s*:\s*', re.IGNORECASE)

# Updated to match pk_screen_v2_2.py comprehensive tokenization
URL_RE = re.compile(r'https?://\S+')
EMAIL_RE = re.compile(r'\b[\w.-]+@[\w.-]+\.\w+\b')
CJK_RE = re.compile("[" "\u3400-\u4DBF" "\u4E00-\u9FFF" "\u3040-\u30FF" "\uAC00-\uD7AF" "]")
MATH_CHARS = "^_+-=*/%<>×÷=()[]{}≈≃≅≡∼∑∏√∞°·•→←≤≥±∫∂≔⟂⊥∥"
MATH_RE = re.compile("[" + re.escape(MATH_CHARS) + "]")

def is_preamble_line(text: str) -> bool:
    return bool(PREAMBLE_RE.search(text or ""))

def strip_leading_tag(text: str):
    m = TAG_RE.match(text or "")
    if not m:
        return (None, False, text or "")
    label = m.group(1).upper()
    uncertain = bool(m.group(2))
    rest = (text or "")[m.end():]
    return (label, uncertain, rest)

def split_my_answer(text: str) -> str:
    return MYANSWER_RE.sub("", text or "")

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
    if not text: return 0
    if not re.search(r"[\w]", text) and not CJK_RE.search(text):
        return 0
    cjk_count, rest = count_cjk_runs(text)
    math_count = tokenize_mathish(rest)
    rest_wo_math = re.sub(MATH_RE, " ", rest)
    basic = tokenize_basic_english(rest_wo_math)
    return cjk_count + math_count + basic

def count_annotated_file(filepath):
    """Count words from annotated file with [AI]/[STUDENT] tags."""
    student_words = 0
    ai_words = 0
    unk_words = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n\r')
            
            # Skip preambles
            if is_preamble_line(line):
                continue
            
            # Extract tag and content
            label, uncertain, rest = strip_leading_tag(line)
            if not label:
                continue
            
            # Strip "My answer:" prefix if student
            if label == 'STUDENT':
                rest = split_my_answer(rest)
            
            # Count words using comprehensive tokenizer
            wc = line_token_count(rest)
            
            if label == 'STUDENT':
                student_words += wc
            elif label == 'AI':
                ai_words += wc
            elif label == 'UNK':
                unk_words += wc
    
    total = student_words + ai_words
    pct = (student_words / total * 100) if total > 0 else 0
    
    return {
        'student': student_words,
        'ai': ai_words,
        'total': total,
        'pct': pct,
        'unk': unk_words
    }

import sys
filepath = sys.argv[1] if len(sys.argv) > 1 else 'Data Formatted to Analyze/out_rows-run3/annotations/P79-G8-S5.annotated.txt'

print("="*90)
print(f"TESTING COMPREHENSIVE TOKENIZATION ON {filepath}")
print("="*90)

result = count_annotated_file(filepath)

print(f"\nAutomated count: {result['pct']:.1f}% student  ({result['student']} student, {result['ai']} AI, {result['total']} total)")
print(f"                 (Unknown: {result['unk']} words)")

print("\nManual calibration:")
print(f"  Eleanor: 60.0% student  (1826 student, 1219 AI, 3045 total)")
print(f"  Zheng:   57.8% student  (1884 student, 1375 AI, 3259 total)")

print("\nComparison:")
eleanor_diff = abs(result['pct'] - 60.0)
zheng_diff = abs(result['pct'] - 57.8)
avg_manual = (60.0 + 57.8) / 2
avg_diff = abs(result['pct'] - avg_manual)

print(f"  Difference from Eleanor: {eleanor_diff:.1f} percentage points")
print(f"  Difference from Zheng:   {zheng_diff:.1f} percentage points")
print(f"  Difference from average: {avg_diff:.1f} percentage points")

if avg_diff <= 10:
    print(f"\n✓ WITHIN TOLERANCE (±10pp)")
else:
    print(f"\n✗ OUTSIDE TOLERANCE (>{avg_diff:.1f}pp difference)")
