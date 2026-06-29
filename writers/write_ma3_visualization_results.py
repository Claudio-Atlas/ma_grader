"""
write_ma3_visualization_results.py — Writes MA3 Visualization tab results to grading sheet

Writes scores and feedback to the MA3 grading sheet:
    Row 11: Bin Table (6 pts)
    Row 12: Lower/Upper Limits (12 pts)
    Row 13: Title/Freq/RelFreq (18 pts)
    Row 14: Histogram (6 pts)
    Row 15: Formatting (4 pts)
"""

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font
from utilities.feedback_renderer import render_feedback

# Standard black font for feedback cells
BLACK_FONT = Font(color="000000")

TAB = "ma3_visualization"


def write_ma3_visualization_results(ws_grading: Worksheet, results: dict) -> Worksheet:
    """
    Writes MA3 Visualization results into the grading sheet.
    
    Args:
        ws_grading: The grading sheet worksheet
        results: Dict from grade_visualization_tab() containing scores and feedback
    
    Returns:
        Updated worksheet
    """
    
    # Row 11 - Bin Table (6 pts)
    ws_grading["F11"].value = results.get("bin_score", 0)
    ws_grading["G11"].value = render_feedback(results.get("bin_feedback"), TAB)
    ws_grading["G11"].font = BLACK_FONT
    
    # Row 12 - Lower/Upper Limits (12 pts)
    ws_grading["F12"].value = results.get("limits_score", 0)
    ws_grading["G12"].value = render_feedback(results.get("limits_feedback"), TAB)
    ws_grading["G12"].font = BLACK_FONT
    
    # Row 13 - Title/Freq/RelFreq (18 pts)
    ws_grading["F13"].value = results.get("freqdist_score", 0)
    ws_grading["G13"].value = render_feedback(results.get("freqdist_feedback"), TAB)
    ws_grading["G13"].font = BLACK_FONT
    
    # Row 14 - Histogram (6 pts)
    ws_grading["F14"].value = results.get("histogram_score", 0)
    ws_grading["G14"].value = render_feedback(results.get("histogram_feedback"), TAB)
    ws_grading["G14"].font = BLACK_FONT
    
    # Row 15 - Formatting (4 pts)
    ws_grading["F15"].value = results.get("format_score", 0)
    ws_grading["G15"].value = render_feedback(results.get("format_feedback"), TAB)
    ws_grading["G15"].font = BLACK_FONT
    
    return ws_grading
