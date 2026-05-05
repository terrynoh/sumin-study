# Edexcel 4MA1 Item Quality Review

Status: v0.1 qualitative review  
Date: 2026-05-05  
Scope: Q-001 to Q-020, CR-001 to CR-025  
Target: Pearson Edexcel International GCSE Mathematics A 4MA1 Higher, Year 10 pacing

## 1. Review Conclusion

The current quadratics item bank can remain active after the Edexcel metadata pivot, with two important qualifications:

1. The first daily path should prioritise Q-001 to Q-008 and Q-015 to Q-018 before formula/completing-square stretch work.
2. Q-009 to Q-014, Q-019, and Q-020 should remain available as Stretch or later sequencing until Sumin's school sequence confirms readiness.

No item body is invalid for Edexcel 4MA1 Higher. The main risk is pacing, not syllabus mismatch.

## 2. Review Criteria

Each item was reviewed against four gates:

- Edexcel fit: aligns to 4MA1 Higher content.
- Year 10 fit: suitable for early Higher preparation or correctly marked as stretch.
- Metacognitive fit: exposes a clear thinking break, not only final-answer marking.
- Transfer/performance fit: supports changed form, changed wording, context, graph/algebra translation, or method choice.

## 3. Higher Target Items

| Item | Current band | Edexcel fit | Year 10 fit | Decision | Notes |
|---|---|---|---|---|---|
| Q-001 | core_target | 2.4B | Strong | Keep active | Basic monic factorising; good first diagnostic. |
| Q-002 | core_target | 2.4B | Strong | Keep active | Negative middle term tests sign reasoning. |
| Q-003 | core_target | 2.4B | Strong | Keep active | Mixed signs; good transfer from Q-001/Q-002. |
| Q-004 | core_target | 2.4B | Strong | Keep active | Difference of two squares is a compact structure-recognition check. |
| Q-005 | core_target | 2.7A | Strong | Keep active | Solving after factorising is central to performance transfer. |
| Q-006 | core_target | 2.4B | Moderate | Keep active | Non-monic factorising is Higher-relevant; may need repair support for early Year 10. |
| Q-007 | core_target | 2.4B | Moderate | Keep active | Good sign-placement diagnostic for non-monic factorising. |
| Q-008 | core_target | 2.4B | Moderate | Keep active | Good non-monic consolidation; watch cognitive load. |
| Q-009 | stretch | 2.4D/2.7B | Later | Keep as Stretch | Completing square is Higher, but not first-path Year 10 unless school has started it. |
| Q-010 | stretch | 2.4D/2.7B | Later | Keep as Stretch | Same as Q-009 with negative middle term. |
| Q-011 | stretch | 2.4D/3.3 | Later | Keep as Stretch | Useful representation transfer, but should follow completed-square fluency. |
| Q-012 | stretch | 2.7B | Later | Keep as Stretch | Quadratic formula is valid Higher content. |
| Q-013 | stretch | 2.7B support | Later | Keep as Stretch | Discriminant is useful formula reasoning; not a standalone first-path objective. |
| Q-014 | stretch | 2.7B | Later | Keep as Stretch | Rounding adds exam-performance value. |
| Q-015 | transfer | 2.7C/2.7A | Strong | Keep active | Context-to-equation transfer; should appear after Q-005. |
| Q-016 | transfer | 2.7C/2.7A | Strong | Keep active | Consecutive integer model is a good expression-building task. |
| Q-017 | transfer | 2.7C/2.7A | Moderate | Keep active | Uses triangle area plus quadratic; good transfer, slightly higher load. |
| Q-018 | transfer | 3.3/2.7A | Strong | Keep active | Factorised form to roots/intercepts supports graph/algebra transfer. |
| Q-019 | transfer | 3.3 | Later | Keep as Stretch | Sketching from completed-square form is useful but should follow graph features. |
| Q-020 | stretch | 2.7C/3.3 | Later | Keep as Stretch | Contextual maximum-height item is valid but high-load. |

## 4. Repair Items

| Item group | Items | Decision | Notes |
|---|---|---|---|
| Product/sum facts | CR-001, CR-002 | Keep | Directly supports monic factorising and product/sum search. |
| Sign rules | CR-003, CR-004 | Keep | Essential for factor signs and root signs. |
| Squares/roots | CR-005, CR-006 | Keep | Supports difference of squares, formula, discriminant, and graph values. |
| Expression language | CR-007, CR-008 | Keep | Strong metacognitive value: expression vs equation distinction is a common stuck point. |
| Like terms/substitution | CR-009 to CR-012 | Keep | Supports expansion, graph table values, and formula substitution. |
| Linear equation repair | CR-013, CR-014 | Keep | Supports turning factors into roots. |
| Rearranging / zero form | CR-015, CR-016 | Keep | CR-016 is especially important for Edexcel form-and-solve questions. |
| Expanding/factorising repair | CR-017 to CR-020, CR-023, CR-024 | Keep | Good prerequisite repair for non-monic, common-factor, and double-bracket checks. |
| Graph repair | CR-021, CR-022 | Keep | Supports graph interpretation transfer and table-of-values work. |
| Zero-product repair | CR-025 | Keep | Directly supports factorising-to-solving transfer. |

Repair pool concern:
- `prerequisite_ids` is currently overloaded for repair routing in some CR items. It sometimes stores the target item concept that calls the repair, not only a true prerequisite.
- Do not change this immediately because routing tests depend on it.
- Recommended v1.1 schema improvement: add `repair_called_by` or `routing_anchor_ids`, then restore `prerequisite_ids` to its literal meaning.

## 5. Tone and Affective Safety Review

Student-facing text was reviewed for deficit language. The following terms were removed from visible diagnostic/hint/step text:

- cannot
- struggle
- weak
- failing
- behind
- gap
- wrong
- mistake
- error

The replacement style uses:

- "next link"
- "step to check"
- "sign to check"
- "common slip"
- "not yet matched"

New guard:
- `tools/item_language_audit.py`

## 6. Sequencing Recommendation

First stable Year 10 daily sequence:

1. Q-001 to Q-005
2. Q-006 to Q-008
3. Q-015 to Q-018
4. Q-009 to Q-014 only after readiness signal
5. Q-019 to Q-020 as Stretch after graph/completing-square readiness

This preserves Edexcel Higher ambition without making the first experience feel like a level jump.

## 7. Remaining Recommendations

Recommended next implementation:

- Add a future `routing_anchor_ids` field for repair items.
- Add Edexcel past-paper style review after Terry provides school or past paper references.

## 9. Academic Validation Filter Update

Date: 2026-05-05

Accepted before v1 pilot:

- Added CR-023 and CR-024 for direct double-bracket expansion repair.
- Added CR-025 for the zero-product property hinge.
- Reworded procedural metacognition prompts in Q-009, Q-014, and Q-016.
- Reworked Q-013 diagnostic trigger to focus on discriminant interpretation, while keeping the item as Stretch.
- Reframed the dashboard first-message example away from "wrong last time" language.
- Marked Q-001 transfer axis as introductory rather than a transfer variation.

Deferred to v1.1:

- Broader accepted alternative solution paths.
- More step-level error mappings for multi-step Stretch items.
- CR phrasing variety after observing real repetition fatigue.
- `show that` / `hence` exam-literacy items.
- Formal `routing_anchor_ids` separation from `prerequisite_ids`.

## 8. Decision

The item bank is usable for the next product phase, provided the app respects the current sequence bands. Do not expand to new topics until the session engine uses Year 10 sequence bands deliberately.
