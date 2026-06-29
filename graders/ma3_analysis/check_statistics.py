"""
check_statistics.py — Validates statistics formulas (Mean, Median, StdDev, Range)

Grading: 24 points total (2 pts each × 12 cells)

Cell layout:
         G (Before)    H (After)    I (Difference)
Row 18:  Mean          Mean         Mean
Row 19:  Median        Median       Median  
Row 20:  StdDev        StdDev       StdDev
Row 21:  Range         Range        Range

Partial Credit Rules:
- 50% if student uses comma instead of colon (e.g., =AVERAGE(B14,B63) instead of B14:B63)
- 75% if range is slightly off (within 3 rows) due to drag-fill without absolute references
"""

import re
from typing import Tuple, List, Union
from openpyxl.worksheet.worksheet import Worksheet


# Partial credit multipliers
CREDIT_FULL = 1.0
CREDIT_RANGE_OFFSET = 0.75  # Range slightly off (drag-fill error, within 3 rows)
CREDIT_CORRECT_START = 0.50  # Correct function + correct start row, wrong end row
CREDIT_COMMA_NOT_COLON = 0.51  # Used comma instead of colon (slightly different to distinguish)
CREDIT_NONE = 0.0


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


def _extract_function_name(formula: str) -> str:
    """Extract the main function name from a formula."""
    if not formula or not formula.startswith("="):
        return ""
    
    normalized = _normalize_formula(formula)
    
    # Match function name at start (after =)
    match = re.match(r'^=([A-Z_.]+)\(', normalized)
    if match:
        return match.group(1)
    
    # Check for _xlfn. prefix (Excel internal format)
    match = re.match(r'^=_XLFN\.([A-Z_.]+)\(', normalized)
    if match:
        return match.group(1)
    
    return ""


def _uses_anchorarray(formula: str, expected_anchor_col: str) -> bool:
    """
    Check if formula uses ANCHORARRAY to reference a spill range.
    
    Excel 365 uses _xlfn.ANCHORARRAY(D14) to reference a dynamic array
    starting at D14. This is valid when the student used a spill formula
    for the differences.
    
    Args:
        formula: The formula string
        expected_anchor_col: The expected column for the anchor (e.g., "D" for differences)
    
    Returns:
        True if formula uses ANCHORARRAY correctly
    """
    if not formula:
        return False
    
    normalized = _normalize_formula(formula)
    
    # Check for ANCHORARRAY pattern: _XLFN.ANCHORARRAY(D14) or ANCHORARRAY(D14)
    patterns = [
        f"_XLFN.ANCHORARRAY({expected_anchor_col}14)",
        f"ANCHORARRAY({expected_anchor_col}14)",
        f"_XLFN.ANCHORARRAY(${expected_anchor_col}$14)",
        f"ANCHORARRAY(${expected_anchor_col}$14)",
    ]
    
    return any(pattern in normalized for pattern in patterns)


def _detect_comma_instead_of_colon(formula: str, expected_col: str) -> bool:
    """
    Detect if student used comma instead of colon for range.
    e.g., =AVERAGE(B14,B63) instead of =AVERAGE(B14:B63)
    """
    normalized = _normalize_formula(formula)
    
    # Pattern: COL##,COL## (comma separating two cells that should be a range)
    # Matches patterns like B14,B63 or $B$14,$B$63
    comma_pattern = rf'\$?{expected_col}\$?\d+,\$?{expected_col}\$?\d+'
    return bool(re.search(comma_pattern, normalized))


def _detect_minus_instead_of_colon(formula: str, expected_col: str) -> bool:
    """
    Detect if student used minus instead of colon for range.
    e.g., =STDEV.P(B14-B63) instead of =STDEV.P(B14:B63)
    
    This is a common typo where the student types - instead of : 
    (they're on the same key on most keyboards).
    """
    normalized = _normalize_formula(formula)
    
    # Pattern: COL##-COL## inside a function (not as a subtraction operation)
    # Look for pattern inside parentheses: FUNC(COL##-COL##)
    minus_pattern = rf'\(\$?{expected_col}\$?\d+-\$?{expected_col}\$?\d+\)'
    return bool(re.search(minus_pattern, normalized))


