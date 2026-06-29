"""
Canonical MA2 write-up (paper) rubric.

Eight criteria, each scored on a 5-level scale. Point values per level are the
EXACT values from the Canvas rubric (not recomputed from a multiplier), so the
app matches Canvas to the penny. Total possible = 42.

Level index: 0 -> Unsatisfactory (1), ... 4 -> Target (5).
"""

LEVEL_NAMES = ["Unsatisfactory", "Insufficient", "Approaching", "Acceptable", "Target"]

# Generic completeness descriptions shared by the question-based criteria,
# ordered level 1 (index 0) .. level 5 (index 4).
_GENERIC = [
    "Responses are missing entirely or so brief/vague that very few details are conveyed without follow-up questions.",
    "Most responses are brief or vague; a reasonable reader would need follow-ups to clarify a majority of them.",
    "One or more questions were neglected, or there are substantial gaps requiring considerable follow-up.",
    "Responses are largely complete but leave some gaps that would need a few follow-up questions.",
    "Complete answer to each question; a reasonable reader would need at most one or two follow-ups.",
]

_PROJECT_HEADING = [
    "No title provided, regardless of whether other title elements are included.",
    "No title, and one or more other title-section elements are missing.",
    "No title, or one or more other title-section elements is incorrect.",
    "A title is provided but does not accurately summarize the project, or a title element is incorrect/missing.",
    "Title accurately summarizes the project and the other title-section elements are correct.",
]

_REFERENCES = [
    "No sources provided.",
    "Only one academic source provided.",
    "Three or fewer references total (at least two academic).",
    "Only four references total (at least three academic).",
    "At least 5 references (3 academic); each has an APA citation, a short description, and where it was used.",
]

# name, points per level (index 0..4 = level 1..5), descriptions
CRITERIA = [
    {"key": "project_heading", "name": "Project Heading",
     "points": [0.0, 0.79, 1.22, 1.49, 1.75], "descriptions": _PROJECT_HEADING},
    {"key": "income_projection", "name": "Income and Projection",
     "points": [0.0, 3.15, 4.9, 5.95, 7.0], "descriptions": _GENERIC},
    {"key": "student_loans", "name": "Student Loans",
     "points": [0.0, 3.15, 4.9, 5.95, 7.0], "descriptions": _GENERIC},
    {"key": "credit_cards", "name": "Credit Cards",
     "points": [0.0, 3.15, 4.9, 5.95, 7.0], "descriptions": _GENERIC},
    {"key": "annual_budget", "name": "Annual Budget",
     "points": [0.0, 3.15, 4.9, 5.95, 7.0], "descriptions": _GENERIC},
    {"key": "ethics_worldview", "name": "Ethics and Christian Worldview Analysis",
     "points": [0.0, 1.58, 2.45, 2.98, 3.5], "descriptions": _GENERIC},
    {"key": "summary_reflections", "name": "Summary and Reflections",
     "points": [0.0, 2.36, 3.68, 4.46, 5.25], "descriptions": _GENERIC},
    {"key": "references", "name": "References",
     "points": [0.0, 1.58, 2.45, 2.98, 3.5], "descriptions": _REFERENCES},
]

TOTAL_POSSIBLE = round(sum(c["points"][4] for c in CRITERIA), 2)  # 42.0


def criterion_levels(crit):
    """Return level option dicts for one criterion (level 5 first for display)."""
    out = []
    for idx in range(4, -1, -1):
        out.append({
            "level": idx + 1,
            "name": LEVEL_NAMES[idx],
            "points": crit["points"][idx],
            "description": crit["descriptions"][idx],
        })
    return out


def points_for_level(crit_key, level):
    """Exact points for a criterion at a 1-5 level."""
    for c in CRITERIA:
        if c["key"] == crit_key:
            if 1 <= level <= 5:
                return c["points"][level - 1]
    return 0.0


def level_for_points(crit, value):
    """Best-matching 1-5 level for a stored points value (or None)."""
    if value is None:
        return None
    for idx, p in enumerate(crit["points"]):
        if abs(p - value) < 0.01:
            return idx + 1
    return None
