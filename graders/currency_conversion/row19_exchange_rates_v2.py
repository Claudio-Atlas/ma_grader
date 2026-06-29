# graders/currency_conversion_v2/row19_exchange_rates_v2.py

import requests
import urllib3

# Suppress InsecureRequestWarning when we need to bypass corporate proxy SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_live_usd_rates():
    """
    Fetch live FX rates with USD as the base currency.
    
    Handles corporate proxy/firewall environments that perform SSL inspection
    by falling back to verify=False if SSL verification fails.
    
    Returns: (rates_dict, error_message_or_none)
    """
    api_url = "https://open.er-api.com/v6/latest/USD"
    
    # First try with normal SSL verification
    try:
        response = requests.get(api_url, timeout=15, verify=True)
        response.raise_for_status()
        rates = response.json().get("rates", {})
        if not isinstance(rates, dict) or not rates:
            return {}, "API returned no rates."
        return rates, None
    except requests.exceptions.SSLError:
        # SSL error - likely corporate proxy doing SSL inspection
        # Retry without SSL verification
        try:
            response = requests.get(api_url, timeout=15, verify=False)
            response.raise_for_status()
            rates = response.json().get("rates", {})
            if not isinstance(rates, dict) or not rates:
                return {}, "API returned no rates."
            return rates, None
        except Exception as e:
            return {}, f"SSL bypass also failed: {str(e)}"
    except Exception as e:
        return {}, str(e)


def grade_row19_exchange_rates_v2(sheet, live_rates=None, country_entries=None):
    """
    Currency Conversion V2 - Row 19 (C19-F19)

    Validates the exchange rates in C19-F19. The "correct" rate is anchored to
    the currency of the COUNTRY the student chose in Row 16 (passed in as
    country_entries), so a wrong code in Row 18 does not also cost the rate
    point. If the country couldn't be resolved, we fall back to the student's
    typed code in Row 18.

    Scoring (same as V1 actual code behavior):
      - Accuracy: within +/-5% of live rate -> 1.0 pt each (max 4.0)
      - Formatting: must show 3 decimals -> 0.25 pt each (max 1.0)

    Returns:
      (total_score, accuracy_score, format_score, feedback)
        feedback is list[(code, params)]
    """

    # Allow reuse of fetched rates (so later wrapper can fetch once)
    if live_rates is None:
        live_rates, err = fetch_live_usd_rates()
        if err:
            return 0.0, 0.0, 0.0, [("CC19_API_FETCH_FAILED", {"error": err})]

    feedback = []

    accuracy_score = 0.0
    format_score = 0.0

    code_cells = ["C18", "D18", "E18", "F18"]
    rate_cells = ["C19", "D19", "E19", "F19"]

    for idx, (code_cell, rate_cell) in enumerate(zip(code_cells, rate_cells)):
        raw_code = sheet[code_cell].value
        raw_rate = sheet[rate_cell].value

        student_code = str(raw_code).strip().upper() if raw_code else ""
        student_rate = raw_rate if isinstance(raw_rate, (int, float)) else None

        # --- Determine the anchor currency (consistency) ---
        # Prefer the currency of the country the student chose; fall back to the
        # student's typed code if the country couldn't be resolved.
        anchor_code = None
        if country_entries and idx < len(country_entries) and country_entries[idx]:
            cc = country_entries[idx].get("currency_code")
            if cc and cc in live_rates:
                anchor_code = cc
        if anchor_code is None and student_code in live_rates:
            anchor_code = student_code

        # --- Validate the rate against the anchor currency ---
        if anchor_code is None:
            if not student_code:
                feedback.append(("CC19_CODE_MISSING", {"code_cell": code_cell, "rate_cell": rate_cell}))
            else:
                feedback.append(("CC19_CODE_INVALID", {"code_cell": code_cell, "code": student_code}))
        else:
            true_rate = live_rates[anchor_code]
            lower = true_rate * 0.95
            upper = true_rate * 1.05

            if student_rate is None:
                feedback.append(("CC19_RATE_NOT_NUMERIC", {"rate_cell": rate_cell}))
            else:
                if lower <= float(student_rate) <= upper:
                    accuracy_score += 1.0
                    feedback.append((
                        "CC19_RATE_WITHIN_TOLERANCE",
                        {
                            "rate_cell": rate_cell,
                            "student_rate": float(student_rate),
                            "true_rate": float(true_rate),
                            "tolerance": "+/-5%"
                        }
                    ))
                else:
                    feedback.append((
                        "CC19_RATE_OUTSIDE_TOLERANCE",
                        {
                            "rate_cell": rate_cell,
                            "student_rate": float(student_rate),
                            "true_rate": float(true_rate),
                            "tolerance": "+/-5%"
                        }
                    ))

        # --- Formatting check (3 decimals) ---
        number_format = sheet[rate_cell].number_format
        fmt = str(number_format) if number_format is not None else ""
        fmt_norm = fmt.replace('"', "").lower()

        # Accept explicit 0.000 format OR a value that actually has 3+ decimal digits
        has_format_code = ("0.000" in fmt_norm) or ("#.000" in fmt_norm)
        has_3_decimals = False
        if isinstance(student_rate, (int, float)):
            rate_str = str(float(student_rate))
            if '.' in rate_str:
                decimal_digits = len(rate_str.split('.')[1].rstrip('0'))
                has_3_decimals = decimal_digits >= 3

        if has_format_code or has_3_decimals:
            format_score += 0.25
            feedback.append(("CC19_FORMAT_OK", {"rate_cell": rate_cell}))
        else:
            feedback.append(("CC19_FORMAT_BAD", {"rate_cell": rate_cell}))

    total_score = round(accuracy_score + format_score, 2)

    # Summary line (still code-based)
    feedback.insert(0, (
        "CC19_SUMMARY",
        {
            "accuracy": round(accuracy_score, 2),
            "accuracy_possible": 4.0,
            "formatting": round(format_score, 2),
            "formatting_possible": 1.0,
            "total": total_score,
            "total_possible": 5.0
        }
    ))

    return total_score, round(accuracy_score, 2), round(format_score, 2), feedback
