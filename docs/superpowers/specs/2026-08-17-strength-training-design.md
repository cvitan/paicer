# Strength Training Design

**Date:** 2026-08-17
**Status:** Phases 1-3 and 5 implemented and **verified end-to-end**
(2026-08-18). A strength workout from `examples/strength-8week.yaml` was
uploaded to Garmin Connect and fetched back: all 15 steps round-tripped
identically — four repeat groups with correct `childStepId` association,
every category/exerciseName pair preserved, `reps` resolved to
conditionTypeId 10, rest durations exact including the superset's
asymmetric 30s/75s pattern, and `weightUnit` honouring the imperial
config.

Two findings from that verification:
- paicer numbers `stepOrder` per repeat group rather than globally as
  Connect does. Garmin normalises it on upload, so this pre-existing
  divergence is harmless and needs no change.
- Plans containing strength YAML fail on older paicer versions with an
  opaque `Error: 'targetType'`, because the pre-strength step builder
  reads `step["targetType"]` unconditionally. Nothing hints that the tool
  is simply out of date.

**Phase 4 verified** (2026-08-18) against a real logged strength
activity. The inferred shape was right about the envelope
(`{activityId, exerciseSets}`), `setType: "REST"`, `repetitionCount`, and
weight being in grams (22687 g round-trips to exactly 50.0 lb). It was
wrong or incomplete in three ways, now fixed:

- `exercises` is an array of candidates. In the captured response every
  working set held three identical entries at 99.6, and the only entry
  with differing confidences was an unclassified warmup whose highest
  value was already first — so `exercises[0]` would in fact have worked.
  The parser still selects by highest `probability`, as a defensive
  choice rather than an evidenced one: nothing documents that Garmin
  sorts the array.
- `wktStepIndex` links a logged set back to its step in the planned
  workout. It was being discarded; it is the basis for planned-vs-actual
  matching and is now kept.
- Warmup and trailing blocks arrive as `UNKNOWN` with a null name, and
  `weight: 0.0` means "nothing recorded" rather than zero. Both are now
  handled.

A 33-entry real response normalises to 15 training sets. The fixture in
`tests/test_strength.py` is taken verbatim from that response.

**All five phases are now implemented and verified.**

## Goal

Add strength training to paicer as a first-class workout type: authored in
plan YAML, validated against Garmin's exercise catalog, synced to Garmin
Connect as structured `strength_training` workouts, rendered in the Markdown
and HTML plan documents, programmed by a coaching guide the plugin skills
read, and reviewed week-to-week against actual logged sets.

## Findings

These were established empirically against the author's Garmin account
before the design was settled. They are the factual basis for everything
below.

### Strength workout JSON shape

Fetched from a real strength workout ("30-Minute Blast", workoutId
1668531600) via `get_workout_by_id`.

- Sport type is `{"sportTypeId": 5, "sportTypeKey": "strength_training",
  "displayOrder": 5}`.
- Repeat groups (`RepeatGroupDTO`) behave exactly as they do for running —
  `childStepId`, `numberOfIterations`, nested `workoutSteps`.
- Work steps are `stepType: interval` with a new end condition:
  `{"conditionTypeId": 10, "conditionTypeKey": "reps"}`, and
  `endConditionValue` as the rep count.
- Work steps carry four fields no other sport uses: `category` (e.g.
  `BENCH_PRESS`), `exerciseName` (e.g. `BARBELL_BENCH_PRESS`), `weightValue`,
  and `weightUnit`.
- Work steps have `targetType: no.target`. **Rest steps have `targetType:
  null`** — not `no.target`. This asymmetry is real and is reproduced by the
  builder rather than pushed onto the plan author.
- Rest steps are `stepType: rest` with `endCondition: time`, and carry no
  `category`/`exerciseName`.
- `weightUnit` observed as `{"unitId": 9, "unitKey": "pound", "factor":
  453.59237}`. The factor is grams per unit, so Garmin's weight base unit is
  grams.

### Exercise catalog source

Garmin Connect does **not** expose the exercise catalog to authenticated API
clients. Eight candidate endpoints were probed; all returned 404 or 410:

```
/web-data/exercises/exercise_types.json          404
/web-data/exercises/en-US.json                   404
/activity-service/activity/exerciseTypes         410
/workout-service/exercise/types                  404
/workout-service/exercises                       404
/metadata-service/metadata/exercises             404
/fitnessstats-service/exercises                  404
/exercise-service/exercises                      404
```

The canonical source is the **FIT SDK profile**, shipped in the
`garmin-fit-sdk` PyPI package. It defines an `exercise_category` enum (53
values) and one `<category>_exercise_name` enum per category. 51 categories
carry exercise names (`cardio_sensors` and `unknown` do not), totalling
**1,846 exercises**.

