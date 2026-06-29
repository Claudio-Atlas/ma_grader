"""
grade_currency_conversion_tab_v2.py — Main orchestrator for Currency Conversion grading

Purpose: Coordinates all grading checks for the Currency Conversion worksheet tab.
         Aggregates scores and feedback from row-specific checker modules and
         returns a unified results dictionary for the writer to process.

Author: Clayton Ragsdale
Dependencies: row15-row21 checker modules, currency_lookup, requests (for API)

Grading Breakdown (~36 points total):
    Row 15 (Name Letters C15:F15): 2 points (0.5 pts each)
    Row 16 (Country Selection): 2 points (0.5 pts each)
    Row 17 (Date Entries): 2 points (0.5 pts each, must be within 21 days)
    Row 18 (Currency Codes): 4 points (1 pt each)
    Row 19 (Exchange Rates): 4 pts accuracy + 1 pt formatting = 5 points
    Row 20 (Budget Conversion): 8 pts formulas + 1 pt formatting = 9 points
    Row 21 (USD Conversion Back): 8 pts formulas + 1 pt formatting = 9 points
    Row 22 (Formatting Total): Aggregated from rows 19-21 + 1 pt bonus
"""

from typing import Dict, Any, List, Tuple, Optional
from openpyxl.worksheet.worksheet import Worksheet

from .row15_name_letters_v2 import grade_row15_name_letters_v2
from .row16_country_selection_v2 import grade_row16_country_selection_v2
from .row17_date_entries_v2 import grade_row17_date_entries_v2
from .row18_currency_codes_v2 import grade_row18_currency_codes_v2
from .row19_exchange_rates_v2 import grade_row19_exchange_rates_v2, fetch_live_usd_rates
from .row20_budget_conversion_v2 import grade_row20_budget_conversion_v2
from .row21_usd_conversion_back_v2 import grade_row21_usd_conversion_back_v2


