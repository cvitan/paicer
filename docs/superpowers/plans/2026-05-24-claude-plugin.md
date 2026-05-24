# Claude Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package paicer's Claude Code skills as an installable npm plugin (`paicer-claude-plugin`) so users get `/paicer:create-plan` and `/paicer:review-progress` without cloning the repo.

**Architecture:** A `claude-plugin/` subdirectory contains the npm package with a `.claude-plugin/plugin.json` manifest and three skills in `skills/*/SKILL.md` format. The `plan-authoring` skill bundles the two reference YAML examples alongside it. A GitHub Actions workflow publishes to npm when a release tagged `plugin-X.Y.Z` is published.

**Tech Stack:** npm, GitHub Actions, Claude Code plugin format (markdown skills + plugin.json manifest)

---

## File Map

```
claude-plugin/
  package.json
  .claude-plugin/
    plugin.json
  skills/
    create-plan/
      SKILL.md
    review-progress/
      SKILL.md
    plan-authoring/
      SKILL.md
      examples/
        reference-metric.yaml   (copy of examples/reference-metric.yaml)
        reference-imperial.yaml (copy of examples/reference-imperial.yaml)
.github/workflows/
  publish-plugin.yml            (new, alongside existing publish.yml)
```

---

### Task 1: Plugin scaffold

**Files:**
- Create: `claude-plugin/package.json`
- Create: `claude-plugin/.claude-plugin/plugin.json`

- [ ] **Step 1: Create `claude-plugin/package.json`**

```json
{
  "name": "paicer-claude-plugin",
  "version": "0.1.0",
  "description": "Claude Code skills for paicer — create and sync training plans to Garmin Connect",
  "license": "MIT",
  "author": "Tome Cvitan",
  "homepage": "https://github.com/cvitan/paicer",
  "repository": {
    "type": "git",
    "url": "https://github.com/cvitan/paicer.git",
    "directory": "claude-plugin"
  },
  "keywords": ["claude", "paicer", "training", "garmin", "running", "triathlon"]
}
```

- [ ] **Step 2: Create `claude-plugin/.claude-plugin/plugin.json`**

```json
{
  "name": "paicer",
  "description": "Training plan skills for Claude Code: create and review Garmin-connected training plans",
  "version": "0.1.0",
  "author": {
    "name": "Tome Cvitan",
    "email": "tome.cvitan@gmail.com"
  },
  "homepage": "https://github.com/cvitan/paicer",
  "repository": "https://github.com/cvitan/paicer",
  "license": "MIT",
  "keywords": ["training", "garmin", "running", "triathlon", "paicer"]
}
```

- [ ] **Step 3: Validate both files parse as valid JSON**

```bash
node -e "require('./claude-plugin/package.json'); console.log('package.json OK')"
node -e "require('./claude-plugin/.claude-plugin/plugin.json'); console.log('plugin.json OK')"
```

Expected: both print `OK`

- [ ] **Step 4: Commit**

```bash
git add claude-plugin/
git commit -m "feat(plugin): scaffold paicer-claude-plugin npm package"
```

---

### Task 2: create-plan skill

**Files:**
- Create: `claude-plugin/skills/create-plan/SKILL.md`

- [ ] **Step 1: Create `claude-plugin/skills/create-plan/SKILL.md`**

