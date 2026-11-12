# Changelog

## [0.26.2](https://github.com/Ogekuri/shellScripts/compare/v0.26.0..v0.26.2) - 2026-11-12
### ⛰️  Features
- Update gitalias config.
- add scripts/clean.sh build-artifact cleanup pipeline [useReq] *(clean)*
  REQUIREMENTS.md v0.16.0: DES-055, REQ-147, TST-019 added; REQ-144, REQ-136 updated; structure diagram and Section 4.1/5 evidence extended; scripts/clean.sh: resolve repo root, remove build/ and src/shellscripts.egg-info/, remove untracked dist archives, preserve tracked and non-generated dist entries; scripts/pre-release-check.sh: verify scripts/clean.sh executable bit and project structure; tests/test_tst_015_pre_release_check.py: cover clean.sh presence, syntax, executable bit, and structure; tests/test_tst_019_clean_script.py: new behavioral probes for cleanup and tracked-refusal; WORKFLOW.md: add PROC:clean execution unit and EDGE:005

### 🐛  Bug Fixes
- Remove files in dist/ dir.

### 🚜  Changes
- clean stale dist archives before packaging [useReq] *(build)*
  require removal of every dist archive of any version before the build tool runs; print one clean evidence line with the removed archive count; preserve non-generated dist entries; refine REQ-141 and add REQ-155 traceability; update WORKFLOW build unit evidence
- build in temporary directory independent of dist [useReq] *(pre-release-check)*
  REQUIREMENTS.md: DES-024/025/026/043/044, DES-065..068, REQ-081/138/139, REQ-152..154; pre-release-check.sh builds via mktemp -d and BUILD_DIST_DIR, validates artifacts there, removes the temporary directory on every termination path; pre-release-check.sh no longer reads, verifies, cleans, or modifies dist/ entries; build.sh resolves the output directory from BUILD_DIST_DIR (default dist) and passes --out-dir/--outdir; update TST-015 static parsing assertions, WORKFLOW.md runtime model
- remove and verify pre-existing dist artifacts [useReq] *(pre-release-check)*
  requirements: add DES-065, REQ-152, REQ-153 and TST-021; pre-release-check: delete every dist release archive before the build; pre-release-check: verify removal with PASS/FAIL evidence lines; build: document the shared bootstrap archive removal contract; tests: cover removal globs, ordering, and verification evidence; docs: update WORKFLOW pre-release call trace and communication edge
- track dist artifacts as optional, not required [useReq] *(release-pypi)*
  run scripts/build.sh and commit both dist artifacts (sdist + wheel); remove DES-054, DES-056, DES-059 that mandated build artifacts in dist/; reword DES-062 to consume build.sh archives without a commit mandate; release workflow drops setup-python and the tracked-dist preflight step; tests TST-012/TST-013/TST-015/TST-020 and script @satisfies realigned
- read archive epoch from tracked .build-epoch file [useReq] *(build)*
  build.sh resolves SOURCE_DATE_EPOCH from the version-controlled .build-epoch
  file instead of the HEAD committer timestamp; explicit env value wins
  missing/empty/malformed epoch aborts phase 1 with exit 1; build log prints SOURCE_DATE_EPOCH with its source token; .gitignore re-includes .build-epoch; pre-release structure check requires it; requirements add DES-063, DES-064, REQ-149..REQ-151 and extend TST-015; dist archives rebuilt at the deterministic epoch
- consume only committed dist artifacts, drop pre-check job [useReq] *(release-pypi)*
  release workflow removes the pre-release-check job; build-release needs check-branch only; GitHub Release and PyPI consume the dist archives pre-built by
  scripts/build.sh and committed in the tagged commit
  workflow no longer runs scripts/build.sh, scripts/pre-release-check.sh,
  uv sync, or any build-preparatory check (DES-057, DES-062)
  requirements drop DES-028, DES-029, REQ-083, TST-016; tests: TST-020 covers artifact-only job set, TST-012 mapping loses setup-uv
- consolidate cleanup into build.sh and purge all dist builds [useReq] *(build)*
  build.sh removes every dist archive of any version before building; build.sh performs post-build hygiene: build/, egg-info, dist metadata,
  dist temp files, and src __pycache__ trees
  scripts/clean.sh removed; cleanup now owns the build pipeline (DES-055,
  REQ-147, TST-019 dropped)
  pre-release integrity baseline excludes dist/ paths owned by the build; tests updated: TST-015 parses the new phases, obsolete TST-019 removed
- publish committed dist archives without building [useReq] *(release-pypi)*
  DES-056..DES-059: require tracked tag-commit archives; pytest gates publication without workflow builds.
- track build artifacts in dist/ under version control [useReq] *(dist)*
  REQUIREMENTS.md v0.15.0: DES-026, DES-042, DES-043, REQ-081, REQ-139, REQ-140 updated; DES-054 and TST-015 extended; .gitignore: removed dist/ archive exclusion rules; !dist/ and !dist/**/* retained; scripts/build.sh: clean_stale_artifacts leaves tracked dist archives untouched (REQ-141); scripts/pre-release-check.sh: cleanup removes only untracked dist archives; integrity check verifies them; tests/test_tst_015_pre_release_check.py: assertions aligned; dist re-include and no dist exclusion tests; WORKFLOW.md: PROC:pre-release-check cleanup call-trace and file-system boundary updated
- harden sdist and wheel contents and archive validation [useReq] *(build)*
  REQUIREMENTS: add DES-048..DES-053 and REQ-145..REQ-146; revise DES-046 and REQ-135; bump version 0.14.0.; pyproject.toml: raise setuptools floor to 77.0.0 for PEP 639 license fields.; MANIFEST.in: exclude tests/ from sdist; .gitignore re-includes MANIFEST.in.; scripts/build.sh: strip setup.cfg, MANIFEST.in, egg-info from sdist; remove post-build intermediates; validate sdist and wheel members.; WORKFLOW.md: PROC:build call trace updated for new build.sh functions.
- add build pipeline and harden pre-release checks [useReq] *(scripts)*
  Add scripts/build.sh producing validated sdist and wheel artifacts in dist/; Rework scripts/pre-release-check.sh with safety preflight, integrity checks, and signal-safe cleanup; Update .gitignore inverse rules to ignore generated dist archives; Update requirements, workflow model, and pre-release tests
- implement build script, pre-release check and update gitignore [useReq] *(scripts)*
  Add scripts/build.sh for reproducible distribution packaging into dist/; Update scripts/pre-release-check.sh with complete verification and cleanup pipeline; Update .gitignore to preserve inverted logic while targeting built artifacts; Update REQUIREMENTS.md with DES-040..DES-042, REQ-134..REQ-137; Update WORKFLOW.md and REFERENCES.md documentation

### ✨  Refactor
- remove unregistered bin_links module and its tests [useReq] *(commands)*
  Delete src/shell_scripts/commands/bin_links.py: module was absent from _COMMAND_MODULES and shipped in sdist and wheel.; Remove bin-links test cases from tests/test_tst_004_bin_links_clean.py; clean test cases are retained unchanged.; Regenerate usereq/docs/REFERENCES.md; REQUIREMENTS.md and WORKFLOW.md unchanged.; Command map from get_all_commands() is unchanged; pytest 161 passed; build.sh exit 0.
- harden cleanup traps, phase evidence, reproducibility [useReq] *(build)*
  Register EXIT, INT, and TERM traps removing generated build/ and src/shellscripts.egg-info/; Keep the tracked-file guard in remove_intermediate_build_trees; preserve exit status; Emit PASS/FAIL evidence per phase and a BUILD FAILED summary naming the phase; Resolve and export SOURCE_DATE_EPOCH (environment value or HEAD committer time); Pin sdist gzip header and member mtimes to SOURCE_DATE_EPOCH; Use Google Python style for embedded snippets; document build-backend constraints; Update WORKFLOW.md PROC:build; REQUIREMENTS.md unchanged; sdist/wheel member sets unchanged

### ◀️  Revert
- Roll back branch to 5e607e81 (5e607e8158d60ad1ba2fd228879c9afad712d872).
- Roll back branch to d48d3db8 (d48d3db8c60e67b4811aadf8b4de1aa91769c5aa).

## [0.26.0](https://github.com/Ogekuri/shellScripts/compare/v0.25.0..v0.26.0) - 2026-11-11
### 🐛  Bug Fixes
- render object and list leaves as box tables in --print [useReq] *(config-cli)*
  --print now details oggetto leaves as Chiave/Valore box tables (one
  sorted row per entry) and elenco leaves as indexed Valore tables (one
  row per element) instead of single-line JSON blobs, matching the
  tabular-detail requirement for dict/hash/array-shaped parameters;
  scalar leaves keep the REQ-096 = <JSON> rendering. Box-table lines now
  carry the tree continuation bars for non-final siblings, also for
  Sel/Valore and Valore/Significato tables. Extend the config-CLI HDT
  suite with red/green reproducer tests; update WORKFLOW.md call-trace
  roles and regenerate REFERENCES.md.
- enforce DES-034 schema parity gate on --print-raw [useReq] *(config-cli)*
  --print-raw now aborts with the explicit schema-mismatch error when
  CONFIG_SCHEMA and DEFAULT_RUNTIME_CONFIG diverge, matching the parity
  enforcement already applied to --print/--params/--get/--set/--unset
  (DES-032, DES-034); healthy-path REQ-094 behavior is unchanged.
  Add HDT reproducer suite tests/test_tst_018_config_cli.py covering the
  divergence gate for all six configuration commands plus REQ-094 verbatim
  output. Update WORKFLOW.md call-trace and regenerate REFERENCES.md.

