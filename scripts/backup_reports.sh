#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/reports/backups}"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARCHIVE_NAME="fileflow_reports_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
BACKUP_DIR_REL=""

mkdir -p "${BACKUP_DIR}"

# If backups are stored under the project root, exclude that subtree from archive inputs.
if [[ "${BACKUP_DIR}" == "${PROJECT_ROOT}"/* ]]; then
	BACKUP_DIR_REL="${BACKUP_DIR#${PROJECT_ROOT}/}"
fi

if ! command -v tar >/dev/null 2>&1; then
	echo "Error: tar is required but was not found in PATH." >&2
	exit 127
fi

cd "${PROJECT_ROOT}"
TAR_ARGS=(
	"-czf" "${ARCHIVE_PATH}"
	"--exclude=reports/backups"
	"--exclude=reports/backups/*"
)

if [[ -n "${BACKUP_DIR_REL}" ]]; then
	TAR_ARGS+=("--exclude=${BACKUP_DIR_REL}")
	TAR_ARGS+=("--exclude=${BACKUP_DIR_REL}/*")
fi

tar "${TAR_ARGS[@]}" logs reports

echo "Backup created: ${ARCHIVE_PATH}"
