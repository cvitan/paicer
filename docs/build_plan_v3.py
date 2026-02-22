from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)

# Colors
DARK = HexColor('#1a1a2e')
ACCENT = HexColor('#c0392b')
BLUE = HexColor('#2c3e50')
HEADER_BG = HexColor('#2c3e50')
ROW_ALT = HexColor('#eef2f7')
MED_GRAY = HexColor('#cccccc')
DARK_GRAY = HexColor('#666666')
TEAL = HexColor('#16a085')
LIGHT_BLUE = HexColor('#e8f4f8')
LIGHT_RED = HexColor('#fde8e8')
LIGHT_GREEN = HexColor('#e8f4e8')
LIGHT_ORANGE = HexColor('#fef3e8')

WIDTH, HEIGHT = letter
CONTENT_W = WIDTH - 1.3 * inch

doc = SimpleDocTemplate(
    "/home/claude/training_plan_v3.pdf",
    pagesize=letter,
    topMargin=0.45 * inch,
    bottomMargin=0.4 * inch,
    leftMargin=0.65 * inch,
    rightMargin=0.65 * inch,
)

# Styles
title_style = ParagraphStyle('T', fontSize=22, leading=28, textColor=DARK,
    fontName='Helvetica-Bold', spaceAfter=2)
subtitle_style = ParagraphStyle('ST', fontSize=11, leading=15, textColor=DARK_GRAY,
    fontName='Helvetica', spaceAfter=10)
phase_style = ParagraphStyle('PH', fontSize=16, leading=20, textColor=ACCENT,
    fontName='Helvetica-Bold', spaceBefore=2, spaceAfter=3)
week_style = ParagraphStyle('WK', fontSize=13, leading=17, textColor=BLUE,
    fontName='Helvetica-Bold', spaceBefore=4, spaceAfter=2)
section_style = ParagraphStyle('SEC', fontSize=11, leading=14, textColor=TEAL,
    fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=2)
body_style = ParagraphStyle('BD', fontSize=9, leading=12.5, textColor=black,
    fontName='Helvetica', spaceAfter=2)
bold_style = ParagraphStyle('BB', fontSize=9, leading=12.5, textColor=black,
    fontName='Helvetica-Bold', spaceAfter=2)
note_style = ParagraphStyle('NT', fontSize=8.5, leading=11, textColor=DARK_GRAY,
    fontName='Helvetica-Oblique', spaceAfter=2)
rule_style = ParagraphStyle('RL', fontSize=8.5, leading=11.5, textColor=DARK,
    fontName='Helvetica', spaceAfter=1, leftIndent=8)
small_style = ParagraphStyle('SM', fontSize=8.5, leading=11, textColor=DARK_GRAY,
    fontName='Helvetica', spaceAfter=2)

# Cell styles
cell_style = ParagraphStyle('CL', fontSize=7.8, leading=10.5, textColor=black,
    fontName='Helvetica', alignment=TA_LEFT)
cell_bold = ParagraphStyle('CB', fontSize=7.8, leading=10.5, textColor=black,
    fontName='Helvetica-Bold', alignment=TA_LEFT)
cell_header = ParagraphStyle('CH', fontSize=7.8, leading=10.5, textColor=white,
    fontName='Helvetica-Bold', alignment=TA_CENTER)
cell_center = ParagraphStyle('CC', fontSize=7.8, leading=10.5, textColor=black,
    fontName='Helvetica', alignment=TA_CENTER)
cell_small = ParagraphStyle('CS', fontSize=7, leading=9.5, textColor=DARK_GRAY,
    fontName='Helvetica', alignment=TA_CENTER)

story = []

def P(text, style=body_style):
    return Paragraph(text, style)


def phase1_table(sessions):
    """
    sessions: list of [name, description] — adds checkbox column
    3 columns: checkbox, session name, description
    """
    header = [P("✓", cell_header), P("Session", cell_header), P("Details", cell_header)]
    data = [header]
    for name, desc in sessions:
        data.append([
            P("", cell_center),
            P(name, cell_bold),
            P(desc, cell_style),
        ])

    cw = [0.3 * inch, 1.25 * inch, CONTENT_W - 1.55 * inch]
    t = Table(data, colWidths=cw)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.4, MED_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t


def phase2_table(sessions):
    """
    sessions: list of [name, source, description]
    4 columns: checkbox, session, source, description
    """
    header = [P("✓", cell_header), P("Session", cell_header), P("Source", cell_header), P("Details", cell_header)]
    data = [header]
    for name, source, desc in sessions:
        data.append([
            P("", cell_center),
            P(name, cell_bold),
            P(source, cell_small),
            P(desc, cell_style),
        ])

    cw = [0.3 * inch, 1.1 * inch, 0.6 * inch, CONTENT_W - 2.0 * inch]
    t = Table(data, colWidths=cw)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.4, MED_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t


# ============================================================
# COVER PAGE
# ============================================================
story.append(Spacer(1, 0.4 * inch))
story.append(P("Half Marathon → Olympic Triathlon", title_style))
story.append(P("Training Plan", title_style))
story.append(Spacer(1, 4))
story.append(P("Brooklyn Half Marathon: May 17, 2026 (B Race)  •  Olympic Triathlon: July 20, 2026 (A Race)", subtitle_style))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=2, spaceAfter=10))

story.append(P("Plan Overview", section_style))
story.append(P("<b>Phase 1 — Half Marathon Build</b> (Feb 22 – Mar 30, 6 weeks): Running-focused development using Pfitzinger methodology. 4 runs/week + 1–2 easy maintenance rides. No structured swimming.", body_style))
story.append(P("<b>Phase 2 — Overlap: HM Peak + Tri Begins</b> (Mar 31 – May 17, 7 weeks): HM-specific running continues while triathlon swim/bike sessions introduced from RG Active PDF (weeks 1–7). 4 runs + 2 swims + 1 bike per week. Tapers into race week.", body_style))
story.append(P("<b>Phase 3 — Triathlon Only</b> (May 26 – Jul 20, 8 weeks + race week): Follow RG Active PDF weeks 8–16 as written.", body_style))
story.append(Spacer(1, 6))

story.append(P("Pacing Philosophy", section_style))
story.append(P("<b>Easy runs:</b> Guided by heart rate and perceived effort. Conversational. Do not chase pace. RPE 4–5.", body_style))
story.append(P("<b>Quality sessions:</b> Guided by pace and perceived effort. Controlled, not maximal. Finish feeling you could do one more rep.", body_style))
story.append(P("<b>Pace is a target, not a test.</b> If a target feels too hard, slow down. We adjust next week.", body_style))
story.append(Spacer(1, 6))

story.append(P("Overtraining Prevention Rules", section_style))
for r in [
    "1. Maximum 2 hard sessions per week (across all disciplines during Phase 2)",
    "2. Easy days stay easy — no exceptions",
    "3. If sleep, resting HR, or appetite worsen → hold pace, reduce volume",
    "4. Do not \"prove fitness\" mid-plan — consistency beats hero workouts",
    "5. When in doubt, do less",
]:
    story.append(P(r, rule_style))
