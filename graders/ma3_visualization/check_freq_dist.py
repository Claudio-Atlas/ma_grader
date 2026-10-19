"""
check_freq_dist.py — Validates frequency distribution table formulas

Grading:
    Lower/Upper Limits (D28:E38): 12 points (6 pts each column)
    Title/Freq/RelFreq (F28:H38): 18 points (6 pts each column)

Cell layout (rows 28-38):
    D: Lower Limit
    E: Upper Limit
    F: Title of Bin (midpoint)
    G: Frequency (COUNTIF/COUNTIFS/FREQUENCY)
    H: Relative Frequency (freq/total)
"""

import re
from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _normalize_formula(formula: str) -> str:
    """Normalize formula for comparison."""
    if not formula:
        return ""
    return formula.replace(" ", "").upper()


def _check_lower_limit_formula(formula: str, row: int) -> bool:
    """
    Check if lower limit formula is correct.

    Row 28: Should equal E22 (bin min) or E22-0.1
    Rows 29+: Should equal previous upper limit (E{row-1})
    """
    if not formula or not formula.startswith("="):
        return False

    # Strip $ so absolute/mixed references (=$E$22, =E$22) match too.
    normalized = _normalize_formula(formula).replace("$", "")

    if row == 28:
        # First row - should reference E22 (bin min)
        if "E22" in normalized:
            return True
    else:
        # Subsequent rows - should reference previous upper limit
        prev_row = row - 1
        if f"E{prev_row}" in normalized:
            return True

    return False


def _check_upper_limit_formula(formula: str, row: int) -> bool:
    """
    Check if upper limit formula is correct.

    Should equal lower limit + bin width
    Pattern: =D{row}+$E$24 or =D{row}+E24 (any mix of $ signs)
    """
    if not formula or not formula.startswith("="):
        return False

    # Strip $ so absolute/mixed references (=D28+E$24, =D28+$E$24) all match.
    normalized = _normalize_formula(formula).replace("$", "")

    # Should reference D{row} and E24 (bin width) with addition
    if f"D{row}" in normalized and "E24" in normalized and "+" in normalized:
        return True

    return False


def _check_title_formula(formula: str, row: int) -> bool:
    """
    Check if title of bin formula calculates midpoint.
    
    Expected: =(D{row}+E{row})/2
    """
    if not formula or not formula.startswith("="):
        return False
    
    normalized = _normalize_formula(formula)

    # Remove dollar signs for easier matching
    normalized_no_dollars = normalized.replace("$", "")

    # Accept AVERAGE of the two limits, e.g. =AVERAGE(D28:E28) — same midpoint.
    if f"AVERAGE(D{row}:E{row})" in normalized_no_dollars:
        return True
    if f"AVERAGE(D{row},E{row})" in normalized_no_dollars:
        return True

    # Should have D{row}, E{row}, addition, and division by 2
    if f"D{row}" in normalized_no_dollars and f"E{row}" in normalized_no_dollars:
        if "+" in normalized and "/2" in normalized:
            return True
        if "+" in normalized and "2" in normalized:
            return True

    return False


# The 50 difference values. Absolute and relative spellings are equivalent
# once "$" is stripped, but a RELATIVE range dragged down the column shifts
# (B12:B61 -> B13:B62), which no longer matches — exactly the mistake to catch.
_DATA = r"(?:B12:B61|B:B|(?:'?ANALYSIS'?!)?D14:D63)"


def _crit(limit: str, ops: str) -> str:
    """A COUNTIF(S) criterion comparing against a limit cell/range, e.g.
    ">="&D28 or "<"&E28:E38."""
    return rf'"(?:{ops})"&{limit}(?![0-9])'


