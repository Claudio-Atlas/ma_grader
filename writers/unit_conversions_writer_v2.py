# writers/unit_conversions_writer_v2.py

from openpyxl.worksheet.worksheet import Worksheet
from utilities.feedback_renderer import render_feedback


def write_unit_conversions_scores_v2(ws_grading: Worksheet, results: dict) -> Worksheet:
    """
    Writes Unit Conversions V2 results into the grading sheet.

    Uses:
      feedback/unit_conversions.json
    via:
      utilities/json_loader.py + utilities/feedback_renderer.py
    """

    TAB = "unit_conversions"

    # --- Scores ---
    ws_grading["F9"].value  = results.get("final_unit_score", 0)
    ws_grading["F10"].value = results.get("unit_text_score", 0)
    ws_grading["F11"].value = results.get("formulas_score", 0)
    ws_grading["F12"].value = results.get("final_formula_score", 0)
    ws_grading["F13"].value = results.get("temp_and_celsius_score", 0)

    # --- Feedback ---
    ws_grading["G9"].value  = render_feedback(results.get("final_unit_feedback"), TAB)
    ws_grading["G10"].value = render_feedback(results.get("unit_text_feedback"), TAB)
    ws_grading["G11"].value = render_feedback(results.get("formulas_feedback"), TAB)
    ws_grading["G12"].value = render_feedback(results.get("final_formula_feedback"), TAB)
    ws_grading["G13"].value = render_feedback(results.get("temp_and_celsius_feedback"), TAB)

    return ws_grading
