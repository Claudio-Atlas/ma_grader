# writers/build_instructor_master_workbook.py

import os
from typing import List, Optional, Dict, Any

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from utilities.paths import ws_path  # [OK] workspace-aware template path


SUMMARY_SHEET_NAME = "Summary_Template"

SUMMARY_HEADER_ROW = 4
SUMMARY_START_ROW = 5

# Summary columns
COL_NAME = "A"
COL_AUTO_TOTAL = "B"
COL_MANUAL_ADJ = "C"
COL_FINAL_TOTAL = "D"
COL_SECTION1 = "E"
COL_SECTION2 = "F"
COL_SECTION3 = "G"
COL_SECTION4 = "H"

# ── MA1 grading sheet cell map ──
# Individual score cells written by writers (actual numbers, not formulas):
#   Income Analysis:  F3-F7   → section sum = F3+F4+F5+F6+F7
#   Unit Conversions: F9-F13  → section sum = F9+F10+F11+F12+F13
#   Currency:         F15-F22 → section sum = F15+F16+F17+F18+F19+F20+F21+F22
# The template has SUM formulas at F8, F14, F23, F24 but openpyxl can't evaluate them.

MA1_SCORE_CELLS = {
    "section1": ["F3", "F4", "F5", "F6", "F7"],       # Income Analysis
    "section2": ["F9", "F10", "F11", "F12", "F13"],    # Unit Conversions
    "section3": ["F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22"],  # Currency
}
MA1_SECTION_LABELS = ("Income Total", "Unit Total", "Currency Total")

# ── MA3 grading sheet cell map ──
# Analysis:      F3-F9   → section sum
# Visualization: F11-F15 → section sum

MA3_SCORE_CELLS = {
    "section1": ["F3", "F4", "F5", "F6", "F7", "F8", "F9"],   # Analysis
    "section2": ["F11", "F12", "F13", "F14", "F15"],            # Visualization
    "section3": [],                                               # (no third section)
}
MA3_SECTION_LABELS = ("Analysis Total", "Visualization Total", "")

# ── MA2 grading sheet ──
# The MA2 grade sheet computes everything with formulas, which openpyxl can't
# evaluate, so the master recomputes the same numbers from the scores:
#   tab points    F9/F16/F21/F29 = SUM of the tab's rows (out of 26/27/42/44)
#   scaled score  I9/I16/I21/I29 = (points / possible) * 33.25
#   level         H9/H16/H21/H29 = 5/4/3/2/1 at 95%/80%/60%/35%
#   template total I31 = sum of the scaled scores (out of 133)
#   paper         F48 = SUM(F40:F47), added in I33 when the paper is graded

MA2_SECTIONS = [  # (label, rubric rows) — every row counts, the pie chart (F27) included
    ("Income and Projection", range(3, 9)),
    ("Student Loans", range(10, 16)),
    ("Credit Cards", range(17, 21)),
    ("Annual Budget", range(22, 29)),
]
MA2_SCALE = 33.25
MA2_PAPER_ROWS = range(40, 48)

MA2_SCORE_CELLS = {  # kept for reference; MA2 totals come from _read_ma2_scores
    f"section{i + 1}": [f"F{r}" for r in rows] for i, (_, rows) in enumerate(MA2_SECTIONS)
}
MA2_SECTION_LABELS = ("Income Total", "Loans Total", "Credit Total", "Budget Total")

# Extra MA2 columns after the four tab totals (E-H).
MA2_SCALED_COLS = ("I", "J", "K", "L")
MA2_LEVEL_COLS = ("M", "N", "O", "P")
MA2_PAPER_COL = "Q"
MA2_SHORT = ("Income", "Loans", "Credit", "Budget")


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _ma2_level(fraction):
    """The grade sheet's rubric level: =IF(G>=0.95,5,IF(G>=0.8,4,...))."""
    for cutoff, level in ((0.95, 5), (0.8, 4), (0.6, 3), (0.35, 2)):
        if fraction >= cutoff:
            return level
    return 1


