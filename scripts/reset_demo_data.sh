#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

FORCE=false
CLEAN_LOGS=true

usage() {
	cat <<'EOF'
Usage: scripts/reset_demo_data.sh [options]

Restore processed and quarantined files back into data/input.

Options:
	--force          Overwrite existing files in data/input.
	--no-clean-logs  Keep all generated log files and summary output.
	-h, --help       Show this help message.
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--force)
			FORCE=true
			shift
			;;
		--no-clean-logs)
			CLEAN_LOGS=false
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Error: unknown option: $1" >&2
			usage >&2
			exit 2
			;;
	esac
done

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
	echo "Error: Python executable not found: ${PYTHON_BIN}" >&2
	exit 127
fi

mkdir -p "${PROJECT_ROOT}/logs"

UNDO_ARGS=()
if [[ "${FORCE}" == "true" ]]; then
	UNDO_ARGS+=("--force")
fi

cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" "${PROJECT_ROOT}/undo.py" "${UNDO_ARGS[@]}"

if [[ "${CLEAN_LOGS}" == "true" ]]; then
	rm -f \
		"${PROJECT_ROOT}/logs/process.log" \
		"${PROJECT_ROOT}/logs/process.jsonl" \
		"${PROJECT_ROOT}/logs/process.pretty.log" \
		"${PROJECT_ROOT}/logs/summary.json"
	echo "Cleared logs/process.log, logs/process.jsonl, logs/process.pretty.log, and logs/summary.json"
fi

echo "Demo data reset complete."
