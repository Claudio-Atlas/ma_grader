"""
check_predictions.py — Validate predicted salary formulas in E19:E35

Purpose: Checks that students have correctly entered prediction formulas that
         calculate predicted salary based on years of experience using the
         slope and intercept values from B30 and B31.

Author: Clayton Ragsdale
Dependencies: openpyxl.worksheet.formula (for ArrayFormula handling)

Expected Formula Pattern:
    Each cell E19:E35 should contain: =B30*D{row}+B31
    Where D{row} is the years of experience for that row.
    
Technical Note:
    We open workbooks with data_only=False to preserve formula text,
    which means we can't verify calculated values directly. The formula
    reference check is sufficient - if a student references the correct
    cells, their formula will produce the correct result.
"""

import re
from typing import Tuple, List, Dict, Any
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.formula import ArrayFormula
from utilities.formula_equiv import formulas_equivalent


def _has_required_refs(formula: str) -> bool:
    """
    Check if formula contains both B30 (slope) and B31 (intercept) cell references.
    
    This validation ensures the prediction formula uses the calculated slope
    and intercept values rather than hardcoded numbers.
    
    Args:
        formula: The Excel formula string to check
    
    Returns:
        bool: True if both B30 and B31 are referenced
    
    Example:
        >>> _has_required_refs("=B30*D19+B31")
        True
        >>> _has_required_refs("=$B$30*D19+$B$31")
        True
        >>> _has_required_refs("=5000*D19+30000")
        False
    """
    if not formula:
        return False
    # Remove $ signs to handle absolute references like $B$30
    # Convert to uppercase for case-insensitive comparison
    normalized = formula.upper().replace("$", "")
    return "B30" in normalized and "B31" in normalized


def _has_linear_structure(formula: str) -> bool:
    """
    Check if formula has y=mx+b structure (multiplication and addition/subtraction).
    
    This is used for partial credit when students hardcode slope/intercept
    but have the correct mathematical structure.
    
    Args:
        formula: The Excel formula string to check
    
    Returns:
        bool: True if formula has multiplication AND addition/subtraction
    
    Example:
        >>> _has_linear_structure("=148.85*D19-868.95")
        True
        >>> _has_linear_structure("=B30*D19+B31")
        True
        >>> _has_linear_structure("=D19*5")  # No addition/subtraction
        False
    """
    if not formula:
        return False
    has_mult = "*" in formula
    has_add_sub = "+" in formula or "-" in formula.replace("=-", "").replace("E-", "")  # Ignore leading minus or scientific notation
    return has_mult and has_add_sub


def _has_years_ref(formula: str, row: int) -> bool:
    """
    Check if formula references the years of experience cell for this row.
    
    The formula should reference D{row} for the corresponding years value.
    For example, E19's formula should reference D19.
    
    Args:
        formula: The Excel formula string to check
        row: The row number (19-35)
    
    Returns:
        bool: True if the formula references D{row}
    
    Example:
        >>> _has_years_ref("=B30*D19+B31", 19)
        True
        >>> _has_years_ref("=$B$30*$D$19+$B$31", 19)
        True
        >>> _has_years_ref("=B30*D19+B31", 20)  # Wrong row
        False
    """
    if not formula:
        return False
    # Remove $ signs to normalize absolute/mixed references
    normalized = formula.upper().replace("$", "")
    return f"D{row}" in normalized