### 🚜  Changes
- BREAKING CHANGE: rename --params management flag to --info [useReq] *(config-cli)*
  Replace the --params CLI flag with --info across dispatcher help and routing.; Rename config_cli.do_params to do_info and the info tree renderers.; Update REQ/DES/PRJ wording, WORKFLOW runtime model, REFERENCES index, and TST-018 tests.
- add bootstrap, atomic writes, and path-token management [useReq] *(config-cli)*
  Update SRS: REQ-094..REQ-113 rewritten, REQ-114..REQ-133 and
  DES-037..DES-039 added, TST-018 added for the configuration CLI.
  Bootstrap missing config.json with defaults (REQ-116) and persist
  --set/--unset atomically via same-directory temp rename (DES-037).
  Support array/map path tokens (:append/:+/:insert:<Idx>/:<Idx>/
  :<Idx>:<Field>/:<Key>) with re-indexing and range errors.
  Render --print/--params with optional sub-path, [Path] badges,
  default/custom indicators, and copy-pasteable command templates.
  Display all values in plain text without masking (REQ-098).; Enforce stdout/stderr and exit-code contract (REQ-132).
- drop git-root prerequisite from YOLO CLI launchers [useReq] *(ai-commands)*
  YOLO AI CLI commands (agy, claude, codex, copilot, opencode) now execute
  only the registry-defined command vector without Git repository root
  validation and without the project-root error path. CTN-005 scope is
  narrowed to non-YOLO project-context commands; REQ-014/015/017/018/085
  execution semantics unchanged. Test mocks, WORKFLOW call-traces, and
  requirements evidence aligned with the new contract.
- translate Italian user-facing text to English [useReq] *(config-cli)*
  Translate every Italian user-facing string, schema label, and evidence
  token to English per new CTN-007 and updated REQ-060, REQ-097,
  REQ-101, REQ-106, REQ-107..REQ-113: schema kinds (string, integer,
  boolean, selection, list, object), table headers (Sel/Value,
  Value/Meaning, Key/Value, Key/Format, Field/Format), input-example
  notes, --unset warning, req skip-evidence token, and the version-check
  update line; sync SRS, WORKFLOW.md, REFERENCES.md, and unit tests;
  logic and behavior preserved (136 tests pass, static-check clean).
- add input examples and shape tables to --params [useReq] *(config-cli)*
  --params now renders every option with its input type, short
  description, and schema-declared input example (REQ-110/111):
  scalars get an inline (Esempio di input:) suffix, selections get an
  example continuation line below the Valore/Significato table,
  oggetto options get a JSON-object note plus a Chiave/Formato
  default-structure table (REQ-112), and elenco options get a
  JSON-array note plus an element-format table (REQ-113). OptionSpec
  declares a mandatory example token (DES-036); SRS bumped to 0.8.0
  with REQ-110..113 and DES-036. HDT suite extended to 136 passing
  tests; WORKFLOW.md call-trace and REFERENCES.md regenerated.
- BREAKING CHANGE: add schema-driven config CLI (--print-raw/--print/--params/--get/--set/--unset) [useReq] *(config)*
  Add src/shell_scripts/config_cli.py: declarative CONFIG_SCHEMA registry
  mirroring DEFAULT_RUNTIME_CONFIG with import-time parity enforcement
  Implement --print-raw raw file dump, --print box-drawing option tree with
  Sel/Valore selection tables and secret masking, --params hierarchy with
  Valore/Significato tables, and --get/--set/--unset over ':'-separated
  hierarchical paths with typed coercion, choice validation, env acquisition,
  and sorted-key persistence
  Route the new management flags in core.main with lazy module import and
  extend global help
  Requirements: add DES-032..DES-035, REQ-094..REQ-109 (config-CLI sync
  constraint); update WORKFLOW.md runtime model and REFERENCES.md
  Existing tests: 119 passed; static-check clean
- BREAKING CHANGE: remove kiro, gemini, and pi commands [useReq] *(commands)*
  Delete gemini.py, kiro.py, and pi.py launcher modules plus their _COMMAND_MODULES registry entries and HELP_SECTION_COMMANDS AI-section tokens.
  Remove REQ-016, REQ-019, REQ-068, and REQ-069 from SRS 0.6.35; rewrite TST-005 scope and purge affected Evidence rows.
  Drop gemini/kiro/pi launcher tests from the TST-005 suite and gemini/kiro help-row assertions from the TST-001 suite.
  Update README command list, git-prerequisite list, and pi usage example; purge WORKFLOW.md call-trace nodes.
  No backward-compatibility shims per explicit change request.
- refactor YOLO CLI launchers into shared registry [useReq] *(yolo-cli)*
  Add shared registry-based launcher _yolo_common with declarative YoloCliSpec records (DES-030, DES-031).
  agy, claude, codex, copilot, and opencode become thin modules executing the verified YOLO vectors: agy/claude --dangerously-skip-permissions, codex --yolo, copilot --yolo, opencode --auto (REQ-085, REQ-014, REQ-015, REQ-017, REQ-018).
  Remove codex auth-file synchronization and CODEX_HOME mutation (REQ-043, REQ-044 dropped).
  Inline help documents every executed option plus the copilot --allow-all alternative (REQ-086, REQ-092, REQ-093).
  Update TST-005 and TST-017 suites, README, SRS 0.6.34, WORKFLOW, REFERENCES.
- align --version report output columns [useReq] *(version-check)*
  REQUIREMENTS: reword REQ-075/REQ-084, add REQ-091 (label width 18); version_check: add REPORT_LABEL_WIDTH and format_version_report_line helper; version_check: emit Latest @ PyPI / Latest @ GitHub aligned report lines; core: print aligned Current Installed line for --version/--ver; tests: update TST-014 assertions to the aligned three-line report
- add --force flag for forced reinstall on --upgrade [useReq] *(upgrade)*
  Add --force selector to --upgrade and --upgrade --develop/--dev: the
  resolved upgrade command gets ' --force --reinstall --refresh' appended
  for a full re-download and reinstallation (REQ-088, REQ-089).
  Standard (non-forced) upgrade now runs the plain default install command:
  'uv tool install shellscripts' and the develop template without --force
  (REQ-004, REQ-087).
  Reject bare --force without --upgrade with error line and code 1 (REQ-090).; Document --force in inline help and README.md; update REQUIREMENTS.md,
  WORKFLOW.md, REFERENCES.md, and TST-014 unit tests.

## [0.25.0](https://github.com/Ogekuri/shellScripts/compare/v0.24.0..v0.25.0) - 2026-11-09
### ⛰️  Features
- add Antigravity CLI launcher with YOLO mode and alphabetical AI CLI help [useReq] *(agy)*
  Add agy command executing agy --dangerously-skip-permissions via blocking
  subprocess.run with inherited stdio, harmonized with other AI launchers (REQ-085)
  Render AI CLI launch tokens in alphabetical order in agy inline help (REQ-086); Register agy in static command map and global AI help section (DES-001, DES-014); Add TST-017 pytest suite covering argv vector, stdio inheritance, registry
  exposure, and alphabetical help listing
  Update SRS to 0.6.30 with REQ-085/REQ-086/TST-017 and refresh WORKFLOW/REFERENCES

### 🚜  Changes
- BREAKING CHANGE: remove ai-install command, installer module, requirements, and tests [useReq] *(ai-install)*
  Delete src/shell_scripts/commands/ai_install.py and tests/test_tst_003_ai_install.py; Deregister ai-install from static command map and global AI help section (DES-001, DES-014); Remove installer requirements REQ-006..REQ-010, REQ-067, REQ-072..REQ-074, DES-013, TST-003; Restrict PRJ-003 to AI CLI launch; bump SRS to 0.6.31; refresh WORKFLOW/REFERENCES; Update is_windows doc @satisfies after removing DES-013/REQ-008 (utils.py); Breaking: shellscripts ai-install now resolves as unknown command (REQ-002 path)
- render failed lookups as latest unknown with reason [useReq] *(version-check)*
  REQ-084: failed --version source lookups now print
  "<source> latest: unknown (<reason>)" in bright red instead of
  the old "<source> latest check failed: <reason>." line that
  dropped the version line entirely
  reuse _format_request_error so GitHub rate-limit (403/429),
  HTTP 404, and non-HTTP failures show the actual error reason
  REQUIREMENTS.md v0.6.29: REQ-075 scoped to successful lookups,
  REQ-084 added, TST-014 and evidence table extended
  tests: TST-014 assertions updated to normative failure output
  and new GitHub HTTP 404 failure case added

## [0.24.0](https://github.com/Ogekuri/shellScripts/compare/v0.23.0..v0.24.0) - 2026-11-08
### ⛰️  Features
- add pre-release-check.sh release verification pipeline [useReq] *(scripts)*
  Add executable scripts/pre-release-check.sh running mandatory
  pre-release checks: pytest suite with PYTHONPATH=src (.venv fallback),
  dist cleanup, sdist+wheel build via uv build with python3 -m build
  fallback, and sdist/wheel artifact verification.
  Fail-fast semantics with PASS/FAIL evidence lines; exit 1 on first
  failed check, exit 0 only when all checks pass (REQ-079, REQ-080).
  Add requirements DES-021..DES-025, REQ-079, REQ-080, TST-015 and
  static parsing tests in tests/test_tst_015_pre_release_check.py.
  Register PROC:pre-release-check execution unit in WORKFLOW.md.

### 🐛  Bug Fixes
- Fix version number in scripts file.
- add cross-device temp-output promotion in PDF TOC splits [useReq] *(pdf)*
  Add _promote_temp_output EXDEV fallback in pdf_split_by_toc and
  pdf_split_by_format so chunk promotion survives temp directories on
  a different filesystem; previously crashed with OSError EXDEV in
  pdf-split-by-toc and silently dropped chunk TOC in pdf-split-by-format.
  Add cross-device reproducer tests and cwd isolation for split flows
  (TST-007, REQ-031, REQ-032).
  Update WORKFLOW.md call traces and regenerate REFERENCES.md.
