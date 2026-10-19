"""
student_feedback.py — turn grader results into warm, student-facing comments.

Every grading-sheet row is written the same way:

  * full credit  -> one short line of praise specific to that row
  * lost points  -> a short opener, then one bullet per problem. Each bullet
                    names the task, keeps the cell reference in brackets so the
                    student can find it, and says how to fix it.

No scoring math ("2/2 ->"), no [ok]/[x] tags, no lists of things that passed —
the points column already says how many points were earned.

There's also an overall note for the top of the summary: rule-based by
default, optionally written by Claude from the same facts (see ai_overall_note).
"""

import json
import os
import re

BULLET = "• "


# ---------------------------------------------------------------------------
# Row comments
# ---------------------------------------------------------------------------

def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def compose(praise, points, possible, issues=None, fallback=""):
    """Comment for one grading-sheet row.

    praise:   sentence used when the row earns full credit.
    issues:   student-facing problem sentences (warm voice, cell refs in
              brackets). Empty/None means the grader didn't say why points
              were lost, so `fallback` (its legacy comment) is cleaned up and
              used instead.
    """
    pts, poss = _num(points), _num(possible)
    issues = [i.strip() for i in (issues or []) if i and i.strip()]

    if pts is not None and poss and pts >= poss - 1e-9:
        return praise
    if not issues:
        issues = legacy_issues(fallback)
    if not issues:
        return praise if pts is None else "A few points were missed here. Ask your instructor if you'd like details."

    ratio = (pts / poss) if (pts is not None and poss) else 0.0
    n = len(issues)
    if ratio >= 0.75:
        opener = "You're very close here. " + ("One thing to fix:" if n == 1 else "A few things to fix:")
    elif ratio >= 0.4:
        opener = "Good start. " + ("Here's what to fix:" if n == 1 else "Here's what to work on:")
    else:
        opener = "This part needs another look. Here's where to start:"
    return opener + "\n" + "\n".join(BULLET + i for i in issues)


# Legacy grader comments mix passes and problems ("B14 formatted correctly |
# C24 incorrect format ..."). Until every grader reports issues directly, keep
# only the segments that describe a problem.
_PASS_RE = re.compile(
    r"\b(correct(ly)?|matches|complete|valid|present|found and|ok)\b", re.I
)
_FAIL_RE = re.compile(
    r"\b(incorrect|missing|not|no|wrong|should|must|does not|doesn't|"
    r"isn't|error|blank|fix|needs?|instead)\b", re.I
)


_INSTRUCTOR_RE = re.compile(r"\[MANUAL[^\]]*\]|Instructor check", re.I)


def split_instructor_notes(comment):
    """Separate instructor-only notes ("[MANUAL REVIEW] ...", "Instructor check
    ...") from the student comment. Returns (student_text, [notes])."""
    if not comment or not isinstance(comment, str):
        return comment, []
    keep, notes = [], []
    for part in re.split(r"\s*\|\s*|\n+", comment):
        m = _INSTRUCTOR_RE.search(part)
        if m:
            before = part[:m.start()].strip()
            if before:
                keep.append(before)
            notes.append(part[m.start():].strip())
        elif part.strip():
            keep.append(part.strip())
    return " | ".join(keep), notes


def legacy_issues(comment):
    if not comment or not isinstance(comment, str):
        return []
    parts = re.split(r"\s*\|\s*|\n+", comment)
    out = []
    for p in parts:
        p = re.sub(r"^\s*\[(ok|x|~)\]\s*", "", p.strip(), flags=re.I)
        p = re.sub(r"^[A-Za-z ]+:\s*(?=[A-Z]\d)", "", p)  # "Slope: H19 ..." -> "H19 ..."
        if not p:
            continue
        if _FAIL_RE.search(p) or not _PASS_RE.search(p):
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Student first name
# ---------------------------------------------------------------------------

def first_name(raw):
    """Best-effort first name from the name a student typed (students are told
    to pad short names with X's, e.g. 'JoXXXXXXXX Li') or from a file name like
    'Jordan_Rivera'. Returns '' when nothing usable is found."""
    if not raw or not isinstance(raw, str):
        return ""
    token = re.split(r"[\s_,]+", raw.strip())[0]
    token = re.sub(r"[Xx]{2,}$", "", token)        # strip X padding
    token = re.sub(r"[^A-Za-z'\-]", "", token)
    if len(token) < 2:
        return ""
    return token[0].upper() + token[1:]


# ---------------------------------------------------------------------------
# Overall note
# ---------------------------------------------------------------------------

