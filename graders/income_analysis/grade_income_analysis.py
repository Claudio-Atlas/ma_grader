"""
grade_income_analysis.py — Main orchestrator for Income Analysis tab grading

Purpose: Coordinates all grading checks for the Income Analysis worksheet tab.
         Aggregates scores and feedback from individual check modules and returns
         a unified results dictionary for the writer to process.

Author: Clayton Ragsdale
Dependencies: check_name_present, check_slope_intercept, check_slope_intercept_formatting,
              check_predictions, check_predictions_formatting, check_scatterplot

Grading Breakdown (23 points total):
    - Row 3: Name present (1 point)
    - Row 4: Slope/Intercept formulas (6 points) + formatting (1 point) = 7 points
    - Row 5: Predictions formulas (6 points) + formatting (1 point) = 7 points
    - Row 6: Scatterplot (8 points) - NOW AUTO-GRADED
        - XY-Scatterplot present: 3 points
        - Title and axis labels: 3 points
        - Trendline: 1 point
        - Trendline extended: 1 point
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from .check_name_present import check_name_present
from .check_slope_intercept import check_slope_intercept
from .check_slope_intercept_formatting import check_slope_intercept_formatting
from .check_predictions import check_predictions
from .check_predictions_formatting import check_currency_formatting
from .check_scatterplot import check_scatterplot


def grade_income_analysis(ws: Worksheet) -> Dict[str, Any]:
    """
    Run all grading checks for the Income Analysis tab.
    
    This function orchestrates the grading of all Income Analysis criteria:
    1. Name presence check (B1)
    2. Slope/Intercept formula validation (B30, B31)
    3. Slope/Intercept formatting check (0 decimal places)
    4. Predictions formula validation (E19:E35)
    5. Predictions formatting check (currency with 0 decimals)
    
    Feedback Format:
        All feedback is returned as tuples of (code, params) where:
        - code: A feedback code like "IA_SLOPE_CORRECT" that maps to a
                human-readable message in feedback/income_analysis.json
        - params: Dict of parameters to substitute into the message template
    
    Args:
        ws: The openpyxl Worksheet object for the Income Analysis tab
    
    Returns:
        Dict containing scores and feedback for each grading row:
            - name_score: int (0-1)
            - name_feedback: List[Tuple[str, dict]]
            - slope_score: float (0-7) - includes formulas + formatting
            - slope_feedback: List[Tuple[str, dict]]
            - predictions_score: float (0-7) - includes formulas + formatting
            - predictions_feedback: List[Tuple[str, dict]]
            - scatterplot_chart_score: float (0-6) - chart + title + labels (F6)
            - scatterplot_trendline_score: float (0-2) - trendline + extension (F7)
            - scatterplot_feedback: List[Tuple[str, dict]]
    
    Example:
        >>> from openpyxl import load_workbook
        >>> wb = load_workbook("student_submission.xlsx")
        >>> ws = wb["Income Analysis"]
        >>> results = grade_income_analysis(ws)
        >>> print(f"Total auto-graded: {results['name_score'] + results['slope_score'] + results['predictions_score']}")
    """
    results: Dict[str, Any] = {}

    # ============================================================
    # Row 3: Name Check
    # ============================================================
    # Validates that the student's name is present in cell B1
    # Worth 1 point
    score, fb = check_name_present(ws)
    results["name_score"] = score
    results["name_feedback"] = fb

    # ============================================================
    # Row 4: Slope/Intercept (formulas + formatting)
    # ============================================================
    # Slope formula check (B30):
    #   - 3 points for correct =SLOPE(B19:B26,A19:A26)
    #   - 2 points for reversed X/Y (=SLOPE(A19:A26,B19:B26))
    #   - 1 point for using SLOPE() with wrong ranges
    #   - 0 points if missing or not SLOPE()
    #
    # Intercept formula check (B31):
    #   - Same scoring as slope
    #
    # Formatting check:
    #   - 0.5 points for slope with 0 decimal places
    #   - 0.5 points for intercept with 0 decimal places
    slope_score, slope_fb = check_slope_intercept(ws)
    fmt_score, fmt_fb = check_slope_intercept_formatting(ws)

    # Combine formula and formatting scores/feedback for Row 4
    results["slope_score"] = slope_score + fmt_score
    results["slope_feedback"] = (slope_fb or []) + (fmt_fb or [])

    # ============================================================
    # Row 5: Predictions (formulas + formatting)
    # ============================================================
    # Predictions formula check (E19:E35):
    #   - Each cell should be =B30*D{row}+B31 (or equivalent)
    #   - Must reference slope (B30), intercept (B31), and years (D column)
    #   - 6 points total, proportional to correct cells (17 cells)
    #
    # Predictions formatting check:
    #   - All cells should be currency with 0 decimal places
    #   - 1 point total, proportional to correctly formatted cells
    pred_score, pred_fb = check_predictions(ws)
    pred_fmt_score, pred_fmt_fb = check_currency_formatting(ws)

    # Combine formula and formatting scores/feedback for Row 5
    results["predictions_score"] = pred_score + pred_fmt_score
    results["predictions_feedback"] = (pred_fb or []) + (pred_fmt_fb or [])

    # ============================================================
    # Row 6 & 7: Scatterplot (auto-graded, split into two rows)
    # ============================================================
    # Row 6 (F6) - Chart & Labels (6 points):
    #   - XY-Scatterplot present with BLS data: 3 points
    #   - Chart title present: 1 point
    #   - X-axis label present: 1 point
    #   - Y-axis label present: 1 point
    #
    # Row 7 (F7) - Trendline (2 points):
    #   - Trendline added: 1 point
    #   - Trendline extended (8-24 years): 1 point
    chart_labels_score, trendline_score, scatter_fb = check_scatterplot(ws)
    results["scatterplot_chart_score"] = chart_labels_score  # F6 (0-6)
    results["scatterplot_trendline_score"] = trendline_score  # F7 (0-2)
    results["scatterplot_feedback"] = scatter_fb

    return results
