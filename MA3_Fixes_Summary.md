# MA3 Autograder — Issue Review & Fixes

Thanks for the detailed MA3 feedback. Below is the full status of every item,
split into **Round 1 (clear bugs)** — cases where a correct answer was marked
wrong or a count was reported incorrectly — and **Round 2 (scoring/judgment
calls)** — where we adjusted how partial credit and chart scoring work. Every
change is verified with targeted tests, and a full MA3 run (17 students)
completes cleanly.

---

## Round 1 — Clear bugs (false negatives / miscounts)

### Analysis tab

**I18 rejected `=H18-G18`** — **Fixed.** For the Mean of the Differences,
mean(after) − mean(before) equals the mean of the differences exactly, so
`=H18-G18` now earns full credit (previously only an `AVERAGE(...)` formula was
accepted).

### Visualization tab

**Dollar signs marked correct formulas wrong (D28, E28)** — **Fixed.**
Absolute/mixed references such as `=$E$22` (Lower Limit) and `=D28+E$24` (Upper
Limit) weren't recognized, so the cell was marked wrong even though the formula
was correct. This was also the cause of the **"6 out of 12 points deducted"**
case: a student who used a `$` down the whole Upper Limit column lost that entire
6-point column. The checker now ignores `$` signs.

**Bin width (E24) accepted any divisor** — **Fixed.** The grader only checked
that a division existed, so wrong bin widths like `/5`, `/10`, and `/50` — and
even the precedence-broken `=E23-E22/11` — all passed. It now requires dividing
the range by **11** (the number of bins), with the subtraction properly grouped.

**Spill / array formulas only credited the first row** — **Fixed.** A single
dynamic-array formula that fills the whole column (the relative-frequency
`=G28:G38/50`, an array `=FREQUENCY(B12:B61,E28:E37)`, or an array `COUNTIFS`)
was only credited in the top cell, so the student lost ~10 of 11 rows and got
spurious "row 29 is incorrect" errors. The grader now credits all 11 rows for a
valid array/spill formula. (A normal per-row `COUNTIFS` is still graded row-by-row.)

**Bin title (F column) rejected `=AVERAGE(...)`** — **Fixed.** `=AVERAGE(D28:E28)`
gives the identical midpoint to `=(D28+E28)/2` and is now accepted.

**Formatting reported phantom correct cells** — **Fixed.** On a sheet with no
formatting applied, the grader reported "11 of 58 cells formatted correctly"
because it counted Excel's default "General" format as correct. "General"/
unformatted cells no longer count, and the feedback now reports each formatting
group with how many cells are correct, so the count and the details match.

---

## Round 2 — Scoring adjustments (judgment calls)

**Empirical-rule bounds G36/G37 — `=G18-STDEV.S(D14:D63)` scored 0/6.**
**Changed to graded partial credit.** The bounds describe the *differences*, so
both the mean and the standard deviation must be on the differences. This student
got the structure and the standard deviation right, but used the mean of the
*Before* scores (G18) instead of the mean of the differences (I18) — which puts
the bound on the wrong scale (~67 instead of ~−0.5). It now grades on four tiers,
per bound cell (3 pts each):

- **Full (3/3):** mean and stdev both of the differences (`I18`/`AVERAGE(D…)` and
  `I20`/`STDEV(D…)`), correct sign — including `=I18-STDEV.S(D14:D63)` and `=H18-G18` as the mean.
- **Near-miss (2/3):** correct structure and correct difference-stdev, but the
  mean references the wrong dataset (Before/After). *This is where the reported
  `=G18-STDEV.S(...)` lands — it now earns 4 of 6 instead of 0.*
- **Structure only (1.5/3):** right shape but wrong references, or right pieces
  with the wrong +/− sign.
- **None (0/3):** hardcoded numbers, missing, or not a formula.

**Histogram scored a wrong chart too high (a bad chart got 5/6).**
**Rebuilt the 6-point rubric** so presentation points can't rescue a chart that
plots the wrong data:

- Bar/column chart exists — 1.0
- Values reference the Frequency column (G) — 2.0
- Category labels reference the Bin titles (F) — 1.0
- **Gap width = 0%** (a real histogram, not a gapped bar chart) — 0.5
- Chart title present and **not a placeholder** ("Title of Bin", "Chart Title") — 0.5
- X-axis (valid, **not a placeholder** and not "Frequency") + Y-axis titles — 0.5 (0.25 each)

Most importantly, **if the chart doesn't actually plot the Frequency data
(missing, wrong type, or wrong data range), the whole histogram score is capped
at 2 points** — so a well-labeled chart of the wrong data can no longer reach 5/6.
Gap width is now checked (a gapped bar chart loses that half-point), and
placeholder titles / "Title of Bins" axis labels no longer earn credit.

**Frequency boundary / final bin (`<=` vs `<`) was never checked.**
**Added a value-based check.** The grader now confirms the frequencies actually
count every one of the 50 data values. With no buffer on the maximum, a strict
`<` on the final bin drops the max (total = 49); a wrong lower operator (`>`
instead of `>=`) drops more. Credit for the Frequency column is now capped at
`11 − (number of uncounted values)`, so the penalty scales with how many values
were dropped, and the feedback points at the `<=` / `>=` fix. (Students who
buffered the max and total 50 are unaffected.)

**Written analysis (68% / "34 of 50").** No change — the written response is
extracted and left for **manual grading** as before (the grader copies the text
into the grading sheet for your review rather than auto-scoring it).

---

### Summary

- **Round 1 — fixed false negatives/miscounts:** I18 `=H18-G18`; the `$`/mixed-ref
  bug on the Lower/Upper Limits (incl. the 6/12 cascade); bin-width divisor
  validation; spill/array crediting for Frequency and Relative Frequency;
  `=AVERAGE(...)` bin-midpoint titles; the formatting miscount.
- **Round 2 — scoring adjustments:** empirical-rule partial-credit tiers;
  histogram rubric with gap-width, placeholder rejection, and a 2-point cap for
  wrong-data charts; value-based frequency boundary/undercount check.
- **Left as manual grading by design:** the written analysis (68% interpretation).
