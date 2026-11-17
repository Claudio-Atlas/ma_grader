from utilities.formula_equiv import cell_number, formulas_equivalent


def grade_current_income_reference(ws, ws_data=None):
    """
    Grades the Current Income reference in K35.
    Full credit (1 pt) if =B11 (normalized).
    Half credit (0.5 pt) if a hard-coded numeric value equal to the value in B11.

    B11 is itself a formula, so its number comes from ws_data (the tab loaded
    data_only); the formulas sheet only has the formula text.
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
            result["comment"] = "Your current income (K35) should point straight at your income in B11: =B11."
            return result

    # --- Case 2: Hard-coded numeric value (partial credit) ---
    current_income = cell_number(ws, ws_data, "B11")
    if formula in (None, ""):
        result["comment"] = "Your current income (K35) is missing. Enter =B11 to bring it forward."
    elif isinstance(formula, (int, float)) and current_income is not None \
            and round(formula, 2) == round(current_income, 2):
        result["points"] = 0.5
        result["comment"] = "Your current income (K35) is typed in instead of referencing B11. Use =B11 so it updates if B11 changes."
    else:
        result["comment"] = "Your current income (K35) should point straight at your income in B11: =B11."

    return result
