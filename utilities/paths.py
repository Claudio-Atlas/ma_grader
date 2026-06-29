# utilities/paths.py
import os

APP_FOLDER = "MA_Grader"  # default folder name

# Custom workspace override (set by server.py)
_custom_workspace = None


def set_custom_workspace(path: str):
    """Set a custom workspace path (used by the API server)"""
    global _custom_workspace
    _custom_workspace = path


def workspace_root() -> str:
    """
    Get the workspace root directory.
    
    If a custom workspace is set (via settings), use that.
    Otherwise, default to ~/Documents/MA1_Autograder
    """
    global _custom_workspace
    
    if _custom_workspace and os.path.isdir(_custom_workspace):
        # Use custom workspace directly (no extra nesting)
        os.makedirs(_custom_workspace, exist_ok=True)
        return _custom_workspace
    
    # Default: ~/Documents/MA1_Autograder
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    root = os.path.join(docs, APP_FOLDER)
    os.makedirs(root, exist_ok=True)
    return root


def ws_path(*parts) -> str:
    """Join onto workspace root and ensure parent dirs exist."""
    p = os.path.join(workspace_root(), *parts)
    parent = os.path.dirname(p)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    return p


def ensure_dir(*parts) -> str:
    """Ensure a workspace directory exists, return its path."""
    p = os.path.join(workspace_root(), *parts)
    os.makedirs(p, exist_ok=True)
    return p
