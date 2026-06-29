from graders.ma2_income_projection.grade_name_check import grade_income_projection_name
from graders.ma2_income_projection.grade_income_projection_cpi_values import grade_income_projection_cpi_values
from graders.ma2_income_projection.grade_trendline_formulas import grade_slope_formula, grade_intercept_formula
from graders.ma2_income_projection.grade_cpi_projection_section import grade_cpi_projection_section
from graders.ma2_income_projection.grade_income_projection_section import grade_income_projection_section
from graders.ma2_income_projection.grade_income_projection_formatting import grade_income_projection_formatting



def grade_income_projection_tab(ws):
    """
    Master wrapper for 'Income and Projection' tab.
    Returns each section's points and comments separately
    so the writer can easily map them into the Grading Sheet.
    """

    results = {}

    try:
        # --- Individual sub-graders ---
        name = grade_income_projection_name(ws)
        cpi_values = grade_income_projection_cpi_values(ws)
        slope = grade_slope_formula(ws)
        intercept = grade_intercept_formula(ws)
        cpi_projection = grade_cpi_projection_section(ws)
        income_projection = grade_income_projection_section(ws)
        formatting=grade_income_projection_formatting(ws)

        # --- Store each separately for writer integration ---
        results = {
            "name_check": {
                "points": name["points"],
                "comment": name["comment"],
            },
            "cpi_values": {
                "points": cpi_values["points"],
                "comment": cpi_values["comment"],
            },
            "slope_formula": {
                "points": slope["points"],
                "comment": slope["comment"],
            },
            "intercept_formula": {
                "points": intercept["points"],
                "comment": intercept["comment"],
            },
            "cpi_projection_section": {
                "points": cpi_projection["points"],
                "comment": cpi_projection["comment"],
            },
            "income_projection_section": {
                "points": income_projection["points"],
                "comment": income_projection["comment"],
            },
            "formatting_section": {
                "points":formatting["points"],
                "comment":formatting["comment"],
            },
        }

        # --- Optional: total if you want quick verification ---
        total_points = sum([r["points"] for r in results.values()])
        results["total_points"] = total_points

    except Exception as e:
        results = {
            "error": f"Error grading Income and Projection tab: {e}",
            "total_points": 0,
        }

    return results
