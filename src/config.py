import json
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "config.json"

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
    "duplicate_policy": "quarantine"
}


def load_rules_from_config():
    """Load rule configuration from config/config.json, or return defaults."""
    warnings = []
    if not CONFIG_FILE.exists():
        message = f"Config file not found at {CONFIG_FILE}. Using built-in defaults."
        print(message)
        warnings.append(message)
        return DEFAULT_RULES.copy(), "built-in defaults", warnings

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as exc:
        message = f"Warning: could not parse config file {CONFIG_FILE}: {exc}. Using built-in defaults."
        print(message)
        warnings.append(message)
        return DEFAULT_RULES.copy(), "built-in defaults", warnings
    except Exception as exc:
        message = f"Warning: could not read config file {CONFIG_FILE}: {exc}. Using built-in defaults."
        print(message)
        warnings.append(message)
        return DEFAULT_RULES.copy(), "built-in defaults", warnings

    if not isinstance(config, dict):
        message = f"Warning: config file {CONFIG_FILE} must contain a JSON object. Using built-in defaults."
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

    return rules, "config file", warnings
