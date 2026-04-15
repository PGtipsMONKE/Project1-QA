from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "process.log"


def scan_files():
    return [
        path for path in INPUT_DIR.glob("*")
        if path.name != ".gitkeep"
    ]

def test_filename(filename: str):
    """Return a validation result and reason for a filename."""
    try:
        name, extension = filename.rsplit(".", 1)
    except ValueError:
        return False, "missing extension"

    parts = name.split("_")
    if len(parts) != 3:
        return False, "incorrect filename structure"

    _, _, date_part = parts
    try:
        datetime.strptime(date_part, "%d-%b-%Y")
        return True, ""
    except ValueError:
        return False, "invalid date format"
    except Exception:
        return False, "unexpected filename format"

def classify_file(filename: str) -> str:
    """Return classification based on filename prefix."""
    lower_name = filename.lower()
    if lower_name.startswith("invoice"):
        return "invoice"
    if lower_name.startswith("report"):
        return "report"
    if lower_name.startswith("notes"):
        return "notes"
    return "other"

def validate_files(files):
    """Validate a list of file paths and return a validation summary."""
    validated = []
    for file_path in files:
        valid, reason = test_filename(file_path.name)
        validated.append({
            "path": file_path,
            "valid": valid,
            "reason": reason,
        })
    return validated

def route_file(file_path: Path, valid: bool, classification: str) -> Path:
    """Move a file to the correct destination based on validation and classification."""
    if valid:
        destination_dir = PROCESSED_DIR / classification
    else:
        destination_dir = QUARANTINE_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / file_path.name
    return file_path.replace(destination_path)


def write_log_entry(entry: dict):
    """Append a structured log entry to the process log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    header = "timestamp\tfilename\tsource_path\tstatus\tdestination_path\tclassification\treason\n"
    line = (
        f"{entry['timestamp']}\t{entry['filename']}\t{entry['source_path']}\t"
        f"{entry['status']}\t{entry['destination_path']}\t{entry['classification']}\t{entry['reason']}\n"
    )
    write_header = not LOG_FILE.exists()
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        if write_header:
            log_file.write(header)
        log_file.write(line)


def move_valid_and_invalid(validated):
    """Move validated files to processed or quarantine folders and log each action."""
    moved = []
    for entry in validated:
        classification = classify_file(entry["path"].name) if entry["valid"] else "invalid"
        destination = route_file(entry["path"], entry["valid"], classification)
        result = {
            "path": destination,
            "valid": entry["valid"],
            "classification": classification,
            "reason": entry["reason"] or "accepted",
            "source_path": str(entry["path"]),
        }
        write_log_entry({
            "timestamp": datetime.utcnow().isoformat(),
            "filename": entry["path"].name,
            "source_path": result["source_path"],
            "status": "valid" if entry["valid"] else "invalid",
            "destination_path": str(destination),
            "classification": result["classification"],
            "reason": result["reason"],
        })
        moved.append(result)
    return moved


def print_summary(files, moved_files, start_time):
    total_files = len(files)
    valid_count = sum(1 for entry in moved_files if entry["valid"])
    invalid_count = total_files - valid_count
    classification_counts = {}
    invalid_reason_counts = {}

    for entry in moved_files:
        if entry["valid"]:
            classification_counts[entry["classification"]] = classification_counts.get(entry["classification"], 0) + 1
        else:
            invalid_reason_counts[entry["reason"]] = invalid_reason_counts.get(entry["reason"], 0) + 1

    elapsed = datetime.utcnow() - start_time

    print("\nProcessing summary")
    print("------------------")
    print(f"Base directory: {BASE_DIR}")
    print(f"Input folder: {INPUT_DIR.relative_to(BASE_DIR)}")
    print(f"Processed folder: {PROCESSED_DIR.relative_to(BASE_DIR)}")
    print(f"Quarantine folder: {QUARANTINE_DIR.relative_to(BASE_DIR)}")
    print(f"Log file: {LOG_FILE.relative_to(BASE_DIR)}")
    print(f"Total files scanned: {total_files}")
    print(f"Valid files: {valid_count}")
    print(f"Invalid files: {invalid_count}")

    if classification_counts:
        print("\nValid files by classification:")
        for classification, count in sorted(classification_counts.items()):
            print(f"  {classification}: {count}")

    if invalid_reason_counts:
        print("\nInvalid files by reason:")
        for reason, count in sorted(invalid_reason_counts.items()):
            print(f"  {reason}: {count}")

    print(f"Elapsed time: {elapsed}")

# Main execution flow
def main():
    start_time = datetime.utcnow()
    files = scan_files()
    validated = validate_files(files)
    moved_files = move_valid_and_invalid(validated)
    print_summary(files, moved_files, start_time)


if __name__ == "__main__":
    main()