- replace invalid PyPI trove classifier blocking uploads [useReq] *(packaging)*
  PyPI upload of shellscripts-0.23.0 failed with 400 Bad Request: 'Topic :: Software Development :: Configuration Management' is not a valid classifier (verified absent from the canonical trove list at pypi.org).
  Replace it with the canonical 'Topic :: Software Development' entry so trusted-publishing uploads satisfy PyPI core-metadata validation (PRJ-007).
  Add TST-013-scope reproducer test validating every pyproject.toml classifier against an authoritative canonical-list snapshot, asserting the rejected entry stays absent and the canonical replacement is declared (failed pre-fix, passes post-fix). Suite: 121 passing.

### 🚜  Changes
- gate release pipeline on pre-release check job [useReq] *(release)*
  Add dedicated pre-release-check job to release-pypi.yml running
  scripts/pre-release-check.sh (unit tests, build, artifact gates)
  after uv sync --frozen, before any artifact creation (DES-028).
  Declare needs: [check-branch, pre-release-check] on build-release so
  failing tests skip build, attestation, changelog, GitHub release,
  and PyPI publication (DES-029, REQ-083).
  Add TST-016 with tests/test_tst_016_release_precheck_gating.py.; Update REQUIREMENTS.md (v0.6.28) and WORKFLOW.md runtime model.
- leave repo clean of generated artifacts after pre-release-check [useReq] *(scripts)*
  Add cleanup_artifacts EXIT trap removing dist, build, .pytest_cache,
  src/shellscripts.egg-info, and __pycache__ dirs under src/tests on
  both success and failure termination paths (DES-026, DES-027).
  Print parser-stable clean evidence line listing removed groups.; Guarantee no Git-tracked file is removed and repository is artifact
  free on success (REQ-081, REQ-082).
  Extend TST-015 and tests/test_tst_015_pre_release_check.py coverage.; Update REQUIREMENTS.md (v0.6.27) and WORKFLOW.md runtime model.

## [0.23.0](https://github.com/Ogekuri/shellScripts/compare/v0.22.0..v0.23.0) - 2026-11-07
### 🐛  Bug Fixes
- pin setup-uv to resolvable v10.3.3 tag [useReq] *(release-pypi)*
  GitHub runner 2.338.2 failed at 'Prepare all required actions': astral-sh/setup-uv@v10 is an unresolvable ref (no v10 major tag exists upstream; verified via GitHub API - only full semver tags like v10.3.3 exist).
  Pin the exact verified tag v10.3.3 (major 10, Node24 runtime, confirmed via upstream action.yml), keeping CTN-006/DES-015 compliance and restoring PRJ-005/PRJ-007/DES-016 workflow execution.
  Update TST-012 reproducer: extend pin-extraction regex to full-semver refs and set the approved setup-uv ref to v10.3.3 (failed pre-fix, passes post-fix). All other pinned refs verified resolvable; suite 120 passing.
- Fix .gitignore file.
- .gitignore file.

### 🚜  Changes
- BREAKING CHANGE: migrate version checks and release to PyPI trusted publishing [useReq] *(core)*
  Rename release-uvx.yml to release-pypi.yml and add an OIDC Trusted Publishing step gated on master tags (PRJ-007, DES-016, DES-017); release steps run for develop tags without PyPI publication.
  Startup update checks now query the PyPI JSON API (PRJ-004, DES-018); --ver/--version prints installed plus PyPI latest and GitHub latest lines (REQ-003, REQ-075, DES-020).
  --upgrade defaults to uv tool install shellscripts --force from PyPI (REQ-004); new --dev/--develop selector upgrades from the latest GitHub release tag (REQ-076, DES-019); bare selector rejected with code 1 (REQ-077); tag-resolution failure emits bright-red error and code 1 (REQ-078).
  README documents PyPI primary install and GitHub alternative; pyproject adds OS classifier; SRS 0.6.25; WORKFLOW.md and REFERENCES.md updated; tests updated and extended (TST-012..TST-014, 120 passing).
- migrate release workflow actions to Node24 runtimes [useReq] *(release-uvx)*
  Bump actions to Node24-native majors: checkout v4->v7, setup-python v5->v7, setup-uv v3->v10, attest-build-provenance v1->v4, action-gh-release v2->v3; changelog-builder stays v6 (v6.5 node24), all verified upstream.
  Add CTN-006 and DES-015 mandating Node24-or-newer JavaScript action runtimes in release-uvx.yml (SRS 0.6.24).
  Add TST-012 with tests/test_tst_012_workflow_runtime.py verifying the Node24 pin mapping and absence of transitional Node20 override env vars (FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 / ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION).
  Update WORKFLOW.md release unit boundaries, regenerate REFERENCES.md; release automation behavior unchanged, full pytest suite passes (105 tests).

### 📚  Documentation
- Update README.md file.

## [0.22.0](https://github.com/Ogekuri/shellScripts/compare/v0.21.0..v0.22.0) - 2026-07-08
### 🐛  Bug Fixes
- Update README.md file.

## [0.21.0](https://github.com/Ogekuri/shellScripts/compare/v0.20.0..v0.21.0) - 2026-04-14
### ◀️  Revert
- Roll back branch to 4fff5017 (4fff5017777d51608cf7bcbe7e956e970bf95576).

## [0.20.0](https://github.com/Ogekuri/shellScripts/compare/v0.19.0..v0.20.0) - 2026-04-14
### 🚜  Changes
- stop installing pi prompts in req bootstrap [useReq] *(req_cmd)*
  update REQ-050 and TST-010; remove pi:prompts from default req providers; filter pi:prompts from emitted req argv; refresh workflow, references, and targeted tests

## [0.19.0](https://github.com/Ogekuri/shellScripts/compare/v0.18.0..v0.19.0) - 2026-04-13
### 🚜  Changes
- BREAKING CHANGE: remove implicit --tools injection [useReq] *(pi)*
  Worktree: useReq-shellScripts-work-20260413094554
  Requirements: update REQ-068, REQ-069, and TST-005
  Implementation: remove default --tools handling from pi launcher
  Tests: verify unchanged pi argument forwarding in cli launcher suite
  Docs: update WORKFLOW.md and regenerate REFERENCES.md
- BREAKING CHANGE: remove --extra and always install pi notify [useReq] *(ai-install)*
  update REQ-073 and REQ-074 for mandatory pi-notify installation; remove ai-install --extra parsing and install git:github.com/ferologics/pi-notify after pi CLI; refresh TST-003 coverage and regenerate WORKFLOW and REFERENCES

## [0.18.0](https://github.com/Ogekuri/shellScripts/compare/v0.17.0..v0.18.0) - 2026-04-12
### 🚜  Changes
- gate pi extension install behind --extra [useReq] *(ai-install)*
  update REQ-073 and add REQ-074 for --extra semantics; implement ai-install optional --extra parser and gated _install_pi flow; extend TST-003 coverage for selector forwarding and extension gating; refresh WORKFLOW and REFERENCES entries for updated runtime behavior
- add pi.dev ai-install flow [useReq] *(ai_install)*
  update REQUIREMENTS with REQ-072/REQ-073 and TST-003 traceability; add pi.dev npm install plus extension install sequence in ai_install; update ai-install help, WORKFLOW call trace, and REFERENCES index

## [0.17.0](https://github.com/Ogekuri/shellScripts/compare/v0.16.0..v0.17.0) - 2026-04-12
### 🚜  Changes
- remove sudo from linux npm installs [useReq] *(ai-install)*
  update DES-013, REQ-008, and TST-003 for Linux no-sudo npm policy; implement runtime OS branch in ai_install._install_npm_tool; adjust ai-install unit tests for Linux/Windows no-sudo and macOS sudo; refresh WORKFLOW and REFERENCES for updated call-trace and symbols

### 📚  Documentation
- align CLI surface and usage docs [useReq] *(readme)*
  sync command list with active dispatcher mappings; document --write-config and runtime config keys; replace removed command examples and add req/pi/video flows

## [0.16.0](https://github.com/Ogekuri/shellScripts/compare/v0.15.0..v0.16.0) - 2026-04-12
### 🚜  Changes
- add .pi/skills to CLEANUP_PATHS [useReq] *(req_cmd)*
  src/shell_scripts/commands/req_cmd.py: appended ".pi/skills" to CLEANUP_PATHS tuple; REQ-048 coverage extended: .pi/skills is now removed alongside .pi/prompts on req run; docs/REQUIREMENTS.md: version 0.6.18 → 0.6.19 (YAML front matter bump)
- add pi:prompts provider and .pi/prompts cleanup path [useReq] *(req_cmd)*
  REQ-050 updated: hardcoded default providers now include pi:prompts alongside codex:skills; src/shell_scripts/config.py: appended "pi:prompts" to DEFAULT_RUNTIME_CONFIG["req"]["providers"]; src/shell_scripts/commands/req_cmd.py: appended ".pi/prompts" to CLEANUP_PATHS tuple; docs/WORKFLOW.md: updated get_req_profile call-trace description to reflect new defaults; docs/REQUIREMENTS.md: version 0.6.17 → 0.6.18

## [0.15.0](https://github.com/Ogekuri/shellScripts/compare/v0.14.0..v0.15.0) - 2026-04-12
### ⛰️  Features
- enforce git-root skip behavior for req and req --dirs [useReq] *(req_cmd)*
  Add REQ-070/REQ-071 and update TST-010 coverage for git-root validation.
  Implement target pre-checks that skip non-root directories with deterministic skippata evidence.
  Extend req command tests and refresh WORKFLOW/REFERENCES traceability artifacts.