def _check_frequency_formula(formula: str, row: int = None, spill: bool = False) -> bool:
    """Is this a correct count of the data values in bin `row`?

    Accepted (operators may be > or >= on the lower limit, < or <= on the upper):
        =COUNTIFS(B12:B61,">="&D28, B12:B61,"<"&E28)
        =COUNTIF(B12:B61,">="&D28) - COUNTIF(B12:B61,">"&E28)   (and the "<" form)
        =SUMPRODUCT((B12:B61>=D28)*(B12:B61<E28))
        =FREQUENCY(B12:B61, E28:E38)                             (spill)
    The criteria must be comparisons: =COUNTIFS(B12:B61,D28:D38,B12:B61,E28:E38)
    only counts values EQUAL to a limit, so it's wrong.
    """
    if not formula or not formula.startswith("="):
        return False
    f = _normalize_formula(formula).replace("$", "")

    if spill:
        lo, hi = r"D2[0-9]:D3[0-9]", r"E2[0-9]:E3[0-9]"
    else:
        lo, hi = f"D{row}", f"E{row}"

    if "FREQUENCY(" in f:
        return re.search(rf"FREQUENCY\({_DATA},E28:E3[78]\)", f) is not None

    if "COUNTIFS(" in f:
        has_data = len(re.findall(rf"COUNTIFS\({_DATA},|,{_DATA},", f)) >= 2
        return has_data and re.search(_crit(lo, ">=|>"), f) is not None \
            and re.search(_crit(hi, "<=|<"), f) is not None

    if "COUNTIF(" in f:
        parts = re.findall(rf"COUNTIF\({_DATA},([^)]*)\)", f)
        if len(parts) != 2 or "-" not in f:
            return False
        joined = ",".join(parts)
        above = re.search(_crit(lo, ">=|>"), joined) and re.search(_crit(hi, ">=|>"), joined)
        below = re.search(_crit(lo, "<=|<"), joined) and re.search(_crit(hi, "<=|<"), joined)
        return bool(above or below)

    if "SUMPRODUCT(" in f:
        return re.search(rf"{_DATA}(?:>=|>){lo}(?![0-9])", f) is not None \
            and re.search(rf"{_DATA}(?:<=|<){hi}(?![0-9])", f) is not None

    return False


# Fixed totals a relative frequency may divide by.
_TOTALS = (
    r"SUM\(G28:G38\)", r"\(SUM\(G28:G38\)\)",
    rf"COUNTA?\({_DATA}\)", rf"\(COUNTA?\({_DATA}\)\)",
    r"50", r"\(50\)",
)


def _check_relative_freq_formula(formula: str, row: int) -> bool:
    """Relative frequency = this row's frequency / the fixed total.

        =G28/SUM(G$28:G$38)   =G28/50   =G28/COUNT($B$12:$B$61)

    The total must stay put on every row. A relative SUM/COUNT range dragged
    down the column (=G29/SUM(G29:G39), =G29/COUNT(B14:B62)) divides by the
    wrong total, so only the exact fixed range is accepted.
    """
    if not formula or not formula.startswith("="):
        return False
    f = _normalize_formula(formula).replace("$", "")
    f = re.sub(r"^=ROUND\((.*),\d+\)$", r"=\1", f)  # allow a ROUND wrapper
    m = re.fullmatch(rf"=\(?G{row}\)?/(.+)", f)
    return m is not None and any(re.fullmatch(t, m.group(1)) for t in _TOTALS)


def _formula_text(cell_value) -> str:
    """Return the formula string for a normal OR array/spill formula, else ''.

    Excel 365 dynamic-array formulas are read by openpyxl as a normal string in
    the anchor cell; legacy CSE arrays come back as an ArrayFormula object with a
    .text attribute. Handle both.
    """
    text = getattr(cell_value, "text", None)
    if isinstance(text, str) and text.startswith("="):
        return text
    if isinstance(cell_value, str) and cell_value.startswith("="):
        return cell_value
    return ""


def _spans_bin_rows(normalized: str, col: str) -> bool:
    """True if the formula references column `col` as a multi-row range spanning
    the bin table (e.g. G28:G38, D28:D38, E28:E37).

    A single spill/array formula fills the whole column, so its anchor cell
    references a range like G28:G38 — whereas a per-row formula only references
    single cells (G28). Rows constrained to 20-39 so the data range (B12:B61)
    can't accidentally match.
    """
    return bool(re.search(rf'{col}\$?2[0-9]:\$?{col}\$?3[0-9]', normalized))


def _is_spill_frequency(anchor_value) -> bool:
    """Detect a single frequency formula (in G28) that fills the whole column:
    FREQUENCY(...), an ArrayFormula, or a dynamic COUNTIF(S)/SUMPRODUCT that
    references the bin-limit columns (D/E) as ranges."""
    text = _formula_text(anchor_value)
    if not text:
        return False
    normalized = _normalize_formula(text).replace("$", "")
    # FREQUENCY always returns an array over the bins.
    if "FREQUENCY(" in normalized:
        return True
    is_array_obj = type(anchor_value).__name__ == "ArrayFormula"
    has_count = any(f in normalized for f in ("COUNTIF(", "COUNTIFS(", "SUMPRODUCT("))
    # Legacy CSE array of a counting function.
    if is_array_obj and has_count:
        return True
    # Dynamic-array COUNTIFS referencing the limit columns as ranges, e.g.
    # =COUNTIFS(B12:B61,">"&D28:D38, B12:B61,"<"&E28:E38)
    if has_count and (_spans_bin_rows(normalized, "D") or _spans_bin_rows(normalized, "E")):
        return True
    return False


