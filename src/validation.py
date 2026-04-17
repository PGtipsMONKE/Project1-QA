from datetime import datetime


def test_filename(filename: str, rules: dict):
    """Return a validation result and reason for a filename."""
    try:
        name, extension = filename.rsplit(".", 1)
    except ValueError:
        return False, "missing extension"

    parts = name.split(rules["filename_separator"])
    if len(parts) != rules["required_parts"]:
        return False, "incorrect filename structure"

    _, _, date_part = parts
    try:
        datetime.strptime(date_part, rules["date_format"])
    except ValueError:
        return False, "invalid date format"
    except Exception:
        return False, "unexpected filename format"

    allowed_extensions = rules.get("allowed_extensions")
    if allowed_extensions is not None and extension.lower() not in allowed_extensions:
        return False, "unsupported extension"

    return True, ""


def classify_file(filename: str, rules: dict) -> str:
    """Return classification based on filename prefix and configuration."""
    lower_name = filename.lower()
    for prefix, classification in rules["classification_prefixes"].items():
        if lower_name.startswith(prefix.lower()):
            return classification
    return "other"


def extract_file_date(filename: str, rules: dict):
    """Parse and return the date component from a valid filename, or None."""
    try:
        name, _ = filename.rsplit(".", 1)
        parts = name.split(rules["filename_separator"])
        if len(parts) != rules["required_parts"]:
            return None
        return datetime.strptime(parts[2], rules["date_format"]).date()
    except Exception:
        return None


def validate_files(files, rules):
    """Validate a list of file paths and return a validation summary."""
    validated = []
    for file_path in files:
        valid, reason = test_filename(file_path.name, rules)
        validated.append({
            "path": file_path,
            "valid": valid,
            "reason": reason,
            "file_date": extract_file_date(file_path.name, rules) if valid else None,
        })
    return validated
