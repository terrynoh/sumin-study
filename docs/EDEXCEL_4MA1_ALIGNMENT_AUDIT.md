# Edexcel 4MA1 Higher Alignment Audit

Status: v0.1 audit, not yet implemented  
Date: 2026-05-05  
Student context: Year 10  
Target qualification: Pearson Edexcel International GCSE Mathematics A, 4MA1, Higher Tier  
Current project baseline before audit: Cambridge IGCSE Mathematics 0580 Extended

## 1. Audit Conclusion

The learning product direction is still correct, but the exam-board alignment is not.

Keep:
- The core product purpose.
- The quadratics MVP.
- The metacognitive stuck-point model.
- The mastery vector.
- The hint ladder.
- The repair routing architecture.
- React + Vite, local-first deployment, SQLite, and the existing API structure.

Change:
- Replace Cambridge 0580 as the exam board target with Pearson Edexcel International GCSE Mathematics A 4MA1 Higher.
- Replace Cambridge source references and Cambridge-style item metadata.
- Reframe `core_repair` as prerequisite repair drawn from Foundation-assumed knowledge, not Cambridge Core.
- Update calculator and assessment assumptions: 4MA1 Higher has two Higher papers, 4MA1/1H and 4MA1/2H, both allowing calculators.
- Add Edexcel syllabus reference metadata to concept and item records before expanding the item bank.

## 2. Non-Negotiable Product Purpose

The exam-board pivot must not weaken the original purpose.

This program is not primarily a question-volume tool. It is a self-study system that helps Sumin notice where her mathematical thinking breaks, reconnect that break, and transfer the repaired understanding into unfamiliar Edexcel 4MA1 Higher exam problems.

The three controlling dimensions are:

1. Metacognitive control  
   The student learns to observe how she thinks while solving mathematics. A correct answer is not enough if the system cannot help her name the thinking move that worked or failed.

2. Affective control  
   The student should recover perceived control: "my effort has a visible path to improvement." The system must avoid turning data into surveillance or fixed-ability judgement.

3. Performance and transfer  
   The final output must improve exam performance by moving beyond instrumental procedure memory. The student must handle changed wording, changed form, graph/algebra translation, contextual questions, and method choice.

## 3. Official Edexcel 4MA1 Higher Anchors

Primary source:
- Pearson Edexcel International GCSE in Mathematics (Specification A) (4MA1), specification PDF.

Relevant official anchors:
- Subject code: 4MA1.
- Higher paper codes: 4MA1/1H and 4MA1/2H.
- Assessment: two externally assessed papers, each 2 hours and 100 marks, each worth 50%.
- Higher Tier assumes Foundation Tier subject content.
- Higher Tier assesses grades 9-4.
- Calculator use is allowed in the examinations.

Relevant Higher quadratics content:
- 2.4 Algebraic manipulation:
  - understand the concept of a quadratic expression and factorise such expressions.
  - complete the square for a given quadratic expression.
- 2.7 Quadratic equations:
  - solve quadratic equations by factorisation.
  - solve quadratic equations by using the quadratic formula or completing the square.
  - form and solve quadratic equations from data given in a context.
  - solve simultaneous equations in two unknowns, one linear and one quadratic.
- 2.8 Inequalities:
  - solve quadratic inequalities in one unknown and represent the solution set on a number line.
- 3.3 Graphs:
  - recognise, generate points, plot and interpret graphs of linear and quadratic functions.

## 4. Current Local Alignment Findings

### 4.1 Files With Direct Cambridge Assumptions

Must modify:
- `MVP_SPEC.md`
  - Contains Cambridge 0580 Extended as product-language/exam-readiness target.
  - Contains IGCSE/Cambridge notation as target notation.
- `docs/DESIGN_BRIEF.md`
  - Section 14 confirms Cambridge IGCSE 0580 Extended.
  - Problem source pipeline says Cambridge-first.
  - Item path language uses Extended/Core framing.
- `content/quadratics/concept_graph.json`
  - `exam_board.board` is Cambridge IGCSE Mathematics.
  - `syllabus_code` is 0580.
  - `source_refs` point to Cambridge 0580 overview and syllabuses.
  - `core_policy` and `extended_policy` are Cambridge-style tier language.
  - Includes a `Non-calculator strategy` node, which is not a primary 4MA1 Higher paper assumption.
- `content/quadratics/items/**/*.json`
  - Many items use `source_type: cambridge_style_original`.
  - Extended items include notes such as "Original Cambridge-style item for IGCSE 0580 Extended."
- `docs/API_SPEC.md`
  - Uses `extended` and `core_repair` in API examples. This is technically usable but semantically should be redefined.

Can keep for now but rename later:
- Backend enum values `extended` and `core_repair`.
  - These are implementation labels and tests currently depend on them.
  - Recommended v1 migration: keep enum values for compatibility, but document their Edexcel meaning:
    - `extended` = Edexcel 4MA1 Higher target item.
    - `core_repair` = prerequisite repair item based on Foundation-assumed knowledge.
  - Rename to `higher` / `foundation_repair` only after API and tests are stable.

## 5. Quadratics MVP Fit

Quadratics remains a strong MVP topic for Edexcel 4MA1 Higher.

Strong fit:
- Factorising quadratics.
- Solving by factorisation.
- Quadratic formula.
- Completing the square.
- Forming and solving quadratic equations from context.
- Quadratic graphs and interpretation.

Needs staged placement for Year 10:
- Linear/quadratic simultaneous equations should be Stretch or late Phase 1 content.
- Quadratic inequalities should be Stretch or Phase 1.5 content.
- Algebraic fractions involving quadratics should be separate from the first quadratics MVP unless school sequence confirms readiness.

