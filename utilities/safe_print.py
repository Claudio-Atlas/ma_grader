# utilities/safe_print.py
# Windows-safe print function that handles Unicode gracefully

import sys


def safe_print(msg):
    """
    Print that won't crash on Windows with Unicode characters.
    Falls back to replacing problematic chars if encoding fails.
    """
    try:
        print(msg)
    except UnicodeEncodeError:
        # Replace any non-ASCII characters with '?'
        safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
        print(safe_msg)


def safe_str(obj):
    """
    Convert object to string, replacing any problematic Unicode chars.
    """
    s = str(obj)
    try:
        s.encode('ascii')
        return s
    except UnicodeEncodeError:
        return s.encode('ascii', errors='replace').decode('ascii')