def _detect_correct_start_wrong_end(formula: str, expected_col: str, expected_start: int, expected_end: int) -> bool:
    """
    Detect if student used correct start row but wrong end row.
    e.g., =AVERAGE(B14:B31) instead of =AVERAGE(B14:B63)
    
    Student gets the function right and knows where the data starts,
    but selected the wrong end point (common when data range isn't obvious).
    """
    normalized = _normalize_formula(formula)
    
    # Extract range from formula: COL##:COL##
    range_pattern = rf'\$?{expected_col}\$?(\d+):\$?{expected_col}\$?(\d+)'
    match = re.search(range_pattern, normalized)
    
    if not match:
        return False
    
    actual_start = int(match.group(1))
    actual_end = int(match.group(2))
    
    # Check if start is correct (or within 1 row) but end is significantly off
    start_correct = abs(actual_start - expected_start) <= 1
    end_wrong = abs(actual_end - expected_end) > 3  # More than drag-fill tolerance
    
    return start_correct and end_wrong


def _detect_range_offset(formula: str, expected_col: str, expected_start: int, expected_end: int, tolerance: int = 3) -> bool:
    """
    Detect if student's range is slightly off (within tolerance rows).
    Common when students drag formulas without absolute references.
    
    e.g., =AVERAGE(B15:B64) instead of =AVERAGE(B14:B63) — offset by 1 row
    """
    normalized = _normalize_formula(formula)
    
    # Extract range from formula: COL##:COL##
    range_pattern = rf'\$?{expected_col}\$?(\d+):\$?{expected_col}\$?(\d+)'
    match = re.search(range_pattern, normalized)
    
    if not match:
        return False
    
    actual_start = int(match.group(1))
    actual_end = int(match.group(2))
    
    # Check if both endpoints are within tolerance (but not exact)
    start_offset = abs(actual_start - expected_start)
    end_offset = abs(actual_end - expected_end)
    
    # If exact match, not an offset error (handled by full credit)
    if start_offset == 0 and end_offset == 0:
        return False
    
    # If within tolerance on both, it's a drag-fill error
    return start_offset <= tolerance and end_offset <= tolerance


def _check_mean_formula(formula: str, col: str) -> Union[float, str]:
    """
    Check if formula uses AVERAGE function with correct range.
    Returns: score multiplier (1.0, 0.75, 0.5, 0.0) or error code string
    """
    func = _extract_function_name(formula)
    if func != "AVERAGE":
        return CREDIT_NONE
    
    normalized = _normalize_formula(formula)
    col_map = {"G": "B", "H": "C", "I": "D"}
    expected_col = col_map.get(col, "")
    
    # Check for ANCHORARRAY (Excel 365 spill reference) - valid for column I (differences)
    if col == "I" and _uses_anchorarray(formula, "D"):
        return CREDIT_FULL
    
    # Check for the exact correct range pattern
    range_patterns = [
        f"{expected_col}14:{expected_col}63",
        f"${expected_col}$14:${expected_col}$63",
        f"${expected_col}14:${expected_col}63",
        f"{expected_col}$14:{expected_col}$63",
    ]
    
    for pattern in range_patterns:
        if pattern in normalized:
            return CREDIT_FULL
    
    # Check for partial credit: comma or minus instead of colon
    if _detect_comma_instead_of_colon(formula, expected_col) or _detect_minus_instead_of_colon(formula, expected_col):
        return CREDIT_COMMA_NOT_COLON
    
    # Check for partial credit: range slightly off (drag-fill error)
    if _detect_range_offset(formula, expected_col, 14, 63):
        return CREDIT_RANGE_OFFSET
    
    # Check for partial credit: correct start, wrong end (selected wrong range)
    if _detect_correct_start_wrong_end(formula, expected_col, 14, 63):
        return CREDIT_CORRECT_START
    
    return CREDIT_NONE


