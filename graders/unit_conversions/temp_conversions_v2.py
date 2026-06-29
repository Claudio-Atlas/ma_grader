"""
temp_conversions_v2.py — Grade temperature conversion formulas (C40 and A41)

Purpose: Validates the Fahrenheit-to-Celsius (C40) and Celsius-to-Fahrenheit (A41)
         conversion formulas on the Unit Conversions tab. These formulas should
         reference the input cells and use the correct conversion factors.

Author: Clayton Ragsdale
Dependencies: graders.unit_conversions.utils

Temperature Conversion Formulas:
    C40 (Fahrenheit to Celsius): = (5/9) * (A40 - 32)
    A41 (Celsius to Fahrenheit): = (9/5) * C41 + 32

Grading Criteria:
    - Full credit (2 pts): Formula has correct cell references and conversion factor
    - Partial credit (1 pt): Formula produces correct value but missing cell references
    - No credit (0 pts): No formula or wrong result
"""

from typing import Dict, Any, List, Tuple, Optional
from openpyxl.worksheet.worksheet import Worksheet

from graders.unit_conversions.utils import norm_formula


def _get_cell_value(sheet: Worksheet, cell_ref: str) -> Optional[float]:
    """
    Get the numeric value of a cell (handles both values and cached formula results).
    
    Note: When opening workbooks with data_only=False, formula cells show the
    formula text, not the calculated value. This function returns None for
    formula cells since we can't evaluate them without Excel.
    
    Args:
        sheet: The openpyxl Worksheet object
        cell_ref: Cell reference (e.g., "A40", "C40")
    
    Returns:
        float: The numeric value if the cell contains a number
        None: If the cell is empty, contains a formula, or isn't numeric
    """
    try:
        cell = sheet[cell_ref]
        value = cell.value
        
        # If it's a formula string, we can't get the calculated value
        if isinstance(value, str) and value.startswith("="):
            return None
            
        if value is None:
            return None
            
        return float(value)
    except (TypeError, ValueError):
        return None


def _check_c40_calculated_value(sheet: Worksheet) -> bool:
    """
    Check if C40 has the correct calculated value for Fahrenheit to Celsius.
    
    Formula: (5/9) * (A40 - 32)
    
    This is used for partial credit when the student has a formula that
    produces the correct result but doesn't properly reference cell A40.
    
    Args:
        sheet: The openpyxl Worksheet object
    
    Returns:
        bool: True if C40's value matches the expected calculation
    """
    try:
        a40_val = _get_cell_value(sheet, "A40")
        c40_val = _get_cell_value(sheet, "C40")
        
        if a40_val is None or c40_val is None:
            return False
            
        # Calculate expected Celsius value
        expected = (5/9) * (a40_val - 32)
        # Allow small floating-point tolerance
        return abs(expected - c40_val) < 0.01
    except (TypeError, ValueError):
        return False


def _check_a41_calculated_value(sheet: Worksheet) -> bool:
    """
    Check if A41 has the correct calculated value for Celsius to Fahrenheit.
    
    Formula: (9/5) * C41 + 32
    
    This is used for partial credit when the student has a formula that
    produces the correct result but doesn't properly reference cell C41.
    
    Args:
        sheet: The openpyxl Worksheet object
    
    Returns:
        bool: True if A41's value matches the expected calculation
    """
    try:
        c41_val = _get_cell_value(sheet, "C41")
        a41_val = _get_cell_value(sheet, "A41")
        
        if c41_val is None or a41_val is None:
            return False
            
        # Calculate expected Fahrenheit value
        expected = (9/5) * c41_val + 32
        # Allow small floating-point tolerance
        return abs(expected - a41_val) < 0.01
    except (TypeError, ValueError):
        return False