- add pi.dev launcher with default tools behavior [useReq] *(pi)*
  Add the new  command to the command registry and AI help section.
  Define launcher behavior that forwards CLI args unchanged while appending default  only when no explicit tools option is provided.
  Update requirements, workflow, references, and launcher tests for REQ-068/REQ-069 traceability.

### 📚  Documentation
- Update README.md file.

## [0.14.0](https://github.com/Ogekuri/shellScripts/compare/v0.13.0..v0.14.0) - 2026-04-09
### 🚜  Changes
- enforce no-auto-update flag [useReq] *(copilot)*
  Update REQ-015 to require --no-auto-update for Copilot launcher.
  Pass --no-auto-update in src/shell_scripts/commands/copilot.py.
  Adjust launcher tests and workflow runtime model for the new argv contract.

## [0.13.0](https://github.com/Ogekuri/shellScripts/compare/v0.12.0..v0.13.0) - 2026-04-07
### 🐛  Bug Fixes
- retry Windows Copilot install on transient lock [useReq] *(ai-install)*
  add one retry path for Windows Copilot npm install failures; add a focused reproducer unit test for retry behavior; update workflow and references docs for the changed runtime behavior

### 🚜  Changes
- BREAKING CHANGE: align Kiro installer with stable manifest [useReq] *(ai-install)*
  Update DES-013, REQ-010, TST-003 and add REQ-067 for Kiro platform behavior.\nReplace hardcoded Kiro archive mappings with manifest-driven Linux ZIP resolution.\nSwitch Kiro source to prod.download.cli.kiro.dev/stable/latest manifest endpoint.\nImplement Linux package selection by architecture and libc class (gnu/musl).\nAdd explicit unsupported-platform errors for Kiro on Windows and macOS.\nExpand ai-install tests for manifest resolution and unsupported-platform handling.\nRefresh WORKFLOW and REFERENCES documentation for updated call trace and symbols.
- resolve Claude/Kiro packages by runtime OS [useReq] *(ai-install)*
  Update DES-013, REQ-009, REQ-010, and TST-003 for runtime-OS package resolution.\nRefactor ai-install Claude/Kiro download flows to select Linux/Windows/macOS artifacts.\nAdd Claude artifact fallback handling and runtime-OS archive selection for Kiro.\nExpand TST-003 unit coverage for runtime-OS package selection and fallback behavior.\nRefresh WORKFLOW and REFERENCES docs for updated installer call traces.\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

## [0.12.0](https://github.com/Ogekuri/shellScripts/compare/v0.11.0..v0.12.0) - 2026-04-07
### 🐛  Bug Fixes
- Fix opencode exec on Windows.
- Fix exit sequence.

### 🚜  Changes
- add auth copy evidence output [useReq] *(codex)*
  Update REQ-043 and REQ-044 to require informational output for both auth copy directions.
  Emit print_info evidence line after each auth.json copy in codex command flow.
  Extend TST-005 codex tests to assert both copy-evidence messages.
  Refresh WORKFLOW and REFERENCES to reflect updated codex runtime behavior.
- replace auth symlink flow with auth sync [useReq] *(codex)*
  Update REQ-043 and REQ-044 to require bidirectional auth.json copy synchronization.
  Copy auth.json from home to project before codex launch and copy back after termination.
  Adapt TST-005 codex launcher tests and regenerate workflow/reference docs.
- BREAKING CHANGE: rename AI launcher commands and group global help [useReq] *(core)*
- normalize docs and source line endings [useReq] *(core)*
  preserve merged requirement and terminal cleanup content while normalizing file EOLs; keep REQUIREMENTS, WORKFLOW, REFERENCES, core.py, and utils.py in consistent checkout format
- disable terminal raw mouse capture on exit [useReq] *(core)*
  update REQ-064 and add REQ-065 for explicit terminal mouse shutdown sequence; prepend ?9l mode-off escape before existing ?1000l..?1016l writes; align core/utils Doxygen metadata plus WORKFLOW and REFERENCES docs; verification: req --here --static-check and focused core pytest executed
- enforce terminal reset after child command exit [useReq] *(core)*
  Update REQ-064 to require inherited stdio, blocking wait, and terminal-state restore.; Capture stdin TTY state at CLI entry and restore raw/cbreak plus xterm mouse modes in main() finally.; Add utils terminal helpers with best-effort stty sane fallback for Git Bash and Unix terminals.; Update WORKFLOW runtime call-trace and regenerate REFERENCES for new symbols.
- normalize line endings post-merge [useReq] *(repo)*
  Normalize merged files to repository LF convention after worktree merge.
  No functional deltas; content changes are newline normalization only.
- use blocking subprocess runners [useReq] *(commands)*
  Update SRS to require subprocess.run for external command execution.
  Replace launcher/dispatch/video/pdf tiler process-replacement calls with blocking subprocess calls.
  Propagate child return codes and keep stdio inherited for interactive subprocesses.
  Align affected unit tests and regenerate workflow/reference docs.

## [0.11.0](https://github.com/Ogekuri/shellScripts/compare/v0.10.0..v0.11.0) - 2026-04-05
### 🐛  Bug Fixes
- CRLF will be replaced by LF.
- normalize launcher paths across platforms [useReq] *(launcher)*
  normalize launcher root path comparison across Git Bash and POSIX paths; replace readlink -f dependency with canonical cd/pwd resolution; update WORKFLOW and REFERENCES for launcher runtime model

### 🚜  Changes
- use token-based AI CLI execution [useReq] *(cli-launchers)*
  Update REQ-014/015/016/018/019/043 to remove hardcoded absolute binaries.
  Switch cli-codex, cli-copilot, cli-gemini, cli-opencode, and cli-kiro to command tokens.
  Adjust TST-005 launcher assertions and skip symlink-only codex tests when privilege is unavailable on Windows.
  Refresh WORKFLOW and regenerate REFERENCES for traceability.

## [0.10.0](https://github.com/Ogekuri/shellScripts/compare/v0.9.0..v0.10.0) - 2026-04-02
### 🚜  Changes
- report cleanup evidence for req [useReq] *(req_cmd)*
  Update REQ-048 and TST-010 for cleanup evidence output.
  Add REQ-062 and REQ-063 for deleted/skip reporting.
  Emit deterministic cleanup evidence for each predefined path.
  Differentiate deleted files and directories in req cleanup.
  Extend req command tests for deleted dir, deleted file, and skip cases.
  Refresh WORKFLOW and REFERENCES traces for req cleanup flow.

## [0.9.0](https://github.com/Ogekuri/shellScripts/compare/v0.8.0..v0.9.0) - 2026-04-01
### 🐛  Bug Fixes
- Fix git repository.

## [0.8.0](https://github.com/Ogekuri/shellScripts/compare/v0.7.0..v0.8.0) - 2026-03-30
### 🚜  Changes
- persist cooldown on all request outcomes [useReq] *(version-check)*
  Update version-check requirements for every request outcome
  Persist cooldown JSON after successful requests and request errors
  Keep default idle delay at 3600 seconds and error cooldown at 86400 seconds
  Add non-HTTP request error formatting and bright-red output handling
  Refresh workflow and references documentation
- update success and error cooldowns [useReq] *(version-check)*
  Req-Change-ID: useReq-shellScripts-work-20260330152925
  Update SRS cooldown values for version-check flow
  Set default success idle delay to 3600 seconds
  Set HTTP error idle delay to 86400 seconds
  Refresh workflow and references documentation
- force 1h cooldown on rate limits [useReq] *(version-check)*
  Req-Change-ID: useReq-shellScripts-work-20260330151242\nUpdate requirements for forced version checks and rate-limit cooldowns\nImplement fixed 3600s cooldown for HTTP 403/429 responses\nPersist idle_delay_seconds metadata in version cache JSON\nRefresh workflow and references documentation

## [0.7.0](https://github.com/Ogekuri/shellScripts/compare/v0.6.0..v0.7.0) - 2026-03-29
### ⛰️  Features
- add ffmpeg video2h264/video2h265 commands [useReq] *(video-conversion)*
  Append REQ-057/REQ-058 and TST-011 in REQUIREMENTS.md.
  Implement new command modules and register them in command map.
  Update WORKFLOW/REFERENCES and add unit tests for argv and help exposure.
- enforce external executable checks across command flows [useReq] *(core)*
  Append REQ-055 and REQ-056 to requirements specification.
  Introduce shared OS-aware executable detection and shell command executable parsing in utils.
  Add pre-execution guards to command runners based on activated option paths and fail with deterministic error message.
  Update unit tests, WORKFLOW runtime model, and regenerate REFERENCES index for traceability.

### 🐛  Bug Fixes
- isolate luminance sidecar temp artifacts [useReq] *(dng2hdr2jpg)*
  Defect: luminance backend could leave .pp3 sidecar files in caller cwd.
  Cause: backend subprocess inherited process cwd instead of temp workspace.
  Fix: run luminance-hdr-cli from merged TIFF parent temp directory and restore cwd.
  Tests: add failing reproducer for .pp3 leakage and verify pass after fix.
  Docs: update WORKFLOW and regenerate REFERENCES for symbol map alignment.
- tighten auto-zero p50 quantization and bit-depth clamp [useReq] *(dng2hdr2jpg)*
  add white-level scalar helper for shared bit-depth/preview normalization logic; clamp container-derived bits_per_color with white-level evidence; make EV quantization deterministic on midpoint floating residue; cap preview normalization denominator to min(preview max, raw white level); add three reproducer tests for bit-depth, quantization, and p50 normalization; update WORKFLOW and regenerate REFERENCES
