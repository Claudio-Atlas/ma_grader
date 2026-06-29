#!/usr/bin/env python3
"""
MA2 grading-logic audit.

Throws a battery of mathematically-EQUIVALENT correct formulas (and some clearly
wrong ones) at each formula-checking grader, then reports which correct variants
get rejected (FALSE NEGATIVES — students lose points unfairly) and which wrong
variants get accepted (FALSE POSITIVES — wrong answers get credit).

This changes NO grading logic — it only measures it. Run from the engine root:

    python3 tests/ma2_audit.py
"""

import os
import sys

# Make the engine importable when run from anywhere.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from openpyxl import Workbook

from graders.ma2_income_projection.grade_monthly_income import grade_monthly_income
from graders.ma2_income_projection.grade_five_year_income import grade_five_year_income
from graders.ma2_income_projection.grade_inflation_rate import grade_inflation_rate
from graders.ma2_income_projection.grade_projected_cpi import grade_projected_cpi
from graders.ma2_income_projection.grade_current_income_reference import grade_current_income_reference
from graders.ma2_student_loans.grade_unsubsidized_setup import grade_unsubsidized_setup
from graders.ma2_annual_budget.grade_budget_row28 import grade_budget_row28
from graders.ma2_annual_budget.grade_budget_row26 import grade_budget_row26
from graders.ma2_annual_budget.grade_budget_row27 import grade_budget_row27
from graders.ma2_annual_budget.grade_budget_row30_32 import grade_budget_row30, grade_budget_row32


def _ws(cells):
    """Build a throwaway worksheet with the given {cell: value} map."""
    wb = Workbook()
    ws = wb.active
    for ref, val in cells.items():
        ws[ref] = val
    return ws


