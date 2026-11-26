#!/usr/bin/env python3
"""@brief Cargo (crates.io) bootstrap and Trusted Publishing registration command.

@details Executes the five-phase pipeline mirroring the `npm-bootstrap-trust`
philosophy: crates.io authentication check through the registry API, crate
name availability check, temporary placeholder crate creation via
`cargo init`, `cargo publish` of version `0.0.0`, and GitHub
trusted-publisher registration through the crates.io trusted-publishing API
followed by trust-configuration verification. Every mutating step fails fast
and the temporary directory is removed on every exit path.
@note cargo provides no CLI for registry identity or trusted-publishing
configuration, so registry operations use the crates.io HTTP API while
project creation and publication use the cargo CLI.
@satisfies PRJ-009, DES-070, REQ-182, REQ-183, REQ-184, REQ-185, REQ-186,
REQ-187, REQ-188, REQ-189, REQ-190, REQ-191, REQ-192
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from typing import NoReturn

from shell_scripts.utils import print_error, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Bootstrap a new crates.io crate and register its GitHub trusted publisher."

## @var CRATES_API
#  @brief Canonical crates.io API base URL used by every registry request.
#  @details Authentication, availability, and trusted-publishing calls all
#  target this base so operations never depend on ambient registry mirrors.
#  @satisfies REQ-187, REQ-188, REQ-191
CRATES_API = "https://crates.io/api/v1"

## @var USER_AGENT
#  @brief HTTP User-Agent header value sent with every crates.io request.
#  @details crates.io rejects requests that omit a descriptive User-Agent.
USER_AGENT = f"{PROGRAM} cargo-bootstrap-trust"

## @var HTTP_TIMEOUT
#  @brief Timeout in seconds applied to every crates.io HTTP request.
HTTP_TIMEOUT = 10

## @var TOKEN_ENV_VARIABLE
#  @brief Environment variable holding the crates.io token override.
#  @details First token-resolution source; wins over the credentials file.
#  @satisfies REQ-186
TOKEN_ENV_VARIABLE = "CARGO_REGISTRIES_CRATES_IO_TOKEN"

## @var TOKEN_CREDENTIALS_KEY
#  @brief JSON key of the crates.io token inside the cargo credentials file.
#  @details Second token-resolution source, read from
#  `$CARGO_HOME/credentials` with `CARGO_HOME` defaulting to `~/.cargo`.
#  @satisfies REQ-186
TOKEN_CREDENTIALS_KEY = "registry.crates.io-token"

## @var MIN_RUSTC_VERSION
#  @brief Minimum supported rustc version tuple `(1, 89, 0)`.
#  @details Versions comparing lower abort the command.
#  @satisfies REQ-185
MIN_RUSTC_VERSION = (1, 89, 0)

## @var MIN_CARGO_VERSION
#  @brief Minimum supported cargo version tuple `(1, 89, 0)`.
#  @details cargo 1.89 ships the crates.io Trusted Publishing support required
#  by the OIDC publish executed from the configured GitHub workflow.
#  @satisfies REQ-185
MIN_CARGO_VERSION = (1, 89, 0)

## @var CRATE_NAME_PATTERN
#  @brief Anchored conservative crate-name regex `^[a-z0-9][a-z0-9_-]*$`.
#  @details Accepts only lowercase ASCII letters, digits, `-`, and `_` with a
#  non-leading separator; uppercase letters and dots are rejected.
#  @satisfies REQ-183
CRATE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

## @var MAX_CRATE_NAME_LENGTH
#  @brief Maximum accepted crate-name length matching the crates.io limit.
#  @satisfies REQ-183
MAX_CRATE_NAME_LENGTH = 64

## @var GITHUB_REPO_PATTERN
#  @brief Anchored `owner/repo` validation regex
#  `^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$`.
#  @details Repository tokens MUST NOT be URLs or carry extra slashes.
#  @satisfies REQ-184
GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$")

## @var WORKFLOW_FILE_PATTERN
#  @brief Anchored bare workflow-filename regex
#  `^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$`.
#  @details Rejects paths, directory components, and unsupported extensions.
#  @satisfies REQ-184
WORKFLOW_FILE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$")

## @var VERSION_PATTERN
#  @brief Anchored strict `X.Y.Z` semantic-version regex.
#  @details Used to locate the version token inside `rustc --version` and
#  `cargo --version` output; malformed values abort the version gate.
#  @satisfies REQ-185
VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class _UsageParser(argparse.ArgumentParser):
    """@brief `argparse` parser variant preserving the legacy exit code.

    @details Overrides `error` so usage errors print the message plus usage
    text to stderr and terminate with exit code `1`, matching the
    `npm-bootstrap-trust` `usage(1)`/`die` semantics instead of the argparse
    default `2`.
    @satisfies REQ-182
    """

    def error(self, message):
        """@brief Terminate argument parsing with the legacy failure contract.

        @details Prints the bare message to stderr, then the usage text, then
        raises `SystemExit(1)`.
        @param message {str} Parsing error description.
        @return {None} Never returns; raises `SystemExit`.
        @throws {SystemExit} Always exit code `1`.
        @satisfies REQ-182
        """
        self.print_usage(sys.stderr)
        print_error(message)
        self.exit(1)


def _build_parser():
    """@brief Build the `cargo-bootstrap-trust` argument parser.

    @details Registers required `-p/--package`, `-r/--repo`, and
    `-f/--workflow` options plus the default `-h/--help` action on the
    `_UsageParser` variant.
    @return {_UsageParser} Configured parser instance.
    @satisfies REQ-182
    """
    parser = _UsageParser(
        description=(
            "Bootstrap a new crates.io crate with a placeholder publish and"
            " register its GitHub Trusted Publisher configuration."
        ),
    )
    parser.add_argument(
        "-p", "--package", required=True, help="New crates.io crate name.",
    )
    parser.add_argument(
        "-r", "--repo", required=True,
        help="GitHub repository in owner/repo format.",
    )
    parser.add_argument(
        "-f", "--workflow", required=True,
        help="Workflow file name inside .github/workflows/ (with .yml or .yaml).",
    )
    return parser


def _die(message) -> NoReturn:
    """@brief Print an error line and terminate with exit code `1`.

    @details Mirrors the `npm-bootstrap-trust` `die` helper using the shared
    `[ERROR]` stderr renderer.
    @param message {str} Failure description rendered after the `[ERROR]`
      prefix.
    @return {None} Never returns; raises `SystemExit`.
    @throws {SystemExit} Always exit code `1`.
    @satisfies REQ-182, REQ-183, REQ-184, REQ-185, REQ-187, REQ-188, REQ-190,
    REQ-191
    """
    print_error(message)
    sys.exit(1)


def _validate_inputs(package_name, github_repo, workflow_file):
    """@brief Validate the conservative crate, repository, and workflow tokens.

    @details Applies `CRATE_NAME_PATTERN` plus `MAX_CRATE_NAME_LENGTH`, the
    `GITHUB_REPO_PATTERN` plus owner length at most 39 and owner not ending
    with `-`, and `WORKFLOW_FILE_PATTERN`, aborting with the shared English
    diagnostics on the first failure.
    @param package_name {str} crates.io crate name token.
    @param github_repo {str} GitHub `owner/repo` token.
    @param workflow_file {str} Bare workflow filename token.
    @return {None} Returns on full validation.
    @throws {SystemExit} Exit code `1` via `_die` on the first invalid token.
    @satisfies REQ-183, REQ-184
    """
    if not CRATE_NAME_PATTERN.fullmatch(package_name):
        _die("Invalid crate name (use lowercase letters, digits, _ and -).")
    if len(package_name) > MAX_CRATE_NAME_LENGTH:
        _die(f"Crate name too long (maximum {MAX_CRATE_NAME_LENGTH} characters).")

    if not GITHUB_REPO_PATTERN.fullmatch(github_repo):
        _die("Invalid GitHub repository: use owner/repo, without URLs or extra slashes.")
    gh_owner = github_repo.split("/", 1)[0]
    if len(gh_owner) > 39 or gh_owner.endswith("-"):
        _die("Invalid GitHub owner.")

    if not WORKFLOW_FILE_PATTERN.fullmatch(workflow_file):
        _die("Invalid workflow: pass only the file name, e.g. publish.yml.")


def _parse_version(text):
    """@brief Extract one strict `X.Y.Z` version tuple from tool output.

    @details Scans whitespace-separated tokens of `rustc --version` or
    `cargo --version` output and returns the first token matching
    `VERSION_PATTERN`; tool banners prefix the version with the binary name,
    so no positional assumption is made.
    @param text {str} Raw version output token.
    @return {tuple[int, int, int]|None} Numeric version tuple, or `None` when
      no token matches the strict format.
    @satisfies REQ-185
    """
    for token in text.split():
        match = VERSION_PATTERN.fullmatch(token)
        if match:
            return tuple(int(part) for part in match.groups())
    return None


def _require_toolchain():
    """@brief Validate rustc and cargo presence plus minimum versions.

    @details Checks `rustc` and `cargo` executables via `require_commands`,
    captures `rustc --version` and `cargo --version`, parses both with
    `_parse_version`, and aborts when either executable reports a version
    lower than `MIN_RUSTC_VERSION` or `MIN_CARGO_VERSION` respectively or an
    unparseable value.
    @return {None} Returns when the toolchain satisfies the version gate.
    @throws {SystemExit} Exit code `1` via `require_commands` on missing
      executables or via `_die` on incompatible versions.
    @satisfies REQ-185, CTN-003, REQ-056
    """
    require_commands("rustc", "cargo")

    rustc_result = subprocess.run(
        ["rustc", "--version"], capture_output=True, text=True, check=False,
    )
    cargo_result = subprocess.run(
        ["cargo", "--version"], capture_output=True, text=True, check=False,
    )
    rustc_version = _parse_version(rustc_result.stdout) if rustc_result.returncode == 0 else None
    cargo_version = _parse_version(cargo_result.stdout) if cargo_result.returncode == 0 else None
    rustc_ok = rustc_version is not None and rustc_version >= MIN_RUSTC_VERSION
    cargo_ok = cargo_version is not None and cargo_version >= MIN_CARGO_VERSION
    if not (rustc_ok and cargo_ok):
        _die(
            "Incompatible versions: rustc >= 1.89.0 and cargo >= 1.89.0 required"
            f" (found rustc {rustc_result.stdout.strip()},"
            f" cargo {cargo_result.stdout.strip()})."
        )


def _resolve_registry_token():
    """@brief Resolve the crates.io authentication token.

    @details Reads `TOKEN_ENV_VARIABLE` from the environment first; when
    unset or empty, reads the JSON credentials file
    `$CARGO_HOME/credentials` (`CARGO_HOME` defaulting to `~/.cargo`) and
    extracts `TOKEN_CREDENTIALS_KEY`. Time complexity O(n) over file size.
    @return {str|None} Non-empty token string when resolvable; `None` when the
      environment variable is absent and the credentials file is missing,
      unreadable, malformed, or lacks the token key.
    @satisfies REQ-186
    """
    env_token = os.environ.get(TOKEN_ENV_VARIABLE)
    if env_token:
        return env_token
    cargo_home = Path(os.environ.get("CARGO_HOME", str(Path.home() / ".cargo")))
    credentials_file = cargo_home / "credentials"
    try:
        payload = json.loads(credentials_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    token = payload.get(TOKEN_CREDENTIALS_KEY) if isinstance(payload, dict) else None
    return token if isinstance(token, str) and token else None


def _http_request(url, token=None, payload=None):
    """@brief Execute one crates.io HTTP request and decode the JSON body.

    @details Builds a GET (`payload` is `None`) or JSON PUT request carrying
    `USER_AGENT`, `Accept: application/json`, and an `Authorization: Bearer`
    header when a token is supplied. Time complexity O(n) over response size.
    @param url {str} Absolute crates.io API endpoint URL.
    @param token {str|None} Bearer token; the header is omitted when `None`.
    @param payload {dict|None} JSON body serialized and sent via PUT when
      provided.
    @return {Any} Parsed JSON response payload.
    @throws {urllib.error.HTTPError} On HTTP error responses.
    @throws {urllib.error.URLError} On connection failures.
    @throws {json.JSONDecodeError} On malformed response bodies.
    @satisfies REQ-187, REQ-188, REQ-191
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    method = "GET"
    if payload is not None:
        method = "PUT"
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def _verify_crates_io_auth(token):
    """@brief Verify crates.io authentication through the `/me` endpoint.

    @details Sends `GET {CRATES_API}/me` with the resolved Bearer token and
    prints the authenticated account login; any HTTP error, connection
    failure, or malformed payload aborts with the `cargo login` hint.
    @param token {str} Resolved crates.io Bearer token.
    @return {None} Prints the account evidence line on success.
    @throws {SystemExit} Exit code `1` via `_die` on non-200 responses,
      connection failures, or malformed payloads.
    @satisfies REQ-187
    """
    try:
        payload = _http_request(f"{CRATES_API}/me", token=token)
        account = payload["user"]["login"]
    except urllib.error.HTTPError as error:
        _die(f"crates.io authentication unavailable (HTTP {error.code}). Run: cargo login")
    except urllib.error.URLError as error:
        _die(f"crates.io authentication check failed ({error.reason}). Run: cargo login")
    except (KeyError, json.JSONDecodeError, ValueError):
        _die("crates.io authentication check returned an unexpected payload. Run: cargo login")
    print(f"crates.io account: {account}")


