import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "process.log"
LOG_JSONL_FILE = LOG_DIR / "process.jsonl"
LOG_PRETTY_FILE = LOG_DIR / "process.pretty.log"
SUMMARY_FILE = LOG_DIR / "summary.json"

PRETTY_COLUMNS = [
    ("timestamp", 27),
    ("event_type", 11),
    ("status", 10),
    ("archived", 8),
    ("destination_bucket", 18),
    ("classification", 14),
    ("filename", 36),
    ("reason_code", 28),
]


def _to_tsv_field(value):
    """Render values safely for TSV output without breaking row boundaries."""
    text = "" if value is None else str(value)
    return text.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def _fit_fixed_width(value, width):
    """Return a fixed-width field for aligned plain-text logs."""
    text = _to_tsv_field(value)
    if len(text) > width:
        if width <= 3:
            return text[:width]
        return text[: width - 3] + "..."
    return text.ljust(width)


def _write_pretty_log_row(normalized: dict):
    """Append a fixed-width row so columns align in plain text viewers."""
    header = " | ".join(_fit_fixed_width(name, width) for name, width in PRETTY_COLUMNS)
    separator = "-+-".join("-" * width for _, width in PRETTY_COLUMNS)
    row = " | ".join(_fit_fixed_width(normalized.get(name, ""), width) for name, width in PRETTY_COLUMNS)

    write_header = not LOG_PRETTY_FILE.exists()
    with LOG_PRETTY_FILE.open("a", encoding="utf-8") as pretty_file:
        if write_header:
            pretty_file.write(header + "\n")
            pretty_file.write(separator + "\n")
        pretty_file.write(row + "\n")


def _normalized_log_entry(entry: dict):
    """Normalize event payloads so both TSV and JSONL have a stable schema."""
    return {
        "timestamp": entry.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "run_id": entry.get("run_id", ""),
        "event_type": entry.get("event_type", "file_routed"),
        "filename": entry.get("filename", ""),
        "source_path": entry.get("source_path", ""),
        "status": entry.get("status", ""),
        "archived": bool(entry.get("archived", False)),
        "destination_bucket": entry.get("destination_bucket", ""),
        "destination_path": entry.get("destination_path", ""),
        "classification": entry.get("classification", ""),
        "reason_code": entry.get("reason_code", ""),
        "reason_detail": entry.get("reason_detail", entry.get("reason", "")),
    }


