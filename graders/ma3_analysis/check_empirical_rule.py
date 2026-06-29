"""
check_empirical_rule.py — Validates empirical rule calculations in G36:G37

Grading: 6 points total (3 pts each)

Expected formulas:
    G36 (Lower Bound): =I18-I20  (Mean - StdDev)
    G37 (Upper Bound): =I18+I20  (Mean + StdDev)

Partial Credit (50%):
    - Has the right structure (cell - cell or cell + cell) but wrong cell references
    - Shows understanding of Mean ± StdDev concept even if referencing wrong rows/columns
"""

import re
from typing import Tuple, List, Union
from openpyxl.worksheet.worksheet import Worksheet


# Credit multipliers
CREDIT_FULL = 1.0
CREDIT_WRONG_REFS = 0.5  # Right structure, wrong cell references
CREDIT_NONE = 0.0


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


def _check_lower_bound_formula(formula: str) -> float:
    """
    Check if formula calculates Mean - StdDev.
    Expected: =I18-I20 or =AVERAGE(...)-STDEV(...)
    
    Returns: credit multiplier (1.0, 0.5, or 0.0)
    """
    if not formula or not formula.startswith("="):
        return CREDIT_NONE
    
    normalized = _normalize_formula(formula)
    
    # Remove dollar signs for easier matching
    normalized_no_dollars = normalized.replace("$", "")
    
    # FULL CREDIT: References I18 (mean) and I20 (stdev) with subtraction
    if "I18" in normalized_no_dollars and "I20" in normalized_no_dollars and "-" in normalized:
        return CREDIT_FULL
    
    # FULL CREDIT: Calculates Mean - StdDev directly using functions
    # Pattern: =AVERAGE(...)-STDEV(...) or =AVERAGE(...)-STDEV.S(...) etc.
    has_average = "AVERAGE(" in normalized
    has_stdev = any(s in normalized for s in ["STDEV(", "STDEV.S(", "STDEV.P("])
    has_subtraction = "-" in normalized
    if has_average and has_stdev and has_subtraction:
        return CREDIT_FULL
    
    # PARTIAL CREDIT: Has subtraction pattern with cell references (wrong cells)
    # Pattern: =CELL-CELL where CELL is like G18, H20, I21, etc.
    subtraction_pattern = r'^=\$?[A-Z]\$?\d+\s*-\s*\$?[A-Z]\$?\d+$'
    if re.match(subtraction_pattern, normalized_no_dollars):
        # They have the right structure but wrong references
        return CREDIT_WRONG_REFS
    
    # Also accept patterns like =(G18-I20) with parentheses
    paren_pattern = r'^=\(\$?[A-Z]\$?\d+\s*-\s*\$?[A-Z]\$?\d+\)$'
    if re.match(paren_pattern, normalized_no_dollars):
        # Check if they got I18 and I20 (full credit) or not (partial)
        if "I18" in normalized_no_dollars and "I20" in normalized_no_dollars:
            return CREDIT_FULL
        return CREDIT_WRONG_REFS
    
    return CREDIT_NONE


def _check_upper_bound_formula(formula: str) -> float:
    """
    Check if formula calculates Mean + StdDev.
    Expected: =I18+I20 or =AVERAGE(...)+STDEV(...)
    
    Returns: credit multiplier (1.0, 0.5, or 0.0)
    """
    if not formula or not formula.startswith("="):
        return CREDIT_NONE
    
    normalized = _normalize_formula(formula)
    
    # Remove dollar signs for easier matching
    normalized_no_dollars = normalized.replace("$", "")
    
    # FULL CREDIT: References I18 (mean) and I20 (stdev) with addition
    if "I18" in normalized_no_dollars and "I20" in normalized_no_dollars and "+" in normalized:
        return CREDIT_FULL
    
    # FULL CREDIT: Calculates Mean + StdDev directly using functions
    # Pattern: =AVERAGE(...)+STDEV(...) or =AVERAGE(...)+STDEV.S(...) etc.
    has_average = "AVERAGE(" in normalized
    has_stdev = any(s in normalized for s in ["STDEV(", "STDEV.S(", "STDEV.P("])
    has_addition = "+" in normalized
    if has_average and has_stdev and has_addition:
        return CREDIT_FULL
    
    # PARTIAL CREDIT: Has addition pattern with cell references (wrong cells)
    # Pattern: =CELL+CELL where CELL is like G18, H20, I21, etc.
    addition_pattern = r'^=\$?[A-Z]\$?\d+\s*\+\s*\$?[A-Z]\$?\d+$'
    if re.match(addition_pattern, normalized_no_dollars):
        # They have the right structure but wrong references
        return CREDIT_WRONG_REFS
    
    # Also accept patterns like =(G18+I20) with parentheses
    paren_pattern = r'^=\(\$?[A-Z]\$?\d+\s*\+\s*\$?[A-Z]\$?\d+\)$'
    if re.match(paren_pattern, normalized_no_dollars):
        # Check if they got I18 and I20 (full credit) or not (partial)
        if "I18" in normalized_no_dollars and "I20" in normalized_no_dollars:
            return CREDIT_FULL
        return CREDIT_WRONG_REFS
    
    return CREDIT_NONE


