# TEA Taylor Series Paper

**Generative AI as a Recursive Learning Partner: A Pirie-Kieren Analysis of Taylor Series Instruction in University Calculus**

## Authors

- **Michael Todd Edwards** (The Ohio State University at Lima)
- *[Additional authors as applicable]*

Technology Educator Alliance (TEA)

---

## Project Overview

This project examines how undergraduate calculus students engage in **recursive mathematical understanding** while learning Taylor series through collaboration with generative AI. The study applies the **Pirie-Kieren model of mathematical understanding** to analyze student-AI dialogue transcripts, revealing patterns of folding back and layer progression characteristic of deep mathematical learning.

### Key Innovation

The methodological innovation is the **Pirie-Kieren Work Analysis Protocol (PK-WAP)**, which uses GenAI as a systematic qualitative analysis partner. This approach enables consistent coding across large datasets while maintaining theoretical fidelity to the Pirie-Kieren framework.

---

## Repository Structure

```
TEA-Taylor-Series-Paper/
├── Manuscript/
│   ├── main.tex                    # Primary LaTeX source
│   ├── methods.tex                 # Methods section
│   ├── appendix.tex                # Supplementary materials
│   ├── bibliography.tex            # References
│   └── figures/
│       └── fig1_tikz.tex           # TikZ figure sources
│
├── Scripts/
│   ├── pkwap_analyzer.py           # Main PK-WAP analysis engine
│   ├── pk_screen_v2_2.py           # Phase I word count screening
│   ├── process_anchor_cases.py     # Anchor case batch processing
│   ├── select_anchor_transcripts.py
│   ├── validate_counting.py        # Word count validation
│   ├── reconcile_counts.py         # Cross-validation tools
│   ├── test_all_calibration.py     # Calibration testing suite
│   ├── transcript_reviewer.py      # Flask web app for case tagging
│   ├── review_candidates.py        # Noteworthy case review
│   └── analyze_pkwap_memos.py      # Post-hoc memo analysis
│
├── Templates/
│   ├── P00-G00-S0 PK-WAP TEMPLATE.md   # Gold standard memo template
│   └── reviewer.html                    # Web interface template
│
├── Documentation/
│   ├── REPRODUCIBILITY_README.md
│   ├── VALIDATION_FINDINGS.md
│   ├── calibration_comparison.md
│   └── DATA_SHARING_STATEMENT.md
│
└── Paper Drafts/
    └── Response_to_Reviewers_Draft.md
```

---

## Study Design

### Two-Phase Analysis Pipeline

| Phase | Focus | Methods |
|-------|-------|---------|
| **Phase I** | Quantitative Screening | Automated word count analysis; Student vs. AI talk percentages; High/low engagement case identification |
| **Phase II** | Qualitative Deep Analysis | PK-WAP coding via GenAI; Evidence-based layer identification; Recursive learning pattern detection |

### Participants

- **N=30+** student-AI dialogue transcripts
- University calculus students learning Taylor series
- Transcripts from AI tutoring interactions

---

## Theoretical Framework

### Pirie-Kieren Model of Mathematical Understanding

The Pirie-Kieren model describes mathematical understanding as a recursive, non-linear process through nested layers:

1. **Primitive Knowing** — Prior knowledge brought to the task
2. **Image Making** — Developing mental images through activities
3. **Image Having** — Using images without needing to reconstruct them
4. **Property Noticing** — Recognizing connections between images
5. **Formalising** — Abstracting common properties into formal definitions
6. **Observing** — Reflecting on formal understanding
7. **Structuring** — Connecting formal observations into theory
8. **Inventising** — Creating new questions and mathematical inquiry

### Key Constructs

- **Folding Back**: Returning to inner layers to extend or reconstruct understanding
- **Layer Progression**: Movement outward through increasingly sophisticated understanding
- **Don't Need Boundaries**: Points where prior constructions become embedded and automatic

---

## Installation

```bash
pip install openai python-docx flask pandas
export OPENAI_API_KEY='your-key-here'
```

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `Manuscript/main.tex` | Primary LaTeX source for submission |
| `Templates/P00-G00-S0 PK-WAP TEMPLATE.md` | Gold standard template for PK-WAP analysis memos |
| `Documentation/REPRODUCIBILITY_README.md` | Detailed reproducibility guidelines |

---

## Research Questions

1. How does student-AI dialogue during Taylor series instruction reflect **recursive patterns of mathematical understanding** as characterized by the Pirie-Kieren model?

2. What **folding-back moments** emerge when students encounter conceptual difficulties, and how does AI scaffolding support (or hinder) this process?

3. How can **GenAI-assisted qualitative analysis** maintain theoretical fidelity while enabling systematic coding across large transcript datasets?

---

## Status

📋 **Current Phase**: Manuscript Revision

**Completed**:
- [x] Transcript collection
- [x] Phase I quantitative screening
- [x] Phase II PK-WAP analysis
- [x] Calibration and validation

**In Progress**:
- [ ] Manuscript revisions
- [ ] Response to reviewers

---

## Data Availability

Student transcript data is not included due to privacy protections. Contact the authors for data access inquiries related to research verification.

---

## Citation

See [CITATION.cff](CITATION.cff) for citation details.

---

## Contact

For questions about this project, contact the TEA collaborators via repository issues.
