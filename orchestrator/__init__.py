"""
orchestrator — Pipeline phase coordination for the MA Grader

Purpose: This package contains the main phases of the grading pipeline.
         Each phase handles a specific part of the workflow.

Author: Clayton Ragsdale
Dependencies: openpyxl, graders.*, writers.*, utilities.*

Pipeline Phases:
    - Phase 1 (grade_all): Grades all formula-based criteria for each student (MA1)
    - Phase 1 (grade_all_ma3): Grades Analysis and Visualization tabs (MA3)

Note: Chart export/insert phases (2-4) have been removed. All grading is now
      done via openpyxl without requiring Excel COM automation.
"""

from .phase1_grade_all import phase1_grade_all_students
from .phase1_grade_all_ma2 import phase1_grade_all_students_ma2
from .phase1_grade_all_ma3 import phase1_grade_all_students_ma3

__all__ = [
    "phase1_grade_all_students",
    "phase1_grade_all_students_ma2",
    "phase1_grade_all_students_ma3",
]
