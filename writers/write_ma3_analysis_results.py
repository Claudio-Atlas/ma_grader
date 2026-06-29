"""
write_ma3_analysis_results.py — Writes MA3 Analysis tab results to grading sheet

Writes scores and feedback to the MA3 grading sheet:
    Row 3: Name (1 pt)
    Row 4: Difference Data (6 pts)
    Row 5: Statistics (24 pts)
    Row 6: Percentiles (6 pts)
    Row 7: Empirical Rule (6 pts)
    Row 8: Written Analysis (5 pts) - includes student text for manual grading
    Row 9: Formatting (6 pts)
"""

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font
from utilities.feedback_renderer import render_feedback

# Standard black font for feedback cells
BLACK_FONT = Font(color="000000")

TAB = "ma3_analysis"


def write_ma3_analysis_results(ws_grading: Worksheet, results: dict) -> Worksheet:
    """
    Writes MA3 Analysis results into the grading sheet.
    
    Args:
        ws_grading: The grading sheet worksheet
        results: Dict from grade_analysis_tab() containing scores and feedback
    
    Returns:
        Updated worksheet
    """
    
    # Row 3 - Name (1 pt)
    ws_grading["F3"].value = results.get("name_score", 0)
    ws_grading["G3"].value = render_feedback(results.get("name_feedback"), TAB)
    ws_grading["G3"].font = BLACK_FONT
    
    # Row 4 - Difference Data (6 pts)
    ws_grading["F4"].value = results.get("diff_score", 0)
    ws_grading["G4"].value = render_feedback(results.get("diff_feedback"), TAB)
    ws_grading["G4"].font = BLACK_FONT
    
    # Row 5 - Statistics (24 pts)
    ws_grading["F5"].value = results.get("stats_score", 0)
    ws_grading["G5"].value = render_feedback(results.get("stats_feedback"), TAB)
    ws_grading["G5"].font = BLACK_FONT
    
    # Row 6 - Percentiles (6 pts)
    ws_grading["F6"].value = results.get("percentile_score", 0)
    ws_grading["G6"].value = render_feedback(results.get("percentile_feedback"), TAB)
    ws_grading["G6"].font = BLACK_FONT
    
    # Row 7 - Empirical Rule (6 pts)
    ws_grading["F7"].value = results.get("empirical_score", 0)
    ws_grading["G7"].value = render_feedback(results.get("empirical_feedback"), TAB)
    ws_grading["G7"].font = BLACK_FONT
    
    # Row 8 - Written Analysis (5 pts) - Manual grading required
    # Score is 0 by default - instructor must fill in
    ws_grading["F8"].value = results.get("written_score", 0)
    
    # Include the student's written text in feedback for instructor review
    written_text = results.get("written_text", "")
    written_feedback = results.get("written_feedback", [])
    
    if written_text:
        # Prepend the text with a note for the instructor
        feedback_text = render_feedback(written_feedback, TAB)
        if len(written_text) > 500:
            written_text = written_text[:500] + "..."
        ws_grading["G8"].value = f"[MANUAL GRADING REQUIRED]\n\nStudent's Response:\n{written_text}\n\n{feedback_text}"
    else:
        ws_grading["G8"].value = render_feedback(written_feedback, TAB)
    ws_grading["G8"].font = BLACK_FONT
    
    # Row 9 - Formatting (6 pts)
    ws_grading["F9"].value = results.get("format_score", 0)
    ws_grading["G9"].value = render_feedback(results.get("format_feedback"), TAB)
    ws_grading["G9"].font = BLACK_FONT
    
    return ws_grading
