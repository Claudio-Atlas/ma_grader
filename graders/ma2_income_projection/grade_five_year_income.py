from utilities.formula_equiv import formulas_equivalent, equivalent_to_any


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

    # K35 is defined as =B11 (current income), so =B11*(1+K34) is an equivalent
    # way to write =K35*(1+K34) — accept either reference.
    if f in valid_forms or equivalent_to_any(formula, ["=K35*(1+K34)", "=B11*(1+K34)"]):
        result["points"] = 3
        result["comment"] = "Projected 5-year income formula is correct."
    else:
        result["comment"] = (
            "Incorrect 5-year income formula. Expected =K35*(1+K34) "
            "(or =B11*(1+K34)) or an equivalent form."
        )

    return result
