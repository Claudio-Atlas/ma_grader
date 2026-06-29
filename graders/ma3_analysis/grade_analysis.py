"""
grade_analysis.py — Main orchestrator for MA3 Analysis tab grading

Purpose: Coordinates all grading checks for the Analysis worksheet tab.
         Aggregates scores and feedback from individual checker modules.

Author: Clayton Ragsdale
Dependencies: check_*.py modules in this package

Grading Breakdown (54 points total):
    Name (B10): 1 point
    Difference Data (D14:D63): 6 points (0.12 pts each)
    Statistics (G18:I21): 24 points (2 pts each × 12 cells)
    Percentiles (G27:G28): 6 points (3 pts each)
    Empirical Rule (G36:G37): 6 points (3 pts each)
    Written Analysis: 5 points (manual grading)
    Formatting: 6 points
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from .check_name import check_name
from .check_differences import check_differences
from .check_statistics import check_statistics
from .check_percentiles import check_percentiles
from .check_empirical_rule import check_empirical_rule
from .check_written_analysis import check_written_analysis
from .check_formatting import check_analysis_formatting


def grade_analysis_tab(
    sheet: Worksheet,
    student_name: str = "",
    sheet_data: Worksheet = None
) -> Dict[str, Any]:
    """
    Analysis tab grading orchestrator.
    
    Args:
        sheet: The openpyxl Worksheet object for the Analysis tab (formulas)
        student_name: Student's name from filename (optional, for validation)
        sheet_data: Analysis worksheet loaded with data_only=True (calculated values)
                   Used for reading expected percentile values from F27/F28.
    
    Returns:
        Dict containing scores and feedback for each competency:
            - name_score, name_feedback
            - diff_score, diff_feedback
            - stats_score, stats_feedback
            - percentile_score, percentile_feedback
            - empirical_score, empirical_feedback
            - written_score, written_feedback, written_text
            - format_score, format_feedback
    """
    results: Dict[str, Any] = {}
    
    # ============================================================
    # Name Check (B10) - 1 point
    # ============================================================
    name_score, name_feedback = check_name(sheet)
    results["name_score"] = name_score
    results["name_feedback"] = name_feedback
    
    # ============================================================
    # Difference Data (D14:D63) - 6 points
    # ============================================================
    diff_score, diff_feedback = check_differences(sheet)
    results["diff_score"] = diff_score
    results["diff_feedback"] = diff_feedback
    
    # ============================================================
    # Statistics (G18:I21) - 24 points
    # Mean, Median, StdDev, Range for Before/After/Difference
    # ============================================================
    stats_score, stats_feedback = check_statistics(sheet)
    results["stats_score"] = stats_score
    results["stats_feedback"] = stats_feedback
    
    # ============================================================
    # Percentiles (G27:G28) - 6 points
    # ============================================================
    percentile_score, percentile_feedback = check_percentiles(sheet, sheet_data)
    results["percentile_score"] = percentile_score
    results["percentile_feedback"] = percentile_feedback
    
    # ============================================================
    # Empirical Rule (G36:G37) - 6 points
    # ============================================================
    empirical_score, empirical_feedback = check_empirical_rule(sheet)
    results["empirical_score"] = empirical_score
    results["empirical_feedback"] = empirical_feedback
    
    # ============================================================
    # Written Analysis - 5 points (manual)
    # Copy text to grading sheet for instructor review
    # ============================================================
    written_score, written_feedback, written_text = check_written_analysis(sheet)
    results["written_score"] = written_score
    results["written_feedback"] = written_feedback
    results["written_text"] = written_text
    
    # ============================================================
    # Formatting - 6 points
    # ============================================================
    format_score, format_feedback = check_analysis_formatting(sheet)
    results["format_score"] = format_score
    results["format_feedback"] = format_feedback
    
    return results
