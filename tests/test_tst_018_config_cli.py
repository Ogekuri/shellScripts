#!/usr/bin/env python3
"""HDT unit tests for the shell_scripts configuration CLI parity gate.

Static Analysis (HDT Generator mode):
- UUT list:
  - `config_cli.find_schema_mismatches` (Level 0; pure tree walk over
    `CONFIG_SCHEMA` and `DEFAULT_RUNTIME_CONFIG`).
  - `config_cli.do_print_raw` (Level 1; calls `_fail_on_schema_mismatch`
    and `get_config_path`).
  - `config_cli.do_print`, `config_cli.do_params`, `config_cli.do_get`,
    `config_cli.do_set`, `config_cli.do_unset` (Level 1; each calls
    `_fail_on_schema_mismatch` first).
- Call graph (approximate):
  `do_* -> _fail_on_schema_mismatch -> _SCHEMA_MISMATCHES (import-time
  snapshot produced by find_schema_mismatches)`;
  `do_print_raw -> get_config_path -> Path.home() (HOME environment)`.
- External dependencies to isolate:
  - Filesystem: HOME is redirected to `tmp_path` via monkeypatch so
    `get_config_path()` resolves inside the test-owned tree; no real user
    configuration file is read or written.
  - Schema state: divergence is injected by monkeypatching
    `config_cli._SCHEMA_MISMATCHES`; import-time snapshot is never mutated
    permanently.
  - Terminal: pytest stdout is not a TTY, so `color_enabled()` is `False`
    and emitted lines carry no ANSI escapes.

Test Matrix:
| UUT                    | Level | Scenario                 | Act                  | Assert (expected)                                    |
|------------------------|-------|--------------------------|----------------------|------------------------------------------------------|
| find_schema_mismatches | 0     | aligned repository state | call with no args    | returns `[]`                                          |
| do_print_raw           | 1     | happy: file present      | write file, invoke   | `0` and verbatim file bytes on stdout (REQ-094)       |
| do_print_raw           | 1     | error: schema divergence | inject, invoke       | `1` and explicit schema error line (DES-034)          |
| all six do_* commands  | 1     | error: schema divergence | inject, invoke each  | `1` and explicit schema error line for each (DES-034) |

@satisfies DES-032, DES-034, REQ-094
"""

from __future__ import annotations

import json

import pytest

from shell_scripts import config_cli

_DIVERGENCE = ["default 'demo:x' is not covered by CONFIG_SCHEMA"]
_DIVERGENCE_MARK = "non allineato"


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
        lambda: config_cli.do_params(),
        lambda: config_cli.do_get("management:upgrade"),
        lambda: config_cli.do_set("management:upgrade", "x"),
        lambda: config_cli.do_unset("management:upgrade"),
    ],
    ids=["--print-raw", "--print", "--params", "--get", "--set", "--unset"],
)
def test_all_configuration_commands_fail_on_schema_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys, invoke
) -> None:
    """@brief Verify every configuration CLI command enforces DES-034.

    @details Parametrizes the six configuration command entrypoints over the
    injected divergence state; each MUST return `1` and print the explicit
    schema-alignment error before any other output or filesystem mutation.
    expected_exception: none; expected_output is return code `1` plus the
    divergence error line for every parameterization.
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


def test_do_print_renders_object_leaves_as_chiave_valore_tables(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print` details object leaves as box tables.

    @details Invokes `do_print` on the unmodified repository defaults; every
    `oggetto` leaf MUST be detailed as a `Chiave`/`Valore` box table with one
    row per entry (sorted keys, JSON-encoded cell values) instead of a
    single-line JSON blob, while remaining embedded in the REQ-095 tree.
    expected_output: return code `0`; `Chiave`/`Valore` headers; per-entry
    rows; no `= {` scalar-leaf rendering for object leaves.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies DES-032, REQ-095, REQ-096
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "│ Chiave" in captured.out
    assert "│ code" in captured.out
    assert '["bcompare"]' in captured.out
    assert '= {"' not in captured.out
    assert any(
        line.startswith("│   │   │   ") and "┌" in line
        for line in captured.out.splitlines()
    )


def test_do_print_renders_list_leaves_as_indexed_tables(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `--print` details list leaves as indexed box tables.

    @details Invokes `do_print` on the unmodified repository defaults; every
    `elenco` leaf MUST be detailed as a `#`/`Valore` box table with one row
    per element (1-based position, JSON-encoded cell values) instead of a
    single-line JSON blob.
    expected_output: return code `0`; `#`/`Valore` headers; per-element rows;
    no `= [` scalar-leaf rendering for list leaves.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies DES-032, REQ-095, REQ-096
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "│ #" in captured.out
    assert "claude:prompts" in captured.out
    assert '= ["' not in captured.out
    assert any(
        line.startswith("    │   ") and "┌" in line
        for line in captured.out.splitlines()
    )


def test_do_print_keeps_scalar_leaf_json_encoding(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify scalar leaves keep the `= <JSON>` rendering contract.

    @details Guards REQ-096 against the table-rendering change: string
    scalar leaves (for example `management:upgrade`) MUST continue to render
    as `= <JSON-encoded value>` on the fixed-width name column.
    expected_output: `= "uv tool install shellscripts"` present in stdout.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-096
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_print()
    captured = capsys.readouterr()
    assert return_code == 0
    assert '= "uv tool install shellscripts"' in captured.out


def test_config_schema_declares_input_example_for_every_option() -> None:
    """@brief Verify DES-036 example coverage across the schema registry.

    @details Walks `CONFIG_SCHEMA` depth-first; every `OptionSpec` leaf MUST
    declare a non-empty `example` token consumed by `--params` example
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