def _check_median_formula(formula: str, col: str) -> float:
    """
    Check if formula uses MEDIAN function with correct range.
    Returns: score multiplier (1.0, 0.75, 0.5, 0.0)
    """
    func = _extract_function_name(formula)
    if func != "MEDIAN":
        return CREDIT_NONE
    
    normalized = _normalize_formula(formula)
    col_map = {"G": "B", "H": "C", "I": "D"}
    expected_col = col_map.get(col, "")
    
    # Check for ANCHORARRAY (Excel 365 spill reference) - valid for column I (differences)
    if col == "I" and _uses_anchorarray(formula, "D"):
        return CREDIT_FULL
    
    range_patterns = [
        f"{expected_col}14:{expected_col}63",
        f"${expected_col}$14:${expected_col}$63",
        f"${expected_col}14:${expected_col}63",
        f"{expected_col}$14:{expected_col}$63",
    ]
    
    for pattern in range_patterns:
        if pattern in normalized:
            return CREDIT_FULL
    
    # Check for partial credit: comma instead of colon
    if _detect_comma_instead_of_colon(formula, expected_col) or _detect_minus_instead_of_colon(formula, expected_col):
        return CREDIT_COMMA_NOT_COLON
    
    # Check for partial credit: range slightly off (drag-fill error)
    if _detect_range_offset(formula, expected_col, 14, 63):
        return CREDIT_RANGE_OFFSET
    
    # Check for partial credit: correct start, wrong end (selected wrong range)
    if _detect_correct_start_wrong_end(formula, expected_col, 14, 63):
        return CREDIT_CORRECT_START
    
    return CREDIT_NONE


def _check_stdev_formula(formula: str, col: str) -> float:
    """
    Check if formula uses STDEV, STDEV.P, or STDEV.S function.
    Returns: score multiplier (1.0, 0.75, 0.5, 0.0)
    """
    if not formula or not formula.startswith("="):
        return CREDIT_NONE
    
    normalized = _normalize_formula(formula)
    
    # Handle negative prefix (some students use =-STDEV.S(...))
    if normalized.startswith("=-"):
        normalized = "=" + normalized[2:]
    
    func = _extract_function_name("=" + normalized[1:])  # Re-extract after removing negative
    
    # Also check directly in normalized string
    has_stdev = any(f in normalized for f in ["STDEV(", "STDEV.P(", "STDEV.S("])
    
    if not has_stdev and func not in ["STDEV", "STDEV.P", "STDEV.S"]:
        return CREDIT_NONE
    
    col_map = {"G": "B", "H": "C", "I": "D"}
    expected_col = col_map.get(col, "")
    
    # Check for ANCHORARRAY (Excel 365 spill reference) - valid for column I (differences)
    if col == "I" and _uses_anchorarray(formula, "D"):
        return CREDIT_FULL
    
    range_patterns = [
        f"{expected_col}14:{expected_col}63",
        f"${expected_col}$14:${expected_col}$63",
        f"${expected_col}14:${expected_col}63",
        f"{expected_col}$14:{expected_col}$63",
    ]
    
    for pattern in range_patterns:
        if pattern in normalized:
            return CREDIT_FULL
    
    # Check for partial credit: comma instead of colon
    if _detect_comma_instead_of_colon(formula, expected_col) or _detect_minus_instead_of_colon(formula, expected_col):
        return CREDIT_COMMA_NOT_COLON
    
    # Check for partial credit: range slightly off (drag-fill error)
    if _detect_range_offset(formula, expected_col, 14, 63):
        return CREDIT_RANGE_OFFSET
    
    # Check for partial credit: correct start, wrong end (selected wrong range)
    if _detect_correct_start_wrong_end(formula, expected_col, 14, 63):
        return CREDIT_CORRECT_START
    
    return CREDIT_NONE


