#!/usr/bin/env python3
"""
Select 30 anchor transcripts for Phase II PK-WAP analysis.

Selects:
- 10 transcripts with highest % student talk
- 10 transcripts with lowest % student talk (excluding <10%)
- 10 "noteworthy" transcripts (to be manually flagged or selected)

Reads from Phase I output (simple_mode_final_127/summary.csv)
and generates a selection list.

Usage:
  python3 select_anchor_transcripts.py --input simple_mode_final_127/summary.csv --output anchor_selection.csv
  python3 select_anchor_transcripts.py --noteworthy P03,P08,P15  # Add specific noteworthy cases
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict


def load_phase1_results(csv_path: Path) -> List[Dict]:
    """Load Phase I summary.csv results."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Phase I results not found: {csv_path}")
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def filter_valid_transcripts(data: List[Dict], min_student_pct: float = 10.0) -> List[Dict]:
    """
    Filter out transcripts with <10% student talk (insufficient for PK-WAP).
    Also filter out any with 0% or 100% (likely parsing errors).
    """
    valid = []
    for row in data:
        pct = float(row['pct_student'])
        
        # Skip extreme values
        if pct == 0.0 or pct == 100.0:
            continue
        
        # Skip very low student contribution
        if pct < min_student_pct:
            continue
        
        valid.append(row)
    
    return valid


def select_high_talk(data: List[Dict], n: int = 10) -> List[Dict]:
    """Select n transcripts with highest % student talk."""
    sorted_data = sorted(data, key=lambda x: float(x['pct_student']), reverse=True)
    return sorted_data[:n]


def select_low_talk(data: List[Dict], n: int = 10, exclude_high: List[Dict] = None) -> List[Dict]:
    """
    Select n transcripts with lowest % student talk (but still >10%).
    Exclude any already in high_talk list.
    """
    if exclude_high:
        exclude_ids = {row['filename'] for row in exclude_high}
        data = [row for row in data if row['filename'] not in exclude_ids]
    
    sorted_data = sorted(data, key=lambda x: float(x['pct_student']))
    return sorted_data[:n]


def select_noteworthy(
    data: List[Dict],
    noteworthy_ids: List[str] = None,
    exclude: List[Dict] = None,
    n: int = 10
) -> List[Dict]:
    """
    Select noteworthy transcripts.
    
    If noteworthy_ids provided, use those.
    Otherwise, use heuristics:
    - Large word counts (very engaged)
    - Moderate % student talk (balanced dialogue)
    - Not already in high/low lists
    """
    if exclude:
        exclude_ids = {row['filename'] for row in exclude}
        available = [row for row in data if row['filename'] not in exclude_ids]
    else:
        available = data
    
    # If specific IDs provided, return those
    if noteworthy_ids:
        selected = []
        for row in available:
            transcript_id = row['filename'].replace('.txt', '').replace('.docx', '')
            if transcript_id in noteworthy_ids:
                selected.append(row)
        return selected[:n]
    
    # Otherwise, use heuristics for balanced, substantive dialogues
    # Sort by total words (engagement) and pick from middle % student talk range
    filtered = [
        row for row in available
        if 25.0 <= float(row['pct_student']) <= 75.0  # Balanced dialogue
    ]
    
    # Sort by total words descending
    sorted_data = sorted(filtered, key=lambda x: int(x['total']), reverse=True)
    
    return sorted_data[:n]


