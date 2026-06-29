import re

def normalize_formula(formula: str) -> str:
    """
    Normalize Excel formula string:
    - lowercase
    - remove spaces, $, and extra parentheses
    """
    if not formula:
        return ""
    f = formula.strip().lower().replace(" ", "").replace("$", "")
    # remove outer parentheses if present
    if f.startswith("=(") and f.endswith(")"):
        f = f[1:]
    return f


def grade_slope_formula(ws):
    """
    Checks if H19 contains the correct slope formula =SLOPE(C29:C37,B29:B37).
    Returns dict with points (0–2) and comment.
    """
    result = {"points": 0, "comment": ""}
    cell = ws["H19"]
    formula = cell.value

    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "H19 does not contain a formula."
        return result

    normalized = normalize_formula(formula)
    expected = "=slope(c29:c37,b29:b37)"

    if normalized == expected:
        result["points"] = 2
        result["comment"] = "Slope formula is correct."
    elif normalized.startswith("=slope("):
        result["points"] = 1
        result["comment"] = "Slope formula present but range or arguments incorrect."
    else:
        result["comment"] = "Incorrect or missing slope formula."

    return result


def grade_intercept_formula(ws):
    """
    Checks if H20 contains the correct intercept formula =INTERCEPT(C29:C37,B29:B37).
    Returns dict with points (0–2) and comment.
    """
    result = {"points": 0, "comment": ""}
    cell = ws["H20"]
    formula = cell.value

    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "H20 does not contain a formula."
        return result

    normalized = normalize_formula(formula)
    expected = "=intercept(c29:c37,b29:b37)"

    if normalized == expected:
        result["points"] = 2
        result["comment"] = "Intercept formula is correct."
    elif normalized.startswith("=intercept("):
        result["points"] = 1
        result["comment"] = "Intercept formula present but range or arguments incorrect."
    else:
        result["comment"] = "Incorrect or missing intercept formula."

    return result
