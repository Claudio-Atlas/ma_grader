"""
row28_checker_v2.py — Grade Row 28 of Unit Conversions (kg/lb and in/cm)

Purpose: Validates the conversion ratio formulas, unit labels, and final calculation
         for Row 28, which uses THREE conversion ratios: kg/lb (twice, for lb in
         numerator and denominator) and in/cm (for inch conversion).

Author: Clayton Ragsdale
Dependencies: graders.unit_conversions.utils

Row 28 Layout:
    C28: Starting value (given, in lb/in²)
    F28: First conversion ratio formula
    G28: First ratio unit label
    I28: Second conversion ratio formula
    J28: Second ratio unit label
    L28: Third conversion ratio formula
    M28: Third ratio unit label
    O28: Final formula (=C28*F28*I28*L28)
    P28: Final unit label (kg/cm²)

Grading Criteria:
    - Formulas (6 pts): 2 pts each for F28, I28, L28
    - Unit labels (3 pts): 1 pt each for G28, J28, M28
    - Final formula (2 pts): O28 must multiply C28*F28*I28*L28
    - Final unit (1 pt): P28 must be "kg/cm^2"
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from graders.unit_conversions.utils import norm_formula, norm_unit


def grade_row_28_v2(sheet: Worksheet) -> Dict[str, Any]:
    """
    V2 JSON-driven strict grader for Row 28 (kg/lb and in/cm conversions).
    
    Row 28 uses three conversion ratios to convert lb/in² to kg/cm²:
        - kg/lb: Converts pounds to kilograms
        - in/cm: Converts inches to centimeters (used twice for in²)
    
    Note: The kg/lb ratio is used once, and in/cm is used twice (for
    squared units), but the grader accepts any valid combination that
    could produce the correct result.
    
    Valid Formulas:
        kg/lb ratio: =I9/L9, =1/L9 (references lookup table row 9)
        in/cm ratio: =I20/L20, =1/L20 (references lookup table row 20)
    
    Args:
        sheet: The openpyxl Worksheet object for the Unit Conversions tab
    
    Returns:
        Dict containing scores and feedback for each grading category
    """

    # ============================================================
    # Initialize scoring buckets
    # ============================================================
    formulas_score = 0        # Max 6 points (2 * 3 ratios)
    unit_text_score = 0       # Max 3 points (1 * 3 labels)
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
    # Define valid formulas for Row 28
    # ============================================================
    # Row 9: kg/lb conversion (L9 = 2.205)
    # Row 20: in/cm conversion (L20 = 2.54)
    ratio_options = {
        "kg/lb": {"=I9/L9", "=1/L9"},
        "in/cm": {"=I20/L20", "=1/L20"}
    }

    accepted_units = {"kg/lb", "in/cm"}

    # ============================================================
    # Normalize cell values
    # ============================================================
    F = norm_formula(sheet["F28"].value)
    G = norm_unit(sheet["G28"].value)

    I = norm_formula(sheet["I28"].value)
    J = norm_unit(sheet["J28"].value)

    L = norm_formula(sheet["L28"].value)
    M = norm_unit(sheet["M28"].value)

    O = norm_formula(sheet["O28"].value)
    P = norm_unit(sheet["P28"].value)

    # Define cell pairs to check (3 ratios in Row 28)
    pairs = [
        ("F28", F, "G28", G),
        ("I28", I, "J28", J),
        ("L28", L, "M28", M)
    ]

    # Track ratio usage for debugging (optional)
    ratio_usage = {"kg/lb": 0, "in/cm": 0}
    unit_usage = {"kg/lb": 0, "in/cm": 0}

    # ============================================================
    # Evaluate the three formula/unit pairs independently
    # ============================================================
    for formula_cell, formula_val, unit_cell, unit_val in pairs:

        # ----- UNIT CHECK -----
        if unit_val in accepted_units:
            unit_text_score += 1
            unit_text_feedback.append((
                "UC28_UNIT_CORRECT",
                {"cell": unit_cell, "unit": unit_val}
            ))
            unit_usage[unit_val] += 1
        else:
            unit_text_feedback.append((
                "UC28_UNIT_INCORRECT",
                {"cell": unit_cell, "expected": list(accepted_units)}
            ))

        # ----- FORMULA CHECK -----
        matched_formula = False
        for ratio, valid_forms in ratio_options.items():
            if formula_val in valid_forms:
                formulas_score += 2
                matched_formula = True
                ratio_usage[ratio] += 1
                formulas_feedback.append((
                    "UC28_FORMULA_CORRECT",
                    {"cell": formula_cell, "ratio": ratio}
                ))
                break

        if not matched_formula:
            formulas_feedback.append((
                "UC28_FORMULA_INCORRECT",
                {"cell": formula_cell}
            ))

    # ============================================================
    # Final Formula Check (O28)
    # ============================================================
    # Must reference all four cells with multiplication
    required_refs = ["C28", "F28", "I28", "L28"]
    ratio_refs = ["F28", "I28", "L28"]  # Just the ratio columns

    if all(ref in O for ref in required_refs) and "*" in O:
        # Full credit: references starting value AND all ratios
        final_formula_score = 2
        final_formula_feedback.append((
            "UC28_FINAL_FORMULA_CORRECT",
            {"cell": "O28"}
        ))
    elif all(ref in O for ref in ratio_refs) and "*" in O and "C28" not in O:
        # Partial credit: references ratios but hardcoded starting value
        final_formula_score = 1.5
        final_formula_feedback.append((
            "UC28_FINAL_FORMULA_PARTIAL",
            {"cell": "O28", "note": "Formula references ratios correctly but uses hardcoded starting value. Use C28 for full credit."}
        ))
    else:
        final_formula_feedback.append((
            "UC28_FINAL_FORMULA_INCORRECT",
            {"cell": "O28", "required": required_refs}
        ))

    # ============================================================
    # Final Unit Check (P28)
    # ============================================================
    # After all conversions, result should be kg/cm²
    if P == "kg/cm^2":
        final_unit_score = 1
        final_unit_feedback.append((
            "UC28_FINAL_UNIT_CORRECT",
            {"cell": "P28", "unit": P}
        ))
    else:
        final_unit_feedback.append((
            "UC28_FINAL_UNIT_INCORRECT",
            {"cell": "P28", "expected": "kg/cm^2"}
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
        "final_unit_feedback": final_unit_feedback,

        # Debug info (useful for troubleshooting)
        "debug_usage": {
            "ratio_usage": ratio_usage,
            "unit_usage": unit_usage
        }
    }
