#!/bin/bash
# prepare_public_repo.sh
# 
# Prepare a clean repository for public release
# Excludes all raw data and identifying information

echo "Creating public repository structure..."

# Create base directory
mkdir -p public_release
cd public_release

# Create directory structure
mkdir -p scripts
mkdir -p protocols
mkdir -p validation
mkdir -p examples

echo "Copying analysis scripts..."
cp "../Data Formatted to Analyze/pk_screen_v2_2.py" scripts/
cp "../Data Formatted to Analyze/recount_from_annot.py" scripts/
cp "../Data Formatted to Analyze/batch_rows_v3.py" scripts/ 2>/dev/null || true

echo "Creating protocol documentation..."

# Create transcript screening protocol
cat > protocols/transcript_screening_protocol.md << 'EOF'
# Phase I: Transcript Screening Protocol

## Purpose
Compute quantitative baseline of student vs AI participation for each transcript.

## Outputs
- Page-level counts: Student Words | AI Words
- Transcript totals
- %Student Talk = 100 × (Student / (Student + AI))

## Procedure

### 1. Speaker Attribution
**Primary:** Use explicit speaker tags (Student:, AI:, P:, D:, etc.)

**Fallback heuristics when tags missing:**
- Turn-taking continuity (maintain speaker across contiguous blocks)
- Linguistic cues (prompts/explanations = AI; brief answers = Student)
- Layout cues (bullets/indentation = AI; inline text = Student)
- AI boilerplate detection ("Here's an explanation...", "As an AI...")

### 2. Word Counting Rules
- **Alphanumeric tokens** count as words
- **URLs/emails** = 1 token each
- **Math expressions**: term-by-term (x^2 + 2x + 1 = 7 tokens)
- **CJK text**: ceil(length/2) tokens
- **Punctuation-only**: ignored
- **AI preambles**: removed before counting

### 3. Quality Checks
- Student + AI = Total
- %Student + %AI ≈ 100% (±0.1)
- Flag transcripts with >10% unknown attribution

## Manual Calibration
Three researchers independently counted 5 transcripts:
- LibreOffice highlighting method (page-by-page)
- Inter-rater agreement within 10pp
- Established counting rules iteratively

See calibration_methodology.md for details.
EOF

# Create PK-WAP protocol stub
cat > protocols/pk_wap_protocol.md << 'EOF'
# Pirie-Kieren Work Analysis Protocol (PK-WAP)

## Purpose
Qualitative analysis of mathematical understanding using the Pirie-Kieren framework.

## Eight Nested Layers
1. **Primitive Knowing** - Intuitive, informal starting ideas
2. **Image Making** - Building mental representations
3. **Image Having** - Using representations without re-derivation
4. **Property Noticing** - Recognizing patterns/relationships
5. **Formalizing** - Abstract definitions and theorems
6. **Observing** - Reflecting on formal structures
7. **Structuring** - Theory-building across concepts
8. **Inventising** - Creating new mathematics

## Analysis Process
1. Page-by-page review with word counts
2. Extract representative passages (student & AI)
3. Code for evidence of all 8 layers
4. Identify "folding back" (recursive movement between layers)
5. Document missed pedagogical opportunities
6. Generate analytic memo

## AI-Assisted Analysis
- GPT-4 generates initial memos using standardized prompt
- Human researchers validate and revise
- Gold-standard exemplar prevents analytic drift

See Appendix E in paper for full protocol and exemplar memo.
EOF

# Create calibration methodology
cat > protocols/calibration_methodology.md << 'EOF'
# Manual Calibration Methodology

## Overview
Three researchers (Eleanor, Todd, Zheng) independently counted five transcripts to establish inter-rater reliability and refine counting rules.

## Selected Transcripts
- P79-G8-S5
- P21-G5-S5  
- P100-G12-S4
- P106-GX-SX
- P76-GX-SX

**Selection criteria:** Identified by Zheng (course instructor) for format diversity and representativeness of student submissions.

## Procedure

### For each transcript:

1. **Read electronically** in LibreOffice Writer
2. **Highlight AI passages** (using LibreOffice highlighting tool)
3. **Word count highlighted section** (Tools → Word Count)
4. **Record tally** on paper copy
5. **Highlight student passages**
6. **Word count highlighted section**
7. **Record tally** on paper copy
8. **Work page-by-page**, summing to transcript total

### After each transcript:

