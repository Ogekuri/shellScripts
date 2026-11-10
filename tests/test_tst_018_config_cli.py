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
