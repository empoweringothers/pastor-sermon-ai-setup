# Python-Free Local File Fallback

Use this only when ChatGPT desktop Work or Codex has local file tools but no
Python launcher. Do not install Python merely to use the Pastor Assistant OS.

## Initialize

1. Resolve the OS-native local data folder:

   - macOS: `~/Library/Application Support/Valley Forge Baptist/Pastor Assistant OS`
   - Windows: `%LOCALAPPDATA%\Valley Forge Baptist\Pastor Assistant OS`

2. Confirm that Windows `LOCALAPPDATA` is present and absolute. Never fall back
   to the current folder.
3. Inspect the target. If it contains files but no recognized
   `state/os-state.json`, stop rather than adopting or overwriting it.
4. Show the redacted target and require the exact reply
   `YES, CREATE PASTOR ASSISTANT OS`.
5. Copy only missing files from `assets/workspace-template/` with local file
   tools. Create `state/os-state.json`, `audit/rule-changes.jsonl`, `backups/`,
   `proposals/`, `projects/`, and `reviews/`. Never overwrite a profile or rule
   file in a recognized OS.
6. Use private owner-only file permissions when the host exposes that control.

The state file must contain only:

```json
{
  "schema_version": 1,
  "product": "pastor-assistant-os",
  "created_at": "<UTC ISO timestamp>",
  "updated_at": "<UTC ISO timestamp>",
  "memory_policy": "explicit-approved-rules-only"
}
```

## Load context

Read `profile/church-profile.md`, `profile/pastor-preferences.md`, and
`learning/approved-rules.md`. Do not paste them wholesale into the chat or a
deliverable. Use only the parts relevant to the current task.

## Save a rule

1. Fix and verify the current work.
2. Display one sanitized generalized rule and require
   `YES, SAVE THIS RULE`.
3. Re-read `learning/rules.json` immediately before writing.
4. Back up `rules.json`, `approved-rules.md`, and
   `promotion-candidates.json` under a new timestamped `backups/` folder.
5. Add or confirm one approved `this_pastor` rule with ID, category, reason,
   timestamps, and occurrence count. Never store sermon text or private data.
6. Write a complete temporary JSON file, parse it, then replace `rules.json`.
7. Regenerate `approved-rules.md` from active rules.
8. Append a metadata-only event to `audit/rule-changes.jsonl`; do not repeat the
   rule text in the audit.
9. Re-read all three files. If any check fails, restore the backup and report
   that nothing durable was learned.

Do not save while another task is editing the OS. Do not change plugin files,
GitHub, or church-wide rules.

## Doctor check

Verify required files, parse all JSON, compare active rules with the generated
Markdown list, and report only health, counts, and redacted errors. Never print
rule text or a full private path in a setup report.
