from datetime import datetime

from config import load_rules_from_config
from logger import print_summary, write_log_entry, write_summary_file
from routing import find_ignored_files, route_file, scan_files
from validation import classify_file, validate_files


def move_valid_and_invalid(validated, rules):
    """Move validated files to processed or quarantine folders and log each action."""
    moved = []
    for entry in validated:
        classification = classify_file(entry["path"].name, rules) if entry["valid"] else "invalid"
        destination = route_file(entry["path"], entry["valid"], classification)
        result = {
            "filename": entry["path"].name,
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


def main():
    start_time = datetime.utcnow()
    rules, rules_source = load_rules_from_config()
    files = scan_files(rules)
    ignored_files = find_ignored_files(rules)
    validated = validate_files(files, rules)
    moved_files = move_valid_and_invalid(validated, rules)
    summary = print_summary(files, moved_files, start_time, rules_source, ignored_files)
    summary_file = write_summary_file(summary)
    print(f"Summary file written: {summary_file}")


if __name__ == "__main__":
    main()
