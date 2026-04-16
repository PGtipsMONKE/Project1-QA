import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "process.log"
CONFIG_FILE = BASE_DIR / "config" / "config.json"

DEFAULT_RULES = {
    "required_parts": 3,
    "filename_separator": "_",
    "date_format": "%d-%b-%Y",
    "allowed_extensions": None,
    "ignore_files": [
        ".gitkeep"
    ],
    "classification_prefixes": {
        "invoice": "invoice",
        "report": "report",
        "notes": "notes"
    }
}


def load_rules_from_config():
    """Load rule configuration from config/config.json, or return defaults."""
    if not CONFIG_FILE.exists():
        print(f"Config file not found at {CONFIG_FILE}. Using built-in defaults.")
        return DEFAULT_RULES.copy()

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as exc:
        print(f"Warning: could not parse config file {CONFIG_FILE}: {exc}. Using built-in defaults.")
        return DEFAULT_RULES.copy()
    except Exception as exc:
        print(f"Warning: could not read config file {CONFIG_FILE}: {exc}. Using built-in defaults.")
        return DEFAULT_RULES.copy()

    if not isinstance(config, dict):
        print(f"Warning: config file {CONFIG_FILE} must contain a JSON object. Using built-in defaults.")
        return DEFAULT_RULES.copy()

    rules = DEFAULT_RULES.copy()
    rules["classification_prefixes"] = DEFAULT_RULES["classification_prefixes"].copy()

    if isinstance(config.get("required_parts"), int):
        rules["required_parts"] = config["required_parts"]

    if isinstance(config.get("filename_separator"), str):
        rules["filename_separator"] = config["filename_separator"]

    if isinstance(config.get("date_format"), str):
        rules["date_format"] = config["date_format"]

    if config.get("allowed_extensions") is None:
        rules["allowed_extensions"] = None
    elif isinstance(config.get("allowed_extensions"), list) and all(isinstance(ext, str) for ext in config["allowed_extensions"]):
        rules["allowed_extensions"] = [ext.lower().lstrip(".") for ext in config["allowed_extensions"]]

    if isinstance(config.get("ignore_files"), list) and all(isinstance(item, str) for item in config["ignore_files"]):
        rules["ignore_files"] = config["ignore_files"]

    if isinstance(config.get("classification_prefixes"), dict) and all(
        isinstance(prefix, str) and isinstance(classification, str)
        for prefix, classification in config["classification_prefixes"].items()
    ):
        rules["classification_prefixes"] = config["classification_prefixes"].copy()

    return rules


def scan_files(rules):
    ignored = set(rules.get("ignore_files", []))
    return [
        path for path in INPUT_DIR.glob("*")
        if path.name not in ignored
    ]


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


def validate_files(files, rules):
    """Validate a list of file paths and return a validation summary."""
    validated = []
    for file_path in files:
        valid, reason = test_filename(file_path.name, rules)
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


def move_valid_and_invalid(validated, rules):
    """Move validated files to processed or quarantine folders and log each action."""
    moved = []
    for entry in validated:
        classification = classify_file(entry["path"].name, rules) if entry["valid"] else "invalid"
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
    rules = load_rules_from_config()
    files = scan_files(rules)
    validated = validate_files(files, rules)
    moved_files = move_valid_and_invalid(validated, rules)
    print_summary(files, moved_files, start_time)


if __name__ == "__main__":
    main()