def _join(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def overall_note(name, sections, strengths=None):
    """Rule-based overall note.

    sections:  list of {"name": str, "points": float, "possible": float}
    strengths: optional short phrases for the biggest fully-correct pieces of
               work, most important first (e.g. ["credit card amortization table"]).
    """
    total = sum(_num(s["points"]) or 0 for s in sections)
    possible = sum(_num(s["possible"]) or 0 for s in sections)
    pct = total / possible if possible else 0.0
    hi = f", {name}" if name else ""

    def lost(s):
        return (_num(s["possible"]) or 0) - (_num(s["points"]) or 0)

    missed = sorted((s for s in sections if lost(s) > 1e-9), key=lost, reverse=True)

    if pct >= 0.95:
        opening = f"Excellent work{hi}!"
    elif pct >= 0.85:
        opening = f"Great work{hi}."
    elif pct >= 0.7:
        opening = f"Nice effort{hi}."
    else:
        opening = f"Thanks for your work on this{hi}."

    lines = [opening]
    if not missed:
        lines.append("Every section is correct. That's a completely clean submission.")
        return " ".join(lines)

    strengths = [x for x in (strengths or []) if x][:2]
    if strengths:
        lines.append(f"Your {_join(strengths)} {'is' if len(strengths) == 1 else 'are'} spot on.")

    a = missed[0]["name"]
    if len(missed) == 1:
        lines.append(f"The only points you missed are on the {a} tab.")
    elif len(missed) == 2:
        lines.append(f"Most of the points you missed are on the {a} tab, with a couple more on {missed[1]['name']}.")
    else:
        lines.append(f"Most of the points you missed are on the {a} tab, with a few smaller ones on "
                     f"{missed[1]['name']} and elsewhere.")
    lines.append("The comment on each row shows exactly what to change.")

    if pct < 0.7:
        lines.append("Work through those fixes one at a time, and reach out if anything is unclear.")
    return " ".join(lines)


# ---------------------------------------------------------------------------
# Optional AI-written overall note
# ---------------------------------------------------------------------------

AI_SYSTEM = (
    "You write the overall note an instructor leaves at the top of a college "
    "student's graded Excel assignment. Be warm, encouraging and specific. "
    "Rules: 2 to 4 sentences of plain text. Address the student once as [NAME] "
    "(it is filled in later). Mention one or two real strengths and the most important "
    "thing to fix, using ONLY the facts provided. Never mention points, scores, "
    "percentages or grades. Never invent details, cells or advice that aren't in "
    "the facts. Don't mention that you are an AI."
)


def ai_overall_note(name, sections, row_comments, api_key=None, model=None, timeout=30):
    """Claude-written overall note, or None if disabled/unavailable/invalid.
    Callers fall back to overall_note() on None."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        import requests  # bundled dependency
        from web_adapter import ANTHROPIC_URL, ANTHROPIC_VERSION, DEFAULT_AI_MODEL
    except Exception:
        return None

    # The student's name never leaves the machine: the model writes [NAME] and
    # it's substituted here.
    facts = {
        "sections": [
            {"name": s["name"], "full_credit": (_num(s["points"]) or 0) >= (_num(s["possible"]) or 0) - 1e-9}
            for s in sections
        ],
        "row_feedback": [c for c in row_comments if c],
    }
    try:
        resp = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": model or os.environ.get("MA_GRADER_AI_MODEL") or DEFAULT_AI_MODEL,
                "max_tokens": 300,
                "system": AI_SYSTEM,
                "messages": [{"role": "user", "content": json.dumps(facts, indent=1)}],
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        text = "".join(
            b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text"
        ).strip()
    except Exception:
        return None

    # Guardrails: plain prose, sensible length, no numbers that look like scores.
    if not text or len(text) > 700 or re.search(r"\d+\s*(%|/\s*\d+|points?\b)", text, re.I):
        return None
    if name:
        return text.replace("[NAME]", name)
    # No name: drop the placeholder and any comma attached to it.
    text = re.sub(r",?\s*\[NAME\]\s*,?", lambda m: "," if m.group(0).startswith(",") and m.group(0).endswith(",") else "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def ai_notes_enabled():
    return os.environ.get("MA_GRADER_AI_NOTES") == "1" and bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Shared issue wording
# ---------------------------------------------------------------------------

_FORMAT_NAMES = {
    "currency with two decimals": "Currency with 2 decimal places",
    "percent with two decimals": "Percentage with 2 decimal places",
    "number with 0 decimals": "Number with 0 decimal places",
}


def format_issue(cell, expected_desc, found_fmt=None, label=None):
    """'Years in school (C24) is still in General format. Set it to Number
    with 0 decimal places (Home > Number Format).'"""
    want = _FORMAT_NAMES.get(str(expected_desc).lower(), expected_desc)
    what = f"{label[0].upper() + label[1:]} ({cell})" if label else f"Cell {cell}"
    if not found_fmt or str(found_fmt).lower() == "general":
        state = "is still in General format"
    else:
        state = "has a different number format than the instructions ask for"
    return f"{what} {state}. Set it to {want} (Home → Number Format)."
