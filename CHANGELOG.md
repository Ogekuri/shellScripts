# Changelog

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

[0.1.0]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.1.0