Connect's uppercase strings are the FIT enum values uppercased, one-to-one.
This was verified against all eight category/exercise pairs in the fetched
workout, including the non-obvious ones — `PARTIAL_LOCKOUT` under
`BENCH_PRESS`, `SMITH_MACHINE_OVERHEAD_PRESS` under `SHOULDER_PRESS`. All
eight matched.

Serialized as `{CATEGORY: [EXERCISE_NAME, ...]}` the catalog is ~48 KB.

### Unverified: the `exerciseSets` response shape

`get_activity_exercise_sets()` issues `GET
/activity-service/activity/{id}/exerciseSets`. The account has **zero**
strength activities in its last 200, so the response shape could not be
observed.

The expected shape is a list of sets, each carrying an `exercises` array
(with `category` and `name`), `repetitionCount`, `weight`, and `setType` —
but this is inferred, not confirmed. **No parser is written against it until
a real response is captured.** See Phase 4.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| YAML authoring | Raw `garmin.steps`, like every other sport | Consistency; no new expansion path or concepts |
| Catalog delivery | Vendored generated JSON + regen script | No runtime dep, works offline, ships as package data |
| Validation | Fail loudly at render **and** sync | Bad names fail silently on the watch otherwise |
| Scope | Sync + rendering + coach + review, one spec | Review depth is required by the general-strength goal |
| Discovery | `paicer exercises` CLI | Works post-`pip install`, callable by the authoring skill |
| Weight | Passed through, but guide defaults to RPE | Absolute loads go stale; mirrors the cycling zone+RPE convention |
| Coach intent | General — endurance support, strength, and hypertrophy | Covers real usage, not just runner-accessory work |
| Coach location | Own guide file | `plan-authoring.md` is already 162 lines across five sports |

## Architecture

### Sport registration

`plan_utils.py`:

```python
SPORT_LABELS["strength"] = "Strength"
SPORT_EMOJI["strength"] = "🏋️"
```

`integrations/garmin.py`:

```python
SPORT_TYPES["strength"] = {
    "sportTypeId": 5,
    "sportTypeKey": "strength_training",
    "displayOrder": 5,
}
CONDITION_TYPES["reps"] = 10
```

### Step builder

`_build_exec_step` gains a strength branch, parallel to the existing `is_swim`
branch. It forwards `category`, `exerciseName`, `weightValue` and
`weightUnit` when present, and applies the rest-step rule:

- `stepType: rest` in a strength workout → `targetType: null`
- all other strength steps → `targetType` resolved from YAML as normal

Because the builder applies the rule, plan YAML omits `targetType` on
strength rest steps entirely.

`weightUnit` is derived from the configured unit system rather than written
in YAML. Pound is `{"unitId": 9, "unitKey": "pound", "factor": 453.59237}`,
confirmed. **The kilogram unit id is unknown** and is resolved in Phase 1
against a real upload — it is not guessed.

`weightValue` is accepted but omitted by default; see the coaching guide's
RPE convention.

### Catalog module

```
scripts/generate_exercises.py    # dev-only, reads garmin-fit-sdk
src/paicer/data/exercises.json   # ~48 KB, generated, committed
src/paicer/exercises.py          # lazy load, validate(), search()
```

`garmin-fit-sdk` is a **dev dependency only**. The JSON ships as package
data via `pyproject.toml`.

`exercises.py` exposes:

- `load_catalog()` — lazy, memoized
- `validate(category, name)` — returns `None` or an error string
- `search(term)` — substring match over category and name
- `humanize(name)` — `BARBELL_BENCH_PRESS` → `Barbell Bench Press`

### Validation

A `validate_strength_exercises(plan_data)` function in `plan_utils.py`,
called alongside `validate_training_days` from both `render` and `sync`, so
a typo surfaces at render time rather than at upload.

It checks three conditions, the third being the one Garmin silently ignores:

1. the category exists
2. the exercise exists
3. the exercise belongs to that category

Unknown names use `difflib.get_close_matches` for suggestions:

```
Week 3 day 2 "Upper Push": unknown exercise SQUAT/BARBELL_BACK_SQUATS
  did you mean BARBELL_BACK_SQUAT?
```

### Rendering, with consolidation

The swim step-list block is currently duplicated verbatim in
`formatters/markdown.py:84` and `formatters/html.py:274`. Adding strength
would make three copies across two files.

`extract_swim_steps` therefore generalizes to `extract_step_lines(workout)`
in `plan_utils.py`, dispatching on workout type and returning the same shape
both formatters already consume — a flat list whose items are either a
string or a `(reps, [nested strings])` tuple. Swim output is unchanged; this
is a pure refactor on the swim path, guarded by tests.