def check_predictions(ws: Worksheet) -> Tuple[float, List[Tuple[str, Dict[str, Any]]]]:
    """
    Check predicted salary values in cells E19:E35.
    
    Each prediction formula should:
        1. Reference B30 (slope)
        2. Reference B31 (intercept)
        3. Reference the corresponding D column cell (years of experience)
    
    Expected Formula Pattern:
        =B30*D19+B31 (for row 19)
        =B30*D20+B31 (for row 20)
        ... and so on through row 35
    
    Grading Logic:
        - 6 points total for all 17 rows (E19:E35)
        - Points are proportional: (correct_count / 17) * 6
        - Full credit requires ALL cells to have correct formulas
    
    Error Categories:
        - NOT_FORMULAS: Cell contains a value instead of a formula
        - MISSING_REFS: Formula doesn't reference B30 and/or B31
        - MISSING_YEARS: Formula doesn't reference the correct D column cell
    
    Args:
        ws: The openpyxl Worksheet object for the Income Analysis tab
    
    Returns:
        Tuple of:
            - score: float (0.0 to 6.0)
            - feedback: List of (code, params) tuples describing results
    
    Example:
        >>> score, feedback = check_predictions(worksheet)
        >>> print(f"Predictions score: {score}/6.0")
    """
    total_rows = 17  # E19 through E35

    # ------------------------------------------------------------------
    # Dynamic-array (spill) formula case: a single formula entered in E19
    # such as =B30*D19:D35+B31 spills down the whole range. Only E19 holds
    # the formula; E20:E35 are spill cells. Detect and credit it in full.
    # ------------------------------------------------------------------
    e19_raw = ws["E19"].value
    e19_formula = (
        e19_raw.text if isinstance(e19_raw, ArrayFormula)
        else e19_raw if isinstance(e19_raw, str) else ""
    )
    if e19_formula:
        norm = e19_formula.upper().replace("$", "").replace(" ", "")
        d_range = re.search(r"D(\d+):D(\d+)", norm)
        # Require multiplication (slope * years), so the wrong all-addition
        # spill form =B30+D19:D35+B31 does not get full credit.
        if "B30" in norm and "B31" in norm and "*" in norm and d_range:
            start, end = int(d_range.group(1)), int(d_range.group(2))
            if start <= 19 and end >= 35:
                return 6.0, [("IA_PREDICTIONS_ALL_CORRECT", {"range": "E19:E35"})]

    correct_count = 0
    missing_slope_intercept = 0
    missing_years_ref = 0
    not_formula = 0
    hardcoded_linear = 0  # Has y=mx+b structure but hardcoded values

    # Check each prediction cell
    for row in range(19, 36):  # Rows 19-35 inclusive
        cell = ws[f"E{row}"]
        value = cell.value
        
        # Handle ArrayFormula objects (Excel 365 dynamic arrays)
        # Modern Excel can return formulas as ArrayFormula objects
        if isinstance(value, ArrayFormula):
            formula = value.text
        elif isinstance(value, str) and value.startswith("="):
            # Standard formula string
            formula = value
        else:
            # Not a formula (either a hardcoded value or empty)
            not_formula += 1
            continue
        
        # Check 1: Does formula reference B30 AND B31?
        has_slope_intercept = _has_required_refs(formula)

        # Check 2: Does formula reference the years column for this row?
        has_years = _has_years_ref(formula, row)

        # Check 3: Does formula have y=mx+b structure (for partial credit)?
        has_linear_structure = _has_linear_structure(formula)

        # Check 4: Is it MATHEMATICALLY the prediction slope*years+intercept?
        # This is what rejects the wrong all-addition form =B30+D{row}+B31, which
        # references the right cells but doesn't multiply. The equivalence engine
        # accepts operand-order variants (=D{row}*B30+B31, =B31+B30*D{row}).
        is_math_correct = formulas_equivalent(formula, f"=B30*D{row}+B31")

        # Categorize the result
        if is_math_correct:
            # Formula is correct (references AND multiplies correctly)
            correct_count += 1
        elif has_slope_intercept and not has_years:
            # Has slope/intercept but wrong/missing years reference
            missing_years_ref += 1
        elif not has_slope_intercept and has_years and has_linear_structure:
            # Has y=mx+b structure with years ref but hardcoded slope/intercept
            hardcoded_linear += 1
        else:
            # Missing refs, or refs present but wrong structure (e.g. + instead of *)
            missing_slope_intercept += 1

    # ============================================================
    # Build Feedback
    # ============================================================
    feedback: List[Tuple[str, Dict[str, Any]]] = []
    
    # All correct - full credit
    if correct_count == total_rows:
        return 6.0, [("IA_PREDICTIONS_ALL_CORRECT", {"range": "E19:E35"})]

    # Check for hardcoded linear formulas (half credit case)
    # If ALL formulas have y=mx+b structure but hardcoded values, give 50% credit
    if correct_count == 0 and hardcoded_linear == total_rows:
        feedback.append(("IA_PREDICTIONS_HARDCODED", {
            "count": hardcoded_linear,
            "range": "E19:E35",
            "note": "Formulas have correct y=mx+b structure but use hardcoded slope/intercept values. Use B30 and B31 cell references for full credit."
        }))
        return 3.0, feedback  # Half credit (3 out of 6)
    
    # Partial hardcoded case - some correct, some hardcoded
    if hardcoded_linear > 0 and correct_count == 0:
        # All checked formulas are hardcoded (but maybe some weren't formulas at all)
        hardcoded_ratio = hardcoded_linear / total_rows
        score = round(3.0 * hardcoded_ratio, 1)  # Proportional half credit
        feedback.append(("IA_PREDICTIONS_HARDCODED", {
            "count": hardcoded_linear,
            "range": "E19:E35",
            "note": "Formulas have correct y=mx+b structure but use hardcoded slope/intercept values."
        }))
        return score, feedback

    # None correct - zero credit with specific feedback
    if correct_count == 0:
        if not_formula > 0:
            feedback.append(("IA_PREDICTIONS_NOT_FORMULAS", {
                "count": not_formula,
                "range": "E19:E35"
            }))
        if missing_slope_intercept > 0:
            feedback.append(("IA_PREDICTIONS_MISSING_REFS", {
                "count": missing_slope_intercept,
                "range": "E19:E35",
                "expected": "B30 (slope) and B31 (intercept)"
            }))
        if missing_years_ref > 0:
            feedback.append(("IA_PREDICTIONS_MISSING_YEARS", {
                "count": missing_years_ref,
                "range": "E19:E35"
            }))
        if not feedback:
            # Fallback if no specific issues identified
            feedback.append(("IA_PREDICTIONS_NONE_CORRECT", {"range": "E19:E35"}))
        return 0.0, feedback

    # Partial credit - proportional scoring (mix of correct and other)
    # Full credit for correct, half for hardcoded
    full_pts = correct_count * (6 / total_rows)
    half_pts = hardcoded_linear * (3 / total_rows)
    score = round(full_pts + half_pts, 1)
    
    # Build details string for partial credit feedback
    details = []
    if hardcoded_linear > 0:
        details.append(f"{hardcoded_linear} hardcoded (half credit)")
    if missing_slope_intercept > 0:
        details.append(f"{missing_slope_intercept} missing B30/B31 refs")
    if missing_years_ref > 0:
        details.append(f"{missing_years_ref} missing years ref")
    if not_formula > 0:
        details.append(f"{not_formula} not formulas")
    
    feedback.append(("IA_PREDICTIONS_PARTIAL", {
        "correct": correct_count,
        "total": total_rows,
        "range": "E19:E35",
        "issues": "; ".join(details) if details else ""
    }))
    
    return score, feedback