def _check_crate_availability(package_name):
    """@brief Verify that the crate name is still available on crates.io.

    @details Sends `GET {CRATES_API}/crates/<package>`; HTTP 404 proves
    availability, a 200 payload listing versions aborts as taken, and any
    other outcome aborts as unverifiable. Time complexity O(1) plus network.
    @param package_name {str} Validated crate name token.
    @return {None} Returns when the name is verified available.
    @throws {SystemExit} Exit code `1` via `_die` on existing versions,
      non-404 HTTP errors, connection failures, or malformed payloads.
    @satisfies REQ-188
    """
    try:
        payload = _http_request(f"{CRATES_API}/crates/{package_name}")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return
        _die("Unable to reliably verify that the name is available.")
    except urllib.error.URLError as error:
        _die(f"Unable to reach crates.io ({error.reason}).")
    if payload.get("versions"):
        _die(
            f"Crate '{package_name}' already exists:"
            " aborting to avoid unwanted publications."
        )
    _die("Unable to reliably verify that the name is available.")


def _write_placeholder_crate(temp_dir, package_name, github_repo):
    """@brief Create the placeholder crate skeleton in the temporary directory.

    @details Runs `cargo init --name <package> --vcs none <temp_dir>` with
    captured output, aborts on failure, then overwrites the generated
    `Cargo.toml` with version `0.0.0`, the placeholder description, and the
    repository URL `https://github.com/<repo>`. The `cargo init` binary
    entrypoint compiles offline, keeping the later `cargo publish` verify
    build dependency-free.
    @param temp_dir {str|Path} Existing temporary crate directory.
    @param package_name {str} Validated crate name token.
    @param github_repo {str} Validated GitHub `owner/repo` token.
    @return {None} Writes `Cargo.toml` plus the generated `src/` skeleton.
    @throws {SystemExit} Exit code `1` via `_die` when `cargo init` fails.
    @throws {OSError} Propagated on filesystem write failure.
    @satisfies REQ-189
    """
    init = subprocess.run(
        ["cargo", "init", "--name", package_name, "--vcs", "none", str(temp_dir)],
        capture_output=True, text=True, check=False,
    )
    if init.returncode != 0:
        print_error(init.stderr.strip())
        _die("Failed to initialize the placeholder crate with cargo init.")
    cargo_toml = (
        "[package]\n"
        f'name = "{package_name}"\n'
        'version = "0.0.0"\n'
        'edition = "2021"\n'
        'description = "Initial placeholder to enable crates.io Trusted Publishing"\n'
        f'repository = "https://github.com/{github_repo}"\n'
    )
    (Path(temp_dir) / "Cargo.toml").write_text(cargo_toml, encoding="utf-8")