def test_do_params_appends_input_examples_to_scalar_lines(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify scalar `--params` lines carry inline input examples.

    @details Invokes `do_params` on the unmodified repository; every scalar
    option line MUST append its schema-declared example as
    `(Esempio di input: <token>)` per REQ-110.
    expected_output: return code `0` and inline example suffixes on scalar
    option lines.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-110
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_params()
    captured = capsys.readouterr()
    assert return_code == 0
    assert '(Esempio di input: "uv tool install shellscripts")' in captured.out
    assert '(Esempio di input: "uv tool uninstall shellscripts")' in captured.out


def test_do_params_renders_object_shape_table_and_example(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `oggetto` options document format, shape, and example.

    @details Invokes `do_params` on the unmodified repository; `oggetto`
    options MUST print the JSON-object input note, the `Chiave`/`Formato`
    default-structure table resolved from `DEFAULT_RUNTIME_CONFIG`, and the
    schema-declared example continuation line per REQ-112.
    expected_output: return code `0`; input note; shape table rows; example
    continuation line.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-112
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_params()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "[Oggetto]" in captured.out
    assert "Formato di input: oggetto JSON" in captured.out
    assert "│ Chiave" in captured.out
    assert "│ code" in captured.out
    assert '(Esempio di input: {"code": ["bcompare"], "pdf": ["okular"]})' in captured.out


def test_do_params_renders_list_format_table_and_example(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify `elenco` options document format, elements, and example.

    @details Invokes `do_params` on the unmodified repository; `elenco`
    options MUST print the JSON-array input note, the `Campo`/`Formato`
    element-format table, and the schema-declared example continuation line
    per REQ-113.
    expected_output: return code `0`; input note; element-format row; example
    continuation line.
    @param monkeypatch {pytest.MonkeyPatch} Environment isolation fixture.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-113
    """

    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_params()
    captured = capsys.readouterr()
    assert return_code == 0
    assert "[Elenco]" in captured.out
    assert "Formato di input: elenco JSON" in captured.out
    assert "│ elementi" in captured.out
    assert '(Esempio di input: ["codex:skills", "pi:prompts"])' in captured.out


def test_do_params_prints_example_line_after_selection_table(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    """@brief Verify selection tables are followed by the example line.

    @details Injects a synthetic selection schema and invokes `do_params`;
    the `(Esempio di input: <token>)` continuation line MUST directly follow
    the allowed-value table bottom border per REQ-111, falling back to the
    first allowed choice quoted when no schema example is declared.
    expected_output: return code `0`; example line adjacent below the table
    bottom border.
    @param monkeypatch {pytest.MonkeyPatch} Schema and snapshot isolation.
    @param tmp_path {pathlib.Path} Test-owned temporary directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Asserts behavioral outcome only.
    @satisfies REQ-111
    """

    choice_spec = config_cli.OptionSpec(
        "selezione",
        "Scelta di test per la verifica dell'esempio.",
        choices=(
            config_cli.ChoiceSpec("A", "prima"),
            config_cli.ChoiceSpec("B", "seconda"),
        ),
    )
    schema = (
        (
            "grp",
            config_cli.GroupSpec(
                "Gruppo di test.",
                (("choice", choice_spec),),
            ),
        ),
    )
    monkeypatch.setattr(config_cli, "CONFIG_SCHEMA", schema)
    monkeypatch.setattr(config_cli, "_SCHEMA_MISMATCHES", [])
    _isolate_home(monkeypatch, tmp_path)
    return_code = config_cli.do_params()
    captured = capsys.readouterr()
    out_lines = captured.out.splitlines()
    matching = [
        index
        for index, line in enumerate(out_lines)
        if '(Esempio di input: "A")' in line
    ]
    assert return_code == 0
    assert matching
    assert "└" in out_lines[matching[0] - 1]