1. **Meet as team** to compare results
2. **Discuss discrepancies** (line-by-line if >10% difference)
3. **Refine rules** for ambiguous cases
4. **Document decisions** for next transcript

## Results

**Inter-rater agreement:** Within 10 percentage points on %Student Talk

**Example (P79-G8-S5):**
- Eleanor: 60.0% student (1826/1219/3045)
- Zheng: 57.8% student (1884/1375/3259)
- Difference: 2.2 percentage points ✓

## Counting Tool
**LibreOffice Writer word count** uses whitespace-based word splitting algorithm. This became the reference standard for automated validation.

## Automated Implementation
The `pk_screen_v2_2.py` script with `--simple-words` flag replicates this methodology for scalability across 127 transcripts.
EOF

echo "Creating example anonymized data..."

# Copy the 5 calibration transcripts (de-identified)
mkdir -p data/calibration_transcripts
echo "Copying 5 calibration transcripts for reproducibility..."
for file in P79-G8-S5.txt P21-G5-S5.txt P100-G12-S4.txt P106-GX-SX.txt P76-GX-SX.txt; do
    if [ -f "../Data Formatted to Analyze/$file" ]; then
        cp "../Data Formatted to Analyze/$file" "data/calibration_transcripts/"
        echo "  ✓ $file"
    fi
done

# Copy calibration validation data
if [ -f "../calibration_validation_data.csv" ]; then
    cp "../calibration_validation_data.csv" "data/"
    echo "  ✓ calibration_validation_data.csv"
fi

# Create aggregate results file (will be populated after re-run)
cat > data/aggregate_results_all_127.csv << 'EOF'
# This file will contain word count results for all 127 transcripts
# Format: Transcript_ID,Student_Words,AI_Words,Total_Words,Percent_Student,Status
# To be generated by running: python3 scripts/pk_screen_v2_2.py --input [all_transcripts] --outdir results/
EOF

cat > examples/example_transcript_format.txt << 'EOF'
=== Page 00 ===
P: You are a Personality-based AI Teacher Generator. Your goal is to figure out what kind of teacher I would learn best from...

D: Understood! To discover the teaching style that resonates best with you, I'll start by observing how you respond to different approaches...

P: I prefer direct explanations.

D: Noted. Next question: When you're stuck on a problem, what frustrates you more...

[Example continues...]
EOF

cat > examples/example_annotated_output.txt << 'EOF'
[STUDENT] You are a Personality-based AI Teacher Generator. Your goal is to figure out what kind of teacher I would learn best from...
[AI] Understood! To discover the teaching style that resonates best with you, I'll start by observing how you respond to different approaches...
[STUDENT] I prefer direct explanations.
[AI] Noted. Next question: When you're stuck on a problem, what frustrates you more...
EOF

cat > examples/example_summary.csv << 'EOF'
filename,student_words,ai_words,total,pct_student,unknown_words,status,note
P079-G8-S5.txt,1521,1419,2940,51.7,135,ok,
P021-G5-S5.txt,456,2123,2579,17.7,89,ok,
P100-G12-S4.txt,78,1598,1676,4.7,0,ok,low_student
EOF

echo "Creating validation scripts..."

cp validate_counting.py validation/ 2>/dev/null || echo "# Validation script" > validation/validate_counting.py
cp test_all_calibration.py validation/ 2>/dev/null || echo "# Calibration test" > validation/test_all_calibration.py

echo "Creating LICENSE..."
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 [Your Names/Institution]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

Documentation (protocols/, README.md) is licensed under CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/
EOF

echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Exclude all raw data
*.txt
*.pdf
*.docx
!examples/*.txt

# Exclude identifying information
**/Original Data/
**/Analyzed Cases*/
**/Phase 1 Redo/
calibration*.xlsx
calibration*.csv

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
*.egg-info/

# OS
.DS_Store
Thumbs.db
EOF

echo "Creating requirements.txt..."
cat > requirements.txt << 'EOF'
python-docx>=0.8.11
joblib>=1.1.0
EOF

cp ../REPRODUCIBILITY_README.md README.md

echo ""
echo "Public repository structure created in: public_release/"
echo ""
echo "Next steps:"
echo "1. Review all files for any identifying information"
echo "2. Initialize git repo: cd public_release && git init"
echo "3. Create GitHub repo and push"
echo "4. Add DOI/Zenodo archival for permanent citation"
echo ""
echo "Structure:"
find . -type f | grep -v ".git" | sort
