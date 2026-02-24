# paicer - Development TODO

## Current Status

✓ **Version 0.1 Complete**
- Phase 1 (HM Build): 6 weeks complete in `plans/hm-tri-combo.yaml`
- Clean architecture with integrations & formatters
- Garmin Connect integration working
- Markdown & HTML output working

## Upcoming Work

### 1. Complete hm-tri-combo Plan

**Phase 2 - HM Peak + Tri Overlap (7 weeks)**
- Source: `build_plan_v3.py` lines 320-424
- 4 runs + 2 swims + 1 bike per week
- Add swim sessions (appendix references from PDF)
- Add structured bike sessions
- Brick workouts (bike→run)

**Phase 3 - Triathlon Only (8 weeks)**
- Source: `build_plan_v3.py` lines 467-615
- Faithfully transcribed from RG Active PDF (pages 10-18)
- Swim Session #1-10 (PDF pages 19-20)
- Track Session #1-3 (PDF page 23)
- Open water swimming
- Race simulation sessions

**Key notes:**
- Phase 3 was previously full of errors and completely rebuilt
- Must be faithful to source PDF
- Appendix sessions referenced by number (e.g., "Swim Session #7")

### 2. Garmin Integration Enhancements

**Swimming workouts:**
- Research Garmin swim workout structure
- Add stroke types, drill steps
- Pool vs open water sessions

**Cycling workouts:**
- Power zones support
- FTP-based intervals
- Brick session structure (bike + run transition)

**Multi-sport workouts:**
- Triathlon race simulation
- Transition practice

### 3. Reviews Section
- Add a reviews section to the YAML schema, format is a the following example:
```
reviews:
  - week: 4
    date: "2026-04-15"
    notes: "HR averaged 162 during easy runs (target <145). Suggest slowing easy pace to 6:15/km."
    adjustments:
      - field: "phases[0].weeks[3].workouts[0].description"
        change: "Easy pace adjusted from 6:00 to 6:15/km"
```
- Update the CLAUDE_GUIDE.md and  schema docs to reflect it.


### 4. Agent Skill

Create an Agent Skill for interactive plan building and weekly reviews with adjustments:

**Concept:**
- Asks about current fitness, training days
- Suggests methodology (Pfitzinger, Daniels, etc.)
- Builds YAML plan interactively
- Generates and uploads workouts
- SKILL.md with iomnformation on how to coach someone through plan creation (the questions to ask, methodology knowledge), the YAML schema reference, how to use the formatters, potentially how to do Garmin sync, and how to run a weekly review (pull data, compare to plan, suggest adjustments, append to reviews section). 
- Pace adjustment based on race results
- Recovery week auto-insertion
- Taper week builder
- Race prediction calculator
- Weekly check-in prompts
- Progress tracking
- Auto-adjust paces based on actual performance


### 5. Additional Formatters

Potential output formats:
- **PDF** (reportlab, like build_plan_v3.py)
- **iCal** (.ics for Apple Calendar, Google Calendar)
- **JSON** (for API consumption)
- **CSV** (spreadsheet import)


### 6. New Integrations

Potential integrations to add:
- **Strava** (workout library)
- **Zwift** (cycling workouts)
