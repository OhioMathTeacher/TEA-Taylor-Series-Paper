#!/usr/bin/env python3
"""
PK-WAP Analyzer - Automated Pirie-Kieren Work Analysis Protocol

Generates deep analytic memos for student-AI transcripts following the 
PK-WAP template from Appendix F.

Usage:
  python3 pkwap_analyzer.py --transcript P28-G16-S5.txt --output memos/
  python3 pkwap_analyzer.py --batch transcripts/ --output memos/ --limit 10
  python3 pkwap_analyzer.py --transcript P28-G16-S5.txt --model gpt-4o --temperature 0.3

Requirements:
  - OpenAI API key in environment (OPENAI_API_KEY)
  - Template file: P00-G00-S0 PK-WAP TEMPLATE.md
  - Reference PDFs (optional): Pirie-Kieren framework, Boaler examples
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, List
import json

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not installed.")
    print("Install with: pip install openai")
    sys.exit(1)

# Configuration defaults
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 16000
BATCH_SLEEP = 2.0  # seconds between API calls

# File paths
TEMPLATE_FILE = "P00-G00-S0 PK-WAP TEMPLATE.md"
PIRIE_KIEREN_REF = "pirie_kieren_framework.pdf"  # optional
BOALER_REF = "boaler_examples.pdf"  # optional


def read_file(path: Path) -> str:
    """Read text file with UTF-8 encoding."""
    return path.read_text(encoding="utf-8", errors="ignore")


def load_template(template_path: Path) -> str:
    """Load the PK-WAP template file."""
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template file not found: {template_path}\n"
            f"Please ensure P00-G00-S0 PK-WAP TEMPLATE.md is in the same directory."
        )
    return read_file(template_path)


def build_prompt(transcript: str, template: str, transcript_id: str) -> List[dict]:
    """
    Build the prompt messages for OpenAI API based on Appendix F specification.
    
    Returns a list of message dicts with role and content.
    """
    
    system_message = {
        "role": "system",
        "content": (
            "You are an expert educational researcher specializing in mathematical cognition "
            "and the Pirie-Kieren framework for recursive understanding. You analyze student-AI "
            "dialogue transcripts with deep pedagogical insight, identifying evidence of conceptual "
            "growth, folding-back moments, and missed learning opportunities. Your analyses are "
            "rigorous, evidence-based, and formatted according to strict academic protocols."
        )
    }
    
    user_message = {
        "role": "user",
        "content": f"""I'm researching student–AI mathematical dialogue. Please analyze the attached transcript ({transcript_id}) using the Pirie–Kieren Work Analysis Protocol (PK-WAP) and generate a Deep Research–style memo that follows exactly the structure, headings, numbering, and formatting rules in the template below.

The template rules are non-negotiable:
- Section order, headings, and numbering must match exactly
- Word Count table must follow the template's required column names and order: Page | Student Words | AI Words | % Student Talk
- Include all analytical components listed in the template at full depth
- Analytical content must be specific to the transcript (no generic/template-sounding text)

Follow these steps:
1. Estimate word counts and identify recursive/folding-back moments with narrative detail
2. Code for all 8 Pirie–Kieren layers (Primitive Doing → Inventising)
3. Highlight representative quotes from both student and AI (4–6 per side)
4. Assess missed opportunities for AI to support deeper learning (1–2 sentences per item)
5. Provide a summary that synthesizes growth, agency, and tone

Please take your time—it's okay if this takes several minutes to complete. The goal is a pedagogically insightful, deeply interpretive analysis in the exact format of the template.

---
TEMPLATE (follow this structure exactly):
---

{template}

---
TRANSCRIPT TO ANALYZE ({transcript_id}):
---

{transcript}

---