# Each case: how to score a candidate formula, the max points, and batteries of
# equivalent (should be full) and wrong (should NOT be full) formulas.
CASES = [
    {
        "name": "Projected Monthly Income (K37)",
        "max": 2,
        "run": lambda f: grade_monthly_income(_ws({"K37": f}))["points"],
        "equivalent": ["=K36/12", "=K36*1/12", "=K36*(1/12)", "=1/12*K36",
                       "=(1/12)*K36", "= K36 / 12 "],
        "wrong": ["=K36/2", "=K36*12", "=K35/12"],
    },
    {
        "name": "5-Year Projected Income (K36)",
        "max": 3,
        "run": lambda f: grade_five_year_income(_ws({"K36": f}))["points"],
        "equivalent": ["=K35*(1+K34)", "=(1+K34)*K35", "=K35*(K34+1)",
                       "=(K34+1)*K35", "=K35+K35*K34", "=K34*K35+K35"],
        "wrong": ["=K35*(1-K34)", "=K35*K34", "=K35*1+K34"],
    },
    {
        "name": "Inflation Rate (K34)",
        "max": 2,
        "run": lambda f: grade_inflation_rate(_ws({"K34": f}))["points"],
        "equivalent": ["=K33/C37-1", "=(K33-C37)/C37", "=-1+K33/C37"],
        "wrong": ["=C37/K33-1", "=K33/C37", "=1-K33/C37"],
    },
    {
        "name": "Unsub. Simple Interest (C25)",
        "max": 2,
        "run": lambda f: grade_unsubsidized_setup(
            _ws({"C24": 4, "C25": f, "C26": "=B22+C25"}))["C25"]["points"],
        "equivalent": ["=B22*B23*C24", "=C24*B23*B22", "=B23*B22*C24",
                       "=B22*C24*B23"],
        "wrong": ["=B22*B23", "=B22+B23*C24"],
    },
    {
        "name": "Unsub. New Principal (C26)",
        "max": 2,
        "run": lambda f: grade_unsubsidized_setup(
            _ws({"C24": 4, "C25": "=B22*B23*C24", "C26": f}))["C26"]["points"],
        "equivalent": ["=B22+C25", "=C25+B22", "=B22*(1+B23*C24)",
                       "=(1+B23*C24)*B22", "=B22*(1+C24*B23)"],
        "wrong": ["=B22-C25", "=C25"],
    },
    {
        "name": "Total Annual Budget (D28)",
        "max": 3,
        "run": lambda f: grade_budget_row28(_ws({"D28": f}))["total_points"],
        # The rubric explicitly requires the SUM() function, so the expanded
        # +chain is intentionally NOT full credit (a structural requirement,
        # not a false negative).
        "equivalent": ["=SUM(D18:D27)", "=sum(D18:D27)"],
        "wrong": ["=SUM(D18:D26)", "=SUM(D17:D27)"],
        "structural_reject": ["=D18+D19+D20+D21+D22+D23+D24+D25+D26+D27"],
    },
    {
        "name": "Projected CPI (K33)",
        "max": 3,
        "run": lambda f: grade_projected_cpi(_ws({"K33": f}))["points"],
        "equivalent": ["=H19*K32+H20", "=K32*H19+H20", "=H20+H19*K32",
                       "=H20+K32*H19", "=H19*(K32)+H20"],
        "wrong": ["=H19*K32-H20", "=H19+K32+H20"],
    },
    {
        "name": "Current Income ref (K35)",
        "max": 1,
        "run": lambda f: grade_current_income_reference(_ws({"K35": f, "B11": 50000}))["points"],
        "equivalent": ["=B11", "=+B11", "=(B11)"],
        "wrong": ["=B12", "=C11"],
    },
    {
        "name": "Budget annual cost D26",
        "max": 2,
        "run": lambda f: grade_budget_row26(_ws({"B26": 12, "C26": "='Student Loan'!B29", "D26": f}))["total_points"] - 3,
        "equivalent": ["=B26*C26", "=C26*B26"],
        "wrong": ["=B26+C26", "=B26"],
    },
    {
        "name": "Projected Total 5yr D30",
        "max": 3,
        "run": lambda f: grade_budget_row30(_ws({"D30": f}))["total_points"],
        "equivalent": ["=D28*(1+D29)", "=(1+D29)*D28", "=D28+D28*D29", "=D28*D29+D28"],
        "wrong": ["=D28*(1-D29)", "=D28*D29"],
    },
    {
        "name": "Remaining Total D32",
        "max": 2,
        "run": lambda f: grade_budget_row32(_ws({"D32": f}))["total_points"],
        "equivalent": ["=D31-D30", "=-D30+D31"],
        "wrong": ["=D30-D31", "=D31+D30"],
    },
]


def run():
    false_neg = 0
    false_pos = 0
    print("=" * 74)
    print("MA2 GRADING AUDIT — equivalent-answer coverage")
    print("=" * 74)
    for case in CASES:
        mx = case["max"]
        print(f"\n{case['name']}   (full credit = {mx})")
        print("-" * 60)
        for f in case["equivalent"]:
            pts = case["run"](f)
            full = pts == mx
            flag = "" if full else "   <-- FALSE NEGATIVE (correct, marked down)"
            if not full:
                false_neg += 1
            print(f"  correct  {f:<42} {pts}/{mx}{flag}")
        for f in case["wrong"]:
            pts = case["run"](f)
            full = pts == mx
            flag = "   <-- FALSE POSITIVE (wrong, full credit)" if full else ""
            if full:
                false_pos += 1
            print(f"  wrong    {f:<42} {pts}/{mx}{flag}")
        for f in case.get("structural_reject", []):
            pts = case["run"](f)
            note = "(rubric requires this form — correctly not credited)"
            print(f"  struct   {f:<42} {pts}/{mx}   {note}")
    print("\n" + "=" * 74)
    print(f"SUMMARY:  {false_neg} false negatives (correct answers marked down),  "
          f"{false_pos} false positives (wrong answers credited)")
    print("=" * 74)
    return false_neg, false_pos


if __name__ == "__main__":
    run()
