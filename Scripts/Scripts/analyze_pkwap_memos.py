#!/usr/bin/env python3
"""
Analyze all PK-WAP memos to extract key findings.

Extracts structured data from each memo including:
- Highest PK level reached
- Number of recursive movements
- Agentic moves
- Notable features
- Key quotes
"""

import re
from pathlib import Path
import json

def extract_pk_level(memo_text):
    """Extract the highest PK level reached."""
    # Look for "Highest PK Level: X" pattern
    match = re.search(r'Highest PK Level:\s*(\d+|[IV]+)\s*[–-]\s*([^\n]+)', memo_text, re.IGNORECASE)
    if match:
        level = match.group(1)
        name = match.group(2).strip()
        return f"{level} - {name}"
    
    # Alternative pattern: look for level names in context
    levels = {
        'Inventising': 8,
        'Structuring': 7,
        'Observing': 6,
        'Formalizing': 5,
        'Property Noticing': 4,
        'Image Making': 3,
        'Image Having': 2,
        'Primitive Knowing': 1
    }
    
    for level_name, level_num in levels.items():
        if level_name in memo_text:
            return f"{level_num} - {level_name}"
    
    return "Unknown"

def extract_recursions(memo_text):
    """Extract number of recursive movements/fold-backs."""
    # Look for "Number of Recursions" or similar
    match = re.search(r'(?:Number of )?Recursions?[:\s]+(\d+)', memo_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Count mentions of "fold-back" or "recursive"
    foldbacks = len(re.findall(r'\bfold-?back\b', memo_text, re.IGNORECASE))
    recursives = len(re.findall(r'\brecursive\s+movement\b', memo_text, re.IGNORECASE))
    
    return max(foldbacks, recursives) if (foldbacks or recursives) else 0

def extract_agentic_moves(memo_text):
    """Extract descriptions of agentic moves."""
    agentic = []
    
    # Look for agentic moves section
    agentic_section = re.search(r'Agentic Moves?:?\s*\n(.*?)(?:\n\n|\n#|\Z)', memo_text, re.DOTALL | re.IGNORECASE)
    if agentic_section:
        text = agentic_section.group(1)
        # Extract bullet points or numbered items
        items = re.findall(r'(?:[-*•]\s+|^\d+\.\s+)(.+)', text, re.MULTILINE)
        agentic.extend(items)
    
    return agentic if agentic else ["None identified"]

def extract_notable_features(memo_text):
    """Extract notable features."""
    features = []
    
    # Look for notable features section
    notable_section = re.search(r'Notable Features?:?\s*\n(.*?)(?:\n\n|\n#|\Z)', memo_text, re.DOTALL | re.IGNORECASE)
    if notable_section:
        text = notable_section.group(1)
        # Extract bullet points or numbered items
        items = re.findall(r'(?:[-*•]\s+|^\d+\.\s+)(.+)', text, re.MULTILINE)
        features.extend(items)
    
    return features if features else ["None identified"]

def extract_quotes(memo_text):
    """Extract student quotes from the memo."""
    # Find quoted text
    quotes = re.findall(r'["""]([^"""]+)["""]', memo_text)
    # Return first 2-3 interesting quotes
    return quotes[:3] if quotes else []

def analyze_memo(memo_path):
    """Analyze a single PK-WAP memo."""
    text = memo_path.read_text(encoding='utf-8')
    
    # Extract transcript ID from filename
    transcript_id = memo_path.stem.replace('_PK-WAP', '')
    
    return {
        'transcript_id': transcript_id,
        'pk_level': extract_pk_level(text),
        'recursions': extract_recursions(text),
        'agentic_moves': extract_agentic_moves(text),
        'notable_features': extract_notable_features(text),
        'quotes': extract_quotes(text),
        'memo_path': str(memo_path)
    }

def main():
    memo_dir = Path("PK-WAP Memos")
    
    # Analyze all memos
    results = []
    for memo_file in sorted(memo_dir.glob("*_PK-WAP.md")):
        print(f"Analyzing {memo_file.name}...")
        analysis = analyze_memo(memo_file)
        results.append(analysis)
    
    # Save raw results
    with open('pkwap_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analyzed {len(results)} memos")
    print(f"✓ Results saved to pkwap_analysis_results.json")
    
    # Generate summary statistics
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    # PK Level distribution
    pk_levels = {}
    for r in results:
        level = r['pk_level']
        pk_levels[level] = pk_levels.get(level, 0) + 1
    
    print("\nPK Level Distribution:")
    for level in sorted(pk_levels.keys()):
        count = pk_levels[level]
        print(f"  {level}: {count} cases")
    
    # Recursion statistics
    recursions = [r['recursions'] for r in results]
    avg_recursions = sum(recursions) / len(recursions) if recursions else 0
    print(f"\nRecursive Movements:")
    print(f"  Average: {avg_recursions:.1f}")
    print(f"  Range: {min(recursions)} to {max(recursions)}")
    
    # Agentic moves frequency
    total_agentic = sum(len(r['agentic_moves']) for r in results)
    print(f"\nAgentic Moves:")
    print(f"  Total identified: {total_agentic}")
    print(f"  Average per case: {total_agentic/len(results):.1f}")
    
    # Notable features frequency
    total_features = sum(len(r['notable_features']) for r in results)
    print(f"\nNotable Features:")
    print(f"  Total identified: {total_features}")
    print(f"  Average per case: {total_features/len(results):.1f}")
    
    # Generate detailed report
    print("\n" + "="*70)
    print("DETAILED CASE SUMMARIES")
    print("="*70)
    
    for r in results:
        print(f"\n{r['transcript_id']}:")
        print(f"  PK Level: {r['pk_level']}")
        print(f"  Recursions: {r['recursions']}")
        if r['agentic_moves'] and r['agentic_moves'][0] != "None identified":
            print(f"  Agentic Moves: {len(r['agentic_moves'])} identified")
            for move in r['agentic_moves'][:2]:  # Show first 2
                print(f"    - {move[:80]}...")
        if r['notable_features'] and r['notable_features'][0] != "None identified":
            print(f"  Notable Features: {r['notable_features'][0][:80]}...")

if __name__ == "__main__":
    main()
