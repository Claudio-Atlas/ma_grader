from openpyxl import load_workbook

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _normalize_formula(formula: str) -> str:
    if not isinstance(formula, str):
        return ""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
    )


def _read_cc_parameters(ws_values):
    """
    Reads the student-entered parameters on the Credit Cards tab (data_only sheet).

    Cells:
        C13 - APR
        C14 - Starting balance
        C15 - Payments per year
        C17 - Percent of current balance
        C18 - Fixed minimum payment

    Returns a dictionary with normalized numerical values.
    """

    apr_raw = ws_values["C13"].value
    start_balance = ws_values["C14"].value
    pay_per_year = ws_values["C15"].value
    pct_raw = ws_values["C17"].value
    fixed_min = ws_values["C18"].value

    # Normalize APR → decimal
    apr = float(apr_raw)
    if apr > 1:
        apr = apr / 100.0

    # Normalize percent → decimal
    min_percent = float(pct_raw)
    if min_percent > 1:
        min_percent = min_percent / 100.0

    return {
        "apr": apr,
        "start_balance": float(start_balance),
        "payments_per_year": int(pay_per_year),
        "min_percent": min_percent,
        "min_fixed": float(fixed_min),
    }


def _simulate_payoff(params, max_months=1000):
    """
    Simulates credit card amortization using same rules as Excel.
    Returns:
        payoff_month (int)
        last_start_balance (float)
    """

    balance = params["start_balance"]
    apr = params["apr"]
    n = params["payments_per_year"]
    min_pct = params["min_percent"]
    min_fixed = params["min_fixed"]

    month = 0
    last_start_balance = balance

    while month < max_months and balance > 0.005:
        month += 1
        last_start_balance = balance

        percent_component = min_pct * balance
        scheduled_payment = max(min_fixed, percent_component)
        payment = min(balance, scheduled_payment)

        balance_after_payment = balance - payment
        interest = balance_after_payment * (apr / n)
        balance = balance_after_payment + interest

    return month, last_start_balance


# ------------------------------------------------------------
# Formula / propagation checks
# ------------------------------------------------------------

def _check_base_formulas(ws_formulas):
    """
    Checks:
        - C25 payment formula
        - D25 balance-after-payment formula
        - E25 interest formula
        - B26 new balance formula
        - Propagation pattern rows 26–30

    Returns {points, comment}
    Max 4 points.
    """

    points = 0
    comments = []

    # Row 25 formulas
    c25_f = _normalize_formula(ws_formulas["C25"].value)
    d25_f = _normalize_formula(ws_formulas["D25"].value)
    e25_f = _normalize_formula(ws_formulas["E25"].value)
    b26_f = _normalize_formula(ws_formulas["B26"].value)

    # C25 MIN/MAX structure
    if (
        "min(" in c25_f and
        "max(" in c25_f and
        "c18" in c25_f and
        "c17" in c25_f and
        "b25" in c25_f
    ):
        points += 3
        comments.append("C25 payment formula structure is correct.")
    else:
        comments.append("C25 formula missing MIN/MAX structure or required references.")

    # D25 = B25 - C25
    if "b25" in d25_f and "c25" in d25_f and "-" in d25_f:
        points += 3
        comments.append("D25 formula is correct.")
    else:
        comments.append("D25 should subtract C25 from B25.")

    # E25 = D25 * (C13/C15).  Payments-per-year may be C15 or the literal 12.
    if (
        "d25" in e25_f and
        "c13" in e25_f and
        ("c15" in e25_f or "/12" in e25_f) and
        "/" in e25_f and
        "*" in e25_f
    ):
        points += 3
        comments.append("E25 interest formula is correct.")
    else:
        comments.append("E25 should be D25 * (C13/C15).")

    # B26 = D25 + E25
    if "d25" in b26_f and "e25" in b26_f and "+" in b26_f:
        points += 3
        comments.append("B26 formula structure is correct.")
    else:
        comments.append("B26 should be D25 + E25.")

    # Check propagation rows 26–30
    bad_rows = []

    for row in range(26, 31):
        c_formula = _normalize_formula(ws_formulas[f"C{row}"].value)
        d_formula = _normalize_formula(ws_formulas[f"D{row}"].value)
        e_formula = _normalize_formula(ws_formulas[f"E{row}"].value)

        # C-row: MIN(Brow, MAX(C18, C17 * Brow))
        if not (
            "min(" in c_formula and
            "max(" in c_formula and
            f"b{row}" in c_formula and
            "c18" in c_formula and
            "c17" in c_formula
        ):
            bad_rows.append(f"C{row}")

        # D-row: Brow - Crow
        if not (f"b{row}" in d_formula and f"c{row}" in d_formula and "-" in d_formula):
            bad_rows.append(f"D{row}")

        # E-row: Drow * (C13/C15).  Payments-per-year may be C15 or literal 12.
        if not (
            f"d{row}" in e_formula and
            "c13" in e_formula and
            ("c15" in e_formula or "/12" in e_formula) and
            "/" in e_formula and
            "*" in e_formula
        ):
            bad_rows.append(f"E{row}")

    if bad_rows:
        comments.append("Possible propagation issues in rows: " + ", ".join(sorted(set(bad_rows))))

    return {
        "points": points,
        "comment": " ".join(comments)
    }


