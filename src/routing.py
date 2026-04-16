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


def route_file(file_path: Path, valid: bool, classification: str) -> Path:
    """Move a file to the correct destination based on validation and classification."""
    if valid:
        destination_dir = PROCESSED_DIR / classification
    else:
        destination_dir = QUARANTINE_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / file_path.name
    return file_path.replace(destination_path)