- correct bits-per-color detection from RAW container [useReq] *(dng2hdr2jpg)*
  Fix incorrect bit-depth detection on DNG files where white_level reflects effective dynamic range instead of storage container depth.
  Add a failing reproducer unit test and implement container-bit-depth-first detection with white_level fallback.
  Update workflow/runtime docs and regenerate symbol references for traceability.

### 🚜  Changes
- default codex provider uses skills [useReq] *(req)*
  update REQ-050 to require codex:skills in hardcoded defaults; switch runtime req default provider from codex:prompts to codex:skills; align req-profile test and workflow/reference docs with new default
- soften auto-brightness to preserve scene key [useReq] *(dng2hdr2jpg)*
  Update REQ-088/REQ-090 for light EV-domain correction and bounded gain.
  Implement conservative brightness gain preserving low/high-key balance.
  Add and adjust regression tests for defaults and behavior.
  Update WORKFLOW and regenerate REFERENCES.
- limit auto-brightness gain on highlights [useReq] *(dng2hdr2jpg)*
  Update REQ-090 auto-brightness gain rule with p98 highlight cap.
  Apply p98-based gain limiter in auto-brightness pipeline.
  Add regression test for white-area over-brightening prevention.
  Update WORKFLOW and regenerate REFERENCES documentation.
- BREAKING CHANGE: refactor auto-brightness to BT709 [useReq] *(dng2hdr2jpg)*
  Update REQ-088/089/090/099 and implement BT.709 target-grey pipeline.
  Remove legacy AB knobs, port linear sRGB transfer helpers, and update tests/docs.
- make auto-brightness chroma-neutral [useReq] *(dng2hdr2jpg)*
  Update REQ-090/REQ-099/TST-011 for 16-bit chroma-neutral auto-brightness.
  Implement 16-bit luminance-only auto-brightness with equal RGB gain and anti-clipping cap.
  Replace convertScaleAbs usage with linear clamp-only autolevel mapping.
  Preserve scene-key targeting while removing LAB output reconstruction path.
  Add/adjust tests for 16-bit auto-brightness path and RGB-ratio neutrality checks.
  Regenerate REFERENCES.md and update WORKFLOW.md call-trace entries.
- update auto-adjust defaults [useReq] *(dng2hdr2jpg)*
  Update REQ-083 shared auto-adjust default values.
  Apply new defaults in dng2hdr2jpg constants.
  Refresh workflow and references documentation.
  Verify with req static check and targeted pytest suite.
- add auto pct scaling for adaptive EV and EV-zero [useReq] *(dng2hdr2jpg)*
  Update REQ-063/081/094/097 for --auto-zero-pct and --auto-ev-pct.
  Implement parsing, defaults (50), and downward 0.25 quantization toward zero.
  Apply scaling in auto-zero and auto-ev pipelines.
  Extend help text and update WORKFLOW/REFERENCES.
  Add/update TST-011 coverage for parser, defaults, help, and pipeline behavior.
- preserve low/high key in auto-brightness [useReq] *(dng2hdr2jpg)*
  Update REQ-088 and REQ-090 semantics for scene-key preserving gamma target.
  Add REQ-099 forbidding fixed global-mean forcing for low/high key scenes.
  Implement scene-key target derivation in auto-brightness pipeline.
  Update help/docs and regenerate WORKFLOW.md + REFERENCES.md.
  Add TST-011 coverage for new target derivation and gamma-target selection.
- preserve scene-key auto-zero EV assignment [useReq] *(dng2hdr2jpg)*
  Update REQ-097 and add REQ-098 for scene-key-preserving auto-zero.
  Implement adaptive auto-zero target selection for low/mid/high key scenes.
  Extend TST-011 tests to cover non-forced p50 target behavior.
  Update WORKFLOW and regenerate REFERENCES for changed symbol graph.
- constrain ev-zero to safe range [useReq] *(dng2hdr2jpg)*
  Update requirements to define SAFE_ZERO_MAX=(BASE_MAX-1) for EV-zero selectors.
  Constrain manual --ev-zero and auto-zero resolution to [-SAFE_ZERO_MAX,+SAFE_ZERO_MAX].
  Add safe EV-zero quantization helper preserving at least +/-1 EV bracket.
  Update runtime EV ceiling logging with SAFE_ZERO_MAX and keep MAX_BRACKET semantics.
  Adjust help text and validation messages to safe EV-zero range formula.
  Revise TST-011 coverage for safe bound acceptance and safe-range rejection.
  Update WORKFLOW runtime model and regenerate REFERENCES.
- add auto-zero and zero-centered merge [useReq] *(dng2hdr2jpg)*
  Update REQUIREMENTS for auto-zero EV center resolution and zero-centered luminance merge.
  Implement --auto-zero parser, EV-center resolver, and symmetric adaptive EV-delta around resolved center.
  Enforce manual/auto EV-zero exclusivity and bit-derived MAX constraints with quarter-step quantization.
  Change luminance-hdr-cli exposure list to -ev,0,+ev while preserving extraction centered on resolved ev_zero.
  Align encode stage to treat ev_zero extraction as 0EV reference without extra compensation gain.
  Extend TST-011 coverage for auto-zero parsing, center resolution, and zero-centered merge behavior.
  Regenerate REFERENCES and update WORKFLOW runtime model for new call flow.
- preserve ev-zero center in merged HDR [useReq] *(dng2hdr2jpg)*
  Update REQ-058/062/066/095 and TST-011 for merged-HDR center preservation.
  Apply ev_zero compensation gain 2^(ev_zero) in shared _encode_jpg stage.
  Pass ev_zero from run() to encoder for both enfuse and luminance flows.
  Add regression tests for encoder ev_zero propagation and compensation order.
  Regenerate WORKFLOW and REFERENCES for updated runtime/documentation traceability.
- add ev-zero centered bracketing [useReq] *(dng2hdr2jpg)*
  Update REQ-057/062/063/079/080/081/093 and add REQ-094..REQ-096 for ev-zero behavior.
  Implement --ev-zero parsing, runtime validation, centered multipliers, and luminance EV triplet export.
  Apply dynamic MAX_BRACKET formula with low-ceiling rejection and static EV guardrails.
  Extend TST-011 coverage for ev-zero parsing, range checks, and centered bracketing outputs.
  Update WORKFLOW.md and regenerate REFERENCES.md for runtime and symbol traceability.

### 🎯  Cover Requirements
- add TST-012 verification tests [useReq] *(video2h264)*
  add deterministic monkeypatched ffmpeg boundary tests\n- verify missing argument failure behavior for video2h264/video2h265\n- verify exact ffmpeg argv and <input>.mp4 output naming for REQ-095..REQ-098

### ◀️  Revert
- Roll back branch to 7d08dae6 (7d08dae63f0e5f2c62cf03d14f5a22938da1afbf).
- Roll back branch to deef714f (deef714fa59a6b7d733bc44b41ba1afce0d54336).

## [0.6.0](https://github.com/Ogekuri/shellScripts/compare/v0.5.0..v0.6.0) - 2026-03-27
### ⛰️  Features
- add DNG HDR JPG command [useReq] *(dng2jpg)*
  Append REQ-055..REQ-059 and TST-011 for dng2jpg.
  Register dng2jpg in command registry.
  Implement dng2jpg with --ev parsing, 3-bracket extraction, enfuse merge, JPG output, and temp cleanup.
  Add deterministic unit tests for parser, merge pipeline, failure handling, and dependency checks.
  Update WORKFLOW runtime model and regenerate REFERENCES symbol index.

### 🐛  Bug Fixes
- restore EXIF timestamp sync on real DNG [useReq] *(dng2hdr2jpg)*
  Fix EXIF payload/timestamp extraction to run while source image handle is open.\nHarden EXIF normalization for thumbnail refresh by handling nested integer sequences, range-invalid integer tags, and BYTE tuple conversion to bytes.\nAdd focused regression tests for closed-handle EXIF read and normalization edge cases.\nUpdate WORKFLOW and REFERENCES docs.
- isolate EXIF timestamp sync and handle sequence datetime [useReq] *(dng2hdr2jpg)*
  Add dedicated timestamp sync call in dng2hdr2jpg run pipeline.\nFix EXIF datetime parsing for one-item sequence payloads.\nAdd regression test covering sequence-based EXIF datetime timestamp sync.\nUpdate workflow and references documentation.
- suppress tag-33723 warning and normalize EXIF bytes [useReq] *(dng2hdr2jpg)*
  add failing repro tests for TIFF tag-33723 warning and EXIF byte SHORT crash\n- suppress known non-actionable Pillow metadata warning in EXIF read path\n- normalize null-terminated ASCII byte EXIF scalar/sequence values for piexif.dump\n- update WORKFLOW and regenerate REFERENCES
- parse null-terminated EXIF datetime for timestamp sync [useReq] *(dng2hdr2jpg)*
  add failing reproducer for null-terminated EXIF datetime parsing\n- normalize EXIF datetime token by trimming trailing null byte\n- preserve REQ-074 timestamp synchronization after JPG save\n- update WORKFLOW and regenerate REFERENCES
- disable raw auto-flip in bracket extraction [useReq] *(dng2hdr2jpg)*
  add failing reproducer for missing raw user_flip orientation guard\n- pass user_flip=0 in raw.postprocess during bracket extraction\n- keep JPG and EXIF thumbnail orientation consistent with source DNG\n- update WORKFLOW and regenerate REFERENCES
- normalize EXIF values before piexif dump [useReq] *(dng2hdr2jpg)*
  add failing reproducer for non-integer SHORT EXIF sequence crash\n- normalize integer-like EXIF IFD values before piexif.dump\n- preserve orientation/thumbnail refresh semantics\n- update WORKFLOW and regenerate REFERENCES
