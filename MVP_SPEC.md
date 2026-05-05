# SUMIN STUDY MVP Spec

## 1. Product Philosophy

This program is not a tool for increasing the number of math problems solved.
It is a self-learning system that helps the student discover where their
mathematical thinking breaks down, then reconnect that broken point through
targeted repair.

Korean working definition:

> 이 프로그램은 문제 풀이량을 늘리는 도구가 아니라, 학생이 수학 문제를 풀 때 사고가 끊기는 위치를 발견하고, 그 위치를 다시 연결해주는 자가학습 시스템이다.

The core design goal is to move the student from memorized procedures toward
relational understanding, transfer, and confidence in IGCSE Mathematics.

## 2. Target Student Profile

- Year 10 IGCSE Mathematics student.
- Works hard independently but does not consistently achieve strong results.
- Likely studies by memorizing procedures without fully understanding why,
  when, or how those procedures apply.
- May have accumulated hidden misconceptions, weak prerequisite concepts, or
  exam-language interpretation issues.
- May be bilingual or Korean-dominant while taking math exams in English.

## 3. MVP Scope

The MVP should cover one unit deeply rather than many units superficially.

Recommended MVP unit:

- Quadratics

Rationale:

- Central to Year 10 IGCSE Mathematics.
- Rich prerequisite chain: linear equations, expanding brackets, factorising,
  negative numbers, graph interpretation, formula use.
- Many common misconceptions.
- Strong opportunity for visual explanation and exam-style variation.

MVP non-goal:

- Do not attempt full IGCSE syllabus coverage in v1.
- Do not prioritize large problem volume over diagnostic quality.
- Do not build BKT, CAT, IRT, or full AI tutoring as v1 dependencies.

## 4. Learning Model

The MVP learning loop is:

1. Student attempts a problem.
2. Student enters reasoning or intermediate steps.
3. System checks answer, steps, hint usage, and error pattern.
4. System identifies the likely broken point.
5. System routes the student to Core, Repair, Explore, or Stretch.
6. Student receives a short reflection prompt.
7. Weak points return through spaced review.

The program should trust behavior data more than self-report.

Useful signals:

- Accuracy
- Response time
- Hint level used
- Repeated error type
- Step where work breaks down
- Whether the student can explain the concept
- Whether transfer problems are solved
- Whether the same issue reappears after review

## 5. Mastery Vector

Do not represent mastery as one simple percentage in the MVP. Use a five-part
mastery vector.

```text
mastery(concept) = AND(
  accuracy >= 0.75,
  hint_independence,
  retention,
  transfer,
  articulation
)
```

Suggested interpretation:

- Accuracy: at least 3 of the most recent 4 relevant problems correct.
- Hint independence: recent success with no hint or only level-1 hint.
- Retention: correct again after 3-7 days.
- Transfer: correct on at least one variation problem.
- Articulation: can explain the concept or method in one short sentence.

The student-facing view should show which dimensions are ready and which are
still developing.

Example:

```text
Accuracy: ready
Hint independence: developing
Retention: not checked yet
Transfer: developing
Articulation: ready
```

## 6. Item Bank Quality Gate

A problem may enter the active MVP item bank only when all required metadata is
complete.

Required fields:

1. `concept_ids`
2. `exam_literacy_ids`
3. `prerequisite_ids`
4. `error_category_mapping`
5. `hint_ladder`
6. `expected_solution_steps`

The MVP should prefer 20 high-quality tagged problems over 100 weakly tagged
problems.

### 6.1 Concept Fields

```json
{
  "concept_ids": ["quadratics.factorising.simple"],
  "prerequisite_ids": [
    "algebra.expanding_brackets",
    "number.negative_multiplication",
    "algebra.collecting_like_terms"
  ],
  "exam_literacy_ids": [
    "command_words.show_that",
    "answer_format.factorised_form"
  ]
}
```

### 6.2 Expected Solution Steps

`expected_solution_steps` is not only a solution. It is the standard diagnostic
path used to locate the student's stuck point.

Each step should include:

- Step number
- Mathematical action
- Expected expression or result
- Diagnostic target
- Common errors

Example:

```json
{
  "expected_solution_steps": [
    {
      "step": 1,
      "action": "expand brackets",
      "expression": "x^2 + 3x + 2x + 6",
      "diagnostic_target": "expanding_brackets",
      "common_errors": [
        "multiplies only first terms",
        "drops one middle term"
      ]
    },
    {
      "step": 2,
      "action": "combine like terms",
      "expression": "x^2 + 5x + 6",
      "diagnostic_target": "collecting_like_terms",
      "common_errors": [
        "combines unlike terms",
        "drops x term"
      ]
    }
  ]
}
```

### 6.3 Alternative Paths

Students may solve validly through a different route. The MVP should allow this
without forcing one rigid method.

Optional field:

```json
{
  "accepted_alternative_paths": []
}
```

If a student's solution does not match the standard path or any accepted
alternative path but reaches a valid result, the attempt should enter an
operator review queue.

Operator workflow:

1. Review unmatched successful path.
2. Approve as valid alternative if appropriate.
3. Add it to `accepted_alternative_paths`.

This allows the item bank to evolve through real use.

## 7. Error Taxonomy

Do not collapse all wrong answers into "misconception." Use a broader error
taxonomy.

MVP categories:

1. Calculation error
2. Sign error
3. Formula memory error
4. Conceptual misunderstanding
5. Problem interpretation error
6. Strategy selection error
7. Checking or finalization error
8. Time pressure or test-taking error

Every tagged error should answer:

> Where did the student's thinking break down?

Example:

