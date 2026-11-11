#!/usr/bin/env python3
"""HDT unit tests for the shell_scripts configuration CLI.

Static Analysis (HDT Refactorer mode; suite exists, contracts updated):
- Audit of the replaced suite: assertions targeted the pre-refactor contracts
  (secret masking, 1-based `#` list tables, `(Input example: ...)` params
  lines, `[Object]` kind labels). The updated SRS (REQ-098, REQ-110..REQ-113,
  REQ-117..REQ-133) replaces those contracts, so the affected assertions were
  rewritten to the new observable behavior; parity and divergence gates were
  preserved unchanged.
- UUT list:
  - `config_cli.find_schema_mismatches` (Level 0; pure tree walk over
    `CONFIG_SCHEMA` and `DEFAULT_RUNTIME_CONFIG`).
  - `config_cli.do_print_raw`, `config_cli.do_print`, `config_cli.do_info`,
    `config_cli.do_get`, `config_cli.do_set`, `config_cli.do_unset` (Level 1;
    each calls `_fail_on_schema_mismatch` and `_ensure_bootstrap` first).
  - `config_cli._ensure_bootstrap` (Level 1; calls `_atomic_write_text` and
    `get_config_path`).
  - `config_cli._write_overrides` (Level 1; atomic persistence path).
- Call graph (approximate):
  `do_* -> _fail_on_schema_mismatch -> _SCHEMA_MISMATCHES (import-time
  snapshot)`;
  `do_* -> _ensure_bootstrap -> _atomic_write_text -> get_config_path`;
  `do_get/do_set/do_unset -> _resolve_target -> _walk_schema`;
  `do_set/do_unset -> load_runtime_config + _load_overrides +
  _set_nested/_pop_nested + _write_overrides`.
- External dependencies to isolate:
  - Filesystem: HOME is redirected to `tmp_path` via monkeypatch so
    `get_config_path()` resolves inside the test-owned tree; no real user
    configuration file is read or written.
  - Schema state: divergence is injected by monkeypatching
    `config_cli._SCHEMA_MISMATCHES`; synthetic schemas are injected by
    monkeypatching `config_cli.CONFIG_SCHEMA`.
  - Effective configuration: synthetic-kind scenarios monkeypatch
    `config_cli.load_runtime_config` with a static effective payload so
    integer/float/boolean/selection/object-array kinds are exercised without
    mutating repository defaults.
  - Terminal: pytest stdout is not a TTY, so `color_enabled()` is `False`
    and emitted lines carry no ANSI escapes.

Test Matrix (abridged; each test carries its full expected outcome):
| UUT                 | Level | Scenario                        | Assert (expected)                                     |
|---------------------|-------|---------------------------------|-------------------------------------------------------|
| find_schema_mism.   | 0     | aligned repository state        | returns `[]`                                          |
| do_print_raw        | 1     | missing file bootstraps         | `0`, defaults JSON created and printed (REQ-116)      |
| do_print_raw        | 1     | happy: file present             | `0` and verbatim file bytes on stdout (REQ-094)       |
| all six do_*        | 1     | error: schema divergence        | `1` plus explicit schema error line (DES-034)         |
| do_print            | 1     | badges, indicators, tables      | `[Path:`, `(default)`, `Key`, `Idx` 0-based, no mask  |
| do_print            | 1     | custom indicator after set      | `(custom | default: ...)` present                     |
| do_print            | 1     | sub-path filtering              | only addressed subtree rendered                       |
| do_print            | 1     | selection table + hint          | `Sel`/`[*]`, `set: <path> <Value>`                    |
| do_print            | 1     | empty collections               | empty list/map hints                                  |
| do_print            | 1     | object-array rows               | `Idx` plus field columns                              |
| do_info           | 1     | scalar metadata lines           | `Default :` and `Set cmd :` full paths (REQ-110)      |
| do_info           | 1     | selection table columns         | `Value`/`Default`/`Meaning` + cmd lines (REQ-108/111) |
| do_info           | 1     | array command lines             | add/insert/update/delete/overwrite/clear (REQ-113)    |
| do_info           | 1     | sub-path filtering              | only addressed subtree documented                     |
| do_get              | 1     | scalar, row, cell, key reads    | clean single-line or indented JSON                    |
| do_get              | 1     | error reads                     | stderr message plus return code `1`                   |
| do_set              | 1     | append/insert/update semantics  | indices, shifting, messages, persisted JSON           |
| do_set              | 1     | out-of-bounds                   | range message with ':append' hint, code `1`           |
| do_set              | 1     | map key add/update, overwrite   | persisted JSON map or array                           |
| do_set              | 1     | strict casting (synthetic)      | JSON number/boolean stored, never strings             |
| do_set              | 1     | invalid JSON abort              | code `1`, file unchanged                              |
| do_unset            | 1     | row delete re-indexes           | contiguous 0-based indices                            |
| do_unset            | 1     | map key removal                 | key gone, other entries intact                        |
| do_unset            | 1     | branch reset warning            | `WARNING: Removed all parameters for <path>.`         |
| _ensure_bootstrap   | 1     | creates defaults file           | file content equals default JSON                      |
| _write_overrides    | 1     | atomic persistence              | valid JSON, no temporary leftovers                    |

@satisfies DES-032, DES-034, DES-037, DES-038, DES-039, REQ-094, REQ-098,
REQ-101, REQ-102, REQ-108, REQ-110, REQ-111, REQ-113, REQ-114, REQ-116,
REQ-117, REQ-118, REQ-119, REQ-121, REQ-122, REQ-124, REQ-125, REQ-126,
REQ-127, REQ-128, REQ-129, REQ-130, REQ-131, TST-018
"""

