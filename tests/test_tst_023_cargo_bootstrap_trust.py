"""
@brief Validate the cargo-bootstrap-trust crates.io token-source resolution.
@details HDT Generator-mode suite.
  Static analysis artifact:
  UUTs: `shell_scripts.commands.cargo_bootstrap_trust._lookup_toml_token_path`
  (Level 0: pure TOML path walker), `..._read_toml_credentials_token`
  (Level 1: TOML parse plus path priority), `..._read_legacy_json_token`
  (Level 1: legacy JSON parse), `..._resolve_registry_token` (Level 2:
  environment plus file-source priority), `...run` (Level N: five-phase
  pipeline consuming the resolver during phase [1/5]).
  External dependencies isolated: environment variables (`CARGO_HOME`,
  `CARGO_REGISTRIES_CRATES_IO_TOKEN`) via monkeypatch, filesystem via
  `tmp_path` fixture cargo-home directories, crates.io HTTP and toolchain
  boundaries via module-level monkeypatched functions.
  Test matrix: env-var priority, TOML `[registry] token` happy path, TOML
  `[registries.crates-io] token` fallback, TOML precedence over legacy JSON,
  empty TOML token fallback, legacy JSON happy path, malformed or missing
  files, the all-sources-missing error case, and the phase-[1/5]
  integration flow halting before any mutating step.
@satisfies TST-023, REQ-186
@return {None} Pytest module scope.
"""

import pytest

import shell_scripts.commands.cargo_bootstrap_trust as cargo_trust


def _write_toml_credentials(directory, token_lines):
    """
    @brief Write a `credentials.toml` fixture into a cargo home directory.
    @details Creates only the fixture file; the caller directory stays
      otherwise untouched so resolution falls through declared sources.
    @param directory {Path} Fixture cargo home directory.
    @param token_lines {str} TOML text declaring the token entries.
    @return {None} Creates the file only.
    """
    (directory / "credentials.toml").write_text(token_lines, encoding="utf-8")


def _write_legacy_credentials(directory, payload):
    """
    @brief Write a legacy JSON `credentials` fixture into a cargo home.
    @details Creates only the fixture file with the supplied JSON document.
    @param directory {Path} Fixture cargo home directory.
    @param payload {str} Raw JSON document text.
    @return {None} Creates the file only.
    """
    (directory / "credentials").write_text(payload, encoding="utf-8")


def _isolate_cargo_home(monkeypatch, directory):
    """
    @brief Redirect every token source to an isolated fixture directory.
    @details Unsets the token environment variable and points `CARGO_HOME`
      at `directory` so the real `~/.cargo` state is never read.
    @param monkeypatch {pytest.MonkeyPatch} Environment patch fixture.
    @param directory {Path} Fixture cargo home directory.
    @return {None} Mutates the process environment for one test only.
    """
    monkeypatch.delenv("CARGO_REGISTRIES_CRATES_IO_TOKEN", raising=False)
    monkeypatch.setenv("CARGO_HOME", str(directory))


# ---------------------------------------------------------------------------
# Level 0: _lookup_toml_token_path
# ---------------------------------------------------------------------------

def test_lookup_toml_token_path_returns_nonempty_string_leaf():
    """
    @brief Validate the pure TOML path walker on a present leaf.
    @details Happy path: nested tables resolve to the declared token value.
    @return {None} Assertions only.
    @expected_output The leaf string value.
    @satisfies TST-023, REQ-186
    """
    payload = {"registry": {"token": "toml-token"}}
    expected_output = "toml-token"
    result = cargo_trust._lookup_toml_token_path(
        payload, cargo_trust.TOML_REGISTRY_TOKEN_PATH
    )
    assert result == expected_output


