# MA1 Autograder — Issue Review & Fixes

Your colleague tested an **older version** of the autograder and reported the
items below. Here is the status of each in the **updated** grader, with what was
done. Everything is verified with targeted tests, and a full MA1 run completes
cleanly.

---

## Income Analysis

**1. Missing the 1-point formatting check on slope/intercept**
Already handled in the current version — the slope (B30) and intercept (B31)
number-formatting check (0.5 + 0.5) is graded and folded into the score.

**2. Accepts the swapped `=INTERCEPT(A19:A26,B19:B26)`**
Left as-is by decision: swapped X/Y arguments earn **2 of 3** (partial credit for
a common conceptual mistake), not full credit.

**3. Accepted hard-coded predictions like `=152*8+7`**
Already handled — a fully hard-coded formula with no cell references scores **0**.
(Note: a formula that keeps the year reference but hard-codes the slope/intercept,
e.g. `=152*D19+7`, still earns **half credit** by design.)

**4. Accepts the wrong chart type (scatter with connecting lines)**
**Fixed** — a scatter chart whose points are joined by lines now loses **1 point**.
Detection is deliberately conservative (it only triggers on a real colored line),
so a correct markers-only chart is never penalized.

**5. No check that the chart plots the correct data**
**Improved** — the grader verifies the chart uses the BLS data (columns A & B).
When the chart's data references can't be read automatically, it now **flags the
chart for manual review** (no automatic credit) instead of assuming it's correct.

**6. Predictions rejected the correct spill formula `=B30*D19:D35+B31`**
**Fixed** — the dynamic-array (spill) formula now receives full credit.

---

## Unit Conversions

**7. C40 incorrectly accepted `A40 - 32*9/5`**
Already handled — that formula scores **0**. The grader requires the `5/9`
conversion factor; `A40-32*9/5` uses `9/5` and is correctly rejected.

---

## Currency Conversion

**8. One error counted against the student 2–3 times (should check consistency)**
**Fixed with a consistency redesign.** Each step is now judged against the
student's **own previous choice** rather than re-derived from their name:
- The country they pick anchors the currency-code and exchange-rate checks.
- A wrong starting letter is penalized **once** (in the name-letters row), not
  again down the chain.
- The exchange rate is checked against the **country's** real currency, so a
  wrong currency code no longer also costs the rate point.
Net effect: a single root mistake costs one point instead of three or four.

**9. "venezuela" vs "Venezuela" — case sensitivity**
Already handled — lowercase country names now match.

**10. Does not check the formatting of the foreign currency**
**Fixed** — the foreign-currency cells (row 20) now require the proper **3-letter
currency code** in the format **and 2 decimal places**. A `$` sign (or a plain
number format) no longer earns the formatting point.

**11. Row 21 rejected `=D4*(1/E19)`**
Already handled — accepted (it's equivalent to `=D4/E19`).

**12. Row 20 rejected `=(B4*C19)`**
Already handled — accepted.

**13. `D16: 'hong kong' is not on the approved list` (it is!)**
**Fixed** — "Hong Kong" now matches the list entry "Hong Kong (China)". The
country lookup ignores parenthetical qualifiers and also tolerates obvious typos
(e.g. "Venzuela" → "Venezuela").

---

### Summary

- **Already correct in the updated version:** items 1, 3, 7, 9, 11, 12.
- **Newly fixed:** items 4, 5, 6, 8, 10, 13.
- **Kept by design decision:** item 2 (partial credit for swapped args), and the
  half-credit for hard-coded-with-reference predictions under item 3.
