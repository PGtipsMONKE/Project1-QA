from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
ARCHIVE_DIR = BASE_DIR / "data" / "archive"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"


def ensure_data_directories():
    """Create the required data folders so missing directories do not crash the app."""
    for folder in (INPUT_DIR, ARCHIVE_DIR, PROCESSED_DIR, QUARANTINE_DIR):
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


def _route_result(path: Path, valid: bool, classification: str, reason: str = "", archived: bool = False):
    """Build a normalized routing response tuple."""
    return path, valid, classification, reason, archived


def _move_to_quarantine(file_path: Path, duplicate_policy: str):
    """Move a file to quarantine while applying duplicate handling policy."""
    destination_path = QUARANTINE_DIR / file_path.name
    if destination_path.exists() and duplicate_policy != "overwrite":
        destination_path = _unique_destination(destination_path)
    return _safe_replace(file_path, destination_path)


def route_file(file_path: Path, valid: bool, classification: str, rules: dict, archive_valid: bool = False):
    """Route a file to processed/archive/quarantine and return routing metadata.

    Returns:
        tuple[Path, bool, str, str, bool]:
            destination path, final validity, final classification, reason override, archived flag.
    """
    duplicate_policy = rules.get("duplicate_policy", "quarantine")

    # Valid files go to either archive (date cutoff) or classification-specific processed folder.
    if valid:
        destination_dir = ARCHIVE_DIR if archive_valid else PROCESSED_DIR / classification
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / file_path.name

        # Duplicate handling is controlled by config policy.
        if destination_path.exists():
            # overwrite: keep this file as valid and replace existing destination.
            if duplicate_policy == "overwrite":
                moved_path, error = _safe_replace(file_path, destination_path)
                if error:
                    return _route_result(moved_path, False, "invalid", error, False)
                return _route_result(moved_path, True, classification, "", archive_valid)
            # rename: keep this file as valid under a unique destination name.
            if duplicate_policy == "rename":
                destination_path = _unique_destination(destination_path)
                moved_path, error = _safe_replace(file_path, destination_path)
                if error:
                    return _route_result(moved_path, False, "invalid", error, False)
                return _route_result(moved_path, True, classification, "", archive_valid)

            # duplicate_policy == "quarantine": reject the later duplicate.
            moved_path, error = _move_to_quarantine(file_path, duplicate_policy)
            return _route_result(moved_path, False, "invalid", error or "duplicate filename", False)

        # Non-duplicate valid file: direct move to selected destination.
        moved_path, error = _safe_replace(file_path, destination_path)
        if error:
            return _route_result(moved_path, False, "invalid", error, False)
        return _route_result(moved_path, True, classification, "", archive_valid)

    # Invalid files always go to quarantine regardless of classification.
    moved_path, error = _move_to_quarantine(file_path, duplicate_policy)
    if error:
        return _route_result(moved_path, False, "invalid", error, False)
    return _route_result(moved_path, False, "invalid", "", False)
