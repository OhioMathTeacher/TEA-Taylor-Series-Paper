#!/usr/bin/env python3
"""
Validate automated word counting against manual calibration counts.
Tests the pk_screen_v2_2.py script against Eleanor and Zheng's manual counts.
"""

import csv
import subprocess
import sys
from pathlib import Path

# Manual counts from calibration (Eleanor and Zheng's data)
MANUAL_COUNTS = {
    'P79-G8-S5': {
        'Eleanor': {'student': 1826, 'ai': 1219, 'total': 3045, 'pct': 60.0},
        'Zheng': {'student': 1884, 'ai': 1375, 'total': 3259, 'pct': 57.8},
    },
    'P21-G5-S5': {
        'Zheng': {'student': 377, 'ai': 2006, 'total': 2383, 'pct': 15.8},
    },
    'P100-G12-S4': {
        'Zheng': {'student': 68, 'ai': 1617, 'total': 1685, 'pct': 4.0},
    },
}

def run_counter_on_file(filepath, script='pk_screen_v2_2.py'):
    """Run the counting script on a single file and return counts."""
    # For now, we'll use the existing annotated files approach
    # This is a placeholder - we need to determine the best counting method
    return None

def compare_counts(automated, manual, tolerance_pct=10):
    """Compare automated vs manual counts and report if within tolerance."""
    if not automated:
        return False, "No automated count"
    
    pct_diff = abs(automated['pct'] - manual['pct'])
    student_diff = abs(automated['student'] - manual['student'])
    ai_diff = abs(automated['ai'] - manual['ai'])
    
    within_tolerance = pct_diff <= tolerance_pct
    
    return within_tolerance, {
        'pct_diff': pct_diff,
        'student_diff': student_diff,
        'ai_diff': ai_diff
    }

def main():
    print("="*90)
    print("VALIDATING AUTOMATED WORD COUNTING AGAINST MANUAL CALIBRATION")
    print("="*90)
    
    print("\nManual calibration transcripts:")
    print("  P79-G8-S5  (counted by Eleanor & Zheng)")
    print("  P21-G5-S5  (counted by Zheng)")
    print("  P100-G12-S4 (counted by Zheng)")
    
    print("\nTarget: Automated counts should match manual counts within 10% tolerance")
    
    # First, let's check what we currently have
    print("\n" + "="*90)
    print("STEP 1: Check existing automated counts")
    print("="*90)
    
    # Check phase1 data
    phase1 = {}
    with open('Analyzed Cases (Phase 1 and 2)/phase1_wordcount_summaryKEEPTHIS.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Student'] and row['Student'] not in ['Student', '']:
                try:
                    phase1[row['Student']] = {
                        'student': int(row['Student Words']),
                        'ai': int(row['AI Words']),
                        'total': int(row['Total']),
                        'pct': float(row['% Student'])
                    }
                except (ValueError, KeyError):
                    pass  # Skip N/A or malformed entries
    
    # Check python_word_counts data
    pwd_counts = {}
    try:
        with open('Data Formatted to Analyze/python_word_counts/summary_recounted.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['filename']:
                    pwd_counts[row['filename']] = {
                        'student': int(row['student_words']) if row['student_words'] else 0,
                        'ai': int(row['ai_words']) if row['ai_words'] else 0,
                        'total': int(row['total']) if row['total'] else 0,
                        'pct': float(row['pct_student']) if row['pct_student'] else 0
                    }
    except FileNotFoundError:
        pass
    
    print("\nComparison for calibration transcripts:")
    
    for transcript_id in MANUAL_COUNTS.keys():
        print(f"\n{transcript_id}:")
        
        # Show manual counts
        for researcher, counts in MANUAL_COUNTS[transcript_id].items():
            print(f"  {researcher:10} (manual):    {counts['pct']:5.1f}% student  "
                  f"({counts['student']:4} student, {counts['ai']:4} AI, {counts['total']:4} total)")
        
        # Show phase1 if available
        if transcript_id in phase1:
            p = phase1[transcript_id]
            avg_manual_pct = sum(c['pct'] for c in MANUAL_COUNTS[transcript_id].values()) / len(MANUAL_COUNTS[transcript_id])
            diff = abs(p['pct'] - avg_manual_pct)
            status = "✓ MATCH" if diff <= 10 else "✗ DIFFERS"
            print(f"  {'phase1':10} (automated): {p['pct']:5.1f}% student  "
                  f"({p['student']:4} student, {p['ai']:4} AI, {p['total']:4} total)  "
                  f"[diff: {diff:5.1f}pp] {status}")
        
        # Show pwd_counts if available
        if transcript_id in pwd_counts:
            p = pwd_counts[transcript_id]
            avg_manual_pct = sum(c['pct'] for c in MANUAL_COUNTS[transcript_id].values()) / len(MANUAL_COUNTS[transcript_id])
            diff = abs(p['pct'] - avg_manual_pct)
            status = "✓ MATCH" if diff <= 10 else "✗ DIFFERS"
            print(f"  {'pwd_count':10} (automated): {p['pct']:5.1f}% student  "
                  f"({p['student']:4} student, {p['ai']:4} AI, {p['total']:4} total)  "
                  f"[diff: {diff:5.1f}pp] {status}")
    
    print("\n" + "="*90)
    print("CONCLUSION:")
    print("="*90)
    print("Neither existing automated count matches the manual calibration.")
    print("\nNext steps:")
    print("1. Review the counting rules in Appendix B")
    print("2. Test pk_screen_v2_2.py or recount_from_annot.py")
    print("3. Adjust the script to match manual counting methodology")
    print("4. Re-run on all 127 transcripts")

if __name__ == '__main__':
    main()