- normalize EXIF orientation in copied JPEG metadata [useReq] *(dng2hdr2jpg)*
  Fix orientation metadata mismatch by setting EXIF Orientation (274) to 1 before serializing DNG EXIF payload for JPG save.
  Add reproducer test for orientation normalization and keep EXIF datetime timestamp synchronization behavior unchanged.
  Update WORKFLOW and regenerate REFERENCES for the changed function contracts.
- accept uint8 OpenCV wow input [useReq] *(dng2hdr2jpg)*
  add reproducer test for uint8 OpenCV wow decode path; promote uint8 wow input to uint16 before float normalization; keep uint16 path unchanged and preserve wow pipeline semantics; update WORKFLOW runtime detail and regenerate REFERENCES
- normalize wow uint16 payload before PIL [useReq] *(dng2hdr2jpg)*
  Add failing reproducer for wow uint16 output raising Pillow TypeError.
  Normalize wow-decoded payload to uint8 before fromarray conversion.
  Preserve existing wow command resolution and postprocess semantics.
  Regenerate REFERENCES evidence after source and test updates.
  Re-verify with static check and targeted/full dng2hdr2jpg tests.
- support convert fallback for wow dependency [useReq] *(dng2hdr2jpg)*
  Add failing reproducer for wow path when magick is absent but convert exists.
  Resolve ImageMagick executable via compatibility fallback (magick, convert).
  Wire resolved executable into wow pipeline and keep strict error behavior when none exists.
  Update workflow model and regenerate references.
  Re-verify static checks and targeted unit suite.
- preserve luminance in magic-retouch LAB flow [useReq] *(dng2hdr2jpg)*
  Fix magic-retouch exposure collapse caused by incorrect LAB/HSV float range handling.
  Normalize LAB luminance processing to OpenCV float ranges and clamp correctly.
  Add targeted reproducer test for luminance collapse regression.
  Regenerate REFERENCES for updated symbol ranges.
- correct two-line operators table layout [useReq] *(dng2hdr2jpg)*
  Remove duplicated operators header rows from help table rendering.
  Drop phantom spacer column in bordered operators table output.
  Add focused regression assertions for border geometry and header count.
  Regenerate REFERENCES after symbol-surface updates.
- pass explicit EV list to luminance backend [useReq] *(dng2hdr2jpg)*
  Add -e <minus,zero,plus> to luminance-hdr-cli invocation for EXIF-less TIFF brackets.\nUpdate TST-011 luminance command assertions for default and alias operators.\nRefresh WORKFLOW and REFERENCES for updated runtime behavior.
- use MTB alignment with luminance tone mapper [useReq] *(dng2hdr2jpg)*
  Fix luminance-hdr-cli invocation by separating alignment engine from tone mapper.
  Use -a MTB and --tmo <operator> to satisfy runtime CLI contract.
  Update targeted tests and workflow/reference docs for corrected command shape.
- normalize RGBA merged payload before JPEG write [useReq] *(dng2hdr2jpg)*
  Handle merged HDR outputs that decode as RGBA to avoid JPEG encode failures.
  Convert Pillow-style RGBA images via convert('RGB') and keep ndarray alpha slicing fallback.
  Add targeted reproducer test for RGBA merged payload path and update runtime docs.
- declare runtime raw dependencies for uv install [useReq] *(dng2hdr2jpg)*
  Add rawpy and imageio as Linux runtime dependencies in pyproject metadata.
  Add a defect reproducer test asserting dependency declarations in pyproject.
  Regenerate uv.lock and references after metadata change.

### 🚜  Changes
- add video2h264/video2h265 ffmpeg commands [useReq] *(video)*
  Update PRJ-003 and add REQ-095..REQ-098 for video transcoding.
  Register video2h264 and video2h265 in command module map.
  Implement new command modules with help, argument validation, and exact ffmpeg options.
  Generate REFERENCES and update WORKFLOW call trace for new command paths.
  Run req --here --static-check and pytest tests/test_tst_001_002_core.py.
- use codex skills provider by default [useReq] *(req)*
  Update REQ-050 default-provider contract in docs/REQUIREMENTS.md.
  Switch runtime req default from codex:prompts to codex:skills.
  Adjust REQ-050 tests in tests/test_tst_006_dc_common.py.
  Align docs/WORKFLOW.md runtime-model wording to provider change.
- BREAKING CHANGE: auto-ev always uses max EV from DNG bit depth [useReq] *(dng2hdr2jpg)*
  REQ-080: adaptive pipeline simplified to DNG Metadata Detection -> Max EV Derivation; REQ-081: auto-ev sets EV to MAX=((bits_per_color-8)/2) without luminance analysis; REQ-094: center bracket extraction explicitly at 0 EV (multiplier 1.0); Removed luminance-based preview, percentile computation, and optimization; Removed AutoEvInputs class, AUTO_EV_* constants, SUPPORTED_EV_VALUES; Removed _clamp_ev_to_supported, _quantize_ev_to_supported, _coerce_positive_luminance; Removed _optimize_adaptive_ev_delta function; Breaking change: no backward compatibility maintained
- derive EV max from DNG bits and print metadata [useReq] *(dng2hdr2jpg)*
  Update REQ-057 and REQ-081 to use bit-derived EV MAX formula.
  Add REQ-092 and REQ-093 for bits-per-color and auto-EV MAX logging.
  Implement EV range derivation from RAW white_level metadata.
  Apply runtime validation for static EV against bit-derived supported values.
  Update help text to document MAX=(bits_per_color-8)/2.
  Adapt TST-011 tests for dynamic EV range and logging behavior.
  Regenerate WORKFLOW.md and REFERENCES.md for traceability.
- extend EV range to 0.25..3.0 [useReq] *(dng2hdr2jpg)*
  Update REQ-057 and REQ-081 for quarter-step EV granularity.\nExpand static --ev accepted values to 0.25..3.0 with 0.25 step.\nAlign adaptive --auto-ev quantization to same EV grid and bounds.\nUpdate help text, tests, workflow model, and references.
- set luminance default tmo to mantiuk08 [useReq] *(dng2hdr2jpg)*
  Update REQ-061 and REQ-071; add REQ-091 for mantiuk08 defaults.\nSwitch default --luminance-tmo to mantiuk08.\nApply tuned luminance default contrast=1.2 for mantiuk08.\nKeep reinhard02 tuned defaults unchanged and neutral defaults for others.\nAdjust tests/help/workflow/references to new defaults.
- add auto-brightness pre-stage and knobs [useReq] *(dng2hdr2jpg)*
  Update SRS REQ-063/065/066 and add REQ-088/089/090.
  Implement --auto-brightness and --ab-* parsing/validation/help.
  Apply OpenCV auto-brightness pipeline before static postprocess factors.
  Keep static postprocess behavior unchanged when auto-brightness disabled.
  Add/adjust tests for parsing, defaults, validation, help, and pipeline order.
  Regenerate REFERENCES and update WORKFLOW runtime model.
- share configurable auto-adjust knobs [useReq] *(dng2hdr2jpg)*
  Update REQ-063/065/073/075 and add REQ-082..REQ-087 for shared auto-adjust knobs.
  Introduce AutoAdjustOptions dataclass and embed it in PostprocessOptions.
  Parse --aa-* knobs in both --x=v and --x v forms with strict validation rules.
  Reject --aa-* knobs when --auto-adjust is omitted with explicit knob error.
  Map shared knobs into ImageMagick and OpenCV auto-adjust pipelines.
  Keep pipeline order, EXIF/orientation handling, thumbnail refresh, and timestamps unchanged.
  Extend help output with new knobs and documented defaults.
  Add focused tests for defaults, parsing/validation, IM argv mapping, OpenCV parameter forwarding, and synthetic numeric fixture behavior.
- rename --wow to --auto-adjust across spec, code, and tests [useReq] *(dng2hdr2jpg)*
- remove OpenCV-NP wow mode and sync requirements/help/tests [useReq] *(dng2hdr2jpg)*
- add mandatory --auto-ev adaptive pipeline and remove default EV fallback [useReq] *(dng2hdr2jpg)*
- switch opencode default to prompts [useReq] *(req)*
  Update REQ-050 to require OpenCode prompts default provider.
  Change default req provider from opencode:agents to opencode:prompts.
  Change req cleanup path from .opencode/agent to .opencode/prompt.
  Add regression tests for provider default and OpenCode prompt cleanup.
  Update WORKFLOW runtime notes for req provider and cleanup behavior.
- preserve DNG orientation and refresh EXIF thumbnail [useReq] *(dng2hdr2jpg)*
  update REQ-057 and REQ-066; add REQ-077 and REQ-078\n- preserve source EXIF Orientation in DNG metadata extraction\n- add piexif-based post-save EXIF thumbnail refresh from final JPG\n- keep wow and HDR stages orientation-consistent\n- add piexif dependency in pyproject and uv.lock\n- update TST-011 tests for orientation preservation and thumbnail refresh\n- update WORKFLOW.md and regenerate REFERENCES.md
- add OpenCV-NP wow backend [useReq] *(dng2hdr2jpg)*
  Update REQ-065 and REQ-073, and add REQ-076 for OpenCV-NP wow mode.
  Implement OpenCV-NP wow pipeline with 16-bit<->float conversion and modular dispatch.
  Extend TST-011 coverage for mode parsing, dependency validation, dispatch, and uint8 input handling.
  Refresh WORKFLOW runtime model and regenerate REFERENCES index.
- BREAKING CHANGE: modularize wow mode with OpenCV backend [useReq] *(dng2hdr2jpg)*
  update REQ-065/REQ-073 behavior for wow mode selection; add REQ-075 for OpenCV wow pipeline with uint16<->float flow; implement --wow <ImageMagick|OpenCV> parse/dispatch and dependency gates; port OpenCV wow stages and preserve ImageMagick path; extend TST-011 coverage and update runtime deps; refresh WORKFLOW.md and regenerate REFERENCES.md