```markdown
---
name: create-plan
description: Create or edit a paicer training plan YAML — interviews user, builds plan, syncs to Garmin
---

# Create or Edit Training Plan

Help the user create a new training plan or modify an existing one.

**Invoke the `paicer:plan-authoring` skill** for YAML structure, unit conventions, Garmin patterns, and periodization principles.

## Setup Check

Before anything else, verify paicer is installed:

- Run: `paicer version`
- If the command is not found:
  - Run: `which uv`
  - If uv is available: run `uv tool install paicer`
  - Otherwise: run `pip install paicer` (note: installs into the active Python environment — if `paicer` is still not found after this, the user may need to activate their environment or check their PATH)
- Confirm `paicer version` runs without error before continuing.

## Creating a New Plan

Interview the user **one question at a time**. Wait for each answer before asking the next.

1. What are you training for? (race distance, goal date, first time?)
2. Current fitness? (recent volume, longest recent run/ride, recent races?)
3. How many days per week, and which days?
4. What sports? (running only, triathlon, cycling?)
5. Equipment? (Garmin watch model, power meter, pool access?)
6. Current easy pace? (Adapt to their sport. Calculate race paces from any race results — don't ask them to do the math.)

If they have a Garmin watch: tell them to run `paicer sync w1` after the plan is ready — it will prompt for Garmin credentials on first use. Do NOT ask for credentials directly.

## Plan Length and Start Date

Calculate weeks until race day, then recommend:

- Standard lengths: 8, 10, 12, 16, 20 weeks (pick longest that fits)
- Minimum: 8 weeks for 5K/10K, 12 for half marathon, 16 for marathon/triathlon
- `start_date` should be a Monday, counting back from race day
- More time than needed? Start later, don't pad.

Present: "You have N weeks until race day. I'd recommend an X-week plan starting [date]." Always confirm with the user.

## Building the Plan

1. Read the appropriate reference plan from the `examples/` directory alongside this skill's `plan-authoring` skill (`examples/reference-metric.yaml` or `examples/reference-imperial.yaml`)
2. Create plan file at a path the user chooses (e.g. `~/paicer-plans/my-plan.yaml`)
3. Design phase structure (Base -> Build -> Peak -> Taper)
4. Build week-by-week with progressive volume
5. Add Garmin structures with YAML comments in user's unit system
6. Create YAML anchors for reusable sessions (swim, track)
7. Preview: `paicer render --plan <path>` (saves plan path to `~/.paicer/config`, fails loudly if YAML is invalid)
8. Offer first week sync: `paicer sync w1`
9. If Garmin set up: suggest `/paicer:review-progress` after first week of training

## Modifying an Existing Plan

1. Read plan path from `~/.paicer/config` (key: `plan`)
2. Back up: `cp my-plan.yaml my-plan.backup.yaml`
3. Make edits, preserving sequential numbering and naming conventions
4. Preview: `paicer render` to confirm the YAML is valid
5. If Garmin workouts changed, remind user to re-sync affected weeks
```

- [ ] **Step 2: Verify the file exists and has correct frontmatter**

```bash
head -5 claude-plugin/skills/create-plan/SKILL.md
```

Expected output:
```
---
name: create-plan
description: Create or edit a paicer training plan YAML — interviews user, builds plan, syncs to Garmin
---
```

- [ ] **Step 3: Commit**

```bash
git add claude-plugin/skills/create-plan/
git commit -m "feat(plugin): add create-plan skill with paicer install check"
```

---

### Task 3: review-progress skill

**Files:**
- Create: `claude-plugin/skills/review-progress/SKILL.md`

- [ ] **Step 1: Create `claude-plugin/skills/review-progress/SKILL.md`**

