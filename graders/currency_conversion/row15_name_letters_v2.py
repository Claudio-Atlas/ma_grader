# graders/currency_conversion_v2/row15_name_letters_v2.py

def _split_student_name(student_name: str):
    """
    Supports:
      - 'First Last'
      - 'First_Last'
      - 'First Middle Last'
      - 'First_Middle_Last'
    Returns: (first_name, last_name)
    """
    if not student_name:
        return "", ""

    s = str(student_name).strip()

    if "_" in s:
        parts = [p for p in s.split("_") if p]
    else:
        parts = [p for p in s.split() if p]

    if not parts:
        return "", ""

    first = parts[0]
    last = parts[-1] if len(parts) > 1 else parts[0]
    return first, last


def grade_row15_name_letters_v2(sheet, student_name: str):
    """
    Currency Conversion V2 - Row 15 (C15-F15)

    Rule:
      - C15 = first_name[0]
      - D15 = first_name[1] (or 'M' if missing)
      - E15 = last_name[0]
      - F15 = last_name[1] (or 'M' if missing)

    Scoring:
      - 0.5 points per correct cell (max 2.0)

    Returns:
      (score: float, feedback: list[tuple[str, dict]])
    """

    first_name, last_name = _split_student_name(student_name)

    # Expected letters (uppercase), with fallback 'M'
    expected = [
        (first_name[0].upper() if len(first_name) > 0 else "M"),
        (first_name[1].upper() if len(first_name) > 1 else "M"),
        (last_name[0].upper()  if len(last_name) > 0 else "M"),
        (last_name[1].upper()  if len(last_name) > 1 else "M"),
    ]

    cells = ["C15", "D15", "E15", "F15"]

    score = 0.0
    feedback = []

    for idx, cell in enumerate(cells):
        raw = sheet[cell].value
        student_val = str(raw).strip().upper() if raw is not None else ""

        if student_val == expected[idx]:
            score += 0.5
            feedback.append((
                "CC15_LETTER_CORRECT",
                {"cell": cell, "expected": expected[idx]}
            ))
        else:
            feedback.append((
                "CC15_LETTER_INCORRECT",
                {
                    "cell": cell,
                    "expected": expected[idx],
                    "found": (student_val if student_val else "[blank]")
                }
            ))

    score = round(score, 1)

    if score == 2.0:
        feedback.insert(0, ("CC15_ALL_CORRECT", {"points": 2.0}))
    elif score > 0:
        feedback.insert(0, ("CC15_PARTIAL", {"earned": score, "possible": 2.0}))
    else:
        feedback.insert(0, ("CC15_NONE_CORRECT", {"possible": 2.0}))

    return score, feedback