story.append(Spacer(1, 6))

story.append(P("Weekly Check-In Protocol", section_style))
story.append(P("After each week, share: average pace + HR for each run, subjective feel (easy/moderate/hard), any issues (sleep, soreness, fatigue). Garmin/Strava screenshot ideal. Paces for the following week confirmed or adjusted based on this data.", body_style))
story.append(Spacer(1, 6))

story.append(P("Where to Run", section_style))
story.append(P("<b>Reservoir (Central Park):</b> Flat — ideal for tempo/intervals where you need to hit specific paces.", body_style))
story.append(P("<b>Big Loop (Central Park):</b> Rolling hills — ideal for easy/long runs. Go by effort, not pace. Hills build strength and simulate Brooklyn Half terrain.", body_style))
story.append(Spacer(1, 6))

story.append(P("RPE Reference", section_style))
rpe_data = [
    [P("RPE", cell_header), P("Description", cell_header), P("Usage in this plan", cell_header)],
    [P("4", cell_center), P("Moderate — very happy at this effort", cell_style), P("Recovery, warm-up, cool-down", cell_style)],
    [P("5", cell_center), P("Somewhat strong — sweating, breathing harder", cell_style), P("Easy runs, long runs (early)", cell_style)],
    [P("6", cell_center), P("Strong — out of breath but maintainable for hours", cell_style), P("Steady runs, easy bike, long run pace", cell_style)],
    [P("7", cell_center), P("Very strong — laboured breathing, can hold ~1 hour", cell_style), P("Tempo runs, threshold work", cell_style)],
    [P("8", cell_center), P("Hard — struggling to hold, HR high, sweating heavily", cell_style), P("HM race pace, hard intervals", cell_style)],
    [P("9", cell_center), P("Very hard — hurting, can only hold ~5 min", cell_style), P("Short speed reps only", cell_style)],
]
rpe_t = Table(rpe_data, colWidths=[0.5*inch, 3.0*inch, 3.35*inch])
rpe_t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
    ('GRID', (0, 0), (-1, -1), 0.4, MED_GRAY),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
] + [('BACKGROUND', (0, i), (-1, i), ROW_ALT) for i in range(2, 7, 2)]))
story.append(rpe_t)

story.append(PageBreak())

# ============================================================
# PHASE 1 — ONE PAGE PER WEEK
# ============================================================

p1_header_text = "PHASE 1 — Half Marathon Build  |  Feb 22 – Mar 30"
p1_desc = "Reactivate running fitness from your marathon base. Build threshold pace progressively using Pfitzinger methodology. Easy pace will likely start around 6:00–6:15/km and should naturally come down toward 5:45–5:50/km by week 6 as fitness returns."
p1_structure = "Structure: 4 runs/week + 1–2 easy bike rides (45–60 min, RPE 5) to maintain your FTP cycling base."

phase1_weeks = [
    {
        "title": "WEEK 1 — Feb 22–28",
        "goal": "Ease back in. Establish benchmarks. Don't push.",
        "total": "~39 km running + 1–2 easy rides",
        "sessions": [
            ["Run 1 — Easy", "8 km  •  Easy/conversational  •  RPE 4–5 (~6:00–6:15/km)\nBig loop or easy route. Note natural pace and average HR — this is your baseline."],
            ["Run 2 — Tempo Intervals", "Warm-up: 2 km easy (RPE 4)  •  Main: 3 × 8 min @ 5:25/km (RPE 7)  •  Recovery: 2 min easy jog  •  Cool-down: 2 km easy (RPE 4)\n~12 km total. Reservoir for pace control."],
            ["Run 3 — Easy + Strides", "7 km easy  •  RPE 4–5  •  After: 4 × 20-sec relaxed strides (RPE 8 briefly)\nStrides are smooth accelerations, not sprints. Full recovery between each."],
            ["Run 4 — Long Run", "12 km  •  Easy/conversational  •  RPE 5\nBig loop. Finish feeling you could run another 3–4 km."],
            ["Bike (1–2×)", "45–60 min easy spin  •  RPE 5  •  No structure, just ride."],
        ]
    },
    {
        "title": "WEEK 2 — Mar 1–7",
        "goal": "Extend tempo duration. Building volume gently.",
        "total": "~44 km running + 1–2 easy rides",
        "sessions": [
            ["Run 1 — Easy", "9 km  •  Easy/conversational  •  RPE 4–5"],
            ["Run 2 — Tempo Intervals", "Warm-up: 2 km easy (RPE 4)  •  Main: 2 × 15 min @ 5:25/km (RPE 7)  •  Recovery: 3 min easy jog  •  Cool-down: 2 km easy (RPE 4)\n~13 km total. Reservoir."],
            ["Run 3 — Easy + Strides", "8 km easy  •  RPE 4–5  •  After: 5 × 20-sec strides (RPE 8 briefly)"],
            ["Run 4 — Long Run", "14 km  •  Easy  •  RPE 5"],
            ["Bike (1–2×)", "45–60 min easy spin  •  RPE 5"],
        ]
    },
    {
        "title": "WEEK 3 — Mar 8–14",
        "goal": "Introduce faster intervals. Test pace response.",
        "total": "~44 km running + 1–2 easy rides",
        "sessions": [
            ["Run 1 — Easy", "9 km  •  Easy  •  RPE 4–5"],
            ["Run 2 — Cruise Intervals", "Warm-up: 2 km easy (RPE 4)  •  Main: 4 × 1 km @ 5:15/km (RPE 7–8)  •  Recovery: 90 sec easy jog  •  Cool-down: 2 km easy (RPE 4)\n~12 km total. Reservoir. Should feel firm but controlled — not a race."],
            ["Run 3 — Easy + Strides", "8 km easy  •  RPE 4–5  •  After: 6 × 20-sec strides (RPE 8 briefly)"],
            ["Run 4 — Long Run", "15 km  •  Easy  •  RPE 5"],
            ["Bike (1–2×)", "45–60 min easy spin  •  RPE 5"],
        ]
    },
    {
        "title": "WEEK 4 — Mar 15–21",
        "goal": "Continuous tempo. Long run with a steady finish.",
        "total": "~42–43 km running + 1–2 easy rides",
        "sessions": [
            ["Run 1 — Easy", "10 km  •  Easy  •  RPE 4–5"],
            ["Run 2 — Continuous Tempo", "Warm-up: 2 km easy (RPE 4)  •  Main: 20–25 min @ 5:20/km (RPE 7)  •  Cool-down: 2 km easy (RPE 4)\n~12–13 km total. One sustained effort, no breaks. Big step up from intervals."],
            ["Run 3 — Easy + Strides", "8 km easy  •  RPE 4–5"],
            ["Run 4 — Long Run (steady finish)", "16 km total  •  First 14 km easy (RPE 5), last 2 km @ ~5:30/km (RPE 6–7)\nDon't start the faster portion too early."],
            ["Bike (1–2×)", "45–60 min easy spin  •  RPE 5"],
        ]
    },
    {
        "title": "WEEK 5 — Mar 22–28",
        "goal": "Peak Phase 1 volume. HM-specific longer intervals.",
        "total": "~50 km running + 1–2 easy rides",
        "sessions": [
            ["Run 1 — Easy", "10 km  •  Easy  •  RPE 4–5"],
            ["Run 2 — HM Intervals", "Warm-up: 2 km easy (RPE 4)  •  Main: 2 × 4 km @ 5:15/km (RPE 7–8)  •  Recovery: 3 min easy jog  •  Cool-down: 2 km easy (RPE 4)\n~14 km total. Key session of Phase 1 — sustained hard effort at near-goal pace."],
            ["Run 3 — Easy + Strides", "8 km easy  •  RPE 4–5"],
            ["Run 4 — Long Run", "18 km  •  Easy  •  RPE 5"],
            ["Bike (1–2×)", "45–60 min easy spin  •  RPE 5"],
        ]
    },
    {
        "title": "WEEK 6 — Mar 29 – Apr 3 (Sharpening / Transition)",
        "goal": "Slight volume drop. Maintain intensity. Prepare for Phase 2.",
        "total": "~44 km running + 1–2 easy rides",
        "sessions": [
            ["Run 1 — Easy", "8 km  •  Easy  •  RPE 4–5"],
            ["Run 2 — Extended Tempo", "Warm-up: 2 km easy (RPE 4)  •  Main: 30 min @ 5:15/km (RPE 7)  •  Cool-down: 2 km easy (RPE 4)\n~13 km total. 30 min continuous is a big achievement — trust the process."],
            ["Run 3 — Easy", "7 km  •  Easy  •  RPE 4–5"],
            ["Run 4 — Long Run (steady finish)", "16 km total  •  First 13 km easy (RPE 5), last 3 km @ ~5:25/km (RPE 6–7)"],
            ["Bike (1–2×)", "45–60 min easy spin  •  RPE 5"],
        ]
    },
]

