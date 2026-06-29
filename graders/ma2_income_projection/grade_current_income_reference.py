from utilities.formula_equiv import formulas_equivalent


def grade_current_income_reference(ws):
    """
    Grades the Current Income reference in K35.
    Full credit (1 pt) if =B11 (normalized).
    Half credit (0.5 pt) if a hard-coded numeric value equal to the value in B11.
    """
    result = {"points": 0, "comment": ""}
    cell = ws["K35"]
    formula = cell.value

    # --- Case 1: Proper cell reference formula ---
    if isinstance(formula, str) and formula.startswith("="):
        f = (
            formula.strip()
            .lower()
            .replace(" ", "")
            .replace("$", "")
            .replace("(", "")
            .replace(")", "")
        )

        if f == "=b11" or formulas_equivalent(formula, "=B11"):
            result["points"] = 1
            result["comment"] = "Correctly references current income (B11)."
            return result
        else:
            result["comment"] = "Incorrect reference; should directly reference B11."
            return result

    # --- Case 2: Hard-coded numeric value (partial credit) ---
    try:
        current_income = ws["B11"].value
        if isinstance(formula, (int, float)) and round(formula, 2) == round(current_income, 2):
            result["points"] = 0.5
            result["comment"] = "Hard-coded current income value instead of referencing B11."
        else:
            result["comment"] = "Incorrect or missing reference to current income."
    except Exception as e:
        result["comment"] = f"Error grading current income reference: {e}"

    return result
