# Browser Skills Registry

This folder contains trusted or draft Browser Operator Skill Layer (BOSL) skill files.

Current status:

- Scaffolded on 2026-04-30.
- Skill files are declarative recipes, not execution authority.
- Only approved skills may be considered for future AOR/browser execution.
- Draft skills remain non-executable until a future workflow explicitly supports them.
- Shadow-plan proof can be run with `python -m runtime.browser_skills.shadow_runner <skill_id>`; this validates and logs a plan without launching a browser.

Rules:

- Do not store credentials, cookies, session tokens, local storage, or browser profile paths.
- Do not store raw absolute-only pixel coordinate recipes.
- Do not write candidates here directly from browser runs.
- Put untrusted candidates in `03_INPUTS/Browser-Skill-Candidates/`.
- Validate skill files with `runtime.browser_skills.validator` before promotion.
