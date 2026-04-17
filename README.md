# Project1-QA

## File Naming 
The standard for file naming will follow the following standard: \
<"type">_<"context">_<"date">.<"ext">

For example: \
<notes>_<meeting>_<15-APR-2026>
<report>_<training>_<20-JUN-2026>

## Configuration
`src/main.py` supports an optional JSON rule file at `config/config.json`.

CLI options:
- `--dry-run`: validate and compute routing destinations without moving files.
- `--config <path>`: load rules from a specific JSON file (relative paths are resolved from the project root).
- `--strict`: fail the run if configuration warnings are detected.

If the file is missing or malformed, the loader falls back to built-in defaults and continues processing.

Examples:

```bash
python src/main.py --dry-run
python src/main.py --config config/config.json
python src/main.py --strict
```

The pipeline also auto-creates missing `data/input`, `data/processed`, `data/quarantine`, and `data/archive` folders so it can run safely even when the workspace has not been initialized.

The pipeline also exports a JSON summary file to `logs/summary.json` after each run.

The pipeline writes per-file and lifecycle events to:
- `logs/process.log` as tab-separated rows (TSV)
- `logs/process.jsonl` as JSON Lines (one JSON object per event)
- `logs/process.pretty.log` as fixed-width aligned columns for easier human scanning

`process.log` columns:
- `timestamp`
- `run_id`
- `event_type`
- `filename`
- `source_path`
- `status`
- `archived`
- `destination_bucket`
- `destination_path`
- `classification`
- `reason_code`
- `reason_detail`

### Warnings
The tool reports warnings in the console and includes them in the summary JSON under `warnings`.
Common warning conditions include:
- invalid or missing config file values
- config keys with the wrong data type
- log or summary write failures due to filesystem issues

Supported configuration fields:
- `required_parts`: integer count of filename parts separated by `filename_separator`
- `filename_separator`: string to split the filename before extension
- `date_format`: date parsing format for the final filename segment
- `allowed_extensions`: optional list of extension values without leading dots
- `archive_before_date`: optional date string matching `date_format`; valid files older than this date go to `data/archive` instead of `data/processed` (use `null` to disable)
- `duplicate_policy`: what to do when a destination file already exists; one of `quarantine`, `overwrite`, or `rename`
- `ignore_files`: optional list of input names to skip when scanning
- `classification_prefixes`: prefix-to-classification mapping used by `classify_file()`

Example `config/config.json`:
```json
{
  "required_parts": 3,
  "filename_separator": "_",
  "date_format": "%d-%b-%Y",
  "allowed_extensions": [
    "txt",
    "csv",
    "md"
  ],
  "archive_before_date": null,
  "duplicate_policy": "quarantine",
  "ignore_files": [
    ".gitkeep"
  ],
  "classification_prefixes": {
    "invoice": "invoice",
    "report": "report",
    "notes": "notes"
  }
}
```

## Routing decision matrix

The final destination for each file is determined by validation result, `archive_before_date`, and `duplicate_policy`.

| Condition | duplicate_policy | Final status | Final destination |
| --- | --- | --- | --- |
| Filename is invalid (bad structure/date/ext) | any | invalid | `data/quarantine/<name>` |
| Filename is valid and date is older than `archive_before_date` | overwrite | valid | `data/archive/<name>` (replaces existing) |
| Filename is valid and date is older than `archive_before_date` | rename | valid | `data/archive/<name>_N` if needed |
| Filename is valid and date is older than `archive_before_date` | quarantine | valid if no duplicate, otherwise invalid | `data/archive/<name>` or `data/quarantine/<name>` on duplicate |
| Filename is valid and not archived | overwrite | valid | `data/processed/<classification>/<name>` (replaces existing) |
| Filename is valid and not archived | rename | valid | `data/processed/<classification>/<name>_N` if needed |
| Filename is valid and not archived | quarantine | valid if no duplicate, otherwise invalid | `data/processed/<classification>/<name>` or `data/quarantine/<name>` on duplicate |

Notes:
- `classification` comes from `classification_prefixes`, otherwise `other`.
- In `--dry-run`, the same routing logic is computed and logged, but no files are moved.
- If a filesystem move fails, the file is recorded as invalid with reason `filesystem error: ...`.

## Troubleshooting and runbook

### Exit behavior
- Exit code `0`: run completed.
- Exit code `1`: fatal exception occurred (for example strict-mode config warnings, unexpected I/O failure).

### Common failures

1. Strict mode failure
  - Symptom: `Error: fatal exception during processing: strict mode enabled and configuration warnings were found`
  - Cause: `--strict` was used and at least one config warning was emitted.
  - Fix: correct the config file (field types, values, date formats) or run without `--strict`.

2. Config fallback warnings
  - Symptom: warnings such as `could not parse config file ... Using built-in defaults.`
  - Cause: missing, unreadable, malformed, or invalid config.
  - Fix: validate JSON syntax and field types in the target config file.

3. Filesystem/permissions issues
  - Symptom: warnings when writing logs/summary, or `filesystem error: ...` reasons for routed files.
  - Cause: missing write permission, locked files, path issues.
  - Fix: verify write access to `data/` and `logs/`, and retry.

### Quick operational checks
- Run without moving files: `python src/main.py --dry-run`
- Validate alternate config file: `python src/main.py --config config/config.json --strict`
- Reset demo state: `scripts/reset_demo_data.sh`

## Script reference

| Script | Purpose | Key options / env | Side effects |
| --- | --- | --- | --- |
| `scripts/run_fileflow.sh` | Run pipeline entrypoint | Args forwarded to `src/main.py`; `PYTHON_BIN` override | Creates expected data/log directories, runs pipeline |
| `scripts/reset_demo_data.sh` | Move files back to `data/input` for repeatable demos | `--force`; `--no-clean-logs`; `PYTHON_BIN` override | Restores files from archive/processed/quarantine; clears logs unless `--no-clean-logs` |
| `scripts/backup_reports.sh` | Create timestamped backup archive | `BACKUP_DIR` override | Writes `tar.gz` backup; excludes backup directories from archive inputs |

## Bash scripts for container use

The scripts in `scripts/` are container-safe and resolve paths relative to the repository root, so they can be run from any working directory.

- `scripts/run_fileflow.sh`
  - Runs the pipeline with strict shell settings.
  - Creates required data/log directories if they do not exist.
  - Supports `PYTHON_BIN` override (default: `python3`).

- `scripts/reset_demo_data.sh`
  - Restores files from `data/processed`, `data/archive`, and `data/quarantine` back to `data/input` via `undo.py`.
  - Options:
    - `--force`: overwrite existing files in `data/input`.
    - `--no-clean-logs`: keep generated files in `logs/` (`process.log`, `process.jsonl`, `process.pretty.log`, `summary.json`).
  - Supports `PYTHON_BIN` override (default: `python3`).

- `scripts/backup_reports.sh`
  - Creates a timestamped `tar.gz` archive containing `logs/` and `reports/`.
  - Excludes backup directories from the archive (`reports/backups/` and the path provided by `BACKUP_DIR` when it is inside the project).
  - Supports `BACKUP_DIR` override (default: `reports/backups`).

Example in a Linux container:

```bash
chmod +x scripts/*.sh
./scripts/run_fileflow.sh
./scripts/backup_reports.sh
./scripts/reset_demo_data.sh --force
```