def _check_range_formula(formula: str, col: str) -> float:
    """
    Check if formula calculates MAX - MIN.
    Returns: score multiplier (1.0, 0.75, 0.5, 0.0)
    """
    if not formula or not formula.startswith("="):
        return CREDIT_NONE
    
    normalized = _normalize_formula(formula)
    col_map = {"G": "B", "H": "C", "I": "D"}
    expected_col = col_map.get(col, "")
    
    # Must contain both MAX and MIN
    if "MAX(" not in normalized or "MIN(" not in normalized:
        return CREDIT_NONE
    
    # Should have subtraction
    if "-" not in normalized:
        return CREDIT_NONE
    
    # Check for ANCHORARRAY (Excel 365 spill reference) - valid for column I (differences)
    if col == "I" and _uses_anchorarray(formula, "D"):
        return CREDIT_FULL
    
    # Must reference correct column
    if expected_col not in normalized:
        return CREDIT_NONE
    
    # Check for exact correct ranges in both MAX and MIN
    correct_range_patterns = [
        f"{expected_col}14:{expected_col}63",
        f"${expected_col}$14:${expected_col}$63",
    ]
    
    has_correct_range = any(pattern in normalized for pattern in correct_range_patterns)
    
    if has_correct_range:
        return CREDIT_FULL
    
    # Check for comma instead of colon in MAX or MIN
    if _detect_comma_instead_of_colon(formula, expected_col) or _detect_minus_instead_of_colon(formula, expected_col):
        return CREDIT_COMMA_NOT_COLON
    
    # Check for range offset (drag-fill error)
    if _detect_range_offset(formula, expected_col, 14, 63):
        return CREDIT_RANGE_OFFSET
    
    # Check for correct start, wrong end (selected wrong range)
    if _detect_correct_start_wrong_end(formula, expected_col, 14, 63):
        return CREDIT_CORRECT_START
    
    # Has correct structure (MAX-MIN with right column) but wrong range
    return CREDIT_NONE


