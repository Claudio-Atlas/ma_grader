"""
check_formatting.py — Validates cell formatting in Analysis tab

Grading: 6 points for proper number formatting

Cells that should be formatted as Number with 2 decimal places:
- Statistics cells (G18:I21)
- Percentile cells (G27:G28)
- Empirical rule cells (G36:G37)
"""

from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _is_number_format_2dp(format_code: str) -> bool:
    """
    Check if the number format displays 2 decimal places.
    
    Common valid formats:
        0.00
        #,##0.00
        #,##0.00;[Red]-#,##0.00
        General (if value is already rounded - partial credit)
    """
    if not format_code:
        return False
    
    format_upper = format_code.upper()
    
    # Check for 2 decimal place patterns
    if ".00" in format_code:
        return True
    
    # Check for number format codes
    if "0.00" in format_code:
        return True
    
    return False


def check_analysis_formatting(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check formatting of numeric cells in Analysis tab.
    
    Args:
        sheet: Analysis worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    
    # Cells to check for formatting
    cells_to_check = [
        # Statistics (G18:I21)
        "G18", "H18", "I18",  # Mean
        "G19", "H19", "I19",  # Median
        "G20", "H20", "I20",  # StdDev
        "G21", "H21", "I21",  # Range
        # Percentiles
        "G27", "G28",
        # Empirical Rule
        "G36", "G37",
    ]
    
    correct_count = 0
    total_cells = len(cells_to_check)
    
    for cell_ref in cells_to_check:
        cell = sheet[cell_ref]
        format_code = cell.number_format
        
        if _is_number_format_2dp(format_code):
            correct_count += 1
        else:
            feedback.append(("FORMAT_CELL_WRONG", {"cell": cell_ref}))
    
    # Calculate score (6 points total)
    # Give proportional credit
    score = round((correct_count / total_cells) * 6.0, 2)
    
    # Summary feedback
    if correct_count == total_cells:
        feedback = [("FORMAT_ALL_CORRECT", {})]
    elif correct_count == 0:
        feedback.insert(0, ("FORMAT_PARTIAL", {"correct": 0, "total": total_cells}))
    else:
        feedback.insert(0, ("FORMAT_PARTIAL", {"correct": correct_count, "total": total_cells}))
    
    return score, feedback
