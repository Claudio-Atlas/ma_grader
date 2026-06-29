from utilities.formula_equiv import formulas_equivalent


def grade_monthly_income(ws):
    """
    Grades the Projected Monthly Income formula in K37.
    Full credit (2 pts) if formula matches any of these (normalized):
        =k36/12
        =k36*1/12
    Parentheses are ignored.
    """

    result = {"points": 0, "comment": ""}
    cell = ws["K37"]
    formula = cell.value

    # Must be a formula
    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "K37 does not contain a formula."
        return result

    # --- Normalize ---
    f = (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )

    # --- Acceptable normalized forms ---
    valid_forms = {
        "=k36/12",
        "=k36*1/12",
    }

    if f in valid_forms or formulas_equivalent(formula, "=K36/12"):
        result["points"] = 2
        result["comment"] = "Projected monthly income formula is correct."
    else:
        result["comment"] = (
            "Incorrect monthly income formula. Expected =K36/12 or =K36*(1/12)."
        )

    return result