def _read_ma2_scores(ws) -> Dict[str, Any]:
    """The numbers the MA2 grade sheet's own formulas produce."""
    points, possible, scaled, levels = [], [], [], []
    for _, rows in MA2_SECTIONS:
        pts = sum(v for r in rows if (v := _num(ws[f"F{r}"].value)) is not None)
        poss = sum(v for r in rows if (v := _num(ws[f"E{r}"].value)) is not None)
        frac = pts / poss if poss else 0.0
        points.append(pts)
        possible.append(poss)
        scaled.append(frac * MA2_SCALE)
        levels.append(_ma2_level(frac))
    paper_vals = [v for r in MA2_PAPER_ROWS if (v := _num(ws[f"F{r}"].value)) is not None]
    return {
        "section1": points[0], "section2": points[1], "section3": points[2], "section4": points[3],
        "possible": possible,
        "scaled": scaled,
        "levels": levels,
        "overall": sum(scaled),                                # I31
        "paper": sum(paper_vals) if paper_vals else None,      # F48, once graded
    }


def _grade_files_in_folder(graded_path: str, assignment_type: str = "MA1") -> List[str]:
    graded_path = os.path.abspath(graded_path)
    suffix = f"_{assignment_type.lower()}_grade.xlsx"
    files = []
    for fn in os.listdir(graded_path):
        if fn.lower().endswith(suffix):
            files.append(os.path.join(graded_path, fn))
    files.sort()
    return files


def _read_scores_from_graded_file(grade_path: str, assignment_type: str) -> Dict[str, Any]:
    """
    Open a graded student file and read actual numeric scores from cells.
    Returns dict with keys: section1, section2, section3, overall, student_sections.
    """
    atype = assignment_type.upper()
    if atype == "MA3":
        cell_map = MA3_SCORE_CELLS
    elif atype == "MA2":
        cell_map = MA2_SCORE_CELLS
    else:
        cell_map = MA1_SCORE_CELLS

    wb = None
    try:
        wb = load_workbook(grade_path, data_only=False)
        ws = wb["Grading Sheet"]

        if atype == "MA2":
            return _read_ma2_scores(ws)

        sections = {}
        overall = 0
        for key, cells in cell_map.items():
            total = 0
            for cell_ref in cells:
                val = ws[cell_ref].value
                if isinstance(val, (int, float)):
                    total += val
            sections[key] = total
            overall += total

        result = {
            "section1": sections.get("section1", 0),
            "section2": sections.get("section2", 0),
            "section3": sections.get("section3", 0),
            "overall": overall,
        }
        if "section4" in sections:
            result["section4"] = sections["section4"]
        return result
    finally:
        if wb is not None:
            wb.close()


def _ensure_summary_headers(ws: Worksheet, assignment_type: str = "MA1") -> None:
    """
    Ensure the section columns have labels.
    """
    atype = assignment_type.upper()
    if atype == "MA3":
        labels = MA3_SECTION_LABELS
    elif atype == "MA2":
        labels = tuple(f"{name} (/{poss})" for (name, _), poss in zip(MA2_SECTIONS, (26, 27, 42, 44)))
        ws[f"{COL_AUTO_TOTAL}{SUMMARY_HEADER_ROW}"].value = "Auto Total (/133)"
        ws[f"{COL_FINAL_TOTAL}{SUMMARY_HEADER_ROW}"].value = "Final Total (with paper)"
        for col, short in zip(MA2_SCALED_COLS, MA2_SHORT):
            ws[f"{col}{SUMMARY_HEADER_ROW}"].value = f"{short} Scaled (/{MA2_SCALE})"
        for col, short in zip(MA2_LEVEL_COLS, MA2_SHORT):
            ws[f"{col}{SUMMARY_HEADER_ROW}"].value = f"{short} Level"
        ws[f"{MA2_PAPER_COL}{SUMMARY_HEADER_ROW}"].value = "Paper Subtotal"
    else:
        labels = MA1_SECTION_LABELS
    cols = [COL_SECTION1, COL_SECTION2, COL_SECTION3, COL_SECTION4] if atype == "MA2" else [COL_SECTION1, COL_SECTION2, COL_SECTION3]
    for col, label in zip(cols, labels):
        cell = f"{col}{SUMMARY_HEADER_ROW}"
        if label:
            ws[cell].value = label
        elif ws[cell].value in (None, ""):
            pass  # leave blank for unused sections


