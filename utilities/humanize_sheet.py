"""
humanize_sheet.py — final pass that rewrites a graded sheet's Comments column
in the student-facing voice (see student_feedback.py) and adds an overall note.

It runs after every tab writer, reads each rubric row's points (F), possible
points (E) and the grader's comment (G), and rewrites G. Graders that report
problems in the new voice are used as-is; older grader comments are filtered
down to just the problems.
"""

import math

from openpyxl.styles import Alignment, Font

from utilities import student_feedback as sf

FORMATTING_PRAISE = "Your formatting on this tab is spot on. Every cell is set up the way the instructions ask."

# Per-row praise for full credit, keyed by grading-sheet row.
MA2_PRAISE = {
    3: "Thanks for entering your full name.",
    4: "Your CPI table is complete, and every value matches the reference data. Nice work!",
    5: "Your SLOPE and INTERCEPT formulas are exactly right.",
    6: "Your projection year, projected CPI and inflation rate are all correct. Great job.",
    7: "Your current income, 5-year projection and monthly income formulas are all correct.",
    8: FORMATTING_PRAISE,
    10: "You pulled the right interest rate from the Mortgage Rates tab.",
    11: "Your unsubsidized loan setup (years in school, added interest and new principal) is all correct.",
    12: "Payments per year and number of years are both correct.",
    13: "Your subsidized loan payment, total paid and interest paid are all correct. Nice work!",
    14: "Your unsubsidized loan payment, total paid and interest paid are all correct.",
    15: FORMATTING_PRAISE,
    17: "All five credit card inputs match the values in the description.",
    18: "Your amortization table is correct all the way to payoff. Great job.",
    19: "Years to pay off, total paid and total interest are all calculated correctly.",
    20: FORMATTING_PRAISE,
    22: "Your Housing through Other rows are complete, with a formula for every Total Annual Cost.",
    23: "Your subsidized loan row is correct and pulls the payment straight from the Student Loans tab.",
    24: "Your credit card row is correct and pulls the payment straight from the Credit Cards tab.",
    25: "Your Total Annual Budget adds everything up with SUM, just as asked.",
    26: "Your 5-year projected total and remaining total are both correct.",
    27: "Your pie chart has everything: the right data, a category legend, a clear title and percentage labels. Nice work!",
    28: FORMATTING_PRAISE,
}

# Short names for the biggest pieces of work, used to praise strengths in the
# overall note (only rows earning full credit are mentioned).
MA2_STRENGTHS = {
    18: "credit card amortization table",
    22: "budget table",
    13: "subsidized loan calculations",
    14: "unsubsidized loan calculations",
    4: "CPI table",
    6: "CPI projection",
    7: "income projection",
    27: "pie chart",
    19: "payoff summary",
}

MA2_SECTIONS = [
    ("Income and Projection", range(3, 9)),
    ("Student Loans", range(10, 16)),
    ("Credit Cards", range(17, 21)),
    ("Annual Budget", range(22, 29)),
]

LAYOUTS = {
    # label cell, note cell, merged range for the note
    "MA2": {"praise": MA2_PRAISE, "sections": MA2_SECTIONS, "strengths": MA2_STRENGTHS,
            "label": "G31", "note": "G32", "merge": "G32:H37"},
}


LINE_PT = 15.5  # points per wrapped line at the template's 11pt font


def _lines(text, width_chars):
    return sum(max(1, math.ceil(len(part) / max(10, width_chars))) for part in str(text).split("\n"))


def _fit_row(ws, row, text, col="G"):
    """Grow a fixed-height row so a wrapped comment isn't cut off (never shrinks)."""
    width = (ws.column_dimensions[col].width or 50) * 1.05
    need = _lines(text, width) * LINE_PT + 4
    current = ws.row_dimensions[row].height or 15
    if need > current:
        ws.row_dimensions[row].height = need


def humanize_grading_sheet(ws, assignment, student_name="", row_issues=None):
    """Rewrite column G for every rubric row and add the overall note.

    row_issues: optional {row: [student-facing issue, ...]} from graders that
    report problems directly; those replace the legacy comment for that row.
    Returns the overall note text (or None if the layout is unknown).
    """
    layout = LAYOUTS.get(assignment.upper())
    if not layout:
        return None
    row_issues = row_issues or {}

    comments = []
    for row, praise in layout["praise"].items():
        pts, poss = ws[f"F{row}"].value, ws[f"E{row}"].value
        if not isinstance(poss, (int, float)):
            continue
        text = sf.compose(praise, pts, poss, row_issues.get(row), fallback=ws[f"G{row}"].value)
        ws[f"G{row}"] = text
        ws[f"G{row}"].alignment = Alignment(wrap_text=True, vertical="top")
        _fit_row(ws, row, text)
        comments.append(text)

    sections = []
    for name, rows in layout["sections"]:
        pts = sum(v for r in rows if isinstance(v := ws[f"F{r}"].value, (int, float)))
        poss = sum(v for r in rows if isinstance(v := ws[f"E{r}"].value, (int, float)))
        if poss:
            sections.append({"name": name, "points": pts, "possible": poss})

    # Biggest fully-correct rows first.
    strengths = [
        phrase for row, phrase in sorted(
            layout.get("strengths", {}).items(),
            key=lambda kv: -(ws[f"E{kv[0]}"].value or 0) if isinstance(ws[f"E{kv[0]}"].value, (int, float)) else 0,
        )
        if isinstance(ws[f"E{row}"].value, (int, float))
        and isinstance(ws[f"F{row}"].value, (int, float))
        and ws[f"F{row}"].value >= ws[f"E{row}"].value - 1e-9
    ]

    first = sf.first_name(student_name)
    note = None
    if sf.ai_notes_enabled():
        note = sf.ai_overall_note(first, sections, comments)
    if not note:
        note = sf.overall_note(first, sections, strengths)

    ws[layout["label"]] = "Overall feedback"
    ws[layout["label"]].font = Font(bold=True)
    try:
        ws.merge_cells(layout["merge"])
    except ValueError:
        pass  # already merged (re-grade)
    ws[layout["note"]] = note
    ws[layout["note"]].alignment = Alignment(wrap_text=True, vertical="top")

    # Make the merged note box tall enough: extra height goes on its last row.
    from openpyxl.utils import range_boundaries
    c1, r1, c2, r2 = range_boundaries(layout["merge"])
    from openpyxl.utils import get_column_letter
    width = sum((ws.column_dimensions[get_column_letter(c)].width or 10) for c in range(c1, c2 + 1)) * 1.05
    have = sum((ws.row_dimensions[r].height or 15) for r in range(r1, r2 + 1))
    need = _lines(note, width) * LINE_PT + 6
    if need > have:
        ws.row_dimensions[r2].height = (ws.row_dimensions[r2].height or 15) + (need - have)
    return note
