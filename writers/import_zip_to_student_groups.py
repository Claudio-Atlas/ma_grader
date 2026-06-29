# writers/import_zip_to_student_groups.py

import os
import shutil
import zipfile
from pathlib import Path

from utilities.paths import ensure_dir


def _is_safe_path(base_path: str, target_path: str) -> bool:
    """
    Check if target_path is safely within base_path (no path traversal).
    
    Prevents ZIP slip attacks where malicious archives contain entries
    like '../../../etc/passwd' that escape the extraction directory.
    
    Args:
        base_path: The intended extraction directory
        target_path: The resolved path of the file to extract
    
    Returns:
        True if target_path is within base_path, False otherwise
    """
    # Resolve to absolute paths to handle any symlinks or relative components
    base = os.path.realpath(base_path)
    target = os.path.realpath(target_path)
    
    # Check that target starts with base (is inside the directory)
    return target.startswith(base + os.sep) or target == base


def _safe_extract(zip_file: zipfile.ZipFile, dest_dir: str) -> None:
    """
    Safely extract ZIP contents, validating each path against traversal attacks.
    
    Args:
        zip_file: Open ZipFile object
        dest_dir: Destination directory (must exist)
    
    Raises:
        ValueError: If any archive member attempts path traversal
    """
    for member in zip_file.namelist():
        # Get the target path for this member
        target_path = os.path.join(dest_dir, member)
        
        # Validate it's within our destination
        if not _is_safe_path(dest_dir, target_path):
            raise ValueError(
                f"Blocked path traversal attempt in ZIP: {member}"
            )
    
    # All paths validated, safe to extract
    zip_file.extractall(dest_dir)


def import_zip_to_student_groups(zip_path: str, course_label: str,
                                 assignment_type: str = None) -> str:
    """
    Extracts a downloaded student ZIP into workspace:

        Documents/MA1_Autograder/student_groups/<course_label>/

    Security:
        - Validates all archive paths before extraction (prevents ZIP slip)
        - Rejects any path that would escape the destination directory
    
    Returns:
        destination folder path
    """
    zip_path = os.path.abspath(zip_path)
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Zip not found: {zip_path}")
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Not a valid zip file: {zip_path}")

    course_label = (course_label or "").strip()
    if not course_label:
        raise ValueError("Course label cannot be blank.")

    # [OK] Workspace destination (per-assignment subfolder when provided)
    sub = (assignment_type or "").upper()
    if sub:
        dest_root = ensure_dir("student_groups", course_label, sub)
    else:
        dest_root = ensure_dir("student_groups", course_label)

    # Extract to a temporary folder first
    temp_extract = os.path.join(dest_root, "_tmp_extract")
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)
    os.makedirs(temp_extract, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        # Use safe extraction to prevent path traversal attacks
        _safe_extract(z, temp_extract)

    # If the zip contains one top-level folder, move its contents up
    items = [p for p in Path(temp_extract).iterdir()]

    if len(items) == 1 and items[0].is_dir():
        top = items[0]
        for child in top.iterdir():
            target = Path(dest_root) / child.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(child), str(target))
    else:
        for child in items:
            target = Path(dest_root) / child.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(child), str(target))

    shutil.rmtree(temp_extract, ignore_errors=True)

    return dest_root
