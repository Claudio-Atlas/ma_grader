# utilities/json_loader.py

import json
import os
import sys
from functools import lru_cache

from utilities.paths import ensure_dir, ws_path


def _get_bundled_path(*parts):
    """
    Get the path to bundled data files.
    
    Handles both development mode (files in project folder) and
    PyInstaller bundled mode (files in sys._MEIPASS).
    
    Args:
        *parts: Path components to join
        
    Returns:
        str: Absolute path to the bundled file/folder
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle - data is in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Running as regular Python script - data is in project root
        # This file is in utilities/, so project root = one level up
        base_path = os.path.dirname(os.path.dirname(__file__))
    
    return os.path.join(base_path, *parts)


@lru_cache(maxsize=None)
def load_feedback(tab_name: str) -> dict:
    """
    Load feedback JSON for a given tab.

    Priority:
      1) Workspace (Documents/MA1_Autograder/feedback/<tab>.json)  <-- instructor-editable
      2) Packaged defaults (project_root/feedback/<tab>.json)

    If workspace file doesn't exist but defaults do, we auto-copy defaults
    into workspace on first run so instructors can edit them later.
    """

    # 1) Workspace path (instructor-editable)
    ensure_dir("feedback")
    workspace_path = ws_path("feedback", f"{tab_name}.json")

    if os.path.exists(workspace_path):
        with open(workspace_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2) Default path (bundled with app or in repo)
    default_path = _get_bundled_path("feedback", f"{tab_name}.json")

    if not os.path.exists(default_path):
        raise FileNotFoundError(
            f"Feedback JSON not found for '{tab_name}'.\n"
            f"- Workspace expected: {workspace_path}\n"
            f"- Bundled expected:   {default_path}\n"
            f"Fix: ensure feedback/{tab_name}.json exists."
        )

    # Auto-copy defaults -> workspace so it's editable for instructors
    try:
        with open(default_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(workspace_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return data

    except Exception as e:
        # If copy fails, still load defaults so the app runs
        with open(default_path, "r", encoding="utf-8") as f:
            return json.load(f)
