"""
grade_visualization.py — Main orchestrator for MA3 Visualization tab grading

Purpose: Coordinates all grading checks for the Visualization worksheet tab.
         Aggregates scores and feedback from individual checker modules.

Author: Clayton Ragsdale
Dependencies: check_*.py modules in this package

Grading Breakdown (46 points total):
    Bin Table (E22:E24): 6 points (2 pts each)
    Lower/Upper Limits (D28:E38): 12 points (6 pts each column)
    Title/Freq/RelFreq (F28:H38): 18 points (6 pts each column)
    Histogram: 6 points
    Formatting: 4 points
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from .check_bin_table import check_bin_table
from .check_freq_dist import check_freq_dist_limits, check_freq_dist_values
from .check_histogram import check_histogram
from .check_formatting import check_visualization_formatting


def grade_visualization_tab(sheet: Worksheet) -> Dict[str, Any]:
    """
    Visualization tab grading orchestrator.
    
    Args:
        sheet: The openpyxl Worksheet object for the Visualization tab
    
    Returns:
        Dict containing scores and feedback for each competency:
            - bin_score, bin_feedback
            - limits_score, limits_feedback
            - freqdist_score, freqdist_feedback
            - histogram_score, histogram_feedback
            - format_score, format_feedback
    """
    results: Dict[str, Any] = {}
    
    # ============================================================
    # Bin Table (E22:E24) - 6 points
    # Min, Max, Width formulas
    # ============================================================
    bin_score, bin_feedback = check_bin_table(sheet)
    results["bin_score"] = bin_score
    results["bin_feedback"] = bin_feedback
    
    # ============================================================
    # Lower/Upper Limits (D28:E38) - 12 points
    # ============================================================
    limits_score, limits_feedback = check_freq_dist_limits(sheet)
    results["limits_score"] = limits_score
    results["limits_feedback"] = limits_feedback
    
    # ============================================================
    # Title of Bin / Frequency / Relative Frequency - 18 points
    # F28:F38 (Title), G28:G38 (Freq), H28:H38 (RelFreq)
    # ============================================================
    freqdist_score, freqdist_feedback = check_freq_dist_values(sheet)
    results["freqdist_score"] = freqdist_score
    results["freqdist_feedback"] = freqdist_feedback
    
    # ============================================================
    # Histogram - 6 points
    # Bar chart with correct data and axis labels
    # ============================================================
    histogram_score, histogram_feedback = check_histogram(sheet)
    results["histogram_score"] = histogram_score
    results["histogram_feedback"] = histogram_feedback
    
    # ============================================================
    # Formatting - 4 points
    # ============================================================
    format_score, format_feedback = check_visualization_formatting(sheet)
    results["format_score"] = format_score
    results["format_feedback"] = format_feedback
    
    return results
