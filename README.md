# Project1-QA

## File Naming 
The standard for file naming will follow the following standard: \
<"type">_<"context">_<"date">.<"ext">

For example: \
<notes>_<meeting>_<15-APR-2026>
<report>_<training>_<20-JUN-2026>

## Configuration
`src/main.py` supports an optional JSON rule file at `config/config.json`.

If the file is missing or malformed, the loader falls back to built-in defaults and continues processing.

The pipeline also auto-creates missing `data/input`, `data/processed`, and `data/quarantine` folders so it can run safely even when the workspace has not been initialized.

The pipeline also exports a JSON summary file to `logs/summary.json` after each run.

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

## Bash scripts for container use

The scripts in `scripts/` are container-safe and resolve paths relative to the repository root, so they can be run from any working directory.

- `scripts/run_fileflow.sh`
  - Runs the pipeline with strict shell settings.
  - Creates required data/log directories if they do not exist.
  - Supports `PYTHON_BIN` override (default: `python3`).

- `scripts/reset_demo_data.sh`
  - Restores files from `data/processed` and `data/quarantine` back to `data/input` via `undo.py`.
  - Options:
    - `--force`: overwrite existing files in `data/input`.
    - `--no-clean-logs`: keep `logs/process.log` and `logs/summary.json`.
  - Supports `PYTHON_BIN` override (default: `python3`).

- `scripts/backup_reports.sh`
  - Creates a timestamped `tar.gz` archive containing `logs/` and `reports/`.
  - Excludes existing backup archives under `reports/backups/`.
  - Supports `BACKUP_DIR` override (default: `reports/backups`).

Example in a Linux container:

```bash
chmod +x scripts/*.sh
./scripts/run_fileflow.sh
./scripts/backup_reports.sh
./scripts/reset_demo_data.sh --force
```
