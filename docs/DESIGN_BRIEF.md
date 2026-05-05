# SUMIN STUDY — Design Brief v1.1

> Source of truth: `MVP_SPEC.md` (4-round consensus). This document translates
> the spec into concrete UX/UI design decisions, screen specifications, and
> implementation rules for v1 build.
>
> Version: v1.1 (2026-05-03) — incorporates self-review categories A (10) + B (4).
> Category C (responsive, a11y, font validation, error pattern UX ethics) deferred to v1.5/v2.

---

## 1. Design Principle

Every screen must serve the single core loop:

```
attempt → detect stuck point → repair → return → reflect → retain
```

If a UI element does not support a step in this loop, it is removed.

---

## 2. Visual Design Direction

### 2.1 Core Adjectives

**Focused. Honest. Specific.**

- "You don't know this yet" — direct, not aggressive
- "You broke down here, next step is this" — no vague encouragement
- Student must feel in control, not entertained

### 2.2 Forbidden Elements

- Badges, stars, leaderboards, streak counters
- Empty positivity ("Amazing!" "You're doing great!")
- Animated mascots, game metaphors
- Red color for errors (use amber instead — see 2.3)

### 2.3 Color & Typography

| Element | Direction |
|---|---|
| Background | Off-white `#F9F9F7` — reduce eye strain |
| Body text | Near-black `#1A1A1A` |
| Accent 1 (progress / success) | Muted teal `#3D7A6E` |
| Accent 2 (attention / repair) | Warm amber `#C08A3A` — NO red |
| Borders | Light gray `#E0E0DC` |
| Math rendering | KaTeX, serif math standard |
| UI font | Inter or Noto Sans (KR/EN compatibility) |
| Math display size | 1.2× body text — math is the protagonist |

Note: Final font stack KaTeX + Korean fallback validation deferred to v1.5 (Category C1).

### 2.4 Layout Principles

- **Single focus per screen** — one primary action
- **Left-to-right reading flow** — problem (left) → workspace (center) → feedback (right)
- **Vertical rhythm** — formulas, steps, hints stack vertically
- **No infinite scroll** — sessions have a clear start and end

---

## 3. Information Architecture

```
SUMIN STUDY
│
├── [STUDENT]
│   ├── Onboarding (first 3 days, see §4.1)
│   ├── Dashboard (today's session)
│   ├── Study Session
│   │   ├── Problem Screen
│   │   │   ├── Hint Ladder (overlay)
│   │   │   ├── Step Input
│   │   │   └── Post-attempt Reflection
│   │   ├── Repair Screen (auto-routed on stuck)
│   │   └── Session End Screen
│   ├── Progress (weakness report)
│   └── Review Queue (spaced review due)
│
├── [PARENT]
│   └── Weekly Summary (read-only, terry-reviewed before send)
│
└── [OPERATOR]  ← terry only
    ├── Dashboard (system overview)
    ├── Item Bank Manager
    │   ├── Problem List
    │   ├── Quality Gate Status
    │   └── Unmatched Path Review Queue
    ├── Student Data (whitelisted only — see §11.3)
    │   ├── Aggregate Metrics
    │   ├── Item-level Performance
    │   └── Error Distribution
    └── System Health
```

Role separation: student/parent/operator views accessed through distinct entry
points or role-based routing. Operator view never visible during student session.

---

## 4. Screen Specifications

### 4.0 Onboarding (First 3 Days, Cold-Start Mode)

**Loop stage:** pre-attempt orientation

**Purpose:** gather initial signal without scoring the student.

**Day-by-day:**

| Day | Mode | Mastery vector |
|---|---|---|
| 1 | Diagnostic — 5 worked examples, student follows along | Not displayed |
| 2-3 | Simple Core — full attempt flow, no Repair routing | "developing/ready" only; retention/transfer hidden as "after a few days" |
| 4+ | Normal operation | Full vector active |

Dashboard shows banner during onboarding:

> "We're getting to know how you think. Don't worry about scores yet."

Onboarding skipped if student has prior data.

---

### 4.1 Student Dashboard

**Loop stage:** retain → attempt (session start)

**Purpose:** zero decision fatigue. Today's task is immediately clear.

**Layout:**

