"""
check_formatting.py — Validates cell formatting in Visualization tab

Grading: 4 points for proper formatting

Cells to check:
- Bin table (E22:E24): Number with 2 decimal places
- Lower/Upper limits (D28:E38): Number with 2 decimal places
- Title of Bin (F28:F38): Number with 2 decimal places
- Frequency (G28:G38): Number with 0 decimal places
- Relative Frequency (H28:H38): Percentage with 0 decimal places
"""

from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _is_number_format_2dp(format_code: str) -> bool:
    """Check if format shows 2 decimal places."""
    if not format_code:
        return False
    return ".00" in format_code or "0.00" in format_code


def _is_number_format_0dp(format_code: str) -> bool:
    """Check if format shows 0 decimal places (integer)."""
    if not format_code:
        return False
    # "0" or "General" with no decimals
    if format_code in ["0", "#,##0", "General"]:
        return True
    # Number without decimal portion
    if "0" in format_code and "." not in format_code:
        return True
    return False


def _is_percentage_format(format_code: str) -> bool:
    """Check if format is percentage."""
    if not format_code:
        return False
    return "%" in format_code


def check_visualization_formatting(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check formatting of cells in Visualization tab.
    
    Args:
        sheet: Visualization worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_count = 0
    total_checks = 0
    
    # Bin table cells (E22:E24) - should be 2 decimal places
    for cell_ref in ["E22", "E23", "E24"]:
        total_checks += 1
        cell = sheet[cell_ref]
        if _is_number_format_2dp(cell.number_format):
            correct_count += 1
        else:
            feedback.append(("VIS_FORMAT_CELL_WRONG", {"cell": cell_ref}))
    
    # Lower/Upper limits and Title of Bin - 2 decimal places
    for row in range(28, 39):
        for col in ["D", "E", "F"]:
            total_checks += 1
            cell_ref = f"{col}{row}"
            cell = sheet[cell_ref]
            if _is_number_format_2dp(cell.number_format):
                correct_count += 1
            # Don't add individual feedback for each cell (too verbose)
    
    # Frequency - 0 decimal places
    for row in range(28, 39):
        total_checks += 1
        cell_ref = f"G{row}"
        cell = sheet[cell_ref]
        if _is_number_format_0dp(cell.number_format):
            correct_count += 1
    
    # Relative Frequency - percentage
    for row in range(28, 39):
        total_checks += 1
        cell_ref = f"H{row}"
        cell = sheet[cell_ref]
        if _is_percentage_format(cell.number_format):
            correct_count += 1
    
    # Calculate score (4 points total)
    score = round((correct_count / total_checks) * 4.0, 2)
    
    # Summary feedback
    if correct_count == total_checks:
        feedback = [("VIS_FORMAT_ALL_CORRECT", {})]
    else:
        feedback.insert(0, ("VIS_FORMAT_PARTIAL", {"correct": correct_count, "total": total_checks}))
    
    return score, feedback
