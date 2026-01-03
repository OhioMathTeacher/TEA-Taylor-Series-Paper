# PK-WAP Deep Research Memo — Master Template with Guardrails

---

### Introduction / Context  
Case P35-G1-S4 analyzes student-AI dialogue on Taylor series approximation using PK-WAP. The mathematical scenario involves approximating bacterial growth \( f(t) = \frac{e^{0.3t}}{1 + t^2} \) near \( t = 0 \). Unlabeled student responses to AI prompts are coded as student turns.

---

## 1) Word counts & % student talk by page (estimated)  

| Page | Student Words | AI Words | % Student Talk |
| ---: | ------------: | -------: | -------------: |
| 00   | 0             | 120      | 0              |
| 01   | 0             | 180      | 0              |
| 02   | 6             | 200      | 3              |
| 03   | 16            | 150      | 10             |
| 04   | 0             | 220      | 0              |
| 05   | 18            | 180      | 9              |
| 06   | 0             | 180      | 0              |
| 07   | 0             | 150      | 0              |
| 08   | 200           | 250      | 44             |

**Overall student talk:** 240 words (13% of total dialogue).

---

## 2) Layer Progression Map  
```
Primitive Knowing (P00) → Image-Making (P02) 
     ↗ Property-Noticing (P03) → Formalising (P05) 
    ↻ Fold-back to Property-Noticing (P07) → Formalising (P08)
```
*Fold-back arrows: P07 (testing limitations) → P08 (radius analysis)*

---

## 3) Recursive / folding-back moments (narrative)  
- **Fold-back 1 (P02→P03):** Student initially proposes measuring bacterial reproduction (Image-Making). AI refines the scenario to \( f(t) = \frac{e^{0.3t}}{1 + t^2} \), prompting student to identify computational barriers. Student folds back to Property-Noticing by articulating non-integer exponent difficulties and exponential growth properties.  
- **Fold-back 2 (P07→P08):** After Formalising the approximation (P05), AI challenges validity at \( t = 2 \). Student reconstructs understanding by folding back to Property-Noticing (higher-order term dominance) before Formalising convergence principles (P08).  

---

## 4) PK layer coding (evidence-rich)  

| Layer             | Evidence from transcript | Notes on classification |
| ----------------- | ------------------------ | ----------------------- |
| Primitive Knowing | Student recalls basic exponent properties (P03: "e^n difficult when n not integer") | Foundational arithmetic knowledge |
| Image-Making      | Proposes bacterial growth scenario (P02: "Measure bacteria reproducing") | Initial mental image formation |
| Image-Having      | Refines scenario using AI's function (P03: "Growth rate follows...") | Consolidated mental model |
| Property-Noticing | Identifies function properties (P03: "Fast growth rate"; P08: "Higher-order terms dominate") | Observing mathematical behaviors |
| Formalising       | Constructs Taylor expansion (P05: "1 + 0.3t - 0.955t²"); derives radius (P08: "R=1") | Abstract procedural application |
| Observing         | *No evidence* | Absent; no metacognitive reflection on mathematical system |
| Structuring       | *No evidence* | Absent; no theory-building across concepts |
| Inventising       | *No evidence* | Absent; no novel mathematical extensions |

---

## 5) Page-by-page PK-WAP coding  

| Page | Dominant layer(s) | Representative evidence | Notes |
| ---: | ----------------- | ----------------------- | ----- |
| 00   | Primitive Knowing | AI historical context | Setup with no student input |
| 01   | Primitive Knowing | AI mission description | Conceptual priming |
| 02   | Image-Making      | Student: "Measure bacteria" | Scenario proposal |
| 03   | Property-Noticing | Student: "e^n difficult..." | Function property identification |
| 04   | Image-Having      | AI: "Nonlinear interplay" | Scenario refinement |
| 05   | Formalising       | Student: "1 + 0.3t - 0.955t²" | Polynomial construction |
| 06   | Formalising       | AI: "Discard higher-order terms" | Approximation rationale |
| 07   | Property-Noticing | AI: "Higher-order terms dominate" | Limitation setup |
| 08   | Formalising       | Student: "Radius R=1" | Convergence formalization |

---

## 6) Representative quotes  

**Student:**  
1. P02: "Measure bacteria reproducing" *(Image-Making: Initial problem framing)*  
2. P03: "e^n difficult when n not integer" *(Property-Noticing: Computational barrier)*  
3. P05: "Final quadratic approximation... 1 + 0.3t - 0.955t²" *(Formalising: Abstract procedural application)*  
4. P08: "Neglected higher-order terms... cause large deviation" *(Property-Noticing: Limitation analysis)*  
5. P08: "Radius of convergence R=1" *(Formalising: Convergence formalization)*  
6. P08: "Approximation depends on local behavior" *(Property-Noticing: Proximity principle)*  

**AI:**  
1. P02: "Bacteria growth perfect for Taylor approximations" *(Image-Having: Scenario validation)*  
2. P04: "Numerator grows rapidly, denominator tempers it" *(Property-Noticing: Function behavior)*  
3. P05: "Discard terms with power > 2" *(Formalising: Approximation heuristic)*  
4. P06: "For tiny t, Taylor fantastic" *(Property-Noticing: Contextual strength)*  
5. P07: "Taylor polynomials like a microscope" *(Image-Having: Analogical reinforcement)*  
6. P08: "Convergence controlled by denominator" *(Property-Noticing: Singularity impact)*  

---

## 7) Missed opportunities (elaborated)  
1. **P03:** AI accepted "fast growth rate" without probing rate quantification (e.g., comparing linear vs. exponential growth), missing deeper Property-Noticing.  
2. **P05:** AI verified polynomial without asking why \( t^3+ \) terms are negligible, missing Formalising opportunity for error-bound reasoning.  
3. **P08:** AI praised radius explanation but didn't connect to derivative continuity, missing Structuring potential between convergence and differentiability.  

---

## 8) Summary of Findings  
The dialogue shows robust progression from Image-Making (bacteria scenario) to Formalising (polynomial construction and convergence). Engagement peaked during limitation analysis (P08), where student agency manifested in self-driven radius derivation. Tone remained positive with effective puppy-themed scaffolding, though AI dominated talk time (87%). Key growth occurred during fold-backs: student reconstructed understanding when transitioning from global scenario (P02) to local approximation constraints (P08). PK layers advanced conservatively, peaking at Formalising with no outer-layer activity.  

---

## 9) Final observations  
Student demonstrated strong agency in problem-solving (e.g., self-correcting polynomial coefficients) but relied on AI for procedural scaffolding. Playful tone enhanced engagement without distracting from mathematical goals. To deepen learning, AI could reduce directive prompts (e.g., "discard terms >2") and instead ask open-ended questions about approximation trade-offs. PK movement remained bounded within inner layers, reflecting typical tutoring constraints where metacognitive reflection (Observing+) requires explicit facilitation.  

---

## 10) Conclusion  
P35-G1-S4 exemplifies effective PK progression (PK→IM→PN→F) in function approximation, highlighting how structured AI guidance supports Formalising. The trajectory underscores pedagogical value in strategic fold-backs (e.g., testing limitations) for reconstructing understanding. Future implementations should prioritize student-led justification to cultivate Observing, though this case confirms inner-layer mastery as a realistic outcome for tutoring dialogues.