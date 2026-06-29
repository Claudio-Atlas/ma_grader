from utilities.formula_equiv import formulas_equivalent


def grade_five_year_income(ws):
    """
    Grades the 5-year projected income formula in K36.
    Full credit (3 pts) if formula matches one of the four acceptable normalized forms:
        =k35*(1+k34)
        =(1+k34)*k35
        =k35*(k34+1)
        =(k34+1)*k35
    Parentheses are preserved for structural accuracy.
    """

    result = {"points": 0, "comment": ""}
    cell = ws["K36"]
    formula = cell.value

    # Must be a formula
    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "K36 does not contain a formula."
        return result

    # --- Normalize but keep parentheses ---
    f = (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
    )

    # --- Acceptable normalized forms ---
    valid_forms = {
        "=k35*(1+k34)",
        "=(1+k34)*k35",
        "=k35*(k34+1)",
        "=(k34+1)*k35",
    }

    if f in valid_forms or formulas_equivalent(formula, "=K35*(1+K34)"):
        result["points"] = 3
        result["comment"] = "Projected 5-year income formula is correct."
    else:
        result["comment"] = (
            "Incorrect 5-year income formula. Expected one of: "
            "=K35*(1+K34), =(1+K34)*K35, =K35*(K34+1), or =(K34+1)*K35."
        )

    return result
