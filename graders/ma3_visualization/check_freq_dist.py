"""
check_freq_dist.py — Validates frequency distribution table formulas

Grading:
    Lower/Upper Limits (D28:E38): 12 points (6 pts each column)
    Title/Freq/RelFreq (F28:H38): 18 points (6 pts each column)

Cell layout (rows 28-38):
    D: Lower Limit
    E: Upper Limit
    F: Title of Bin (midpoint)
    G: Frequency (COUNTIF/COUNTIFS/FREQUENCY)
    H: Relative Frequency (freq/total)
"""

import re
from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


def _check_lower_limit_formula(formula: str, row: int) -> bool:
    """
    Check if lower limit formula is correct.
    
    Row 28: Should equal E22 (bin min) or E22-0.1
    Rows 29+: Should equal previous upper limit (E{row-1})
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    if row == 28:
        # First row - should reference E22 (bin min)
        if "E22" in normalized:
            return True
    else:
        # Subsequent rows - should reference previous upper limit
        prev_row = row - 1
        if f"E{prev_row}" in normalized:
            return True
    
    return False


def _check_upper_limit_formula(formula: str, row: int) -> bool:
    """
    Check if upper limit formula is correct.
    
    Should equal lower limit + bin width
    Pattern: =D{row}+$E$24 or =D{row}+E24
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Should reference D{row} and E24 (bin width) with addition
    if f"D{row}" in normalized and "E24" in normalized and "+" in normalized:
        return True
    
    # Also accept $E$24
    if f"D{row}" in normalized and "$E$24" in normalized:
        return True
    
    return False


def _check_title_formula(formula: str, row: int) -> bool:
    """
    Check if title of bin formula calculates midpoint.
    
    Expected: =(D{row}+E{row})/2
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Remove dollar signs for easier matching
    normalized_no_dollars = normalized.replace("$", "")
    
    # Should have D{row}, E{row}, addition, and division by 2
    if f"D{row}" in normalized_no_dollars and f"E{row}" in normalized_no_dollars:
        if "+" in normalized and "/2" in normalized:
            return True
        if "+" in normalized and "2" in normalized:
            return True
    
    return False


def _check_frequency_formula(formula: str) -> bool:
    """
    Check if frequency formula uses COUNTIF, COUNTIFS, or FREQUENCY.
    
    Accept various patterns:
        =COUNTIFS(range, ">="&lower, range, "<="&upper)
        =COUNTIF(range, ">="&D28) - COUNTIF(range, ">"&E28)
        =FREQUENCY(data, bins)
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Check for counting functions
    if "COUNTIFS(" in normalized:
        return True
    
    if "COUNTIF(" in normalized:
        return True
    
    if "FREQUENCY(" in normalized:
        return True
    
    # Also accept SUM with conditional logic
    if "SUMPRODUCT(" in normalized:
        return True
    
    return False


def _check_relative_freq_formula(formula: str, row: int) -> bool:
    """
    Check if relative frequency formula divides by total.
    
    Expected patterns:
        =G{row}/50
        =G{row}/SUM($G$28:$G$38)
        =G{row}/SUM(G:G)
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Must reference the frequency cell for this row
    if f"G{row}" not in normalized:
        return False
    
    # Must have division
    if "/" not in normalized:
        return False
    
    return True


def check_freq_dist_limits(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check Lower Limit (D28:D38) and Upper Limit (E28:E38) formulas.
    
    Args:
        sheet: Visualization worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_lower = 0
    correct_upper = 0
    total_rows = 11  # Rows 28-38
    
    for row in range(28, 39):
        # Check Lower Limit
        cell_ref = f"D{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_LOWER_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("FREQ_LOWER_WRONG", {"cell": cell_ref}))
        elif _check_lower_limit_formula(formula, row):
            correct_lower += 1
        else:
            feedback.append(("FREQ_LOWER_WRONG", {"cell": cell_ref}))
        
        # Check Upper Limit
        cell_ref = f"E{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_UPPER_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("FREQ_UPPER_WRONG", {"cell": cell_ref}))
        elif _check_upper_limit_formula(formula, row):
            correct_upper += 1
        else:
            feedback.append(("FREQ_UPPER_WRONG", {"cell": cell_ref}))
    
    # Calculate score (6 pts each column)
    lower_score = (correct_lower / total_rows) * 6.0
    upper_score = (correct_upper / total_rows) * 6.0
    total_score = round(lower_score + upper_score, 2)
    
    total_correct = correct_lower + correct_upper
    total_cells = total_rows * 2
    
    # Summary feedback
    if total_correct == total_cells:
        feedback = [("FREQ_LIMITS_ALL_CORRECT", {})]
    elif total_correct == 0:
        feedback.insert(0, ("FREQ_LIMITS_NONE_CORRECT", {}))
    else:
        feedback.insert(0, ("FREQ_LIMITS_PARTIAL", {"correct": total_correct, "total": total_cells}))
    
    return total_score, feedback


def check_freq_dist_values(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check Title of Bin (F), Frequency (G), and Relative Frequency (H) formulas.
    
    Args:
        sheet: Visualization worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_title = 0
    correct_freq = 0
    correct_relfreq = 0
    total_rows = 11  # Rows 28-38
    
    for row in range(28, 39):
        # Check Title of Bin (F column)
        cell_ref = f"F{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_TITLE_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("FREQ_TITLE_WRONG", {"cell": cell_ref}))
        elif _check_title_formula(formula, row):
            correct_title += 1
        else:
            feedback.append(("FREQ_TITLE_WRONG", {"cell": cell_ref}))
        
        # Check Frequency (G column)
        cell_ref = f"G{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_COUNT_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            # Check if it's an ArrayFormula object
            if hasattr(formula, '__class__') and 'ArrayFormula' in formula.__class__.__name__:
                correct_freq += 1  # Array formulas are acceptable
            else:
                feedback.append(("FREQ_COUNT_WRONG", {"cell": cell_ref}))
        elif _check_frequency_formula(formula):
            correct_freq += 1
        else:
            feedback.append(("FREQ_COUNT_WRONG", {"cell": cell_ref}))
        
        # Check Relative Frequency (H column)
        cell_ref = f"H{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_REL_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("FREQ_REL_WRONG", {"cell": cell_ref}))
        elif _check_relative_freq_formula(formula, row):
            correct_relfreq += 1
        else:
            feedback.append(("FREQ_REL_WRONG", {"cell": cell_ref}))
    
    # Calculate score (6 pts each column)
    title_score = (correct_title / total_rows) * 6.0
    freq_score = (correct_freq / total_rows) * 6.0
    relfreq_score = (correct_relfreq / total_rows) * 6.0
    total_score = round(title_score + freq_score + relfreq_score, 2)
    
    total_correct = correct_title + correct_freq + correct_relfreq
    total_cells = total_rows * 3
    
    # Summary feedback
    if total_correct == total_cells:
        feedback = [("FREQ_DIST_ALL_CORRECT", {})]
    elif total_correct == 0:
        feedback.insert(0, ("FREQ_DIST_NONE_CORRECT", {}))
    else:
        feedback.insert(0, ("FREQ_DIST_PARTIAL", {"correct": total_correct, "total": total_cells}))
    
    return total_score, feedback
