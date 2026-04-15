# Backlog

## Core user story
“As a user, I want to drop files into a shared folder and run a simple tool that validates, organises, logs, and reports on those files so that the shared area stays tidy and usable.”

## Goals
- Validate shared team files by filename and date format.
- Organise valid files into appropriate processed folders.
- Quarantine invalid files for review.
- Log processing activity and report summary metrics.

## User stories
### 1. File intake and validation
**As a user,**
I want the tool to scan files placed in `data/input` and check whether their filenames follow the standard pattern,
**so that** only correctly named files are accepted for processing.

**Acceptance Criteria:**
- A correctly named file is marked valid.
- An incorrectly named file is marked invalid.
- An invalid date format is rejected.
- The script does not crash on unexpected filenames.

### 2. File classification and routing
**As a user,**
I want valid files to be classified and moved to the right destination folder,
**so that** files are organised automatically and the shared area stays tidy.

**Acceptance Criteria:**
- Files starting with `invoice` and valid move to `data/processed/invoices`.
- Files starting with `report` and valid move to `data/processed/reports`.
- Files starting with `notes` and valid move to `data/processed/notes`.
- Invalid files move to `data/quarantine`.

### 3. Logging and summary reporting
**As a user,**
I want the tool to write a simple processing log and print a summary,
**so that** I can verify what happened during each run.

**Acceptance Criteria:**
- Each processed file generates a log entry with status and destination.
- The console output includes counts for total, valid, and invalid files.
- The log and summary are easy to read.

## Tasks
1. Read files from `data/input`.
2. Validate filenames against the standard naming pattern:
   - `<type>_<context>_<date>.<ext>`
   - Example standard names:
     - `notes_meeting_15-APR-2026.md`
     - `report_training_20-JUN-2026.md`
3. Classify and route valid files by prefix.
4. Move invalid files to `data/quarantine`.
5. Write a log entry for each file.
6. Print a console summary.

## Classification rules
| Condition                       | Classification | Destination               |
| ------------------------------- | -------------- | ------------------------- |
| Starts with `invoice` AND valid | invoice        | `data/processed/invoices` |
| Starts with `report` AND valid  | report         | `data/processed/reports`  |
| Starts with `notes` AND valid   | notes          | `data/processed/notes`    |
| Invalid filename                | invalid        | `data/quarantine`         |

## Implementation notes
- Keep the first version simple and easy to extend.
- Focus on readable, beginner-friendly code.
- Use the existing repository folders: `data/input`, `data/processed`, `data/quarantine`, and `logs`.

## Future enhancements
- Add classification rules based on file age relative to the current date.
- Add classification rules based on file type extension such as `.pdf`, `.csv`, `.txt`.
- Consider adding retry or notification support for quarantined files.