def _register_trusted_publisher(token, package_name, github_repo, workflow_file):
    """@brief Register the GitHub trusted publisher through the crates.io API.

    @details Sends `PUT {CRATES_API}/crates/<package>/trusted_publishing/github_actions_config`
    with JSON body `{"repository": "<owner/repo>", "workflow": "<workflow>"}`
    and the resolved Bearer token. Time complexity O(1) plus network.
    @param token {str} Resolved crates.io Bearer token.
    @param package_name {str} Validated crate name token.
    @param github_repo {str} Validated GitHub `owner/repo` token.
    @param workflow_file {str} Validated bare workflow filename token.
    @return {None} Returns when the trusted publisher is created.
    @throws {SystemExit} Exit code `1` via `_die` with the
      publication-without-trust diagnostic on HTTP or connection failures.
    @satisfies REQ-191
    """
    url = f"{CRATES_API}/crates/{package_name}/trusted_publishing/github_actions_config"
    body = {"repository": github_repo, "workflow": workflow_file}
    try:
        _http_request(url, token=token, payload=body)
    except urllib.error.HTTPError as error:
        _die(
            f"Crate '{package_name}' published, but the trust was NOT created"
            f" (HTTP {error.code})."
            " Configure it manually on crates.io or retry only the"
            " trusted-publishing registration."
        )
    except urllib.error.URLError as error:
        _die(
            f"Crate '{package_name}' published, but the trust was NOT created"
            f" ({error.reason})."
            " Configure it manually on crates.io or retry only the"
            " trusted-publishing registration."
        )


