# Changelog

## [0.2.0](https://github.com/Ogekuri/shellScripts/compare/v0.1.0..v0.2.0) - 2026-03-20
### ⛰️  Features
- Update github workflow.

### 🚜  Changes
- add centralized runtime config and --write-config [useReq] *(core)*
  - Update SRS requirement IDs for runtime configuration behavior.
  - Add config module loading ~/.config/shellScripts/config.json with default fallback merge.
  - Implement --write-config management command writing default JSON payload.
  - Refactor diff/edit/view wrappers and management commands to use runtime config.
  - Extend tests for startup config load, write-config, and runtime dispatch profiles.
  - Regenerate REFERENCES.md and update WORKFLOW.md runtime model.
- simplify GitHub automation requirement [useReq] *(requirements)*
  - Update REQUIREMENTS to remove release.yml-specific requirements.
  - Keep a single requirement for .github/workflows/release-uvx.yml presence.
  - Align WORKFLOW and regenerate REFERENCES for traceability.
- rename wrappers to diff/edit/view [useReq] *(commands)*
  - Update REQUIREMENTS for generic diff/edit/view command semantics.
  - Replace command registry keys and module paths; remove legacy wrappers.
  - Rename command modules and remove Double Commander naming from help.
  - Extend TST-006 checks for generic help naming and missing-arg behavior.
  - Update WORKFLOW call traces and regenerate REFERENCES index.
- ensure auth symlink before codex launch [useReq] *(cli-codex)*
  - add REQ-043 and REQ-044 for cli-codex auth symlink guard
  - update TST-005 scope and evidence mapping in REQUIREMENTS
  - implement auth symlink verification/creation and info output in cli_codex
  - extend cli launcher tests for create and no-op symlink paths
  - update WORKFLOW and regenerate REFERENCES
- BREAKING CHANGE: remove bin-links CLI registration and SRS refs [useReq] *(commands)*
  - update REQUIREMENTS: remove REQ-011 and REQ-012 and adjust PRJ-003
  - update TST-004 scope to REQ-013 only
  - remove bin-links from command registry dispatch map
  - refresh WORKFLOW call-trace and REFERENCES index
- replace release-uvx with release workflow path [useReq] *(release-workflow)*
  - Update SRS to encode release workflow behavior and artifact publication requirements.
  - Rename workflow file to .github/workflows/release.yml and remove legacy file path references.
  - Refresh workflow runtime model pointers for release execution unit and communication edge.
  - UID: useReq-shellScripts-work-20260319192252

### 📚  Documentation
- Update README.md document.

## [0.1.0](https://github.com/Ogekuri/shellScripts/releases/tag/v0.1.0) - 2026-03-19
### ⛰️  Features
- Initial Commit.
- Add uv.lock file.
- Initial commit.

### 🐛  Bug Fixes
- resolve static-check defects across CLI commands [useReq] *(core)*
  - remove unused imports and invalid f-strings in command modules\n- harden pdf-crop typing flow for Pylance and Ruff compliance\n- refresh docs/REFERENCES.md to reflect updated symbol metadata

### 🎯  Cover Requirements
- add requirement coverage suites for TST-001..TST-008 [useReq] *(tests)*
  - Add deterministic pytest suites mapped to uncovered TST requirements.\n- Verify CLI dispatch, installers, wrappers, PDF flows, and venv/tests behaviors.\n- Encode Doxygen-style metadata on test modules and helper stubs for traceability.

### 📚  Documentation
- align CLI usage documentation with current commands [useReq] *(readme)*
  - UID: 20260319T190156Z\n- replace README TODO placeholders with actionable usage docs\n- document management flags and full command inventory\n- add install/run examples for uv tool, uvx, and local launcher\n- describe command-specific runtime dependencies and key workflows
- refresh repository reference index [useReq] *(core)*
  - regenerate docs/REFERENCES.md from current source evidence\n- update module entrypoints and dependency anchors for agent navigation
- generate execution-unit runtime model [useReq] *(workflow)*
  - add deterministic Execution Units Index with stable IDs\n- map internal call-trace trees for launcher, main CLI, and release workflow\n- capture explicit communication edges and external boundaries
- Add docs/REQUIREMENTS.md file.


# History

- \[0.1.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.1.0
- \[0.2.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.2.0

[0.1.0]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.1.0
[0.2.0]: https://github.com/Ogekuri/shellScripts/compare/v0.1.0..v0.2.0