Strength lines humanize the enum and append reps, skipping rest steps
exactly as swim does:

```
3x:
  - Barbell Bench Press — 8 reps
  - Dumbbell Flye — 8 reps
- Barbell Biceps Curl — 8 reps
```

The HTML formatter's `.swim-steps` CSS class is renamed to
`.workout-steps`.

### `paicer exercises`

```
paicer exercises                    # 51 categories with counts
paicer exercises --search bench     # substring match, CATEGORY/NAME per line
paicer exercises --category SQUAT   # all exercises in one category
```

Output is one `CATEGORY/EXERCISE_NAME` per line — greppable, and cheap for
the authoring skill to call via Bash.

### Coaching guide

New file: `claude-plugin/guides/strength-coaching.md`, read by both skills
when a plan contains strength workouts. `plan-authoring.md` gains only the
`strength` row in the Workout Types table plus the YAML step pattern, with a
pointer to the new guide.

The guide covers:

- **Goal-driven programming** — strength, hypertrophy, and endurance-support
  each with their own set/rep/rest scheme and progression model
- **Split patterns** — full-body, upper/lower, push/pull/legs, body-part
- **Equipment-gated selection** — full gym, home weights, bodyweight only,
  with substitutions across tiers
- **Interaction with endurance training** — lift placement relative to key
  run sessions, volume through Base/Build/Peak/Taper. This is the part no
  general lifting reference provides and is the guide's main value.
- **Load prescription convention** — RPE in the step `description` by
  default, mirroring the existing cycling zone+RPE convention. Absolute
  `weightValue` is supported but not the documented default, because
  prescribed loads rot as the athlete gets stronger.
- **Exercise selection workflow** — choose the movement conceptually from
  general training knowledge, then `paicer exercises --search` to resolve
  the exact enum, then write it. Never guess the string.

### Interview hooks

`create-plan/SKILL.md`: `strength` joins the Q1 sports list. A conditional
block, asked only when strength is included, covers goal, equipment access,
lifting experience, and days per week. Equipment and goal both gate exercise
selection, so both are required before any programming happens.

### Review

`review_data.py` calls `get_activity_exercise_sets()` for activities whose
`typeKey` is `strength_training`, and normalizes the response into
per-exercise sets. Weight converts from grams to the configured unit system.

`review-progress/SKILL.md` gains a strength analysis section: progressive
overload across weeks, prescribed vs actual reps, stall detection, weekly
volume by movement pattern, and whether lifting is compromising key
endurance sessions.

Activity matching reuses the existing `W{week_num}: {name}` convention. No
new matching logic.

## Implementation Phases

Sequenced so the unverified parts come after the facts that unblock them.

**Phase 1 — Sync.** Sport registration, `reps` condition, step builder
fields and the rest-step `null` rule. Resolve the kilogram unit id against a
real upload. Ends with a strength workout uploaded to Connect and visually
confirmed correct.

**Phase 2 — Catalog, validation, CLI.** Regen script, vendored JSON,
`exercises.py`, `validate_strength_exercises`, `paicer exercises`.

**Phase 3 — Rendering.** `extract_step_lines` refactor (swim tests green
first), strength branch, both formatters, CSS rename.

**Phase 4 — Review.** **Blocked on a captured `exerciseSets` response.**
Requires logging one real strength session on the watch. Capture the
response, then write the parser against it.

**Phase 5 — Docs and coaching.** `docs/garmin-api.md` strength section,
`strength-coaching.md`, `plan-authoring.md` pointer, interview and review
skill hooks, strength sessions added to all four reference YAMLs.

## Testing

- Builder emits correct strength JSON: `reps` condition, `category`/
  `exerciseName` forwarded, work steps `no.target`, **rest steps `null`**
- Repeat groups nest correctly for strength
- Validation catches an unknown exercise and suggests the near match
- Validation catches a right-name-wrong-category pair
- Swim output is characterized **before** the refactor: add tests pinning
  `extract_swim_steps` output for the reference plans' swim sessions, then
  repoint those same assertions at `extract_step_lines`. They must pass
  unchanged across the rename.
- `extract_step_lines` produces expected strength lines and skips rest steps
- `paicer exercises --search` and `--category` output
- Reference YAMLs with strength sessions render without error
- Review normalization against the **captured** `exerciseSets` fixture
  (Phase 4)

## Non-Goals

- Strength as a leg within a `multisport` workout
- Percentage-of-1RM prescription and 1RM tracking
- Shorthand `exercises:` YAML authoring — explicitly rejected in favour of
  consistency with the other sports
- Automatic load progression written back into the plan YAML by review
