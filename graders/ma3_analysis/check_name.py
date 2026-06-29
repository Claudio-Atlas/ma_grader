"""
check_name.py — Validates student name entry in B10

Grading: 1 point for entering full name
"""

from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def check_name(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check if student entered their name in cell B10.
    
    Args:
        sheet: Analysis worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    
    cell_value = sheet["B10"].value
    
    if cell_value is None or str(cell_value).strip() == "":
        feedback.append(("NAME_MISSING", {}))
        return 0.0, feedback
    
    name = str(cell_value).strip()
    
    # Check if it's still the placeholder
    if name.lower() in ["your name here", "enter name", "name"]:
        feedback.append(("NAME_MISSING", {}))
        return 0.0, feedback
    
    # Check if name seems too short (less than 3 characters)
    if len(name) < 3:
        feedback.append(("NAME_TOO_SHORT", {"name": name}))
        return 0.5, feedback
    
    # Name is present
    feedback.append(("NAME_PRESENT", {"name": name}))
    return 1.0, feedback