def check_statistics(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check statistics formulas in G18:I21.
    
    Args:
        sheet: Analysis worksheet
        
    Returns:
        Tuple of (score, feedback_list)
        
    Partial Credit:
        - Full credit (100%): Correct function with correct range
        - 75% credit: Correct function, range slightly off (drag-fill error)
        - 50% credit: Correct function, used comma instead of colon
        - 0% credit: Wrong function, missing, or completely wrong
    """
    feedback = []
    total_score = 0.0
    total_cells = 12
    points_per_cell = 2.0
    full_credit_count = 0
    partial_credit_count = 0
    
    # Define the checks
    checks = [
        # (row, col, stat_type, check_func, ok_code, partial_code, wrong_code, missing_code)
        (18, "G", "Mean", _check_mean_formula, "STAT_MEAN_OK", "STAT_MEAN_PARTIAL", "STAT_MEAN_WRONG", "STAT_MEAN_MISSING"),
        (18, "H", "Mean", _check_mean_formula, "STAT_MEAN_OK", "STAT_MEAN_PARTIAL", "STAT_MEAN_WRONG", "STAT_MEAN_MISSING"),
        (18, "I", "Mean", _check_mean_formula, "STAT_MEAN_OK", "STAT_MEAN_PARTIAL", "STAT_MEAN_WRONG", "STAT_MEAN_MISSING"),
        (19, "G", "Median", _check_median_formula, "STAT_MEDIAN_OK", "STAT_MEDIAN_PARTIAL", "STAT_MEDIAN_WRONG", "STAT_MEDIAN_MISSING"),
        (19, "H", "Median", _check_median_formula, "STAT_MEDIAN_OK", "STAT_MEDIAN_PARTIAL", "STAT_MEDIAN_WRONG", "STAT_MEDIAN_MISSING"),
        (19, "I", "Median", _check_median_formula, "STAT_MEDIAN_OK", "STAT_MEDIAN_PARTIAL", "STAT_MEDIAN_WRONG", "STAT_MEDIAN_MISSING"),
        (20, "G", "StdDev", _check_stdev_formula, "STAT_STDEV_OK", "STAT_STDEV_PARTIAL", "STAT_STDEV_WRONG", "STAT_STDEV_MISSING"),
        (20, "H", "StdDev", _check_stdev_formula, "STAT_STDEV_OK", "STAT_STDEV_PARTIAL", "STAT_STDEV_WRONG", "STAT_STDEV_MISSING"),
        (20, "I", "StdDev", _check_stdev_formula, "STAT_STDEV_OK", "STAT_STDEV_PARTIAL", "STAT_STDEV_WRONG", "STAT_STDEV_MISSING"),
        (21, "G", "Range", _check_range_formula, "STAT_RANGE_OK", "STAT_RANGE_PARTIAL", "STAT_RANGE_WRONG", "STAT_RANGE_MISSING"),
        (21, "H", "Range", _check_range_formula, "STAT_RANGE_OK", "STAT_RANGE_PARTIAL", "STAT_RANGE_WRONG", "STAT_RANGE_MISSING"),
        (21, "I", "Range", _check_range_formula, "STAT_RANGE_OK", "STAT_RANGE_PARTIAL", "STAT_RANGE_WRONG", "STAT_RANGE_MISSING"),
    ]
    
    for row, col, stat_type, check_func, ok_code, partial_code, wrong_code, missing_code in checks:
        cell_ref = f"{col}{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append((missing_code, {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append((wrong_code, {"cell": cell_ref}))
        else:
            credit = check_func(formula, col)
            
            if credit == CREDIT_FULL:
                total_score += points_per_cell
                full_credit_count += 1
            elif credit == CREDIT_RANGE_OFFSET:
                # 75% credit for range slightly off (drag-fill without absolute refs)
                total_score += points_per_cell * CREDIT_RANGE_OFFSET
                partial_credit_count += 1
                feedback.append((partial_code, {
                    "cell": cell_ref, 
                    "reason": "range_offset",
                    "hint": "Range is slightly off - use absolute references ($) when copying formulas"
                }))
            elif credit == CREDIT_COMMA_NOT_COLON:
                # 50% credit for comma instead of colon
                total_score += points_per_cell * CREDIT_COMMA_NOT_COLON
                partial_credit_count += 1
                feedback.append((partial_code, {
                    "cell": cell_ref,
                    "reason": "comma_not_colon", 
                    "hint": "Used comma instead of colon - B14,B63 only uses 2 cells, B14:B63 uses the full range"
                }))
            elif credit == CREDIT_CORRECT_START:
                # 50% credit for correct function and start row, but wrong end row
                total_score += points_per_cell * CREDIT_CORRECT_START
                partial_credit_count += 1
                feedback.append((partial_code, {
                    "cell": cell_ref,
                    "reason": "wrong_end_row",
                    "hint": "Correct function and start row, but data range should end at row 63"
                }))
            else:
                feedback.append((wrong_code, {"cell": cell_ref}))
    
    # Round final score
    score = round(total_score, 2)
    
    # Summary feedback
    if full_credit_count == total_cells:
        feedback = [("STATS_ALL_CORRECT", {})]
    elif full_credit_count == 0 and partial_credit_count == 0:
        feedback.insert(0, ("STATS_NONE_CORRECT", {}))
    elif partial_credit_count > 0:
        feedback.insert(0, ("STATS_PARTIAL_CREDIT", {
            "full_credit": full_credit_count,
            "partial_credit": partial_credit_count,
            "score": score,
            "max_score": total_cells * points_per_cell
        }))
    else:
        feedback.insert(0, ("STATS_PARTIAL", {"correct": full_credit_count}))
    
    return score, feedback