def print_help(version):
    """@brief Print command-specific help text.

    @details Renders usage line, option list, and behavioral summary in
    English, following the shared command help layout.
    @param version {str} Current CLI version token rendered in the usage line.
    @return {None} Writes to stdout.
    @satisfies PRJ-002, REQ-182
    """
    print(f"Usage: {PROGRAM} cargo-bootstrap-trust ({version})")
    print()
    print("cargo-bootstrap-trust options:")
    print("  --help        - Show this help message.")
    print("  -p <package>  - New crates.io crate name.")
    print("  -r <owner/repo> - GitHub repository in owner/repo format.")
    print("  -f <workflow.yml> - Workflow file name inside .github/workflows/.")
    print()
    print("Publishes a temporary 0.0.0 placeholder crate and registers the")
    print("GitHub Trusted Publisher configuration for the crate on crates.io.")


def run(args):
    """@brief Execute the five-phase crates.io bootstrap and trust pipeline.

    @details Phase order: `[1/5]` crates.io authentication via the `/me`
    endpoint using the token resolved by `_resolve_registry_token`;
    `[2/5]` crate availability via the crates.io crate endpoint, aborting on
    existing versions or a failure without an HTTP 404 marker; `[3/5]`
    placeholder crate creation in a fresh temporary directory;
    `[4/5]` publication via `cargo publish`; `[5/5]` GitHub trusted-publisher
    creation through the crates.io trusted-publishing API plus trust
    configuration verification. The temporary directory is removed on every
    exit path; every failure aborts with exit code `1`.
    @param args {list[str]} Command arguments (without the command token).
    @return {int} `0` after successful publication and trust verification.
    @throws {SystemExit} Exit code `1` on usage errors, invalid inputs,
      missing or incompatible toolchain, failed authentication, taken or
      unverifiable crate name, failed publication, or failed trust
      creation/verification.
    @satisfies REQ-182, REQ-183, REQ-184, REQ-185, REQ-186, REQ-187, REQ-188,
    REQ-189, REQ-190, REQ-191, REQ-192
    """
    parser = _build_parser()
    opts = parser.parse_args(args)

    _validate_inputs(opts.package, opts.repo, opts.workflow)
    _require_toolchain()

    temp_dir = None
    try:
        print("[1/5] Verifying crates.io authentication...")
        token = _resolve_registry_token()
        if not token:
            _die("crates.io authentication unavailable. Run: cargo login")
        _verify_crates_io_auth(token)
        print("NOTE: trusted publishing requires write permission on the crate.")

        temp_dir = tempfile.mkdtemp(prefix="cargo-bootstrap.")

        print("[2/5] Verifying that the crate does not exist yet...")
        _check_crate_availability(opts.package)

        print("[3/5] Creating the temporary placeholder crate...")
        _write_placeholder_crate(temp_dir, opts.package, opts.repo)

        print(f"[4/5] Publishing {opts.package}@0.0.0...")
        publish = subprocess.run(
            ["cargo", "publish"],
            cwd=temp_dir, check=False,
        )
        if publish.returncode != 0:
            _die("Initial publish failed. The trust was not created.")

        print("[5/5] Creating the GitHub Trusted Publisher...")
        _register_trusted_publisher(token, opts.package, opts.repo, opts.workflow)

        print()
        print(f"Trust registered for {opts.package}:")
        url = f"{CRATES_API}/crates/{opts.package}/trusted_publishing/github_actions_config"
        try:
            trust_payload = _http_request(url, token=token)
        except (urllib.error.HTTPError, urllib.error.URLError):
            _die(
                "Trust created by the command, but the configuration could not"
                " be read for later verification."
            )
        print(json.dumps(trust_payload, indent=2, sort_keys=True))
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

    print()
    print(f"Operation completed: {opts.package}@0.0.0 published; trust creation command succeeded.")
    print("WARNING: the trust will be validated only after a successful OIDC publish")
    print("from the workflow within 2 days.")
    print("The GitHub repository/workflow are not created by this command.")
    return 0