def save_selection(
    high_talk: List[Dict],
    low_talk: List[Dict],
    noteworthy: List[Dict],
    output_path: Path
):
    """Save the selected 30 anchor transcripts to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['category', 'filename', 'student_words', 'ai_words', 'total', 'pct_student']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write high talk
        for row in high_talk:
            writer.writerow({
                'category': 'high_talk',
                **{k: row[k] for k in fieldnames[1:]}
            })
        
        # Write low talk
        for row in low_talk:
            writer.writerow({
                'category': 'low_talk',
                **{k: row[k] for k in fieldnames[1:]}
            })
        
        # Write noteworthy
        for row in noteworthy:
            writer.writerow({
                'category': 'noteworthy',
                **{k: row[k] for k in fieldnames[1:]}
            })
    
    print(f"Selection saved to: {output_path}")


def print_summary(high_talk, low_talk, noteworthy):
    """Print summary of selected transcripts."""
    print("\n" + "="*60)
    print("ANCHOR TRANSCRIPT SELECTION SUMMARY")
    print("="*60)
    
    print("\nHIGH STUDENT TALK (10):")
    for i, row in enumerate(high_talk, 1):
        transcript_id = row['filename'].replace('.txt', '').replace('.docx', '')
        print(f"  {i:2}. {transcript_id:15} - {row['pct_student']:>5}% student ({row['total']:>5} total words)")
    
    print("\nLOW STUDENT TALK (10):")
    for i, row in enumerate(low_talk, 1):
        transcript_id = row['filename'].replace('.txt', '').replace('.docx', '')
        print(f"  {i:2}. {transcript_id:15} - {row['pct_student']:>5}% student ({row['total']:>5} total words)")
    
    print("\nNOTEWORTHY CASES (10):")
    for i, row in enumerate(noteworthy, 1):
        transcript_id = row['filename'].replace('.txt', '').replace('.docx', '')
        print(f"  {i:2}. {transcript_id:15} - {row['pct_student']:>5}% student ({row['total']:>5} total words)")
    
    print("\n" + "="*60)
    print(f"TOTAL: {len(high_talk) + len(low_talk) + len(noteworthy)} anchor transcripts selected")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Select 30 anchor transcripts for Phase II PK-WAP analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("simple_mode_final_127/summary.csv"),
        help="Phase I summary.csv file (default: simple_mode_final_127/summary.csv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("anchor_selection.csv"),
        help="Output file for selected transcripts (default: anchor_selection.csv)"
    )
    parser.add_argument(
        "--noteworthy",
        type=str,
        help="Comma-separated list of noteworthy transcript IDs (e.g., P03,P08,P15)"
    )
    parser.add_argument(
        "--min-student",
        type=float,
        default=10.0,
        help="Minimum %% student talk to be considered valid (default: 10.0)"
    )
    
    args = parser.parse_args()
    
    # Load Phase I results
    print(f"Loading Phase I results from: {args.input}")
    data = load_phase1_results(args.input)
    print(f"  Loaded {len(data)} transcripts")
    
    # Filter valid transcripts
    valid_data = filter_valid_transcripts(data, args.min_student)
    excluded = len(data) - len(valid_data)
    print(f"  Filtered to {len(valid_data)} valid transcripts (excluded {excluded} with <{args.min_student}% or extreme values)")
    
    # Select high talk
    high_talk = select_high_talk(valid_data, n=10)
    
    # Select low talk (excluding high talk)
    low_talk = select_low_talk(valid_data, n=10, exclude_high=high_talk)
    
    # Parse noteworthy IDs if provided
    noteworthy_ids = None
    if args.noteworthy:
        noteworthy_ids = [id.strip() for id in args.noteworthy.split(',')]
        print(f"  Using manual noteworthy list: {noteworthy_ids}")
    
    # Select noteworthy (excluding high and low)
    noteworthy = select_noteworthy(
        valid_data,
        noteworthy_ids=noteworthy_ids,
        exclude=high_talk + low_talk,
        n=10
    )
    
    # Save and print
    save_selection(high_talk, low_talk, noteworthy, args.output)
    print_summary(high_talk, low_talk, noteworthy)
    
    # Generate file list for batch processing
    filelist_path = args.output.parent / "anchor_transcripts.txt"
    with open(filelist_path, 'w') as f:
        for row in high_talk + low_talk + noteworthy:
            f.write(row['filename'] + '\n')
    
    print(f"\nFile list saved to: {filelist_path}")
    print(f"Use this with pkwap_analyzer.py for batch processing")


if __name__ == "__main__":
    main()