@pytest.mark.parametrize(
    "payload,path",
    [
        ("not-a-table", cargo_trust.TOML_REGISTRY_TOKEN_PATH),
        ({}, cargo_trust.TOML_REGISTRY_TOKEN_PATH),
        ({"registry": "not-a-table"}, cargo_trust.TOML_REGISTRY_TOKEN_PATH),
        ({"registry": {"token": ""}}, cargo_trust.TOML_REGISTRY_TOKEN_PATH),
        ({"registry": {"token": 7}}, cargo_trust.TOML_REGISTRY_TOKEN_PATH),
        (
            {"registries": {"other": {"token": "x"}}},
            cargo_trust.TOML_REGISTRIES_TOKEN_PATH,
        ),
    ],
)
def test_lookup_toml_token_path_returns_none_for_invalid_structures(payload, path):
    """
    @brief Validate the TOML path walker on missing and invalid structures.
    @details Boundary and error cases: non-mapping root, absent segment,
      non-mapping intermediate, empty string leaf, non-string leaf, and
      mismatched registries path all resolve to `None`.
    @param payload {object} Parsed TOML document fixture.
    @param path {tuple[str, ...]} Dotted path segments under test.
    @return {None} Assertions only.
    @expected_output `None` for every invalid structure.
    @satisfies TST-023, REQ-186
    """
    expected_output = None
    assert cargo_trust._lookup_toml_token_path(payload, path) == expected_output


# ---------------------------------------------------------------------------
# Level 1: credential-file readers
# ---------------------------------------------------------------------------

def test_read_toml_credentials_returns_registry_token(tmp_path):
    """
    @brief Validate the TOML credentials reader on `[registry] token`.
    @details Happy path mirroring the `cargo login` output of cargo >= 1.66,
      including the cargo >= 1.89 versions enforced by the toolchain gate.
    @param tmp_path {Path} Pytest temporary fixture directory.
    @return {None} Assertions only.
    @expected_output The `[registry] token` value.
    @satisfies TST-023, REQ-186
    """
    _write_toml_credentials(tmp_path, '[registry]\ntoken = "toml-token"\n')
    expected_output = "toml-token"
    result = cargo_trust._read_toml_credentials_token(tmp_path)
    assert result == expected_output


def test_read_toml_credentials_falls_back_to_registries_section(tmp_path):
    """
    @brief Validate the `[registries.crates-io] token` TOML fallback.
    @details Boundary case: the default `[registry]` section is absent and
      the named-registry section supplies the token.
    @param tmp_path {Path} Pytest temporary fixture directory.
    @return {None} Assertions only.
    @expected_output The `[registries.crates-io] token` value.
    @satisfies TST-023, REQ-186
    """
    _write_toml_credentials(
        tmp_path, '[registries.crates-io]\ntoken = "toml-alt"\n'
    )
    expected_output = "toml-alt"
    result = cargo_trust._read_toml_credentials_token(tmp_path)
    assert result == expected_output


def test_read_toml_credentials_prefers_registry_over_registries(tmp_path):
    """
    @brief Validate `registry.token` precedence inside the TOML file.
    @details Boundary case: both TOML sections declare a token and the
      default-registry path wins.
    @param tmp_path {Path} Pytest temporary fixture directory.
    @return {None} Assertions only.
    @expected_output The `[registry] token` value.
    @satisfies TST-023, REQ-186
    """
    _write_toml_credentials(
        tmp_path,
        '[registry]\ntoken = "primary"\n[registries.crates-io]\ntoken = "fallback"\n',
    )
    expected_output = "primary"
    result = cargo_trust._read_toml_credentials_token(tmp_path)
    assert result == expected_output


@pytest.mark.parametrize(
    "content",
    [
        "registry = [unterminated\n",
        "",
        "[registry]\nother = 1\n",
    ],
)
def test_read_toml_credentials_returns_none_for_unusable_files(tmp_path, content):
    """
    @brief Validate the TOML reader on malformed, empty, and tokenless files.
    @details Error cases: a malformed TOML document raises `TOMLDecodeError`,
      an empty file parses without token paths, and a file lacking both
      token paths yields no value; every case returns `None`.
    @param tmp_path {Path} Pytest temporary fixture directory.
    @param content {str} Fixture file content.
    @return {None} Assertions only.
    @expected_output `None` for every unusable file.
    @satisfies TST-023, REQ-186
    """
    _write_toml_credentials(tmp_path, content)
    expected_output = None
    assert cargo_trust._read_toml_credentials_token(tmp_path) == expected_output


