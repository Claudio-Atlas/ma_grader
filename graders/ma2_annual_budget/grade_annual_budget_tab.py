# graders/annual_budget/grade_annual_budget_tab.py

from openpyxl import load_workbook

from graders.ma2_annual_budget.grade_budget_housing_other import grade_budget_housing_other
from graders.ma2_annual_budget.grade_budget_row26 import grade_budget_row26
from graders.ma2_annual_budget.grade_budget_row27 import grade_budget_row27
from graders.ma2_annual_budget.grade_budget_row28 import grade_budget_row28
from graders.ma2_annual_budget.grade_budget_row30_32 import (
    grade_budget_row30,
    grade_budget_row32,
)
from graders.ma2_annual_budget.grade_budget_formatting import grade_budget_formatting
from graders.ma2_annual_budget.grade_budget_pie_chart import grade_budget_pie_chart


def grade_annual_budget_tab(student_file_path):
    """
    Wrapper for the ENTIRE Annual Budget tab.

    Sections included:
    - B18:D25 (Housing→Other daily/weekly/etc costs)
    - Row 26 (Monthly student loan payment)
    - Row 27 (Monthly credit card payment)
    - Row 28 (Total Annual Budget SUM)
    - Row 30 (Projected Total in 5 Years)
    - Row 32 (Remaining Total)
    - Formatting for D30 and D32

    Returns a dictionary containing:
        {
            "housing_other": {...},
            "row26": {...},
            "row27": {...},
            "row28": {...},
            "row30": {...},
            "row32": {...},
            "formatting": {...}
        }
    """

    try:
        # Load workbook with formulas visible
        wb = load_workbook(student_file_path, data_only=False)
        ws = wb["Annual Budget"]

        # --------------------------
        # Run all section graders
        # --------------------------
        housing_other = grade_budget_housing_other(ws)
        row26 = grade_budget_row26(ws)
        row27 = grade_budget_row27(ws)
        row28 = grade_budget_row28(ws)
        row30 = grade_budget_row30(ws)
        row32 = grade_budget_row32(ws)
        formatting = grade_budget_formatting(ws)
        pie_chart = grade_budget_pie_chart(ws)

        wb.close()

        # --------------------------
        # Package results
        # --------------------------
        return {
            "housing_other": housing_other,
            "row26": row26,
            "row27": row27,
            "row28": row28,
            "row30": row30,
            "row32": row32,
            "formatting": formatting,
            "pie_chart": pie_chart,
        }

    except Exception as e:
        return {"error": f"Error grading Annual Budget tab: {e}"}
