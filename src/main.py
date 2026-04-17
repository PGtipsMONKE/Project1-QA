from datetime import datetime

from config import load_rules_from_config
from logger import print_summary, write_log_entry, write_summary_file
from routing import ensure_data_directories, find_ignored_files, route_file, scan_files
from validation import classify_file, validate_files


def move_valid_and_invalid(validated, rules):
    """Move validated files to processed or quarantine folders and log each action."""
    moved = []
    archive_before_date = rules.get("archive_before_date")
    for entry in validated:
        classification = classify_file(entry["path"].name, rules) if entry["valid"] else "invalid"
        archive_valid = (
            entry["valid"]
            and archive_before_date is not None
            and entry.get("file_date") is not None
            and entry["file_date"] < archive_before_date
        )
        destination, routed_valid, routed_classification, override_reason, archived = route_file(
            entry["path"],
            entry["valid"],
            classification,
            rules,
            archive_valid=archive_valid,
        )
        reason = override_reason or entry["reason"] or "accepted"
        if archived and not override_reason:
            reason = f"archived: file date before cutoff ({archive_before_date.isoformat()})"
        result = {
            "filename": entry["path"].name,
            "path": destination,
            "valid": routed_valid,
            "classification": routed_classification,
            "reason": reason,
            "source_path": str(entry["path"]),
            "archived": archived,
        }
        write_log_entry({
            "timestamp": datetime.utcnow().isoformat(),
            "filename": entry["path"].name,
            "source_path": result["source_path"],
            "status": "valid" if result["valid"] else "invalid",
            "destination_path": str(destination),
            "classification": result["classification"],
            "reason": result["reason"],
        })
        moved.append(result)
    return moved


def main():
    start_time = datetime.utcnow()
    try:
        rules, rules_source, config_warnings = load_rules_from_config()
        ensure_data_directories()
        files = scan_files(rules)
        ignored_files = find_ignored_files(rules)
        validated = validate_files(files, rules)
        moved_files = move_valid_and_invalid(validated, rules)
        summary = print_summary(files, moved_files, start_time, rules_source, ignored_files, config_warnings)
        summary_file = write_summary_file(summary)
        print(f"Summary file written: {summary_file}")
        return 0
    except Exception as exc:
        print(f"Error: fatal exception during processing: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