def test_read_legacy_json_token_returns_credentials_key(tmp_path):
    """
    @brief Validate the legacy JSON reader on `registry.crates.io-token`.
    @details Happy path for the pre-1.66 JSON credentials file.
    @param tmp_path {Path} Pytest temporary fixture directory.
    @return {None} Assertions only.
    @expected_output The legacy JSON token value.
    @satisfies TST-023, REQ-186
    """
    _write_legacy_credentials(
        tmp_path, '{"registry.crates.io-token": "json-token"}'
    )
    expected_output = "json-token"
    result = cargo_trust._read_legacy_json_token(tmp_path)
    assert result == expected_output


@pytest.mark.parametrize(
    "content",
    [
        "{invalid json",
        '{"other-key": 1}',
        "",
    ],
)
def test_read_legacy_json_token_returns_none_for_unusable_files(tmp_path, content):
    """
    @brief Validate the legacy JSON reader on malformed and tokenless files.
    @details Error cases: malformed JSON, JSON without the token key, and an
      empty file all return `None`.
    @param tmp_path {Path} Pytest temporary fixture directory.
    @param content {str} Fixture file content.
    @return {None} Assertions only.
    @expected_output `None` for every unusable file.
    @satisfies TST-023, REQ-186
    """
    _write_legacy_credentials(tmp_path, content)
    expected_output = None
    assert cargo_trust._read_legacy_json_token(tmp_path) == expected_output


# ---------------------------------------------------------------------------
# Level 2: _resolve_registry_token source priority
# ---------------------------------------------------------------------------

def test_resolve_registry_token_prefers_environment_variable(monkeypatch, tmp_path):
    """
    @brief Validate that the environment variable wins over both files.
    @details Arrange declares all three sources with distinct tokens; the
      environment value must be returned unchanged.
    @param monkeypatch {pytest.MonkeyPatch} Environment patch fixture.
    @param tmp_path {Path} Fixture cargo home directory holding both files.
    @return {None} Assertions only.
    @expected_output The environment-variable token.
    @satisfies TST-023, REQ-186
    """
    _write_toml_credentials(tmp_path, '[registry]\ntoken = "toml-token"\n')
    _write_legacy_credentials(
        tmp_path, '{"registry.crates.io-token": "json-token"}'
    )
    monkeypatch.setenv("CARGO_REGISTRIES_CRATES_IO_TOKEN", "env-token")
    monkeypatch.setenv("CARGO_HOME", str(tmp_path))
    expected_output = "env-token"
    assert cargo_trust._resolve_registry_token() == expected_output


def test_resolve_registry_token_prefers_toml_over_legacy_json(monkeypatch, tmp_path):
    """
    @brief Validate TOML precedence over the legacy JSON credentials file.
    @details Arrange declares both files; the modern TOML token must win,
      mirroring cargo's own credentials migration precedence.
    @param monkeypatch {pytest.MonkeyPatch} Environment patch fixture.
    @param tmp_path {Path} Fixture cargo home directory holding both files.
    @return {None} Assertions only.
    @expected_output The TOML token.
    @satisfies TST-023, REQ-186
    """
    _write_toml_credentials(tmp_path, '[registry]\ntoken = "toml-token"\n')
    _write_legacy_credentials(
        tmp_path, '{"registry.crates.io-token": "json-token"}'
    )
    _isolate_cargo_home(monkeypatch, tmp_path)
    expected_output = "toml-token"
    assert cargo_trust._resolve_registry_token() == expected_output