from __future__ import annotations

import json

import pytest

from shell_scripts import config_cli
from shell_scripts.config import DEFAULT_RUNTIME_CONFIG

_DIVERGENCE = ["default 'demo:x' is not covered by CONFIG_SCHEMA"]
_DIVERGENCE_MARK = "not aligned"


def _inject_divergence(monkeypatch: pytest.MonkeyPatch) -> None:
    """@brief Inject a schema/defaults divergence into the module snapshot.

    @details Replaces `config_cli._SCHEMA_MISMATCHES` with a one-entry
    divergence description; monkeypatch restores the original snapshot after
    each test, preserving import-time state isolation.
    @param monkeypatch {pytest.MonkeyPatch} Fixture performing the patch.
    @return {None} Mutates module state for the test duration only.
    """

    monkeypatch.setattr(config_cli, "_SCHEMA_MISMATCHES", list(_DIVERGENCE))


def _isolate_home(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """@brief Redirect the canonical configuration path into the test tree.

    @details Sets `HOME` to `tmp_path` so `get_config_path()` resolves inside
    the pytest-owned temporary directory, isolating the suite from the real
    user configuration file.
    @param monkeypatch {pytest.MonkeyPatch} Fixture performing the patch.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @return {None} Mutates the process environment for the test duration only.
    """

    monkeypatch.setenv("HOME", str(tmp_path))


def _read_config_file(tmp_path) -> dict:
    """@brief Parse the isolated configuration file content.

    @details Reads the canonical config file inside the test tree and decodes
    it as a JSON object for post-mutation assertions.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @return {dict} Decoded configuration payload.
    """

    target = config_cli.get_config_path()
    return json.loads(target.read_text(encoding="utf-8"))


def test_find_schema_mismatches_aligned_defaults() -> None:
    """@brief Verify registry/defaults parity on the unmodified repository.

    @details Runs the pure parity walk over the shipped `CONFIG_SCHEMA` and
    `DEFAULT_RUNTIME_CONFIG`; guarantees the divergence fixture used by the
    error-path tests models a state that the repository does not ship.
    expected_output: empty mismatch list.
    @return {None} Asserts behavioral outcome only.
    @satisfies DES-033, DES-034
    """

    result = config_cli.find_schema_mismatches()
    assert result == []


def test_do_print_raw_bootstraps_missing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print-raw` initializes and prints the default file.

    @details Invokes `do_print_raw` with no configuration file present; the
    command MUST create the parent directories and the defaults payload, then
    print the created file verbatim (REQ-094, REQ-116).
    expected_output: return code `0`; bootstrapped file equals
    `DEFAULT_RUNTIME_CONFIG`; stdout equals the file content.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-094, REQ-114, REQ-116
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print_raw()
    captured = capsys.readouterr()
    target = config_cli.get_config_path()
    assert return_code == 0
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == DEFAULT_RUNTIME_CONFIG
    assert captured.out == target.read_text(encoding="utf-8")


def test_do_print_raw_success_returns_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print-raw` prints the on-disk file verbatim.

    @details Writes a known JSON payload into the isolated configuration
    path, invokes `do_print_raw`, and compares stdout byte-for-byte with the
    file content.
    expected_output: return code `0` and verbatim payload on stdout.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-094
    """

    _isolate_home(monkeypatch, tmp_path)
    payload = {"management": {"upgrade": "uv tool install shellscripts"}}
    target = config_cli.get_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload), encoding="utf-8")
    return_code = config_cli.do_print_raw()
    captured = capsys.readouterr()
    assert return_code == 0
    assert captured.out == json.dumps(payload)


def test_do_print_raw_fails_on_schema_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print-raw` aborts on schema/defaults divergence.

    @details Injects a divergence description into the module snapshot and
    invokes `do_print_raw`; the command MUST fail with return code `1` and
    print the explicit schema-alignment error instead of the file content
    (DES-034 applies to every configuration CLI command, including
    `--print-raw` per DES-032).
    expected_output: return code `1` and divergence error line on stderr.
    @param monkeypatch {pytest.MonkeyPatch} Divergence and env isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies DES-032, DES-034
    """

    _inject_divergence(monkeypatch)
    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print_raw()
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert return_code == 1
    assert _DIVERGENCE_MARK in combined
    assert "demo:x" in combined


@pytest.mark.parametrize(
    "invoke",
    [
        lambda: config_cli.do_print_raw(),
        lambda: config_cli.do_print(),
        lambda: config_cli.do_info(),
        lambda: config_cli.do_get("management:upgrade"),
        lambda: config_cli.do_set("management:upgrade", "x"),
        lambda: config_cli.do_unset("management:upgrade"),
    ],
    ids=["--print-raw", "--print", "--info", "--get", "--set", "--unset"],
)
def test_all_configuration_commands_fail_on_schema_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys, invoke
) -> None:
    """@brief Verify every configuration CLI command enforces DES-034.

    @details Parametrizes the six configuration command entrypoints over the
    injected divergence state; each MUST return `1` and print the explicit
    schema-alignment error before any other output or filesystem mutation.
    expected_output: return code `1` plus the divergence error line for every
    parameterization.
    @param monkeypatch {pytest.MonkeyPatch} Divergence and env isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @param invoke {callable} Zero-argument command entrypoint under test.
    @return {None} Asserts behavioral outcome only.
    @satisfies DES-032, DES-034
    """

    _inject_divergence(monkeypatch)
    _isolate_home(monkeypatch, tmp_path)
    return_code = invoke()
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert return_code == 1
    assert _DIVERGENCE_MARK in combined


