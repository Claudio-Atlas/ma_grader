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
def normalize_unit_text(val):
    """
    Normalizes unit strings used across Unit Conversions.
    - Strips spaces
    - Lowercases
    - Normalizes hr -> h, day -> d, year -> yr
    - Normalizes slashes: e.g., 'mcg/mg' stays 'mcg/mg'
    """
    if val is None:
        return ""

    s = str(val).strip().lower()

    # Remove spaces
    s = s.replace(" ", "")

    # Normalize time units
    s = s.replace("hr", "h")
    s = s.replace("day", "d")
    s = s.replace("year", "yr")

    # If student typed y/ -> assume yr/
    if s.startswith("y/"):
        s = s.replace("y/", "yr/")

    return s


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
