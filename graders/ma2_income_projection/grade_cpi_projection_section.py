from graders.ma2_income_projection.grade_projection_year import grade_projection_year
from graders.ma2_income_projection.grade_projected_cpi import grade_projected_cpi
from graders.ma2_income_projection.grade_inflation_rate import grade_inflation_rate

def grade_cpi_projection_section(ws):
    """
    Wrapper for CPI Projection section (K32–K34)
    Total: 6 points (1 + 3 + 2)
    """
    result = {"points": 0, "comment": "", "details": {}}

    try:
        # --- Individual graders ---
        year = grade_projection_year(ws)
        cpi = grade_projected_cpi(ws)
        infl = grade_inflation_rate(ws)

        # --- Total and summary ---
        total_points = year["points"] + cpi["points"] + infl["points"]

        result["points"] = total_points
        result["details"] = {
            "Projection Year (K32)": year,
            "Projected CPI (K33)": cpi,
            "Inflation Rate (K34)": infl,
        }

        result["comment"] = (
            f"CPI Projection Section → "
            f"Year: {year['points']}/1, CPI: {cpi['points']}/3, Inflation: {infl['points']}/2 "
            f"= Total {total_points}/6"
        )

    except Exception as e:
        result["points"] = 0
        result["comment"] = f"Error grading CPI Projection section: {e}"

    return result
