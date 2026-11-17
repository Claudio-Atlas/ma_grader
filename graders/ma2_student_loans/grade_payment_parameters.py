from utilities.xl import load_workbook  # strips _xlfn. prefixes
from graders.ma2_student_loans.grade_unsubsidized_setup import is_constant

def grade_payment_parameters(student_file_path):
    """
    Grades the simple input values in B27 and B28 on the 'Student Loans' tab.
    Each cell is worth 1 point.

    Expected defaults:
        B27 = 12   (payments per year)
        B28 = 10   (loan years)

    Returns a dictionary with points, comments, and total.
    """
    # --- Editable expected values ---
    expected_values = {
        "B27": 12,
        "B28": 10,
    }

    wb = load_workbook(student_file_path, data_only=True)
    ws = wb["Student Loans"]
    ws_f = None  # formulas, loaded only when a value wasn't saved

    results = {}
    total_points = 0

    for cell, expected in expected_values.items():
        student_val = ws[cell].value
        entry = {"points": 0, "comment": ""}

        if student_val is None:
            # No saved value (file not recalculated): a constant formula like
            # =12 still counts.
            if ws_f is None:
                ws_f = load_workbook(student_file_path)["Student Loans"]
            if is_constant(ws_f[cell].value, expected):
                student_val = expected
        if student_val == expected:
            entry["points"] = 1
            entry["comment"] = f"{cell} value correct ({student_val})."
        else:
            label = {"B27": "payments per year", "B28": "number of years"}.get(cell, "value")
            entry["comment"] = (
                f"Your {label} ({cell}) should be {expected}, but it's {student_val}."
            )

        total_points += entry["points"]
        results[cell] = entry

    wb.close()

    results["total_points"] = total_points
    results["comment"] = " | ".join([r["comment"] for c, r in results.items() if c in expected_values])

    return results
