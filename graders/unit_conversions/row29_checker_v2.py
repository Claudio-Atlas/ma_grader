"""
row29_checker_v2.py — Grade Row 29 of Unit Conversions (ft/mi, yr/d, d/h)

Purpose: Validates the conversion ratio formulas, unit labels, and final calculation
         for Row 29, which uses THREE conversion ratios to convert mi/yr to ft/h:
         ft/mi (feet per mile), yr/d (years per day), and d/h (days per hour).

Author: Clayton Ragsdale
Dependencies: graders.unit_conversions.utils

Row 29 Layout:
    C29: Starting value (given, in mi/yr)
    F29: First conversion ratio formula (ft/mi, yr/d, or d/h)
    G29: First ratio unit label
    I29: Second conversion ratio formula
    J29: Second ratio unit label
    L29: Third conversion ratio formula
    M29: Third ratio unit label
    O29: Final formula (=C29*F29*I29*L29)
    P29: Final unit label (ft/h or ft/hr)

Grading Criteria:
    - Formulas (6 pts): 2 pts each for F29, I29, L29
    - Unit labels (3 pts): 1 pt each for G29, J29, M29
    - Final formula (2 pts): O29 must multiply C29*F29*I29*L29
    - Final unit (1 pt): P29 must be "ft/h" or "ft/hr"
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from graders.unit_conversions.utils import norm_formula, norm_unit


def grade_row_29_v2(sheet: Worksheet) -> Dict[str, Any]:
    """
    V2 JSON-driven strict grader for Row 29 (ft/mi, yr/d, d/h conversions).
    
    Row 29 converts mi/yr to ft/h using three conversion ratios:
        - ft/mi: Feet per mile (5280 ft/mi)
        - yr/d: Years per day (inverse of 365 d/yr)
        - d/h: Days per hour (inverse of 24 h/d)
    
    Time Unit Normalization:
        - hr → h
        - day → d
        - year → yr
        - y/ → yr/ (handles abbreviated year)
    
    Valid Formulas:
        ft/mi: =L21/I21, =L21, =L21/1 (row 21 has 5280)
        yr/d:  =I23/L23, =1/L23 (row 23 has 365)
        d/h:   =I22/L22, =1/L22 (row 22 has 24)
    
    Args:
        sheet: The openpyxl Worksheet object for the Unit Conversions tab
    
    Returns:
        Dict containing scores and feedback for each grading category
    """

    # ============================================================
    # Initialize scoring buckets
    # ============================================================
    formulas_score = 0         # Max 6 points (3 ratios * 2 pts)
    unit_text_score = 0        # Max 3 points (3 labels * 1 pt)
    final_formula_score = 0    # Max 2 points
    final_unit_score = 0       # Max 1 point

    # ============================================================
    # Initialize feedback buckets
    # ============================================================
    formulas_feedback: List[Tuple[str, Dict[str, Any]]] = []
    unit_text_feedback: List[Tuple[str, Dict[str, Any]]] = []
    final_formula_feedback: List[Tuple[str, Dict[str, Any]]] = []
    final_unit_feedback: List[Tuple[str, Dict[str, Any]]] = []

    # ============================================================
    # Define valid formulas for Row 29
    # ============================================================
    # Row 21: ft/mi (L21 = 5280)
    # Row 23: yr/d (L23 = 365)
    # Row 22: d/h (L22 = 24)
    ratio_formulas = {
        "ft/mi": {"=L21/I21", "=L21", "=L21/1"},
        "yr/d":  {"=I23/L23", "=1/L23"},
        "d/h":   {"=I22/L22", "=1/L22"}
    }

    accepted_units = {"ft/mi", "yr/d", "d/h"}

    # ============================================================
    # Helper function for time unit normalization
    # ============================================================
    def normalize_time_unit(u: str) -> str:
        """
        Normalize time unit abbreviations for consistent comparison.
        
        Handles common variations students might use:
        - hr → h
        - day → d  
        - year → yr
        - y/ → yr/ (abbreviated year at start of ratio)
        """
        if not isinstance(u, str):
            return ""
        u = u.replace("hr", "h")
        u = u.replace("day", "d")
        u = u.replace("year", "yr")
        u = u.replace("y/", "yr/")  # Handle "y/d" → "yr/d"
        return u

    # ============================================================
    # Normalize cell values
    # ============================================================
    F = norm_formula(sheet["F29"].value)
    I = norm_formula(sheet["I29"].value)
    L = norm_formula(sheet["L29"].value)
    O = norm_formula(sheet["O29"].value)

    G = normalize_time_unit(norm_unit(sheet["G29"].value))
    J = normalize_time_unit(norm_unit(sheet["J29"].value))
    M = normalize_time_unit(norm_unit(sheet["M29"].value))
    P = normalize_time_unit(norm_unit(sheet["P29"].value))

    # Define cell pairs to check (3 ratios in Row 29)
    pairs = [
        ("F29", F, "G29", G),
        ("I29", I, "J29", J),
        ("L29", L, "M29", M)
    ]

    # Track which ratios have been used (prevent double-counting)
    used_ratios = set()

    # ============================================================
    # Evaluate three formula/unit pairs
    # ============================================================
    for f_cell, f_val, u_cell, u_val in pairs:

        # ----- UNIT CHECK -----
        if u_val in accepted_units:
            unit_text_score += 1
            unit_text_feedback.append((
                "UC29_UNIT_CORRECT",
                {"cell": u_cell, "unit": u_val}
            ))
        else:
            unit_text_feedback.append((
                "UC29_UNIT_INCORRECT",
                {"cell": u_cell, "expected": list(accepted_units)}
            ))

        # ----- FORMULA CHECK -----
        # Check each ratio pattern, but only count each ratio once
        matched = False
        for ratio, forms in ratio_formulas.items():
            if f_val in forms and ratio not in used_ratios:
                formulas_score += 2
                used_ratios.add(ratio)
                matched = True
                formulas_feedback.append((
                    "UC29_FORMULA_CORRECT",
                    {"cell": f_cell, "ratio": ratio}
                ))
                break

        if not matched:
            formulas_feedback.append((
                "UC29_FORMULA_INCORRECT",
                {"cell": f_cell}
            ))

    # ============================================================
    # Final formula check - O29
    # ============================================================
    # Must reference all four cells with multiplication
    required_refs = ["C29", "F29", "I29", "L29"]
    ratio_refs = ["F29", "I29", "L29"]  # Just the ratio columns

    if all(ref in O for ref in required_refs) and "*" in O:
        # Full credit: references starting value AND all ratios
        final_formula_score = 2
        final_formula_feedback.append((
            "UC29_FINAL_FORMULA_CORRECT",
            {"cell": "O29"}
        ))
    elif all(ref in O for ref in ratio_refs) and "*" in O and "C29" not in O:
        # Partial credit: references ratios but hardcoded starting value
        final_formula_score = 1.5
        final_formula_feedback.append((
            "UC29_FINAL_FORMULA_PARTIAL",
            {"cell": "O29", "note": "Formula references ratios correctly but uses hardcoded starting value. Use C29 for full credit."}
        ))
    else:
        final_formula_feedback.append((
            "UC29_FINAL_FORMULA_INCORRECT",
            {"cell": "O29", "required": required_refs}
        ))

    # ============================================================
    # Final unit check - P29
    # ============================================================
    # After all conversions, result should be ft/h (accept ft/hr too)
    if P in {"ft/h", "ft/hr"}:
        final_unit_score = 1
        final_unit_feedback.append((
            "UC29_FINAL_UNIT_CORRECT",
            {"cell": "P29", "unit": P}
        ))
    else:
        final_unit_feedback.append((
            "UC29_FINAL_UNIT_INCORRECT",
            {"cell": "P29", "expected": "ft/h or ft/hr"}
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
