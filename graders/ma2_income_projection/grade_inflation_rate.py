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
        result["comment"] = "Your inflation rate (K34) isn't a formula yet. Compare projected to current CPI: =K33/C37-1."
        return result

    # Use the equivalence engine as the authority: it respects parentheses and
    # operator precedence, so it accepts =K33/C37-1 and =(K33-C37)/C37 but
    # correctly REJECTS =K33-C37/C37 (which Excel evaluates as K33 - 1, a
    # different value). Do NOT strip parentheses for matching — that was the
    # bug that let the wrong-precedence form through.
    if formulas_equivalent(formula, "=K33/C37-1"):
        result["points"] = 2
        result["comment"] = "Inflation Rate formula is correct."
    else:
        result["comment"] = (
            "Your inflation rate (K34) should be the percent change from current to projected CPI: "
            "=(K33-C37)/C37 or =K33/C37-1. Watch the parentheses: =K33-C37/C37 divides first."
        )

    return result
