"""
unit_conversions_checker_v2.py — Main orchestrator for Unit Conversions tab grading

Purpose: Coordinates all grading checks for the Unit Conversions worksheet tab.
         Aggregates scores and feedback from row-specific checker modules and
         returns a unified results dictionary for the writer to process.

Author: Clayton Ragsdale
Dependencies: row26_checker_v2, row27_checker_v2, row28_checker_v2, row29_checker_v2,
              temp_conversions_v2

Grading Breakdown (46 points total):
    Row 26 (mcg/mg, ml/tsp):
        - 4 pts: Conversion ratio formulas (2 pts each)
        - 2 pts: Unit labels
        - 2 pts: Final formula (O26)
        - 1 pt:  Final unit label (P26)
    
    Row 27 (gal/l, h/d):
        - 4 pts: Conversion ratio formulas
        - 2 pts: Unit labels
        - 2 pts: Final formula (O27)
        - 1 pt:  Final unit label (P27)
    
    Row 28 (kg/lb, in/cm) - 3 ratios:
        - 6 pts: Conversion ratio formulas (2 pts each)
        - 3 pts: Unit labels
        - 2 pts: Final formula (O28)
        - 1 pt:  Final unit label (P28)
    
    Row 29 (ft/mi, yr/d, d/h) - 3 ratios:
        - 6 pts: Conversion ratio formulas
        - 3 pts: Unit labels
        - 2 pts: Final formula (O29)
        - 1 pt:  Final unit label (P29)
    
    Temperature Conversions (C40, A41):
        - 4 pts: Temperature formulas (2 pts each)
"""

from typing import Dict, Any, List, Tuple
from openpyxl.worksheet.worksheet import Worksheet

from graders.unit_conversions.row26_checker_v2 import grade_row_26_v2
from graders.unit_conversions.row27_checker_v2 import grade_row_27_v2
from graders.unit_conversions.row28_checker_v2 import grade_row_28_v2
from graders.unit_conversions.row29_checker_v2 import grade_row_29_v2
from graders.unit_conversions.temp_conversions_v2 import grade_temp_conversions_v2


def grade_unit_conversions_tab_v2(sheet: Worksheet) -> Dict[str, Any]:
    """
    Orchestrate grading for the entire Unit Conversions tab using the V2 system.
    
    This function runs all row checkers and aggregates their results into
    a unified dictionary. Each row checker evaluates:
        - Conversion ratio formulas (references to lookup tables)
        - Unit labels (text describing the conversion ratio)
        - Final formula (multiplies all ratios together)
        - Final unit label (resulting unit after all conversions)
    
    Scoring Categories:
        - unit_text_score: Sum of all unit label checks (rows 26-29)
        - formulas_score: Sum of all conversion ratio formula checks
        - final_formula_score: Sum of all final formula checks (O column)
        - final_unit_score: Sum of all final unit label checks (P column)
        - temp_and_celsius_score: Temperature conversion formulas
    
    Args:
        sheet: The openpyxl Worksheet object for the Unit Conversions tab
    
    Returns:
        Dict containing:
            - Scores for each category (unit_text_score, formulas_score, etc.)
            - Feedback lists for each category (unit_text_feedback, etc.)
    
    Example:
        >>> from openpyxl import load_workbook
        >>> wb = load_workbook("student_submission.xlsx")
        >>> ws = wb["Unit Conversions"]
        >>> results = grade_unit_conversions_tab_v2(ws)
        >>> total = sum([
        ...     results['unit_text_score'],
        ...     results['formulas_score'],
        ...     results['final_formula_score'],
        ...     results['final_unit_score'],
        ...     results['temp_and_celsius_score']
        ... ])
        >>> print(f"Total: {total}/46")
    """

    # ============================================================
    # Run each row checker
    # ============================================================
    r26 = grade_row_26_v2(sheet)  # mcg/mg and ml/tsp conversions
    r27 = grade_row_27_v2(sheet)  # gal/l and h/d conversions
    r28 = grade_row_28_v2(sheet)  # kg/lb and in/cm conversions (3 ratios)
    r29 = grade_row_29_v2(sheet)  # ft/mi, yr/d, d/h conversions (3 ratios)
    temp = grade_temp_conversions_v2(sheet)  # Temperature: C40 and A41

    # ============================================================
    # Aggregate scores from all rows
    # ============================================================

    # Unit text score: Points for correct unit labels (G, J, M columns)
    unit_text_score = (
        r26["unit_text_score"]
        + r27["unit_text_score"]
        + r28["unit_text_score"]
        + r29["unit_text_score"]
    )

    # Formula score: Points for correct conversion ratio formulas (F, I, L columns)
    formulas_score = (
        r26["formulas_score"]
        + r27["formulas_score"]
        + r28["formulas_score"]
        + r29["formulas_score"]
    )

    # Final formula score: Points for correct final calculation (O column)
    final_formula_score = (
        r26["final_formula_score"]
        + r27["final_formula_score"]
        + r28["final_formula_score"]
        + r29["final_formula_score"]
    )

    # Final unit score: Points for correct final unit label (P column)
    final_unit_score = (
        r26["final_unit_score"]
        + r27["final_unit_score"]
        + r28["final_unit_score"]
        + r29["final_unit_score"]
    )

    # Temperature conversion score
    temp_score = temp["temp_and_celsius_score"]

    # ============================================================
    # Aggregate feedback lists from all rows
    # ============================================================

    unit_text_feedback: List[Tuple[str, Dict[str, Any]]] = (
        r26["unit_text_feedback"]
        + r27["unit_text_feedback"]
        + r28["unit_text_feedback"]
        + r29["unit_text_feedback"]
    )

    formulas_feedback: List[Tuple[str, Dict[str, Any]]] = (
        r26["formulas_feedback"]
        + r27["formulas_feedback"]
        + r28["formulas_feedback"]
        + r29["formulas_feedback"]
    )

    final_formula_feedback: List[Tuple[str, Dict[str, Any]]] = (
        r26["final_formula_feedback"]
        + r27["final_formula_feedback"]
        + r28["final_formula_feedback"]
        + r29["final_formula_feedback"]
    )

    final_unit_feedback: List[Tuple[str, Dict[str, Any]]] = (
        r26["final_unit_feedback"]
        + r27["final_unit_feedback"]
        + r28["final_unit_feedback"]
        + r29["final_unit_feedback"]
    )

    temp_feedback: List[Tuple[str, Dict[str, Any]]] = temp["temp_and_celsius_feedback"]

    # ============================================================
    # Return unified V2 structure
    # ============================================================

    return {
        # Scores
        "unit_text_score": unit_text_score,
        "formulas_score": formulas_score,
        "final_formula_score": final_formula_score,
        "final_unit_score": final_unit_score,
        "temp_and_celsius_score": temp_score,

        # Feedback lists
        "unit_text_feedback": unit_text_feedback,
        "formulas_feedback": formulas_feedback,
        "final_formula_feedback": final_formula_feedback,
        "final_unit_feedback": final_unit_feedback,
        "temp_and_celsius_feedback": temp_feedback,
    }
