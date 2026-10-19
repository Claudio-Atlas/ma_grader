"""
grade_credit_card_amortization.py — Credit Cards amortization table (24 pts).

The table (starting at row 25) has one row per month with five columns:

    A: Month number        (1, 2, 3, ...)
    B: Current Balance      B25 = C14 (start balance);  B{r} = D{r-1} + E{r-1}
    C: Payment              = MIN(B{r}, MAX(C18, C17*B{r}))
    D: Balance After Pay    = B{r} - C{r}
    E: Interest             = D{r} * (C13/C15)

Scoring (per Richard's suggestion): the four computed columns B, C, D, E are each
worth 6 points (24 total), scored by how many rows follow the correct formula
pattern. This is robust to how far a student drags the table and to where it pays
off — the formula pattern is identical on every row — and it gives clear,
per-column feedback instead of a single opaque number.
"""

import re

from utilities.xl import load_workbook  # strips _xlfn. prefixes

from graders.ma2_credit_cards.compute_credit_card_payoff import compute_credit_card_payoff_months

START_ROW = 25
MAX_SCAN = 800  # safety cap
COL_LABELS = {
    "B": "Current Balance",
    "C": "Payment",
    "D": "Balance After Payment",
    "E": "Interest",
}


# What each column's formula should look like (row 26 shown).
EXPECTED = {
    "B": "the previous row's balance after payment plus its interest, like =D25+E25",
    "C": "the smaller of the balance and the minimum payment, like =MIN(B26,MAX($C$18,$C$17*B26))",
    "D": "the balance minus the payment, like =B26-C26",
    "E": "the balance after payment times the monthly rate, like =D26*($C$13/$C$15)",
}


def _norm(formula) -> str:
    if not isinstance(formula, str):
        return ""
    return formula.strip().lower().replace(" ", "").replace("$", "")


def _find_table_rows(ws_f):
    """Return the list of populated table rows: START_ROW down to the last row
    whose Payment (C) cell holds a formula. Stops after a few blank rows."""
    last = START_ROW
    blanks = 0
    r = START_ROW
    while r < START_ROW + MAX_SCAN:
        c = ws_f[f"C{r}"].value
        if isinstance(c, str) and c.startswith("="):
            last = r
            blanks = 0
        else:
            blanks += 1
            if blanks >= 3:
                break
        r += 1
    return list(range(START_ROW, last + 1)), last


def _has(f, ref):
    """True if normalized formula f references cell `ref` exactly (so "d25"
    doesn't match inside "d250")."""
    return re.search(rf"(?<![a-z0-9]){ref}(?![0-9])", f) is not None


def _row_ok(col, r, f):
    """Is formula f (normalized) in column `col` at row r the correct pattern?"""
    if col == "B":
        if r == START_ROW:
            # Start balance: references C14 (often wrapped in an IF(... , C14)).
            return _has(f, "c14")
        return _has(f, f"d{r-1}") and _has(f, f"e{r-1}") and ("+" in f)
    if col == "C":
        return ("min(" in f) and ("max(" in f) and _has(f, f"b{r}") and _has(f, "c17") and _has(f, "c18")
    if col == "D":
        return _has(f, f"b{r}") and _has(f, f"c{r}") and ("-" in f)
    if col == "E":
        return (
            _has(f, f"d{r}") and _has(f, "c13")
            and (_has(f, "c15") or re.search(r"/12(?![0-9])", f) is not None)
            and ("/" in f) and ("*" in f)
        )
    return False


def _expected_payoff_months(ws_v, ws_f=None):
    """Months to pay off, simulated from the student's own parameters
    (C13 APR, C14 balance, C15 payments/yr, C17 min %, C18 fixed min).
    None if they aren't all numbers."""
    def val(ref):
        # Cached value, else the typed value (files never recalculated in Excel).
        v = ws_v[ref].value
        if not isinstance(v, (int, float)) and ws_f is not None:
            v = ws_f[ref].value
        return v

    try:
        apr = float(val("C13"))
        balance = float(val("C14"))
        per_year = int(val("C15"))
        pct = float(val("C17"))
        fixed = float(val("C18"))
    except (TypeError, ValueError):
        return None
    if balance <= 0 or per_year <= 0 or (pct <= 0 and fixed <= 0):
        return None
    apr_pct = apr if apr > 1 else apr * 100   # accept 0.2 or 20
    pct = pct / 100 if pct > 1 else pct
    months = compute_credit_card_payoff_months(balance, pct, fixed, apr_pct, per_year)
    return months if months < 600 else None   # never pays off within the cap


