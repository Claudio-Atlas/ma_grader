"""
check_empirical_rule.py — Validates empirical rule calculations in G36:G37

Grading: 6 points total (3 pts each)

Expected formulas:
    G36 (Lower Bound): =I18-I20  (Mean - StdDev)
    G37 (Upper Bound): =I18+I20  (Mean + StdDev)

Partial Credit (50%):
    - Has the right structure (cell - cell or cell + cell) but wrong cell references
    - Shows understanding of Mean ± StdDev concept even if referencing wrong rows/columns
"""

import re
from typing import Tuple, List, Union
from openpyxl.worksheet.worksheet import Worksheet


# Credit multipliers (of the 3 points per bound cell)
CREDIT_FULL = 1.0            # 3/3 — mean & stdev both of the differences
CREDIT_NEAR_MISS = 2.0 / 3.0  # 2/3 — right structure + correct diff stdev, wrong mean
CREDIT_STRUCT = 0.5         # 1.5/3 — right shape only (wrong refs or wrong operation)
CREDIT_WRONG_REFS = CREDIT_STRUCT  # backwards-compat alias
CREDIT_NONE = 0.0


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


# The empirical-rule bounds describe the distribution of the DIFFERENCES, so both
# the mean and the standard deviation must be computed on the differences:
#   lower = mean(diff) - stdev(diff)     upper = mean(diff) + stdev(diff)
# Correct "mean of differences" forms:  I18, AVERAGE(D14:D63), or H18-G18.
# Correct "stdev of differences" forms: I20, STDEV/STDEV.S/STDEV.P(D14:D63).
_DIFF_RANGE = r'D14:D63'
_STDEV_DIFF_RE = re.compile(r'STDEV(\.[SP])?\(' + _DIFF_RANGE + r'\)')
_STDEV_WRONG_RE = re.compile(r'STDEV(\.[SP])?\([BC]14:[BC]63\)')
_CELL_OP_CELL_RE = re.compile(r'^\(?[A-Z]\d+\)?[+\-]\(?[A-Z]\d+\)?$')


def _sign_before(body: str, idx: int):
    """Return the +/- operator immediately preceding position `idx` (skipping any
    opening parentheses), or None."""
    j = idx - 1
    while j >= 0 and body[j] == '(':
        j -= 1
    if j >= 0 and body[j] in '+-':
        return body[j]
    return None


def _bound_credit(formula: str, is_lower: bool) -> float:
    """Grade an empirical-rule bound formula. Returns a credit multiplier:
    1.0 (full), 2/3 (near-miss: wrong mean), 0.5 (structure only), or 0.0."""
    if not isinstance(formula, str) or not formula.startswith("="):
        return CREDIT_NONE

    body = _normalize_formula(formula).replace("$", "")[1:]  # drop '=' and $

    # --- stdev term ---
    m_stdev = _STDEV_DIFF_RE.search(body)
    stdev_diff = bool(m_stdev) or ("I20" in body)
    stdev_wrong = bool(_STDEV_WRONG_RE.search(body)) or "G20" in body or "H20" in body

    # --- mean term ---
    mean_diff = ("I18" in body) or ("AVERAGE(D14:D63)" in body) or ("H18-G18" in body)
    mean_wrong = ("G18" in body) or ("H18" in body) \
        or ("AVERAGE(B14:B63)" in body) or ("AVERAGE(C14:C63)" in body)
    if "H18-G18" in body:
        # Here H18/G18 form the difference-mean expression, not a wrong reference.
        mean_wrong = False

    # --- operation/sign attached to the stdev term ---
    if m_stdev:
        sign = _sign_before(body, m_stdev.start())
    elif "I20" in body:
        sign = _sign_before(body, body.find("I20"))
    else:
        sign = None
    want = '-' if is_lower else '+'
    sign_ok = (sign == want)

    # --- classify ---
    # Full: mean & stdev both of the differences, correct sign.
    if mean_diff and stdev_diff and sign_ok:
        return CREDIT_FULL
    # Right pieces but wrong operation (e.g. added in the lower cell): structure.
    if mean_diff and stdev_diff and not sign_ok:
        return CREDIT_STRUCT
    # Near-miss: correct difference-stdev and correct sign, but the mean points at
    # the wrong dataset (Before/After) — bound is numerically wrong.
    if stdev_diff and sign_ok and mean_wrong and not mean_diff:
        return CREDIT_NEAR_MISS
    # Structure only: a mean-like term and a stdev-like term with the right sign,
    # but they reference the wrong statistics.
    mean_any = mean_diff or mean_wrong
    stdev_any = stdev_diff or stdev_wrong
    if mean_any and stdev_any and sign_ok:
        return CREDIT_STRUCT
    # Structure only: a plain =CELL±CELL shape (right idea, wrong references).
    if _CELL_OP_CELL_RE.match(body):
        return CREDIT_STRUCT
    return CREDIT_NONE