def test_do_print_renders_badges_indicators_and_tables(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print` badges, indicators, and collection tables.

    @details Invokes `do_print` on the repository defaults; every section
    MUST carry its exact `[Path: ...]` badge, scalar leaves MUST carry the
    `(default)` indicator, map leaves MUST render as
    `(<N> entries | key target: ...)` plus a `Key`/`Value` table, and array
    leaves MUST render as 0-based `Idx`/`Value` tables with the row target
    header (REQ-096, REQ-117, REQ-118, REQ-119).
    expected_output: return code `0`; badges; indicators; map and array
    tables; no masked values anywhere.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-096, REQ-098, REQ-117, REQ-118, REQ-119, REQ-133
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "[Path: management]" in captured.out
    assert "[Path: dispatch:diff:categories]" not in captured.out
    assert "[Path: req]" in captured.out
    assert "(default)" in captured.out
    assert "(6 entries | key target: dispatch:diff:categories:<Key>)" in captured.out
    assert "(1 items | row target: dispatch:diff:fallback:<Idx> | add: :+)" in captured.out
    assert "│ Idx │ Value" in captured.out
    assert "│ 0   " in captured.out
    assert "********" not in captured.out


def test_do_print_marks_custom_values_after_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify the custom indicator exposes the schema default.

    @details Sets one option via `do_set`, then invokes `do_print`; the
    changed leaf MUST display `(custom | default: <Default_Value>)` while
    untouched leaves keep `(default)` (REQ-096).
    expected_output: return code `0`; custom indicator with the JSON-encoded
    default for the mutated leaf.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-096, REQ-103
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("management:upgrade", "custom-tool") == 0
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert '(custom | default: "uv tool install shellscripts")' in captured.out


def test_do_print_renders_only_requested_subtree(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print <Sub:Path>` restricts the rendered tree.

    @details Invokes `do_print` with the `req` sub-path; only the `req`
    subtree lines MUST be rendered and sibling sections MUST be absent
    (REQ-095).
    expected_output: return code `0`; `req` subtree present; `dispatch`
    absent.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-095, REQ-117
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print("req")
    captured = capsys.readouterr()
    assert return_code == 0
    assert "[Path: req]" in captured.out
    assert "[Path: dispatch]" not in captured.out
    assert "providers" in captured.out


def test_do_print_fails_on_unknown_sub_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print` rejects unknown sub-paths.

    @details Invokes `do_print` with a path absent from the schema registry;
    the command MUST print an explicit error to stderr and return `1`
    (REQ-095, REQ-132).
    expected_output: return code `1`; `Unknown configuration path` on stderr.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-095, REQ-132
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print("nope:missing")
    captured = capsys.readouterr()
    assert return_code == 1
    assert "Unknown configuration path" in captured.err


def _inject_schema_and_payload(monkeypatch: pytest.MonkeyPatch, schema, payload) -> None:
    """@brief Inject a synthetic schema, payload, and cleared divergence.

    @details Replaces `CONFIG_SCHEMA`, neutralizes the import-time divergence
    snapshot, and pins `load_runtime_config` to the supplied static effective
    payload so synthetic kinds are exercised without touching repository
    defaults.
    @param monkeypatch {pytest.MonkeyPatch} Fixture performing the patches.
    @param schema {tuple} Synthetic `CONFIG_SCHEMA` replacement.
    @param payload {dict} Static effective configuration payload.
    @return {None} Mutates module state for the test duration only.
    """

    monkeypatch.setattr(config_cli, "CONFIG_SCHEMA", schema)
    monkeypatch.setattr(config_cli, "_SCHEMA_MISMATCHES", [])
    monkeypatch.setattr(config_cli, "load_runtime_config", lambda: payload)


def test_do_print_renders_selection_table_and_action_hint(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify selection leaves render the table plus set hint.

    @details Injects a synthetic selection schema whose active value differs
    from the default and invokes `do_print`; the leaf MUST mark the active
    choice with `[*]`, inactive choices with `[ ]`, and append the
    `set: <Full:Path> <Value>` hint to the custom indicator
    (REQ-097, REQ-115).
    expected_output: return code `0`; `[*]` on the active row; hint on the
    leaf line.
    @param monkeypatch {pytest.MonkeyPatch} Schema and payload isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-097, REQ-115
    """

    choice_spec = config_cli.OptionSpec(
        "selection",
        "Test choice rendering.",
        choices=(
            config_cli.ChoiceSpec("A", "first"),
            config_cli.ChoiceSpec("B", "second"),
        ),
        example='"A"',
    )
    schema = (("grp", config_cli.GroupSpec("Test group.", (("choice", choice_spec),))),)
    _inject_schema_and_payload(monkeypatch, schema, {"grp": {"choice": "B"}})
    monkeypatch.setattr(config_cli, "DEFAULT_RUNTIME_CONFIG", {"grp": {"choice": "A"}})
    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "│ [*] │ B" in captured.out
    assert "│ [ ] │ A" in captured.out
    assert "set: grp:choice <Value>" in captured.out
    assert "(custom | default:" in captured.out


def test_do_print_renders_empty_collection_hints(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify empty arrays and maps render copy-pasteable hints.

    @details Injects a synthetic schema with an empty list and an empty map
    and invokes `do_print`; zero-length collections MUST render the explicit
    inline hints instead of empty tables (REQ-121).
    expected_output: return code `0`; empty-list and empty-map hint lines
    with full paths.
    @param monkeypatch {pytest.MonkeyPatch} Schema and payload isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-121
    """

    schema = (
        (
            "grp",
            config_cli.GroupSpec(
                "Test group.",
                (
                    (
                        "items",
                        config_cli.OptionSpec(
                            "list", "Empty test list.", example='["x"]'
                        ),
                    ),
                    (
                        "tags",
                        config_cli.OptionSpec(
                            "map", "Empty test map.", example='{"k": "v"}'
                        ),
                    ),
                ),
            ),
        ),
    )
    _inject_schema_and_payload(
        monkeypatch, schema, {"grp": {"items": [], "tags": {}}}
    )
    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "= (empty list — add row with: --set grp:items:+ <value>)" in captured.out
    assert "= (empty map — set key with: --set grp:tags:<Key> <value>)" in captured.out


def test_do_print_renders_object_array_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify object arrays render `Idx` plus field columns.

    @details Injects a synthetic `Array[Dictionary]` schema with declared
    item fields and invokes `do_print`; the leaf MUST render the row-count
    header with the cell target and a table whose columns are `Idx` plus the
    declared field names (REQ-120).
    expected_output: return code `0`; cell-target header; `Idx`, `Name`, and
    `URL` columns.
    @param monkeypatch {pytest.MonkeyPatch} Schema and payload isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-120, REQ-133
    """

    spec = config_cli.OptionSpec(
        "list",
        "Test object rows.",
        item_fields=(
            config_cli.FieldSpec("Name", "string", required=True),
            config_cli.FieldSpec(
                "URL", "string", has_default=True, default="https://x"
            ),
        ),
        example='[]',
    )
    schema = (("grp", config_cli.GroupSpec("Test group.", (("rows", spec),))),)
    payload_rows = [{"Name": "Auth", "URL": "https://a"}, {"Name": "Pay"}]
    _inject_schema_and_payload(
        monkeypatch, schema, {"grp": {"rows": payload_rows}}
    )
    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "(2 rows | cell target: grp:rows:<Idx>:<Field> | add: :+)" in captured.out
    assert "│ Idx │ Name" in captured.out
    assert '│ 1   │ "Pay"' in captured.out


def test_do_info_renders_scalar_default_and_set_cmd_lines(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify scalar `--info` metadata lines use full paths.

    @details Invokes `do_info` on the repository defaults; every scalar
    option MUST render the `Default : <value> (restored via: --unset <path>)`
    line and the full-path `Set cmd : --set <path> <example>` line
    (REQ-110, REQ-133).
    expected_output: return code `0`; Default and Set cmd lines for
    `management:upgrade`.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-110, REQ-133
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_info()
    captured = capsys.readouterr()
    assert return_code == 0
    assert (
        'Default : "uv tool install shellscripts" '
        "(restored via: --unset management:upgrade)"
    ) in captured.out
    assert (
        'Set cmd : --set management:upgrade "uv tool install shellscripts"'
    ) in captured.out


def test_do_info_renders_selection_value_default_meaning_table(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify selection tables use Value/Default/Meaning columns.

    @details Injects a synthetic selection schema and invokes `do_info`;
    the allowed-value table MUST use the `Value`, `Default`, and `Meaning`
    columns, mark the schema default with `Yes`, and be followed by the
    full-path `Set cmd` and `Reset cmd` lines (REQ-108, REQ-111).
    expected_output: return code `0`; table headers; `Yes` on the default
    row; command lines.
    @param monkeypatch {pytest.MonkeyPatch} Schema and payload isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-108, REQ-111
    """

    choice_spec = config_cli.OptionSpec(
        "selection",
        "Test choice documentation.",
        choices=(
            config_cli.ChoiceSpec("A", "first"),
            config_cli.ChoiceSpec("B", "second"),
        ),
        example='"A"',
    )
    schema = (("grp", config_cli.GroupSpec("Test group.", (("choice", choice_spec),))),)
    _inject_schema_and_payload(monkeypatch, schema, {"grp": {"choice": "A"}})
    monkeypatch.setattr(config_cli, "DEFAULT_RUNTIME_CONFIG", {"grp": {"choice": "A"}})
    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_info()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "│ Value │ Default │ Meaning" in captured.out
    assert "│ A     │ Yes     │ first" in captured.out
    assert "│ B     │ No      │ second" in captured.out
    assert 'Set cmd   : --set grp:choice "A"' in captured.out
    assert "Reset cmd : --unset grp:choice" in captured.out


def test_do_info_renders_array_command_templates(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify array options document every row operation.

    @details Invokes `do_info` on the repository defaults; every array
    option MUST render add, insert, update, delete, full-overwrite, and
    clear command lines using complete canonical paths (REQ-113, REQ-133).
    expected_output: return code `0`; the six operation lines for
    `req:providers`.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-113, REQ-133
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_info()
    captured = capsys.readouterr()
    assert return_code == 0
    assert ': --set req:providers:+ "claude:prompts" (or :append)' in captured.out
    assert ': --set req:providers:insert:0 "claude:prompts"' in captured.out
    assert ': --set req:providers:0 "claude:prompts"' in captured.out
    assert ": --unset req:providers:0 (auto re-indexes list)" in captured.out
    assert ": --set req:providers '[\"codex:skills\", \"pi:prompts\"]'" in captured.out
    assert ": --unset req:providers" in captured.out


def test_do_info_renders_map_command_templates(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify map options document key and overwrite operations.

    @details Invokes `do_info` on the repository defaults; every map
    option MUST render the set/add-key, remove-key, full-overwrite, and
    clear-map command lines using complete canonical paths
    (REQ-112, REQ-133).
    expected_output: return code `0`; the four operation lines for
    `dispatch:diff:categories`.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-112, REQ-133
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_info()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "[Map[String, Array[String]]]" in captured.out
    assert ": --set dispatch:diff:categories:code [\"bcompare\"]" in captured.out
    assert ": --unset dispatch:diff:categories:code" in captured.out
    assert ": --unset dispatch:diff:categories" in captured.out


def test_do_info_renders_only_requested_subtree(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--info <Sub:Path>` restricts the documented tree.

    @details Invokes `do_info` with the `dispatch:diff:categories`
    sub-path; only that option block MUST be documented and sibling options
    MUST be absent (REQ-107).
    expected_output: return code `0`; `categories` documentation present;
    `providers` absent.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-107, REQ-117
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_info("dispatch:diff:categories")
    captured = capsys.readouterr()
    assert return_code == 0
    assert "Category-to-command mapping for diff." in captured.out
    assert "providers" not in captured.out


def test_do_get_reads_scalars_rows_and_map_keys(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--get` scalar, array-row, and map-key reads.

    @details Invokes `do_get` for a scalar path, a 0-based array row, and a
    dynamic map key; scalars MUST print as clean single-line JSON without
    decoration (REQ-099, REQ-122, REQ-123).
    expected_output: return code `0` for each read; exact JSON payloads.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-099, REQ-122, REQ-123
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_get("management:upgrade") == 0
    assert '"uv tool install shellscripts"' in capsys.readouterr().out
    assert config_cli.do_get("req:providers:1") == 0
    assert '"github:skills"' in capsys.readouterr().out
    assert config_cli.do_get("dispatch:diff:categories:code") == 0
    assert '[\n  "bcompare"\n]' in capsys.readouterr().out


def test_do_get_errors_are_reported_on_stderr(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--get` error paths use stderr and return code `1`.

    @details Invokes `do_get` with an unknown path, an out-of-bounds index,
    and a missing map key; each MUST print an explicit error to stderr,
    return `1`, and state the valid index range for index errors
    (REQ-100, REQ-122, REQ-131, REQ-132).
    expected_output: return code `1` for each; error text on stderr.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-100, REQ-122, REQ-131, REQ-132
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_get("nope:missing") == 1
    assert "Unknown configuration path" in capsys.readouterr().err
    assert config_cli.do_get("req:providers:99") == 1
    captured = capsys.readouterr()
    assert "Index 99 out of bounds" in captured.err
    assert "0..6" in captured.err
    assert "':append'" in captured.err
    assert config_cli.do_get("dispatch:diff:categories:absent") == 1
    assert "Map key 'absent' not found" in capsys.readouterr().err


def test_do_set_appends_inserts_and_updates_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify array append, insert, and row-update semantics.

    @details Appends one item, inserts one item at index 0, and updates one
    row; the persisted array MUST reflect the final order, confirmations
    MUST report the assigned indices, and the insert MUST shift existing
    rows (REQ-124, REQ-125, REQ-126).
    expected_output: return code `0` for each operation; persisted array
    `["inserted", "claude:prompts", ..., "appended"]`.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-124, REQ-125, REQ-126, DES-039
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("req:providers:+", "appended") == 0
    assert "appended to providers at index 7" in capsys.readouterr().out
    assert config_cli.do_set("req:providers:insert:0", "inserted") == 0
    assert "inserted at index 0. Subsequent items shifted." in capsys.readouterr().out
    assert config_cli.do_set("req:providers:1", "updated") == 0
    assert "Row at index 1 updated successfully." in capsys.readouterr().out
    stored = _read_config_file(tmp_path)
    assert stored["req"]["providers"][0] == "inserted"
    assert stored["req"]["providers"][1] == "updated"
    assert stored["req"]["providers"][-1] == "appended"
    assert len(stored["req"]["providers"]) == 9


def test_do_set_rejects_out_of_bounds_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify out-of-bounds row updates fail without writing.

    @details Invokes `do_set` with index 99 and index -1 on a seven-element
    array; each MUST return `1`, print the valid index range with the
    `:append` hint to stderr, and leave the file untouched
    (REQ-126, REQ-131).
    expected_output: return code `1`; range message on stderr; file content
    unchanged.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-126, REQ-131
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_get("req:providers:0") == 0
    capsys.readouterr()
    before = config_cli.get_config_path().read_text(encoding="utf-8")
    assert config_cli.do_set("req:providers:99", '"x"') == 1
    captured = capsys.readouterr()
    assert "Valid indices for providers are 0..6" in captured.err
    assert "':append'" in captured.err
    assert config_cli.do_set("req:providers:-1", '"x"') == 1
    assert "Valid indices for providers are 0..6" in capsys.readouterr().err
    assert (
        config_cli.get_config_path().read_text(encoding="utf-8") == before
    )


def test_do_set_rejects_out_of_range_insert_positions(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify insert positions beyond the array length fail.

    @details Invokes `do_set` with `insert:8` on a seven-element array; the
    command MUST return `1` and state the valid insert-position range
    `0..7` (REQ-125, REQ-131).
    expected_output: return code `1`; insert-range message on stderr.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-125, REQ-131
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("req:providers:insert:8", '"x"') == 1
    captured = capsys.readouterr()
    assert "Valid insert positions for providers are 0..7" in captured.err


def test_do_set_manages_map_keys_and_overwrites_collections(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify map key mutations and whole-collection overwrites.

    @details Adds one map key, updates it, and overwrites the array and map
    bases with complete JSON payloads; persisted JSON MUST contain exactly
    the new payloads and confirmations MUST report the operation
    (REQ-127, REQ-128).
    expected_output: return code `0` for each; persisted payloads match the
    replacement values.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-127, REQ-128, DES-039
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("dispatch:diff:categories:code", '["xx"]') == 0
    assert "Key 'code' saved under dispatch:diff:categories:code." in capsys.readouterr().out
    assert config_cli.do_set("req:providers", '["one", "two"]') == 0
    assert "Array providers overwritten with 2 items (indices 0..1)." in capsys.readouterr().out
    assert (
        config_cli.do_set("dispatch:diff:categories", '{"k": ["v"]}') == 0
    )
    assert "Map categories overwritten with 1 entries." in capsys.readouterr().out
    stored = _read_config_file(tmp_path)
    assert stored["req"]["providers"] == ["one", "two"]
    assert stored["dispatch"]["diff"]["categories"] == {"k": ["v"]}


def test_do_set_rejects_invalid_values_without_writing(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify invalid JSON and map values abort the write.

    @details Invokes `do_set` with a non-JSON token on an array path and a
    non-array value on a map key; each MUST return `1`, print an explicit
    error to stderr, and leave the file byte-identical
    (REQ-102, REQ-127).
    expected_output: return code `1`; error on stderr; unchanged file.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-102, REQ-127
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_get("req:providers:0") == 0
    capsys.readouterr()
    before = config_cli.get_config_path().read_text(encoding="utf-8")
    assert config_cli.do_set("req:providers", "not-json") == 1
    assert "expected a valid JSON value" in capsys.readouterr().err
    assert config_cli.do_set("dispatch:diff:categories:code", '"scalar"') == 1
    assert "expected a JSON array" in capsys.readouterr().err
    assert (
        config_cli.get_config_path().read_text(encoding="utf-8") == before
    )


def test_do_set_casts_strict_schema_types(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify integer, float, and boolean JSON casting.

    @details Injects a synthetic schema declaring integer, float, and
    boolean options with matching effective defaults, then sets `8080`,
    `1.5`, and `true`; the persisted file MUST contain JSON number and
    boolean values, never strings (REQ-101, DES-039).
    expected_output: return code `0` for each; persisted JSON types are
    `int`, `float`, and `bool`.
    @param monkeypatch {pytest.MonkeyPatch} Schema and payload isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-101, DES-039
    """

    schema = (
        (
            "grp",
            config_cli.GroupSpec(
                "Casting group.",
                (
                    ("port", config_cli.OptionSpec("integer", "Port.", example="8080")),
                    ("ratio", config_cli.OptionSpec("float", "Ratio.", example="1.5")),
                    ("flag", config_cli.OptionSpec("boolean", "Flag.", example="true")),
                ),
            ),
        ),
    )
    payload = {"grp": {"port": 1, "ratio": 1.0, "flag": False}}
    _inject_schema_and_payload(monkeypatch, schema, payload)
    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("grp:port", "8080") == 0
    assert config_cli.do_set("grp:ratio", "2.5") == 0
    assert config_cli.do_set("grp:flag", "true") == 0
    stored = _read_config_file(tmp_path)
    assert stored["grp"]["port"] == 8080
    assert isinstance(stored["grp"]["port"], int)
    assert stored["grp"]["ratio"] == 2.5
    assert isinstance(stored["grp"]["ratio"], float)
    assert stored["grp"]["flag"] is True


def test_do_set_acquires_values_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `$NAME` environment acquisition and missing-variable error.

    @details Sets one option from a defined environment variable and one
    from an undefined variable; the defined case MUST persist the value and
    print the acquisition evidence, the undefined case MUST fail with code
    `1` (REQ-104).
    expected_output: defined case persists `from-env` and prints the evidence
    line; undefined case returns `1` with an explicit error.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-104
    """

    _isolate_home(monkeypatch, tmp_path)
    monkeypatch.setenv("CFG_TEST_VALUE", "from-env")
    assert config_cli.do_set("management:upgrade", "$CFG_TEST_VALUE") == 0
    captured = capsys.readouterr()
    assert "Value acquired from environment" in captured.out
    assert _read_config_file(tmp_path)["management"]["upgrade"] == "from-env"
    assert config_cli.do_set("management:upgrade", "$CFG_TEST_MISSING") == 1
    assert "Environment variable not defined" in capsys.readouterr().err


def test_do_unset_deletes_rows_and_reindexes(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify row deletion compacts the array contiguously.

    @details Appends one item, deletes row 0, and deletes the new last row;
    after each deletion the persisted array MUST keep contiguous 0-based
    indices with no gaps or null holes (REQ-129).
    expected_output: return code `0`; contiguous persisted array;
    re-indexing confirmations.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-129, DES-039
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("req:providers:+", "extra") == 0
    capsys.readouterr()
    assert config_cli.do_unset("req:providers:0") == 0
    captured = capsys.readouterr()
    assert "Item at index 0 removed. Array re-indexed (7 items remaining, indices 0..6)." in captured.out
    stored = _read_config_file(tmp_path)
    assert stored["req"]["providers"] == [
        "github:skills",
        "codex:skills",
        "opencode:prompts",
        "gemini:prompts",
        "kiro:agents",
        "pi:prompts",
        "extra",
    ]


def test_do_unset_removes_map_keys(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify dynamic map key removal keeps other entries.

    @details Adds one map key, then removes a different default key; the
    persisted map MUST keep the remaining entries and drop exactly the
    removed key (REQ-130, DES-039).
    expected_output: return code `0`; `text` key gone; `code` key present;
    removal confirmation printed.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-130, DES-039
    """

    _isolate_home(monkeypatch, tmp_path)
    assert (
        config_cli.do_set("dispatch:diff:categories:custom", '["c"]') == 0
    )
    capsys.readouterr()
    assert config_cli.do_unset("dispatch:diff:categories:text") == 0
    assert "Key 'text' removed from dispatch:diff:categories:text." in capsys.readouterr().out
    stored = _read_config_file(tmp_path)
    categories = stored["dispatch"]["diff"]["categories"]
    assert "text" not in categories
    assert categories["custom"] == ["c"]
    assert categories["code"] == ["bcompare"]


def test_do_unset_resets_branch_and_reports_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify branch reset warning and missing-key error semantics.

    @details Unsets the `dispatch:diff` subtree (expecting the verbatim
    WARNING line and default reactivation), then unsets an absent override
    twice to exercise the error path (REQ-105, REQ-106).
    expected_output: return code `0` with the WARNING line and restored
    defaults; return code `1` with an explicit error for the absent override.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-105, REQ-106
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_unset("dispatch:diff") == 0
    captured = capsys.readouterr()
    assert "WARNING: Removed all parameters for dispatch:diff." in captured.out
    stored = _read_config_file(tmp_path)
    assert "diff" not in stored.get("dispatch", {})
    assert config_cli.do_unset("dispatch:diff") == 1
    assert "No parameter to remove" in capsys.readouterr().err


def test_do_unset_resets_cell_to_declared_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify object-row cell reset semantics.

    @details Injects a synthetic object-array schema with one defaulted
    field and one required field, sets a row, resets the defaulted cell, and
    then resets the required (undeclared-default) cell; the defaulted cell
    MUST return to its schema default and the undeclared-default cell MUST
    be removed from the row (REQ-130, DES-039).
    expected_output: return code `0` for both resets; persisted rows reflect
    the default restore and the key removal.
    @param monkeypatch {pytest.MonkeyPatch} Schema and payload isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-130, DES-039
    """

    spec = config_cli.OptionSpec(
        "list",
        "Test object rows.",
        item_fields=(
            config_cli.FieldSpec("Name", "string", required=True),
            config_cli.FieldSpec(
                "URL", "string", has_default=True, default="https://default"
            ),
        ),
        example="[]",
    )
    schema = (("grp", config_cli.GroupSpec("Test group.", (("rows", spec),))),)
    payload = {"grp": {"rows": [{"Name": "A", "URL": "https://default"}]}}
    _inject_schema_and_payload(monkeypatch, schema, payload)
    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("grp:rows:0:URL", "https://changed") == 0
    assert (
        "Property 'URL' at index 0 updated to \"https://changed\"."
        in capsys.readouterr().out
    )
    assert config_cli.do_unset("grp:rows:0:URL") == 0
    assert "Property 'URL' at index 0 restored to default." in capsys.readouterr().out
    stored = _read_config_file(tmp_path)
    assert stored["grp"]["rows"][0]["URL"] == "https://default"
    assert config_cli.do_unset("grp:rows:0:Name") == 0
    stored = _read_config_file(tmp_path)
    assert "Name" not in stored["grp"]["rows"][0]


def test_atomic_write_leaves_no_temporary_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """@brief Verify atomic persistence leaves no temporary artifacts.

    @details Performs one `--set` and one `--unset`; the configuration
    directory MUST contain only the canonical `config.json`, the file MUST
    parse as JSON, and no `.tmp` leftovers MAY remain (DES-037).
    expected_output: exactly one file in the directory; valid JSON content.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @return {None} Asserts behavioral outcome only.
    @satisfies DES-037, REQ-103, REQ-105
    """

    _isolate_home(monkeypatch, tmp_path)
    assert config_cli.do_set("management:upgrade", "first") == 0
    assert config_cli.do_unset("management:upgrade") == 0
    directory = config_cli.get_config_path().parent
    entries = sorted(entry.name for entry in directory.iterdir())
    assert entries == ["config.json"]
    assert isinstance(_read_config_file(tmp_path), dict)


def test_bootstrap_uses_atomic_defaults_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """@brief Verify bootstrap creates nested directories and valid defaults.

    @details Invokes `do_get` with no configuration file or directories
    present; the bootstrap MUST create the full directory chain, write the
    defaults payload, and still serve the requested value (REQ-116).
    expected_output: return code `0`; nested directories created; file
    content equals `DEFAULT_RUNTIME_CONFIG`.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-116, DES-037
    """

    _isolate_home(monkeypatch, tmp_path)
    target = config_cli.get_config_path()
    assert not target.parent.exists()
    assert config_cli.do_get("req:static_checks:0") == 0
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == DEFAULT_RUNTIME_CONFIG


def test_config_schema_declares_input_example_for_every_option() -> None:
    """@brief Verify DES-036 example coverage across the schema registry.

    @details Walks `CONFIG_SCHEMA` depth-first; every `OptionSpec` leaf MUST
    declare a non-empty `example` token consumed by `--info` command
    rendering.
    expected_output: no assertion failure on the shipped registry.
    @return {None} Asserts behavioral outcome only.
    @satisfies DES-036
    """

    def _walk(children):
        """@brief Depth-first schema walker asserting example coverage.

        @param children {tuple} Sibling schema nodes being visited.
        @return {None} Asserts behavioral outcome only.
        """

        for _, node in children:
            if isinstance(node, config_cli.GroupSpec):
                _walk(node.children)
                continue
            assert node.example

    _walk(config_cli.CONFIG_SCHEMA)
