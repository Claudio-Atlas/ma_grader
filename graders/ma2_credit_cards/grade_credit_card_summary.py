from openpyxl import load_workbook

def _norm(f):
    """Normalize Excel formulas for easier checking."""
    if not isinstance(f, str):
        return ""
    return (
        f.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
    )


def _check_j25_years(ws_formulas, payoff_month, excel_row):
    """
    J25 = number of years to pay off.
    Acceptable:
        =A{excel_row}/12   OR
        ={payoff_month}/12
    Worth 3 points.
    """
    formula = ws_formulas["J25"].value
    f = _norm(formula)

    # Payments-per-year may be the literal 12 or a reference to C15 (which is 12).
    acceptable = {
        f"=a{excel_row}/12", f"={payoff_month}/12",
        f"=a{excel_row}/c15", f"={payoff_month}/c15",
    }

    if f in acceptable:
        return {
            "points": 3,
            "comment": "J25 correctly calculates years to pay off (months ÷ 12 or ÷ C15).",
        }
    else:
        return {
            "points": 0,
            "comment": (
                f"J25 incorrect. Expected =A{excel_row}/12 or /C15 "
                f"(or ={payoff_month}/12 or /C15)."
            ),
        }


def _check_j26_total_paid(ws_formulas, excel_row):
    """
    J26 = SUM of all payments in column C from row 5 to payoff row.
    Expected: =SUM(C5:C{excel_row})
    (Flexible to allow lower/upper case and $ removal)
    Worth 3 points.
    """
    formula = ws_formulas["J26"].value
    f = _norm(formula)

    expected = f"=sum(c25:c{excel_row})"

    if f == expected:
        return {
            "points": 3,
            "comment": f"J26 correctly sums payments with {expected}.",
        }

    return {
        "points": 0,
        "comment": f"J26 incorrect. Expected {expected}.",
    }


def _check_j27_interest(ws_formulas, excel_row):
    """
    J27 = total interest paid. Two valid approaches:
        - subtraction:  =J26-B25
        - sum of the monthly interest column:  =SUM(E25:E{payoff_row})
    Worth 3 points.
    """
    formula = ws_formulas["J27"].value
    f = _norm(formula)

    expected_sub = "=j26-b25"
    expected_sum = f"=sum(e25:e{excel_row})"

    if f in (expected_sub, expected_sum):
        return {
            "points": 3,
            "comment": "J27 correctly calculates total interest (J26-B25 or SUM of column E).",
        }

    return {
        "points": 0,
        "comment": f"J27 incorrect. Expected =J26-B25 or =SUM(E25:E{excel_row}).",
    }


# -------------------------------------------------------------------
# MAIN PUBLIC WRAPPER
# -------------------------------------------------------------------

def grade_credit_card_summary(student_file_path, payoff_month, excel_row):
    """
    Grades the credit card summary section (J25–J27).

    payoff_month: integer (e.g., 194)
    excel_row: payoff row in the sheet (e.g., 218)

    Returns:
        {
            "J25": {...},
            "J26": {...},
            "J27": {...},
            "total_points": int,
            "comment": "combined summary"
        }
    """

    wb_f = load_workbook(student_file_path, data_only=False)
    ws_f = wb_f["Credit Cards"]

    j25 = _check_j25_years(ws_f, payoff_month, excel_row)
    j26 = _check_j26_total_paid(ws_f, excel_row)
    j27 = _check_j27_interest(ws_f, excel_row)

    wb_f.close()

    total = j25["points"] + j26["points"] + j27["points"]

    return {
        "J25": j25,
        "J26": j26,
        "J27": j27,
        "total_points": total,
        "comment": f"{j25['comment']} | {j26['comment']} | {j27['comment']}"
    }
