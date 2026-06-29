# graders/currency_conversion_v2/row21_usd_conversion_back_v2.py

import re


def _normalize_formula(formula):
    """
    Normalize an Excel formula string for comparison:
      - removes leading '='
      - strips $, spaces, parentheses
      - lowercase
    """
    if not isinstance(formula, str):
        return ""
    f = formula.lstrip("=")
    f = f.replace("$", "")
    f = re.sub(r"[()\s]", "", f)
    return f.lower()


def _formula_contains_refs(formula: str, required_refs: list) -> bool:
    """
    Check if a formula contains all required cell references.
    
    Args:
        formula: The formula string (e.g., '=D4/C19')
        required_refs: List of required cell refs (e.g., ['D4', 'C19'])
    
    Returns:
        True if ALL required references are found in the formula
    """
    if not formula:
        return False
    
    # Normalize: remove =, $, spaces, and lowercase
    cleaned = formula.lstrip("=").replace("$", "").replace(" ", "").lower()
    
    for ref in required_refs:
        ref_lower = ref.lower()
        if ref_lower not in cleaned:
            return False
    
    return True


def _values_match(actual, expected, tolerance=0.01) -> bool:
    """
    Check if two values match within a tolerance.
    
    Args:
        actual: The actual value from the cell
        expected: The expected calculated value
        tolerance: Relative tolerance (default 1%)
    
    Returns:
        True if values match within tolerance
    """
    if actual is None or expected is None:
        return False
    
    try:
        actual_float = float(actual)
        expected_float = float(expected)
        
        if expected_float == 0:
            return abs(actual_float) < 0.01
        
        relative_diff = abs(actual_float - expected_float) / abs(expected_float)
        return relative_diff <= tolerance
    except (ValueError, TypeError):
        return False


def _get_cell_value_safe(sheet, cell_ref):
    """Safely get a cell's numeric value, returning None if not numeric."""
    try:
        val = sheet[cell_ref].value
        if val is None:
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def grade_row21_usd_conversion_back_v2(sheet, values_sheet=None):
    """
    Currency Conversion V2 - Row 21 (C21-F21)

    Rule (same as V1):
      Converts foreign amount (D4) back to USD using the corresponding rate in row 19:
        C21 = D4 / C19
        D21 = D4 / D19
        E21 = D4 / E19
        F21 = D4 / F19

    Scoring (BULLETPROOF):
      - Formula correctness: 2.0 pts per cell (max 8.0)
        - Full credit if: formula contains D4 AND rate cell AND calculated value is correct
      - Formatting correctness (currency, 2 decimals): 0.25 pts per cell (max 1.0)
      - Total possible: 9.0

    Args:
        sheet: Worksheet with formulas (data_only=False)
        values_sheet: Worksheet with calculated values (data_only=True), optional

    Returns:
      (total_score, formula_score, format_score, feedback)
        feedback is list[(code, params)]
    """

    usd_cell = "D4"
    rate_row = 19
    budget_row = 20  # Row 20 contains the foreign budget (B4 * rate)
    row = 21
    cols = ["C", "D", "E", "F"]

    formula_score = 0.0
    format_score = 0.0
    feedback = []
    
    # Get D4 value for expected calculations
    d4_value = _get_cell_value_safe(sheet, usd_cell)

    for col in cols:
        cell_ref = f"{col}{row}"
        source_rate_cell = f"{col}{rate_row}"
        source_budget_cell = f"{col}{budget_row}"

        raw_formula = sheet[cell_ref].value
        
        # -----------------------------
        # Formula check (BULLETPROOF - refs + value)
        # -----------------------------
        if not isinstance(raw_formula, str) or not raw_formula.startswith("="):
            feedback.append(("CC21_FORMULA_MISSING", {"cell": cell_ref, "expected": f"=D4/{source_rate_cell}"}))
        else:
            # Method 1: Check for required cell references
            # The formula should reference D4 (USD amount) AND the rate cell (C19/D19/etc.)
            # OR it could reference the budget cell (C20/D20) and rate cell
            has_required_refs = (
                _formula_contains_refs(raw_formula, [usd_cell, source_rate_cell]) or
                _formula_contains_refs(raw_formula, [source_budget_cell, source_rate_cell])
            )
            
            # Method 2: Check exact formula match (traditional approach)
            cleaned = _normalize_formula(raw_formula)
            expected = _normalize_formula(f"{usd_cell}/{source_rate_cell}")
            exact_match = (cleaned == expected)
            
            # Method 3: Verify calculated value is correct (if values_sheet provided)
            value_correct = False
            if values_sheet is not None and d4_value is not None:
                rate_value = _get_cell_value_safe(sheet, source_rate_cell)
                if rate_value is not None and rate_value != 0:
                    expected_value = d4_value / rate_value
                    actual_value = _get_cell_value_safe(values_sheet, cell_ref)
                    value_correct = _values_match(actual_value, expected_value)
            
            # Check if formula has division (correct concept) but hardcoded values
            has_division = "/" in raw_formula or "1/" in raw_formula
            
            # Award credit: need refs + value (if we can check), or exact match
            if exact_match:
                formula_score += 2.0
                feedback.append(("CC21_FORMULA_OK", {"cell": cell_ref, "expected": f"=D4/{source_rate_cell}"}))
            elif has_required_refs:
                if values_sheet is None:
                    # Can't verify value, trust the references
                    formula_score += 2.0
                    feedback.append(("CC21_FORMULA_OK", {
                        "cell": cell_ref, 
                        "expected": f"=D4/{source_rate_cell}",
                        "note": "Formula uses correct cell references"
                    }))
                elif value_correct:
                    # References correct AND value correct - full credit
                    formula_score += 2.0
                    feedback.append(("CC21_FORMULA_OK", {
                        "cell": cell_ref, 
                        "expected": f"=D4/{source_rate_cell}",
                        "note": "Formula uses correct cell references and value is correct"
                    }))
                else:
                    # References correct but value wrong - no credit
                    feedback.append(("CC21_FORMULA_BAD", {
                        "cell": cell_ref, 
                        "expected": f"=D4/{source_rate_cell}",
                        "note": "Formula has correct refs but calculated value is incorrect"
                    }))
            elif has_division:
                # Partial credit: formula shows correct concept (division) but hardcoded values
                formula_score += 0.75
                feedback.append(("CC21_FORMULA_PARTIAL", {
                    "cell": cell_ref,
                    "expected": f"=D4/{source_rate_cell}",
                    "note": "Formula uses division (correct concept) but hardcoded values. Use cell references for full credit."
                }))
            else:
                feedback.append(("CC21_FORMULA_BAD", {"cell": cell_ref, "expected": f"=D4/{source_rate_cell}"}))

        # -----------------------------
        # Formatting check (same acceptance logic as V1)
        # -----------------------------
        num_fmt = str(sheet[cell_ref].number_format).lower()
        if "$" in num_fmt or "currency" in num_fmt or "0.00" in num_fmt:
            format_score += 0.25
            feedback.append(("CC21_FORMAT_OK", {"cell": cell_ref}))
        else:
            feedback.append(("CC21_FORMAT_BAD", {"cell": cell_ref}))

    total_score = round(formula_score + format_score, 2)

    feedback.insert(0, (
        "CC21_SUMMARY",
        {
            "formula": round(formula_score, 2),
            "formula_possible": 8.0,
            "formatting": round(format_score, 2),
            "formatting_possible": 1.0,
            "total": total_score,
            "total_possible": 9.0
        }
    ))

    return total_score, round(formula_score, 2), round(format_score, 2), feedback