Weak diagnosis:

```text
The student got a quadratics question wrong.
```

Useful diagnosis:

```text
The student set up the quadratic correctly, but made a repeated sign error
when expanding brackets with negative coefficients.
```

## 8. Hint Ladder

The tutor should not rush to provide the answer. It should use a structured
hint ladder.

MVP hint ladder:

1. Hint 1: point to the relevant concept or representation.
2. Hint 2: suggest the first step.
3. Hint 3: identify a likely error or stuck point.
4. Hint 4: show a similar worked example or solution structure.

The final support should explain the solution structure, not merely reveal the
answer.

Hint usage is also diagnostic data. Repeated high-level hint use may indicate a
self-regulation or prerequisite issue.

## 9. Track Structure

The MVP uses four learning tracks.

| Track | Entry condition | Failure effect |
| --- | --- | --- |
| Core | Daily automatic assignment | Can lower mastery and route to Repair |
| Repair | Triggered by Core failure | Goes back through prerequisites |
| Explore | Opens after at least one Core success that day | No mastery penalty |
| Stretch | Opens after stable weekly Core performance | No mastery penalty; may inform future difficulty |

Design principle:

- Core protects progress.
- Repair protects understanding.
- Explore protects curiosity.
- Stretch protects challenge and ambition.

Explore and Stretch failures should not punish the student. They should create
useful information without increasing fear of trying.

## 10. Language and Notation Policy

The product should be built in English by default. This is a deliberate exam-readiness decision for Pearson Edexcel International GCSE Mathematics A 4MA1 Higher.

Korean may be used only as an optional support layer when it helps the student understand a concept that is otherwise blocked. Korean should not be the default UI language, the default problem language, or the default answer language.

Policy:

- Product UI: English.
- Problems and item bank content: English.
- Hints: English first; optional Korean support only when needed.
- Math terminology: English first.
- Korean: explanatory annotation, not the main answer language.
- Exam answer practice: English required.
- Command words: repeated in original English.
- Notation: Edexcel International GCSE Mathematics A style is the target style.
- Internal collaboration notes may be Korean if useful, but student-facing product assets should remain English.

Add item-level notation metadata where useful.

Example:

```json
{
  "notation_style": "igcse_standard"
}
```

If the student gives a mathematically valid answer in a Korean-school notation style, the system may mark the math as valid but should trigger a follow-up:

```text
Now rewrite this in Edexcel-style notation.
```

Important exam literacy topics:

- "Show that..."
- "Hence..."
- "Give your answer in terms of..."
- "Sketch..."
- "Describe..."
- "Interpret..."
- Units
- Rounding
- Significant figures
- Required answer form

## 11. Views

The product needs three separate views because Terry may act as both parent and
system operator.

### 11.1 Student View

Purpose:

- Support self-learning and confidence.
- Show progress without creating surveillance pressure.

Content:

- Today's Core task
- Current stuck point
- Next action
- Short reflection
- Weekly strengths and weak points

Tone:

- Direct
- Encouraging
- Specific
- Not childish

### 11.2 Parent View

Purpose:

- Help Terry support the student emotionally and academically.
- Avoid turning the system into a monitoring tool.

Content:

- Weekly patterns
- Improving areas
- Repeated stuck points
- One or two suggested support actions

Example:

```text
This week, confidence dropped when negative multiplication appeared inside
quadratic expansion. A short five-minute review of signs before the next
session would help.
```

Generation policy:

- LLM drafts the weekly parent summary.
- Terry reviews it before using it.
- Delivery happens outside the system, such as LINE or a direct conversation.
- No automatic push notification in MVP.

### 11.3 Operator View

Purpose:

- Let Terry inspect system quality and learning data.

Content:

- Raw attempts
- Item-level accuracy
- Hint usage
- Error category distribution
- Unmatched solution paths
- Item bank quality gaps
- System diagnostics

Warning:

- Operator view should not be used as parent view. The system should make this
  role distinction visible.

## 12. Success Metrics

The MVP succeeds if these four outcomes improve:

1. The student can describe weaknesses more specifically.
2. Transfer improves on variation problems.
3. Avoidance or frustration toward math study decreases.
4. Terry can separate parent mode from operator mode.

Supporting metrics:

- Fewer repeated errors in the same diagnostic category.
- Lower hint level over time for the same concept.
- Retention success after 3-7 days.
- More accurate student self-assessment before solving.
- Increased ability to explain why a method works.

## 13. Recommended Build Order

1. Create the quadratics concept and prerequisite map.
2. Define exam literacy nodes and notation policy.
3. Build the item bank schema.
4. Create 20 fully tagged MVP problems.
5. Build the step-input UI.
6. Implement answer and expression checking.
7. Implement hint ladder display.
8. Implement error-category recording.
9. Implement student progress view.
10. Implement parent weekly summary draft.
11. Implement operator review queue.
12. Add simple spaced review.

Defer:

- BKT
- CAT
- IRT calibration
- Full dynamic LLM tutoring
- Full syllabus expansion
- Gamified badge or leaderboard systems

## 14. Claude Next Task

Claude should use this spec to produce:

1. A detailed product/design brief.
2. A first site/app information architecture.
3. Initial wireframe-level screen descriptions for:
   - Student daily study screen
   - Problem solving screen
   - Hint ladder interaction
   - Weakness report
   - Parent weekly summary
   - Operator dashboard
4. A visual design direction suitable for a Year 10 IGCSE learner:
   - Calm, focused, not childish.
   - Encouraging without heavy gamification.
   - Strong emphasis on clarity, progress, and diagnosis.
   - English-first math language with optional Korean support.


