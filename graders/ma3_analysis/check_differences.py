"""
check_differences.py — Validates difference calculations in D14:D63

Grading: 6 points total (0.12 pts each for 50 cells)
Expected formula pattern: =C{row}-B{row}
"""

import re
from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison (remove spaces, uppercase)."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


def _is_valid_difference_formula(formula: str, row: int) -> bool:
    """
    Check if formula correctly calculates After - Before for this row.
    
    Valid patterns:
        =C14-B14
        =C14 - B14
        =$C$14-$B$14
        =SUM(C14-B14)  (equivalent result)
        =(C14-B14)
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)
    
    # Pattern: =C{row}-B{row} with optional $ signs
    patterns = [
        f"=C{row}-B{row}",
        f"=$C${row}-$B${row}",
        f"=$C{row}-$B{row}",
        f"=C${row}-B${row}",
        f"=$C${row}-B{row}",
        f"=C{row}-$B${row}",
        # Wrapped in parentheses
        f"=(C{row}-B{row})",
        f"=($C${row}-$B${row})",
        # Wrapped in SUM (same result)
        f"=SUM(C{row}-B{row})",
        f"=SUM($C${row}-$B${row})",
    ]
    
    normalized_patterns = [_normalize_formula(p) for p in patterns]
    
    return normalized in normalized_patterns


def _is_valid_array_formula(formula_obj, start_row: int, end_row: int) -> bool:
    """
    Check if an ArrayFormula correctly calculates differences for the range.
    
    Excel 365 allows spill formulas like =C14:C63-B14:B63 in D14 that
    automatically fills D14:D63.
    """
    from openpyxl.worksheet.formula import ArrayFormula
    
    if not isinstance(formula_obj, ArrayFormula):
        return False
    
    # Get the formula text
    formula_text = getattr(formula_obj, 'text', '')
    if not formula_text:
        return False
    
    normalized = _normalize_formula(formula_text)
    
    # Valid array formula patterns for difference calculation
    # =C14:C63-B14:B63 or with $ signs
    patterns = [
        f"=C{start_row}:C{end_row}-B{start_row}:B{end_row}",
        f"=$C${start_row}:$C${end_row}-$B${start_row}:$B${end_row}",
        f"=$C{start_row}:$C{end_row}-$B{start_row}:$B{end_row}",
    ]
    
    normalized_patterns = [_normalize_formula(p) for p in patterns]
    
    return normalized in normalized_patterns


def check_differences(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check difference formulas in D14:D63.
    
    Handles both:
    - Individual formulas in each cell (=C14-B14, =C15-B15, etc.)
    - Excel 365 spill/array formulas (=C14:C63-B14:B63 in D14 only)
    
    Args:
        sheet: Analysis worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    from openpyxl.worksheet.formula import ArrayFormula
    
    feedback = []
    correct_count = 0
    total_cells = 50
    points_per_cell = 6.0 / total_cells  # 0.12 per cell
    
    # First, check if D14 contains a valid array formula (Excel 365 spill)
    d14_cell = sheet["D14"]
    d14_value = d14_cell.value
    
    # Check for ArrayFormula - get text attribute directly if it exists
    # This approach works regardless of type checking issues in PyInstaller
    formula_text = getattr(d14_value, 'text', None)
    
    # If we have a text attribute that looks like a formula, it's an array formula
    is_array_formula = (
        formula_text is not None and 
        isinstance(formula_text, str) and 
        formula_text.startswith('=')
    )
    
    if is_array_formula:
        # Use text-based validation for PyInstaller compatibility
        if formula_text:
            normalized = _normalize_formula(formula_text)
            valid_patterns = [
                _normalize_formula("=C14:C63-B14:B63"),
                _normalize_formula("=$C$14:$C$63-$B$14:$B$63"),
            ]
            if normalized in valid_patterns:
                # Full credit - array formula covers entire range
                return 6.0, [("DIFF_ALL_CORRECT_ARRAY", {
                    "formula": formula_text
                })]
            else:
                # Array formula exists but wrong formula
                feedback.append(("DIFF_ARRAY_WRONG", {
                    "cell": "D14",
                    "found": formula_text
                }))
                return 0.0, feedback
    
    # Standard check: individual formulas in each cell
    for row in range(14, 64):  # Rows 14-63
        cell = sheet[f"D{row}"]
        cell_ref = f"D{row}"
        
        # Get the formula (not the calculated value)
        formula = cell.value
        
        # Check if it's a formula
        # Use duck typing for ArrayFormula detection (PyInstaller compatibility)
        is_cell_array_formula = (
            isinstance(formula, ArrayFormula) or 
            type(formula).__name__ == 'ArrayFormula' or
            (hasattr(formula, 'text') and hasattr(formula, 'ref'))
        )
        
        if formula is None:
            feedback.append(("DIFF_FORMULA_MISSING", {"cell": cell_ref, "row": row}))
        elif is_cell_array_formula:
            # ArrayFormula in a cell other than D14 - likely a spill cell
            feedback.append(("DIFF_NOT_FORMULA", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("DIFF_NOT_FORMULA", {"cell": cell_ref}))
        elif _is_valid_difference_formula(formula, row):
            correct_count += 1
            # Only add individual OK feedback if there are errors (to avoid 50 OK messages)
        else:
            feedback.append(("DIFF_FORMULA_WRONG", {
                "cell": cell_ref, 
                "row": row,
                "found": formula
            }))
    
    # Calculate score
    score = round(correct_count * points_per_cell, 2)
    
    # Summary feedback
    if correct_count == total_cells:
        feedback = [("DIFF_ALL_CORRECT", {})]
    elif correct_count == 0:
        feedback.insert(0, ("DIFF_NONE_CORRECT", {}))
    else:
        feedback.insert(0, ("DIFF_PARTIAL", {"correct": correct_count}))
    
    return score, feedback
