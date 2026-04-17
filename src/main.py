import argparse
from datetime import UTC, datetime
from uuid import uuid4

from config import load_rules_from_config
from logger import print_summary, write_log_entry, write_summary_file
from routing import ensure_data_directories, find_ignored_files, route_file, scan_files
from validation import classify_file, validate_files


def move_valid_and_invalid(validated, rules, run_id, dry_run=False):
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
            dry_run=dry_run,
        )
        reason = override_reason or entry["reason"] or "accepted"
        if dry_run:
            reason = f"dry-run: {reason}"
        if archived and not override_reason:
            reason = f"archived: file date before cutoff ({archive_before_date.isoformat()})"
            if dry_run:
                reason = f"dry-run: {reason}"
        result = {
            "filename": entry["path"].name,
            "path": destination,
            "valid": routed_valid,
            "classification": routed_classification,
            "reason": reason,
            "source_path": str(entry["path"]),
            "archived": archived,
        }
        destination_bucket = "quarantine"
        if result["valid"] and result["archived"]:
            destination_bucket = "archive"
        elif result["valid"]:
            destination_bucket = "processed"
        write_log_entry({
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "run_id": run_id,
            "event_type": "file_routed",
            "filename": entry["path"].name,
            "source_path": result["source_path"],
            "status": "valid" if result["valid"] else "invalid",
            "archived": result["archived"],
            "destination_bucket": destination_bucket,
            "destination_path": str(destination),
            "classification": result["classification"],
            "reason_code": result["reason"].split(":", 1)[0].strip().lower().replace(" ", "_"),
            "reason_detail": result["reason"],
        })
        moved.append(result)
    return moved


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Process files from data/input into processed/archive/quarantine.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and compute destinations without moving files.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a JSON config file (relative paths resolve from project root).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat configuration warnings as fatal errors.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    start_time = datetime.now(UTC)
    run_id = uuid4().hex
    try:
        write_log_entry({
            "timestamp": start_time.isoformat().replace("+00:00", "Z"),
            "run_id": run_id,
            "event_type": "run_start",
            "status": "started",
            "reason_detail": f"dry_run={args.dry_run} strict={args.strict}",
        })
        rules, rules_source, config_warnings = load_rules_from_config(args.config)
        if args.strict and config_warnings:
            raise RuntimeError("strict mode enabled and configuration warnings were found")
        ensure_data_directories()
        files = scan_files(rules)
        ignored_files = find_ignored_files(rules)
        validated = validate_files(files, rules)
        moved_files = move_valid_and_invalid(validated, rules, run_id, dry_run=args.dry_run)
        summary = print_summary(files, moved_files, start_time, rules_source, ignored_files, config_warnings, run_id=run_id)
        summary_file = write_summary_file(summary)
        write_log_entry({
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "run_id": run_id,
            "event_type": "run_end",
            "status": "completed",
            "reason_detail": (
                f"processed={summary['processed_files']} archived={summary['archived_files']} "
                f"quarantined={summary['quarantined_files']} dry_run={args.dry_run}"
            ),
        })
        print(f"Summary file written: {summary_file}")
        return 0
    except Exception as exc:
        write_log_entry({
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "run_id": run_id,
            "event_type": "run_end",
            "status": "failed",
            "reason_detail": str(exc),
        })
        print(f"Error: fatal exception during processing: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