def grade_temp_conversions_v2(sheet: Worksheet) -> Dict[str, Any]:
    """
    V2 JSON-driven strict grader for temperature conversions.
    
    Checks two temperature conversion formulas:
        - C40: Fahrenheit to Celsius = (5/9) * (A40 - 32)
        - A41: Celsius to Fahrenheit = (9/5) * C41 + 32
    
    Grading Logic:
        For each formula (C40 and A41):
        - 2 points: Has formula with correct conversion factor AND cell references
        - 1 point: Has formula with correct calculated value but missing cell refs
        - 0 points: No formula, wrong formula, or incorrect value
    
    Required Formula Components:
        C40: Must contain "A40-32" AND "5/9" AND multiplication (*)
        A41: Must contain "C41" AND "9/5" AND "+32" AND multiplication (*)
    
    Args:
        sheet: The openpyxl Worksheet object for the Unit Conversions tab
    
    Returns:
        Dict containing:
            - temp_and_celsius_score: int (0-4)
            - temp_and_celsius_feedback: List of (code, params) tuples
    """

    # ============================================================
    # Initialize scoring
    # ============================================================
    score = 0  # Max 4 points (2 per formula)
    feedback: List[Tuple[str, Dict[str, Any]]] = []

    # ============================================================
    # Extract and normalize values
    # ============================================================
    # Important: Check for formula (starts with "=") on RAW value BEFORE
    # normalizing, since normalization may strip or modify the "=" sign
    c40_raw = sheet["C40"].value
    a41_raw = sheet["A41"].value
    
    # Determine if cells contain formulas
    c40_is_formula = isinstance(c40_raw, str) and c40_raw.strip().startswith("=")
    a41_is_formula = isinstance(a41_raw, str) and a41_raw.strip().startswith("=")
    
    # Now normalize for pattern matching
    c40 = norm_formula(c40_raw)
    a41 = norm_formula(a41_raw)

    # ============================================================
    # Define required formula components
    # ============================================================
    
    # C40: Fahrenheit to Celsius
    # Formula pattern: (5/9)*(A40-32)
    # Required fragments (after normalization to uppercase)
    required_c40 = {
        "A40-32",   # Must reference A40 and subtract 32
        "5/9"       # Must have 5/9 conversion factor
    }

    # A41: Celsius to Fahrenheit
    # Formula pattern: (9/5)*C41+32
    required_a41 = {
        "C41",      # Must reference C41
        "9/5",      # Must have 9/5 conversion factor
        "+32"       # Must add 32
    }

    # ============================================================
    # Grade C40 formula (Fahrenheit to Celsius)
    # ============================================================
    
    # Check if it's a formula with multiplication
    c40_has_formula = c40_is_formula and isinstance(c40, str) and "*" in c40
    # Check if formula has all required components
    c40_has_refs = c40_has_formula and all(fragment in c40 for fragment in required_c40)

    # Check if formula has correct structure but hardcoded values (no A40 reference)
    c40_has_structure = (c40_has_formula and 
                         "5/9" in c40 and 
                         "-32" in c40 and
                         "A40" not in c40)
    
    if c40_has_refs:
        # Full credit: formula with correct cell references and conversion factor
        score += 2
        feedback.append(("UC_TEMP_C40_CORRECT", {"cell": "C40"}))
    elif c40_has_structure or (c40_has_formula and _check_c40_calculated_value(sheet)):
        # Partial credit: formula has correct math structure but hardcoded values
        score += 1
        feedback.append(("UC_TEMP_C40_PARTIAL", {
            "cell": "C40",
            "note": "Formula has correct conversion math but uses hardcoded values. "
                    "Use cell reference (A40) for full credit."
        }))
    else:
        # No credit
        feedback.append(("UC_TEMP_C40_INCORRECT", {
            "cell": "C40",
            "required": list(required_c40)
        }))

    # ============================================================
    # Grade A41 formula (Celsius to Fahrenheit)
    # ============================================================
    
    # Check if it's a formula with multiplication
    a41_has_formula = a41_is_formula and isinstance(a41, str) and "*" in a41
    # Check if formula has all required components
    # STRICT: +32 must be added at end, not multiplied inside parens
    a41_plus32_correct = "+32" in a41 and "+32)" not in a41
    a41_has_refs = a41_has_formula and "C41" in a41 and "9/5" in a41 and a41_plus32_correct

    # Check if formula has correct structure but hardcoded values (no C41 reference)
    # STRICT: +32 must be ADDED at the end, not multiplied inside parentheses
    # Good: =(9/5)*15+32  Bad: =(9/5)*(15+32)
    # Check that "+32" is not followed by ")" which would indicate it's inside parens
    a41_plus32_at_end = "+32" in a41 and "+32)" not in a41
    a41_has_structure = (a41_has_formula and 
                         "9/5" in a41 and 
                         a41_plus32_at_end and
                         "C41" not in a41)
    
    if a41_has_refs:
        # Full credit: formula with correct cell references and conversion factor
        score += 2
        feedback.append(("UC_TEMP_A41_CORRECT", {"cell": "A41"}))
    elif a41_has_structure or (a41_has_formula and _check_a41_calculated_value(sheet)):
        # Partial credit: formula has correct math structure but hardcoded values
        score += 1
        feedback.append(("UC_TEMP_A41_PARTIAL", {
            "cell": "A41", 
            "note": "Formula has correct conversion math but uses hardcoded values. "
                    "Use cell reference (C41) for full credit."
        }))
    else:
        # No credit
        feedback.append(("UC_TEMP_A41_INCORRECT", {
            "cell": "A41",
            "required": list(required_a41)
        }))

    # ============================================================
    # Return V2 structured output
    # ============================================================
    return {
        "temp_and_celsius_score": min(score, 4),  # Cap at 4 points
        "temp_and_celsius_feedback": feedback
    }
