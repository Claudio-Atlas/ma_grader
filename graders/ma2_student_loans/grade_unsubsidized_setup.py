import re

from utilities.formula_equiv import formulas_equivalent, equivalent_to_any


def normalize_formula(formula: str) -> str:
    """Normalize formula for consistent comparison."""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )

def _check_c24_constant(ws):
    """Checks that C24 contains a constant 4 (1 point)."""
    result = {"points": 0, "comment": ""}
    val = ws["C24"].value

    if val == 4:
        result["points"] = 1
        result["comment"] = "C24 correctly entered as 4 years in school."
    else:
        result["comment"] = f"C24 incorrect; expected constant 4, found {val}."
    return result


def _check_c25_interest_formula(ws):
    """Checks that C25 contains I = P*r*t (2 points)."""
    result = {"points": 0, "comment": ""}
    formula = ws["C25"].value

    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "C25 missing formula for simple interest (I=P*r*t)."
        return result

    f = normalize_formula(formula)
    # Allow any commutative order of B22, B23, C24 multiplied together
    valid_patterns = {
        "=b22*b23*c24",
        "=b22*c24*b23",
        "=b23*b22*c24",
        "=b23*c24*b22",
        "=c24*b22*b23",
        "=c24*b23*b22",
    }

    # B14 and B23 both hold the interest rate, so either reference is valid.
    if f in valid_patterns or equivalent_to_any(
        formula, ["=B22*B23*C24", "=B22*B14*C24"]
    ):
        result["points"] = 2
        result["comment"] = "C25 simple interest formula is correct."
    else:
        result["comment"] = (
            "C25 formula incorrect. Expected I = B22*B23*C24 or any order of those references."
        )

    return result


def _check_c26_new_principal(ws):
    """Checks that C26 adds interest to principal (2 points)."""
    result = {"points": 0, "comment": ""}
    formula = ws["C26"].value

    if not isinstance(formula, str) or not formula.startswith("="):
        result["comment"] = "C26 missing formula for new principal (P + I)."
        return result

    f = normalize_formula(formula)

    # Accept either sum form or expanded equivalent
    valid_forms = {
        "=c25+b22",
        "=b22+c25",
        "=b22*(1+b23*c24)",
        "=b22*(1+c24*b23)",
        "=b22*(1+b23*c24)",
        "=b22*(1+c24*b23)",
    }

    if f in valid_forms or equivalent_to_any(formula, ["=B22+C25", "=B22*(1+B23*C24)"]):
        result["points"] = 2
        result["comment"] = "C26 new principal formula is correct."
    else:
        result["comment"] = (
            "C26 formula incorrect. Expected =B22+C25, =C25+B22, "
            "or equivalent like =B22*(1+B23*C24)."
        )

    return result


def grade_unsubsidized_setup(ws):
    """
    Grades the unsubsidized loan setup section (C24:C26).
    Total = 5 points.
    """
    results = {}
    total = 0

    c24 = _check_c24_constant(ws)
    c25 = _check_c25_interest_formula(ws)
    c26 = _check_c26_new_principal(ws)

    results["C24"] = c24
    results["C25"] = c25
    results["C26"] = c26
    total = c24["points"] + c25["points"] + c26["points"]

    results["total_points"] = total
    results["comment"] = (
        f"C24: {c24['comment']} | C25: {c25['comment']} | C26: {c26['comment']}"
    )

    return results
