"""
Quick Vibe Coded - File Restoration Script for easy Testing and Debugging
"""

from pathlib import Path
import argparse

ROOT_DIR = Path(__file__).resolve().parent
INPUT_DIR = ROOT_DIR / "data" / "input"
SOURCE_DIRS = [ROOT_DIR / "data" / "processed", ROOT_DIR / "data" / "quarantine"]


def collect_files(directories):
    for directory in directories:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.name != ".gitkeep":
                yield path


def restore_files(force: bool = False):
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    moved = []
    skipped = []

    for source_path in collect_files(SOURCE_DIRS):
        destination_path = INPUT_DIR / source_path.name

        if destination_path.exists() and not force:
            skipped.append(source_path)
            continue

        destination_path = destination_path if force else INPUT_DIR / source_path.name
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.replace(destination_path)
        moved.append(source_path)

    return moved, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Restore moved files from processed/quarantine back into data/input."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite files in data/input if they already exist.",
    )
    args = parser.parse_args()

    moved, skipped = restore_files(force=args.force)

    print(f"Restored {len(moved)} file(s) to {INPUT_DIR}")
    if skipped:
        print(f"Skipped {len(skipped)} file(s) because they already exist in input:")
        for path in skipped:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
