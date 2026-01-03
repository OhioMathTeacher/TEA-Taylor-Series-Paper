# PK-WAP Deep Research Memo — Master Template with Guardrails

---

### Introduction / Context

Case P94-G6-S4 analyzes student-AI dialogue on applying Taylor series approximations to quantum wavefunctions for electron position prediction. The mathematical scenario involves constructing Taylor expansions for ψ(r,θ,φ,t), analyzing error terms, and evaluating validity under quantum constraints. Unlabeled student responses to AI prompts are treated as student contributions per protocol.

---

## 1) Word counts & % student talk by page (estimated)

| Page | Student Words | AI Words | % Student Talk |
| ---: | ------------: | -------: | -------------: |
| 00   |            11 |      150 |            6.8 |
| 01   |           180 |      100 |           64.3 |
| 02   |           200 |      100 |           66.7 |
| 03   |           100 |       50 |           66.7 |
| 04   |             0 |      150 |            0.0 |
| 05   |           250 |       50 |           83.3 |
| 06   |           100 |        0 |          100.0 |
| 07   |             0 |      100 |            0.0 |
| 08   |           250 |        0 |          100.0 |
| 09   |           200 |      150 |           57.1 |
| 10   |             0 |      100 |            0.0 |

**Overall student talk:** 1291 words (**57.6**).

---

## 2) Layer Progression Map

```
Primitive Knowing (P00)
↓
Image-Making (P01)
↓
Image-Having (P02) → Property-Noticing (P03) 
    ↖ (fold-back: P03 critique) 
    ↙ 
Image-Having (P03 refinement) 
↓ 
Formalising (P05) 
    ↖ (fold-back: P05 critique) 
    ↙ 
Formalising (P05 revised) 
↓ 
Property-Noticing (P08) 
↓ 
Property-Noticing (P09)
```

---

## 3) Recursive / folding-back moments (narrative)

**P03 Fold-back (Image-Having → Reconstruction):** After the AI challenged the student's radial-only Taylor expansion (P02), the student folded back to Image-Having to incorporate time-dependence and mixed derivatives. The student reconstructed the approximation by adding ∂ψ/∂t and ∂²ψ/∂r∂t terms, demonstrating adaptive understanding of multivariate requirements while maintaining physical interpretations (P03).

**P05 Fold-back (Formalising → Error Refinement):** When the AI critiqued the stationary-state assumption in temporal validity calculations (P05), the student folded back to Formalising to derive new error bounds under time-dependent perturbation V(t) = V₀ + εcos(ωt). This involved reformulating ∂ψ/∂t with perturbation terms and scaling error with ε/ℏ, showing deeper formalization of approximation limits (P05 revised).

---

## 4) PK layer coding (evidence-rich)

| Layer             | Evidence from transcript | Notes on classification |
| ----------------- | ------------------------ | ----------------------- |
| Primitive Knowing | Student states impossibility of exact electron trajectory calculation (P00) | Basic recall of quantum constraint without elaboration |
| Image-Making      | Student explains Heisenberg's uncertainty principle and Schrödinger complexity (P01) | Building conceptual understanding of approximation necessity |
| Image-Having      | Student constructs Taylor terms for ψ(r) with physical interpretations (P02) and adds time derivatives post-critique (P03) | Using expansion as tool with physical meaning |
| Property-Noticing | Student quantifies error bounds (P03), identifies Rydberg validity conditions (P08), and laser failure scenarios (P09) | Noting approximation properties/limits without abstraction |
| Formalising       | Student derives spatial cutoff via |R₂(r)/ψ(r)| > 0.1 inequality and temporal validity with perturbation (P05) | Systematic application of formal procedures |
| Observing         | *No evidence* | No metacognitive reflection on mathematical system |
| Structuring       | *No evidence* | No theoretical synthesis of multiple concepts |
| Inventising       | *No evidence* | No novel mathematical questions or extensions |

---

## 5) Page-by-page PK-WAP coding

