import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "process.log"
SUMMARY_FILE = LOG_DIR / "summary.json"


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


def generate_summary(files, moved_files, start_time, rules_source, ignored_files):
    total_files = len(files)
    valid_count = sum(1 for entry in moved_files if entry["valid"])
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
        "config_rules_source": rules_source,
        "base_directory": str(BASE_DIR),
        "input_folder": str(Path(__file__).resolve().parent.parent / "data" / "input"),
        "processed_folder": str(Path(__file__).resolve().parent.parent / "data" / "processed"),
        "quarantine_folder": str(Path(__file__).resolve().parent.parent / "data" / "quarantine"),
        "log_file": str(LOG_FILE.relative_to(BASE_DIR)),
        "summary_file": str(SUMMARY_FILE.relative_to(BASE_DIR)),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "elapsed_seconds": elapsed.total_seconds(),
        "total_files_scanned": total_files,
        "ignored_files": [path.name for path in sorted(ignored_files, key=lambda p: p.name)],
        "processed_files": valid_count,
        "quarantined_files": invalid_count,
        "valid_rate": round(valid_rate, 1),
        "invalid_rate": round(invalid_rate, 1),
        "valid_files_by_classification": classification_counts,
        "invalid_files_by_reason": invalid_reason_counts,
        "top_invalid_filenames": invalid_filenames[:5],
    }


def print_summary(files, moved_files, start_time, rules_source, ignored_files):
    summary = generate_summary(files, moved_files, start_time, rules_source, ignored_files)

    print("\nProcessing summary")
    print("------------------")
    print(f"Config rules source: {summary['config_rules_source']}")
    print(f"Base directory: {summary['base_directory']}")
    print(f"Input folder: {summary['input_folder']}")
    print(f"Processed folder: {summary['processed_folder']}")
    print(f"Quarantine folder: {summary['quarantine_folder']}")
    print(f"Log file: {summary['log_file']}")
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

    if summary['top_invalid_filenames']:
        print(f"\nTop {len(summary['top_invalid_filenames'])} invalid filenames:")
        for filename in summary['top_invalid_filenames']:
            print(f"  {filename}")

    print(f"Elapsed time: {summary['elapsed_seconds']} seconds")
    return summary


def write_summary_file(summary, path=SUMMARY_FILE):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if isinstance(path, str):
        path = Path(path)
    with path.open("w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2)
    return path
