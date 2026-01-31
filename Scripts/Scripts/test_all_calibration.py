#!/usr/bin/env python3
"""
Test all 5 manual calibration files to determine which need tag flipping.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from test_flipped_count import count_with_flipped_tags, line_token_count, TAG_RE, PREAMBLE_RE

# Manual calibration data
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
    'P106-GX-SX': [
        ('Eleanor', 24.6, 472, 1446, 1918),
        ('Zheng', 21.4, 382, 1402, 1784),
    ],
    'P76-GX-SX': [
        ('Eleanor', 22.9, 531, 1785, 2316),
        ('Zheng', 18.5, 381, 1682, 2063),
    ],
}

def count_without_flipping(filepath):
    """Count with original tags (no flip)."""
    student_words = 0
    ai_words = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n\r')
            
            if PREAMBLE_RE.search(line):
                continue
            
            m = TAG_RE.match(line)
            if not m:
                continue
            
            label = m.group(1).upper()
            rest = line[m.end():]
            
            if label not in ['AI', 'STUDENT']:
                continue
            
            wc = line_token_count(rest)
            
            if label == 'STUDENT':
                student_words += wc
            elif label == 'AI':
                ai_words += wc
    
    total = student_words + ai_words
    pct = (student_words / total * 100) if total > 0 else 0
    
    return {'student': student_words, 'ai': ai_words, 'total': total, 'pct': pct}

def test_file(basename):
    filepath = f"Data Formatted to Analyze/out_rows-run3/annotations/{basename}.annotated.txt"
    
    if not os.path.exists(filepath):
        print(f"\n{basename}: MISSING annotated file")
        return
    
    if os.path.getsize(filepath) == 0:
        print(f"\n{basename}: EMPTY annotated file (0 bytes)")
        return
    
    print(f"\n{'='*90}")
    print(f"{basename}")
    print('='*90)
    
    # Get manual average
    manual_pcts = [pct for _, pct, _, _, _ in MANUAL_DATA[basename]]
    avg_manual = sum(manual_pcts) / len(manual_pcts)
    
    # Test original tags
    original = count_without_flipping(filepath)
    orig_diff = abs(original['pct'] - avg_manual)
    
    # Test flipped tags
    flipped = count_with_flipped_tags(filepath)
    flip_diff = abs(flipped['pct'] - avg_manual)
    
    # Show manual
    print("\nManual calibration:")
    for researcher, pct, s, a, t in MANUAL_DATA[basename]:
        print(f"  {researcher:10}: {pct:5.1f}% student  ({s:4} student, {a:4} AI, {t:4} total)")
    print(f"  {'Average':10}: {avg_manual:5.1f}%")
    
    # Show automated
    print("\nAutomated counts:")
    print(f"  Original:   {original['pct']:5.1f}% student  ({original['student']:4} student, {original['ai']:4} AI, {original['total']:4} total)  [diff: {orig_diff:5.1f}pp]")
    print(f"  Flipped:    {flipped['pct']:5.1f}% student  ({flipped['student']:4} student, {flipped['ai']:4} AI, {flipped['total']:4} total)  [diff: {flip_diff:5.1f}pp]")
    
    # Determine which is better
    if orig_diff < flip_diff:
        status = "✓ USE ORIGINAL TAGS"
        tolerance = "✓ WITHIN" if orig_diff <= 10 else "✗ OUTSIDE"
    else:
        status = "✓ USE FLIPPED TAGS"
        tolerance = "✓ WITHIN" if flip_diff <= 10 else "✗ OUTSIDE"
    
    print(f"\nRecommendation: {status}")
    print(f"Tolerance: {tolerance} 10pp threshold (best diff: {min(orig_diff, flip_diff):.1f}pp)")

if __name__ == '__main__':
    print("="*90)
    print("TESTING ALL 5 MANUAL CALIBRATION FILES")
    print("="*90)
    
    for basename in ['P79-G8-S5', 'P21-G5-S5', 'P100-G12-S4', 'P106-GX-SX', 'P76-GX-SX']:
        test_file(basename)
    
    print("\n" + "="*90)
    print("SUMMARY")
    print("="*90)
    print("Next step: Determine if pattern exists (e.g., all conversation transcripts reversed)")
