"""
ma3_visualization — Graders for MA3 Visualization tab

This package contains modules for grading the Visualization worksheet:
- Bin table (Min, Max, Width)
- Frequency distribution (Lower/Upper limits, Title, Frequency, Relative Frequency)
- Histogram (bar chart with proper data and labels)
- Formatting checks
"""

from .grade_visualization import grade_visualization_tab
from .check_bin_table import check_bin_table
from .check_freq_dist import check_freq_dist_limits, check_freq_dist_values
from .check_histogram import check_histogram
from .check_formatting import check_visualization_formatting

__all__ = [
    "grade_visualization_tab",
    "check_bin_table",
    "check_freq_dist_limits",
    "check_freq_dist_values",
    "check_histogram",
    "check_visualization_formatting",
]
