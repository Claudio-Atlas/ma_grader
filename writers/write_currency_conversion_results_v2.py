# writers/write_currency_conversion_results_v2.py

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font
from utilities.feedback_renderer import render_feedback

# Standard black font for feedback cells
BLACK_FONT = Font(color="000000")


def _filter_feedback(feedback_list, include_format=True):
    """
    Filter feedback list to include or exclude FORMAT codes.
    
    Args:
        feedback_list: List of (code, params) tuples
        include_format: If True, return only FORMAT codes. If False, exclude FORMAT codes.
    
    Returns:
        Filtered list of (code, params) tuples
    """
    if not feedback_list:
        return []
    
    result = []
    for code, params in feedback_list:
        is_format_code = "FORMAT" in code
        
        if include_format and is_format_code:
            result.append((code, params))
        elif not include_format and not is_format_code:
            # Also exclude SUMMARY codes from individual rows (they contain format info)
            if "_SUMMARY" not in code:
                result.append((code, params))
    
    return result


def write_currency_conversion_results_v2(ws_grading: Worksheet, results: dict) -> Worksheet:
    """
    Writes Currency Conversion V2 results into the grading sheet.
    
    Feedback routing:
        - G15-G18: All feedback for those rows
        - G19: Only accuracy feedback (no formatting)
        - G20: Only formula feedback (no formatting)
        - G21: Only formula feedback (no formatting)
        - G22: ALL formatting feedback from rows 19, 20, 21 combined

    Uses:
      feedback/currency_conversion.json
    via:
      utilities/json_loader.py + utilities/feedback_renderer.py
    """

    TAB = "currency_conversion"

    # Row 15
    ws_grading["F15"].value = results.get("row15_score", 0)
    ws_grading["G15"].value = render_feedback(results.get("row15_feedback"), TAB)
    ws_grading["G15"].font = BLACK_FONT

    # Row 16
    ws_grading["F16"].value = results.get("row16_score", 0)
    ws_grading["G16"].value = render_feedback(results.get("row16_feedback"), TAB)
    ws_grading["G16"].font = BLACK_FONT

    # Row 17
    ws_grading["F17"].value = results.get("row17_score", 0)
    ws_grading["G17"].value = render_feedback(results.get("row17_feedback"), TAB)
    ws_grading["G17"].font = BLACK_FONT

    # Row 18
    ws_grading["F18"].value = results.get("row18_score", 0)
    ws_grading["G18"].value = render_feedback(results.get("row18_feedback"), TAB)
    ws_grading["G18"].font = BLACK_FONT

    # Row 19 - Accuracy feedback only (formatting goes to G22)
    row19_feedback = results.get("row19_feedback", [])
    row19_accuracy_fb = _filter_feedback(row19_feedback, include_format=False)
    ws_grading["F19"].value = results.get("row19_accuracy_score", 0)
    ws_grading["G19"].value = render_feedback(row19_accuracy_fb, TAB)
    ws_grading["G19"].font = BLACK_FONT

    # Row 20 - Formula feedback only (formatting goes to G22)
    row20_feedback = results.get("row20_feedback", [])
    row20_formula_fb = _filter_feedback(row20_feedback, include_format=False)
    ws_grading["F20"].value = results.get("row20_formula_score", 0)
    ws_grading["G20"].value = render_feedback(row20_formula_fb, TAB)
    ws_grading["G20"].font = BLACK_FONT

    # Row 21 - Formula feedback only (formatting goes to G22)
    row21_feedback = results.get("row21_feedback", [])
    row21_formula_fb = _filter_feedback(row21_feedback, include_format=False)
    ws_grading["F21"].value = results.get("row21_formula_score", 0)
    ws_grading["G21"].value = render_feedback(row21_formula_fb, TAB)
    ws_grading["G21"].font = BLACK_FONT

    # Row 22 - Formatting Total with ALL formatting feedback combined
    row19_format_fb = _filter_feedback(row19_feedback, include_format=True)
    row20_format_fb = _filter_feedback(row20_feedback, include_format=True)
    row21_format_fb = _filter_feedback(row21_feedback, include_format=True)
    
    all_format_feedback = row19_format_fb + row20_format_fb + row21_format_fb
    
    ws_grading["F22"].value = results.get("formatting_total", 0)
    ws_grading["G22"].value = render_feedback(all_format_feedback, TAB)
    ws_grading["G22"].font = BLACK_FONT

    return ws_grading