for i, w in enumerate(phase1_weeks):
    story.append(P(p1_header_text, phase_style))
    story.append(P(p1_desc, body_style))
    story.append(P(p1_structure, body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=MED_GRAY, spaceBefore=2, spaceAfter=4))
    story.append(P(w["title"], week_style))
    story.append(P(f"<i>Goal: {w['goal']}</i>", note_style))
    story.append(P(f"<b>Total: {w['total']}</b>", small_style))
    story.append(Spacer(1, 4))
    story.append(phase1_table(w["sessions"]))

    # Week 6 — add success criteria
    if i == 5:
        story.append(Spacer(1, 8))
        story.append(P("End of Phase 1 — Success Criteria", section_style))
        story.append(P("☐  Tempo at 5:20–5:25/km feels controlled, not desperate", rule_style))
        story.append(P("☐  Long runs of 16–18 km leave you tired but functional next day", rule_style))
        story.append(P("☐  Easy pace has come down naturally (closer to 5:45–5:55/km)", rule_style))
        story.append(P("☐  No injuries, no illness, motivation intact", rule_style))
        story.append(Spacer(1, 4))
        story.append(P("Share your data after Week 6. Paces for Phase 2 confirmed before starting.", note_style))

    story.append(PageBreak())


# ============================================================
# PHASE 2 — ONE PAGE PER WEEK, full context on each page
# ============================================================

p2_header_text = "PHASE 2 — Overlap: HM Peak + Tri Begins  |  Mar 31 – May 17"
p2_desc = "Continue progressing HM-specific running while introducing structured swim and bike from the RG Active triathlon plan (weeks 1–7). Taper all disciplines into Brooklyn Half race day."
p2_structure = "Structure: 4 runs + 2 swims + 1 bike per week (9 sessions). ~8–10 hours/week."
p2_rule = "<b>CRITICAL RULE:</b> Maximum 2 hard sessions per week across all disciplines. Tuesday quality run = always hard #1. Hard #2 = either Saturday long run (when it has a tempo finish) or harder bike — never both. If fatigued → reduce bike first, then swim. Protect the running."

