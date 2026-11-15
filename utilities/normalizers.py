# utilities/normalizers.py

"""
Shared normalization functions for formulas and units used across all
Unit Conversion grading modules and other MA1 grading logic.

This centralizes behavior so row checkers stay clean and consistent.
"""

import re


# ------------------------------
# FORMULA NORMALIZATION
# ------------------------------
def normalize_formula(val):
    """
    Normalizes an Excel formula string by:
    - Converting to string
    - Removing $, spaces, surrounding parentheses
    - Converting to uppercase
    - Standardizing operator spacing
    """
    if val is None:
        return ""

    s = str(val).strip()

    # Remove absolute reference symbols
    s = s.replace("$", "")

    # Remove spaces
    s = s.replace(" ", "")

    # Remove wrapping parentheses around the entire expression
    # Example: ((B30*D19)+B31) -> (B30*D19)+B31 -> B30*D19+B31
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]

    # Convert to uppercase
    s = s.upper()

    # Collapse double parentheses (( -> (
    s = s.replace("((", "(")
    s = s.replace("))", ")")

    return s


# ------------------------------
# UNIT NORMALIZATION
# ------------------------------
# Spelled-out, plural and alternate unit names -> the short form the graders
# compare against (e.g. "inch" -> "in", "hrs" -> "h", "lbs" -> "lb").
_UNIT_ALIASES = {
    "h": "h", "hr": "h", "hrs": "h", "hour": "h", "hours": "h",
    "d": "d", "day": "d", "days": "d",
    "y": "yr", "yr": "yr", "yrs": "yr", "year": "yr", "years": "yr",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
    "in": "in", "ins": "in", "inch": "in", "inches": "in",
    "ft": "ft", "foot": "ft", "feet": "ft",
    "mi": "mi", "mile": "mi", "miles": "mi",
    "cm": "cm", "centimeter": "cm", "centimeters": "cm",
    "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
    "l": "l", "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "gal": "gal", "gallon": "gal", "gallons": "gal",
    "ml": "ml", "milliliter": "ml", "milliliters": "ml",
    "tsp": "tsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "mg": "mg", "milligram": "mg", "milligrams": "mg",
    "mcg": "mcg", "microgram": "mcg", "micrograms": "mcg",
}


def _normalize_unit_token(tok):
    """One side of a ratio label, e.g. "inch (in)" -> "in", "2.54 cm" -> "cm",
    "hrs" -> "h", "in^2" -> "in^2". Unknown words are left as typed."""
    t = re.sub(r"\(.*?\)", "", tok)                  # "(in)" notes
    t = re.sub(r"(?<!\^)\d+(?:\.\d+)?", "", t)       # numbers like 2.54, 365 (not ^2)
    t = t.replace(" ", "")
    m = re.fullmatch(r"([a-z]+)(\^\d+)?", t)
    if not m:
        return tok.replace(" ", "")
    base, exp = m.group(1), m.group(2) or ""
    return _UNIT_ALIASES.get(base, base) + exp


def normalize_unit_text(val):
    """
    Normalizes unit labels used across Unit Conversions to the short form the
    graders compare against, so the same unit written differently matches:
        "inch (in)/cm" -> "in/cm"     "in/2.54 cm" -> "in/cm"
        "yr/365 d"     -> "yr/d"      "d/hrs"      -> "d/h"
        "ft/hrs"       -> "ft/h"      "lb/in^2"    -> "lb/in^2"
    Each side of the "/" is normalized on its own; exponents (^2) are kept.
    """
    if val is None:
        return ""

    s = str(val).strip().lower()
    if not s:
        return ""
    return "/".join(_normalize_unit_token(part) for part in s.split("/"))


# ------------------------------
# ROW-SPECIFIC NORMALIZATION HELPERS
# ------------------------------

def normalize_time_unit(unit):
    """
    Normalizes time-based units for Rows 27 + 29.
    """
    if not unit:
        return ""

    u = unit.lower().replace(" ", "")
    u = u.replace("hr", "h")
    u = u.replace("day", "d")
    u = u.replace("year", "yr")

    # If student typed y/ -> assume yr/
    if u.startswith("y/"):
        u = u.replace("y/", "yr/")

    return u


def normalize_temp_formula(val):
    """
    More permissive normalization for temperature formulas,
    allowing variations of (5/9), 5/9, etc.
    """
    if val is None:
        return ""

    s = str(val).strip().replace(" ", "").replace("$", "").upper()

    # Remove extra parentheses
    while s.startswith("(") and s.endswith(")"):
        s = s[1:-1]

    return s