def _check_lower_bound_formula(formula: str) -> float:
    """Check Mean - StdDev bound. Returns credit multiplier."""
    return _bound_credit(formula, is_lower=True)


def _check_upper_bound_formula(formula: str) -> float:
    """Check Mean + StdDev bound. Returns credit multiplier."""
    return _bound_credit(formula, is_lower=False)


def check_empirical_rule(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check empirical rule formulas in G36 (lower) and G37 (upper).
    
    Args:
        sheet: Analysis worksheet
        
    Returns:
        Tuple of (score, feedback_list)
        
    Partial Credit:
        - Full credit (100%): Correct formula =I18±I20
        - Partial credit (50%): Right structure (cell±cell) but wrong references
        - No credit: Missing, not a formula, or wrong structure
    """
    feedback = []
    total_score = 0.0
    points_per_cell = 3.0
    full_credit_count = 0
    partial_credit_count = 0
    
    bounds = [
        ("G36", _check_lower_bound_formula, "Mean - StdDev",
         "EMPIRICAL_LOWER_OK", "EMPIRICAL_LOWER_PARTIAL", "EMPIRICAL_LOWER_WRONG", "EMPIRICAL_LOWER_MISSING"),
        ("G37", _check_upper_bound_formula, "Mean + StdDev",
         "EMPIRICAL_UPPER_OK", "EMPIRICAL_UPPER_PARTIAL", "EMPIRICAL_UPPER_WRONG", "EMPIRICAL_UPPER_MISSING"),
    ]

    for cell_ref, check_func, shape, ok_code, partial_code, wrong_code, missing_code in bounds:
        formula = sheet[cell_ref].value

        if formula is None or str(formula).strip() == "":
            feedback.append((missing_code, {"cell": cell_ref}))
            continue
        if not isinstance(formula, str) or not formula.startswith("="):
            feedback.append((wrong_code, {"cell": cell_ref}))
            continue

        credit = check_func(formula)

        if credit == CREDIT_FULL:
            total_score += points_per_cell
            full_credit_count += 1
            feedback.append((ok_code, {"cell": cell_ref}))
        elif credit == CREDIT_NEAR_MISS:
            # Right structure + correct stdev of the differences, but the mean
            # references the wrong dataset (Before/After) — bound is off-scale.
            total_score += points_per_cell * CREDIT_NEAR_MISS
            partial_credit_count += 1
            feedback.append((partial_code, {
                "cell": cell_ref,
                "reason": "wrong_mean",
                "hint": f"Correct structure ({shape}) and standard deviation of the "
                        "differences, but the mean should be the mean of the DIFFERENCES "
                        "(I18), not of the Before/After scores.",
                "found": formula
            }))
        elif credit == CREDIT_STRUCT:
            total_score += points_per_cell * CREDIT_STRUCT
            partial_credit_count += 1
            feedback.append((partial_code, {
                "cell": cell_ref,
                "reason": "structure_only",
                "hint": f"Right idea ({shape}) but should reference I18 (Mean of the "
                        "differences) and I20 (StdDev of the differences) with the correct sign.",
                "found": formula
            }))
        else:
            feedback.append((wrong_code, {"cell": cell_ref}))
    
    # Calculate score
    score = round(total_score, 2)
    
    # Summary feedback
    if full_credit_count == 2:
        feedback = [("EMPIRICAL_ALL_CORRECT", {})]
    elif full_credit_count == 0 and partial_credit_count == 0:
        feedback.insert(0, ("EMPIRICAL_NONE_CORRECT", {}))
    elif partial_credit_count > 0:
        feedback.insert(0, ("EMPIRICAL_PARTIAL_CREDIT", {
            "full_credit": full_credit_count,
            "partial_credit": partial_credit_count,
            "score": score,
            "max_score": 6.0
        }))
    else:
        feedback.insert(0, ("EMPIRICAL_PARTIAL", {"correct": full_credit_count}))
    
    return score, feedback