```
┌─────────────────────────────────────────────────┐
│  SUMIN STUDY          [Progress] [Settings]     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Today's Session                                │
│  ─────────────────────────────────────          │
│                                                 │
│  CORE  (required)                               │
│  ┌───────────────────────────────────────┐      │
│  │ Factorising quadratics                │      │
│  │ Last time we worked on sign control.  │      │
│  │ Continue the next factorising link.   │      │
│  │                          [Start →]    │      │
│  └───────────────────────────────────────┘      │
│                                                 │
│  REVIEW  (due today)                            │
│  ┌───────────────────────────────────────┐      │
│  │ 2 concepts due for retention check    │      │
│  │                          [Review →]   │      │
│  └───────────────────────────────────────┘      │
│                                                 │
│  EXPLORE  (unlocks after Core)                  │
│  ┌───────────────────────────────────────┐      │
│  │ 🔒 Complete today's Core first        │      │
│  └───────────────────────────────────────┘      │
│                                                 │
│  Mastery: Factorising quadratics                │
│  Accuracy ████████░░  Hint indep. ████░░░░      │
│  Retention — not checked    Transfer — needs 1  │
│  Articulation ✓                                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Decisions:**
- Core at top; other tracks visually subordinate
- Mastery vector always visible — student knows where they are
- "Last time we worked on..." — momentum framing before specific diagnostics

---

### 4.2 Problem Solving Screen

**Loop stage:** attempt → detect stuck point

**Purpose:** capture step-by-step reasoning so the system can locate where
thinking breaks down.

**Layout:**

```
┌──────────────────────────────────────────────────────────┐
│  ← Back    Factorising quadratics    Core · Q2 of 3      │
├──────────────────────────────────────────────────────────┤
│  PROBLEM                                                 │
│  ─────────────────────────────────────────────           │
│  Factorise:                                              │
│                                                          │
│         x² + 5x + 6                                      │
│                                                          │
│  ─────────────────────────────────────────────           │
│  Before you start (asked every 3rd problem):             │
│  What method will you use? [_______________]             │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  YOUR WORK                                               │
│  ─────────────────────────────────────────────           │
│  Step 1: ________________________________________        │
│  Step 2: ________________________________________        │
│  Step 3: ________________________________________        │
│  [+ Add step]                                            │
│                                                          │
│  Final answer: ______________________________________    │
│                                                          │
│                                    [Check answer →]      │
├──────────────────────────────────────────────────────────┤
│  [Hint]  Level: none used · Using a hint is fine.        │
│  [한국어 설명 보기 ▾]  ← collapsed by default            │
└──────────────────────────────────────────────────────────┘
```

**Decisions:**

- **"Before you start" cadence (B1):** asked every 3rd Core problem, not every problem.
  Daily cadence keeps metacognitive data fresh without fatigue.
- **Step input:** final-answer-only loses stuck point location. Step capture is
  the diagnostic engine.
- **Math input mechanism (A5):** v1 uses **plain text + auto-LaTeX preview**
  (e.g. `x^2 + 5x + 6` rendered live as math). MathLive WYSIWYG editor deferred
  to v1.5. Multiple-choice / fill-in-blank format rejected for v1 — sacrifices
  solution-path freedom required for stuck-point detection.
- **Hint button:** bottom, non-pushy. "Using a hint is fine" removes guilt.
  Level shown for transparency.
- **Korean toggle (B2):** `[한국어 설명 보기]` collapsed by default. Expanding
  shows Korean annotation under English; toggle state per-session, not persisted.

---

### 4.3 Hint Ladder Interaction

**Loop stage:** attempt (when stuck)

**Purpose:** minimum hint for maximum self-solve. No premature solution-pulling.

**Layout (slide-in panel over Problem Screen):**

```
┌──────────────────────────────────────────┐
│  Hint  ·  Level 1 of 4         [✕ Close] │
├──────────────────────────────────────────┤
│                                          │
│  Think about what type of problem        │
│  this is. What algebraic structure are   │
│  you working with?                       │
│                                          │
│  [I'm still stuck → Level 2]            │
│  [Got it, let me try again →]           │
└──────────────────────────────────────────┘
```

**Hint level content structure:**

| Level | Content | Language |
|---|---|---|
| 1 | Hint at relevant concept/representation | English (optional Korean note) |
| 2 | Show only the first step | English |
| 3 | Point out a likely error | English, Korean allowed |
| 4 | Show similar worked example structure | English — structure not answer |

**Decisions:**
- After each hint, "Got it, let me try again" returns to problem
- After Level 4, "Show solution structure" displays step flow (not numerical answer)
- Hint level recorded in attempt; updates `hint_independence` per A9 rules
- Hint panel does not fully cover problem — student reads both

---

### 4.4 Repair Screen

**Loop stage:** repair → return

**Purpose:** when stuck, fetch the missing prerequisite tool. Frame as
equipment-gathering, not punishment ("장비 챙기러 간다" — round-3 consensus).

**Layout:**

```
┌──────────────────────────────────────────────────┐
│  Going back to fix something  ·  Repair          │
├──────────────────────────────────────────────────┤
│  You got stuck on:                               │
│    Factorising x² - 5x + 6                       │
│                                                  │
│  The issue looks like: sign with negatives.      │
│                                                  │
│  Let's fix the building block first:             │
│    What is (-2) × (-3) ?                         │
│                                                  │
│  [Your answer: ___]    [Submit]                  │
│                                                  │
│  After this, we'll go back to the original.      │
└──────────────────────────────────────────────────┘
```

**Behavior:**
- Triggered by Track transition rule (§9.1)
- One prerequisite problem at a time
- On correct: "Ready to retry the original?" confirmation, then return
- On incorrect: route to deeper prerequisite (recursive Repair, max depth 3)
- No mastery penalty during Repair attempts — tool, not test

---

### 4.5 Post-attempt Reflection Screen

**Loop stage:** reflect

**Purpose:** capture articulation data; build student's metacognitive habit.

**Layout:**

```
┌──────────────────────────────────────────────┐
│  Quick check                                 │
├──────────────────────────────────────────────┤
│  In one sentence, why did this method work?  │
│  [_________________________________________] │
│                                              │
│  [Skip]  [Save and continue →]              │
└──────────────────────────────────────────────┘
```

**Frequency:** only after the last correct problem of a Core session.
Reflection on every problem causes fatigue and degrades articulation data quality.

**Storage:** input goes to `reflection_log`. v1 uses keyword matching against
concept's expected explanation tokens to score `articulation` dimension.
LLM classification deferred to v2.

---

### 4.6 Review Queue Screen

**Loop stage:** retain

**Purpose:** spaced retention check. Not a new-learning session.

**Layout:**

```
┌──────────────────────────────────────────────────┐
│  Memory check                                    │
├──────────────────────────────────────────────────┤
│  3 concepts to refresh today.                    │
│  These are not new — you've seen them before.    │
│                                                  │
│  ▸ Expanding (a+b)(c+d)         · 5 days ago    │
│  ▸ Negative multiplication      · 7 days ago    │
│  ▸ Factorising x² + bx + c      · 3 days ago    │
│                                                  │
│  Each takes ~2 minutes.    [Start →]            │
└──────────────────────────────────────────────────┘
```

**Difference from Core:**
- Re-issues problems student has already solved + 1 transfer variation per concept
- No Repair routing (review failure → mark `retention=stripped`, schedule re-review)
- No Hint Ladder Level 3-4 (giving away structure defeats retention test)
- Fast pass intent — limit per concept ~2 minutes

---

### 4.7 Session End Screen (B4)

**Loop stage:** retain → next-day attempt

**Purpose:** explicit closure; surface what changed and what's next.

**Layout:**

```
┌──────────────────────────────────────────────────┐
│  Session complete  ·  24 minutes                 │
├──────────────────────────────────────────────────┤
│                                                  │
│  Today you:                                      │
│    • Solved 3 of 4 Core problems                 │
│    • Repaired one prerequisite (sign rules)      │
│    • Sign errors dropped from 5 to 1             │
│                                                  │
│  Next session focus:                             │
│    Variation problems for transfer check         │
│                                                  │
│              [Done]                              │
└──────────────────────────────────────────────────┘
```

**No streak counter, no badge, no "great job".** Specific, factual, forward-looking.

---

### 4.8 Weakness Report (Progress Screen)

**Loop stage:** reflect

**Purpose:** student sees "where my thinking breaks down".

**Layout:**

```
┌──────────────────────────────────────────────────────┐
│  My Progress                          This week ▾    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  QUADRATICS                                          │
│  ─────────────────────────────────────────           │
│                                                      │
│  Factorising (simple)                                │
│  Accuracy        ██████████  ready                   │
│  Hint indep.     ████░░░░░░  developing              │
│  Retention       ░░░░░░░░░░  not checked yet         │
│  Transfer        ███░░░░░░░  developing              │
│  Articulation    ██████████  ready                   │
│                                                      │
│  Where you break down:                               │
│  ┌──────────────────────────────────────────┐        │
│  │ Sign errors when expanding brackets      │        │
│  │ with negative coefficients.              │        │
│  │ Appeared in 4 of your last 6 attempts   │        │
│  │ on this concept.                         │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  Factorising (with coefficient of x²)               │
│  Accuracy        ████░░░░░░  developing              │
│  ...                                                 │
│                                                      │
│  Error pattern (rolling 14 days):                    │
│  Sign error          ████████░░                      │
│  Problem interpret.  ████░░░░░░                      │
│  Calculation         ██░░░░░░░░                      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Decisions:**
- No percentages in main vector — `developing/ready/not checked` only
- "Where you break down" in natural language — the system's core differentiator
- Error pattern uses **rolling 14-day window**, not cumulative — avoids
  accumulating defeat (Category C4 partial mitigation)
- No red colors anywhere

---

### 4.9 Parent Weekly Summary

**Loop stage:** retain (external support loop)

**Purpose:** equip terry to support the student. Not surveillance.

**Format (LLM-drafted, terry reviewed before send):**

```
┌──────────────────────────────────────────────────────┐
│  Weekly Summary — Week of 28 April                   │
│  For: Terry (Parent view)                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  This week Sumin worked on factorising quadratics.   │
│                                                      │
│  IMPROVING                                           │
│  She can now factorise simple quadratics without     │
│  hints in most attempts.                             │
│                                                      │
│  STILL DEVELOPING                                    │
│  Confidence drops when negative numbers appear       │
│  inside brackets. Specific and fixable, not a        │
│  general weakness.                                   │
│                                                      │
│  ONE THING THAT WOULD HELP                           │
│  A five-minute review of multiplying negative        │
│  numbers together before her next session would      │
│  likely reduce this error significantly.             │
│                                                      │
│  No action needed beyond that this week.             │
│                                                      │
│  ─────────────────────────────────────────           │
│  [Edit draft]  [Mark as sent]                        │
└──────────────────────────────────────────────────────┘
```

**Decisions:**
- Fixed three-section structure (IMPROVING / STILL DEVELOPING / ONE THING)
- No raw numbers ("4 of 6 attempts") — those belong to Operator view
- "No action needed beyond that" — discourage over-intervention
- Delivery: terry reviews draft, sends manually via LINE or conversation

---

### 4.10 Operator Dashboard

**Loop stage:** system maintenance, not learning loop

**Purpose:** terry inspects system quality and item bank.

**Layout (tabs):**

```
┌──────────────────────────────────────────────────────────┐
│  OPERATOR VIEW          [System] [Items] [Student] [Log] │
├──────────────────────────────────────────────────────────┤
│  ⚠️  Operator mode. This is not the parent view.         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [System tab]                                            │
│  Items in bank: 12 / gate-passed    8 / pending          │
│  Unmatched solution paths: 2 → [Review]                  │
│  Last session: 2026-05-03  Duration: 24 min              │
│  Parent summary: drafted, not sent                       │
│                                                          │
│  [Items tab]                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Problem ID | Concept | Gates | Accuracy | Hints  │    │
│  │ Q-001      | fact.   | ✅    | 71%      | L2 avg │    │
│  │ Q-002      | fact.   | ⚠️ missing: prerequisite_ids │  │
│  │ Q-003      | expand  | ✅    | 88%      | L1 avg │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  UNMATCHED PATHS (2)                                     │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Q-001 · Attempt #7 · 2026-05-03                  │    │
│  │ Student's path: [view steps]                      │    │
│  │ Result: correct                                   │    │
│  │ [Approve as alternative] [Flag as unusual]        │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  [Student tab — see §11.3 for whitelisted fields only]   │
│  Attempts: 47 total                                      │
│  Error distribution:                                     │
│  Sign error ████████  Strategy ████  Calc ██            │
│  → [Export aggregate CSV]                                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Decisions:**
- Top banner "this is not parent view" — prevents role confusion (round-4 consensus)
- Quality gate status uses **explicit field names** (B3): "missing: prerequisite_ids"
  not opaque "⚠️3"
- Unmatched path review surfaced at top — operator's primary maintenance task
- Student tab restricted to whitelisted fields (see §11.3)

---

## 5. Mastery Vector — Measurement Events (A7)

| Dimension | Update trigger | Calculation rule |
|---|---|---|
| `accuracy` | Every attempt | 3+ correct out of last 4 attempts on this concept |
| `hint_independence` | Every attempt | Last 1 attempt used hint level 0 or 1 |
| `retention` | Auto-scheduled review at 3 and 7 days post-mastery | Pass review → ready; fail → strip and re-schedule |
| `transfer` | Variation problem issued (system-flagged) | Correct on 1 variation problem of same concept |
| `articulation` | Post-attempt reflection submission | v1: keyword match against expected explanation tokens; v2: LLM classification |

**State transitions per dimension:** `not checked → developing → ready`.

**v1 mastery dimension stability policy** (intentional, conservative):

| Dimension | Drop behavior in v1 |
|---|---|
| `accuracy` | Auto-drops via 4-attempt rolling window — recent failures naturally lower the count |
| `hint_independence` | Based on most recent correct attempt's hint level. Recent failures alone do not drop the dimension once a recent correct exists |
| `retention` | Once a 3+ day gap between two corrects exists OR a Review passes, stays `ready` until a subsequent Review fails |
| `transfer` | Once any correct attempt uses a `transfer_variation_of`, stays `ready` |
| `articulation` | Reflects the latest reflection sample; drops to `developing` if the latest is `False` |

Rationale: v1 prioritises stability and a clear progress signal over strict regression. A student who has demonstrated transfer or retention should not lose that recognition due to a single off-day attempt. v2 may revisit per-dimension drop strictness based on observed student data.

This policy aligns with the implementation in `backend/mastery.py`.

`mastered(concept)` requires ALL 5 dimensions = `ready`.

---

## 6. Track Transition Rules (A8)

| Transition | Condition |
|---|---|
| Core → Repair | 2 consecutive incorrect on same concept OR detected `error_category` matches a prerequisite domain |
| Repair → Core | 1 prerequisite problem correct AND student confirms "ready to retry" |
| Repair → deeper Repair | Repair problem also incorrect (max depth 3, then surface to operator) |
| Explore unlock | At least 1 Core problem passed today |
| Stretch unlock | Past 7 days, at least 1 concept has all 5 mastery dimensions = ready |

Stretch and Explore failures: no mastery effect, recorded as exploration data only.

---

## 7. Hint Usage → Mastery Rules (A9)

| Hint level used | Effect on `accuracy` (if correct) | Effect on `hint_independence` |
|---|---|---|
| 0 (none) | +1 | +1 (independent) |
| 1 | +1 | +0.5 (partial) |
| 2 or 3 | +1 weighted 0.5 | 0 |
| 4 (structure shown) | not counted | 0 |
| Any level, incorrect | -1 | 0 |

Principle: hint use is not punished, but `independence` reflects it honestly.

---

## 8. AI Tutor Invocation Policy (A6)

**v1 = 100% static + rule-based.** No LLM calls in the student loop.

| Function | v1 implementation | v2 upgrade |
|---|---|---|
| Stuck point message | Match student input against `expected_solution_steps[].common_errors`; output pre-written diagnostic sentence | Dynamic LLM-generated diagnosis |
| Hint ladder content | Read directly from item's `hint_ladder` field | Adaptive hint generation |
| Repair routing | Rule: error_category → prerequisite_id mapping | Conceptual similarity from KG embedding |
| Articulation scoring | Keyword match against expected tokens | LLM classification |
| Parent weekly summary | Template-filled from aggregates | LLM-drafted (then terry-reviewed) — **earliest LLM use** |

This boundary closes v1 scope and prevents accidental LLM cost or latency
in the student loop.

---

## 9. Korean Annotation UI Policy (B2)

- Korean is annotation, not primary content
- `[한국어 설명 보기 ▾]` toggle present on Problem Screen and Hint Ladder
- Default: collapsed
- State: per-session (resets next day) — prevents Korean dependency
- Math notation: never translated; IGCSE notation only
- Command words: never translated; e.g. "Show that..." stays English with
  a footnote-style Korean gloss when toggled

---

## 10. Operator View — Student Data Whitelist (A10)

**Allowed in Operator view:**
- Aggregate metrics (accuracy %, average hint level, error distribution)
- Per-item attempt count and correct ratio
- Item quality gate status
- Unmatched solution paths (student's submitted steps for review)
- Mastery vector current state and history

**Forbidden in Operator view (or isolated to a separate "Deep dive" screen
that requires explicit confirmation each session):**
- Reflection input verbatim text (student's own sentences)
- Pre-attempt metacognition input verbatim ("What method will you use?")
- Future v2 student-tutor dialogue verbatim

Rationale: operational data ≠ personal data. Terry holding both operator and
parent roles risks unintentional exposure of the student's private expression.

---

## 11. Interaction Flow — Core Session

```
Dashboard
  └─ [Start Core →]
       └─ Problem Screen
            ├─ [Check answer →] ──→ Correct
            │                         └─ (last problem of session?)
            │                              ├─ yes → Post-attempt Reflection
            │                              │         └─ Session End Screen
            │                              └─ no  → next problem
            │
            ├─ [Check answer →] ──→ Incorrect
            │    └─ Stuck point detected (via §8 v1 static match)
            │         └─ "You got the setup right but the sign changed here."
            │              └─ [Go to Repair →]
            │                   └─ Repair Screen (§4.4)
            │                        ├─ correct → return to original
            │                        └─ incorrect → deeper Repair (max 3)
            │
            └─ [Hint →]
                 └─ Hint Ladder overlay (§4.3)
                      └─ Level 1~4 sequential
                           └─ [Got it, try again →] ──→ Problem Screen
```

---

## 12. Build Order Recommendation

Aligned with `MVP_SPEC.md §13`. Design-side dependencies:

1. **Concept + prerequisite map** (data) → unblocks all UI mastery displays
2. **Item bank schema** (data) → unblocks Problem Screen, Hint Ladder, Repair
3. **20 fully tagged MVP problems** → unblocks any meaningful student session
4. **Step-input UI + auto-LaTeX preview** (frontend) → unblocks attempts
5. **Static stuck-point matcher** (backend rule engine) → unblocks Repair routing
6. **Hint Ladder display** (frontend) → unblocks self-paced help
7. **Mastery vector tracker** (backend) → unblocks Progress screen
8. **Progress / Weakness Report** (frontend) → unblocks reflection loop
9. **Spaced review scheduler + Review Queue screen** → unblocks retention dimension
10. **Operator dashboard (Items + Unmatched paths)** → unblocks bank evolution
11. **Parent weekly summary template** (with later v2 LLM upgrade hook) → external support

Deferred (v1.5 / v2):
- LLM-driven dynamic stuck-point messages
- LLM articulation scoring
- Responsive / mobile
- Accessibility audit
- KaTeX + Korean font validation
- MathLive WYSIWYG math editor
- LLM parent summary auto-draft

---

## 13. What This Document Does NOT Cover

- API contracts and payload schemas (handled in `docs/SCHEMAS.md` — to be created by codex)
- Item bank actual JSON examples for all 20 problems (codex deliverable)
- Data persistence layer (SQLite v1 default per round-1 stack agreement)
- Authentication and role enforcement implementation (single-student MVP can defer)

---

## 14. Confirmed Decisions (updated 2026-05-05)

| Decision | Choice | Rationale / Constraint |
|---|---|---|
| Exam board | **Pearson Edexcel International GCSE Mathematics A 4MA1 Higher** | Primary path. Existing `extended` items mean Edexcel Higher target items. Existing `core_repair` items mean Foundation-assumed prerequisite repair, not a lower-course target. |
| Frontend framework | **React + Vite** | Streamlit forbidden for student-facing UI. Streamlit allowed only for operator prototypes and data inspection (`tools/operator-prototype/`). |
| Student device | **Desktop** | Mobile/tablet out of v1 scope. Layouts assume 1024×768 minimum. Keyboard input primary. Hint Ladder slide-in panel desktop viewport assumption. |
| Product language | **English-first / student-facing English** | UI, problems, hints, and reports should be produced in English by default for Edexcel International GCSE readiness. Korean is optional support annotation only, not the main product language. |
| Deployment model | **Local-first desktop web app** | v1 runs on the student desktop. Development PC creates release build; student PC runs local app/browser with local SQLite data. Online/cloud sync deferred. |
| v1 pilot launch UX | **PowerShell launcher + Windows shortcuts** | Internally transparent and debuggable, externally app-like for the student. `SUMIN STUDY` opens student view, `SUMIN STUDY Operator` opens operator view, and exe wrapper is deferred until the learning loop stabilizes. |
| Problem source pipeline | **Official Pearson Edexcel 4MA1-first** | Codex may use official public Pearson Edexcel 4MA1 materials for syllabus and style calibration. Terry-provided school/private PDFs can be added as references. App item bank should be structured Edexcel-style original content, not raw PDF copying. |

### Implications on §12 Build Order

- Step 4 "Step-input UI + auto-LaTeX preview" → React component, not Streamlit
- Item path layout: `content/quadratics/items/extended/Q-NNN.json` (main) and `content/quadratics/items/core/CR-NNN.json` (repair)
- `frontend/` directory = React + Vite project
- `tools/operator-prototype/` directory = optional Streamlit utilities

---


---

## 15. v1 Acceptance Criteria

v1 is launchable only when a single daily student session can complete all five behaviours below:

1. Attempt three Core problems.
2. Use at least one full Hint Ladder from level 1 to level 4.
3. Trigger at least one Repair branch and return to the original learning path.
4. See mastery vector changes on the Session End screen.
5. Let the Operator confirm a natural-language stuck-point sentence in the Weakness Report.

If any of these five are missing, v1 is not complete. Additional visual polish belongs to v1.1 after these behaviours work.

## 16. Onboarding Absence Handling

If the student is absent or skips the second onboarding session:

- Only the retention dimension should move back to `developing`.
- Other mastery vector dimensions should remain unchanged.
- The next attended session enters `Onboarding Day 2` mode once.
- Mastery-vector display should be simplified during that catch-up session.

## 17. Parent Summary Generation

Parent summary policy:

- v1: operator-written summary using a fixed template.
- v2: LLM-drafted summary reviewed by Terry before use.
- No automatic push notification in v1.
- Parent summary must remain supportive, not surveillance-oriented.

## 18. Deployment and Content Pipeline Notes

Deployment:

- v1 is a local-first desktop web app.
- Development happens on the build/development PC.
- Release build is copied or packaged for the student desktop.
- v1 pilot uses Windows shortcuts over transparent PowerShell launchers:
  - `SUMIN STUDY` opens the student view.
  - `SUMIN STUDY Operator` opens the operator view.
  - `Stop SUMIN STUDY` stops local services.
- Student learning data is stored locally on the student PC, preferably SQLite.
- Online hosting, account auth, and cloud sync are deferred until after v1 learning-loop validation.

Problem sources:

- Use official public Pearson Edexcel 4MA1 resources where Codex can access them.
- Use Terry-provided school/private PDFs only when explicitly supplied.
- Build the active item bank as structured English Edexcel-style original content with source references.
- Do not treat raw PDF scraping or raw past-paper copying as the app content model.
- C-003 must follow the pattern: first 5 problems, Opus quality-gate review, then remaining 15.

## Changelog

- **v1.6 (2026-05-05)** — Exam-board alignment corrected to Pearson Edexcel International GCSE Mathematics A 4MA1 Higher; `core_repair` redefined as Foundation-assumed prerequisite repair.
- **v1.5 (2026-05-04)** — §5 mastery dimension stability policy clarified; v1 conservative (no auto-drop for `retention`/`transfer`/`articulation` once `ready`); aligns spec with `backend/mastery.py`.
- **v1.4 (2026-05-03)** — Added deployment/content-source decisions (§14, §18) and FINAL REVIEW fixes: v1 acceptance criteria (§15), onboarding absence handling (§16), parent summary generation policy (§17).
- **v1.3 (2026-05-03)** — Product language decision added (§14): English-first / student-facing English; Korean only as optional support annotation.
- **v1.2 (2026-05-03)** — Confirmed decisions added (§14): exam board, framework, device. §13 "open decision" entry for framework removed.
- **v1.1 (2026-05-03)** — Self-review categories A1–A10 + B1–B4 incorporated.
  Category C deferred to v1.5/v2 with explicit notes in §2.3, §4.8, etc.
- **v1.0 (2026-05-03)** — Initial Opus draft, in-conversation only, not saved.