def _detect_payoff(ws_v, rows):
    """Payoff row = first row where the Balance After Payment (D) reaches ~0 with
    a positive starting balance. None if the table never pays off."""
    for r in rows:
        b = ws_v[f"B{r}"].value
        d = ws_v[f"D{r}"].value
        if isinstance(b, (int, float)) and isinstance(d, (int, float)):
            if b > 0.005 and abs(d) <= 0.05:
                return r
    return None


def grade_credit_card_amortization(student_file_path):
    """
    Grade the amortization table. Returns:
        {
            "total_points": float (0-24),
            "comment": str (per-column breakdown),
            "column_points": {"B":.., "C":.., "D":.., "E":..},
            "payoff_row": {"payoff_month": int, "excel_row": int, "last_row": int},
        }
    """
    wb_f = load_workbook(student_file_path, data_only=False)
    wb_v = load_workbook(student_file_path, data_only=True)
    ws_f = wb_f["Credit Cards"]
    ws_v = wb_v["Credit Cards"]

    rows, last = _find_table_rows(ws_f)

    # The table must run down to the payoff month. If it never reaches a zero
    # balance, score each column over the rows it SHOULD have (simulated from
    # the student's parameters), so a table cut short can't earn full marks.
    payoff_row = _detect_payoff(ws_v, rows)
    expected_months = _expected_payoff_months(ws_v, ws_f)
    comments = []
    n = len(rows)
    if payoff_row is None and expected_months and expected_months > n:
        n = expected_months
        comments.append(
            f"Your table stops at row {last} (month {len(rows)}) before the balance reaches $0. "
            f"Fill the formulas down until it's paid off, in month {expected_months} "
            f"(row {START_ROW + expected_months - 1})."
        )

    correct = {c: 0 for c in "BCDE"}
    bad = {c: [] for c in "BCDE"}

    for r in rows:
        for col in "BCDE":
            if _row_ok(col, r, _norm(ws_f[f"{col}{r}"].value)):
                correct[col] += 1
            else:
                bad[col].append(f"{col}{r}")

    column_points = {}
    total = 0.0
    for col in "BCDE":
        pts = round(6.0 * correct[col] / n, 2) if n else 0.0
        column_points[col] = pts
        total += pts
        if correct[col] == n:
            comments.append(f"{COL_LABELS[col]} column ({col}): all {n} rows correct — {pts}/6.")
        else:
            if not bad[col]:
                continue  # only short because the table stops early (said above)
            first = bad[col][0]
            more = f" and {len(bad[col]) - 1} more" if len(bad[col]) > 1 else ""
            comments.append(
                f"Your {COL_LABELS[col]} column needs a fix starting at {first}{more}. "
                f"Each row should be {EXPECTED[col]}, filled down the column."
            )

    total = round(total, 2)

    if payoff_row is not None:
        a_val = ws_v[f"A{payoff_row}"].value
        payoff_month = int(a_val) if isinstance(a_val, (int, float)) else (payoff_row - START_ROW + 1)
    elif expected_months:
        # Never paid off: grade the summary against the true payoff month.
        payoff_month = expected_months
        payoff_row = START_ROW + expected_months - 1
    else:
        payoff_row = last
        payoff_month = last - START_ROW + 1

    wb_f.close()
    wb_v.close()

    return {
        "total_points": total,
        "comment": " | ".join(comments),
        "column_points": column_points,
        "payoff_row": {"payoff_month": payoff_month, "excel_row": payoff_row, "last_row": last},
    }
