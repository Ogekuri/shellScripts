"""
@brief Validate the cargo-bootstrap-trust crates.io token-source resolution.
@details HDT Generator-mode suite.
  Static analysis artifact:
  UUTs: `shell_scripts.commands.cargo_bootstrap_trust._lookup_toml_token_path`
  (Level 0: pure TOML path walker), `..._read_toml_credentials_token`
  (Level 1: TOML parse plus path priority), `..._read_legacy_json_token`
  (Level 1: legacy JSON parse), `..._resolve_registry_token` (Level 2:
  environment plus file-source priority), `..._verify_crates_io_auth`
  (Level 1: `/me` response classification), `...run` (Level N: five-phase
  pipeline consuming the resolver during phase [1/5]).
  External dependencies isolated: environment variables (`CARGO_HOME`,
  `CARGO_REGISTRIES_CRATES_IO_TOKEN`) via monkeypatch, filesystem via
  `tmp_path` fixture cargo-home directories, crates.io HTTP and toolchain
  boundaries via module-level monkeypatched functions.
  Test matrix: env-var priority, TOML `[registry] token` happy path, TOML
  `[registries.crates-io] token` fallback, TOML precedence over legacy JSON,
  empty TOML token fallback, legacy JSON happy path, malformed or missing
  files, the all-sources-missing error case, and the phase-[1/5]
  integration flow halting before any mutating step, the `/me` response
  classification (403 website-only detail authenticates, 401 and generic
  HTTP failures abort), the missing-token abort hint, and the placeholder
  `Cargo.toml` manifest contract declaring the non-empty SPDX license
  metadata required by the crates.io publish gate.
@satisfies TST-023, TST-024, REQ-186, REQ-187, REQ-189, REQ-190, REQ-193
@return {None} Pytest module scope.
"""

import email.message
import io
import json
import types
import urllib.error

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
# Level 1: _verify_crates_io_auth /me response classification (TST-024)
# ---------------------------------------------------------------------------

def _http_error(code, body):
    """
    @brief Build one `HTTPError` carrying a JSON body for classification tests.
    @details Simulates the crates.io `/me` error boundary consumed by
      `_is_website_only_auth_probe` without any network access.
    @param code {int} HTTP status code of the simulated response.
    @param body {bytes} Raw response body returned by `HTTPError.read`.
    @return {urllib.error.HTTPError} Simulated error response.
    """
    return urllib.error.HTTPError(
        cargo_trust.CRATES_API + "/me", code, "Error", email.message.Message(), io.BytesIO(body)
    )


def _website_only_body():
    """
    @brief Build the upstream website-only 403 JSON error body.
    @details Encodes the exact upstream detail token carried by
      `WEBSITE_ONLY_DETAIL`.
    @return {bytes} JSON body carrying the website-only detail.
    """
    payload = {"errors": [{"detail": cargo_trust.WEBSITE_ONLY_DETAIL}]}
    return json.dumps(payload).encode("utf-8")


def test_verify_auth_accepts_website_only_403(monkeypatch, capsys):
    """
    @brief Validate that the upstream website-only 403 detail authenticates.
    @details REQ-187/REQ-193: crates.io emits the website-only detail only
      after resolving the presented API token, so `_verify_crates_io_auth`
      treats HTTP 403 carrying `WEBSITE_ONLY_DETAIL` as a successful
      verification and prints the English evidence line.
    @param monkeypatch {pytest.MonkeyPatch} HTTP boundary patch fixture.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Assertions only.
    @expected_output The `WEBSITE_ONLY_AUTH_EVIDENCE` line without SystemExit.
    @satisfies TST-024, REQ-187, REQ-193
    """
    def _fake_request(url, token=None, payload=None):
        raise _http_error(403, _website_only_body())

    monkeypatch.setattr(cargo_trust, "_http_request", _fake_request)
    expected_output = cargo_trust.WEBSITE_ONLY_AUTH_EVIDENCE
    cargo_trust._verify_crates_io_auth("valid-token")
    assert expected_output in capsys.readouterr().out


def test_verify_auth_prints_account_on_http_200(monkeypatch, capsys):
    """
    @brief Validate that an HTTP 200 `/me` payload still prints the login.
    @details Happy path guarding the authenticated 200 branch while the 403
      classification is added.
    @param monkeypatch {pytest.MonkeyPatch} HTTP boundary patch fixture.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Assertions only.
    @expected_output The `crates.io account: <login>` evidence line.
    @satisfies TST-024, REQ-187
    """
    def _fake_request(url, token=None, payload=None):
        return {"user": {"login": "octocat"}}

    monkeypatch.setattr(cargo_trust, "_http_request", _fake_request)
    expected_output = "crates.io account: octocat"
    cargo_trust._verify_crates_io_auth("valid-token")
    assert expected_output in capsys.readouterr().out