- copy DNG EXIF and sync JPG timestamps [useReq] *(dng2hdr2jpg)*
  update REQUIREMENTS with EXIF/timestamp behavior (REQ-066, REQ-074); implement EXIF payload extraction/copy and EXIF datetime -> file atime/mtime sync; add TST-011 cases for EXIF propagation and missing-datetime fallback; update WORKFLOW runtime trace and regenerate REFERENCES
- add optional wow pre-jpeg 16-bit stage [useReq] *(dng2hdr2jpg)*
  Update requirements REQ-063/REQ-065/REQ-066 and add REQ-073 for --wow flow.
  Implement --wow parsing and gated dependency checks in dng2hdr2jpg.
  Add validated ImageMagick wow pipeline with temporary lossless 16-bit artifacts.
  Wire wow stage between shared postprocess and JPEG encoding.
  Extend/adjust unit tests for wow flag, help text, parser rejection, and wow pipeline.
  Update WORKFLOW call-trace and regenerate REFERENCES index.
- restore dng2hdr2tiff and shared help [useReq] *(dng2hdr2)*
  Update requirements to include dng2hdr2tiff command behavior and shared help.
  Register dng2hdr2tiff in command map and add wrapper command module.
  Refactor dng2hdr2jpg into shared pipeline with JPG/TIFF final encoders.
  Share help sections across JPG/TIFF and move JPG compression help to tail.
  Add tests for command registration, shared help, and TIFF output path.
  Refresh WORKFLOW and regenerate REFERENCES for updated runtime model.
- BREAKING CHANGE: reduce jpg conversion artifacts from 16-bit output [useReq] *(dng2hdr2jpg)*
  update REQ-066 to require deterministic ordered dither in uint16->uint8 conversion; add REQ-079 for JPEG artifact-reduction encode flags; implement Bayer-4x4 ordered dithering helper for final 16-bit to 8-bit conversion; keep jpg compression quality mapping and add progressive + 4:4:4 subsampling flags; extend TST-011 encode assertions and add ordered-dither contract test; update WORKFLOW and regenerate REFERENCES
- BREAKING CHANGE: switch magic denoise to deterministic strength [useReq] *(dng2hdr2jpg)*
  update REQ-073 and REQ-075 for --magic-denoise-strength semantics; replace threshold/noise-gate denoise with deterministic strength-driven denoise; rename CLI/parser/help/dataclass field from threshold to strength; update and extend TST-011 coverage for new option and deterministic denoise execution; refresh WORKFLOW and regenerate REFERENCES
- bypass zero-valued magic stages [useReq] *(dng2hdr2jpg)*
  refine REQ-075 with strict zero-control bypass semantics; skip denoise/gamma-bias/vibrance/sharpen stage computation when control is zero; add regression test proving zero-control paths do not call stage kernels; regenerate REFERENCES to keep symbol evidence aligned
- BREAKING CHANGE: refactor adaptive magic-retouch controls [useReq] *(dng2hdr2jpg)*
  update REQ-073/REQ-075/REQ-078 for adaptive retouch semantics; remove legacy filter-based CLI controls and parse new adaptive controls; implement ordered float-domain adaptive stages with noise-safe sharpening; refresh tests and regenerate WORKFLOW/REFERENCES docs
- BREAKING CHANGE: replace magic-retouch with OpenCV filter pipeline [useReq] *(dng2hdr2jpg)*
  update requirements, code, tests, workflow, references
- retune magic-retouch defaults for noise control [useReq] *(dng2hdr2jpg)*
  update REQ-075 to require anti-clumping default tuning\n- increase denoise defaults and slightly reduce enhancement defaults\n- align noise-conservative defaults unit test expectations\n- update WORKFLOW runtime note for magic_retouch default intent\n- regenerate REFERENCES index after implementation change
- tune magic-retouch defaults to reduce noise [useReq] *(dng2hdr2jpg)*
  Update REQ-075 to require noise-conservative default values.
  Adjust default denoise/detail parameters for lower noise amplification.
  Add targeted unit test validating tuned default constants.
  Regenerate REFERENCES for updated constants.
- add 16-bit magic-retouch processing pipeline [useReq] *(dng2hdr2jpg)*
  Update SRS REQ-063/066 and add REQ-073..REQ-077 for magic-retouch flow.
  Refactor dng2hdr2jpg to split 16-bit postprocess from JPG encoding.
  Add optional in-memory magic-retouch stage with configurable controls.
  Add opencv-python and numpy Linux runtime dependencies to package metadata.
  Extend TST-011 unit tests for parser/help/pipeline ordering and dependency coverage.
  Regenerate WORKFLOW and REFERENCES documentation.
- enforce exclusive backend selector and backend defaults [useReq] *(dng2hdr2jpg)*
  Update REQUIREMENTS for mandatory backend selector and backend-specific postprocess defaults.\nImplement --enable-enfuse support and mutual exclusion with --enable-luminance.\nApply luminance reinhard02 tuned defaults and neutral defaults otherwise.\nUpdate dng2hdr2jpg help and parser behavior accordingly.\nExtend tests for selector validation and default profiles.\nRefresh WORKFLOW and REFERENCES documentation.
- remove non-exposed control rows [useReq] *(dng2hdr2jpg)*
  update REQ-063 to constrain control-table rows to exposed CLI controls; remove ferwerda and mai from Luminance operator main CLI controls table; update WORKFLOW runtime note and regenerate REFERENCES
- update luminance operator table help [useReq] *(dng2hdr2jpg)*
  update REQ-070 for three-column two-line-header operator table\n- render operator rows as two physical lines with secondary header row\n- keep default --luminance-tmo as reinhard02 and aligned Unicode borders\n- update WORKFLOW runtime notes and regenerate REFERENCES index
- default luminance hdr weight to flat [useReq] *(dng2hdr2jpg)*
  Update REQ-061 default luminance-hdr-weight from triangular to flat.
  Adjust dng2hdr2jpg default constant and default-backend test assertions.
  Update WORKFLOW runtime wording and regenerate REFERENCES.
- render two-line luminance operator rows [useReq] *(dng2hdr2jpg)*
  Update REQ-070 to require two physical lines per operator row.
  Refactor help table generation with operator-row expansion helper.
  Adjust help-output tests for two-line bordered layout markers.
  Refresh WORKFLOW and REFERENCES documentation after implementation.
- set reinhard02 default and help tables [useReq] *(dng2hdr2jpg)*
  Update REQ-061 to default luminance TMO reinhard02.\nAdd REQ-070 for aligned Unicode box tables in help output.\nImplement luminance operator and controls box tables in print_help.\nKeep luminance backend command semantics and passthrough behavior.\nAdjust TST-011 assertions for default tmo and table rendering.\nRefresh WORKFLOW model and regenerate REFERENCES.
- simplify luminance argv passthrough [useReq] *(dng2hdr2jpg)*
  Update REQ-061/062/063/067/068 for minimal luminance defaults.\nForward explicit --tmo* arguments only when provided.\nEmit --ldrTiff 16b in luminance-hdr-cli command.\nAdapt TST-011 parser/help/argv assertions and reload guard.\nRefresh WORKFLOW and regenerate REFERENCES.
- simplify luminance backend controls [useReq] *(dng2hdr2jpg)*
  Revise REQ-058/061/062/063 and add REQ-067/068/069 for luminance base parameters
  Replace operator/map options with hdr model/weight/response/tmo + m08 controls
  Generate deterministic -e and enforce bracket order ev_minus,ev_zero,ev_plus
  Keep shared neutral postprocess defaults to avoid implicit double corrections
  Update TST-011 tests, WORKFLOW.md, and regenerate REFERENCES.md
- add shared TIFF postprocess JPEG stage [useReq] *(dng2hdr2jpg)*
  Update REQ-058/062/063 and add REQ-065/REQ-066 for shared postprocess
  Refactor dng2hdr2jpg to produce intermediate HDR TIFF for both backends
  Add configurable post-gamma, brightness, contrast, saturation, jpg compression
  Add Pillow runtime dependency and lock update
  Align TST-011 tests with new dependency tuple and postprocess behavior
  Regenerate WORKFLOW.md and REFERENCES.md
- add configurable RAW gamma extraction [useReq] *(dng2hdr2jpg)*
  Update REQ-057/REQ-063 and add REQ-064 for gamma option parsing.\nImplement --gamma parsing/default and pass gamma to raw.postprocess.\nSet no_auto_bright=True, keep output_bps=16, and preserve camera WB.\nExtend TST-011 tests and refresh WORKFLOW/REFERENCES docs.
- require camera WB in RAW postprocess [useReq] *(dng2hdr2jpg)*
  Update REQ-057 and TST-011 to require raw.postprocess flags use_camera_wb=True and no_auto_bright=False.\nImplement bracket extraction flag changes in dng2hdr2jpg.\nUpdate tests, WORKFLOW, and regenerate REFERENCES for traceability.
- add optional luminance-hdr backend and operators [useReq] *(dng2hdr2jpg)*
  Update REQ-056..REQ-059 and add REQ-060..REQ-063 for dual HDR backends and luminance options.
  Implement --enable-luminance with default enfuse behavior and luminance-hdr-cli execution path.
  Support --luminance-operator and --luminance-map-* option parsing and help documentation.
  Extend TST-011 coverage and refresh workflow/references docs.
- BREAKING CHANGE: rename command and enforce Linux-only [useReq] *(dng2hdr2jpg)*
  Update REQ-055..REQ-059 for dng2hdr2jpg rename and Linux-only runtime.
  Rename command module/test files and command registry mapping.
  Add runtime OS guard with explicit Windows and MacOS unavailability messages.
  Keep EV bracket/HDR merge behavior on Linux and regenerate workflow/references docs.

