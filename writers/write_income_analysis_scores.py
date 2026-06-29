# writers/write_income_analysis_scores.py

from utilities.feedback_renderer import render_feedback


def _filter_scatterplot_feedback(feedback_list, trendline=False):
    """
    Filter scatterplot feedback into chart vs trendline categories.
    
    Args:
        feedback_list: List of (code, params) tuples
        trendline: If True, return trendline feedback. If False, return chart feedback.
    
    Returns:
        Filtered list of (code, params) tuples
    """
    if not feedback_list:
        return []
    
    # Trendline-related feedback codes
    trendline_codes = {'IA_SCATTER_TRENDLINE_PRESENT', 'IA_SCATTER_TRENDLINE_MISSING',
                       'IA_SCATTER_EXTENDED_CORRECT', 'IA_SCATTER_EXTENDED_MISSING'}
    
    result = []
    for code, params in feedback_list:
        is_trendline = code in trendline_codes
        
        if trendline and is_trendline:
            result.append((code, params))
        elif not trendline and not is_trendline:
            result.append((code, params))
    
    return result


def write_income_analysis_scores(grading_ws, ia_results):
    """
    Write Income Analysis scores and feedback to the Grading Sheet.

    Income Analysis now uses feedback codes + params rendered via:
      utilities/feedback_renderer.py + feedback/income_analysis.json
    
    Scatterplot feedback is split:
      - G6: Chart presence, title, axis labels
      - G7: Trendline presence, extension
    """
    TAB = "income_analysis"

    # Row 3 - Name
    grading_ws["F3"] = ia_results.get("name_score", 0)
    grading_ws["G3"] = render_feedback(ia_results.get("name_feedback"), TAB)

    # Row 4 - Slope & Intercept (formulas + formatting)
    grading_ws["F4"] = ia_results.get("slope_score", 0)
    grading_ws["G4"] = render_feedback(ia_results.get("slope_feedback"), TAB)

    # Row 5 - Predictions (formulas + formatting)
    grading_ws["F5"] = ia_results.get("predictions_score", 0)
    grading_ws["G5"] = render_feedback(ia_results.get("predictions_feedback"), TAB)

    # Row 6 - Scatterplot Chart & Labels (6 points max)
    # Feedback: chart found, title, x-label, y-label
    scatter_feedback = ia_results.get("scatterplot_feedback", [])
    chart_feedback = _filter_scatterplot_feedback(scatter_feedback, trendline=False)
    grading_ws["F6"] = ia_results.get("scatterplot_chart_score", 0)
    grading_ws["G6"] = render_feedback(chart_feedback, TAB)
    
    # Row 7 - Scatterplot Trendline (2 points max)
    # Feedback: trendline present, extension correct
    trendline_feedback = _filter_scatterplot_feedback(scatter_feedback, trendline=True)
    grading_ws["F7"] = ia_results.get("scatterplot_trendline_score", 0)
    grading_ws["G7"] = render_feedback(trendline_feedback, TAB)
