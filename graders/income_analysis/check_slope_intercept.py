"""
check_slope_intercept.py — Validate SLOPE and INTERCEPT formulas

Purpose: Checks that students have correctly entered the SLOPE() and INTERCEPT()
         Excel functions in cells B30 and B31 respectively. These formulas should
         use the income data (B19:B26) as Y values and years of experience (A19:A26)
         as X values.

Author: Clayton Ragsdale
Dependencies: None (uses only openpyxl worksheet objects)

Common Student Mistakes:
    - Swapping X and Y ranges (most common - partial credit given)
    - Using wrong cell ranges
    - Not using formulas at all (entering values manually)
"""

from typing import Tuple, List, Dict, Any
from openpyxl.worksheet.worksheet import Worksheet


def check_slope_intercept(ws: Worksheet) -> Tuple[int, List[Tuple[str, Dict[str, Any]]]]:
    """
    Check the slope and intercept formulas in B30 and B31.
    
    Expected Formulas:
        - B30: =SLOPE(B19:B26,A19:A26)  # (y_values, x_values)
        - B31: =INTERCEPT(B19:B26,A19:A26)  # (y_values, x_values)
    
    Grading Logic:
        For each formula (slope and intercept):
        - 3 points: Correct formula with correct ranges
        - 2 points: Correct function with reversed X/Y ranges (common mistake)
        - 1 point: Uses the correct function but with wrong ranges
        - 0 points: Missing, not a formula, or using wrong function
        
        Total possible: 6 points
    
    The function also detects when both formulas have reversed X/Y ranges
    and adds summary feedback explaining the common mistake.
    
    Args:
        ws: The openpyxl Worksheet object for the Income Analysis tab
    
    Returns:
        Tuple of:
            - score: int (0-6)
            - feedback: List of (code, params) tuples describing each check
    
    Example:
        >>> score, feedback = check_slope_intercept(worksheet)
        >>> print(f"Slope/Intercept formula score: {score}/6")
        >>> for code, params in feedback:
        ...     print(f"{code}: {params}")
    """
    # Get cell values for slope and intercept
    slope_cell = ws["B30"]
    intercept_cell = ws["B31"]

    # Normalize formulas for comparison:
    # - Strip whitespace
    # - Remove spaces
    # - Remove $ (absolute references)
    # - Convert to uppercase for case-insensitive comparison
    slope_formula = ""
    if isinstance(slope_cell.value, str):
        slope_formula = slope_cell.value.strip().replace(" ", "").replace("$", "").upper()
    
    intercept_formula = ""
    if isinstance(intercept_cell.value, str):
        intercept_formula = intercept_cell.value.strip().replace(" ", "").replace("$", "").upper()

    score = 0
    feedback: List[Tuple[str, Dict[str, Any]]] = []

    # Define correct and reversed formula patterns
    # Correct: SLOPE(y_values, x_values) where y=income (B), x=years (A)
    correct_slope = "=SLOPE(B19:B26,A19:A26)"
    correct_intercept = "=INTERCEPT(B19:B26,A19:A26)"
    
    # Reversed: Common mistake where students swap X and Y arguments
    reversed_slope = "=SLOPE(A19:A26,B19:B26)"
    reversed_intercept = "=INTERCEPT(A19:A26,B19:B26)"

    # Track if X and Y are reversed (for summary feedback)
    slope_reversed = False
    intercept_reversed = False

    # ============================================================
    # Check Slope Formula (B30)
    # ============================================================
    if slope_formula == correct_slope:
        # Perfect: Correct function with correct argument order
        score += 3
        feedback.append(("IA_SLOPE_CORRECT", {"cell": "B30"}))
    elif slope_formula == reversed_slope:
        # Partial credit: Function is right but X/Y are swapped
        score += 2
        slope_reversed = True
        feedback.append(("IA_SLOPE_REVERSED", {"cell": "B30"}))
    elif "SLOPE(" in slope_formula:
        # Minimal credit: Using SLOPE but with wrong ranges
        score += 1
        feedback.append(("IA_SLOPE_WRONG_RANGE", {"cell": "B30"}))
    else:
        # No credit: Missing formula or using wrong function
        feedback.append(("IA_SLOPE_MISSING", {"cell": "B30"}))

    # ============================================================
    # Check Intercept Formula (B31)
    # ============================================================
    if intercept_formula == correct_intercept:
        # Perfect: Correct function with correct argument order
        score += 3
        feedback.append(("IA_INTERCEPT_CORRECT", {"cell": "B31"}))
    elif intercept_formula == reversed_intercept:
        # Partial credit: Function is right but X/Y are swapped
        score += 2
        intercept_reversed = True
        feedback.append(("IA_INTERCEPT_REVERSED", {"cell": "B31"}))
    elif "INTERCEPT(" in intercept_formula:
        # Minimal credit: Using INTERCEPT but with wrong ranges
        score += 1
        feedback.append(("IA_INTERCEPT_WRONG_RANGE", {"cell": "B31"}))
    else:
        # No credit: Missing formula or using wrong function
        feedback.append(("IA_INTERCEPT_MISSING", {"cell": "B31"}))

    # ============================================================
    # Add summary if both formulas have reversed X/Y
    # ============================================================
    # This is a common conceptual mistake worth highlighting
    if slope_reversed and intercept_reversed:
        feedback.insert(0, ("IA_XY_DATA_SWAPPED", {
            "note": "X and Y data ranges are swapped in both formulas. "
                    "SLOPE and INTERCEPT expect (Y_values, X_values). "
                    "Received 4/6 for formulas (-2 points)."
        }))

    return score, feedback