def test_verify_auth_aborts_on_401_invalid_token(monkeypatch, capsys):
    """
    @brief Validate the invalid-token 401 abort with the login hint.
    @details REQ-193: HTTP 401 on `/me` proves the token is invalid and must
      abort with the `cargo login` hint on stderr and exit code `1`.
    @param monkeypatch {pytest.MonkeyPatch} HTTP boundary patch fixture.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1` from `_die`.
    @expected_output `crates.io authentication unavailable (HTTP 401). Run: cargo login` on stderr.
    @satisfies TST-024, REQ-193
    """
    def _fake_request(url, token=None, payload=None):
        payload = {"errors": [{"detail": "invalid token"}]}
        raise _http_error(401, json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(cargo_trust, "_http_request", _fake_request)
    expected_output = "crates.io authentication unavailable (HTTP 401). Run: cargo login"
    with pytest.raises(SystemExit):
        cargo_trust._verify_crates_io_auth("invalid-token")
    assert expected_output in capsys.readouterr().err


def test_verify_auth_aborts_on_403_without_website_detail(monkeypatch, capsys):
    """
    @brief Validate that a 403 lacking the website-only detail aborts.
    @details REQ-193 boundary: classification is detail-based, so a 403
      carrying the `this action requires authentication` detail must abort
      instead of authenticating.
    @param monkeypatch {pytest.MonkeyPatch} HTTP boundary patch fixture.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1` from `_die`.
    @expected_output `crates.io authentication unavailable (HTTP 403). Run: cargo login` on stderr.
    @satisfies TST-024, REQ-193
    """
    def _fake_request(url, token=None, payload=None):
        payload = {"errors": [{"detail": "this action requires authentication"}]}
        raise _http_error(403, json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(cargo_trust, "_http_request", _fake_request)
    expected_output = "crates.io authentication unavailable (HTTP 403). Run: cargo login"
    with pytest.raises(SystemExit):
        cargo_trust._verify_crates_io_auth("valid-token")
    assert expected_output in capsys.readouterr().err


def test_verify_auth_aborts_on_malformed_403_body(monkeypatch, capsys):
    """
    @brief Validate that a 403 with an unparseable body aborts.
    @details Error case: `_is_website_only_auth_probe` returns `False` for a
      malformed body and the caller aborts with the login hint.
    @param monkeypatch {pytest.MonkeyPatch} HTTP boundary patch fixture.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1` from `_die`.
    @expected_output `crates.io authentication unavailable (HTTP 403). Run: cargo login` on stderr.
    @satisfies TST-024, REQ-193
    """
    def _fake_request(url, token=None, payload=None):
        raise _http_error(403, b"not-json")

    monkeypatch.setattr(cargo_trust, "_http_request", _fake_request)
    expected_output = "crates.io authentication unavailable (HTTP 403). Run: cargo login"
    with pytest.raises(SystemExit):
        cargo_trust._verify_crates_io_auth("valid-token")
    assert expected_output in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Level 1: _write_placeholder_crate manifest contract
# ---------------------------------------------------------------------------

def test_write_placeholder_crate_declares_license_metadata(monkeypatch, tmp_path):
    """
    @brief Validate that the placeholder Cargo.toml declares license metadata.
    @details Reproducer for the crates.io publish rejection `400 Bad Request:
      missing or empty metadata fields: license`: `_write_placeholder_crate`
      MUST emit a non-empty SPDX `license` field in the generated `[package]`
      manifest so the REQ-190 `cargo publish` succeeds. The `cargo init`
      subprocess boundary is isolated with a zero-status stub, keeping the
      test deterministic and network-free; the REQ-189 tokens (version,
      placeholder description, repository URL) stay asserted as regression
      guards.
    @param monkeypatch {pytest.MonkeyPatch} Subprocess boundary patch fixture.
    @param tmp_path {Path} Fixture placeholder crate directory.
    @return {None} Assertions only.
    @expected_output Manifest line `license = "<PLACEHOLDER_LICENSE>"` with a
      non-empty SPDX token plus the REQ-189 manifest tokens.
    @satisfies REQ-189, REQ-190
    """
    def _fake_run(command, **kwargs):
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cargo_trust.subprocess, "run", _fake_run)
    cargo_trust._write_placeholder_crate(
        tmp_path, "githubtemplaterust", "Ogekuri/GitHub-Template-Rust"
    )
    manifest = (tmp_path / "Cargo.toml").read_text(encoding="utf-8")
    assert cargo_trust.PLACEHOLDER_LICENSE
    expected_output = f'license = "{cargo_trust.PLACEHOLDER_LICENSE}"\n'
    assert expected_output in manifest
    assert 'version = "0.0.0"\n' in manifest
    assert (
        'description = "Initial placeholder to enable crates.io Trusted Publishing"\n'
        in manifest
    )
    assert 'repository = "https://github.com/Ogekuri/GitHub-Template-Rust"\n' in manifest


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


def test_run_aborts_without_token_with_login_hint(monkeypatch, tmp_path, capsys):
    """
    @brief Validate the missing-token abort literal of phase [1/5].
    @details REQ-193/REQ-186: an isolated empty `CARGO_HOME` without the
      environment variable must abort before the availability phase with
      the exact `crates.io authentication unavailable. Run: cargo login`
      hint on stderr and exit code `1`.
    @param monkeypatch {pytest.MonkeyPatch} Environment and module patch
      fixture.
    @param tmp_path {Path} Empty fixture cargo home directory.
    @param capsys {pytest.CaptureFixture} Output capture fixture.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1` from `_die`.
    @expected_output `crates.io authentication unavailable. Run: cargo login` on stderr.
    @satisfies TST-024, REQ-193, REQ-186
    """
    _isolate_cargo_home(monkeypatch, tmp_path)
    monkeypatch.setattr(cargo_trust, "_require_toolchain", lambda: None)
    expected_output = "crates.io authentication unavailable. Run: cargo login"
    with pytest.raises(SystemExit):
        cargo_trust.run(
            [
                "-p", "githubtemplaterust",
                "-r", "Ogekuri/GitHub-Template-Rust",
                "-f", "release-cargo.yml",
            ]
        )
    assert expected_output in capsys.readouterr().err
