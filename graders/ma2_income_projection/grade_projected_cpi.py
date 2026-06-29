from utilities.formula_equiv import formulas_equivalent


def grade_projected_cpi(ws):
    """
    Grades the Projected CPI formula in K33.
    Full credit (3 pts) if formula matches one of the four acceptable normalized forms:
        =h19*k32+h20
        =k32*h19+h20
        =h20+h19*k32
        =h20+k32*h19
    All cosmetic differences (spaces, $, parentheses) are ignored.
    """

    result = {"points": 0, "comment": ""}
    cell = ws["K33"]
    formula = cell.value

    # Must be a formula
    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "K33 does not contain a formula."
        return result

    # --- Normalize formula ---
    f = (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )

    # --- Acceptable normalized options ---
    valid_forms = {
        "=h19*k32+h20",
        "=k32*h19+h20",
        "=h20+h19*k32",
        "=h20+k32*h19",
    }

    if f in valid_forms or formulas_equivalent(formula, "=H19*K32+H20"):
        result["points"] = 3
        result["comment"] = "Projected CPI formula is correct."
    else:
        result["comment"] = (
            "Incorrect Projected CPI formula. Expected one of the valid forms: "
            "=H19*K32+H20, =K32*H19+H20, =H20+H19*K32, or =H20+K32*H19."
        )

    return result