phase2_weeks = [
    {
        "title": "WEEK 1 (Tri Wk 1) — Mar 31",
        "goal": "Introduce tri sessions. Maintain Phase 1 running fitness.",
        "total": "~45 km run  •  2.5 km swim  •  20 km bike",
        "sessions": [
            ["Mon — Swim", "Tri PDF", "Tri PDF Session #2  •  1.5 km  •  Drills/Intervals  •  RPE 5–7\nFirst structured swim in months. Focus on feel, breathing, technique."],
            ["Tue — Run: Quality", "HM Plan", "Warm-up: 2 km easy (RPE 4)  •  Main: 3 × 10 min @ 5:15/km (RPE 7)  •  Recovery: 2 min jog  •  Cool-down: 2 km easy (RPE 4)\n~14 km total. Reservoir. Extending from Phase 1."],
            ["Wed — Bike", "Tri PDF", "20 km  •  RPE 5–6 steady state  •  \"Just ride\"\nFrom Tri PDF Wk 1 Sunday session."],
            ["Thu — Swim", "Tri PDF", "Tri PDF Session #1  •  1 km  •  Drills/Intervals  •  RPE 5–7\nShorter technique session."],
            ["Fri — Run: Easy", "HM Plan", "8 km  •  Easy/conversational  •  RPE 4–5"],
            ["Sat — Run: Long", "HM Plan", "17 km  •  Easy  •  RPE 5\nBig loop."],
            ["Sun — Run: Easy + Strides", "HM Plan", "7 km easy (RPE 4–5)  •  4 × 20-sec strides (RPE 8 briefly)"],
        ]
    },
    {
        "title": "WEEK 2 (Tri Wk 2) — Apr 7",
        "goal": "Push tempo duration. Swims progressing per PDF.",
        "total": "~46 km run  •  3 km swim  •  25 km bike",
        "sessions": [
            ["Mon — Swim", "Tri PDF", "Tri PDF Session #3  •  1.5 km  •  Drills/Intervals  •  RPE 5–7"],
            ["Tue — Run: Quality", "HM Plan", "Warm-up: 2 km easy (RPE 4)  •  Main: 30 min continuous @ 5:15/km (RPE 7)  •  Cool-down: 2 km easy (RPE 4)\n~13 km total. Reservoir. Sustained effort."],
            ["Wed — Bike", "Tri PDF", "25 km  •  RPE 5–7 steady  •  From Tri PDF Wk 2"],
            ["Thu — Swim + Run", "Tri PDF", "1.5 km swim (Tri PDF Session #2, RPE 5–7) + 5 km easy run (RPE 5–6)\nPer Tri PDF Wk 2 combo session."],
            ["Fri — Run: Easy", "HM Plan", "8 km  •  Easy  •  RPE 4–5"],
            ["Sat — Run: Long", "HM Plan", "18 km  •  Easy  •  RPE 5"],
            ["Sun — Run: Easy + Strides", "HM Plan", "7 km easy (RPE 4–5)  •  5 × 20-sec strides (RPE 8 briefly)"],
        ]
    },
    {
        "title": "WEEK 3 (Tri Wk 3) — Apr 14",
        "goal": "First brick week. Introduce race pace touches.",
        "total": "~47 km run  •  3.5 km swim  •  35 km bike (incl. brick)",
        "sessions": [
            ["Mon — Swim", "Tri PDF", "Tri PDF Session #4  •  2 km  •  Drills/Intervals  •  RPE 5–7"],
            ["Tue — Run: Quality", "HM Plan", "Warm-up: 2 km easy (RPE 4)  •  Main: 2 × 12 min @ 5:10/km (RPE 7–8)  •  Recovery: 3 min jog  •  Cool-down: 2 km easy (RPE 4)\n~13 km total. First time at 5:10 — should feel firm but manageable."],
            ["Wed — Bike", "Tri PDF", "20 km  •  RPE 5–7 mixed effort  •  From Tri PDF Wk 3"],
            ["Thu — Swim", "Tri PDF", "Tri PDF Session #3  •  1.5 km  •  RPE 5–7"],
            ["Fri — Run: Easy", "HM Plan", "8 km  •  Easy  •  RPE 4–5"],
            ["Sat — Run: Long (steady finish)", "HM Plan", "18 km total  •  First 15 km easy (RPE 5), last 3 km @ 5:20/km (RPE 6–7)"],
            ["Sun — BRICK", "Tri PDF", "15 km bike (RPE 5–6) → 3 km easy run (RPE 6–7)\nFrom Tri PDF Wk 3. Start the run slow — legs will feel odd."],
        ]
    },
    {
        "title": "WEEK 4 (Tri Wk 4) — Apr 21",
        "goal": "Peak quality week. Longest long run.",
        "total": "~49 km run  •  3.5 km swim  •  30 km bike",
        "sessions": [
            ["Mon — Swim", "Tri PDF", "Tri PDF Session #5  •  2 km  •  Drills/Intervals  •  RPE 5–8"],
            ["Tue — Run: Quality", "HM Plan", "Warm-up: 2 km easy (RPE 4)  •  Main: 3 × 2 km @ 5:05–5:10/km (RPE 7–8)  •  Recovery: 2 min jog  •  Cool-down: 2 km easy (RPE 4)\n~14 km total. Hardest run session in the plan. If 5:05 feels like a stretch, stay at 5:10."],
            ["Wed — Bike", "Tri PDF", "30 km  •  Intervals/hills (RPE 5–8)  •  From Tri PDF Wk 4\nThis is week's 2nd hard session. If Tuesday was tough, ride at RPE 6 steady instead."],
            ["Thu — Swim + Track", "Tri PDF", "1.5 km swim (Tri PDF Session #3, RPE 5–7) + 5 km track (Tri PDF Track Session #1, RPE 7–8)"],
            ["Fri — Run: Easy", "HM Plan", "9 km  •  Easy  •  RPE 4–5"],
            ["Sat — Run: Long", "HM Plan", "20 km  •  Easy  •  RPE 5\nPeak long run. Do not push — pure endurance."],
            ["Sun — Run: Easy + Strides", "HM Plan", "7 km easy (RPE 4–5)  •  4 × 20-sec strides (RPE 8 briefly)"],
        ]
    },
    {
        "title": "WEEK 5 (Tri Wk 5) — Apr 28",
        "goal": "Second brick. Sustained race-pace running.",
        "total": "~47 km run  •  3.5 km swim  •  35 km bike (incl. brick)",
        "sessions": [
            ["Mon — Swim", "Tri PDF", "Tri PDF Session #6  •  2 km  •  Drill/Intervals  •  RPE 5–8"],
            ["Tue — Run: Quality", "HM Plan", "Warm-up: 2 km easy (RPE 4)  •  Main: 20 min @ 5:10/km + 10 min @ 5:05/km (RPE 7–8)  •  Cool-down: 2 km easy (RPE 4)\n~14 km total. Split tempo — first block settles you, second simulates late-race push."],
            ["Wed — Bike", "Tri PDF", "20 km  •  RPE 5–7 intervals  •  From Tri PDF Wk 5"],
            ["Thu — Swim", "Tri PDF", "Tri PDF Session #2  •  1.5 km  •  RPE 5–7"],
            ["Fri — Run: Easy", "HM Plan", "8 km  •  Easy  •  RPE 4–5"],
            ["Sat — Run: Long (steady finish)", "HM Plan", "19 km total  •  First 15 km easy (RPE 5), last 4 km @ 5:15/km (RPE 6–7)"],
            ["Sun — BRICK", "Tri PDF", "15 km bike (RPE 5–6) → 3 km run (RPE 6)\nFrom Tri PDF Wk 5. Keep the run controlled."],
        ]
    },
    {
        "title": "WEEK 6 (Tri Wk 6) — May 5 (Sharpening)",
        "goal": "Volume drops. First real touches of goal pace. Stay sharp, stay fresh.",
        "total": "~42 km run  •  2 km swim  •  20 km bike",
        "sessions": [
            ["Mon — Swim", "Tri PDF", "Tri PDF Session #4  •  2 km  •  RPE 5–7\nOnly 1 swim this week — keep it moderate."],
            ["Tue — Run: Quality", "HM Plan", "Warm-up: 2 km easy (RPE 4)  •  Main: 4 × 1 km @ 5:00–5:05/km (RPE 8)  •  Recovery: 90 sec jog  •  Cool-down: 2 km easy (RPE 4)\n~12 km total. First time touching 5:00/km. Fast but not desperate. If 5:00 feels like a sprint, run at 5:05."],
            ["Wed — Bike", "Tri PDF", "20 km  •  RPE 5–6 easy  •  Reduced from PDF Wk 6"],
            ["Thu — Rest or Swim", "—", "Listen to your body. If fresh, easy 30 min swim (RPE 4–5). If tired, rest."],
            ["Fri — Run: Easy", "HM Plan", "7 km  •  Easy  •  RPE 4–5"],
            ["Sat — Run: Long (moderate)", "HM Plan", "16 km total  •  First 13 km easy (RPE 5), last 3 km @ 5:20/km (RPE 6–7)"],
            ["Sun — Run: Easy", "HM Plan", "6 km easy  •  RPE 4–5  •  Strides optional"],
        ]
    },
    {
        "title": "WEEK 7 — May 12 (RACE WEEK)",
        "goal": "Taper everything. Arrive rested, sharp, confident.",
        "total": "~16–19 km running pre-race  •  light swim/bike",
        "sessions": [
            ["Mon — Swim", "Tri PDF", "Easy 1.5 km  •  RPE 4–5  •  Technique focus. Loosen up."],
            ["Tue — Run: Sharpener", "HM Plan", "8 km total  •  Warm-up: 2 km easy (RPE 4)  •  Main: 3 × 3 min @ 5:05/km (RPE 7–8)  •  Recovery: 2 min jog  •  Cool-down: 2 km easy (RPE 4)\nShort, sharp — remind your legs what race pace feels like."],
            ["Wed — Bike", "Tri PDF", "15 km easy spin  •  RPE 5  •  Just keep the legs moving."],
            ["Thu — Run: Easy", "HM Plan", "5 km  •  Very easy  •  RPE 4\nGentle shakeout."],
            ["Fri — Rest", "—", "Complete rest. Hydrate, eat well, sleep."],
            ["Sat — Shakeout (optional)", "—", "20–30 min easy walk or 3 km very easy jog (RPE 3–4). Or rest."],
            ["Sun — RACE DAY", "RACE", "<b>Brooklyn Half Marathon — May 17</b>\nStart: 5:10–5:15/km through Prospect Park (RPE 7). Settle: 5:05–5:10/km on flat (RPE 7–8). At 15 km: if controlled, push toward 5:00/km (RPE 8+). Do NOT start at goal pace."],
        ]
    },
]

