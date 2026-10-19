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
        result["comment"] = (
            "Your slope (H19) is a typed number instead of a formula. Use "
            "=SLOPE(C29:C37, B29:B37) so it updates with your CPI table."
            if formula not in (None, "") else
            "Your slope (H19) is empty. Enter =SLOPE(C29:C37, B29:B37)."
        )
        return result

    normalized = normalize_formula(formula)
    expected = "=slope(c29:c37,b29:b37)"

    if normalized == expected:
        result["points"] = 2
        result["comment"] = "Slope formula is correct."
    elif normalized.startswith("=slope("):
        result["points"] = 1
        result["comment"] = (
            "Your SLOPE formula (H19) is close, but the ranges aren't quite right. It "
            "should use the CPI values first, then the years: =SLOPE(C29:C37, B29:B37)."
        )
    else:
        result["comment"] = "Your slope (H19) should use the SLOPE function: =SLOPE(C29:C37, B29:B37)."

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
        result["comment"] = (
            "Your intercept (H20) is a typed number instead of a formula. Use "
            "=INTERCEPT(C29:C37, B29:B37) so it updates with your CPI table."
            if formula not in (None, "") else
            "Your intercept (H20) is empty. Enter =INTERCEPT(C29:C37, B29:B37)."
        )
        return result

    normalized = normalize_formula(formula)
    expected = "=intercept(c29:c37,b29:b37)"

    if normalized == expected:
        result["points"] = 2
        result["comment"] = "Intercept formula is correct."
    elif normalized.startswith("=intercept("):
        result["points"] = 1
        result["comment"] = (
            "Your INTERCEPT formula (H20) is close, but the ranges aren't quite right. It "
            "should use the CPI values first, then the years: =INTERCEPT(C29:C37, B29:B37)."
        )
    else:
        result["comment"] = "Your intercept (H20) should use the INTERCEPT function: =INTERCEPT(C29:C37, B29:B37)."

    return result
