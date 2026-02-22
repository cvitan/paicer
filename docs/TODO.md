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

### 3. New Integrations

Potential integrations to add:
- **Apple Watch / Apple Fitness**
- **TrainingPeaks**
- **Strava** (workout library)
- **Zwift** (cycling workouts)

Each implements `WorkoutIntegration` interface in `src/integrations/base.py`.

### 4. Claude Code Skill

Create a `/coach` skill for interactive plan building:

**Concept:**
```bash
/coach "I want to train for a marathon in 16 weeks"
```

Claude:
- Asks about current fitness, training days
- Suggests methodology (Pfitzinger, Daniels, etc.)
- Builds YAML plan interactively
- Generates and uploads workouts

**Implementation:**
- Create `.claude/skills/coach/` directory
- Skill prompts user for requirements
- Uses CLAUDE_GUIDE.md for methodology
- Outputs to `plans/my-plan.yaml`
- Offers to upload to Garmin

### 5. Additional Formatters

Potential output formats:
- **PDF** (reportlab, like build_plan_v3.py)
- **iCal** (.ics for Apple Calendar, Google Calendar)
- **JSON** (for API consumption)
- **CSV** (spreadsheet import)

Each implements `DocumentFormatter` interface in `src/formatters/base.py`.

### 6. Features

**Training plan features:**
- Pace adjustment based on race results
- Recovery week auto-insertion
- Taper week builder
- Race prediction calculator

**Workflow features:**
- Weekly check-in prompts
- Progress tracking
- Auto-adjust paces based on actual performance

### 7. Documentation

- Add examples for Phase 2-3 workouts once complete
- Document swim/bike workout structures
- Add troubleshooting for common issues
- Video/GIF showing Garmin sync workflow

## Reference Files

**Keep:**
- `build_plan_v3.py` - Source for Phase 2-3 data
- `rgactive_16_week_triathlon_training plan.pdf` - Source for Phase 3 details
- `integrations/garmin.md` - Technical reference
- `CLAUDE_GUIDE.md` - Workflow guide

**Removed:**
- ~~`context.md`~~ - Info moved here
- ~~`training_plan_v3.pdf`~~ - Output of build_plan_v3.py (regenerate if needed)
