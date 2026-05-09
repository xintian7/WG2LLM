# Changelog

This file uses an entry format of:

- Date: YYYY-MM-DD
- Version: vX.Y (see `.env` for version value)
- Main activities: bullet list

---

Date: 2026-05-08
Version: v0.1

Main activities:
- Initial app scaffold for WGII AI Assistant and first Streamlit workflow setup.
- Added primary action buttons for AI-use support workflows.
- Added dependency management in `requirements.txt` and supporting markdown documentation.
- Added initial user-guide content and repository housekeeping updates.
- Added Notion integration groundwork for logging/submission workflows.
- Added sidebar roadmap (To-do section) for planned feature releases.
- Applied iterative minor improvements and stability edits.

Notes & next steps:
- Continue expanding under-development buttons into production features.
- Keep `requirements.txt` aligned with deployed runtime packages.
- Add lightweight test/checklist coverage before each release update.

---

Date: 2026-05-09
Version: v0.1.1

Main activities:
- Added a dedicated feedback component in `functions/feedback_form.py` with Notion submission support.
- Configured feedback form defaults for this app: `app_name=TSU_LLM`, `NOTION_TOKEN`, and `DATABASE_ID_feedback`.
- Added server-side validation for required message, conditional email requirement, and basic email format checks.
- Updated feedback copy with finalized user-facing text and required-field instruction.
- Changed feedback access flow to a sidebar hyperlink and dedicated routed page (`?page=feedback`).
- Placed feedback entry point in the sidebar between User Guide and To-do.
- Simplified redirected feedback page by removing extra heading/introduction to focus on form completion.
- Updated user guide text to document the Give feedback capability.

Notes & next steps:
- Verify Notion database property names match current payload keys in production.
- Add optional anti-spam/rate-limit handling for public feedback submissions.
- Consider storing feedback submission telemetry (success/failure counts) for maintenance.

---

Date: 2026-05-09
Version: v0.1b

Main activities:
- Refactored the main app into modular panel/button components under functions to reduce app_wp2llm.py size and improve maintainability.
- Merged and removed the legacy button_check_aicase helper by integrating its logic into the AI guidance panel module.
- Added Notion logging support for separate token usage fields from API responses: token_input (prompt tokens) and token_output (completion tokens).
- Updated AI use case, rephrase, and grammar features to capture and write token_input/token_output to Notion.
- Added sidebar section "Other WGII TSU Apps" and linked the WGII Literature App.
- Performed final workspace diagnostics sweep with no reported errors.

Notes & next steps:
- Confirm token_input/token_output property types in production Notion DB (number preferred) and validate one end-to-end submission for each of the first three buttons.
- Consider adding a small admin diagnostics panel to display the latest API token usage and Notion write status for easier release checks.

---

Last updated: 2026-05-09
