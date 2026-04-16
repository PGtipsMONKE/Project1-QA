#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
	echo "Error: Python executable not found: ${PYTHON_BIN}" >&2
	exit 127
fi

# Ensure expected directories exist so volume mounts start cleanly.
mkdir -p \
	"${PROJECT_ROOT}/data/input" \
	"${PROJECT_ROOT}/data/processed" \
	"${PROJECT_ROOT}/data/quarantine" \
	"${PROJECT_ROOT}/logs"

cd "${PROJECT_ROOT}"
exec "${PYTHON_BIN}" "${PROJECT_ROOT}/src/main.py" "$@"