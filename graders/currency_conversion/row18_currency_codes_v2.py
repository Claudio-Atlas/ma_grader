# graders/currency_conversion_v2/row18_currency_codes_v2.py

def grade_row18_currency_codes_v2(sheet, country_entries):
    """
    Currency Conversion V2 - Row 18 (C18-F18)

    Rule (same as V1):
      - Each cell must contain the correct currency code for the country
        selected in Row 16.
      - Each correct code = 1 point (max 4).
      - Works independently even if Row 16 was partially or fully incorrect.

    Inputs:
      - country_entries: list of dicts or None, aligned with C16-F16

    Returns:
      (score: float, feedback: list[(code, params)])
    """

    score = 0.0
    feedback = []
    cols = ["C", "D", "E", "F"]

    for idx, col in enumerate(cols):
        cell = f"{col}18"
        raw_val = sheet[cell].value
        student_code = str(raw_val).strip().upper() if raw_val else ""

        entry = country_entries[idx]  # may be None

        # --- Row 16 invalid / missing ---
        if entry is None:
            if student_code:
                feedback.append((
                    "CC18_COUNTRY_UNKNOWN",
                    {"cell": cell, "found": student_code}
                ))
            else:
                feedback.append((
                    "CC18_COUNTRY_UNKNOWN_BLANK",
                    {"cell": cell}
                ))
            continue

        expected_code = entry.get("currency_code")

        # --- Correct ---
        if student_code == expected_code:
            score += 1
            feedback.append((
                "CC18_CODE_CORRECT",
                {
                    "cell": cell,
                    "code": student_code,
                    "country": entry.get("country")
                }
            ))
        else:
            feedback.append((
                "CC18_CODE_INCORRECT",
                {
                    "cell": cell,
                    "expected": expected_code,
                    "found": (student_code if student_code else "[blank]"),
                    "country": entry.get("country")
                }
            ))

    score_rounded = round(score, 1)
    if score_rounded == 4.0:
        feedback.insert(0, ("CC18_ALL_CORRECT", {"points": 4.0}))
    elif score_rounded > 0:
        feedback.insert(0, ("CC18_PARTIAL", {"earned": score_rounded, "possible": 4.0}))
    else:
        feedback.insert(0, ("CC18_NONE_CORRECT", {"possible": 4.0}))

    return score_rounded, feedback