| Page | Dominant layer(s) | Representative evidence | Notes |
| ---: | ----------------- | ----------------------- | ----- |
| 00   | Primitive Knowing | "It is impossible to accurately calculate..." | Basic factual recall |
| 01   | Image-Making      | Explanation of physical/mathematical constraints | Conceptual framing |
| 02   | Image-Having      | Taylor term construction with physical meanings | Tool application |
| 03   | Image-Having      | Addition of ∂ψ/∂t term post-critique | Reconstruction |
| 04   | N/A               | AI prompt only | No student response |
| 05   | Formalising       | Spatial cutoff derivation via inequality | Formal procedure |
| 06   | Formalising       | Temporal validity calculation extension | Continued formalization |
| 07   | N/A               | AI prompt only | No student response |
| 08   | Property-Noticing | Validity arguments for Rydberg atoms | Condition identification |
| 09   | Property-Noticing | Failure analysis for attosecond lasers | Limitation recognition |
| 10   | N/A               | AI prompt only | No student response |

---

## 6) Representative quotes

**Student:**  
1. P01: "Heisenberg's uncertainty principle states that we cannot simultaneously determine the position and momentum... Therefore, we cannot directly use this function." *(Image-Making)*  
2. P02: "First-order term: Linear drift of electron probability density" *(Image-Having physical interpretation)*  
3. P05: "We want to find |r−ro| when the error exceeds 10%" *(Formalising inequality setup)*  
4. P08: "For Rydberg atoms... Taylor approximation may hold for short-timescale observations" *(Property-Noticing validity)*  
5. P09: "Under attosecond laser pulses... Taylor approximation will completely fail" *(Property-Noticing limitation)*  
6. P09: "Perturbation parameter ε far exceeds Eₙ" *(Property-Noticing mathematical reason)*  

**AI:**  
1. P00: "Taylor polynomials were born of necessity—Newton used them to approximate orbital paths" *(Context-setting)*  
2. P02: "Critical Interruption: Defend smooth differentiability assumption" *(Challenging Image-Having)*  
3. P05: "Your temporal validity assumes stationary state—electrons are rarely obliging" *(Pushing Formalising rigor)*  
4. P07: "Refine spatial cutoff: What percentage of probability density discarded?" *(Demanding quantitative precision)*  
5. P09: "You failed to confront nodal singularities where ψ=0" *(Summative feedback gap)*  
6. P10: "What did this teach about the price of tractability?" *(Metacognitive prompt)*  

---

## 7) Missed opportunities (elaborated)

1. **P03 Expansion critique:** AI corrected missing time-dependence but missed asking student to self-identify limitations by comparing static vs. dynamic systems, preventing deeper Property-Noticing.  
2. **P05 Stationary state:** AI noted assumption flaw but didn't prompt contrast between stationary/non-stationary states, missing chance to reinforce Image-Having foundations.  
3. **P08 Validity arguments:** AI accepted qualitative "short-timescale" justification without requesting mathematical parameterization (e.g., τ_system vs. τ_approximation), foregoing Formalising advancement.  

---

## 8) Summary of Findings

The student demonstrated strong agency in navigating complex quantum approximations, progressing from Primitive Knowing to Formalising through iterative fold-backs. Dominant layers were Image-Having (tool application) and Formalising (error quantification), with Property-Noticing emerging when evaluating experimental scenarios. Tone remained task-focused under AI's adversarial "Snape" persona, with key growth in revising expansions post-critique and formalizing perturbation effects. No evidence of Observing or beyond, consistent with conservative coding.  

---

## 9) Final observations

PK movement centered on reconstructing understanding at Image-Having/Formalising layers after AI challenges, showing responsive agency but limited metacognition. The demanding tone ensured precision yet potentially inhibited reflective depth. For improvement, strategically placed prompts connecting approximation trade-offs to broader mathematical principles could scaffold Observing. Student consistently engaged with technical rigor but did not abstract beyond immediate problem constraints.  

---

## 10) Conclusion

This case matters for demonstrating how targeted fold-backs (Image-Having → Formalising) support robust procedural knowledge in applied mathematics. The trajectory Primitive Knowing → Image-Making → Image-Having → Formalising → Property-Noticing reflects effective scaffolding for technical domains, though metacognitive growth remained unrealized. Pedagogically, it highlights the need to balance adversarial rigor with structured reflection opportunities to advance beyond Formalising.