from openpyxl import load_workbook

def normalize_formula(formula: str) -> str:
    """Normalize Excel formula string for consistent comparison."""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )

def compute_manual_pmt(P, r, n, t):
    """Compute expected PMT value manually, matching Excel logic."""
    try:
        monthly_rate = r / n
        payment = (monthly_rate * P) / (1 - (1 + monthly_rate) ** (-n * t))
        return payment
    except Exception:
        return None


# -------------------------------------------------------------------------
# C29 – Monthly Payment (Unsubsidized)
# -------------------------------------------------------------------------
def _check_c29_pmt_formula(ws_formulas, ws_values):
    """
    Checks the unsubsidized loan PMT formula in C29.
    Worth 4 points total:
        - 3 pts for correct formula structure (no PMT use)
        - 1 pt for correct computed value (matches within ±0.05)
    """
    result = {"points": 0, "comment": ""}
    formula = ws_formulas["C29"].value

    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "C29 must contain a formula for unsubsidized monthly payment (no PMT function)."
        return result

    f = normalize_formula(formula)

    if "pmt(" in f:
        result["comment"] = "C29 uses the built-in PMT function, which is not allowed."
        return result

    required_refs = ["c26", "b27", "b28"]
    missing = [r for r in required_refs if r not in f]
    if missing:
        result["comment"] = f"C29 formula missing required references: {', '.join(missing)}."
        return result

    # The interest rate lives in both B23 and B14, so either reference is valid.
    if "b23" not in f and "b14" not in f:
        result["comment"] = "C29 formula must reference the interest rate (B23 or B14)."
        return result

    if "/" not in f or "^-" not in f:
        result["comment"] = "C29 formula missing division or negative exponent structure."
        return result

    points = 3
    comments = ["Formula structure is correct."]

    try:
        P = ws_values["C26"].value
        r = ws_values["B23"].value
        n = ws_values["B27"].value
        t = ws_values["B28"].value
        student_val = ws_values["C29"].value

        if None in (P, r, n, t, student_val):
            comments.append("Could not verify numeric value — one or more inputs missing.")
        else:
            expected_val = compute_manual_pmt(P, r, n, t)
            if expected_val is not None and abs(student_val - expected_val) <= 0.05:
                points += 1
                comments.append(f"Calculated payment matches expected value ({expected_val:.2f}).")
            else:
                comments.append(
                    f"Value appears incorrect. Expected about {expected_val:.2f}, found {student_val:.2f}."
                )
    except Exception as e:
        comments.append(f"Error verifying computed value: {e}")

    result["points"] = points
    result["comment"] = " ".join(comments)
    return result


# -------------------------------------------------------------------------
# C30 – Total Amount Paid
# -------------------------------------------------------------------------
def _check_c30_total_paid(ws_formulas, ws_values):
    """
    Checks the total amount paid formula for the unsubsidized loan in C30.
    Worth 2 points total:
        - 1 pt for correct structure (C29*B27*B28)
        - 1 pt for correct computed value (within ±0.05)
    """
    result = {"points": 0, "comment": ""}
    formula = ws_formulas["C30"].value

    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "C30 must contain a formula for total amount paid."
        return result

    f = normalize_formula(formula)
    required_refs = ["c29", "b27", "b28"]
    missing = [r for r in required_refs if r not in f]
    if missing:
        result["comment"] = f"C30 formula missing required references: {', '.join(missing)}."
        return result

    if "*" not in f:
        result["comment"] = "C30 formula must multiply the payment, payments per year, and years."
        return result

    points = 1
    comments = ["Formula structure is correct."]

    try:
        pmt = ws_values["C29"].value
        n = ws_values["B27"].value
        t = ws_values["B28"].value
        student_val = ws_values["C30"].value

        if None in (pmt, n, t, student_val):
            comments.append("Could not verify numeric value — one or more inputs missing.")
        else:
            expected_val = pmt * n * t
            if abs(student_val - expected_val) <= 0.05:
                points += 1
                comments.append(f"Numeric result matches expected total ({expected_val:.2f}).")
            else:
                comments.append(
                    f"Incorrect total paid. Expected about {expected_val:.2f}, found {student_val:.2f}."
                )
    except Exception as e:
        comments.append(f"Error verifying numeric value: {e}")

    result["points"] = points
    result["comment"] = " ".join(comments)
    return result


# -------------------------------------------------------------------------
# C31 – Interest Paid
# -------------------------------------------------------------------------
def _check_c31_interest_paid(ws_formulas):
    """
    Checks the interest paid formula in C31.
    Worth 2 points total:
        - 2 pts for exact formula =C30-B22
    """
    result = {"points": 0, "comment": ""}
    formula = ws_formulas["C31"].value

    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "C31 must contain a formula for interest paid."
        return result

    f = formula.strip().lower().replace(" ", "").replace("$", "")
    valid_form = "=c30-b22"

    if f == valid_form:
        result["points"] = 2
        result["comment"] = "Interest paid formula is correct."
    else:
        result["comment"] = "Incorrect interest formula. Expected =C30-B22."

    return result


# -------------------------------------------------------------------------
# Wrapper Function – Unsubsidized Loan Section
# -------------------------------------------------------------------------
def grade_unsubsidized_payment_section(student_file_path):
    """
    Grades the unsubsidized payment section (C29–C31).
    Loads both formula and value workbooks.

    Returns a dictionary with points and comments for each cell,
    and a total score for the section (8 points possible).
    """
    wb_formulas = load_workbook(student_file_path, data_only=False)
    wb_values = load_workbook(student_file_path, data_only=True)

    ws_formulas = wb_formulas["Student Loans"]
    ws_values = wb_values["Student Loans"]

    c29 = _check_c29_pmt_formula(ws_formulas, ws_values)
    c30 = _check_c30_total_paid(ws_formulas, ws_values)
    c31 = _check_c31_interest_paid(ws_formulas)

    results = {
        "C29": c29,
        "C30": c30,
        "C31": c31,
        "total_points": c29["points"] + c30["points"] + c31["points"],
        "comment": " | ".join([c29["comment"], c30["comment"], c31["comment"]]),
    }

    wb_formulas.close()
    wb_values.close()

    return results
