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


def _reference_date(sheet):
    """When the student saved the workbook (falls back to today). Rates can't
    have been looked up after this, which bounds the dates without depending on
    WHEN the instructor grades."""
    try:
        modified = sheet.parent.properties.modified
        if isinstance(modified, datetime):
            return modified.date()
    except AttributeError:
        pass
    return date.today()


def _year_fixed(d, anchor):
    """`d` with its year swapped to the anchor's year (a one-year typo), or None."""
    if d.year == anchor.year or abs(d.year - anchor.year) != 1:
        return None
    try:
        return d.replace(year=anchor.year)
    except ValueError:  # Feb 29 in a non-leap year
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
      - A date whose year is off by one (e.g. 10/04/2025 among 2026 dates) is
        accepted as a typo.
      - Dates must be plausible: not after the workbook was saved and not more
        than a year before it (so stale or copied dates don't pass just because
        they agree with each other).

    Scoring:
      - 0.5 points per valid, consistent date (max 2.0).

    Returns:
      (score: float, feedback: list[(code, params)], parsed_dates: list[date|None])
    """
    max_spread_days = 21
    max_age_days = 365
    cols = ["C", "D", "E", "F"]
    ref = _reference_date(sheet)

    parsed = {col: _parse_date(sheet[f"{col}17"].value) for col in cols}
    parsed_dates = [parsed[col] for col in cols]

    # Anchor on the date that the most other dates agree with (a 2-vs-2 split
    # goes to the more recent pair). Robust to a single outlier.
    valid = [d for d in parsed.values() if d is not None]

    def support(a):
        return sum(1 for d in valid if abs((d - a).days) <= max_spread_days)

    anchor = max(valid, key=lambda a: (support(a), a)) if valid else None

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

        # Forgive a one-year typo when the corrected date fits with the others.
        effective = d
        fixed = _year_fixed(d, anchor)
        if abs((d - anchor).days) > max_spread_days and fixed is not None \
                and abs((fixed - anchor).days) <= max_spread_days:
            effective = fixed

        age = (ref - effective).days
        spread = abs((effective - anchor).days)
        if age < -1 or age > max_age_days:
            feedback.append(("CC17_DATE_OUT_OF_RANGE", {
                "cell": cell, "date": str(d), "saved": str(ref), "max_age": max_age_days,
            }))
        elif spread > max_spread_days:
            feedback.append(("CC17_DATE_INCONSISTENT", {
                "cell": cell, "date": str(d), "max_days": max_spread_days, "off_by": spread
            }))
        elif effective != d:
            score += 0.5
            feedback.append(("CC17_DATE_YEAR_TYPO", {"cell": cell, "date": str(d), "year": effective.year}))
        else:
            score += 0.5
            feedback.append(("CC17_DATE_VALID", {"cell": cell, "date": str(d)}))

    score_rounded = round(score, 1)
    if score_rounded == 2.0:
        feedback.insert(0, ("CC17_ALL_VALID", {"points": 2.0, "max_days": max_spread_days}))
    elif score_rounded > 0:
        feedback.insert(0, ("CC17_PARTIAL", {"earned": score_rounded, "possible": 2.0, "max_days": max_spread_days}))
    else:
        feedback.insert(0, ("CC17_NONE_VALID", {"possible": 2.0, "max_days": max_spread_days}))

    return score_rounded, feedback, parsed_dates
