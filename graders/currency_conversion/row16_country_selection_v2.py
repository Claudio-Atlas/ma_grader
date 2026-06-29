# graders/currency_conversion_v2/row16_country_selection_v2.py

import re
from graders.currency_conversion.currency_lookup import (
    get_country_entry_by_name,
    resolve_country,
    country_currency_dict,
)
from graders.currency_conversion.utils import norm_unit


# Build set of available first letters from country list
AVAILABLE_LETTERS = set(name[0].lower() for name in country_currency_dict.keys())


def _resolve_cell_value(sheet, cell_ref: str) -> str:
    """
    Get the displayed value of a cell, resolving simple cell references.
    
    If the cell contains a formula like '=F27', look up the referenced cell's value.
    This handles students who link to the country list instead of typing directly.
    
    Args:
        sheet: The openpyxl Worksheet object
        cell_ref: Cell reference like 'C16'
    
    Returns:
        The resolved string value of the cell
    """
    cell = sheet[cell_ref]
    raw = cell.value
    
    if raw is None:
        return ""
    
    # If it's not a string, convert it
    if not isinstance(raw, str):
        return str(raw).strip()
    
    raw = raw.strip()
    
    # Check if it's a simple cell reference formula (e.g., =F27, =$F$27)
    # Country list is on the SAME tab, so no cross-sheet references needed
    simple_ref_pattern = r'^=\$?([A-Za-z]+)\$?(\d+)$'
    
    match = re.match(simple_ref_pattern, raw)
    if match:
        # Simple reference like =F27 or =$F$27
        col, row = match.groups()
        ref_cell = f"{col.upper()}{row}"
        ref_value = sheet[ref_cell].value
        if ref_value is not None:
            return str(ref_value).strip()
        return ""
    
    # If it starts with = but isn't a simple reference, it's a complex formula
    # In that case, return the formula as-is (will likely fail validation)
    if raw.startswith("="):
        return raw
    
    # Regular value, return as-is
    return raw


def _get_fallback_letter(expected_letter: str) -> str:
    """
    If the expected letter has no countries, return the next available letter.
    Letters with no/limited countries: X (none), O/Q/W/Y/Z (one each)
    """
    letter = expected_letter.lower()
    
    # If letter has countries, use it as-is
    if letter in AVAILABLE_LETTERS:
        return letter
    
    # Otherwise find next available letter in alphabet
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    start_idx = alphabet.index(letter) if letter in alphabet else 0
    
    # Search forward from the expected letter
    for i in range(1, 26):
        next_idx = (start_idx + i) % 26
        next_letter = alphabet[next_idx]
        if next_letter in AVAILABLE_LETTERS:
            return next_letter
    
    # Fallback to 'm' if nothing found (shouldn't happen)
    return 'm'


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

    # Prefer underscore split if present (your pipeline uses First_Last)
    if "_" in s:
        parts = [p for p in s.split("_") if p]
    else:
        parts = [p for p in s.split() if p]

    if not parts:
        return "", ""

    first = parts[0]
    last = parts[-1] if len(parts) > 1 else parts[0]
    return first, last


def grade_row16_country_selection_v2(sheet, student_name: str):
    """
    Currency Conversion V2 - Row 16 (C16-F16)

    Rule:
      - C16, D16 must start with first two letters of FIRST name
      - E16, F16 must start with first two letters of LAST name
      - 0.5 pts each cell (max 2.0)
      - Country must exist on approved list (currency_lookup)

    Returns:
      (score: float, feedback: list[(code, params)], country_entries: list[entry_or_none])
    """

    first_name, last_name = _split_student_name(student_name)

    first = first_name.lower()
    last = last_name.lower()

    # Name-derived initials, used only as a FALLBACK when the student left the
    # corresponding Row 15 letter blank.
    raw_letters = [
        first[0] if len(first) > 0 else "m",
        first[1] if len(first) > 1 else "m",
        last[0] if len(last) > 0 else "m",
        last[1] if len(last) > 1 else "m",
    ]
    fallback_letters = [_get_fallback_letter(letter) for letter in raw_letters]

    cells = ["C16", "D16", "E16", "F16"]
    letter_cells = ["C15", "D15", "E15", "F15"]

    score = 0.0
    feedback = []
    matched_entries = {}

    for idx, cell in enumerate(cells):
        # Consistency: judge the country against the letter the STUDENT actually
        # put in Row 15 (so a wrong letter is penalized once, in Row 15 — not
        # again here). Fall back to the name-derived letter if Row 15 is blank.
        raw15 = sheet[letter_cells[idx]].value
        student_letter = (str(raw15).strip()[:1].lower() if raw15 and str(raw15).strip()
                          else fallback_letters[idx].lower())

        # Use _resolve_cell_value to handle cell references (e.g., =F27 linking to country list)
        raw = _resolve_cell_value(sheet, cell)
        country_name = norm_unit(raw) if raw else ""

        if not country_name:
            feedback.append(("CC16_COUNTRY_BLANK", {"cell": cell}))
            continue

        # Resolve the country, tolerating obvious typos (forgiven).
        entry, how = resolve_country(country_name)

        if not entry:
            feedback.append(("CC16_COUNTRY_NOT_APPROVED", {"cell": cell, "found": country_name}))
            continue

        canonical_country = entry["country"]
        # The resolved country anchors Row 18 (code) and Row 19 (rate) regardless
        # of whether the initial matches, so one error never cascades.
        matched_entries[cell] = entry

        if not canonical_country.lower().startswith(student_letter):
            feedback.append((
                "CC16_COUNTRY_WRONG_INITIAL",
                {
                    "cell": cell,
                    "country": canonical_country,
                    "expected_letter": student_letter.upper()
                }
            ))
            continue

        score += 0.5
        feedback.append((
            "CC16_COUNTRY_CORRECT",
            {
                "cell": cell,
                "country": canonical_country,
                "expected_letter": student_letter.upper()
            }
        ))

    score = round(score, 1)

    # Summary message first
    if score == 2.0:
        feedback.insert(0, ("CC16_ALL_CORRECT", {"points": 2.0}))
    elif score > 0:
        feedback.insert(0, ("CC16_PARTIAL", {"earned": score, "possible": 2.0}))
    else:
        feedback.insert(0, ("CC16_NONE_CORRECT", {"possible": 2.0}))

    ordered_entries = [matched_entries.get(c) for c in cells]
    return score, feedback, ordered_entries