```markdown
---
name: review-progress
description: Compare last week's Garmin activities against the training plan and discuss adjustments
---

# Training Plan Weekly Review

Compare last week's Garmin activities against the plan and discuss adjustments.

**Invoke the `paicer:plan-authoring` skill** for unit conventions and pace conversion reference.

## Setup Check

Before anything else, verify paicer is installed:

- Run: `paicer version`
- If the command is not found:
  - Run: `which uv`
  - If uv is available: run `uv tool install paicer`
  - Otherwise: run `pip install paicer`
- Confirm `paicer version` runs without error before continuing.

## Steps

Read `units` from `~/.paicer/config` (default: `metric`). Present all values in the user's preferred system.

1. Read `plan` path from `~/.paicer/config`, then read the plan YAML using Read tool (do NOT write scripts to parse YAML).
2. Pull review data:
   ```
   uv run python -m paicer.review_data <plan_path>    # most recently completed week
   uv run python -m paicer.review_data <plan_path> 3  # specific week number
   ```
3. Match activities by `activityName` against `W{week_num}: {name}` (prefixed format from Garmin upload). Do NOT match by date — users often shift days.
4. Analyze using the `intervals` array — NOT overall activity averages. Each interval has `type` (INTERVAL_WARMUP, INTERVAL_ACTIVE, INTERVAL_RECOVERY, INTERVAL_COOLDOWN), `paceSecPerKm`, `averageHR`, `averagePower`, `distance`, `duration`.
   - **Structured workouts (tempo, intervals):** Compare INTERVAL_ACTIVE entries against targets. Overall average is misleading (includes warmup/cooldown).
   - **Easy runs:** May only have INTERVAL_ACTIVE or no intervals. Use overall average.
   - **Elevation context:** Check `elevationGain`/`elevationLoss` on every activity. Hilly runs raise HR at the same effort — don't flag elevated HR without accounting for elevation. Mention gain when it's notable (>5 m/km).
   - **Running with pace targets:** compare each INTERVAL_ACTIVE pace vs planned, note HR
   - **Running with HR targets:** compare INTERVAL_ACTIVE HR vs target zone
   - **Cycling with power targets:** compare INTERVAL_ACTIVE power vs target zone
   - **Swimming:** completion check (did the session happen?)
   - **Distance:** actual vs planned
   - **HR time in zones** (`hrTimeInZones`): Use to verify easy runs stayed in Zone 1–2. If zone 3+ time exceeds ~10% of duration on an easy run, flag it (accounting for elevation). For tempo/interval workouts, zone distribution confirms effort matched intent.
   - **Aerobic training effect** (`aerobicTrainingEffect`): 1–5 scale. Easy runs should be 2.0–3.0 ("maintaining"). Tempo/intervals 3.0–4.0 ("improving"). Long runs 3.0–4.5. Flag if an easy run scores >3.5 (too hard) or a key session scores <2.5 (too easy). Useful as a weekly load summary — sum or average across sessions to gauge overall training stress.
   - **Training status** (`trainingStatus`): Included at top level of review data. Report:
     - **Acute-to-chronic ratio**: optimal 0.8–1.5. Below 0.8 = detraining. Above 1.5 = overreaching risk. If above 1.3, note it as something to watch.
     - **Load balance feedback**: Garmin's own assessment (e.g., ABOVE_TARGETS, WITHIN_TARGETS). If above targets, discuss whether next week should be lighter.
     - **VO2max trend**: note if it changed from previous review.
     - **Training status phrase**: e.g., PRODUCTIVE, MAINTAINING, OVERREACHING. Flag non-productive states.
5. For unmatched workouts: check for other activities that might be the same workout done under a different name. Ask user to confirm before using.
6. Flag mismatches: HR too high/low at target pace, missed workouts, distance deviations.
7. Present findings conversationally. Discuss adjustments.
8. If pace adjustments agreed, update `targetValueOne`/`targetValueTwo` and descriptions in YAML.
9. Add review entry:
   ```yaml
   reviews:
     - week: N
       date: "YYYY-MM-DD"
       notes: "Summary"
       adjustments:
         - "Description of each change"
   ```

   **Notes content:** stick to training-relevant facts — pace, HR, power, distance, elevation, completion vs plan, perceived effort, weather if it affected execution, illness/injury that affected sessions. **Skip lifestyle context** like alcohol consumption, social events, work stress, or other personal details that are not training data — even when the user mentions them in chat.

10. Run `paicer render` to confirm the YAML is valid after edits.

## Race Week (special handling)

When the upcoming week contains a race, the standard review flow still applies — but **race-week conversations must lead with the HR ceiling rule, not with fueling/kit/course details.** See the "Race Strategy and Execution Priorities" section of the `paicer:plan-authoring` skill for the priority order.

The single highest-leverage piece of race-day advice is: *"Stay below the HR ceiling until the release km. Then push."* If that gets buried under gel timing, breakfast composition, and kit selection conversations, the user loses the race in execution even when training is fit. Make it the headline of every race-week message.

If the race workout has a `race_strategy:` field, surface its `one_liner` prominently in every race-week conversation.
```

- [ ] **Step 2: Verify the file exists and has correct frontmatter**

```bash
head -5 claude-plugin/skills/review-progress/SKILL.md
```

Expected:
```
---
name: review-progress
description: Compare last week's Garmin activities against the training plan and discuss adjustments
---
```

- [ ] **Step 3: Commit**

```bash
git add claude-plugin/skills/review-progress/
git commit -m "feat(plugin): add review-progress skill"
```

---

### Task 4: plan-authoring skill with bundled examples

**Files:**
- Create: `claude-plugin/skills/plan-authoring/SKILL.md`
- Create: `claude-plugin/skills/plan-authoring/examples/reference-metric.yaml`
- Create: `claude-plugin/skills/plan-authoring/examples/reference-imperial.yaml`

- [ ] **Step 1: Copy example YAML files**

