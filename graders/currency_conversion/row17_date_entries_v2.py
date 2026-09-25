# graders/currency_conversion_v2/row17_date_entries_v2.py

from datetime import datetime, date


def _parse_date(cell_value):
    """Return a date for a cell value (datetime, date, or MM/DD/YYYY[-ish] text),
    or None if it isn't a parseable date."""
    if cell_value is None or cell_value == "":
        return None
    if isinstance(cell_value, datetime):
        return cell_value.date()
    if isinstance(cell_value, date):
        return cell_value
    text = str(cell_value).strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%m-%d-%Y", "%m-%d-%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def grade_row17_date_entries_v2(sheet):
    """
    Currency Conversion V2 - Row 17 (C17-F17)

    Rule:
      - Each cell must contain a valid date.
      - The dates must be CONSISTENT with each other — i.e. all looked up around
        the same time (within 21 days of one another). This replaces the old
        "within 21 days of today" test, which wrongly failed on-time dates when
        the assignment is graded after its due date.

    Scoring:
      - 0.5 points per valid, consistent date (max 2.0).

    Returns:
      (score: float, feedback: list[(code, params)], parsed_dates: list[date|None])
    """
    max_spread_days = 21
    cols = ["C", "D", "E", "F"]

    parsed = {col: _parse_date(sheet[f"{col}17"].value) for col in cols}
    parsed_dates = [parsed[col] for col in cols]

    # Anchor on the median of the valid dates — robust to a single outlier.
    valid = sorted(d for d in parsed.values() if d is not None)
    anchor = valid[len(valid) // 2] if valid else None

    score = 0.0
    feedback = []

    for col in cols:
        cell = f"{col}17"
        d = parsed[col]

        if d is None:
            raw = sheet[cell].value
            if raw is None or str(raw).strip() == "":
                feedback.append(("CC17_DATE_MISSING", {"cell": cell}))
            else:
                feedback.append(("CC17_DATE_PARSE_ERROR", {"cell": cell}))
            continue

        spread = abs((d - anchor).days) if anchor is not None else 0
        if spread <= max_spread_days:
            score += 0.5
            feedback.append(("CC17_DATE_VALID", {"cell": cell, "date": str(d)}))
        else:
            feedback.append(("CC17_DATE_INCONSISTENT", {
                "cell": cell, "date": str(d), "max_days": max_spread_days, "off_by": spread
            }))

    score_rounded = round(score, 1)
    if score_rounded == 2.0:
        feedback.insert(0, ("CC17_ALL_VALID", {"points": 2.0, "max_days": max_spread_days}))
    elif score_rounded > 0:
        feedback.insert(0, ("CC17_PARTIAL", {"earned": score_rounded, "possible": 2.0, "max_days": max_spread_days}))
    else:
        feedback.insert(0, ("CC17_NONE_VALID", {"possible": 2.0, "max_days": max_spread_days}))

    return score_rounded, feedback, parsed_dates
