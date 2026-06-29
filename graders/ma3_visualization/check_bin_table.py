"""
check_bin_table.py — Validates bin table formulas in E22:E24

Grading: 6 points total (2 pts each)
    E22: Bin Min = MIN(B12:B61) or MIN of difference data
    E23: Bin Max = MAX(B12:B61) or MAX of difference data
    E24: Bin Width = (Max - Min) / number_of_bins
"""

import re
from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


def _check_min_formula(formula: str) -> bool:
    """Check if formula uses MIN function on difference data."""
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Must use MIN function
    if "MIN(" not in normalized:
        return False
    
    # Should reference the difference data column (B in Visualization)
    # Valid patterns:
    #   - B12:B61, $B$12:$B$61 (explicit range)
    #   - B:B, $B:$B (entire column reference - valid approach)
    #   - B14:B63 (if they copied from Analysis sheet reference)
    if "B:B" in normalized or "$B:$B" in normalized:
        return True
    if "B" in normalized and ("12" in normalized or "14" in normalized):
        return True
    
    return False


def _check_max_formula(formula: str) -> bool:
    """Check if formula uses MAX function on difference data."""
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Must use MAX function
    if "MAX(" not in normalized:
        return False
    
    # Should reference the difference data column (B in Visualization)
    # Valid patterns:
    #   - B12:B61, $B$12:$B$61 (explicit range)
    #   - B:B, $B:$B (entire column reference - valid approach)
    #   - B14:B63 (if they copied from Analysis sheet reference)
    if "B:B" in normalized or "$B:$B" in normalized:
        return True
    if "B" in normalized and ("12" in normalized or "61" in normalized or "63" in normalized or "14" in normalized):
        return True
    
    return False


def _check_width_formula(formula: str) -> bool:
    """
    Check if formula calculates bin width.
    
    Expected patterns:
        =(E23-E22)/10
        =(E23-E22)/11
        =($E$23-$E$22)/10
        =(Max-Min)/n
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Remove dollar signs for easier matching
    normalized_no_dollars = normalized.replace("$", "")
    
    # Must have division
    if "/" not in normalized:
        return False
    
    # Should reference E22 and E23 (or calculate max-min)
    if "E22" in normalized_no_dollars and "E23" in normalized_no_dollars:
        return True
    
    # Or reference the max/min cells with subtraction
    if "MAX" in normalized and "MIN" in normalized and "-" in normalized:
        return True
    
    return False


def check_bin_table(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check bin table formulas in E22, E23, E24.
    
    Args:
        sheet: Visualization worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_count = 0
    points_per_cell = 2.0
    
    # Check E22 (Bin Min)
    cell = sheet["E22"]
    formula = cell.value
    
    if formula is None or str(formula).strip() == "":
        feedback.append(("BIN_MIN_MISSING", {}))
    elif not isinstance(formula, str) or not formula.startswith("="):
        feedback.append(("BIN_MIN_WRONG", {}))
    elif _check_min_formula(formula):
        correct_count += 1
        feedback.append(("BIN_MIN_OK", {}))
    else:
        feedback.append(("BIN_MIN_WRONG", {}))
    
    # Check E23 (Bin Max)
    cell = sheet["E23"]
    formula = cell.value
    
    if formula is None or str(formula).strip() == "":
        feedback.append(("BIN_MAX_MISSING", {}))
    elif not isinstance(formula, str) or not formula.startswith("="):
        feedback.append(("BIN_MAX_WRONG", {}))
    elif _check_max_formula(formula):
        correct_count += 1
        feedback.append(("BIN_MAX_OK", {}))
    else:
        feedback.append(("BIN_MAX_WRONG", {}))
    
    # Check E24 (Bin Width)
    cell = sheet["E24"]
    formula = cell.value
    
    if formula is None or str(formula).strip() == "":
        feedback.append(("BIN_WIDTH_MISSING", {}))
    elif not isinstance(formula, str) or not formula.startswith("="):
        feedback.append(("BIN_WIDTH_WRONG", {}))
    elif _check_width_formula(formula):
        correct_count += 1
        feedback.append(("BIN_WIDTH_OK", {}))
    else:
        feedback.append(("BIN_WIDTH_WRONG", {}))
    
    # Calculate score
    score = round(correct_count * points_per_cell, 2)
    
    # Summary feedback
    if correct_count == 3:
        feedback = [("BIN_ALL_CORRECT", {})]
    elif correct_count == 0:
        feedback.insert(0, ("BIN_NONE_CORRECT", {}))
    else:
        feedback.insert(0, ("BIN_PARTIAL", {"correct": correct_count}))
    
    return score, feedback
