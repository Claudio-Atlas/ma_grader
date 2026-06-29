import os
import shutil

from utilities.paths import ensure_dir

def _copy_tree(src_dir: str, dest_dir: str):
    if not os.path.isdir(src_dir):
        return
    os.makedirs(dest_dir, exist_ok=True)

    for name in os.listdir(src_dir):
        src = os.path.join(src_dir, name)
        dst = os.path.join(dest_dir, name)

        if os.path.isdir(src):
            _copy_tree(src, dst)
        else:
            # Only copy if missing (so instructors can customize later)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)

def bootstrap_assets(project_root: str):
    """
    Copies packaged assets (templates/, feedback/) into workspace:
      Documents/MA1_Autograder/templates
      Documents/MA1_Autograder/feedback
    """
    src_templates = os.path.join(project_root, "templates")
    src_feedback = os.path.join(project_root, "feedback")

    dest_templates = ensure_dir("templates")
    dest_feedback = ensure_dir("feedback")

    _copy_tree(src_templates, dest_templates)
    _copy_tree(src_feedback, dest_feedback)
