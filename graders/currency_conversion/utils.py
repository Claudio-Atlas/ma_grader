def norm_unit(unit):
    """Normalizes unit strings by removing whitespace, dollar signs, and lowercasing."""
    if not unit:
        return ""
    return str(unit).replace("$", "").strip().lower()
