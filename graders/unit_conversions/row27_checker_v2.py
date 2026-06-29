"""
row27_checker_v2.py — Grade Row 27 of Unit Conversions (gal/l and h/d)

Purpose: Validates the conversion ratio formulas, unit labels, and final calculation
         for Row 27, which converts liters/hour to gallons/day using two intermediate
         ratios: gal/l (gallons per liter) and h/d (hours per day).

Author: Clayton Ragsdale
Dependencies: graders.unit_conversions.utils

Row 27 Layout:
    C27: Starting value (given)
    F27: First conversion ratio formula (gal/l OR h/d)
    G27: First ratio unit label
    I27: Second conversion ratio formula (the other ratio)
    J27: Second ratio unit label
    O27: Final formula (=C27*F27*I27)
    P27: Final unit label (gal/d)

Grading Criteria:
    - Formulas (4 pts): 2 pts each for F27 and I27
    - Unit labels (2 pts): 1 pt each for G27 and J27
    - Final formula (2 pts): O27 must multiply C27*F27*I27
    - Final unit (1 pt): P27 must be "gal/d"
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from graders.unit_conversions.utils import norm_formula, norm_unit


def grade_row_27_v2(sheet: Worksheet) -> Dict[str, Any]:
    """
    V2 JSON-driven strict grader for Row 27 (gal/l and h/d conversions).
    
    Grading Rules:
        - Each cell pair (F27/G27, I27/J27) must contain exactly one of the
          required conversion ratios
        - Time unit normalization: hr→h, day→d
        - Final formula must multiply the starting value by both ratios
    
    Valid Formulas:
        gal/l ratio: =L16/I16, =L16, =L16/1 (references lookup table row 16)
        h/d ratio:   =L22/I22, =L22, =L22/1 (references lookup table row 22)
    
    Args:
        sheet: The openpyxl Worksheet object for the Unit Conversions tab
    
    Returns:
        Dict containing scores and feedback for each grading category
    """

    # ============================================================
    # Initialize scoring buckets
    # ============================================================
    formulas_score = 0        # Max 4 points (2 + 2)
    unit_text_score = 0       # Max 2 points
    final_formula_score = 0   # Max 2 points
    final_unit_score = 0      # Max 1 point

    # ============================================================
    # Initialize feedback buckets
    # ============================================================
    formulas_feedback: List[Tuple[str, Dict[str, Any]]] = []
    unit_text_feedback: List[Tuple[str, Dict[str, Any]]] = []
    final_formula_feedback: List[Tuple[str, Dict[str, Any]]] = []
    final_unit_feedback: List[Tuple[str, Dict[str, Any]]] = []

    # ============================================================
    # Define valid formulas for Row 27
    # ============================================================
    # L16 = 0.264... (gallons per liter)
    # L22 = 24 (hours per day)
    ratio_options = {
        "gal/l": {"=L16/I16", "=L16", "=L16/1"},
        "h/d":   {"=L22/I22", "=L22", "=L22/1"}
    }

    valid_units = {"gal/l", "h/d"}

    # ============================================================
    # Normalize cell values
    # ============================================================
    F = norm_formula(sheet["F27"].value)
    I = norm_formula(sheet["I27"].value)
    O = norm_formula(sheet["O27"].value)

    # Helper function to normalize time units in labels
    def normalize_time(u: str) -> str:
        """Normalize time abbreviations: hr→h, day→d"""
        u = u.replace("hr", "h")
        u = u.replace("day", "d")
        return u

    G = normalize_time(norm_unit(sheet["G27"].value))
    J = normalize_time(norm_unit(sheet["J27"].value))
    P = normalize_time(norm_unit(sheet["P27"].value))

    # ============================================================
    # Check Formula + Unit pairs for F27/G27 and I27/J27
    # ============================================================
    pairs = [
        ("F27", F, "G27", G),
        ("I27", I, "J27", J)
    ]

    for formula_cell, formula_val, unit_cell, unit_val in pairs:

        # ----- UNIT CHECK -----
        if unit_val in valid_units:
            unit_text_score += 1
            unit_text_feedback.append((
                "UC27_UNIT_CORRECT",
                {"cell": unit_cell, "unit": unit_val}
            ))
        else:
            unit_text_feedback.append((
                "UC27_UNIT_INCORRECT",
                {"cell": unit_cell, "expected": list(valid_units)}
            ))

        # ----- FORMULA CHECK -----
        # Check if formula matches any valid ratio pattern
        matched = False
        for ratio, valid_forms in ratio_options.items():
            if formula_val in valid_forms:
                formulas_score += 2
                matched = True
                formulas_feedback.append((
                    "UC27_FORMULA_CORRECT",
                    {"cell": formula_cell, "ratio": ratio}
                ))
                break

        if not matched:
            formulas_feedback.append((
                "UC27_FORMULA_INCORRECT",
                {"cell": formula_cell}
            ))

    # ============================================================
    # Final formula check - O27
    # ============================================================
    # Must reference C27, F27, I27 with multiplication
    required_refs = ["C27", "F27", "I27"]
    ratio_refs = ["F27", "I27"]  # Just the ratio columns

    if all(ref in O for ref in required_refs) and "*" in O:
        # Full credit: references starting value AND all ratios
        final_formula_score = 2
        final_formula_feedback.append((
            "UC27_FINAL_FORMULA_CORRECT",
            {"cell": "O27"}
        ))
    elif all(ref in O for ref in ratio_refs) and "*" in O and "C27" not in O:
        # Partial credit: references ratios but hardcoded starting value
        final_formula_score = 1.5
        final_formula_feedback.append((
            "UC27_FINAL_FORMULA_PARTIAL",
            {"cell": "O27", "note": "Formula references ratios correctly but uses hardcoded starting value. Use C27 for full credit."}
        ))
    else:
        final_formula_feedback.append((
            "UC27_FINAL_FORMULA_INCORRECT",
            {"cell": "O27", "required": required_refs}
        ))

    # ============================================================
    # Final unit check - P27
    # ============================================================
    # After converting l/h through gal/l and h/d, result is gal/d
    if P == "gal/d":  # strict match after normalization
        final_unit_score = 1
        final_unit_feedback.append((
            "UC27_FINAL_UNIT_CORRECT",
            {"cell": "P27", "unit": P}
        ))
    else:
        final_unit_feedback.append((
            "UC27_FINAL_UNIT_INCORRECT",
            {"cell": "P27", "expected": "gal/d"}
        ))

    # ============================================================
    # Return V2 structure
    # ============================================================
    return {
        "formulas_score": formulas_score,
        "unit_text_score": unit_text_score,
        "final_formula_score": final_formula_score,
        "final_unit_score": final_unit_score,

        "formulas_feedback": formulas_feedback,
        "unit_text_feedback": unit_text_feedback,
        "final_formula_feedback": final_formula_feedback,
        "final_unit_feedback": final_unit_feedback
    }
