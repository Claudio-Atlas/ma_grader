#!/usr/bin/env python3
"""
Regression checks for grading issues instructors reported (v1.4 issue lists).

Each case is a formula that was graded wrong; this asserts the corrected
behavior. Run from the engine root:

    python3 tests/reported_issues.py
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from openpyxl import Workbook

from utilities.xl import strip_future_prefixes
from graders.currency_conversion.row20_budget_conversion_v2 import grade_row20_budget_conversion_v2
from graders.ma3_analysis.check_empirical_rule import _bound_credit, check_empirical_rule
from graders.ma3_analysis.check_written_analysis import check_written_analysis
from graders.ma3_visualization.check_bin_table import _check_min_formula
from graders.ma3_visualization.check_freq_dist import (
    _check_frequency_formula, _check_relative_freq_formula, check_freq_dist_values,
)

failures = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label}: got {got!r}, want {want!r}")
    if not ok:
        failures.append(label)


print("MA1 · Currency Conversion C20:F20")
for label, tmpl, want in [
    ("text string =\"MXN \"&(C19*B4) gets no credit", '="MXN "&({r}*B4)', 0.0),
    ("=B4*C19 full credit", "=B4*{r}", 8.0),
    ("=ROUND(B4*C19,2) full credit", "=ROUND(B4*{r},2)", 8.0),
]:
    ws = Workbook().active
    ws["B4"] = 500
    for c in "CDEF":
        ws[f"{c}19"] = 20.1
        ws[f"{c}20"] = tmpl.format(r=f"{c}19")
    check(label, grade_row20_budget_conversion_v2(ws)[1], want)

print("MA3 · Analysis G36:G37")
check("=I18-1*(I20) lower", _bound_credit("=I18-1*(I20)", True), 1.0)
check("=I18+1*(I20) upper", _bound_credit("=I18+1*(I20)", False), 1.0)
wb = Workbook()
ws = wb.active
ws["G36"] = "=AVERAGE(D14:D63)-_xlfn.STDEV.S(D14:D63)"   # as Excel saves it
ws["G37"] = "=AVERAGE(D14:D63)+_xlfn.STDEV.S(D14:D63)"
strip_future_prefixes(wb)
check("=AVERAGE(D14:D63)-STDEV.S(D14:D63) (saved with _xlfn.)", check_empirical_rule(ws)[0], 6.0)

print("MA3 · Written analysis mentioning 68%")
ws = Workbook().active
ws["C41"] = ("According to the empirical rule, approximately 68% of the students should expect "
             "to see an increase in their scores between 0.91 and 4.84 points.")
check("answer containing '68%' is found", check_written_analysis(ws)[1][0][0], "WRITTEN_FOUND")

print("MA3 · Visualization")
check("G: =COUNTIFS(B12:B61,D28:D38,...) rejected",
      _check_frequency_formula("=COUNTIFS(B12:B61, D28:D38, B12:B61, E28:E38)", spill=True), False)
check("G: comparison COUNTIFS accepted",
      _check_frequency_formula('=COUNTIFS($B$12:$B$61,">="&D30,$B$12:$B$61,"<"&E30)', 30), True)
check("H: dragged =G29/SUM(G29:G39) rejected", _check_relative_freq_formula("=G29/SUM(G29:G39)", 29), False)
check("H: =G29/SUM(G$28:G$38) accepted", _check_relative_freq_formula("=G29/SUM(G$28:G$38)", 29), True)
check("H: dragged =G29/COUNT(B14:B62) rejected", _check_relative_freq_formula("=G29/COUNT(B14:B62)", 29), False)
check("H: =G29/COUNT(B$12:B$61) accepted", _check_relative_freq_formula("=G29/COUNT(B$12:B$61)", 29), True)
check("E22: =MIN(Analysis!D14:D63)-0.1 accepted", _check_min_formula("=MIN(Analysis!D14:D63)-0.1"), True)

ws = Workbook().active
for r in range(28, 39):
    ws[f"F{r}"] = f"=(D{r}+E{r})/2"
    ws[f"G{r}"] = f'=COUNTIFS($B$12:$B$61,">="&D{r},$B$12:$B$61,"<"&E{r})'
    ws[f"H{r}"] = f"=G{r}/SUM(G$28:G$38)"
check("fully correct table scores 18", check_freq_dist_values(ws)[0], 18.0)

print("MA1 · Unit Conversions (Nov 2026 review)")
from utilities.normalizers import normalize_unit_text
from graders.unit_conversions.utils import has_typed_number, norm_formula
for label, want in [("inch (in)/cm", "in/cm"), ("in/2.54 cm", "in/cm"), ("yr/365 d", "yr/d"),
                    ("d/24 h", "d/h"), ("ft/hrs", "ft/h"), ("kg/cm^2", "kg/cm^2"), ("lbs/kg", "lb/kg")]:
    check(f"unit label {label!r}", normalize_unit_text(label), want)
check("=F26*I26 has no typed starting value", has_typed_number(norm_formula("=F26*I26")), False)
check("=18*F26*I26 has a typed starting value", has_typed_number(norm_formula("=18*F26*I26")), True)

print("MA3 · Class review (Nov 2026)")
import tempfile
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, MultiLevelStrRef
from utilities.xl import has_cached_values
from graders.ma3_analysis.check_statistics import _check_mean_formula, _check_range_formula
from graders.ma3_visualization.check_bin_table import _check_width_formula
from graders.ma3_visualization.check_histogram import _is_placeholder_title, check_histogram
from graders.ma3_visualization.grade_visualization import grade_visualization_tab

# 1. Relative frequency over a fixed total
wb = Workbook()
ws = wb.active
ws["I38"] = "=SUM(G28:G38)"
ws["J38"] = 50
ws["K38"] = "=AVERAGE(G28:G38)"
ws["H28"] = "=G28/(SUM(_xlfn.ANCHORARRAY($G$28)))"   # as Excel saves G28#
strip_future_prefixes(wb)
check("H: =G28/$I$38 (I38 =SUM(G28:G38)) accepted", _check_relative_freq_formula("=G28/$I$38", 28, ws), True)
check("H: =G29/I$38 accepted", _check_relative_freq_formula("=G29/I$38", 29, ws), True)
check("H: =G28/$J$38 (J38 holds 50) accepted", _check_relative_freq_formula("=G28/$J$38", 28, ws), True)
check("H: =G28/I38 (relative total cell) rejected", _check_relative_freq_formula("=G28/I38", 28, ws), False)
check("H: =G29/$K$38 (not a total) rejected", _check_relative_freq_formula("=G29/$K$38", 29, ws), False)
check("H: =G28/(SUM(ANCHORARRAY($G$28))) accepted", _check_relative_freq_formula(ws["H28"].value, 28, ws), True)
check("H: =G28/SUM(G28#) accepted", _check_relative_freq_formula("=G28/SUM(G28#)", 28, ws), True)

# 2. Bin width divisor counted from the table, and files without cached values
check("E24: =(E23-E22)/ROWS(D28:D38) accepted", _check_width_formula("=(E23-E22)/ROWS(D28:D38)"), True)
check("E24: =(E23-E22)/COUNT(E28:E38) accepted", _check_width_formula("=(E23-E22)/COUNT(E28:E38)"), True)
check("E24: =(E23-E22)/COUNTA(F28:F38) accepted", _check_width_formula("=(E23-E22)/COUNTA(F28:F38)"), True)
check("E24: =(E23-E22)/ROWS(D28:D37) rejected", _check_width_formula("=(E23-E22)/ROWS(D28:D37)"), False)
check("E24: =(E23-E22)/ROWS(D28:E38) rejected", _check_width_formula("=(E23-E22)/ROWS(D28:E38)"), False)
with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "no_cache.xlsx")
    wb = Workbook()
    wb.active.title = "Visualization"
    wb.active["B12"] = 1.5
    wb.active["E22"] = "=MIN(B12:B61)"   # openpyxl saves no calculated values
    wb.save(path)
    wb_f, wb_v = load_workbook(path), load_workbook(path, data_only=True)
    check("workbook saved without calculated values is detected", has_cached_values(wb_f, wb_v), False)
    fb = grade_visualization_tab(wb_f.active, wb_v.active, cached_values=False)["freqdist_feedback"]
    check("frequency row gets the no-cached-values note", any(c == "VIZ_NO_CACHED_VALUES" for c, _ in fb), True)

# 3. Placeholder titles only when the whole title is a placeholder
for title, want in [("Change in Test Score (Title of Bin)", False), ("Title of Bin", True),
                    ("Title of Bins", True), ("Chart Title", True), ("Axis Title", True), ("title of bin ", True)]:
    check(f"placeholder {title!r}", _is_placeholder_title(title), want)

# 4. Statistics ranges: one extra empty row is fine, skipped data rows aren't
check("=AVERAGE(B14:B64) full credit", _check_mean_formula("=AVERAGE(B14:B64)", "G"), 1.0)
check("=(MAX(B14:B63)-(MIN(B14:B64))) full credit", _check_range_formula("=(MAX(B14:B63)-(MIN(B14:B64)))", "G"), 1.0)
check("=MAX(B14:B63)-MIN(B16:B63) charged", _check_range_formula("=MAX(B14:B63)-MIN(B16:B63)", "G"), 0.75)
check("=MAX(B14:B62)-MIN(B14:B62) charged", _check_range_formula("=MAX(B14:B62)-MIN(B14:B62)", "G"), 0.75)
check("=AVERAGE(B15:B64) charged", _check_mean_formula("=AVERAGE(B15:B64)", "G"), 0.75)
check("=AVERAGE(B14:B63) full credit", _check_mean_formula("=AVERAGE(B14:B63)", "G"), 1.0)


# 5. Chart edge cases
def histogram(build):
    ws = Workbook().active
    chart = BarChart()
    chart.title, chart.x_axis.title, chart.y_axis.title = "Change in Scores", "Change", "Frequency"
    chart.gapWidth = 0
    build(ws, chart)
    ws.add_chart(chart, "J2")
    score, fb = check_histogram(ws)
    return score, [c for c, _ in fb]


def two_column_labels(ws, chart):
    chart.add_data(Reference(ws, min_col=7, min_row=28, max_row=38))
    chart.series[0].cat = AxDataSource(multiLvlStrRef=MultiLevelStrRef(f="Visualization!$F$28:$G$38"))


def two_series(ws, chart):
    chart.add_data(Reference(ws, min_col=6, min_row=28, max_row=38))
    chart.add_data(Reference(ws, min_col=7, min_row=28, max_row=38))


score, codes = histogram(two_column_labels)
check("labels from F28:G38: half label credit", score, 5.5)
check("labels from F28:G38: says to use only F28:F38", "HIST_LABELS_TWO_COLUMNS" in codes, True)
score, codes = histogram(two_series)
check("series F and G, no labels: frequency credited", score, 5.0)
check("series F and G: says to remove the extra series", "HIST_EXTRA_SERIES" in codes and "HIST_CAPPED" not in codes, True)

print("MA3 · Bin table showing #REF!")
from graders.ma3_visualization.check_bin_table import check_bin_table
ws_f, ws_v = Workbook().active, Workbook().active
ws_f["E22"], ws_f["E23"], ws_f["E24"] = "=MIN(B12:B61)-0.1", "=MAX(B12:B61)+0.1", "=(E23-E22)/11"
for c in ("E22", "E23", "E24"):
    ws_v[c] = "#REF!"
score, fb = check_bin_table(ws_f, ws_v)
check("right formulas but #REF! values earn nothing", score, 0.0)
check("feedback says the cell shows #REF!", any(c == "BIN_VALUE_ERROR" for c, _ in fb), True)
ws_v["E22"], ws_v["E23"], ws_v["E24"] = -0.6, 8.9, (8.9 + 0.6) / 11
check("same formulas with real values keep full credit", check_bin_table(ws_f, ws_v)[0], 6.0)

print("MA2 · Class review (Nov 2026)")
from graders.ma2_annual_budget.grade_budget_row26 import grade_budget_row26
from graders.ma2_annual_budget.grade_budget_row27 import grade_budget_row27
from graders.ma2_credit_cards.compute_credit_card_payoff import compute_credit_card_payoff_months
from graders.ma2_credit_cards.grade_credit_card_amortization import grade_credit_card_amortization
from graders.ma2_credit_cards.grade_credit_card_parameters import grade_credit_card_parameters
from graders.ma2_income_projection.grade_current_income_reference import grade_current_income_reference
from graders.ma2_income_projection.grade_income_projection_cpi_values import grade_income_projection_cpi_values
from graders.ma2_income_projection.grade_trendline_formulas import grade_intercept_formula
from graders.ma2_income_projection.load_cpi_data import get_cpi_value
from graders.ma2_student_loans.grade_unsubsidized_setup import _check_c24_constant
from utilities.humanize_sheet import NO_REASON_NOTE, humanize_grading_sheet
from writers.build_instructor_master_workbook import build_instructor_master_workbook

# 1. Credit card parameters typed one cell over (D17/D18 instead of C17/C18)
with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "Pat_Sample_MA2.xlsx")
    wb = Workbook()
    rnd = wb.active
    rnd.title = "Random"
    rnd["H19"], rnd["H20"], rnd["H21"], rnd["H22"] = 2150, 2.5, 20, 25
    cc = wb.create_sheet("Credit Cards")
    cc["C13"], cc["C14"], cc["C15"], cc["D17"], cc["D18"] = 0.2, 2150, 12, 0.025, 25
    months = compute_credit_card_payoff_months(2150, 0.025, 25, 20, 12)
    for i in range(months):
        r = 25 + i
        cc[f"A{r}"] = i + 1
        cc[f"B{r}"] = "=C14" if i == 0 else f"=D{r-1}+E{r-1}"
        cc[f"C{r}"] = f"=MIN(B{r},MAX(B{r}*$D$17,$D$18))"
        cc[f"D{r}"] = f"=MAX(0,B{r}-C{r})"
        cc[f"E{r}"] = f"=D{r}*$C$13/$C$15"
    wb.save(path)
    params = grade_credit_card_parameters(path)
    check("misplaced inputs: partial credit", params["total_points"], 4.0)
    check("misplaced inputs: says D17 instead of C17", "in D17 instead of C17" in params["comment"], True)
    check("misplaced inputs: located", params["locations"], {"C17": "D17", "C18": "D18"})
    check("table using D17/D18: full credit", grade_credit_card_amortization(path, params["locations"])["total_points"], 24.0)
    check("payoff month matches the review (152)", months, 152)

# 1b. A row that loses points without a reason is flagged, never the generic line;
# 3b. grader error text never reaches a comment.
ws = Workbook().active
for r, e in [(4, 6), (18, 24)]:
    ws[f"E{r}"], ws[f"F{r}"] = e, 0
ws["G4"] = "Error grading CPI section: type str doesn't define __round__ method"
problems = []
humanize_grading_sheet(ws, "MA2", "Pat Sample", problems=problems)
check("no-reason row gets the instructor note", ws["G18"].value, NO_REASON_NOTE)
check("generic fallback never used", "A few points were missed" in str(ws["G4"].value) + str(ws["G18"].value), False)
check("exception text kept out of the comment", "Error grading" in str(ws["G4"].value), False)
check("both reported as issues", [p.split(":")[0] for p in problems], ["Row 4", "Row 4", "Row 18"])

# 2. Years in school entered as =4
ws = Workbook().active
ws["C24"] = "=4"
check("C24 =4 full credit", _check_c24_constant(ws)["points"], 1)
ws["C24"] = "=5"
check("C24 =5 no credit", _check_c24_constant(ws)["points"], 0)

# 3. K35 typed as the number B11 calculates to
ws_f, ws_v = Workbook().active, Workbook().active
ws_f["B11"] = '=IF(OR(C1="Your Name Here",C2="Current Year"),"Enter your name and year.",LEN(C$1)^4+40000)'
ws_v["B11"] = 68561
ws_f["K35"] = ws_v["K35"] = 68561
res = grade_current_income_reference(ws_f, ws_v)
check("K35 typed number: half credit", res["points"], 0.5)
check("K35 typed number: says to use =B11", "typed in" in res["comment"] and "=B11" in res["comment"], True)

# 4. CPI reference data back to 2013, and the table's first row (29) checked
check("Feb 2014 CPI in reference data", get_cpi_value(2014, "Feb"), 234.781)
check("Jan 2013 CPI in reference data", get_cpi_value(2013, "Jan"), 230.28)
ws = Workbook().active
for i, r in enumerate(range(29, 38)):
    ws[f"A{r}"], ws[f"B{r}"], ws[f"C{r}"] = 2, 2014 + i, get_cpi_value(2014 + i, "Feb")
check("full CPI table from 2014 scores 6", grade_income_projection_cpi_values(ws)["points"], 6)
ws["C29"] = 234781   # decimal point dropped
res = grade_income_projection_cpi_values(ws)
check("C29 = 234781 is flagged", res["points"] < 6 and "(C29)" in res["comment"], True)

# 5. Feedback wording
ws = Workbook().active
ws["H20"] = "=-INTERCEPT(C29:C37,B29:B37)"
check("=-INTERCEPT says to remove the minus sign", "minus sign" in grade_intercept_formula(ws)["comment"], True)
ws = Workbook().active
check("empty C26 says it's empty", "(C26) is empty" in grade_budget_row26(ws)["comment"], True)
check("empty C27 says it's empty", "(C27) is empty" in grade_budget_row27(ws)["comment"], True)

# 6. Instructor master matches the grade sheet
with tempfile.TemporaryDirectory() as tmp:
    tpl = os.path.join(_ROOT, "assets_templates")
    wb = load_workbook(os.path.join(tpl, "MA2_Grading_Sheet_Template.xlsx"))
    ws = wb["Grading Sheet"]
    for r in list(range(3, 9)) + list(range(10, 16)) + list(range(17, 21)) + list(range(22, 29)):
        ws[f"F{r}"] = ws[f"E{r}"].value          # full credit everywhere...
    ws["F4"], ws["F18"] = 5.75, 20                # ...except two rows
    for r in range(40, 48):
        ws[f"F{r}"] = 1
    wb.save(os.path.join(tmp, "Pat_Sample_MA2_Grade.xlsx"))
    master = load_workbook(build_instructor_master_workbook(
        tmp, template_path=os.path.join(tpl, "Template_Master.xlsx"), assignment_type="MA2"))["Summary_Template"]
    want_total = round(25.75 / 26 * 33.25 + 33.25 + 38 / 42 * 33.25 + 33.25, 2)
    check("master Budget Total includes the pie chart (44/44)", master["H5"].value, 44)
    check("master Auto Total = grade sheet I31 (scaled)", master["B5"].value, want_total)
    check("master Credit scaled = I21", master["K5"].value, round(38 / 42 * 33.25, 2))
    check("master Credit level = H21 (90% -> 4)", master["O5"].value, 4)
    check("master paper subtotal = F48", master["Q5"].value, 8)
    check("master Final Total adds the paper", master["D5"].value, "=B5+C5+Q5")

print()
if failures:
    print(f"{len(failures)} FAILED: {failures}")
    sys.exit(1)
print("All reported issues stay fixed.")