def check_empirical_rule(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check empirical rule formulas in G36 (lower) and G37 (upper).
    
    Args:
        sheet: Analysis worksheet
        
    Returns:
        Tuple of (score, feedback_list)
        
    Partial Credit:
        - Full credit (100%): Correct formula =I18±I20
        - Partial credit (50%): Right structure (cell±cell) but wrong references
        - No credit: Missing, not a formula, or wrong structure
    """
    feedback = []
    total_score = 0.0
    points_per_cell = 3.0
    full_credit_count = 0
    partial_credit_count = 0
    
    # Check Lower Bound (G36)
    cell_ref = "G36"
    cell = sheet[cell_ref]
    formula = cell.value
    
    if formula is None or str(formula).strip() == "":
        feedback.append(("EMPIRICAL_LOWER_MISSING", {"cell": cell_ref}))
    elif not isinstance(formula, str) or not formula.startswith("="):
        feedback.append(("EMPIRICAL_LOWER_WRONG", {"cell": cell_ref}))
    else:
        credit = _check_lower_bound_formula(formula)
        if credit == CREDIT_FULL:
            total_score += points_per_cell
            full_credit_count += 1
            feedback.append(("EMPIRICAL_LOWER_OK", {"cell": cell_ref}))
        elif credit == CREDIT_WRONG_REFS:
            total_score += points_per_cell * CREDIT_WRONG_REFS
            partial_credit_count += 1
            feedback.append(("EMPIRICAL_LOWER_PARTIAL", {
                "cell": cell_ref,
                "reason": "wrong_refs",
                "hint": "Correct structure (Mean - StdDev) but should reference I18 (Mean) and I20 (StdDev)",
                "found": formula
            }))
        else:
            feedback.append(("EMPIRICAL_LOWER_WRONG", {"cell": cell_ref}))
    
    # Check Upper Bound (G37)
    cell_ref = "G37"
    cell = sheet[cell_ref]
    formula = cell.value
    
    if formula is None or str(formula).strip() == "":
        feedback.append(("EMPIRICAL_UPPER_MISSING", {"cell": cell_ref}))
    elif not isinstance(formula, str) or not formula.startswith("="):
        feedback.append(("EMPIRICAL_UPPER_WRONG", {"cell": cell_ref}))
    else:
        credit = _check_upper_bound_formula(formula)
        if credit == CREDIT_FULL:
            total_score += points_per_cell
            full_credit_count += 1
            feedback.append(("EMPIRICAL_UPPER_OK", {"cell": cell_ref}))
        elif credit == CREDIT_WRONG_REFS:
            total_score += points_per_cell * CREDIT_WRONG_REFS
            partial_credit_count += 1
            feedback.append(("EMPIRICAL_UPPER_PARTIAL", {
                "cell": cell_ref,
                "reason": "wrong_refs",
                "hint": "Correct structure (Mean + StdDev) but should reference I18 (Mean) and I20 (StdDev)",
                "found": formula
            }))
        else:
            feedback.append(("EMPIRICAL_UPPER_WRONG", {"cell": cell_ref}))
    
    # Calculate score
    score = round(total_score, 2)
    
    # Summary feedback
    if full_credit_count == 2:
        feedback = [("EMPIRICAL_ALL_CORRECT", {})]
    elif full_credit_count == 0 and partial_credit_count == 0:
        feedback.insert(0, ("EMPIRICAL_NONE_CORRECT", {}))
    elif partial_credit_count > 0:
        feedback.insert(0, ("EMPIRICAL_PARTIAL_CREDIT", {
            "full_credit": full_credit_count,
            "partial_credit": partial_credit_count,
            "score": score,
            "max_score": 6.0
        }))
    else:
        feedback.insert(0, ("EMPIRICAL_PARTIAL", {"correct": full_credit_count}))
    
    return score, feedback