# ------------------------------------------------------------
# Final payoff row check
# ------------------------------------------------------------

def _check_payoff_row(ws_formulas, ws_values, payoff_month, last_start_balance, params):
    """
    Checks:
        - Column A month number
        - Column B remaining balance
        - Column C payment formula + numeric value
        - Column D = 0 final balance
        - Column E = 0 interest

    Returns {points, comment, payoff_month, excel_row}
    """

    points = 0
    comments = []
    tol = 0.05

    excel_row = payoff_month + 24

    # A: month number
    a_val = ws_values[f"A{excel_row}"].value
    if a_val == payoff_month:
        points += 1
        comments.append(f"A{excel_row} month number is correct.")
    else:
        comments.append(f"A{excel_row} should be {payoff_month}, found {a_val}.")

    # B: remaining balance
    b_val = ws_values[f"B{excel_row}"].value
    if b_val is None:
        comments.append(f"B{excel_row} is blank.")
    else:
        # Should match simulated last_start_balance
        if abs(b_val - last_start_balance) <= tol:
            points += 3
            comments.append(f"B{excel_row} balance matches expected final balance.")
        else:
            comments.append(
                f"B{excel_row} expected ≈ {last_start_balance:.2f}, found {b_val:.2f}."
            )

    # C: payment formula must still be MIN/MAX
    c_formula = _normalize_formula(ws_formulas[f"C{excel_row}"].value)
    c_val = ws_values[f"C{excel_row}"].value

    if (
        "min(" in c_formula and
        "max(" in c_formula and
        f"b{excel_row}" in c_formula and
        "c17" in c_formula and
        "c18" in c_formula
    ):
        # Payment should equal remaining balance
        if c_val is not None and b_val is not None and abs(c_val - b_val) <= tol:
            points += 3
            comments.append(f"C{excel_row} payment matches remaining balance.")
        else:
            comments.append(
                f"C{excel_row} payment should equal B{excel_row}."
            )
    else:
        comments.append(f"C{excel_row} formula incorrectly modified or missing MIN/MAX.")

    # D: must be zero
    d_val = ws_values[f"D{excel_row}"].value
    if d_val is not None and abs(d_val) <= tol:
        points += 3
        comments.append(f"D{excel_row} balance after payment is zero.")
    else:
        comments.append(f"D{excel_row} should be 0; found {d_val}.")

    # E: must be zero
    e_val = ws_values[f"E{excel_row}"].value
    if e_val is not None and abs(e_val) <= tol:
        points += 3
        comments.append(f"E{excel_row} interest is zero.")
    else:
        comments.append(f"E{excel_row} should be 0; found {e_val}.")

    # Cap at 4 points max
    points = min(points, 12)

    return {
        "points": points,
        "comment": " ".join(comments),
        "payoff_month": payoff_month,
        "excel_row": excel_row,
    }


# ------------------------------------------------------------
# Public wrapper
# ------------------------------------------------------------

def grade_credit_card_amortization(student_file_path):
    """
    Grades the amortization table in the 'Credit Cards' tab.
    Returns:
        {
            "formula_structure": {...},
            "payoff_row": {...},
            "total_points": int
        }
    """

    wb_f = load_workbook(student_file_path, data_only=False)
    wb_v = load_workbook(student_file_path, data_only=True)

    ws_f = wb_f["Credit Cards"]
    ws_v = wb_v["Credit Cards"]

    # Extract parameters
    params = _read_cc_parameters(ws_v)

    # Simulate payoff
    payoff_month, last_start_balance = _simulate_payoff(params)

    # Check formulas & structure
    base = _check_base_formulas(ws_f)

    # Check final payoff row
    payoff = _check_payoff_row(ws_f, ws_v, payoff_month, last_start_balance, params)

    wb_f.close()
    wb_v.close()

    total_points = base["points"] + payoff["points"]

    return {
        "formula_structure": base,
        "payoff_row": payoff,
        "total_points": total_points,
    }