### ◀️  Revert
- Roll back branch to fdf33e12 (fdf33e12e4d40eb7ef5195778285558ea9e1a5f4).

## [0.5.0](https://github.com/Ogekuri/shellScripts/compare/v0.4.0..v0.5.0) - 2026-03-20
### 🐛  Bug Fixes
- propagate external req failure exit code [useReq] *(req_cmd)*
  handle subprocess.CalledProcessError in req command; return external exit code and emit deterministic error; add reproducer test for failure path; update WORKFLOW runtime note; regenerate REFERENCES index

## [0.4.0](https://github.com/Ogekuri/shellScripts/compare/v0.3.0..v0.4.0) - 2026-03-20
### 🐛  Bug Fixes
- use npm.cmd on Windows when resolving npm [useReq] *(ai-install)*
  Reproduce WinError 2 with a dedicated failing unit test for ai-install npm execution on Windows.
  Fix _install_npm_tool to resolve and use npm.cmd on Windows, preserving non-Windows sudo behavior.
  Keep behavior aligned with existing REQ-008/REQ-047 without SRS changes.
  Regenerate REFERENCES.md and verify with static-check plus targeted/full pytest suites.

## [0.3.0](https://github.com/Ogekuri/shellScripts/compare/v0.2.0..v0.3.0) - 2026-03-20
### 🚜  Changes
- make npm sudo usage OS-aware [useReq] *(ai-install)*
  Update SRS for startup OS detection and ai-install OS-aware sudo behavior.
  Implement cached runtime OS detection at CLI startup in utils/core.
  Change ai-install npm command assembly: no sudo on Windows, sudo otherwise.
  Extend TST-001 and TST-003 mapped tests for OS detection and sudo branching.
  Update WORKFLOW.md and regenerate REFERENCES.md for traceability.

## [0.2.0](https://github.com/Ogekuri/shellScripts/compare/v0.1.0..v0.2.0) - 2026-03-20
### ⛰️  Features
- Update github workflow.

### 🚜  Changes
- add centralized runtime config and --write-config [useReq] *(core)*
  Update SRS requirement IDs for runtime configuration behavior.
  Add config module loading ~/.config/shellScripts/config.json with default fallback merge.
  Implement --write-config management command writing default JSON payload.
  Refactor diff/edit/view wrappers and management commands to use runtime config.
  Extend tests for startup config load, write-config, and runtime dispatch profiles.
  Regenerate REFERENCES.md and update WORKFLOW.md runtime model.
- simplify GitHub automation requirement [useReq] *(requirements)*
  Update REQUIREMENTS to remove release.yml-specific requirements.
  Keep a single requirement for .github/workflows/release-uvx.yml presence.
  Align WORKFLOW and regenerate REFERENCES for traceability.
- rename wrappers to diff/edit/view [useReq] *(commands)*
  Update REQUIREMENTS for generic diff/edit/view command semantics.
  Replace command registry keys and module paths; remove legacy wrappers.
  Rename command modules and remove Double Commander naming from help.
  Extend TST-006 checks for generic help naming and missing-arg behavior.
  Update WORKFLOW call traces and regenerate REFERENCES index.
- ensure auth symlink before codex launch [useReq] *(cli-codex)*
  add REQ-043 and REQ-044 for cli-codex auth symlink guard; update TST-005 scope and evidence mapping in REQUIREMENTS; implement auth symlink verification/creation and info output in cli_codex; extend cli launcher tests for create and no-op symlink paths; update WORKFLOW and regenerate REFERENCES
- BREAKING CHANGE: remove bin-links CLI registration and SRS refs [useReq] *(commands)*
  update REQUIREMENTS: remove REQ-011 and REQ-012 and adjust PRJ-003; update TST-004 scope to REQ-013 only; remove bin-links from command registry dispatch map; refresh WORKFLOW call-trace and REFERENCES index
- replace release-uvx with release workflow path [useReq] *(release-workflow)*
  Update SRS to encode release workflow behavior and artifact publication requirements.
  Rename workflow file to .github/workflows/release.yml and remove legacy file path references.
  Refresh workflow runtime model pointers for release execution unit and communication edge.
  UID: useReq-shellScripts-work-20260319192252

### 📚  Documentation
- Update README.md document.

## [0.1.0](https://github.com/Ogekuri/shellScripts/releases/tag/v0.1.0) - 2026-03-19
### ⛰️  Features
- Initial Commit.
- Add uv.lock file.
- Initial commit.

### 🐛  Bug Fixes
- resolve static-check defects across CLI commands [useReq] *(core)*
  remove unused imports and invalid f-strings in command modules\n- harden pdf-crop typing flow for Pylance and Ruff compliance\n- refresh docs/REFERENCES.md to reflect updated symbol metadata

### 🎯  Cover Requirements
- add requirement coverage suites for TST-001..TST-008 [useReq] *(tests)*
  Add deterministic pytest suites mapped to uncovered TST requirements.\n- Verify CLI dispatch, installers, wrappers, PDF flows, and venv/tests behaviors.\n- Encode Doxygen-style metadata on test modules and helper stubs for traceability.

### 📚  Documentation
- align CLI usage documentation with current commands [useReq] *(readme)*
  UID: 20260319T190156Z\n- replace README TODO placeholders with actionable usage docs\n- document management flags and full command inventory\n- add install/run examples for uv tool, uvx, and local launcher\n- describe command-specific runtime dependencies and key workflows
- refresh repository reference index [useReq] *(core)*
  regenerate docs/REFERENCES.md from current source evidence\n- update module entrypoints and dependency anchors for agent navigation
- generate execution-unit runtime model [useReq] *(workflow)*
  add deterministic Execution Units Index with stable IDs\n- map internal call-trace trees for launcher, main CLI, and release workflow\n- capture explicit communication edges and external boundaries
- Add docs/REQUIREMENTS.md file.


# History

- \[0.1.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.1.0
- \[0.2.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.2.0
- \[0.3.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.3.0
- \[0.4.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.4.0
- \[0.5.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.5.0
- \[0.6.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.6.0
- \[0.7.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.7.0
- \[0.8.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.8.0
- \[0.9.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.9.0
- \[0.10.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.10.0
- \[0.11.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.11.0
- \[0.12.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.12.0
- \[0.13.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.13.0
- \[0.14.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.14.0
- \[0.15.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.15.0
- \[0.16.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.16.0
- \[0.17.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.17.0
- \[0.18.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.18.0
- \[0.19.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.19.0
- \[0.20.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.20.0
- \[0.21.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.21.0
- \[0.22.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.22.0
- \[0.23.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.23.0
- \[0.24.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.24.0
- \[0.25.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.25.0
- \[0.26.0\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.26.0
- \[0.26.2\]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.26.2

[0.1.0]: https://github.com/Ogekuri/shellScripts/releases/tag/v0.1.0
[0.2.0]: https://github.com/Ogekuri/shellScripts/compare/v0.1.0..v0.2.0
[0.3.0]: https://github.com/Ogekuri/shellScripts/compare/v0.2.0..v0.3.0
[0.4.0]: https://github.com/Ogekuri/shellScripts/compare/v0.3.0..v0.4.0
[0.5.0]: https://github.com/Ogekuri/shellScripts/compare/v0.4.0..v0.5.0
[0.6.0]: https://github.com/Ogekuri/shellScripts/compare/v0.5.0..v0.6.0
[0.7.0]: https://github.com/Ogekuri/shellScripts/compare/v0.6.0..v0.7.0
[0.8.0]: https://github.com/Ogekuri/shellScripts/compare/v0.7.0..v0.8.0
[0.9.0]: https://github.com/Ogekuri/shellScripts/compare/v0.8.0..v0.9.0
[0.10.0]: https://github.com/Ogekuri/shellScripts/compare/v0.9.0..v0.10.0
[0.11.0]: https://github.com/Ogekuri/shellScripts/compare/v0.10.0..v0.11.0
[0.12.0]: https://github.com/Ogekuri/shellScripts/compare/v0.11.0..v0.12.0
[0.13.0]: https://github.com/Ogekuri/shellScripts/compare/v0.12.0..v0.13.0
[0.14.0]: https://github.com/Ogekuri/shellScripts/compare/v0.13.0..v0.14.0
[0.15.0]: https://github.com/Ogekuri/shellScripts/compare/v0.14.0..v0.15.0
[0.16.0]: https://github.com/Ogekuri/shellScripts/compare/v0.15.0..v0.16.0
[0.17.0]: https://github.com/Ogekuri/shellScripts/compare/v0.16.0..v0.17.0
[0.18.0]: https://github.com/Ogekuri/shellScripts/compare/v0.17.0..v0.18.0
[0.19.0]: https://github.com/Ogekuri/shellScripts/compare/v0.18.0..v0.19.0
[0.20.0]: https://github.com/Ogekuri/shellScripts/compare/v0.19.0..v0.20.0
[0.21.0]: https://github.com/Ogekuri/shellScripts/compare/v0.20.0..v0.21.0
[0.22.0]: https://github.com/Ogekuri/shellScripts/compare/v0.21.0..v0.22.0
[0.23.0]: https://github.com/Ogekuri/shellScripts/compare/v0.22.0..v0.23.0
[0.24.0]: https://github.com/Ogekuri/shellScripts/compare/v0.23.0..v0.24.0
[0.25.0]: https://github.com/Ogekuri/shellScripts/compare/v0.24.0..v0.25.0
[0.26.0]: https://github.com/Ogekuri/shellScripts/compare/v0.25.0..v0.26.0
[0.26.2]: https://github.com/Ogekuri/shellScripts/compare/v0.26.0..v0.26.2
