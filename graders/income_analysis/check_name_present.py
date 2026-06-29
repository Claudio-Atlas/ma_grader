"""
check_name_present.py — Validate student name presence on Income Analysis tab

Purpose: Checks if the student has entered their name in cell B1 of the
         Income Analysis worksheet. This is a simple 1-point check that
         ensures the assignment can be attributed to the correct student.

Author: Clayton Ragsdale
Dependencies: None (uses only openpyxl worksheet objects)
"""

from typing import Tuple, List, Dict, Any
from openpyxl.worksheet.worksheet import Worksheet


def check_name_present(ws_income: Worksheet) -> Tuple[int, List[Tuple[str, Dict[str, Any]]]]:
    """
    Check if a name is present in cell B1 of the Income Analysis worksheet.
    
    This check validates that the student has entered identifying information
    in the designated name cell. Any non-empty value is accepted - the grader
    doesn't validate that it matches the filename or any expected format.
    
    Grading Logic:
        - 1 point: Cell B1 contains any non-empty text
        - 0 points: Cell B1 is empty or contains only whitespace
    
    Args:
        ws_income: The openpyxl Worksheet object for the Income Analysis tab
    
    Returns:
        Tuple of:
            - score: int (0 or 1)
            - feedback: List containing a single tuple of (code, params)
                       Code is either "IA_NAME_PRESENT" or "IA_NAME_MISSING"
    
    Example:
        >>> score, feedback = check_name_present(worksheet)
        >>> if score == 1:
        ...     print("Name found!")
        >>> else:
        ...     print(feedback[0])  # ("IA_NAME_MISSING", {"cell": "B1"})
    """
    # Get the value from cell B1
    name_cell = ws_income["B1"]
    
    # Extract and clean the value (handle None, numbers, etc.)
    name = str(name_cell.value).strip() if name_cell.value else ""

    # Check if any non-whitespace content exists
    if name:
        # Student has entered a name
        return 1, [("IA_NAME_PRESENT", {"cell": "B1"})]
    else:
        # Cell is empty or whitespace-only
        return 0, [("IA_NAME_MISSING", {"cell": "B1"})]
