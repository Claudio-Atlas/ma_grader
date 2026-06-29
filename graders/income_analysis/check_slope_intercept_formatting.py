"""
check_slope_intercept_formatting.py — Validate slope/intercept number formatting

Purpose: Checks that the slope (B30) and intercept (B31) cells are formatted
         correctly as numbers with 0 decimal places. This ensures students
         understand proper number formatting in Excel.

Author: Clayton Ragsdale
Dependencies: None (uses only openpyxl worksheet objects)

Accepted Formats:
    - "0" or "#,##0" (standard number with no decimals)
    - Various Excel built-in number formats without decimals
    - "General" format is accepted (displays as integer for whole numbers)
"""

from typing import Tuple, List, Dict, Any
from openpyxl.worksheet.worksheet import Worksheet


def _is_zero_decimal_number_format(fmt: str) -> bool:
    """
    Check if a number format displays numbers with 0 decimal places.
    
    This function validates Excel number format strings to determine if they
    will display values without decimal places. It handles various Excel
    format string patterns.
    
    Args:
        fmt: The Excel number format string (e.g., "#,##0", "0.00", "General")
    
    Returns:
        bool: True if the format shows 0 decimal places, False otherwise
    
    Example:
        >>> _is_zero_decimal_number_format("#,##0")
        True
        >>> _is_zero_decimal_number_format("0.00")
        False
        >>> _is_zero_decimal_number_format("General")
        True
    """
    if not fmt or not isinstance(fmt, str):
        return False
    
    # Normalize: strip whitespace (don't lowercase - format strings are case-sensitive)
    fmt = fmt.strip()
    
    # Exact matches for common Excel formats without decimals
    allowed_exact = {
        "0",
        "0_",
        "0_)",
        "#,##0",
        "#,##0_",
        "#,##0_)",
        "0;-0;0",
        "#,##0;-#,##0;0",
        "#,##0;-#,##0",
        "#,##0_);(#,##0)",          # Accounting format (negative in parentheses)
        "#,##0_);[Red](#,##0)",     # Accounting format (negative in red)
        "0_);(0)",
        "0_);[Red](0)",
        "General",                   # General format displays whole numbers as integers
    }
    
    if fmt in allowed_exact:
        return True
    
    # Pattern-based check: reject formats with decimal places
    # Formats with ".0", ".00", ".#" etc. have decimal places
    if ".0" in fmt or ".#" in fmt:
        return False
    
    # Accept if it contains number placeholders (0 or #) and no decimals
    # This catches custom formats like "0 units" or similar
    has_number_chars = "0" in fmt or "#" in fmt
    if has_number_chars:
        return True
    
    return False


def check_slope_intercept_formatting(ws: Worksheet) -> Tuple[float, List[Tuple[str, Dict[str, Any]]]]:
    """
    Check formatting of slope (B30) and intercept (B31) cells.
    
    Expected Formatting:
        Both cells should be formatted as numbers with 0 decimal places.
        This could be achieved with formats like "#,##0", "0", or similar.
    
    Grading Logic:
        - 0.5 points: Slope (B30) formatted with 0 decimal places
        - 0.5 points: Intercept (B31) formatted with 0 decimal places
        - Total possible: 1.0 points
    
    Args:
        ws: The openpyxl Worksheet object for the Income Analysis tab
    
    Returns:
        Tuple of:
            - score: float (0.0, 0.5, or 1.0)
            - feedback: List of (code, params) tuples for each cell checked
    
    Example:
        >>> score, feedback = check_slope_intercept_formatting(worksheet)
        >>> print(f"Formatting score: {score}/1.0")
    """
    # Get the cells
    slope_cell = ws["B30"]
    intercept_cell = ws["B31"]

    # Get the number format applied to each cell
    slope_fmt = slope_cell.number_format
    intercept_fmt = intercept_cell.number_format

    score = 0.0
    feedback: List[Tuple[str, Dict[str, Any]]] = []

    # ============================================================
    # Check Slope Formatting (B30)
    # ============================================================
    if _is_zero_decimal_number_format(slope_fmt):
        score += 0.5
        feedback.append(("IA_SLOPE_FORMAT_CORRECT", {"cell": "B30"}))
    else:
        # Include the found format for debugging/feedback
        feedback.append(("IA_SLOPE_FORMAT_INCORRECT", {
            "cell": "B30",
            "found": slope_fmt
        }))

    # ============================================================
    # Check Intercept Formatting (B31)
    # ============================================================
    if _is_zero_decimal_number_format(intercept_fmt):
        score += 0.5
        feedback.append(("IA_INTERCEPT_FORMAT_CORRECT", {"cell": "B31"}))
    else:
        # Include the found format for debugging/feedback
        feedback.append(("IA_INTERCEPT_FORMAT_INCORRECT", {
            "cell": "B31",
            "found": intercept_fmt
        }))

    return score, feedback
