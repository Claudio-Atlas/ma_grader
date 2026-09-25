import re

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


def _check_j25_years(ws_formulas, payoff_month, excel_row, value_ok=False):
    """
    J25 = number of years to pay off.
    Acceptable:
        =A{excel_row}/12   OR
        ={payoff_month}/12
    Worth 3 points.
    """
    formula = ws_formulas["J25"].value
    f = _norm(formula)

    # Years to pay off = (payoff month) / 12. The month may come from any month
    # cell in column A (the student references their own payoff row) or be typed,
    # and payments-per-year may be the literal 12 or a reference to C15.
    if value_ok or re.fullmatch(r"=a\d+/(12|c15)", f) or re.fullmatch(r"=\d+/(12|c15)", f):
        return {
            "points": 3,
            "comment": "J25 correctly calculates years to pay off (months ÷ 12 or ÷ C15).",
        }
    return {
        "points": 0,
        "comment": "J25 incorrect. Expected the payoff month ÷ 12 (e.g. =A{row}/12 or =A{row}/C15).",
    }


def _check_j26_total_paid(ws_formulas, excel_row, value_ok=False):
    """
    J26 = SUM of all payments in column C from row 5 to payoff row.
    Expected: =SUM(C5:C{excel_row})
    (Flexible to allow lower/upper case and $ removal)
    Worth 3 points.
    """
    formula = ws_formulas["J26"].value
    f = _norm(formula)

    # Total paid = SUM of the Payment column from row 25 down to the student's own
    # payoff/last row (any end row is fine — trailing rows are 0, so the sum is
    # the same). Accept =SUM(C25:C{n}) for any n.
    if value_ok or re.fullmatch(r"=sum\(c25:c\d+\)", f):
        return {
            "points": 3,
            "comment": "J26 correctly sums the Payment column from C25 to the payoff row.",
        }

    return {
        "points": 0,
        "comment": "J26 incorrect. Expected =SUM(C25:C{payoff row}).",
    }


def _check_j27_interest(ws_formulas, excel_row, value_ok=False):
    """
    J27 = total interest paid. Two valid approaches:
        - subtraction:  =J26-B25
        - sum of the monthly interest column:  =SUM(E25:E{payoff_row})
    Worth 3 points.
    """
    formula = ws_formulas["J27"].value
    f = _norm(formula)

    # Total interest = total paid (J26) minus the original balance (referenced as
    # B25 or C14), OR the SUM of the monthly-interest column E down to any end row.
    if value_ok or f in ("=j26-b25", "=j26-c14") or re.fullmatch(r"=sum\(e25:e\d+\)", f):
        return {
            "points": 3,
            "comment": "J27 correctly calculates total interest (J26 minus the balance, or SUM of column E).",
        }

    return {
        "points": 0,
        "comment": "J27 incorrect. Expected =J26-B25 (or =J26-C14) or =SUM(E25:E{payoff row}).",
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
    wb_v = load_workbook(student_file_path, data_only=True)
    ws_f = wb_f["Credit Cards"]
    ws_v = wb_v["Credit Cards"]

    # --- Value-based expectations: accept ANY formula that computes the right
    # number (handles the many valid variants — COUNTIF, different end rows,
    # etc.). Structural pattern-matching in each check is a fallback. ---
    def _num(cell):
        v = ws_v[cell].value
        return float(v) if isinstance(v, (int, float)) else None

    start_balance = _num("C14")
    total_paid = sum(v for r in range(25, 701) if (v := _num(f"C{r}")) is not None)
    total_interest = sum(v for r in range(25, 701) if (v := _num(f"E{r}")) is not None)
    expected_years = payoff_month / 12.0 if payoff_month else None

    def _close(cell, expected, tol):
        got = _num(cell)
        return got is not None and expected is not None and abs(got - expected) <= tol

    j25_value_ok = _close("J25", expected_years, 0.05)
    j26_value_ok = _close("J26", total_paid, 0.5)
    # Total interest = total paid − starting balance (== sum of column E).
    j27_expected = (total_paid - start_balance) if start_balance is not None else None
    j27_value_ok = _close("J27", total_interest, 0.5) or (
        j27_expected is not None and _close("J27", j27_expected, 0.5)
    )

    j25 = _check_j25_years(ws_f, payoff_month, excel_row, value_ok=j25_value_ok)
    j26 = _check_j26_total_paid(ws_f, excel_row, value_ok=j26_value_ok)
    j27 = _check_j27_interest(ws_f, excel_row, value_ok=j27_value_ok)

    wb_f.close()
    wb_v.close()

    total = j25["points"] + j26["points"] + j27["points"]

    return {
        "J25": j25,
        "J26": j26,
        "J27": j27,
        "total_points": total,
        "comment": f"{j25['comment']} | {j26['comment']} | {j27['comment']}"
    }
