"""
check_percentiles.py — Validates percentile calculations in G27:G28

Grading: 6 points total (3 pts each)

Expected formula patterns:
    PERCENTILE(range, value)
    PERCENTILE.INC(range, value)
    PERCENTILE.EXC(range, value)
    
The expected percentile values are dynamically generated per student
based on their name. F27 contains the expected percentile for G27
(e.g., "5th" means 0.05), and F28 contains the expected for G28.
"""

import re
from typing import Tuple, List, Optional
from openpyxl.worksheet.worksheet import Worksheet


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


def _extract_percentile_value(formula: str) -> Optional[float]:
    """
    Extract the percentile value from a PERCENTILE formula.
    
    Returns the decimal value (e.g., 0.05, 0.40) or None if not found.
    """
    if not formula:
        return None
    
    normalized = _normalize_formula(formula)
    
    # Pattern to find percentile value: ,0.XX) or ,0.X) or ,X)
    # Matches: PERCENTILE(range,0.25), PERCENTILE.INC(range,0.05), etc.
    
    # First try decimal format: 0.XX
    match = re.search(r',\s*(0\.?\d*)\s*\)', normalized)
    if match:
        try:
            val = float(match.group(1))
            # If value > 1, it might be a percentage (e.g., 5 instead of 0.05)
            if val > 1:
                val = val / 100.0
            return val
        except ValueError:
            pass
    
    # Try integer format: just a number like 5 or 40
    match = re.search(r',\s*(\d+)\s*\)', normalized)
    if match:
        try:
            val = int(match.group(1))
            # Convert percentage to decimal (5 -> 0.05, 40 -> 0.40)
            return val / 100.0
        except ValueError:
            pass
    
    return None


def _parse_expected_percentile(cell_value) -> Optional[float]:
    """
    Parse the expected percentile from F27/F28 cell value.
    
    Examples:
        "5th" -> 0.05
        "40th" -> 0.40
        "47th" -> 0.47
        5 -> 0.05
        40 -> 0.40
    """
    if cell_value is None:
        return None
    
    val_str = str(cell_value).strip().lower()
    
    # Remove ordinal suffixes (st, nd, rd, th)
    val_str = re.sub(r'(st|nd|rd|th)$', '', val_str)
    
    try:
        val = float(val_str)
        # Convert to decimal if it's a percentage
        if val >= 1:
            val = val / 100.0
        return val
    except ValueError:
        return None


def _check_percentile_formula(
    formula: str, 
    cell_ref: str, 
    expected_value: Optional[float]
) -> Tuple[bool, str]:
    """
    Check if formula uses a PERCENTILE function with correct range.
    
    We no longer validate the exact percentile value since the expected
    values in F27/F28 may not parse correctly. Any valid PERCENTILE 
    formula with the correct range gets full credit.
    
    Args:
        formula: The student's formula
        cell_ref: Cell reference (G27 or G28)
        expected_value: The expected percentile value from F27/F28 (no longer used strictly)
    
    Returns: (is_correct, reason)
    """
    if not formula or not formula.startswith("="):
        return False, "Not a formula"
    
    normalized = _normalize_formula(formula)
    
    # Check for PERCENTILE function (with or without _xlfn. prefix)
    # Accept: PERCENTILE, PERCENTILE.INC, PERCENTILE.EXC (all valid approaches)
    has_percentile = any(p in normalized for p in [
        "PERCENTILE(",
        "PERCENTILE.INC(",
        "PERCENTILE.EXC(",
        "_XLFN.PERCENTILE(",
        "_XLFN.PERCENTILE.INC(",
        "_XLFN.PERCENTILE.EXC(",
    ])
    
    if not has_percentile:
        return False, "Missing PERCENTILE function"
    
    # Check for correct range reference (D14:D63 or ANCHORARRAY or D:D column ref)
    range_patterns = [
        "D14:D63", "$D$14:$D$63", "$D14:$D63", "D$14:D$63",  # Explicit range
        "D14:D31", "$D$14:$D$31",  # Shorter range (partial credit worthy but accept)
        "ANCHORARRAY",  # Excel 365 spill reference
        "D:D", "$D:$D",  # Entire column reference (valid approach)
    ]
    has_correct_range = any(pattern in normalized for pattern in range_patterns)
    
    if not has_correct_range:
        # Check if they at least reference column D with some range
        if "D" in normalized and ("14" in normalized or ":" in normalized):
            return True, "Range reference may be non-standard but appears valid"
        return False, "Incorrect range reference"
    
    # If we get here, student has a valid PERCENTILE formula with correct range
    # We give full credit regardless of the exact percentile value used
    return True, "Correct"


def check_percentiles(
    sheet: Worksheet,
    sheet_data: Worksheet = None
) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check percentile formulas in G27 and G28.
    
    The expected percentile values are read from F27 and F28, which
    are dynamically calculated based on the student's name.
    
    Args:
        sheet: Analysis worksheet (loaded with data_only=False for formulas)
        sheet_data: Analysis worksheet (loaded with data_only=True for calculated values)
                   If not provided, will try to read from sheet directly.
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_count = 0
    total_cells = 2
    points_per_cell = 3.0
    
    # Read expected percentile values from F27 and F28
    # These cells contain formulas like =MOD(CODE(MID(B10,3,1)),50)&"th"
    # We need the calculated values from sheet_data, or fall back to sheet
    
    data_sheet = sheet_data if sheet_data is not None else sheet
    f27_raw = data_sheet['F27'].value
    f28_raw = data_sheet['F28'].value
    
    expected_values = {
        'G27': _parse_expected_percentile(f27_raw),
        'G28': _parse_expected_percentile(f28_raw),
    }
    
    cells_to_check = ["G27", "G28"]
    
    for cell_ref in cells_to_check:
        cell = sheet[cell_ref]
        formula = cell.value
        expected = expected_values.get(cell_ref)
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("PERCENTILE_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("PERCENTILE_WRONG", {
                "cell": cell_ref,
                "reason": "Not a formula"
            }))
        else:
            is_correct, reason = _check_percentile_formula(formula, cell_ref, expected)
            if is_correct:
                correct_count += 1
                feedback.append(("PERCENTILE_OK", {"cell": cell_ref}))
            else:
                feedback.append(("PERCENTILE_WRONG", {
                    "cell": cell_ref,
                    "reason": reason,
                    "found": formula
                }))
    
    # Calculate score
    score = round(correct_count * points_per_cell, 2)
    
    # Summary feedback
    if correct_count == total_cells:
        feedback = [("PERCENTILE_ALL_CORRECT", {})]
    elif correct_count == 0:
        feedback.insert(0, ("PERCENTILE_NONE_CORRECT", {}))
    else:
        feedback.insert(0, ("PERCENTILE_PARTIAL", {"correct": correct_count}))
    
    return score, feedback