```bash
mkdir -p claude-plugin/skills/plan-authoring/examples
cp examples/reference-metric.yaml claude-plugin/skills/plan-authoring/examples/
cp examples/reference-imperial.yaml claude-plugin/skills/plan-authoring/examples/
```

- [ ] **Step 2: Verify the copies are valid YAML**

```bash
python -c "import yaml; yaml.safe_load(open('claude-plugin/skills/plan-authoring/examples/reference-metric.yaml')); print('metric OK')"
python -c "import yaml; yaml.safe_load(open('claude-plugin/skills/plan-authoring/examples/reference-imperial.yaml')); print('imperial OK')"
```

Expected: `metric OK` and `imperial OK`

- [ ] **Step 3: Create `claude-plugin/skills/plan-authoring/SKILL.md`**

This is the full plan-authoring reference adapted for plugin use. Key changes from `.claude/skills/plan-authoring.md`:
- `units` from `~/.paicer/config` (not `.env`)
- Examples referenced relative to this skill's base directory
- Advanced example linked to GitHub
- `docs/garmin-api.md` linked to GitHub
- `make test` → `paicer render`
- Skill references updated to `paicer:create-plan` / `paicer:review-progress`

```markdown
---
name: plan-authoring
description: Use when creating, editing, or reviewing training plan YAML - covers structure rules, unit conventions, Garmin patterns, workout types, and periodization principles
---

# Plan Authoring

Reference for writing correct training plan YAML. Used by `/paicer:create-plan`, `/paicer:review-progress`, and ad-hoc plan edits.

> For a full real-world example (half marathon + triathlon combo plan), see [`examples/hm-tri-combo.yaml`](https://github.com/cvitan/paicer/blob/main/examples/hm-tri-combo.yaml) in the paicer repo.

## Unit System

Read `units` from `~/.paicer/config` (default: `metric`). Use for all text fields (`name`, `description`) and YAML comments on Garmin values.

Garmin steps always use metric (meters, sec/km). Add comments in the user's system: `endConditionValue: 6437  # 4 mi`.

**Imperial conventions** — use clean round numbers, not conversions:
- Runs: 3, 4, 5, 6, 8, 10, 13, 16, 20 miles
- Bikes: 10, 15, 20, 25, 40 miles
- Paces: round to nearest :15 (7:30, 7:45, 8:00/mi)
- Swim: yards for US pools (200, 500, 1000 yds)
- Track: stays in meters (400m tracks are universal)

## YAML Structure Rules

- Single `start_date` — all dates calculated from it
- Day numbers = 1-based positions in `training_days`, not weekday names
- Days must be sequential within a week (1, 2, 3... no gaps except same-day pairs)
- Non-optional workouts must not exceed `training_days` slots
- Week/day numbers sequential within their parent
- `name`: descriptive with distance/workout info (e.g., "Easy 8km", "Tempo 3x8min"). Week prefix added at Garmin sync time.

## Workout Types

| Type | Garmin Sport | Notes |
|------|-------------|-------|
| `run` | running (1) | HR zone for easy, pace targets for tempo/intervals |
| `track` | running (1) | Reusable via YAML anchors |
| `bike` | cycling (2) | See cycling target rules below |
| `swim` | swimming (4) | Lap-button cue cards with `description` per step |
| `multisport` | multi_sport (10) | `garmin.legs`, each with `sport` + `steps` |
| `race` | — | Race day entry, typically `skip_garmin: true` |

## Flags

- **`optional: true`** — shows as "Optional:" in docs, doesn't count against training_days. If it has a `garmin:` section, uploads to library without scheduling. Doesn't override `skip_garmin`.
- **`skip_garmin: true`** — no Garmin upload at all.

## Cycling Target Rules

Garmin evaluates power zone targets against 3-second average power. On undulating outdoor terrain, this causes constant out-of-zone alerts regardless of actual effort — and the visual deviation banners obscure the data screens you actually want to see. The Garmin Connect API does not support configuring a longer averaging window.

Power is still the right measurement for hard cycling intervals when a power meter is present. The fix is to keep the structured workout shape but stop letting Garmin enforce target zones on the bike. The user paces by feel + lap-average power on the data screen, and gets clean post-ride power data for analysis.

**Use `heart.rate.zone` for:**
- All steady-state / endurance cycling (single-interval rides at zone 2–3)
- Warmup and cooldown steps in steady rides
- Brick workout bike legs that are steady-state at Z2/Z3