def build_instructor_master_workbook(
    graded_path: str,
    template_path: Optional[str] = None,
    output_filename: str = "INSTRUCTOR_MASTER.xlsx",
    assignment_type: str = "MA1",
) -> str:
    """
    Builds a summary-only instructor master workbook with actual values
    (not external link formulas) read from each student's graded file.

    Saves into:
      graded_output/<course>/INSTRUCTOR_MASTER.xlsx

    Returns: absolute path to created workbook
    """
    graded_path = os.path.abspath(graded_path)

    if not os.path.isdir(graded_path):
        raise FileNotFoundError(f"graded_path not found: {graded_path}")

    if template_path is None:
        template_path = ws_path("templates", "Template_Master.xlsx")
    else:
        template_path = os.path.abspath(template_path)

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"[ERROR] Template_Master.xlsx not found at:\n{template_path}\n\n"
            f"Place it here:\nDocuments/MA1_Autograder/templates/Template_Master.xlsx"
        )

    grade_files = _grade_files_in_folder(graded_path, assignment_type)
    if not grade_files:
        raise FileNotFoundError(f"No *_{assignment_type}_Grade.xlsx files found in: {graded_path}")

    wb = None

    try:
        wb = load_workbook(template_path)

        if SUMMARY_SHEET_NAME not in wb.sheetnames:
            raise KeyError(f"Template missing sheet: {SUMMARY_SHEET_NAME}")

        ws_summary = wb[SUMMARY_SHEET_NAME]
        _ensure_summary_headers(ws_summary, assignment_type)

        row = SUMMARY_START_ROW

        for full_grade_path in grade_files:
            grade_filename = os.path.basename(full_grade_path)
            suffix = f"_{assignment_type}_Grade.xlsx"
            if grade_filename.endswith(suffix):
                student_base = grade_filename[:-len(suffix)]
            else:
                student_base = grade_filename.rsplit("_", 2)[0]

            # Read actual scores from the graded file
            scores = _read_scores_from_graded_file(full_grade_path, assignment_type)

            # Name
            ws_summary[f"{COL_NAME}{row}"].value = student_base

            # Auto Total (actual value)
            ws_summary[f"{COL_AUTO_TOTAL}{row}"].value = round(scores["overall"], 2)

            # Manual Adj default 0
            manual_cell = f"{COL_MANUAL_ADJ}{row}"
            if ws_summary[manual_cell].value in (None, ""):
                ws_summary[manual_cell].value = 0

            # Final Total = Auto + Manual (+ the written paper for MA2, like I33)
            final = f"={COL_AUTO_TOTAL}{row}+{COL_MANUAL_ADJ}{row}"
            if assignment_type.upper() == "MA2":
                final += f"+{MA2_PAPER_COL}{row}"
            ws_summary[f"{COL_FINAL_TOTAL}{row}"].value = final

            # Section totals (actual values)
            ws_summary[f"{COL_SECTION1}{row}"].value = scores["section1"]
            ws_summary[f"{COL_SECTION2}{row}"].value = scores["section2"]
            ws_summary[f"{COL_SECTION3}{row}"].value = scores["section3"]
            if assignment_type.upper() == "MA2":
                ws_summary[f"{COL_SECTION4}{row}"].value = scores.get("section4", 0)
                for col, v in zip(MA2_SCALED_COLS, scores["scaled"]):
                    ws_summary[f"{col}{row}"].value = round(v, 2)
                for col, v in zip(MA2_LEVEL_COLS, scores["levels"]):
                    ws_summary[f"{col}{row}"].value = v
                paper = scores["paper"]
                ws_summary[f"{MA2_PAPER_COL}{row}"].value = round(paper, 2) if paper is not None else None

            row += 1

        out_path = os.path.join(graded_path, output_filename)
        wb.save(out_path)
        return out_path

    finally:
        if wb is not None:
            wb.close()
