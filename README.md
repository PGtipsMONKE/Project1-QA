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

Supported configuration fields:
- `required_parts`: integer count of filename parts separated by `filename_separator`
- `filename_separator`: string to split the filename before extension
- `date_format`: date parsing format for the final filename segment
- `allowed_extensions`: optional list of extension values without leading dots
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
