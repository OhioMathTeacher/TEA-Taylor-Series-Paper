#!/usr/bin/env python3
"""
Fix reversed speaker attribution in annotated files and recount.
The automated annotation got AI/Student backwards - this flips them.
"""

import re, math, sys

# Counting logic (same as before)
URL_RE = re.compile(r'https?://\S+')
EMAIL_RE = re.compile(r'\b[\w.-]+@[\w.-]+\.\w+\b')
CJK_RE = re.compile("[" "\u3400-\u4DBF" "\u4E00-\u9FFF" "\u3040-\u30FF" "\uAC00-\uD7AF" "]")
MATH_CHARS = "^_+-=*/%<>×÷=()[]{}≈≃≅≡∼∑∏√∞°·•→←≤≥±∫∂≔⟂⊥∥"
MATH_RE = re.compile("[" + re.escape(MATH_CHARS) + "]")
TAG_RE = re.compile(r'^\[([A-Z]+)\]\s*', re.IGNORECASE)
PREAMBLE_PHRASES = [
    "you are a personality-based ai teacher generator",
    "step 1: personality test",
    "internal teacher profile",
    "the activity (to be revealed step by step)",
    "rule reminder:",
    "step 2 follow-up",
]
PREAMBLE_RE = re.compile("|".join(map(re.escape, PREAMBLE_PHRASES)), re.IGNORECASE)

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

def count_with_flipped_tags(filepath):
    """Count words with AI/Student tags FLIPPED."""
    student_words = 0
    ai_words = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n\r')
            
            # Skip preambles
            if PREAMBLE_RE.search(line):
                continue
            
            # Extract tag
            m = TAG_RE.match(line)
            if not m:
                continue
            
            orig_label = m.group(1).upper()
            rest = line[m.end():]
            
            # FLIP the tags
            if orig_label == 'STUDENT':
                flipped_label = 'AI'
            elif orig_label == 'AI':
                flipped_label = 'STUDENT'
            else:
                continue  # Skip UNK
            
            # Count words
            wc = line_token_count(rest)
            
            if flipped_label == 'STUDENT':
                student_words += wc
            elif flipped_label == 'AI':
                ai_words += wc
    
    total = student_words + ai_words
    pct = (student_words / total * 100) if total > 0 else 0
    
    return {
        'student': student_words,
        'ai': ai_words,
        'total': total,
        'pct': pct
    }

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'Data Formatted to Analyze/out_rows-run3/annotations/P79-G8-S5.annotated.txt'
    
    # Manual calibration data for different files
    MANUAL_DATA = {
        'P79-G8-S5': [
            ('Eleanor', 60.0, 1826, 1219, 3045),
            ('Zheng', 57.8, 1884, 1375, 3259),
        ],
        'P100-G12-S4': [
            ('Zheng', 4.0, 68, 1617, 1685),
        ],
        'P21-G5-S5': [
            ('Zheng', 15.8, 377, 2006, 2383),
        ],
    }
    
    # Detect which file we're processing
    import os
    basename = os.path.basename(filepath).replace('.annotated.txt', '')
    
    print("="*90)
    print(f"COUNTING WITH FLIPPED TAGS: {basename}")
    print("="*90)
    
    result = count_with_flipped_tags(filepath)
    
    print(f"\nAutomated (FLIPPED): {result['pct']:.1f}% student  ({result['student']} student, {result['ai']} AI, {result['total']} total)")
    
    # Show manual counts for this file
    if basename in MANUAL_DATA:
        print("\nManual calibration:")
        manual_pcts = []
        for researcher, pct, s, a, t in MANUAL_DATA[basename]:
            print(f"  {researcher:10}: {pct:5.1f}% student  ({s} student, {a} AI, {t} total)")
            manual_pcts.append(pct)
        
        avg_manual = sum(manual_pcts) / len(manual_pcts)
        diff = abs(result['pct'] - avg_manual)
        
        print(f"\nDifference from manual average: {diff:.1f} percentage points")
        
        if diff <= 10:
            print(f"✓ WITHIN TOLERANCE (±10pp)")
        else:
            print(f"✗ OUTSIDE TOLERANCE")
    else:
        print(f"\nNo manual calibration data for {basename}")