def test_resolve_registry_token_falls_back_to_legacy_json(monkeypatch, tmp_path):
    """
    @brief Validate the legacy JSON fallback when only that file exists.
    @details Boundary case honoring pre-1.66 cargo installations.
    @param monkeypatch {pytest.MonkeyPatch} Environment patch fixture.
    @param tmp_path {Path} Fixture cargo home directory holding only JSON.
    @return {None} Assertions only.
    @expected_output The legacy JSON token.
    @satisfies TST-023, REQ-186
    """
    _write_legacy_credentials(
        tmp_path, '{"registry.crates.io-token": "json-token"}'
    )
    _isolate_cargo_home(monkeypatch, tmp_path)
    expected_output = "json-token"
    assert cargo_trust._resolve_registry_token() == expected_output


def test_resolve_registry_token_skips_empty_toml_token(monkeypatch, tmp_path):
    """
    @brief Validate that an empty TOML token falls through to the next path.
    @details Boundary case: `[registry] token` set to the empty string must
      not short-circuit the `[registries.crates-io] token` fallback.
    @param monkeypatch {pytest.MonkeyPatch} Environment patch fixture.
    @param tmp_path {Path} Fixture cargo home directory.
    @return {None} Assertions only.
    @expected_output The `[registries.crates-io] token` value.
    @satisfies TST-023, REQ-186
    """
    _write_toml_credentials(
        tmp_path, '[registry]\ntoken = ""\n[registries.crates-io]\ntoken = "toml-alt"\n'
    )
    _isolate_cargo_home(monkeypatch, tmp_path)
    expected_output = "toml-alt"
    assert cargo_trust._resolve_registry_token() == expected_output


def test_resolve_registry_token_returns_none_without_sources(monkeypatch, tmp_path):
    """
    @brief Validate the all-sources-missing error case.
    @details Empty fixture cargo home with no environment variable must
      resolve to `None` so `run` aborts with the `cargo login` hint.
    @param monkeypatch {pytest.MonkeyPatch} Environment patch fixture.
    @param tmp_path {Path} Empty fixture cargo home directory.
    @return {None} Assertions only.
    @expected_output `None`.
    @satisfies TST-023, REQ-186
    """
    _isolate_cargo_home(monkeypatch, tmp_path)
    expected_output = None
    assert cargo_trust._resolve_registry_token() == expected_output


# ---------------------------------------------------------------------------
# Level N: run() phase [1/5] integration
# ---------------------------------------------------------------------------

def test_run_verifies_authentication_with_toml_token(monkeypatch, tmp_path):
    """
    @brief Validate that phase [1/5] passes the TOML token to the auth check.
    @details Runs the `cargo-bootstrap-trust` pipeline with an isolated
      `CARGO_HOME` containing only `credentials.toml`, stubs the toolchain
      gate and HTTP boundaries, and halts the pipeline at phase [2/5] with
      `SystemExit` before any mutating step. Asserts the recorder observed
      the TOML token, proving the acceptance flow `cargo login` ->
      `credentials.toml` -> successful authentication handshake.
    @param monkeypatch {pytest.MonkeyPatch} Environment and module patch
      fixture.
    @param tmp_path {Path} Fixture cargo home directory.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Raised by the stubbed availability gate.
    @expected_output The recorded TOML token observed by the auth stub.
    @satisfies TST-023, REQ-186, REQ-187
    """
    _write_toml_credentials(tmp_path, '[registry]\ntoken = "toml-run-token"\n')
    _isolate_cargo_home(monkeypatch, tmp_path)
    observed = {}

    def _fake_verify(token):
        observed["token"] = token

    def _stop_before_mutation(package_name):
        raise SystemExit(1)

    monkeypatch.setattr(cargo_trust, "_require_toolchain", lambda: None)
    monkeypatch.setattr(cargo_trust, "_verify_crates_io_auth", _fake_verify)
    monkeypatch.setattr(cargo_trust, "_check_crate_availability", _stop_before_mutation)
    expected_output = "toml-run-token"
    with pytest.raises(SystemExit):
        cargo_trust.run(
            [
                "-p", "githubtemplaterust",
                "-r", "Ogekuri/GitHub-Template-Rust",
                "-f", "release-cargo.yml",
            ]
        )
    assert observed["token"] == expected_output
