#!/usr/bin/env python3
"""
Compare manual counts from Appendix C with automated counts from screen_run_final.
Help identify which transcripts need manual review and which automated counts can be trusted.
"""

import csv
import re
from pathlib import Path

def parse_appendix_c_table():
    """
    Extract the word count data from appendix.tex Table 5.
    Returns dict mapping student_id -> {ai_words, student_words, total, pct_ai, pct_student}
    """
    appendix_path = Path("Manuscript (LaTeX)/appendix.tex")
    
    manual_counts = {}
    in_table = False
    
    with open(appendix_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Start when we see the table data
            if 'P01-G8-S4' in line or in_table:
                in_table = True
                
                # End at bottomrule
                if '\\bottomrule' in line:
                    break
                    
                # Parse data lines: P01-G8-S4 & 3558 & 203 & 3761 & 94.6 & 5.4 \\
                match = re.match(r'(P\d+-G\w+-S\w+)\s+&\s+(\d+)\s+&\s+(\d+)\s+&\s+(\d+)\s+&\s+([\d.]+)\s+&\s+([\d.]+)', line)
                if match:
                    student_id = match.group(1)
                    manual_counts[student_id] = {
                        'ai_words': int(match.group(2)),
                        'student_words': int(match.group(3)),
                        'total': int(match.group(4)),
                        'pct_ai': float(match.group(5)),
                        'pct_student': float(match.group(6))
                    }
    
    return manual_counts

def read_automated_counts():
    """Read the automated counts from screen_run_final/summary.csv"""
    auto_counts = {}
    
    with open('Data Formatted to Analyze/screen_run_final/summary.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract student ID from filename (e.g., P01-G8-S4.txt -> P01-G8-S4)
            filename = row['filename']
            student_id = filename.rsplit('.', 1)[0]  # Remove extension
            
            auto_counts[student_id] = {
                'ai_words': int(row['ai_words']),
                'student_words': int(row['student_words']),
                'total': int(row['total']),
                'pct_student': float(row['pct_student']),
                'unknown_words': int(row['unknown_words']),
                'status': row['status'],
                'note': row['note']
            }
    
    return auto_counts

def compare_counts(manual, automated):
    """Compare manual and automated counts and categorize differences"""
    
    results = {
        'close_match': [],      # Within 10% tolerance
        'moderate_diff': [],    # 10-25% difference
        'large_diff': [],       # >25% difference
        'manual_only': [],      # In manual but not automated
        'auto_only': [],        # In automated but not manual
        'needs_review': []      # Flagged by automated system
    }
    
    all_ids = set(manual.keys()) | set(automated.keys())
    
    for student_id in sorted(all_ids):
        if student_id not in manual:
            results['manual_only'].append(student_id)
            continue
        if student_id not in automated:
            results['auto_only'].append(student_id)
            continue
            
        m = manual[student_id]
        a = automated[student_id]
        
        # Check if flagged for review
        if a['status'] == 'needs_review':
            results['needs_review'].append({
                'id': student_id,
                'manual_pct': m['pct_student'],
                'auto_pct': a['pct_student'],
                'diff': abs(m['pct_student'] - a['pct_student']),
                'note': a['note'],
                'unknown_words': a['unknown_words']
            })
            continue
        
        # Compare percentages
        diff = abs(m['pct_student'] - a['pct_student'])
        
        comparison = {
            'id': student_id,
            'manual_student': m['student_words'],
            'manual_ai': m['ai_words'],
            'manual_pct': m['pct_student'],
            'auto_student': a['student_words'],
            'auto_ai': a['ai_words'],
            'auto_pct': a['pct_student'],
            'diff': diff
        }
        
        if diff <= 10:
            results['close_match'].append(comparison)
        elif diff <= 25:
            results['moderate_diff'].append(comparison)
        else:
            results['large_diff'].append(comparison)
    
    return results

def main():
    print("="*80)
    print("RECONCILING MANUAL AND AUTOMATED WORD COUNTS")
    print("="*80)
    
    print("\n1. Reading manual counts from Appendix C...")
    manual = parse_appendix_c_table()
    print(f"   Found {len(manual)} manual counts")
    
    print("\n2. Reading automated counts from screen_run_final...")
    automated = read_automated_counts()
    print(f"   Found {len(automated)} automated counts")
    
    print("\n3. Comparing counts...")
    results = compare_counts(manual, automated)
    
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    
    print(f"\n✓ Close matches (≤10% diff):     {len(results['close_match'])}")
    print(f"⚠ Moderate differences (10-25%): {len(results['moderate_diff'])}")
    print(f"✗ Large differences (>25%):      {len(results['large_diff'])}")
    print(f"🔍 Flagged for review:            {len(results['needs_review'])}")
    print(f"📋 Only in manual:                {len(results['manual_only'])}")
    print(f"📋 Only in automated:             {len(results['auto_only'])}")
    
    # Write detailed report
    with open('count_reconciliation_report.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Student_ID', 'Manual_%Student', 'Auto_%Student', 
                        'Diff', 'Manual_Student_Words', 'Manual_AI_Words', 
                        'Auto_Student_Words', 'Auto_AI_Words', 'Auto_Unknown_Words', 'Note'])
        
        for item in results['close_match']:
            writer.writerow(['CLOSE_MATCH', item['id'], f"{item['manual_pct']:.1f}", 
                           f"{item['auto_pct']:.1f}", f"{item['diff']:.1f}",
                           item['manual_student'], item['manual_ai'],
                           item['auto_student'], item['auto_ai'], 0, ''])
        
        for item in results['moderate_diff']:
            writer.writerow(['MODERATE_DIFF', item['id'], f"{item['manual_pct']:.1f}", 
                           f"{item['auto_pct']:.1f}", f"{item['diff']:.1f}",
                           item['manual_student'], item['manual_ai'],
                           item['auto_student'], item['auto_ai'], 0, ''])
        
        for item in results['large_diff']:
            writer.writerow(['LARGE_DIFF', item['id'], f"{item['manual_pct']:.1f}", 
                           f"{item['auto_pct']:.1f}", f"{item['diff']:.1f}",
                           item['manual_student'], item['manual_ai'],
                           item['auto_student'], item['auto_ai'], 0, ''])
        
        for item in results['needs_review']:
            writer.writerow(['NEEDS_REVIEW', item['id'], f"{item['manual_pct']:.1f}", 
                           f"{item['auto_pct']:.1f}", f"{item['diff']:.1f}",
                           '', '', '', '', item['unknown_words'], item['note']])
    
    print("\n✓ Detailed report written to: count_reconciliation_report.csv")
    
    # Show some examples of large differences
    if results['large_diff']:
        print("\n" + "="*80)
        print("EXAMPLES OF LARGE DIFFERENCES (first 10):")
        print("="*80)
        for item in results['large_diff'][:10]:
            print(f"\n{item['id']}:")
            print(f"  Manual:    {item['manual_pct']:.1f}% student ({item['manual_student']} student, {item['manual_ai']} AI)")
            print(f"  Automated: {item['auto_pct']:.1f}% student ({item['auto_student']} student, {item['auto_ai']} AI)")
            print(f"  Difference: {item['diff']:.1f} percentage points")
    
    # Show flagged cases
    if results['needs_review']:
        print("\n" + "="*80)
        print("FLAGGED FOR REVIEW (first 10):")
        print("="*80)
        for item in results['needs_review'][:10]:
            print(f"\n{item['id']}: {item['note']}")
            print(f"  Manual:    {item['manual_pct']:.1f}% student")
            print(f"  Automated: {item['auto_pct']:.1f}% student")
            print(f"  Unknown words: {item['unknown_words']}")

if __name__ == '__main__':
    main()