def write_log_entry(entry: dict):
    """Append a structured log entry to both TSV and JSONL process logs."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        normalized = _normalized_log_entry(entry)
        header = (
            "timestamp\trun_id\tevent_type\tfilename\tsource_path\tstatus\tarchived\t"
            "destination_bucket\tdestination_path\tclassification\treason_code\treason_detail\n"
        )
        fields = [
            normalized["timestamp"],
            normalized["run_id"],
            normalized["event_type"],
            normalized["filename"],
            normalized["source_path"],
            normalized["status"],
            str(normalized["archived"]).lower(),
            normalized["destination_bucket"],
            normalized["destination_path"],
            normalized["classification"],
            normalized["reason_code"],
            normalized["reason_detail"],
        ]
        line = "\t".join(_to_tsv_field(field) for field in fields) + "\n"
        write_header = not LOG_FILE.exists()
        with LOG_FILE.open("a", encoding="utf-8") as log_file:
            if write_header:
                log_file.write(header)
            log_file.write(line)

        with LOG_JSONL_FILE.open("a", encoding="utf-8") as jsonl_file:
            json.dump(normalized, jsonl_file, ensure_ascii=True)
            jsonl_file.write("\n")

        _write_pretty_log_row(normalized)
    except OSError as exc:
        print(f"Warning: could not write log entry to {LOG_FILE}: {exc}")


def generate_summary(files, moved_files, start_time, rules_source, ignored_files, warnings=None, run_id=""):
    warnings = warnings or []
    total_files = len(files)
    valid_count = sum(1 for entry in moved_files if entry["valid"])
    archived_count = sum(1 for entry in moved_files if entry.get("archived"))
    processed_count = sum(1 for entry in moved_files if entry["valid"] and not entry.get("archived"))
    invalid_count = total_files - valid_count
    classification_counts = {}
    invalid_reason_counts = {}
    invalid_filenames = []

    for entry in moved_files:
        if entry["valid"]:
            classification_counts[entry["classification"]] = classification_counts.get(entry["classification"], 0) + 1
        else:
            invalid_reason_counts[entry["reason"]] = invalid_reason_counts.get(entry["reason"], 0) + 1
            invalid_filenames.append(entry["filename"])

    end_time = datetime.utcnow()
    elapsed = end_time - start_time
    valid_rate = (valid_count / total_files * 100) if total_files else 0
    invalid_rate = (invalid_count / total_files * 100) if total_files else 0

    return {
        "run_id": run_id,
        "config_rules_source": rules_source,
        "base_directory": str(BASE_DIR),
        "input_folder": str(Path(__file__).resolve().parent.parent / "data" / "input"),
        "archive_folder": str(Path(__file__).resolve().parent.parent / "data" / "archive"),
        "processed_folder": str(Path(__file__).resolve().parent.parent / "data" / "processed"),
        "quarantine_folder": str(Path(__file__).resolve().parent.parent / "data" / "quarantine"),
        "log_file": str(LOG_FILE.relative_to(BASE_DIR)),
        "log_jsonl_file": str(LOG_JSONL_FILE.relative_to(BASE_DIR)),
        "log_pretty_file": str(LOG_PRETTY_FILE.relative_to(BASE_DIR)),
        "summary_file": str(SUMMARY_FILE.relative_to(BASE_DIR)),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "elapsed_seconds": elapsed.total_seconds(),
        "total_files_scanned": total_files,
        "ignored_files": [path.name for path in sorted(ignored_files, key=lambda p: p.name)],
        "processed_files": processed_count,
        "archived_files": archived_count,
        "quarantined_files": invalid_count,
        "valid_rate": round(valid_rate, 1),
        "invalid_rate": round(invalid_rate, 1),
        "valid_files_by_classification": classification_counts,
        "invalid_files_by_reason": invalid_reason_counts,
        "top_invalid_filenames": invalid_filenames[:5],
        "warnings": warnings,
    }


def print_summary(files, moved_files, start_time, rules_source, ignored_files, warnings=None, run_id=""):
    summary = generate_summary(files, moved_files, start_time, rules_source, ignored_files, warnings, run_id=run_id)

    print("\nProcessing summary")
    print("------------------")
    if summary['run_id']:
        print(f"Run ID: {summary['run_id']}")
    print(f"Config rules source: {summary['config_rules_source']}")
    print(f"Base directory: {summary['base_directory']}")
    print(f"Input folder: {summary['input_folder']}")
    print(f"Archive folder: {summary['archive_folder']}")
    print(f"Processed folder: {summary['processed_folder']}")
    print(f"Quarantine folder: {summary['quarantine_folder']}")
    print(f"Log file: {summary['log_file']}")
    print(f"JSONL log file: {summary['log_jsonl_file']}")
    print(f"Pretty log file: {summary['log_pretty_file']}")
    print(f"Summary file: {summary['summary_file']}")
    print(f"Start time: {summary['start_time']}")
    print(f"End time: {summary['end_time']}")
    print(f"Total files scanned: {summary['total_files_scanned']}")
    print(f"Ignored files: {len(summary['ignored_files'])}")
    if summary['ignored_files']:
        print("Ignored filenames:")
        for filename in summary['ignored_files']:
            print(f"  {filename}")
    print(f"Processed files: {summary['processed_files']}")
    print(f"Archived files: {summary['archived_files']}")
    print(f"Quarantined files: {summary['quarantined_files']}")
    print(f"Valid rate: {summary['valid_rate']:.1f}%")
    print(f"Invalid rate: {summary['invalid_rate']:.1f}%")

    if summary['valid_files_by_classification']:
        print("\nValid files by classification:")
        for classification, count in sorted(summary['valid_files_by_classification'].items()):
            print(f"  {classification}: {count}")

    if summary['invalid_files_by_reason']:
        print("\nInvalid files by reason:")
        for reason, count in sorted(summary['invalid_files_by_reason'].items()):
            print(f"  {reason}: {count}")

    if summary['warnings']:
        print("\nWarnings:")
        for warning in summary['warnings']:
            print(f"  {warning}")

    if summary['top_invalid_filenames']:
        print(f"\nTop {len(summary['top_invalid_filenames'])} invalid filenames:")
        for filename in summary['top_invalid_filenames']:
            print(f"  {filename}")

    print(f"Elapsed time: {summary['elapsed_seconds']} seconds")
    return summary


def write_summary_file(summary, path=SUMMARY_FILE):
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if isinstance(path, str):
            path = Path(path)
        with path.open("w", encoding="utf-8") as summary_file:
            json.dump(summary, summary_file, indent=2)
    except OSError as exc:
        print(f"Warning: could not write summary file {path}: {exc}")
    return path