def _spill_frequency_ok(anchor_value) -> bool:
    """A whole-column frequency formula must also count correctly."""
    return _check_frequency_formula(_formula_text(anchor_value), spill=True)


def _is_spill_relfreq(anchor_value) -> bool:
    """Detect a single relative-frequency formula (in H28) that fills the whole
    column: e.g. =G28:G38/50, =G28:G38/SUM(...), or an ArrayFormula."""
    text = _formula_text(anchor_value)
    if not text:
        return False
    normalized = _normalize_formula(text).replace("$", "")
    if "/" not in normalized:
        return False
    # The NUMERATOR must be the frequency range (=G28:G38/..., =G28#/...);
    # a per-row =G28/SUM(G28:G38) only has the range in its denominator.
    if re.match(r"=(?:ROUND\()?\(?(?:G2[0-9]:G3[0-9]|G28#)", normalized):
        return True
    if type(anchor_value).__name__ == "ArrayFormula" and "G" in normalized:
        return True
    return False


def _spill_relfreq_ok(anchor_value) -> bool:
    """A whole-column relative frequency must divide by the fixed total,
    e.g. =G28:G38/SUM(G28:G38) or =G28#/50."""
    f = _normalize_formula(_formula_text(anchor_value)).replace("$", "")
    f = re.sub(r"^=ROUND\((.*),\d+\)$", r"=\1", f)
    m = re.fullmatch(r"=\(?(?:G28:G3[78]|G28#)\)?/(.+)", f)
    return m is not None and any(re.fullmatch(t, m.group(1)) for t in _TOTALS)


def check_freq_dist_limits(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check Lower Limit (D28:D38) and Upper Limit (E28:E38) formulas.
    
    Args:
        sheet: Visualization worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_lower = 0
    correct_upper = 0
    total_rows = 11  # Rows 28-38
    
    for row in range(28, 39):
        # Check Lower Limit
        cell_ref = f"D{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_LOWER_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("FREQ_LOWER_WRONG", {"cell": cell_ref}))
        elif _check_lower_limit_formula(formula, row):
            correct_lower += 1
        else:
            feedback.append(("FREQ_LOWER_WRONG", {"cell": cell_ref}))
        
        # Check Upper Limit
        cell_ref = f"E{row}"
        cell = sheet[cell_ref]
        formula = cell.value
        
        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_UPPER_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("FREQ_UPPER_WRONG", {"cell": cell_ref}))
        elif _check_upper_limit_formula(formula, row):
            correct_upper += 1
        else:
            feedback.append(("FREQ_UPPER_WRONG", {"cell": cell_ref}))
    
    # Calculate score (6 pts each column)
    lower_score = (correct_lower / total_rows) * 6.0
    upper_score = (correct_upper / total_rows) * 6.0
    total_score = round(lower_score + upper_score, 2)
    
    total_correct = correct_lower + correct_upper
    total_cells = total_rows * 2
    
    # Summary feedback
    if total_correct == total_cells:
        feedback = [("FREQ_LIMITS_ALL_CORRECT", {})]
    elif total_correct == 0:
        feedback.insert(0, ("FREQ_LIMITS_NONE_CORRECT", {}))
    else:
        feedback.insert(0, ("FREQ_LIMITS_PARTIAL", {"correct": total_correct, "total": total_cells}))
    
    return total_score, feedback