**Use `no.target` with `description` for:**
- Any step that would otherwise have a `power.zone` target (threshold, VO2, surge intervals, hard brick blocks)
- Warmup/cooldown of structured power workouts (so the entire workout is banner-free, not just the work intervals)

**Description format (Fenix/Edge display fits ~30–40 chars cleanly):**
```
"<duration> @ Z<n> (RPE <n>)"
```
Examples: `"5 km @ Z2 (RPE 5)"`, `"6 min @ Z3 (RPE 6)"`, `"1 min @ Z5 (RPE 9)"`.

Don't include explicit watt numbers — FTP changes over time and the zone label remains correct as long as zones are kept current.

**Why HR works for steady cycling:** HR naturally smooths terrain-induced fluctuations. On a hilly loop, power spikes uphill and drops downhill, but HR stays in zone if effort is consistent. Same logic as running easy runs with HR targets. HR-targeted bike steps don't trigger banner spam because heart rate physiologically lags terrain.

**Roadmap:** for users without a power meter, the right pattern is to use `heart.rate.zone` targets across all bike steps including hard intervals. Not yet implemented — current plans assume a power meter for the bike.

## Garmin Step Patterns

Read the `examples/reference-metric.yaml` or `examples/reference-imperial.yaml` files in the `examples/` directory alongside this skill for working examples of every pattern. For the complete Garmin API reference, see [docs/garmin-api.md](https://github.com/cvitan/paicer/blob/main/docs/garmin-api.md).

**Common patterns:**
- Easy run: single `interval` step + `heart.rate.zone` zone 2
- Steady bike: single `interval` step + `heart.rate.zone` zone 2–3
- Bike intervals: `warmup` (HR zone) + `repeat` group (HR recovery + power work) + `cooldown` (HR zone)
- Tempo: `warmup` + `repeat` group (work + recovery) + `cooldown`
- Swim: `lap.button` + `description` per step, `rest` steps between sections
- Multisport: `garmin.legs` array, each leg has `sport` + `steps`
- Reusable sessions: YAML anchors in `swim_sessions:` / `track_sessions:` blocks

## Periodization Principles

- **Progressive overload:** +5-10% volume/week, recovery week every 3-4 weeks
- **Polarized intensity:** ~80% easy (RPE 4-5), ~20% hard (RPE 7-9), minimal grey zone
- **Specificity:** Training mirrors race demands as plan progresses
- **Taper:** 2-3 weeks before race, -30-50% volume, maintain intensity
- **Rest sequencing:** Rest day after long/hard sessions. Easy before hard, rest after hard/long.
- **Phase structure:** Base (aerobic) -> Build (race-specific) -> Peak (sharpening) -> Taper

## Race Strategy and Execution Priorities

**Race outcome is determined more by execution discipline than by training. Race-day decisions are not equal weight.** When advising on race week, lead with the single rule that decides 80% of the outcome: **HR ceiling discipline**.

### Priority order (by impact on finishing time)

1. **HR ceiling discipline** (saves or costs 5–15 min) — set a hard cap below LTHR, hold it religiously until the release km, push only in the final stretch
2. **Pacing strategy first 5 km** (saves or costs 3–8 min — tied to #1) — let people pass you, ignore corral pressure, run by HR not by feel
3. **Fueling** (saves or costs 2–5 min in late race) — gel timing aligned with aid stations, tested in training
4. **Kit / chafe management** (saves or costs 1–3 min from comfort) — singlet, socks, shorts all tested
5. **Hydration** (saves or costs 1–2 min) — sip at every aid station from km 8+, pour on head if warm
6. **Carb load** (saves or costs 1–2 min) — single solid carb-load day before race for HM, longer for marathon
7. **Sleep** (background factor) — bank sleep Wed/Thu; Friday night sleep matters less than people think
8. **Course strategy details** (saves or costs <1 min in good conditions) — useful color, not the main lever

### HR ceiling rule (the headline)

- **HM:** HR cap ≈ LTHR − 9 to −12 bpm. Hold until km 16 (last 5 km). Then lift cap, push by feel.
- **Marathon:** HR cap ≈ LTHR − 16 to −20 bpm. Hold until km 32 (last 10 km). Lift cap, but stay below LTHR until last 5 km.
- **10K:** HR cap ≈ LTHR − 3 to −5 bpm. Hold until km 7, push.
- **5K:** HR cap doesn't really apply — run by feel.

Race-day HR for the same pace typically runs 5–8 bpm higher than training HR. Plan for this.

**Time-to-failure at intensities near threshold:**
- At LTHR: ~60 minutes sustainable
- LTHR + 5 bpm: ~30 minutes
- LTHR + 10 bpm: ~10 minutes

This is why HM at threshold = bonk-by-km-15. Run 5+ bpm below threshold and time-to-failure extends to 3+ hours.

### `race_strategy` YAML field

For any `race` type workout, include a `race_strategy:` block. Renderers display this prominently for race week:

```yaml
- day: 6
  type: "race"
  name: "RACE: Brooklyn Half Marathon"
  skip_garmin: true
  description: "Race description, course notes, etc."
  race_strategy:
    hr_cap: 165
    cap_release_km: 16
    one_liner: "Stay below HR 165 until km 16. Then push."
    notes: |
      Hilly first 5 km (Prospect Park). Don't chase corral pace.
      Race-day HR runs 5-8 bpm above training HR — recalibrate in moment.
      Fueling: 2 SiS gels at aid stations after km 5 and km 14.
```

**Required fields:** `hr_cap`, `cap_release_km`, `one_liner`
**Optional fields:** `notes`, `target_time`, `target_pace`

### What NOT to lead with in race-week conversations

Cover these, but never let them displace the HR ceiling rule as the headline:
- Gel brand/timing minutiae, carb load gram counts, breakfast composition, kit selection, course-guide narrative

## Pace Conversion

Garmin pace values are sec/km. Convert: `5:25/km = 325 sec/km`.

To min/mi: multiply sec/km by 1.60934. Example: 325 sec/km = 523 sec/mi = 8:43/mi.

## Validation

Run `paicer render` after changes to confirm the YAML is valid.
```

- [ ] **Step 4: Verify file exists and frontmatter is correct**

```bash
head -5 claude-plugin/skills/plan-authoring/SKILL.md
```

Expected:
```
---
name: plan-authoring
description: Use when creating, editing, or reviewing training plan YAML - covers structure rules, unit conventions, Garmin patterns, workout types, and periodization principles
---
```

- [ ] **Step 5: Verify examples directory has both files**

```bash
ls claude-plugin/skills/plan-authoring/examples/
```

Expected: `reference-imperial.yaml  reference-metric.yaml`

- [ ] **Step 6: Commit**

```bash
git add claude-plugin/skills/plan-authoring/
git commit -m "feat(plugin): add plan-authoring skill with bundled reference examples"
```

---

### Task 5: npm publish workflow

**Files:**
- Create: `.github/workflows/publish-plugin.yml`

**Pre-requisite (manual, one-time):** Before the first release, add an `NPM_TOKEN` secret to the GitHub repo:
1. Go to npmjs.com → Account → Access Tokens → Generate New Token → "Automation" type
2. Go to GitHub repo → Settings → Secrets and variables → Actions → New repository secret
3. Name: `NPM_TOKEN`, value: the token from step 1

The first `npm publish` also creates the package on npm automatically — no manual npm package creation needed (unlike PyPI).

- [ ] **Step 1: Create `.github/workflows/publish-plugin.yml`**

```yaml
name: Publish plugin to npm

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    if: startsWith(github.event.release.tag_name, 'plugin-')
    steps:
      - uses: actions/checkout@v4

      - name: Verify tag matches package.json version
        run: |
          TAG="${{ github.event.release.tag_name }}"
          VERSION="${TAG#plugin-}"
          PKG_VERSION=$(node -p "require('./claude-plugin/package.json').version")
          if [ "$VERSION" != "$PKG_VERSION" ]; then
            echo "Tag '$TAG' (version '$VERSION') does not match package.json version '$PKG_VERSION'"
            exit 1
          fi

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'

      - name: Publish to npm
        run: npm publish
        working-directory: claude-plugin
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

- [ ] **Step 2: Verify the workflow file parses as valid YAML**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/publish-plugin.yml')); print('workflow OK')"
```

Expected: `workflow OK`

- [ ] **Step 3: Verify both workflows exist side by side**

```bash
ls .github/workflows/
```

Expected: `publish-plugin.yml  publish.yml`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/publish-plugin.yml
git commit -m "ci: add npm publish workflow for paicer-claude-plugin"
```
