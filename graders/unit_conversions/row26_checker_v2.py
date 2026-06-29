"""
row26_checker_v2.py — Grade Row 26 of Unit Conversions (mcg/mg and ml/tsp)

Purpose: Validates the conversion ratio formulas, unit labels, and final calculation
         for Row 26, which converts mcg/lb to mcg/tsp using two intermediate ratios:
         mcg/mg (micrograms per milligram) and ml/tsp (milliliters per teaspoon).

Author: Clayton Ragsdale
Dependencies: graders.unit_conversions.utils

Row 26 Layout:
    C26: Starting value (given)
    F26: First conversion ratio formula (mcg/mg OR ml/tsp)
    G26: First ratio unit label
    I26: Second conversion ratio formula (the other ratio)
    J26: Second ratio unit label
    O26: Final formula (=C26*F26*I26)
    P26: Final unit label (mcg/tsp)

Grading Criteria:
    - Formulas (4 pts): 2 pts each for F26 and I26 (must reference lookup table)
    - Unit labels (2 pts): 1 pt each for G26 and J26
    - Final formula (2 pts): O26 must multiply C26*F26*I26
    - Final unit (1 pt): P26 must be "mcg/tsp"
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from graders.unit_conversions.utils import norm_formula, norm_unit


def grade_row_26_v2(sheet: Worksheet) -> Dict[str, Any]:
    """
    V2 JSON-driven strict grader for Row 26 (mcg/mg and ml/tsp conversions).
    
    Grading Rules:
        - Each cell pair (F26/G26, I26/J26) must contain exactly one of the
          required conversion ratios
        - Ratios cannot be duplicated (e.g., can't use mcg/mg twice)
        - Order doesn't matter (mcg/mg can be in F26 or I26)
        - Final formula must multiply the starting value by both ratios
    
    Valid Formulas:
        mcg/mg ratio: =L14/I14, =L14, =L14/1 (references lookup table row 14)
        ml/tsp ratio: =L17/I17, =L17, =L17/1 (references lookup table row 17)
    
    Args:
        sheet: The openpyxl Worksheet object for the Unit Conversions tab
    
    Returns:
        Dict containing:
            - formulas_score: int (0-4)
            - unit_text_score: int (0-2)
            - final_formula_score: int (0-2)
            - final_unit_score: int (0-1)
            - *_feedback: Lists of (code, params) tuples for each category
    """

    # ============================================================
    # Initialize scoring buckets
    # ============================================================
    formulas_score = 0        # Max 4 points (2 per required ratio)
    unit_text_score = 0       # Max 2 points (1 per unit label)
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
    # Define accepted formula patterns
    # ============================================================
    # These formulas reference the lookup table values
    # L14 = 1000 (mcg per mg), I14 = 1 (divisor for ratio)
    # L17 = 4.929... (ml per tsp), I17 = 1 (divisor for ratio)
    mcg_mg_forms = {"=L14/I14", "=L14", "=L14/1"}
    ml_tsp_forms = {"=L17/I17", "=L17", "=L17/1"}

    # ============================================================
    # Normalize cell values
    # ============================================================
    F = norm_formula(sheet["F26"].value)  # First ratio formula
    G = norm_unit(sheet["G26"].value)      # First ratio unit label
    I = norm_formula(sheet["I26"].value)  # Second ratio formula
    J = norm_unit(sheet["J26"].value)      # Second ratio unit label
    O = norm_formula(sheet["O26"].value)  # Final formula
    P = norm_unit(sheet["P26"].value)      # Final unit label

    # ============================================================
    # Define valid unit labels for Row 26
    # ============================================================
    valid_units = {"mcg/mg", "ml/tsp"}

    # Track which ratios have been found (prevent duplicates)
    found_mcg = False
    found_ml = False

    # ============================================================
    # 1. UNIT LABEL CHECKS (G26 and J26)
    # ============================================================
    
    # Check G26 unit label
    if G in valid_units:
        unit_text_score += 1
        unit_text_feedback.append(("UC26_UNIT_VALID_G", {"cell": "G26", "unit": G}))
    else:
        unit_text_feedback.append(("UC26_UNIT_INVALID_G", {
            "cell": "G26",
            "expected": list(valid_units)
        }))

    # Check J26 unit label
    if J in valid_units:
        unit_text_score += 1
        unit_text_feedback.append(("UC26_UNIT_VALID_J", {"cell": "J26", "unit": J}))
    else:
        unit_text_feedback.append(("UC26_UNIT_INVALID_J", {
            "cell": "J26",
            "expected": list(valid_units)
        }))

    # ============================================================
    # 2. FORMULA CHECKS - STRICT (no duplicates allowed)
    # ============================================================

    # Check F26 formula
    if F in mcg_mg_forms and not found_mcg:
        # Found mcg/mg ratio in F26
        formulas_score += 2
        found_mcg = True
        formulas_feedback.append(("UC26_FORMULA_F_VALID", {
            "cell": "F26",
            "ratio": "mcg/mg"
        }))
    elif F in ml_tsp_forms and not found_ml:
        # Found ml/tsp ratio in F26
        formulas_score += 2
        found_ml = True
        formulas_feedback.append(("UC26_FORMULA_F_VALID", {
            "cell": "F26",
            "ratio": "ml/tsp"
        }))
    else:
        # Invalid formula or duplicate ratio
        formulas_feedback.append(("UC26_FORMULA_F_INVALID", {"cell": "F26"}))

    # Check I26 formula
    if I in mcg_mg_forms and not found_mcg:
        # Found mcg/mg ratio in I26
        formulas_score += 2
        found_mcg = True
        formulas_feedback.append(("UC26_FORMULA_I_VALID", {
            "cell": "I26",
            "ratio": "mcg/mg"
        }))
    elif I in ml_tsp_forms and not found_ml:
        # Found ml/tsp ratio in I26
        formulas_score += 2
        found_ml = True
        formulas_feedback.append(("UC26_FORMULA_I_VALID", {
            "cell": "I26",
            "ratio": "ml/tsp"
        }))
    else:
        # Invalid formula or duplicate ratio
        formulas_feedback.append(("UC26_FORMULA_I_INVALID", {"cell": "I26"}))

    # ============================================================
    # 3. FINAL FORMULA CHECK (O26)
    # ============================================================
    # Final formula must reference C26, F26, and I26 with multiplication
    required_refs = ["C26", "F26", "I26"]
    ratio_refs = ["F26", "I26"]  # Just the ratio columns

    if all(ref in O for ref in required_refs) and "*" in O:
        # Full credit: references starting value AND all ratios
        final_formula_score = 2
        final_formula_feedback.append(("UC26_FINAL_FORMULA_CORRECT", {"cell": "O26"}))
    elif all(ref in O for ref in ratio_refs) and "*" in O and "C26" not in O:
        # Partial credit: references ratios but hardcoded starting value
        final_formula_score = 1.5
        final_formula_feedback.append(("UC26_FINAL_FORMULA_PARTIAL", {
            "cell": "O26",
            "note": "Formula references ratios correctly but uses hardcoded starting value. Use C26 for full credit."
        }))
    else:
        final_formula_feedback.append(("UC26_FINAL_FORMULA_INCORRECT", {
            "cell": "O26",
            "required": required_refs
        }))

    # ============================================================
    # 4. FINAL UNIT CHECK (P26)
    # ============================================================
    # After converting mcg/lb through mcg/mg and ml/tsp, result is mcg/tsp
    if P == "mcg/tsp":
        final_unit_score = 1
        final_unit_feedback.append(("UC26_FINAL_UNIT_CORRECT", {
            "cell": "P26",
            "unit": P
        }))
    else:
        final_unit_feedback.append(("UC26_FINAL_UNIT_INCORRECT", {
            "cell": "P26",
            "expected": "mcg/tsp"
        }))

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
