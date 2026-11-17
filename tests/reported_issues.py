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

print()
if failures:
    print(f"{len(failures)} FAILED: {failures}")
    sys.exit(1)
print("All reported issues stay fixed.")
