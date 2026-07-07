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


# The frequency table has 11 bins (rows 28-38), so the bin width is the data
# range divided by 11.
NUM_BINS = 11


def _check_width_formula(formula: str, values_sheet=None) -> bool:
    """
    Check if formula calculates the bin width = (max - min) / number_of_bins.

    Accept:
        =(E23-E22)/11
        =($E$23-$E$22)/11
        =(MAX(...)-MIN(...))/11

    Reject:
        - wrong divisors (/5, /10, /50, ...) — must divide by 11 bins
        - the un-parenthesized =E23-E22/11, which Excel evaluates as
          E23-(E22/11) because division binds tighter than subtraction.
    """
    if not formula or not formula.startswith("="):
        return False

    normalized = _normalize_formula(formula).replace("$", "")

    # Must have division.
    if "/" not in normalized:
        return False

    # Divisor (number of bins) must be exactly 11 (not part of a longer number).
    div_ok = bool(re.search(r'/\(?11\)?(?![\d.])', normalized))

    # The subtraction must be grouped so operator precedence is correct.
    grouped_cells = ("(E23-E22)" in normalized) or ("(E22-E23)" in normalized)
    grouped_maxmin = (
        "MAX(" in normalized and "MIN(" in normalized and "-" in normalized
    )

    if div_ok and (grouped_cells or grouped_maxmin):
        return True

    # Value-based fallback: accept if the computed width equals (max-min)/11,
    # however the student expressed it (e.g. referencing a bin-count cell).
    if values_sheet is not None:
        try:
            mn = float(values_sheet["E22"].value)
            mx = float(values_sheet["E23"].value)
            got = float(values_sheet["E24"].value)
            expected = (mx - mn) / float(NUM_BINS)
            if expected != 0 and abs(got - expected) / abs(expected) <= 0.001:
                return True
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    return False


def check_bin_table(sheet: Worksheet, values_sheet: Worksheet = None) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check bin table formulas in E22, E23, E24.

    Args:
        sheet: Visualization worksheet (formulas)
        values_sheet: Visualization worksheet loaded data_only (calculated values),
                      used as a fallback to verify the bin-width value.

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
    elif _check_width_formula(formula, values_sheet):
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