for w in phase2_weeks:
    story.append(P(p2_header_text, phase_style))
    story.append(P(p2_desc, body_style))
    story.append(P(p2_structure, body_style))
    story.append(P(p2_rule, body_style))
    story.append(Spacer(1, 3))

    # Weekly template table
    tw = CONTENT_W / 7
    template_data = [
        [P("MON", cell_header), P("TUE", cell_header), P("WED", cell_header), P("THU", cell_header), P("FRI", cell_header), P("SAT", cell_header), P("SUN", cell_header)],
        [P("Swim\n(Tri PDF)", cell_center), P("Run\nQuality", cell_center), P("Bike\n(Tri PDF)", cell_center), P("Swim\n(Tri PDF)", cell_center), P("Run\nEasy", cell_center), P("Run\nLong", cell_center), P("Run Easy\nor Brick", cell_center)],
    ]
    tmpl = Table(template_data, colWidths=[tw]*7)
    tmpl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('BACKGROUND', (0, 1), (0, 1), LIGHT_BLUE),
        ('BACKGROUND', (1, 1), (1, 1), LIGHT_RED),
        ('BACKGROUND', (2, 1), (2, 1), LIGHT_GREEN),
        ('BACKGROUND', (3, 1), (3, 1), LIGHT_BLUE),
        ('BACKGROUND', (4, 1), (4, 1), LIGHT_ORANGE),
        ('BACKGROUND', (5, 1), (5, 1), LIGHT_RED),
        ('BACKGROUND', (6, 1), (6, 1), LIGHT_ORANGE),
        ('GRID', (0, 0), (-1, -1), 0.4, MED_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(tmpl)

    story.append(HRFlowable(width="100%", thickness=1, color=MED_GRAY, spaceBefore=2, spaceAfter=3))
    story.append(P(w["title"], week_style))
    story.append(P(f"<i>Goal: {w['goal']}</i>", note_style))
    story.append(P(f"<b>Total: {w['total']}</b>", small_style))
    story.append(Spacer(1, 3))
    story.append(phase2_table(w["sessions"]))
    story.append(PageBreak())


# ============================================================
# PHASE 3 — Week-by-week
# ============================================================

p3_header_text = "PHASE 3 — Triathlon Only  |  May 26 – Jul 20"
p3_desc = "Follow the RG Active triathlon plan from Week 8 through race day. Your half marathon running fitness carries forward — tri runs are shorter (5–10 km) but with more intensity and brick work. Open water swimming begins in Week 2."
p3_rule = "<b>KEY NOTES:</b> New strength program (2a/2b) starts this phase. Test all race kit by Week 6 (Jun 30). Week 5 is peak volume (114.5 km) — prioritise sleep and recovery nutrition. Refer to Tri PDF appendix for swim session breakdowns and strength program details."

# Recovery Week page
story.append(P(p3_header_text, phase_style))
story.append(P(p3_desc, body_style))
story.append(P(p3_rule, body_style))
story.append(HRFlowable(width="100%", thickness=1, color=MED_GRAY, spaceBefore=2, spaceAfter=4))
story.append(P("Recovery Week  |  May 18–25", week_style))
story.append(P("3–5 days of easy, unstructured movement after the half marathon. Walk, gentle spin, easy swim. No intervals, no structure. Let your body absorb the race effort. If something is sore, rest it. If you feel good by Thursday/Friday, a 20–30 min easy swim or spin is fine.", body_style))
story.append(Spacer(1, 6))
recovery_sessions = [
    ("Mon", "Rest or walk. Race recovery day."),
    ("Tue", "Rest or gentle 20 min walk."),
    ("Wed", "Optional: 20–30 min easy spin @RPE 4. Keep it very light."),
    ("Thu", "Optional: 20–30 min easy swim — relaxed laps, no drills. @RPE 4."),
    ("Fri", "Rest or gentle walk/stretch."),
    ("Sat", "Optional: 30 min easy ride @RPE 4–5. Loosen the legs."),
    ("Sun", "Rest. Prepare for Phase 3 start on Monday."),
]
story.append(phase1_table(recovery_sessions))
story.append(Spacer(1, 8))
story.append(P("<b>Triathlon Race Strategy (July 20)</b>", section_style))
story.append(P("<b>Swim (1.5 km):</b> Start steady, find rhythm, sight every 4–6 strokes. Draft if possible. RPE 7.", body_style))
story.append(P("<b>Bike (40 km):</b> Your strength. RPE 7–8 but stay controlled — save legs for the run. Stay aero, hydrate.", body_style))
story.append(P("<b>Run (10 km):</b> First 2 km will feel strange. Start RPE 6–7, settle, build to RPE 8 over second half.", body_style))
story.append(PageBreak())

# Phase 3 week data — faithfully transcribed from RG Active PDF pages 10-18
# NOTE: 9 PDF weeks (8-16) fit into 8 calendar weeks. Weeks 15 (taper) and 16
# (race week) are merged into a single final week (Jul 14-20) using Wk 16's
# race-week schedule, since Wk 16 is specifically designed for race-day lead-in.
phase3_weeks = [
    {
        "num": 1, "tri": 8, "dates": "May 26 - Jun 1",
        "title": "Week 1 (Tri PDF Wk 8)  |  May 26 \u2013 Jun 1  |  89 km total",
        "goals": "Two months in \u2014 maintain harder efforts for longer and more consistently. New strength program (2a/2b). Start thinking about hydration and fuelling for longer rides. Consider day-to-day and recovery nutrition.",
        "sessions": [
            ("Mon: Swim 2.5 km", "Swim Session #7 (Drill/Pacing). When using paddles, they slow your cadence so you can focus on stroke technique. Holding harder efforts for longer; shorter sprints for speed."),
            ("Tue: Bike 25 km", "Intervals. 5 km warm up @RPE 4\u20135. Main set: 1 min @RPE 5, 6 min @RPE 6, 1 min @RPE 7, 1 min @RPE 8, 1 min @RPE 9. Repeat until 23 km. 2 km @RPE 4. <i>Outdoor option:</i> 50 min as 5 min @RPE 5 / 5 min @RPE 7. RPE 6 = sustainable moderate pace; RPE 8 = threshold/race pace; RPE 9 = unsustainable beyond ~1 min."),
            ("Wed: Strength + Run 5 km", "Strength Program 2a (new program \u2014 take time to learn exercises before increasing difficulty). Run: Track Session #1 (1\u00d71600 m, 2\u00d7800 m, 4\u00d7400 m). Aim to better times from last time you did this session."),
            ("Thu: REST", "Full rest day."),
            ("Fri: Strength + Swim 2.5 km", "Strength Program 2b. Swim Session #8 (TT/Pacing). If using a swim watch or pace clock, you should see improvements in speed and ability to hold speed for longer."),
            ("Sat: Run 9 km", "Long steady run @RPE 5\u20136. Pace should be kept well within comfort. Focus on holding pace for whole duration. Good benchmark for base pace after 2 months of training \u2014 use this to pace longer runs for the rest of the program."),
            ("Sun: Bike 45 km", "Hills. Steady state with hills included. Maintain steady cadence and rhythm. Pace judgement on climbs. Riding uphill increases strength; learning to descend confidently will be valuable."),
        ],
    },
    {
        "num": 2, "tri": 9, "dates": "Jun 2 - Jun 8",
        "title": "Week 2 (Tri PDF Wk 9)  |  Jun 2 \u2013 Jun 8  |  70.5 km total",
        "goals": "\"Time Trial\" week \u2014 test progress and set race target pace. Any new kit (goggles, trainers, elastic laces, bike shoes, tri suit) must be tested in training. Open water competency is a massive factor for race day.",
        "sessions": [
            ("Mon: Swim 2.5 km", "Swim Session #7 (Drill/Intervals). Swim the first 1 km of the main set as a straight Time Trial for a race-pace time \u2014 good progress marker. Resume second km as normal interval breakdown. When breathing, keep one eye in the water and lead hand out front."),
            ("Tue: Bike 20 km", "Time Trial. 1 km warm up @RPE 5. Then aim to hit threshold speed for the rest of the distance. Easy leg spin to cool down. Flat route preferred; also suitable for turbo/gym bike. Tests how well you can hold goal race pace."),
            ("Wed: Swim 2 km + Run 10 km", "Swim Session #4 (Intervals/Steady). Run: Aim for your fastest sustainable pace for 10 km @RPE 8. Best effort 'test' \u2014 may be slower than race-day target but gives rough idea of progress and whether target time is realistic."),
            ("Thu: REST", "Full rest day."),
            ("Fri: Strength + Run 5 km", "Strength Program 2a. Run: Track Session #1 (1\u00d71600 m, 2\u00d7800 m, 4\u00d7400 m). Aim to hit the 800s at 5 sec/lap faster than the 1600, and the 400s another 3\u20135 sec/lap quicker. Each repeated distance must be consistent."),
            ("Sat: Swim 1 km (OWS)", "<b>First open water swim!</b> First goal: ensure proper wetsuit fitting and spend time acclimatising to the water (may be colder early season). Cover distance aiming to swim smoothly, keeping good technique. Practice sighting. Practice breathing to weaker side."),
            ("Sun: Brick 25 km + 5 km", "Negative split. Complete first half of each discipline at steady tempo @RPE 6, building into race pace @RPE 8 for last half. Play with position on bars for flat &amp; climbing. Use gears to keep cadence smooth. Learning to run a negative split out of transition helps pacing."),
        ],
    },
    {
        "num": 3, "tri": 10, "dates": "Jun 9 - Jun 15",
        "title": "Week 3 (Tri PDF Wk 10)  |  Jun 9 \u2013 Jun 15  |  94.5 km total",
        "goals": "Test new kit in training. Open water competency building \u2014 massive factor for comfort and confidence on race day. Practice getting wetsuit on/off and warming up quickly so it\u2019s routine on race day. Consider goggle choice for weather/lighting.",
        "sessions": [
            ("Mon: Swim 2.5 km", "Swim Session #8 (Drills/Intervals). Count strokes per length to check technique \u2014 if count increases, you\u2019re losing efficiency or fatiguing. When breathing, keep one eye in the water, lead hand out front until recovery arm is coming forward."),
            ("Tue: Bike 25 km", "Intervals. Incremental set: 8 km @RPE 5, 8 km @RPE 7, 8 km @RPE 8\u20139. 1 km cool down. Increasing work rate and learning to pace near/above threshold. Suitable for turbo/indoor trainer. If outdoors, aim to raise average HR by 5\u201310 bpm every 10 km."),
            ("Wed: Strength + Run 10 km", "Strength Program 2a. Run: Sub-max steady @RPE 6. Aim for comfortable good run form with minimal changes in HR. Can do as off-road run with minimal undulation. Warm up with foam rolling &amp; mobility for better run form."),
            ("Thu: REST", "Full rest day."),
            ("Fri: Strength + Run 5.5 km", "Strength Program 2b. Run: Fartlek \u2014 random intervals on a route of your choosing. Average pace ~@RPE 6, with time spent between RPE 5\u20139. Good session to do with a friend (take turns calling sprints/efforts)."),
            ("Sat: Swim 1.5 km (OWS)", "Open water. Developing confidence and skills. Fit wetsuit properly, acclimatise, relax stroke, focus on breathing. Start adding sighting every 2\u20134 breaths. Join a group if possible for coaching points. @RPE 6\u20137."),
            ("Sun: Bike 50 km", "Hills. Head out on a route @RPE 6. Plan some hills for harder work intervals. Good pacing on hills is important \u2014 too easy and you lose time, too hard and you\u2019ll be slower on the flats."),
        ],
    },
    {
        "num": 4, "tri": 11, "dates": "Jun 16 - Jun 22",
        "title": "Week 4 (Tri PDF Wk 11)  |  Jun 16 \u2013 Jun 22  |  84.5 km total",
        "goals": "Endurance improvements should be clear \u2014 hold higher efforts for longer. Use hill sessions for power and control. Keep improving open water skills &amp; confidence. Throw in a quick transition practice after OWS (wetsuit off quickly while moving, running after swim).",
        "sessions": [
            ("Mon: Swim 2.5 km", "Swim Session #7 (Drills/Intervals). Pace control \u2014 aim to repeat pace of each set. Maintain alignment and form even on harder/shorter sets. Losing technique makes you slower."),
            ("Tue: Bike 30 km", "Hills. Use a hilly route or one good climb (>3 min ascent). Mix seated and standing climbing, keep rhythm. Get used to descending too. Plan a 5\u20138 km loop around one hill and repeat if no hilly route available."),
            ("Wed: Swim 2 km + Run 7.5 km", "Swim Session #5 (Intervals). Run: Track Session #3 (1\u00d71200 m, 3\u00d7400 m, 1\u00d71200 m, 3\u00d7400 m, 1\u00d71200 m, 3\u00d7400 m = 7600 m total). Sets of same distance should be repeated at the same speed/time. Aim to beat times from previous attempts. Longer sets closer to goal race pace; shorter sets faster."),
            ("Thu: REST", "Full rest day."),
            ("Fri: Strength + Run 5 km", "Strength Program 2b. Run: Steady tempo @RPE 7. Focus on run form and posture. Aim to keep 1 km splits as similar as possible. Ensure hydrated; practice with race-day energy products."),
            ("Sat: Swim 1.5 km (OWS)", "Open water. Practice sighting, adapting stroke to wetsuit and open water. Slow cadence and work with buoyancy of suit. Break session into adaptation time, then finish with 400\u2013500 m hard effort @RPE 7. Focus on controlling breathing (often first to go in cold open water)."),
            ("Sun: Brick 30 km + 5 km", "Option 1: Split into two mini-bricks of 15 km/2.5 km for more transition practice and speed work. Option 2: Complete through once at race pace. Experiment with aero positions (hoods, drops). @RPE 7\u20138."),
        ],
    },
    {
        "num": 5, "tri": 12, "dates": "Jun 23 - Jun 29",
        "title": "Week 5 (Tri PDF Wk 12)  |  Jun 23 \u2013 Jun 29  |  114.5 km total  \u2605 PEAK VOLUME",
        "goals": "Largest volume week \u2014 ensure sufficient fuelling and recovery/sleep. Stick to distance increases as best you can. Familiar sessions should show noticeable improvements. Tweak sessions (e.g. swims) to work on weaker areas if confident.",
        "sessions": [
            ("Mon: Swim 2.5 km", "Swim Session #8 (Drills/Intervals). Keep body position in mind \u2014 legs high in the water. Think about rotation through hips and forearm position on catch."),
            ("Tue: Bike 35 km", "Intervals. 5\u00d75 format: 10 min warm up @RPE 5. Then: 5 min @RPE 6, 5 min @RPE 8\u20139. Repeat until 3\u20135 km to go, warm down @RPE 4\u20135. Suitable for turbo or outside. Outdoors: plan a route for loops or out-and-back."),
            ("Wed: Strength + Run 10 km", "Strength Program 2a. Run @RPE 6\u20139: break into 4\u00d72.5 km at RPE 6\u21928\u21927\u21929. Working at RPE 9 towards end will feel very tough but is good race-day prep and mental prep for working hard."),
            ("Thu: REST", "Full rest day."),
            ("Fri: Strength + Run 5 km", "Strength Program 2b. Run: Track Session #1 (1\u00d71600 m, 2\u00d7800 m, 4\u00d7400 m). Aim to match or beat times from last track session. Strength program should be getting easier \u2014 increase weights/times."),
            ("Sat: Swim 2 km (OWS)", "Open water. Continue wetsuit prep: get suit on, warm up dry-side, acclimatise and warm up within a couple of minutes (race-day practice). Work in harder efforts in the later part. 1-arm drills aid rotation &amp; stroke efficiency for open water."),
            ("Sun: Bike 60 km", "Hills. Steady state @RPE 6\u20138. Maintain steady cadence and rhythm on climbs and flat. If you have access to your race course, do a recon ride (2 laps). Pace judge climbs, note prevailing wind direction."),
        ],
    },
    {
        "num": 6, "tri": 13, "dates": "Jun 30 - Jul 6",
        "title": "Week 6 (Tri PDF Wk 13)  |  Jun 30 \u2013 Jul 6  |  93.5 km total",
        "goals": "High volume running week \u2014 last tough one before taper. Speed work and pacing are key. Start thinking about race-day fluid needs. If you have new race-day shoes, start wearing them in now. Field test ALL planned race equipment this week.",
        "sessions": [
            ("Mon: Swim 2.5 km", "Swim Session #9 (Drills/Intervals). Final fitness push \u2014 use shorter efforts to work hard and longer efforts to refocus on technique. Paddle work for stroke strength."),
            ("Tue: Bike 30 km", "Mixed effort/fartlek. Preferably outdoors on naturally varied route. Add harder \u2018fartlek\u2019 style efforts. Practice longer aerobar/drop efforts to work hard in a lower position. @RPE 5\u20137. Take adequate water &amp; fuelling."),
            ("Wed: Swim 2 km + Run 10 km", "Swim Session #6 (Intervals). Run: Negative split \u2014 complete second half quicker than first, keeping intensity moderate @RPE 5\u20137. High volume day \u2014 if possible, plan good gap between swim and run. Make sure to eat and drink enough before/after. Wear tri-suit underneath wetsuit. Practice sighting and speed work."),
            ("Thu: REST", "Full rest day. Consider booking a recovery massage \u2014 your body will thank you for maintenance."),
            ("Fri: Strength + Run 5 km", "Strength Program 2a. Run: Fartlek \u2014 random intervals, average @RPE 6 with bursts RPE 5\u20139. Learning to return to base pace following effort. Good session with a friend."),
            ("Sat: Swim 1.5 km (OWS)", "Open water. Longer steady duration. Run through wetsuit fitting, lubricant, tri-suit underneath. If you can swim with a friend or group, good practice for race-day conditions. Mixing up speed simulates fatigue."),
            ("Sun: Brick 35 km + 7.5 km", "<b>Race simulation.</b> Use intended race kit, clothing, nutrition, bottles. Bike: warm up over first 2 km then build to @RPE 8+. Run: run strong off bike for first 2 km then settle into easier pace. Prep bike as for race day (bottles, nutrition, spares)."),
        ],
    },
    {
        "num": 7, "tri": 14, "dates": "Jul 7 - Jul 13",
        "title": "Week 7 (Tri PDF Wk 14)  |  Jul 7 \u2013 Jul 13  |  94.5 km total",
        "goals": "Last high volume week before taper. By end of this week you\u2019ll have a good race plan and realistic target. Plan your pacing and nutrition strategy. Make sure you have all equipment needed \u2014 any last-minute purchases must be tested over race distance.",
        "sessions": [
            ("Mon: Swim 2.5 km", "Swim Session #7 (Drills/Intervals). You should be swimming these at your best pace in the program. Getting near best 100 m &amp; 200 m times \u2014 the real show of fitness comes when you replicate this pace in open water."),
            ("Tue: Bike 25 km", "Intervals. Indoors: 3 km warm up @RPE 5\u20138. Main: 1 min @RPE 5, 6 min @RPE 6, 1 min @RPE 7, 1 min @RPE 8, 1 min @RPE 9. Repeat until 2\u20133 km to go, cool down @RPE 4. Outdoors: fartlek with longer efforts. Working above and below threshold."),
            ("Wed: Run 10 km", "Steady state @RPE 6\u20137. Aerobic run, route of your choosing. Focus on run form, posture and finishing feeling strong. If off-road or hilly, pace yourself to keep effort in correct zone. <i>(Note: rest shifts to Thursday this week.)</i>"),
            ("Thu: REST", "Full rest day."),
            ("Fri: Strength + Run 5 km", "Strength Program 2b. Run: Track Session #1 (1\u00d71600 m, 2\u00d7800 m, 4\u00d7400 m). Working above race pace. Can do each repeated distance as a negative split, trying to beat time of last segment by 1\u20132 seconds."),
            ("Sat: Swim 2 km (OWS)", "Race day prep. Get suit on in plenty of time, fit properly. Warm up on land then in water within 2 min (race-day simulation). Practice start, swim race distance (1.5 km). Use remaining distance for sprints. Final race-pace prep \u2014 polish technique and pacing. Practice open water race starts."),
            ("Sun: Bike 50 km", "Hills. Steady state \u2014 maintain cadence and rhythm. Pace judgement on hills. Good pacing on hills maintains optimal race pace (too easy = lose time, too hard = slower on flats)."),
        ],
    },
    {
        "num": "RW", "tri": "15-16", "dates": "Jul 14 - Jul 20",
        "title": "Race Week (Tri PDF Wk 16)  |  Jul 14\u201320  |  72.5 km total (inc. race)",
        "goals": "The hard work is done \u2014 nothing you can do now will make you fitter. Focus on maintaining peak while allowing recovery. Keep sessions high quality with good pace work. Reduced volume allows adaptation/recovery. Stick to what you know in training. <i>Note: Tri PDF Wk 15 (taper) is absorbed into prior weeks; this week follows Wk 16 race-week schedule.</i>",
        "sessions": [
            ("Mon: Swim 1.5 km", "Mixed intensity. 200 m warm up, 200 m pull buoy @RPE 6, 400 m @RPE 7, 200 m @RPE 8, 2\u00d7100 m @RPE 9, 100 m warm down. Steady work with bursts \u2014 shouldn\u2019t feel tired after this."),
            ("Tue: Bike 15 km", "Final pre-race bike check. Ride steady in race setup, carry what you plan to carry. Add 2\u20134 min bursts @RPE 5\u20137. After ride, clean bike and give tyres a once-over. Is all in working order? Do you have the spares you need?"),
            ("Wed: Run 2.5 km", "Steady pace, focus on form and light foot strike. Add short bursts of harder effort @RPE 5\u20137. This distance should feel very easy now. Should feel good when you finish."),
            ("Thu: Mobility 30 min", "WARM-UP / FLEXIBILITY part of strength routine ONLY. If feeling good, optional gentle 1 km run @RPE 5\u20136 to stay loose. If possible, book a massage."),
            ("Fri: Run 1 km", "Still warming up \u2014 keep legs moving at a good tempo, but not quite race pace @RPE 7. Nice short session to loosen off."),
            ("Sat: Swim 750 m", "Relaxed effort, loosening off with a few short bursts @RPE 5\u20137. Good position, technique, relaxed stroke. Can do in open water for confidence boost and wetsuit removal practice. If you\u2019ve travelled to the event, this helps get over the journey."),
            ("Sun: RACE DAY!", "<b>Olympic Triathlon: 1.5 km Swim / 40 km Bike / 10 km Run.</b> The hard work is over. Stick to what you know from training. Race hard, race well, and have fun!"),
        ],
    },
]
for w in phase3_weeks:
    story.append(P(p3_header_text, phase_style))
    story.append(P(p3_desc, body_style))
    story.append(P(p3_rule, body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=MED_GRAY, spaceBefore=2, spaceAfter=3))
    story.append(P(w["title"], week_style))
    story.append(P("<b>Goals:</b> " + w["goals"], note_style))
    story.append(phase1_table(w["sessions"]))
    story.append(PageBreak())


# ============================================================
# QUICK REFERENCE TIMELINE
# ============================================================
story.append(P("Quick Reference — Full Timeline", phase_style))
story.append(Spacer(1, 6))

timeline = [
    [P("Period", cell_header), P("Dates", cell_header), P("Phase", cell_header), P("Focus", cell_header), P("Sessions/Wk", cell_header)],
    [P("Pre-plan", cell_style), P("Now – Feb 21", cell_style), P("Cycling base", cell_style), P("4× cycling/week, building FTP", cell_style), P("4 bike", cell_center)],
    [P("Wk 1–6", cell_style), P("Feb 22 – Mar 30", cell_style), P("Phase 1", cell_bold), P("HM running build (Pfitzinger) + maintenance rides", cell_style), P("4 run, 1–2 bike", cell_center)],
    [P("Wk 7–12", cell_style), P("Mar 31 – May 11", cell_style), P("Phase 2", cell_bold), P("HM peak + Tri PDF swims/bikes (Wk 1–6)", cell_style), P("4 run, 2 swim, 1 bike", cell_center)],
    [P("Wk 13", cell_style), P("May 12–17", cell_style), P("Race Week", cell_bold), P("Taper → Brooklyn Half Marathon", cell_style), P("Taper", cell_center)],
    [P("Recovery", cell_style), P("May 18–25", cell_style), P("Recovery", cell_style), P("Easy movement only", cell_style), P("As needed", cell_center)],
    [P("Wk 14–21", cell_style), P("May 26 – Jul 13", cell_style), P("Phase 3", cell_bold), P("Tri PDF Weeks 8–14, full triathlon build", cell_style), P("Per PDF", cell_center)],
    [P("Wk 22", cell_style), P("Jul 14–20", cell_style), P("Race Week", cell_bold), P("Tri PDF Week 16, race day July 20", cell_style), P("Race!", cell_center)],
]

cw_tl = [0.7*inch, 1.2*inch, 0.8*inch, 2.9*inch, 0.9*inch]
t_tl = Table(timeline, colWidths=cw_tl)
t_tl.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('GRID', (0, 0), (-1, -1), 0.4, MED_GRAY),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ('BACKGROUND', (0, 5), (-1, 5), HexColor('#fff3e0')),
    ('BACKGROUND', (0, 8), (-1, 8), HexColor('#e8f5e9')),
] + [('BACKGROUND', (0, i), (-1, i), ROW_ALT) for i in range(2, 8, 2)]))
story.append(t_tl)
story.append(Spacer(1, 16))

story.append(P("This plan was designed around your specific situation — a strong cycling base, marathon experience from fall 2025, a 3-month detraining gap, and two races 9 weeks apart. Every pace is a starting point. We adjust weekly based on real data. Trust the process, follow the checklist, and don't try to prove anything in training.", body_style))
story.append(Spacer(1, 6))
story.append(P("<i>Plan prepared February 2026. Paces subject to weekly adjustment based on training data.</i>", note_style))

doc.build(story)
print("PDF v3 created successfully!")
