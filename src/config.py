import json
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "config.json"
BASE_DIR = Path(__file__).resolve().parent.parent

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
    },
    "duplicate_policy": "quarantine",
    "archive_before_date": None,
}


def load_rules_from_config(config_path=None):
    """Load rule configuration from a JSON file, or return defaults."""
    warnings = []
    config_file = Path(config_path) if config_path else CONFIG_FILE
    if config_path and not config_file.is_absolute():
        config_file = BASE_DIR / config_file

    if not config_file.exists():
        message = f"Config file not found at {config_file}. Using built-in defaults."
        print(message)
        warnings.append(message)
        return DEFAULT_RULES.copy(), "built-in defaults", warnings

    try:
        with config_file.open("r", encoding="utf-8") as config_handle:
            config = json.load(config_handle)
    except json.JSONDecodeError as exc:
        message = f"Warning: could not parse config file {config_file}: {exc}. Using built-in defaults."
        print(message)
        warnings.append(message)
        return DEFAULT_RULES.copy(), "built-in defaults", warnings
    except Exception as exc:
        message = f"Warning: could not read config file {config_file}: {exc}. Using built-in defaults."
        print(message)
        warnings.append(message)
        return DEFAULT_RULES.copy(), "built-in defaults", warnings

    if not isinstance(config, dict):
        message = f"Warning: config file {config_file} must contain a JSON object. Using built-in defaults."
        print(message)
        warnings.append(message)
        return DEFAULT_RULES.copy(), "built-in defaults", warnings

    rules = DEFAULT_RULES.copy()
    rules["classification_prefixes"] = DEFAULT_RULES["classification_prefixes"].copy()

    if isinstance(config.get("required_parts"), int):
        rules["required_parts"] = config["required_parts"]
    elif "required_parts" in config:
        message = "Ignored 'required_parts' in config because it must be an integer."
        print(message)
        warnings.append(message)

    if isinstance(config.get("filename_separator"), str):
        rules["filename_separator"] = config["filename_separator"]
    elif "filename_separator" in config:
        message = "Ignored 'filename_separator' in config because it must be a string."
        print(message)
        warnings.append(message)

    if isinstance(config.get("date_format"), str):
        rules["date_format"] = config["date_format"]
    elif "date_format" in config:
        message = "Ignored 'date_format' in config because it must be a string."
        print(message)
        warnings.append(message)

    if config.get("allowed_extensions") is None:
        rules["allowed_extensions"] = None
    elif isinstance(config.get("allowed_extensions"), list) and all(isinstance(ext, str) for ext in config["allowed_extensions"]):
        rules["allowed_extensions"] = [ext.lower().lstrip(".") for ext in config["allowed_extensions"]]
    elif "allowed_extensions" in config:
        message = "Ignored 'allowed_extensions' in config because it must be a list of strings."
        print(message)
        warnings.append(message)

    if isinstance(config.get("ignore_files"), list) and all(isinstance(item, str) for item in config["ignore_files"]):
        rules["ignore_files"] = config["ignore_files"]
    elif "ignore_files" in config:
        message = "Ignored 'ignore_files' in config because it must be a list of strings."
        print(message)
        warnings.append(message)

    if isinstance(config.get("classification_prefixes"), dict) and all(
        isinstance(prefix, str) and isinstance(classification, str)
        for prefix, classification in config["classification_prefixes"].items()
    ):
        rules["classification_prefixes"] = config["classification_prefixes"].copy()
    elif "classification_prefixes" in config:
        message = "Ignored 'classification_prefixes' in config because it must be a mapping of strings to strings."
        print(message)
        warnings.append(message)

    if isinstance(config.get("duplicate_policy"), str) and config["duplicate_policy"] in {"quarantine", "overwrite", "rename"}:
        rules["duplicate_policy"] = config["duplicate_policy"]
    elif "duplicate_policy" in config:
        message = "Ignored 'duplicate_policy' in config because it must be one of 'quarantine', 'overwrite', or 'rename'."
        print(message)
        warnings.append(message)

    if config.get("archive_before_date") is None:
        rules["archive_before_date"] = None
    elif isinstance(config.get("archive_before_date"), str):
        try:
            rules["archive_before_date"] = datetime.strptime(config["archive_before_date"], rules["date_format"]).date()
        except ValueError:
            message = (
                "Ignored 'archive_before_date' in config because it must match "
                f"the configured date_format ({rules['date_format']})."
            )
            print(message)
            warnings.append(message)
        except Exception as exc:
            message = f"Ignored 'archive_before_date' due to unexpected error: {exc}."
            print(message)
            warnings.append(message)
    elif "archive_before_date" in config:
        message = "Ignored 'archive_before_date' in config because it must be a string or null."
        print(message)
        warnings.append(message)

    return rules, f"config file ({config_file})", warnings
