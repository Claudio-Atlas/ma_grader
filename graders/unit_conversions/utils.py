"""
utils.py — Shared utility functions for Unit Conversions graders

Purpose: Provides a thin wrapper layer that exposes shared normalization utilities
         to all Unit Conversions row checkers. This allows grading modules to stay
         self-contained while using the centralized normalizer functions.

Author: Clayton Ragsdale
Dependencies: utilities.normalizers

Note: The actual normalization logic lives in utilities/normalizers.py to ensure
      consistency across all grading modules. This file simply re-exports those
      functions with shorter names for convenience.
"""

from typing import Any

from utilities.normalizers import (
    normalize_formula,
    normalize_unit_text,
    normalize_time_unit,
    normalize_temp_formula
)


def norm_formula(val: Any) -> str:
    """
    Normalize an Excel formula for comparison.
    
    Wrapper for shared normalize_formula function. Applies the following:
        - Converts to string
        - Removes $, spaces, surrounding parentheses
        - Converts to uppercase
    
    Args:
        val: The formula value from an Excel cell (str, None, or other)
    
    Returns:
        str: Normalized formula string, or empty string if None
    
    Example:
        >>> norm_formula("= $L$14 / $I$14 ")
        "=L14/I14"
    """
    return normalize_formula(val)


def norm_unit(val: Any) -> str:
    """
    Normalize a unit label for comparison.
    
    Wrapper for shared normalize_unit_text function. Applies the following:
        - Converts to string
        - Strips whitespace
        - Lowercases
        - Normalizes time units (hr→h, day→d, year→yr)
    
    Args:
        val: The unit text from an Excel cell (str, None, or other)
    
    Returns:
        str: Normalized unit string, or empty string if None
    
    Example:
        >>> norm_unit("mcg / mg")
        "mcg/mg"
        >>> norm_unit("hours/day")
        "h/d"
    """
    return normalize_unit_text(val)


def norm_time_unit(val: Any) -> str:
    """
    Normalize a time-based unit for comparison.
    
    Wrapper for shared normalize_time_unit function. Specifically designed
    for time units used in rows 27 and 29. Applies:
        - Converts to string
        - Strips whitespace
        - Lowercases
        - Normalizes: hr→h, day→d, year→yr
    
    Args:
        val: The unit text from an Excel cell (str, None, or other)
    
    Returns:
        str: Normalized time unit string, or empty string if None
    
    Example:
        >>> norm_time_unit("hours/day")
        "h/d"
        >>> norm_time_unit("year/d")
        "yr/d"
    """
    return normalize_time_unit(val)


def norm_temp_formula(val: Any) -> str:
    """
    Normalize a temperature conversion formula for comparison.
    
    Wrapper for shared normalize_temp_formula function. More permissive
    normalization designed for temperature formulas that may use various
    valid representations of fractions like (5/9), 5/9, etc.
    
    Args:
        val: The formula value from an Excel cell (str, None, or other)
    
    Returns:
        str: Normalized formula string, or empty string if None
    
    Example:
        >>> norm_temp_formula("=(5/9)*(A40-32)")
        "5/9*(A40-32)"
    """
    return normalize_temp_formula(val)
