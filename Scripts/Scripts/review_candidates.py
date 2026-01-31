#!/usr/bin/env python3
"""
Interactive tool to review middle-range transcripts and flag noteworthy cases.

Displays first ~30 lines of each transcript to help identify:
- GenAI errors or hallucinations
- Creative detours or unexpected approaches
- Language-switching
- Interesting conceptual moves
- Technical difficulties

Usage:
  python3 review_candidates.py
"""

import csv
from pathlib import Path
import sys

def load_candidates():
    """Load middle-range candidates from Phase I results."""
    with open('../simple_mode_final_127/summary.csv', 'r') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]
    
    # Filter valid cases
    valid = [row for row in data 
             if 10.0 < float(row['pct_student']) < 100.0]
    
    # Sort and exclude top/bottom 10
    sorted_valid = sorted(valid, key=lambda x: float(x['pct_student']), reverse=True)
    middle = sorted_valid[10:-10]
    
    # Sort by word count for review
    return sorted(middle, key=lambda x: int(x['total']), reverse=True)


def preview_transcript(filename, lines=35):
    """Show preview of transcript file."""
    base_name = filename.replace('.docx', '.txt')
    path = Path('../Data Formatted to Analyze') / base_name
    
    if not path.exists():
        return f"File not found: {path}", 0
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            preview = ''.join(content[:lines])
            total_lines = len(content)
            return preview, total_lines
    except Exception as e:
        return f"Error reading file: {e}", 0


def main():
    candidates = load_candidates()
    noteworthy = []
    
    print("="*70)
    print("NOTEWORTHY CASE IDENTIFICATION TOOL")
    print("="*70)
    print("\nReviewing middle-range transcripts for:")
    print("  - GenAI errors or hallucinations")
    print("  - Creative detours or unexpected approaches")
    print("  - Language-switching")
    print("  - Interesting conceptual moves or failures")
    print("  - Technical difficulties revealing limitations\n")
    
    print(f"Total candidates: {len(candidates)}\n")
    
    for i, row in enumerate(candidates, 1):
        filename = row['filename']
        transcript_id = filename.replace('.txt', '').replace('.docx', '')
        pct = row['pct_student']
        total = row['total']
        
        print("\n" + "="*70)
        print(f"[{i}/{len(candidates)}] {transcript_id}")
        print(f"Student Talk: {pct}% | Total Words: {total}")
        print("="*70)
        
        preview, total_lines = preview_transcript(filename)
        
        if isinstance(preview, str) and "Error" in preview:
            print(preview)
            continue
        
        print(preview)
        print(f"\n[Showing first 35 of {total_lines} lines]")
        
        while True:
            response = input("\n(n)oteworthy, (s)kip, (m)ore lines, (q)uit? ").lower().strip()
            
            if response == 'n':
                reason = input("  Reason (genai-error/creative-detour/language-switch/other): ")
                noteworthy.append({
                    'id': transcript_id,
                    'filename': filename,
                    'pct_student': pct,
                    'total': total,
                    'reason': reason
                })
                print(f"  ✓ {transcript_id} marked as noteworthy ({reason})")
                break
            elif response == 's':
                break
            elif response == 'm':
                more_preview, _ = preview_transcript(filename, lines=70)
                print("\n" + more_preview)
                print(f"\n[Showing first 70 of {total_lines} lines]")
            elif response == 'q':
                print("\n\nSaving and exiting...")
                save_results(noteworthy)
                return
            else:
                print("  Invalid input. Use n/s/m/q")
    
    print("\n\nReview complete!")
    save_results(noteworthy)


def save_results(noteworthy):
    """Save noteworthy selections."""
    if not noteworthy:
        print("No noteworthy cases selected.")
        return
    
    output_path = Path('noteworthy_candidates.csv')
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['id', 'filename', 'pct_student', 'total', 'reason']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(noteworthy)
    
    print(f"\n{len(noteworthy)} noteworthy cases saved to: {output_path}")
    print("\nSummary:")
    for item in noteworthy:
        print(f"  - {item['id']:15} ({item['pct_student']:>5}%, {item['total']:>4} words) - {item['reason']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
