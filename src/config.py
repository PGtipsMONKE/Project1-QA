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
    }
}


def load_rules_from_config():
    """Load rule configuration from config/config.json, or return defaults."""
    if not CONFIG_FILE.exists():
        print(f"Config file not found at {CONFIG_FILE}. Using built-in defaults.")
        return DEFAULT_RULES.copy(), "built-in defaults"

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as exc:
        print(f"Warning: could not parse config file {CONFIG_FILE}: {exc}. Using built-in defaults.")
        return DEFAULT_RULES.copy(), "built-in defaults"
    except Exception as exc:
        print(f"Warning: could not read config file {CONFIG_FILE}: {exc}. Using built-in defaults.")
        return DEFAULT_RULES.copy(), "built-in defaults"

    if not isinstance(config, dict):
        print(f"Warning: config file {CONFIG_FILE} must contain a JSON object. Using built-in defaults.")
        return DEFAULT_RULES.copy(), "built-in defaults"

    rules = DEFAULT_RULES.copy()
    rules["classification_prefixes"] = DEFAULT_RULES["classification_prefixes"].copy()

    if isinstance(config.get("required_parts"), int):
        rules["required_parts"] = config["required_parts"]

    if isinstance(config.get("filename_separator"), str):
        rules["filename_separator"] = config["filename_separator"]

    if isinstance(config.get("date_format"), str):
        rules["date_format"] = config["date_format"]

    if config.get("allowed_extensions") is None:
        rules["allowed_extensions"] = None
    elif isinstance(config.get("allowed_extensions"), list) and all(isinstance(ext, str) for ext in config["allowed_extensions"]):
        rules["allowed_extensions"] = [ext.lower().lstrip(".") for ext in config["allowed_extensions"]]

    if isinstance(config.get("ignore_files"), list) and all(isinstance(item, str) for item in config["ignore_files"]):
        rules["ignore_files"] = config["ignore_files"]

    if isinstance(config.get("classification_prefixes"), dict) and all(
        isinstance(prefix, str) and isinstance(classification, str)
        for prefix, classification in config["classification_prefixes"].items()
    ):
        rules["classification_prefixes"] = config["classification_prefixes"].copy()

    return rules, "config file"
