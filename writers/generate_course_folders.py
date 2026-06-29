# writers/generate_course_folders.py

from utilities.logger import get_logger
from utilities.paths import ensure_dir


def generate_course_folders(course_label: str, assignment_type: str = None):
    """
    Creates/ensures the course-specific folders exist INSIDE the user's workspace.
    When an assignment_type is given, each top folder gets a per-assignment
    subfolder so MA1/MA2/MA3 stay cleanly separated:

        <workspace>/
            student_groups/COURSE_LABEL/MA2
            student_submissions/COURSE_LABEL/MA2
            graded_output/COURSE_LABEL/MA2

    Returns:
        (folder_safe_label, graded_path, submissions_path)
    """
    logger = get_logger()

    folder_safe_label = course_label.replace(" ", "_").replace("/", "_")

    # Per-assignment subfolder (e.g. "MA2") when provided.
    sub = (assignment_type or "").upper()
    parts = [folder_safe_label] + ([sub] if sub else [])

    # Ensure all 3 course folders exist in the workspace
    groups_path = ensure_dir("student_groups", *parts)
    graded_path = ensure_dir("graded_output", *parts)
    submissions_path = ensure_dir("student_submissions", *parts)

    logger.info(f"Workspace folders ready for: {course_label}")
    logger.debug(f"   - Student groups:   {groups_path}")
    logger.debug(f"   - Student files:    {submissions_path}")
    logger.debug(f"   - Graded output:    {graded_path}")

    return folder_safe_label, graded_path, submissions_path
