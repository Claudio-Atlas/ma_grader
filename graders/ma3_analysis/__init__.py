"""
ma3_analysis — Graders for MA3 Analysis tab

This package contains modules for grading the Analysis worksheet:
- Name entry (B10)
- Difference calculations (D14:D63)
- Statistics formulas (Mean, Median, StdDev, Range)
- Percentile formulas
- Empirical rule formulas
- Written analysis (for manual grading)
- Formatting checks
"""

from .grade_analysis import grade_analysis_tab
from .check_name import check_name
from .check_differences import check_differences
from .check_statistics import check_statistics
from .check_percentiles import check_percentiles
from .check_empirical_rule import check_empirical_rule
from .check_written_analysis import check_written_analysis
from .check_formatting import check_analysis_formatting

__all__ = [
    "grade_analysis_tab",
    "check_name",
    "check_differences",
    "check_statistics",
    "check_percentiles",
    "check_empirical_rule",
    "check_written_analysis",
    "check_analysis_formatting",
]
