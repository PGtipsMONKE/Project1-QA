#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/reports/backups}"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARCHIVE_NAME="fileflow_reports_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"

mkdir -p "${BACKUP_DIR}"

if ! command -v tar >/dev/null 2>&1; then
	echo "Error: tar is required but was not found in PATH." >&2
	exit 127
fi

cd "${PROJECT_ROOT}"
tar \
	--exclude='reports/backups/*' \
	-czf "${ARCHIVE_PATH}" \
	logs \
	reports

echo "Backup created: ${ARCHIVE_PATH}"
