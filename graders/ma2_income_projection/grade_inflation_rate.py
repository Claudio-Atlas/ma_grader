from utilities.formula_equiv import formulas_equivalent


def grade_inflation_rate(ws):
    """
    Grades the 5-year Inflation Rate formula in K34.
    Full credit (2 pts) if formula matches one of the acceptable normalized forms:
        =k33/c37-1
        =(k33-c37)/c37
    Cosmetic differences (spaces, $, parentheses) are ignored.
    """

    result = {"points": 0, "comment": ""}
    cell = ws["K34"]
    formula = cell.value

    # Must be a formula
    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "K34 does not contain a formula."
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
        "=k33/c37-1",
        "=k33-c37/c37",
    }

    if f in valid_forms or formulas_equivalent(formula, "=K33/C37-1"):
        result["points"] = 2
        result["comment"] = "Inflation Rate formula is correct."
    else:
        result["comment"] = (
            "Incorrect Inflation Rate formula. Expected either =K33/C37-1 or (K33-C37)/C37."
        )

    return result