def check_freq_dist_values(sheet: Worksheet, values_sheet: Worksheet = None) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check Title of Bin (F), Frequency (G), and Relative Frequency (H) formulas.

    Args:
        sheet: Visualization worksheet (formulas)
        values_sheet: Visualization worksheet loaded data_only (calculated values),
                      used to verify the frequencies actually count every data
                      value (a strict `<` on the final bin with no buffer, or a
                      wrong boundary operator, silently drops values).

    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_title = 0
    correct_freq = 0
    correct_relfreq = 0
    total_rows = 11  # Rows 28-38

    # A single spill/array formula in the anchor cell (G28 for Frequency, H28 for
    # Relative Frequency) fills the whole column, so openpyxl only sees the
    # formula in the top cell. Detect that up front and credit all rows instead
    # of penalizing the (apparently blank) spill cells below.
    freq_is_spill = _is_spill_frequency(sheet["G28"].value)
    relfreq_is_spill = _is_spill_relfreq(sheet["H28"].value)

    if freq_is_spill and _spill_frequency_ok(sheet["G28"].value):
        correct_freq = total_rows
    elif freq_is_spill:
        feedback.append(("FREQ_COUNT_WRONG", {"cell": "G28"}))
    if relfreq_is_spill and _spill_relfreq_ok(sheet["H28"].value):
        correct_relfreq = total_rows
    elif relfreq_is_spill:
        feedback.append(("FREQ_REL_WRONG", {"cell": "H28"}))

    for row in range(28, 39):
        # Check Title of Bin (F column)
        cell_ref = f"F{row}"
        cell = sheet[cell_ref]
        formula = cell.value

        if formula is None or str(formula).strip() == "":
            feedback.append(("FREQ_TITLE_MISSING", {"cell": cell_ref}))
        elif not isinstance(formula, str) or not formula.startswith("="):
            feedback.append(("FREQ_TITLE_WRONG", {"cell": cell_ref}))
        elif _check_title_formula(formula, row):
            correct_title += 1
        else:
            feedback.append(("FREQ_TITLE_WRONG", {"cell": cell_ref}))

        # Check Frequency (G column) — skip per-row checks if it's a spill.
        if not freq_is_spill:
            cell_ref = f"G{row}"
            cell = sheet[cell_ref]
            formula = cell.value

            if formula is None or str(formula).strip() == "":
                feedback.append(("FREQ_COUNT_MISSING", {"cell": cell_ref}))
            elif not isinstance(formula, str) or not formula.startswith("="):
                # A legacy array (CSE) formula: grade its text like any other.
                if _check_frequency_formula(_formula_text(formula), row):
                    correct_freq += 1
                else:
                    feedback.append(("FREQ_COUNT_WRONG", {"cell": cell_ref}))
            elif _check_frequency_formula(formula, row):
                correct_freq += 1
            else:
                feedback.append(("FREQ_COUNT_WRONG", {"cell": cell_ref}))

        # Check Relative Frequency (H column) — skip per-row checks if spill.
        if not relfreq_is_spill:
            cell_ref = f"H{row}"
            cell = sheet[cell_ref]
            formula = cell.value

            if formula is None or str(formula).strip() == "":
                feedback.append(("FREQ_REL_MISSING", {"cell": cell_ref}))
            elif not isinstance(formula, str) or not formula.startswith("="):
                feedback.append(("FREQ_REL_WRONG", {"cell": cell_ref}))
            elif _check_relative_freq_formula(formula, row):
                correct_relfreq += 1
            else:
                feedback.append(("FREQ_REL_WRONG", {"cell": cell_ref}))
    
    # Value-based check: do the frequencies account for EVERY data value?
    # A strict `<` on the final bin (with no buffer on the max) or a wrong
    # boundary operator drops values, so the frequencies total fewer than the 50
    # data points even though the formulas look structurally fine. Cap the
    # frequency credit at (11 - number of uncounted values) so the penalty scales
    # with how many values were dropped.
    if values_sheet is not None:
        data_count = 0
        for r in range(12, 62):
            v = values_sheet[f"B{r}"].value
            if isinstance(v, (int, float)):
                data_count += 1
        freq_sum = 0.0
        have_values = False
        for r in range(28, 39):
            v = values_sheet[f"G{r}"].value
            if isinstance(v, (int, float)):
                freq_sum += v
                have_values = True
        # NOTE: this is a manual-review FLAG only — it does NOT deduct points.
        # A shortfall can be caused by an upstream error (wrong bin width or
        # limits) that is already graded elsewhere, or by unreliable cached
        # values, so auto-deducting here caused false negatives. We surface it
        # for the instructor to check the boundaries/bin width by eye.
        if data_count > 0 and have_values and freq_sum > 0:
            missing = data_count - int(round(freq_sum))
            if missing > 0:
                feedback.append(("FREQ_COUNT_UNDERCOUNT", {
                    "counted": int(round(freq_sum)),
                    "total": data_count
                }))

    # Calculate score (6 pts each column)
    title_score = (correct_title / total_rows) * 6.0
    freq_score = (correct_freq / total_rows) * 6.0
    relfreq_score = (correct_relfreq / total_rows) * 6.0
    total_score = round(title_score + freq_score + relfreq_score, 2)
    
    total_correct = correct_title + correct_freq + correct_relfreq
    total_cells = total_rows * 3
    
    # Summary feedback
    if total_correct == total_cells:
        feedback = [("FREQ_DIST_ALL_CORRECT", {})]
    elif total_correct == 0:
        feedback.insert(0, ("FREQ_DIST_NONE_CORRECT", {}))
    else:
        feedback.insert(0, ("FREQ_DIST_PARTIAL", {"correct": total_correct, "total": total_cells}))
    
    return total_score, feedback
