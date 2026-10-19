from graders.ma2_income_projection.grade_current_income_reference import grade_current_income_reference
from graders.ma2_income_projection.grade_five_year_income import grade_five_year_income
from graders.ma2_income_projection.grade_monthly_income import grade_monthly_income

def grade_income_projection_section(ws):
    """
    Wrapper for Income Projection section (K35–K37)
    Total: 6 points (1 + 3 + 2)
    """
    result = {"points": 0, "comment": "", "details": {}}

    try:
        # --- Individual graders ---
        income_ref = grade_current_income_reference(ws)
        five_year = grade_five_year_income(ws)
        monthly = grade_monthly_income(ws)

        # --- Total and summary ---
        total_points = income_ref["points"] + five_year["points"] + monthly["points"]

        result["points"] = total_points
        result["details"] = {
            "Current Income (K35)": income_ref,
            "Five-Year Income (K36)": five_year,
            "Monthly Income (K37)": monthly,
        }

        # Each part's own comment (the points column already shows the score).
        result["comment"] = " | ".join(p["comment"] for p in (income_ref, five_year, monthly) if p.get("comment"))

    except Exception as e:
        result["points"] = 0
        result["comment"] = f"Error grading Income Projection section: {e}"

    return result
