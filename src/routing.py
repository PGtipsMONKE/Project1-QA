from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"


def scan_files(rules):
    ignored = set(rules.get("ignore_files", []))
    return [
        path for path in INPUT_DIR.glob("*")
        if path.name not in ignored
    ]


def find_ignored_files(rules):
    ignored = set(rules.get("ignore_files", []))
    return [
        path for path in INPUT_DIR.glob("*")
        if path.name in ignored
    ]


def _unique_destination(path: Path) -> Path:
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 1
    candidate = path
    while candidate.exists():
        candidate = parent / f"{stem}_{index}{suffix}"
        index += 1
    return candidate


def route_file(file_path: Path, valid: bool, classification: str, rules: dict):
    """Move a file to the correct destination based on validation and classification."""
    duplicate_policy = rules.get("duplicate_policy", "quarantine")
    if valid:
        destination_dir = PROCESSED_DIR / classification
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / file_path.name
        if destination_path.exists():
            if duplicate_policy == "overwrite":
                return file_path.replace(destination_path), True, classification, ""
            if duplicate_policy == "rename":
                destination_path = _unique_destination(destination_path)
                return file_path.replace(destination_path), True, classification, ""
            # quarantine duplicates by rejecting later file
            destination_dir = QUARANTINE_DIR
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_path = destination_dir / file_path.name
            if destination_path.exists():
                destination_path = _unique_destination(destination_path)
            return file_path.replace(destination_path), False, "invalid", "duplicate filename"
        return file_path.replace(destination_path), True, classification, ""
    destination_dir = QUARANTINE_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / file_path.name
    if destination_path.exists():
        if duplicate_policy == "overwrite":
            return file_path.replace(destination_path), False, "invalid", ""
        if duplicate_policy == "rename":
            destination_path = _unique_destination(destination_path)
            return file_path.replace(destination_path), False, "invalid", ""
        destination_path = _unique_destination(destination_path)
        return file_path.replace(destination_path), False, "invalid", ""
    return file_path.replace(destination_path), False, "invalid", ""