Generate the complete PK-WAP memo now, following the template structure exactly.
"""
    }
    
    return [system_message, user_message]


def call_openai(
    messages: List[dict],
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> str:
    """Call OpenAI API and return the response content."""
    client = OpenAI()
    
    print(f"  Calling OpenAI API ({model}, temp={temperature})...")
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return response.choices[0].message.content.strip()


def save_memo(content: str, output_path: Path, transcript_id: str):
    """Save the generated memo to a markdown file."""
    output_path.mkdir(parents=True, exist_ok=True)
    
    memo_file = output_path / f"{transcript_id}_PK-WAP.md"
    memo_file.write_text(content, encoding="utf-8")
    
    return memo_file


def process_transcript(
    transcript_path: Path,
    template_path: Path,
    output_dir: Path,
    model: str,
    temperature: float,
    max_tokens: int
) -> dict:
    """
    Process a single transcript through PK-WAP analysis.
    
    Returns a dict with status info.
    """
    transcript_id = transcript_path.stem  # e.g., "P28-G16-S5"
    
    print(f"\nProcessing: {transcript_id}")
    print(f"  Loading transcript from {transcript_path}...")
    
    try:
        # Load files
        transcript = read_file(transcript_path)
        template = load_template(template_path)
        
        # Build prompt
        messages = build_prompt(transcript, template, transcript_id)
        
        # Call API
        start_time = time.time()
        memo_content = call_openai(messages, model, temperature, max_tokens)
        elapsed = time.time() - start_time
        
        # Save output
        memo_file = save_memo(memo_content, output_dir, transcript_id)
        
        print(f"  ✓ Complete in {elapsed:.1f}s")
        print(f"  Saved to: {memo_file}")
        
        return {
            "transcript_id": transcript_id,
            "status": "success",
            "output_file": str(memo_file),
            "elapsed_seconds": elapsed,
            "memo_length": len(memo_content)
        }
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {
            "transcript_id": transcript_id,
            "status": "error",
            "error": str(e)
        }


def batch_process(
    transcript_dir: Path,
    template_path: Path,
    output_dir: Path,
    model: str,
    temperature: float,
    max_tokens: int,
    limit: Optional[int] = None
):
    """Process multiple transcripts in batch."""
    
    # Find all transcript files
    transcript_files = sorted(transcript_dir.glob("P*.txt"))
    
    if not transcript_files:
        print(f"No transcript files (P*.txt) found in {transcript_dir}")
        return
    
    if limit:
        transcript_files = transcript_files[:limit]
    
    print(f"Found {len(transcript_files)} transcript(s) to process")
    
    results = []
    
    for i, transcript_path in enumerate(transcript_files, 1):
        print(f"\n[{i}/{len(transcript_files)}]", end=" ")
        
        result = process_transcript(
            transcript_path,
            template_path,
            output_dir,
            model,
            temperature,
            max_tokens
        )
        
        results.append(result)
        
        # Save progress log
        log_file = output_dir / "pkwap_batch_log.json"
        with open(log_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Rate limiting
        if i < len(transcript_files):
            time.sleep(BATCH_SLEEP)
    
    # Summary
    print("\n" + "="*60)
    print("BATCH PROCESSING COMPLETE")
    print("="*60)
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    
    print(f"Total processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        total_time = sum(r.get("elapsed_seconds", 0) for r in results if r["status"] == "success")
        avg_time = total_time / successful
        print(f"Average time per memo: {avg_time:.1f}s")
    
    print(f"\nLog saved to: {log_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate PK-WAP analytic memos for student-AI transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single transcript
  python3 pkwap_analyzer.py --transcript P28-G16-S5.txt --output memos/
  
  # Batch process (first 10)
  python3 pkwap_analyzer.py --batch transcripts/ --output memos/ --limit 10
  
  # Custom model settings
  python3 pkwap_analyzer.py --transcript P28.txt --model gpt-4-turbo --temperature 0.3
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--transcript",
        type=Path,
        help="Single transcript file to process"
    )
    input_group.add_argument(
        "--batch",
        type=Path,
        help="Directory containing multiple transcripts to process"
    )
    
    # Output and template
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./pkwap_memos"),
        help="Output directory for generated memos (default: ./pkwap_memos)"
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(TEMPLATE_FILE),
        help=f"Path to PK-WAP template file (default: {TEMPLATE_FILE})"
    )
    
    # Model configuration
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {DEFAULT_TEMPERATURE})"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum tokens in response (default: {DEFAULT_MAX_TOKENS})"
    )
    
    # Batch options
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of transcripts to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Validate API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Process
    if args.transcript:
        # Single file mode
        if not args.transcript.exists():
            print(f"Error: Transcript file not found: {args.transcript}")
            sys.exit(1)
        
        process_transcript(
            args.transcript,
            args.template,
            args.output,
            args.model,
            args.temperature,
            args.max_tokens
        )
    else:
        # Batch mode
        if not args.batch.is_dir():
            print(f"Error: Batch directory not found: {args.batch}")
            sys.exit(1)
        
        batch_process(
            args.batch,
            args.template,
            args.output,
            args.model,
            args.temperature,
            args.max_tokens,
            args.limit
        )


if __name__ == "__main__":
    main()