def grade_currency_conversion_tab_v2(
    sheet: Worksheet,
    student_name: str,
    values_sheet: Optional[Worksheet] = None
) -> Dict[str, Any]:
    """
    Currency Conversion V2 grading orchestrator.
    
    This function coordinates all row-level graders for the Currency Conversion
    tab and returns a unified results dictionary that matches the expected
    format for the writer module.
    
    Grading Flow:
        1. Row 15: Validate name initials match student's filename
        2. Row 16: Validate country selection (must start with correct letters)
        3. Row 17: Validate dates are recent (within 21 days)
        4. Row 18: Validate currency codes match selected countries
        5. Row 19: Validate exchange rates against live API (±5% tolerance)
        6. Row 20: Validate budget conversion formulas (=B4*rate)
        7. Row 21: Validate USD conversion back formulas (=D4/rate)
    
    Data Dependencies:
        - Row 16's country entries are passed to Row 18 for code validation
        - Row 19 uses live exchange rate API for accuracy checking
    
    Args:
        sheet: The openpyxl Worksheet object for the Currency Conversion tab
        student_name: Student's name from filename (e.g., "John_Doe")
    
    Returns:
        Dict containing:
            - row15_score, row15_feedback
            - row16_score, row16_feedback
            - row17_score, row17_feedback
            - row18_score, row18_feedback
            - row19_accuracy_score, row19_format_score, row19_feedback
            - row20_formula_score, row20_format_score, row20_feedback
            - row21_formula_score, row21_format_score, row21_feedback
            - formatting_total (sum of formatting scores + 1 bonus)
    
    Example:
        >>> from openpyxl import load_workbook
        >>> wb = load_workbook("student_submission.xlsx")
        >>> ws = wb["Currency Conversion"]
        >>> results = grade_currency_conversion_tab_v2(ws, "John_Doe")
        >>> print(f"Row 15 score: {results['row15_score']}")
    """

    results: Dict[str, Any] = {}

    # ============================================================
    # Row 15: Name Letters (C15:F15)
    # ============================================================
    # Student should enter first two letters of first name (C15, D15)
    # and first two letters of last name (E15, F15)
    score15, fb15 = grade_row15_name_letters_v2(sheet, student_name)
    results["row15_score"] = score15
    results["row15_feedback"] = fb15

    # ============================================================
    # Row 16: Country Selection (C16:F16)
    # ============================================================
    # Countries must start with the letters entered in Row 15
    # Returns country_entries for use by Row 18 currency code validation
    score16, fb16, country_entries = grade_row16_country_selection_v2(sheet, student_name)
    results["row16_score"] = score16
    results["row16_feedback"] = fb16

    # ============================================================
    # Row 17: Date Entries (C17:F17)
    # ============================================================
    # Each cell must contain a valid date within 21 days of today
    score17, fb17, _parsed_dates = grade_row17_date_entries_v2(sheet)
    results["row17_score"] = score17
    results["row17_feedback"] = fb17

    # ============================================================
    # Row 18: Currency Codes (C18:F18)
    # ============================================================
    # Currency codes must match the countries selected in Row 16
    score18, fb18 = grade_row18_currency_codes_v2(sheet, country_entries)
    results["row18_score"] = score18
    results["row18_feedback"] = fb18

    # ============================================================
    # Row 19: Exchange Rates (C19:F19) - API-based validation
    # ============================================================
    # Fetch live rates once and pass to the grader
    # This is more efficient and allows better error handling
    live_rates, err = fetch_live_usd_rates()
    
    if err:
        # API fetch failed - zero score with error feedback
        score19_total, acc19, fmt19 = 0.0, 0.0, 0.0
        fb19: List[Tuple[str, Dict[str, Any]]] = [("CC19_API_FETCH_FAILED", {"error": err})]
    else:
        # Grade exchange rates against live values (±5% tolerance).
        # Anchor each rate to the student's chosen country (consistency), so a
        # wrong currency code in Row 18 doesn't also cost the Row 19 rate point.
        score19_total, acc19, fmt19, fb19 = grade_row19_exchange_rates_v2(
            sheet, live_rates=live_rates, country_entries=country_entries
        )

    # Split into accuracy and formatting components (matching V1 structure)
    results["row19_accuracy_score"] = round(min(acc19, 4.0), 2)
    results["row19_format_score"] = round(max(0.0, fmt19), 2)
    results["row19_feedback"] = fb19

    # ============================================================
    # Row 20: Budget Conversion Formulas (C20:F20)
    # ============================================================
    # Each cell should be =B4*{rate_cell} (e.g., =B4*C19)
    # Pass values_sheet to verify calculated values are correct
    score20_total, formula20, fmt20, fb20 = grade_row20_budget_conversion_v2(
        sheet, values_sheet, country_entries=country_entries
    )
    results["row20_formula_score"] = round(min(formula20, 8.0), 2)
    results["row20_format_score"] = round(max(0.0, fmt20), 2)
    results["row20_feedback"] = fb20

    # ============================================================
    # Row 21: USD Conversion Back Formulas (C21:F21)
    # ============================================================
    # Each cell should be =D4/{rate_cell} (e.g., =D4/C19)
    # Pass values_sheet to verify calculated values are correct
    score21_total, formula21, fmt21, fb21 = grade_row21_usd_conversion_back_v2(sheet, values_sheet)
    results["row21_formula_score"] = round(min(formula21, 8.0), 2)
    results["row21_format_score"] = round(max(0.0, fmt21), 2)
    results["row21_feedback"] = fb21

    # ============================================================
    # Formatting Total (Row 22)
    # ============================================================
    # Sum formatting scores from rows 19, 20, 21 plus a 1-point bonus
    # This rewards students who consistently apply proper formatting
    raw_formatting_sum = (
        float(results["row19_format_score"]) +
        float(results["row20_format_score"]) +
        float(results["row21_format_score"])
    )
    formatting_bonus = 1.0  # Bonus for overall formatting
    formatting_total = round(raw_formatting_sum + formatting_bonus, 2)
    results["formatting_total"] = formatting_total

    return results
