from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"


def ensure_data_directories():
    """Create the required data folders so missing directories do not crash the app."""
    for folder in (INPUT_DIR, PROCESSED_DIR, QUARANTINE_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def scan_files(rules):
    ensure_data_directories()
    ignored = set(rules.get("ignore_files", []))
    return [
        path for path in INPUT_DIR.glob("*")
        if path.name not in ignored
    ]


def find_ignored_files(rules):
    ensure_data_directories()
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


def _safe_replace(source: Path, destination: Path):
    try:
        return source.replace(destination), ""
    except OSError as exc:
        return destination, f"filesystem error: {exc}"


def route_file(file_path: Path, valid: bool, classification: str, rules: dict):
    """Move a file to the correct destination based on validation and classification."""
    duplicate_policy = rules.get("duplicate_policy", "quarantine")
    if valid:
        destination_dir = PROCESSED_DIR / classification
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / file_path.name
        if destination_path.exists():
            if duplicate_policy == "overwrite":
                moved_path, error = _safe_replace(file_path, destination_path)
                return (moved_path, False, "invalid", error) if error else (moved_path, True, classification, "")
            if duplicate_policy == "rename":
                destination_path = _unique_destination(destination_path)
                moved_path, error = _safe_replace(file_path, destination_path)
                return (moved_path, False, "invalid", error) if error else (moved_path, True, classification, "")
            # quarantine duplicates by rejecting later file
            destination_dir = QUARANTINE_DIR
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_path = destination_dir / file_path.name
            if destination_path.exists():
                destination_path = _unique_destination(destination_path)
            moved_path, error = _safe_replace(file_path, destination_path)
            return (moved_path, False, "invalid", error or "duplicate filename")
        moved_path, error = _safe_replace(file_path, destination_path)
        return (moved_path, False, "invalid", error) if error else (moved_path, True, classification, "")
    destination_dir = QUARANTINE_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / file_path.name
    if destination_path.exists():
        if duplicate_policy == "overwrite":
            moved_path, error = _safe_replace(file_path, destination_path)
            return (moved_path, False, "invalid", error) if error else (moved_path, False, "invalid", "")
        if duplicate_policy == "rename":
            destination_path = _unique_destination(destination_path)
            moved_path, error = _safe_replace(file_path, destination_path)
            return (moved_path, False, "invalid", error) if error else (moved_path, False, "invalid", "")
        destination_path = _unique_destination(destination_path)
        moved_path, error = _safe_replace(file_path, destination_path)
        return (moved_path, False, "invalid", error) if error else (moved_path, False, "invalid", "")
    moved_path, error = _safe_replace(file_path, destination_path)
    return (moved_path, False, "invalid", error) if error else (moved_path, False, "invalid", "")
