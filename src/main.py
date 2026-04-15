import os
from pathlib import Path

INPUT_DIR = Path("../data/input")
PROCESSED_DIR = Path("../data/processed")
QUARANTINE_DIR = Path("../data/quarantine")


def scan_files():
    return list(INPUT_DIR.glob("*"))


def main():
    files = scan_files()
    print(f"Found {len(files)} files")


if __name__ == "__main__":
    main()