## 6. Year 10 Sequencing Recommendation

Use Edexcel Higher as the destination, but pace the first MVP as Year 10 appropriate.

Recommended order:

1. Prerequisite repair
   - negative numbers
   - expanding brackets
   - collecting like terms
   - solving linear equations
   - simple substitution
   - coordinates and tables of values

2. Higher target core
   - recognising quadratic standard form
   - factorising monic quadratics
   - factorising non-monic quadratics
   - difference of two squares
   - solving by factorisation

3. Transfer layer
   - same concept with changed signs
   - required form changes
   - equations not already equal to zero
   - context-to-equation translation
   - graph/algebra connection

4. Later Higher extension
   - quadratic formula
   - completing the square
   - simultaneous linear/quadratic equations
   - quadratic inequalities
   - algebraic fractions involving quadratics

## 7. Item Bank Audit Criteria

Before any new item becomes active, it should pass both existing quality gates and Edexcel alignment gates.

Required Edexcel metadata additions:
- `exam_board`: `edexcel_igcse_math_a`
- `syllabus_code`: `4MA1`
- `tier_target`: `higher`
- `paper_codes`: `["4MA1/1H", "4MA1/2H"]` when applicable
- `syllabus_refs`: e.g. `["2.4B", "2.7A"]`
- `calculator_policy`: `calculator_allowed`
- `source_style`: `edexcel_style_original`
- `year10_sequence_band`: `prerequisite_repair | core_target | transfer | stretch`
- `transfer_axis`: wording_change | sign_change | form_change | context_change | representation_change | method_choice

Do not copy raw past-paper questions into the app item bank unless licensing is explicitly cleared. Use official materials for syllabus and style calibration; write structured original items with source-style references.

## 8. CORE Purpose Fit Checks

Each item should be checked against the product purpose, not only the syllabus.

### Metacognitive Fit

Pass if:
- The item has identifiable expected solution steps.
- The item can identify at least one likely stuck point.
- Feedback helps the student name the thinking break.
- The item supports reflection or articulation when appropriate.

Fail if:
- The item only checks final-answer accuracy.
- The item cannot distinguish conceptual error from procedural slip.
- The hint ladder gives a method but not a thinking move.

### Affective Safety

Pass if:
- The student sees a specific next action.
- The wording preserves perceived control.
- Repair feels like "recover the missing link", not "go down a level."

Fail if:
- The UI or report frames the student as weak, behind, or failing.
- The system exposes too many raw metrics in the student or parent view.
- The repair path feels punitive.

### Transfer and Performance Fit

Pass if:
- The item or its follow-up variation changes representation, wording, form, or context.
- The system tracks whether the student can choose the method, not just execute a known method.
- The item aligns to 4MA1 Higher exam style and mark visibility.

Fail if:
- The item only repeats the same surface pattern.
- The student can pass by memorising a procedure without explaining why it applies.
- There is no transfer variation.

## 9. Required Fix List

Priority 0: freeze expansion
- Do not add more Cambridge-labelled content.
- Do not continue broad feature work until the source-of-truth docs are corrected.

Priority 1: source-of-truth correction
- Update `MVP_SPEC.md` to Edexcel 4MA1 Higher.
- Update `docs/DESIGN_BRIEF.md` confirmed decisions.
- Add this audit as a controlling reference.

Priority 2: concept graph correction
- Replace `exam_board` and `source_refs`.
- Add Edexcel syllabus reference coverage for quadratics.
- Reword `core_repair` policy as Foundation-assumed prerequisite repair.
- Demote or rename `exam.non_calculator_strategy`; for 4MA1 it should not drive v1.
- Add or tag nodes for Edexcel-specific Higher extensions:
  - `quadratics.simultaneous_linear_quadratic`
  - `quadratics.quadratic_inequalities`
  - `algebra.algebraic_fractions_quadratic` as later extension

Priority 3: item metadata correction
- Convert `cambridge_style_original` to `edexcel_style_original`.
- Replace Cambridge notes on all Q and CR items.
- Add Edexcel syllabus refs and Year 10 sequence bands.
- Audit Q-001 to Q-020 for Edexcel 4MA1 Higher fit.
- Audit CR-001 to CR-025 for Foundation-assumed prerequisite repair fit.

Priority 4: tests and tooling
- Add `tools/edexcel_alignment_audit.py`.
- The audit should fail on:
  - `Cambridge`
  - `0580`
  - `cambridge_style_original`
  - active items without `syllabus_refs`
  - active items without `year10_sequence_band`
  - active items with `calculator_policy` missing
- Keep backend enum migration separate to avoid destabilising the working app.

## 10. Recommended Next Phase

Next phase ID: `EDEXCEL-PIVOT-001`

Work items:

W1. Update source-of-truth docs  
Target files: `MVP_SPEC.md`, `docs/DESIGN_BRIEF.md`

W2. Update concept graph exam metadata and Edexcel quadratics references  
Target file: `content/quadratics/concept_graph.json`

W3. Extend item schema for Edexcel alignment metadata  
Target files: `schema/item.py`, possibly `app/schemas.py` only if API exposure is needed

W4. Bulk update item source metadata without changing problem bodies  
Target files: `content/quadratics/items/**/*.json`

W5. Add audit script and run existing tests  
Target file: `tools/edexcel_alignment_audit.py`

W6. After metadata passes, review the actual 20 Higher items for Edexcel style and Year 10 sequence fit.

## 11. Decision

Proceed with Edexcel pivot. Preserve the learning architecture. Treat Cambridge 0580 as a mistaken alignment assumption, not as a reason to discard the implementation.
