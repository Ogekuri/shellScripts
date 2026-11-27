# Files Structure
```
.
└── src
    └── shell_scripts
        ├── __init__.py
        ├── __main__.py
        ├── commands
        │   ├── __init__.py
        │   ├── _dc_common.py
        │   ├── _yolo_common.py
        │   ├── agy.py
        │   ├── cargo_bootstrap_trust.py
        │   ├── chrome_debug.py
        │   ├── claude.py
        │   ├── clean.py
        │   ├── codex.py
        │   ├── copilot.py
        │   ├── dicom2jpg.py
        │   ├── dicomviewer.py
        │   ├── diff_cmd.py
        │   ├── doxygen_cmd.py
        │   ├── edit_cmd.py
        │   ├── meld_highlight_theme.py
        │   ├── net_cmd.py
        │   ├── npm_bootstrap_trust.py
        │   ├── opencode.py
        │   ├── pdf_crop.py
        │   ├── pdf_merge.py
        │   ├── pdf_split_by_format.py
        │   ├── pdf_split_by_toc.py
        │   ├── pdf_tiler_090.py
        │   ├── pdf_tiler_100.py
        │   ├── pdf_toc_clean.py
        │   ├── tests_cmd.py
        │   ├── ubuntu_dark_theme.py
        │   ├── venv_cmd.py
        │   ├── video2h264.py
        │   ├── video2h265.py
        │   ├── view_cmd.py
        │   ├── vscode_cmd.py
        │   └── vsinsider_cmd.py
        ├── config_cli.py
        ├── config.py
        ├── core.py
        ├── utils.py
        └── version_check.py
```

# __init__.py | Python | 5L | 0 symbols | 1 imports | 0 comments
> Path: `src/shell_scripts/__init__.py`

## Imports
```
from .core import main  # noqa: F401
```


---

# __main__.py | Python | 5L | 0 symbols | 2 imports | 0 comments
> Path: `src/shell_scripts/__main__.py`

## Imports
```
from .core import main
import sys
```


---

# __init__.py | Python | 83L | 2 symbols | 2 imports | 8 comments
> Path: `src/shell_scripts/commands/__init__.py`

## Imports
```
import importlib
from types import ModuleType
```

## Definitions

### fn `def get_command(name: str) -> ModuleType | None` (L53-68)
- @brief Static map from CLI command names to importable module paths.
- @brief Resolve one CLI command token to its command module.
- @details Enables lazy command loading and deterministic command exposure.
Removing an entry removes command discoverability and dispatch reachability.
- @details Performs O(1) dictionary lookup on `_COMMAND_MODULES`; returns `None` for unknown tokens; imports target module lazily only on hit.
- @param name {str} CLI command token.
- @return {ModuleType|None} Imported command module for known token; `None` otherwise.
- @throws {ImportError} If module path exists in map but import fails.
- @satisfies PRJ-003, DES-001
- @satisfies PRJ-001, DES-001, DES-008, DES-069, REQ-057, REQ-058

### fn `def get_all_commands() -> dict[str, str]` (L69-84)
- @brief Build command-description index for help rendering.
- @details Iterates sorted command keys for stable output ordering; imports each module via `get_command`; extracts `DESCRIPTION` or empty string. Time complexity O(N log N) for N commands due to key sorting.
- @return {dict[str, str]} Mapping `command_name -> description`.
- @throws {ImportError} If any mapped command module import fails.
- @satisfies PRJ-002, DES-001, DES-008, DES-069, REQ-057, REQ-058

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_command`|fn|pub|53-68|def get_command(name: str) -> ModuleType | None|
|`get_all_commands`|fn|pub|69-84|def get_all_commands() -> dict[str, str]|


---

# _dc_common.py | Python | 138L | 9 symbols | 3 imports | 5 comments
> Path: `src/shell_scripts/commands/_dc_common.py`

## Imports
```
import os
import subprocess
from shell_scripts.utils import is_executable_command, print_error
```

## Definitions

- var `CODE_EXTENSIONS = {` (L14)
- var `MARKDOWN_EXTENSIONS = {"md", "markdown", "mdown", "mkd"}` (L22)
- var `HTML_EXTENSIONS = {"html", "htm", "xhtml"}` (L23)
- var `IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "svg"}` (L24)
### fn `def get_extension(filepath)` (L27-33)

### fn `def detect_mime(filepath)` (L34-60)
- @brief Detect file MIME type with external tools.
- @details Probes MIME by trying `mimetype` then `file --mime-type`, using executable availability checks before subprocess invocation.
- @param filepath {str} Target file path.
- @return {str} MIME type string or empty string on detection failure.
- @satisfies REQ-024, REQ-056

### fn `def categorize(filepath)` (L61-98)

### fn `def pick_cmd(primary, fallback)` (L99-114)
- @brief Select primary command when executable, else fallback.
- @details Uses shared executable-check helper on first token of primary command vector.
- @param primary {list[str]} Preferred command vector.
- @param fallback {list[str]} Fallback command vector.
- @return {list[str]} Selected executable command vector.
- @satisfies REQ-024, REQ-055

### fn `def dispatch(category_cmds, fallback_cmd, filepath, extra_args)` (L115-139)
- @brief Dispatch diff/edit/view command by detected file category.
- @details Resolves category-specific command vector, validates executable availability, and executes selected command via blocking subprocess run.
- @param category_cmds {dict[str, list[str]]} Category-to-command mapping.
- @param fallback_cmd {list[str]} Fallback command vector.
- @param filepath {str} Target file path.
- @param extra_args {list[str]} Additional arguments forwarded to executable.
- @return {int} `1` when executable is unavailable; child return code otherwise.
- @satisfies REQ-024, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`CODE_EXTENSIONS`|var|pub|14||
|`MARKDOWN_EXTENSIONS`|var|pub|22||
|`HTML_EXTENSIONS`|var|pub|23||
|`IMAGE_EXTENSIONS`|var|pub|24||
|`get_extension`|fn|pub|27-33|def get_extension(filepath)|
|`detect_mime`|fn|pub|34-60|def detect_mime(filepath)|
|`categorize`|fn|pub|61-98|def categorize(filepath)|
|`pick_cmd`|fn|pub|99-114|def pick_cmd(primary, fallback)|
|`dispatch`|fn|pub|115-139|def dispatch(category_cmds, fallback_cmd, filepath, extra...|


---

# _yolo_common.py | Python | 184L | 5 symbols | 4 imports | 29 comments
> Path: `src/shell_scripts/commands/_yolo_common.py`

## Imports
```
from __future__ import annotations
import subprocess
from dataclasses import dataclass
from shell_scripts.utils import require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L21)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
### class `class YoloCliSpec` `@dataclass(frozen=True)` (L25-52)
- @brief Declarative definition of one YOLO-mode external AI CLI.
- @details Immutable registry record; a command module becomes a YOLO launcher by binding exactly one instance of this record.
- @satisfies DES-030

### fn `def get_yolo_spec(command: str) -> YoloCliSpec` (L112-124)
- @brief O(1) command-token lookup index over `YOLO_CLI_REGISTRY`.
- @brief Resolve the declarative YOLO CLI record for one command token.
- @details Performs O(1) dictionary lookup on `YOLO_CLI_INDEX`. Time complexity O(1).
- @param command {str} Dispatcher command token (for example `codex`).
- @return {YoloCliSpec} Registry record bound to the command token.
- @throws {KeyError} If the command token is not registered.
- @satisfies DES-030
- @satisfies DES-030

### fn `def print_yolo_help(command: str, version: str, description: str) -> None` (L125-163)
- @brief Render YOLO command help documenting the full YOLO CLI registry.
- @details Emits the command description, usage line, executed YOLO option with its behavioral note, optional documented alternative option, and the complete registry listing with every executed option and note in ascending alphabetical command order; does not mutate process state. Time complexity O(n) over registered YOLO CLI record count.
- @param command {str} Dispatcher command token whose help is rendered.
- @param version {str} CLI version string propagated by dispatcher.
- @param description {str} One-line command description for the help header.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-086, REQ-092, REQ-093

### fn `def run_yolo_cli(command: str, args: list[str]) -> int` (L164-185)
- @brief Launch one registered YOLO CLI after executable validation.
- @details Resolves the registry record, validates executable availability for the record executable, builds the command vector `[resolved_executable, option] + args`, then executes it through blocking `subprocess.run` with inherited stdio. Performs no Git repository root validation and emits no project-root error output. Time complexity O(n) over forwarded argument count.
- @param command {str} Registered dispatcher command token.
- @param args {list[str]} Additional CLI args forwarded to the external CLI.
- @return {int} Child process return code.
- @throws {KeyError} If the command token is not registered.
- @satisfies REQ-014, REQ-015, REQ-017, REQ-018, REQ-085, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|21||
|`YoloCliSpec`|class|pub|25-52|class YoloCliSpec|
|`get_yolo_spec`|fn|pub|112-124|def get_yolo_spec(command: str) -> YoloCliSpec|
|`print_yolo_help`|fn|pub|125-163|def print_yolo_help(command: str, version: str, descripti...|
|`run_yolo_cli`|fn|pub|164-185|def run_yolo_cli(command: str, args: list[str]) -> int|


---

# agy.py | Python | 50L | 4 symbols | 1 imports | 10 comments
> Path: `src/shell_scripts/commands/agy.py`

## Imports
```
from shell_scripts.commands._yolo_common import (
```

## Definitions

- var `DESCRIPTION = "Launch Antigravity CLI in the project context."` (L19)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
- var `SPEC = get_yolo_spec("agy")` (L23)
- @brief Declarative YOLO CLI record bound to the `agy` command token.
- @satisfies DES-030, REQ-085
### fn `def print_help(version: str) -> None` (L26-38)
- @brief Print command-specific help for `agy`.
- @details Delegates to the shared YOLO help renderer, which emits the executed option documentation and the alphabetical YOLO CLI registry. Time complexity O(n) over registered YOLO CLI record count.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-086, REQ-092

### fn `def run(args: list[str]) -> int` (L39-51)
- @brief Launch Antigravity CLI in YOLO mode after executable validation.
- @details Delegates to the shared YOLO runner executing `agy --dangerously-skip-permissions` plus pass-through args through blocking subprocess run with inherited stdio. Time complexity O(n) over forwarded argument count.
- @param args {list[str]} Additional CLI args forwarded to Antigravity.
- @return {int} Child process return code.
- @satisfies REQ-085, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`DESCRIPTION`|var|pub|19||
|`SPEC`|var|pub|23||
|`print_help`|fn|pub|26-38|def print_help(version: str) -> None|
|`run`|fn|pub|39-51|def run(args: list[str]) -> int|


---

# cargo_bootstrap_trust.py | Python | 626L | 35 symbols | 14 imports | 90 comments
> Path: `src/shell_scripts/commands/cargo_bootstrap_trust.py`

## Imports
```
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.error
import urllib.request
from typing import NoReturn
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L33)
- var `DESCRIPTION = "Bootstrap a new crates.io crate and register its GitHub trusted publisher."` (L34)
- var `CRATES_API = "https://crates.io/api/v1"` (L41)
- @brief Canonical crates.io API base URL used by every registry request.
- @details Authentication, availability, and trusted-publishing calls all
target this base so operations never depend on ambient registry mirrors.
- @satisfies REQ-187, REQ-188, REQ-191
- var `USER_AGENT = f"{PROGRAM} cargo-bootstrap-trust"` (L46)
- @brief HTTP User-Agent header value sent with every crates.io request.
- @details crates.io rejects requests that omit a descriptive User-Agent.
- var `HTTP_TIMEOUT = 10` (L50)
- @brief Timeout in seconds applied to every crates.io HTTP request.
- var `TOKEN_ENV_VARIABLE = "CARGO_REGISTRIES_CRATES_IO_TOKEN"` (L56)
- @brief Environment variable holding the crates.io token override.
- @details First token-resolution source; wins over the credentials file.
- @satisfies REQ-186
- var `TOKEN_CREDENTIALS_KEY = "registry.crates.io-token"` (L63)
- @brief JSON key of the crates.io token inside the cargo credentials file.
- @details Second token-resolution source, read from
`$CARGO_HOME/credentials` with `CARGO_HOME` defaulting to `~/.cargo`.
- @satisfies REQ-186
- var `TOKEN_TOML_FILE = "credentials.toml"` (L72)
- @brief Filename of the modern TOML cargo credentials file.
- @details Third token-resolution source filename, joined under
`$CARGO_HOME` (defaulting to `~/.cargo`); written by `cargo login` of
cargo >= 1.66, including the cargo >= 1.89 versions enforced by
`MIN_CARGO_VERSION`.
- @satisfies REQ-186
- var `TOML_REGISTRY_TOKEN_PATH = ("registry", "token")` (L80)
- @brief Dotted TOML path of the default-registry token inside
`credentials.toml`.
- @details Preferred TOML token location `registry.token`, equivalent to
the `[registry] token` section written by `cargo login`.
- @satisfies REQ-186
- var `TOML_REGISTRIES_TOKEN_PATH = ("registries", "crates-io", "token")` (L88)
- @brief Dotted TOML path of the named-registry token inside
`credentials.toml`.
- @details Fallback TOML token location `registries.crates-io.token`,
equivalent to the `[registries.crates-io] token` section.
- @satisfies REQ-186
- var `MIN_RUSTC_VERSION = (1, 89, 0)` (L94)
- @brief Minimum supported rustc version tuple `(1, 89, 0)`.
- @details Versions comparing lower abort the command.
- @satisfies REQ-185
- var `MIN_CARGO_VERSION = (1, 89, 0)` (L101)
- @brief Minimum supported cargo version tuple `(1, 89, 0)`.
- @details cargo 1.89 ships the crates.io Trusted Publishing support required
by the OIDC publish executed from the configured GitHub workflow.
- @satisfies REQ-185
- var `CRATE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")` (L108)
- @brief Anchored conservative crate-name regex `^[a-z0-9][a-z0-9_-]*$`.
- @details Accepts only lowercase ASCII letters, digits, `-`, and `_` with a
non-leading separator; uppercase letters and dots are rejected.
- @satisfies REQ-183
- var `MAX_CRATE_NAME_LENGTH = 64` (L113)
- @brief Maximum accepted crate-name length matching the crates.io limit.
- @satisfies REQ-183
- var `GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$")` (L120)
- @brief Anchored `owner/repo` validation regex
`^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$`.
- @details Repository tokens MUST NOT be URLs or carry extra slashes.
- @satisfies REQ-184
- var `WORKFLOW_FILE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$")` (L127)
- @brief Anchored bare workflow-filename regex
`^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$`.
- @details Rejects paths, directory components, and unsupported extensions.
- @satisfies REQ-184
- var `VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")` (L134)
- @brief Anchored strict `X.Y.Z` semantic-version regex.
- @details Used to locate the version token inside `rustc --version` and
`cargo --version` output; malformed values abort the version gate.
- @satisfies REQ-185
### class `class _UsageParser(argparse.ArgumentParser)` : argparse.ArgumentParser `priv` (L137-161)
- @brief `argparse` parser variant preserving the legacy exit code.
- @details Overrides `error` so usage errors print the message plus usage text to stderr and terminate with exit code `1`, matching the `npm-bootstrap-trust` `usage(1)`/`die` semantics instead of the argparse default `2`.
- @satisfies REQ-182
- fn `def error(self, message)` (L147-161)
  - @brief `argparse` parser variant preserving the legacy exit code.
  - @brief Terminate argument parsing with the legacy failure contract.
  - @details Overrides `error` so usage errors print the message plus usage
text to stderr and terminate with exit code `1`, matching the
`npm-bootstrap-trust` `usage(1)`/`die` semantics instead of the argparse
default `2`.
  - @details Prints the bare message to stderr, then the usage text, then raises `SystemExit(1)`.
  - @param message {str} Parsing error description.
  - @return {None} Never returns; raises `SystemExit`.
  - @throws {SystemExit} Always exit code `1`.
  - @satisfies REQ-182
  - @satisfies REQ-182

### fn `def _build_parser()` `priv` (L162-190)
- @brief Build the `cargo-bootstrap-trust` argument parser.
- @details Registers required `-p/--package`, `-r/--repo`, and `-f/--workflow` options plus the default `-h/--help` action on the `_UsageParser` variant.
- @return {_UsageParser} Configured parser instance.
- @satisfies REQ-182

### fn `def _die(message) -> NoReturn` `priv` (L191-206)
- @brief Print an error line and terminate with exit code `1`.
- @details Mirrors the `npm-bootstrap-trust` `die` helper using the shared `[ERROR]` stderr renderer.
- @param message {str} Failure description rendered after the `[ERROR]` prefix.
- @return {None} Never returns; raises `SystemExit`.
- @throws {SystemExit} Always exit code `1`.
- @satisfies REQ-182, REQ-183, REQ-184, REQ-185, REQ-187, REQ-188, REQ-190, REQ-191

### fn `def _validate_inputs(package_name, github_repo, workflow_file)` `priv` (L207-235)
- @brief Validate the conservative crate, repository, and workflow tokens.
- @details Applies `CRATE_NAME_PATTERN` plus `MAX_CRATE_NAME_LENGTH`, the `GITHUB_REPO_PATTERN` plus owner length at most 39 and owner not ending with `-`, and `WORKFLOW_FILE_PATTERN`, aborting with the shared English diagnostics on the first failure.
- @param package_name {str} crates.io crate name token.
- @param github_repo {str} GitHub `owner/repo` token.
- @param workflow_file {str} Bare workflow filename token.
- @return {None} Returns on full validation.
- @throws {SystemExit} Exit code `1` via `_die` on the first invalid token.
- @satisfies REQ-183, REQ-184

### fn `def _parse_version(text)` `priv` (L236-254)
- @brief Extract one strict `X.Y.Z` version tuple from tool output.
- @details Scans whitespace-separated tokens of `rustc --version` or `cargo --version` output and returns the first token matching `VERSION_PATTERN`; tool banners prefix the version with the binary name, so no positional assumption is made.
- @param text {str} Raw version output token.
- @return {tuple[int, int, int]|None} Numeric version tuple, or `None` when no token matches the strict format.
- @satisfies REQ-185

### fn `def _require_toolchain()` `priv` (L255-287)
- @brief Validate rustc and cargo presence plus minimum versions.
- @details Checks `rustc` and `cargo` executables via `require_commands`, captures `rustc --version` and `cargo --version`, parses both with `_parse_version`, and aborts when either executable reports a version lower than `MIN_RUSTC_VERSION` or `MIN_CARGO_VERSION` respectively or an unparseable value.
- @return {None} Returns when the toolchain satisfies the version gate.
- @throws {SystemExit} Exit code `1` via `require_commands` on missing executables or via `_die` on incompatible versions.
- @satisfies REQ-185, CTN-003, REQ-056

### fn `def _resolve_registry_token()` `priv` (L288-310)
- @brief Resolve the crates.io authentication token.
- @details Checks sources in priority order: `TOKEN_ENV_VARIABLE` from the environment; the TOML credentials file `$CARGO_HOME/credentials.toml` (`CARGO_HOME` defaulting to `~/.cargo`) via `_read_toml_credentials_token`; the legacy JSON credentials file `$CARGO_HOME/credentials` via `_read_legacy_json_token`. Time complexity O(n) over the largest credentials file size.
- @return {str|None} Non-empty token string when resolvable; `None` when every source is absent, unreadable, malformed, or lacks a token value.
- @satisfies REQ-186

### fn `def _read_toml_credentials_token(cargo_home)` `priv` (L311-337)
- @brief Read the crates.io token from the modern TOML credentials file.
- @details Parses `$CARGO_HOME/credentials.toml` with `tomllib`, then tries `TOML_REGISTRY_TOKEN_PATH` before `TOML_REGISTRIES_TOKEN_PATH` and returns the first non-empty string token. Missing, unreadable, or malformed files resolve to `None` so later sources stay consultable. Time complexity O(n) over file size.
- @param cargo_home {Path} Resolved cargo home directory containing `credentials.toml`.
- @return {str|None} Non-empty token string when resolvable; `None` otherwise.
- @satisfies REQ-186

### fn `def _lookup_toml_token_path(payload, path)` `priv` (L338-356)
- @brief Walk one dotted TOML path and return its non-empty string leaf.
- @details Traverses nested TOML tables segment by segment, rejecting non-mapping intermediates and non-string or empty leaves. Time complexity O(depth) over the requested path length.
- @param payload {dict} Parsed TOML document.
- @param path {tuple[str, ...]} Dotted path segments to resolve.
- @return {str|None} Leaf string value when present and non-empty; `None` otherwise.

### fn `def _read_legacy_json_token(cargo_home)` `priv` (L357-377)
- @brief Read the crates.io token from the legacy JSON credentials file.
- @details Parses `$CARGO_HOME/credentials` as JSON and extracts `TOKEN_CREDENTIALS_KEY`. Missing, unreadable, malformed, or tokenless files resolve to `None`. Time complexity O(n) over file size.
- @param cargo_home {Path} Resolved cargo home directory containing the legacy `credentials` file.
- @return {str|None} Non-empty token string when resolvable; `None` otherwise.
- @satisfies REQ-186

### fn `def _http_request(url, token=None, payload=None)` `priv` (L378-407)
- @brief Execute one crates.io HTTP request and decode the JSON body.
- @details Builds a GET (`payload` is `None`) or JSON PUT request carrying `USER_AGENT`, `Accept: application/json`, and an `Authorization: Bearer` header when a token is supplied. Time complexity O(n) over response size.
- @param url {str} Absolute crates.io API endpoint URL.
- @param token {str|None} Bearer token; the header is omitted when `None`.
- @param payload {dict|None} JSON body serialized and sent via PUT when provided.
- @return {Any} Parsed JSON response payload.
- @throws {urllib.error.HTTPError} On HTTP error responses.
- @throws {urllib.error.URLError} On connection failures.
- @throws {json.JSONDecodeError} On malformed response bodies.
- @satisfies REQ-187, REQ-188, REQ-191

### fn `def _verify_crates_io_auth(token)` `priv` (L408-431)
- @brief Verify crates.io authentication through the `/me` endpoint.
- @details Sends `GET {CRATES_API}/me` with the resolved Bearer token and prints the authenticated account login; any HTTP error, connection failure, or malformed payload aborts with the `cargo login` hint.
- @param token {str} Resolved crates.io Bearer token.
- @return {None} Prints the account evidence line on success.
- @throws {SystemExit} Exit code `1` via `_die` on non-200 responses, connection failures, or malformed payloads.
- @satisfies REQ-187

### fn `def _check_crate_availability(package_name)` `priv` (L432-459)
- @brief Verify that the crate name is still available on crates.io.
- @details Sends `GET {CRATES_API}/crates/<package>`; HTTP 404 proves availability, a 200 payload listing versions aborts as taken, and any other outcome aborts as unverifiable. Time complexity O(1) plus network.
- @param package_name {str} Validated crate name token.
- @return {None} Returns when the name is verified available.
- @throws {SystemExit} Exit code `1` via `_die` on existing versions, non-404 HTTP errors, connection failures, or malformed payloads.
- @satisfies REQ-188

### fn `def _write_placeholder_crate(temp_dir, package_name, github_repo)` `priv` (L460-494)
- @brief Create the placeholder crate skeleton in the temporary directory.
- @details Runs `cargo init --name <package> --vcs none <temp_dir>` with captured output, aborts on failure, then overwrites the generated `Cargo.toml` with version `0.0.0`, the placeholder description, and the repository URL `https://github.com/<repo>`. The `cargo init` binary entrypoint compiles offline, keeping the later `cargo publish` verify build dependency-free.
- @param temp_dir {str|Path} Existing temporary crate directory.
- @param package_name {str} Validated crate name token.
- @param github_repo {str} Validated GitHub `owner/repo` token.
- @return {None} Writes `Cargo.toml` plus the generated `src/` skeleton.
- @throws {SystemExit} Exit code `1` via `_die` when `cargo init` fails.
- @throws {OSError} Propagated on filesystem write failure.
- @satisfies REQ-189

### fn `def _register_trusted_publisher(token, package_name, github_repo, workflow_file)` `priv` (L495-529)
- @brief Register the GitHub trusted publisher through the crates.io API.
- @details Sends `PUT {CRATES_API}/crates/<package>/trusted_publishing/github_actions_config` with JSON body `{"repository": "<owner/repo>", "workflow": "<workflow>"}` and the resolved Bearer token. Time complexity O(1) plus network.
- @param token {str} Resolved crates.io Bearer token.
- @param package_name {str} Validated crate name token.
- @param github_repo {str} Validated GitHub `owner/repo` token.
- @param workflow_file {str} Validated bare workflow filename token.
- @return {None} Returns when the trusted publisher is created.
- @throws {SystemExit} Exit code `1` via `_die` with the publication-without-trust diagnostic on HTTP or connection failures.
- @satisfies REQ-191

### fn `def print_help(version)` (L530-550)
- @brief Print command-specific help text.
- @details Renders usage line, option list, and behavioral summary in English, following the shared command help layout.
- @param version {str} Current CLI version token rendered in the usage line.
- @return {None} Writes to stdout.
- @satisfies PRJ-002, REQ-182

### fn `def run(args)` (L551-627)
- @brief Execute the five-phase crates.io bootstrap and trust pipeline.
- @details Phase order: `[1/5]` crates.io authentication via the `/me` endpoint using the token resolved by `_resolve_registry_token`; `[2/5]` crate availability via the crates.io crate endpoint, aborting on existing versions or a failure without an HTTP 404 marker; `[3/5]` placeholder crate creation in a fresh temporary directory; `[4/5]` publication via `cargo publish`; `[5/5]` GitHub trusted-publisher creation through the crates.io trusted-publishing API plus trust configuration verification. The temporary directory is removed on every exit path; every failure aborts with exit code `1`.
- @param args {list[str]} Command arguments (without the command token).
- @return {int} `0` after successful publication and trust verification.
- @throws {SystemExit} Exit code `1` on usage errors, invalid inputs, missing or incompatible toolchain, failed authentication, taken or unverifiable crate name, failed publication, or failed trust creation/verification.
- @satisfies REQ-182, REQ-183, REQ-184, REQ-185, REQ-186, REQ-187, REQ-188, REQ-189, REQ-190, REQ-191, REQ-192

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|33||
|`DESCRIPTION`|var|pub|34||
|`CRATES_API`|var|pub|41||
|`USER_AGENT`|var|pub|46||
|`HTTP_TIMEOUT`|var|pub|50||
|`TOKEN_ENV_VARIABLE`|var|pub|56||
|`TOKEN_CREDENTIALS_KEY`|var|pub|63||
|`TOKEN_TOML_FILE`|var|pub|72||
|`TOML_REGISTRY_TOKEN_PATH`|var|pub|80||
|`TOML_REGISTRIES_TOKEN_PATH`|var|pub|88||
|`MIN_RUSTC_VERSION`|var|pub|94||
|`MIN_CARGO_VERSION`|var|pub|101||
|`CRATE_NAME_PATTERN`|var|pub|108||
|`MAX_CRATE_NAME_LENGTH`|var|pub|113||
|`GITHUB_REPO_PATTERN`|var|pub|120||
|`WORKFLOW_FILE_PATTERN`|var|pub|127||
|`VERSION_PATTERN`|var|pub|134||
|`_UsageParser`|class|priv|137-161|class _UsageParser(argparse.ArgumentParser)|
|`_UsageParser.error`|fn|pub|147-161|def error(self, message)|
|`_build_parser`|fn|priv|162-190|def _build_parser()|
|`_die`|fn|priv|191-206|def _die(message) -> NoReturn|
|`_validate_inputs`|fn|priv|207-235|def _validate_inputs(package_name, github_repo, workflow_...|
|`_parse_version`|fn|priv|236-254|def _parse_version(text)|
|`_require_toolchain`|fn|priv|255-287|def _require_toolchain()|
|`_resolve_registry_token`|fn|priv|288-310|def _resolve_registry_token()|
|`_read_toml_credentials_token`|fn|priv|311-337|def _read_toml_credentials_token(cargo_home)|
|`_lookup_toml_token_path`|fn|priv|338-356|def _lookup_toml_token_path(payload, path)|
|`_read_legacy_json_token`|fn|priv|357-377|def _read_legacy_json_token(cargo_home)|
|`_http_request`|fn|priv|378-407|def _http_request(url, token=None, payload=None)|
|`_verify_crates_io_auth`|fn|priv|408-431|def _verify_crates_io_auth(token)|
|`_check_crate_availability`|fn|priv|432-459|def _check_crate_availability(package_name)|
|`_write_placeholder_crate`|fn|priv|460-494|def _write_placeholder_crate(temp_dir, package_name, gith...|
|`_register_trusted_publisher`|fn|priv|495-529|def _register_trusted_publisher(token, package_name, gith...|
|`print_help`|fn|pub|530-550|def print_help(version)|
|`run`|fn|pub|551-627|def run(args)|


---

# chrome_debug.py | Python | 87L | 6 symbols | 3 imports | 14 comments
> Path: `src/shell_scripts/commands/chrome_debug.py`

## Imports
```
from pathlib import Path
import subprocess
from shell_scripts.utils import print_info, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L16)
- var `DESCRIPTION = "Launch Google Chrome with remote debugging enabled."` (L17)
- var `DEBUG_PORT = 9222` (L24)
- @brief Fixed Chrome remote-debugging TCP port.
- @details Passed to Chrome as `--remote-debugging-port` and rendered in the
final attach URL.
- @satisfies REQ-169
- var `USER_DATA_SUBDIR = Path(".config") / "google-chrome"` (L31)
- @brief Home-relative Chrome user-data directory path.
- @details Resolved against `Path.home()` at launch time, matching the
legacy script `$HOME/.config/google-chrome` value.
- @satisfies REQ-169
### fn `def print_help(version)` (L34-52)
- @brief Print command-specific help text.
- @details Renders usage line, option list, and behavioral summary in English, following the shared command help layout.
- @param version {str} Current CLI version token rendered in the usage line.
- @return {None} Writes to stdout.
- @satisfies PRJ-002, REQ-169

### fn `def run(args)` (L53-88)
- @brief Spawn the detached Chrome remote-debugging instance.
- @details Validates the `google-chrome` executable, resolves the user-data directory from `Path.home()`, prints English progress messages, spawns `google-chrome --remote-debugging-port=<port> --user-data-dir=<dir>` via `subprocess.Popen` with all stdio streams set to `DEVNULL` and `start_new_session=True` (equivalent to `nohup ... &`), and returns without waiting so the browser outlives the CLI process.
- @param args {list[str]} Unused command arguments.
- @return {int} `0` after spawning the detached browser process.
- @throws {SystemExit} Exit code `1` via `require_commands` when `google-chrome` is not executable.
- @satisfies REQ-169, REQ-170, CTN-003, REQ-056

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|16||
|`DESCRIPTION`|var|pub|17||
|`DEBUG_PORT`|var|pub|24||
|`USER_DATA_SUBDIR`|var|pub|31||
|`print_help`|fn|pub|34-52|def print_help(version)|
|`run`|fn|pub|53-88|def run(args)|


---

# claude.py | Python | 50L | 4 symbols | 1 imports | 10 comments
> Path: `src/shell_scripts/commands/claude.py`

## Imports
```
from shell_scripts.commands._yolo_common import (
```

## Definitions

- var `DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."` (L19)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
- var `SPEC = get_yolo_spec("claude")` (L23)
- @brief Declarative YOLO CLI record bound to the `claude` command token.
- @satisfies DES-030, REQ-017
### fn `def print_help(version: str) -> None` (L26-38)
- @brief Print command-specific help for `claude`.
- @details Delegates to the shared YOLO help renderer, which emits the executed option documentation and the alphabetical YOLO CLI registry. Time complexity O(n) over registered YOLO CLI record count.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-086, REQ-092

### fn `def run(args: list[str]) -> int` (L39-51)
- @brief Launch Claude CLI in YOLO mode after executable validation.
- @details Delegates to the shared YOLO runner executing the PATH-resolved `claude --dangerously-skip-permissions` plus pass-through args through blocking subprocess run with inherited stdio. Time complexity O(n) over forwarded argument count.
- @param args {list[str]} Additional CLI args forwarded to Claude.
- @return {int} Child process return code.
- @satisfies REQ-017, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`DESCRIPTION`|var|pub|19||
|`SPEC`|var|pub|23||
|`print_help`|fn|pub|26-38|def print_help(version: str) -> None|
|`run`|fn|pub|39-51|def run(args: list[str]) -> int|


---

# clean.py | Python | 98L | 5 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/clean.py`

## Imports
```
import os
import shutil
from pathlib import Path
from shell_scripts.utils import require_project_root, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Find and delete cache directories under the project root."` (L9)
- var `CACHE_DIRS = [` (L11)
### fn `def print_help(version)` (L25-33)

### fn `def run(args)` (L34-99)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`CACHE_DIRS`|var|pub|11||
|`print_help`|fn|pub|25-33|def print_help(version)|
|`run`|fn|pub|34-99|def run(args)|


---

# codex.py | Python | 50L | 4 symbols | 1 imports | 10 comments
> Path: `src/shell_scripts/commands/codex.py`

## Imports
```
from shell_scripts.commands._yolo_common import (
```

## Definitions

- var `DESCRIPTION = "Launch OpenAI Codex CLI in the project context."` (L20)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
- var `SPEC = get_yolo_spec("codex")` (L24)
- @brief Declarative YOLO CLI record bound to the `codex` command token.
- @satisfies DES-030, REQ-014
### fn `def print_help(version: str) -> None` (L27-39)
- @brief Print command-specific help for `codex`.
- @details Delegates to the shared YOLO help renderer, which emits the executed option documentation and the alphabetical YOLO CLI registry. Time complexity O(n) over registered YOLO CLI record count.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-086, REQ-092

### fn `def run(args: list[str]) -> int` (L40-51)
- @brief Launch Codex CLI in YOLO mode after executable validation.
- @details Delegates to the shared YOLO runner executing `codex --yolo` plus pass-through args through blocking subprocess run with inherited stdio. Time complexity O(n) over forwarded argument count.
- @param args {list[str]} Additional CLI args forwarded to Codex.
- @return {int} Child process return code.
- @satisfies REQ-014, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`DESCRIPTION`|var|pub|20||
|`SPEC`|var|pub|24||
|`print_help`|fn|pub|27-39|def print_help(version: str) -> None|
|`run`|fn|pub|40-51|def run(args: list[str]) -> int|


---

# copilot.py | Python | 51L | 4 symbols | 1 imports | 10 comments
> Path: `src/shell_scripts/commands/copilot.py`

## Imports
```
from shell_scripts.commands._yolo_common import (
```

## Definitions

- var `DESCRIPTION = "Launch GitHub Copilot CLI in the project context."` (L20)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
- var `SPEC = get_yolo_spec("copilot")` (L24)
- @brief Declarative YOLO CLI record bound to the `copilot` command token.
- @satisfies DES-030, REQ-015, REQ-093
### fn `def print_help(version: str) -> None` (L27-40)
- @brief Print command-specific help for `copilot`.
- @details Delegates to the shared YOLO help renderer, which emits the executed option documentation, the accepted `--allow-all` alternative, and the alphabetical YOLO CLI registry. Time complexity O(n) over registered YOLO CLI record count.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-086, REQ-092, REQ-093

### fn `def run(args: list[str]) -> int` (L41-52)
- @brief Launch Copilot CLI in YOLO mode after executable validation.
- @details Delegates to the shared YOLO runner executing `copilot --yolo` plus pass-through args through blocking subprocess run with inherited stdio. Time complexity O(n) over forwarded argument count.
- @param args {list[str]} Additional CLI args forwarded to Copilot.
- @return {int} Child process return code.
- @satisfies REQ-015, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`DESCRIPTION`|var|pub|20||
|`SPEC`|var|pub|24||
|`print_help`|fn|pub|27-40|def print_help(version: str) -> None|
|`run`|fn|pub|41-52|def run(args: list[str]) -> int|


---

# dicom2jpg.py | Python | 98L | 7 symbols | 4 imports | 3 comments
> Path: `src/shell_scripts/commands/dicom2jpg.py`

## Imports
```
import os
import subprocess
import shutil
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L15)
- var `DESCRIPTION = "Convert DICOM images to JPEG using PixelMed."` (L16)
- var `JAVA_WRAPPERS = "/usr/lib/java-wrappers/java-wrappers.sh"` (L18)
### fn `def print_help(version)` (L21-29)

### fn `def _find_java()` `priv` (L30-36)

### fn `def _find_jars(*jar_names)` `priv` (L37-48)

### fn `def run(args)` (L49-99)
- @brief Run PixelMed converter after executable validation.
- @details Validates Java runtime availability and command executability for the selected Java binary before invoking conversion class.
- @param args {list[str]} Expected `[input_dicom, output_jpeg]` arguments.
- @return {int} Subprocess return code.
- @satisfies REQ-026, REQ-055, REQ-056

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|15||
|`DESCRIPTION`|var|pub|16||
|`JAVA_WRAPPERS`|var|pub|18||
|`print_help`|fn|pub|21-29|def print_help(version)|
|`_find_java`|fn|priv|30-36|def _find_java()|
|`_find_jars`|fn|priv|37-48|def _find_jars(*jar_names)|
|`run`|fn|pub|49-99|def run(args)|


---

# dicomviewer.py | Python | 83L | 7 symbols | 4 imports | 3 comments
> Path: `src/shell_scripts/commands/dicomviewer.py`

## Imports
```
import os
import subprocess
import shutil
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L15)
- var `DESCRIPTION = "Launch PixelMed DICOM image viewer."` (L16)
- var `JAVA_WRAPPERS = "/usr/lib/java-wrappers/java-wrappers.sh"` (L18)
### fn `def print_help(version)` (L21-28)

### fn `def _find_java()` `priv` (L29-35)

### fn `def _find_jars(*jar_names)` `priv` (L36-47)

### fn `def run(args)` (L48-84)
- @brief Run PixelMed DICOM viewer after executable validation.
- @details Validates Java runtime availability and command executability for the selected Java binary before invoking the viewer class.
- @param args {list[str]} DICOM file arguments forwarded to PixelMed viewer.
- @return {int} Subprocess return code.
- @satisfies REQ-025, REQ-055, REQ-056

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|15||
|`DESCRIPTION`|var|pub|16||
|`JAVA_WRAPPERS`|var|pub|18||
|`print_help`|fn|pub|21-28|def print_help(version)|
|`_find_java`|fn|priv|29-35|def _find_java()|
|`_find_jars`|fn|priv|36-47|def _find_jars(*jar_names)|
|`run`|fn|pub|48-84|def run(args)|


---

# diff_cmd.py | Python | 50L | 4 symbols | 3 imports | 4 comments
> Path: `src/shell_scripts/commands/diff_cmd.py`

## Imports
```
import sys
from shell_scripts.config import get_dispatch_profile
from shell_scripts.commands._dc_common import dispatch
```

## Definitions

- var `PROGRAM = "shellscripts"` (L14)
- var `DESCRIPTION = "File differ dispatcher by MIME type."` (L15)
### fn `def print_help(version)` (L18-34)
- @brief Render command help for `diff`.
- @details Prints usage, required file argument semantics, and argument forwarding contract for the selected external diff executable.
- @param version {str} Version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L35-51)
- @brief Execute MIME-routed diff dispatch.
- @details Validates that a file argument exists; on missing argument prints error plus help and returns status code `2`; otherwise resolves runtime dispatch profile and delegates by file category through shared `_dc_common`.
- @param args {list[str]} CLI args where `args[0]` is file path.
- @return {int} Return code `2` on missing file; otherwise delegated dispatch result.
- @satisfies REQ-023, REQ-024

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|14||
|`DESCRIPTION`|var|pub|15||
|`print_help`|fn|pub|18-34|def print_help(version)|
|`run`|fn|pub|35-51|def run(args)|


---

# doxygen_cmd.py | Python | 159L | 7 symbols | 8 imports | 2 comments
> Path: `src/shell_scripts/commands/doxygen_cmd.py`

## Imports
```
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from shell_scripts.utils import require_project_root, require_commands, print_error
from shell_scripts.utils import command_exists
```

## Definitions

- var `PROGRAM = "shellscripts"` (L11)
- var `DESCRIPTION = "Generate Doxygen documentation (HTML, PDF, Markdown)."` (L12)
### fn `def print_help(version)` (L15-24)

### fn `def _supports_generate_markdown()` `priv` (L25-38)

### fn `def _write_doxyfile(path, project_root, src_dir, doxygen_dir, has_md)` `priv` (L39-40)

### fn `def _generate_markdown_fallback(xml_dir, markdown_dir)` `priv` (L76-98)

### fn `def run(args)` (L99-160)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|11||
|`DESCRIPTION`|var|pub|12||
|`print_help`|fn|pub|15-24|def print_help(version)|
|`_supports_generate_markdown`|fn|priv|25-38|def _supports_generate_markdown()|
|`_write_doxyfile`|fn|priv|39-40|def _write_doxyfile(path, project_root, src_dir, doxygen_...|
|`_generate_markdown_fallback`|fn|priv|76-98|def _generate_markdown_fallback(xml_dir, markdown_dir)|
|`run`|fn|pub|99-160|def run(args)|


---

# edit_cmd.py | Python | 50L | 4 symbols | 3 imports | 4 comments
> Path: `src/shell_scripts/commands/edit_cmd.py`

## Imports
```
import sys
from shell_scripts.config import get_dispatch_profile
from shell_scripts.commands._dc_common import dispatch
```

## Definitions

- var `PROGRAM = "shellscripts"` (L14)
- var `DESCRIPTION = "File editor dispatcher by MIME type."` (L15)
### fn `def print_help(version)` (L18-34)
- @brief Render command help for `edit`.
- @details Prints usage, required file argument semantics, and argument forwarding contract for the selected external editor executable.
- @param version {str} Version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L35-51)
- @brief Execute MIME-routed edit dispatch.
- @details Validates that a file argument exists; on missing argument prints error plus help and returns status code `2`; otherwise resolves runtime dispatch profile and delegates by file category through shared `_dc_common`.
- @param args {list[str]} CLI args where `args[0]` is file path.
- @return {int} Return code `2` on missing file; otherwise delegated dispatch result.
- @satisfies REQ-023, REQ-024

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|14||
|`DESCRIPTION`|var|pub|15||
|`print_help`|fn|pub|18-34|def print_help(version)|
|`run`|fn|pub|35-51|def run(args)|


---

# meld_highlight_theme.py | Python | 389L | 15 symbols | 11 imports | 48 comments
> Path: `src/shell_scripts/commands/meld_highlight_theme.py`

## Imports
```
import argparse
import copy
from datetime import datetime
import importlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
```

## Definitions

- var `PROGRAM = "shellscripts"` (L25)
- var `DESCRIPTION = "Create Meld Highlight color schemes for Meld and GtkSourceView."` (L26)
- var `TARGET_SUBDIRS = (` (L33)
- @brief Home-relative style-directory suffixes receiving generated schemes.
- @details Ordered user-directory list covering Meld, GtkSourceView 3/4/5,
and the Flatpak Meld data tree; every entry receives each generated file.
- @satisfies REQ-166
- var `SOURCE_SYSTEM_SUBDIRS = (` (L49)
- @brief Absolute system style directories scanned for candidate schemes.
- @details Read-only discovery roots resolved before the user directories so
that same-id user schemes override system schemes during discovery.
- @satisfies REQ-157
- var `TARGET_DIRS = [Path.home() / part for part in TARGET_SUBDIRS]` (L62)
- @brief Resolved writable style directories under the user home.
- @details Computed at import from `TARGET_SUBDIRS` and `Path.home()` exactly
like the legacy script; tests MAY monkeypatch this module attribute to
redirect generation into fixture directories.
- @satisfies REQ-166
- var `SOURCE_DIRS = [Path(part) for part in SOURCE_SYSTEM_SUBDIRS] + TARGET_DIRS` (L70)
- @brief Resolved scheme discovery directories (system first, user last).
- @details System directories precede user directories so later user entries
overwrite same-id schemes in the discovery map, mirroring the legacy
script; tests MAY monkeypatch this module attribute.
- @satisfies REQ-157
- var `RED_BG = "#cc0000"` (L76)
- @brief Background color applied to the injected `meld:inline` style.
- @details Fixed red highlight palette token shared by every generated scheme.
- @satisfies REQ-160
- var `WHITE_FG = "#ffffff"` (L82)
- @brief Foreground color applied to the injected `meld:inline` style.
- @details Fixed white highlight palette token shared by every generated scheme.
- @satisfies REQ-160
### fn `def _build_parser()` `priv` (L104-131)
- @brief ASCII scheme-id validation pattern `[\w.-]+` with full match semantics.
- @brief Build the `meld-highlight-theme` argument parser.
- @details Rejects scheme files whose `id` attribute contains whitespace,
separators, or non-ASCII characters.
- @details Registers the mutually exclusive `--dark`/`--light` palette selectors plus `--only-meld-base`; `parse_args` errors terminate with exit code `2`, matching the legacy script `argparse` behavior.
- @return {argparse.ArgumentParser} Configured parser instance.
- @satisfies REQ-157
- @satisfies REQ-156

### fn `def all_schemes()` (L132-162)
- @brief Discover candidate style schemes across all source directories.
- @details Iterates `SOURCE_DIRS` in order, parses each `*.xml` file sorted by name, silently skips unreadable or non-`style-scheme` roots, validates the `id` attribute against `_SCHEME_ID_PATTERN`, resolves the display name from `_name`, `name`, or the id, and lets later directories override earlier same-id entries. Time complexity O(N log N) per directory over the XML file inventory.
- @return {dict[str, tuple[str, xml.etree.ElementTree.Element]]} Mapping scheme id to `(display_name, scheme_root_element)`.
- @satisfies REQ-157

### fn `def setting(schema, key)` (L163-183)
- @brief Read one GNOME `gsettings` value.
- @details Runs `gsettings get <schema> <key>` with captured output and a 4-second timeout, returning the stripped stdout on success and `None` on failure, timeout, or missing executable.
- @param schema {str} GSettings schema identifier (e.g. `org.gnome.meld`).
- @param key {str} GSettings key name inside the schema.
- @return {str|None} Stripped value text on success; `None` otherwise.
- @satisfies REQ-163

### fn `def using_dark_theme()` (L184-222)
- @brief Auto-detect whether the desktop currently uses a dark theme.
- @details Reproduces the legacy detection chain: first reads the Meld `prefer-dark-theme` preference and, when a display server is attached, queries the GTK 3 default settings and looks up `theme_bg_color` on a probe `Gtk.TextView`, returning darkness when the summed RGB is below `1.0`; otherwise falls back to the GNOME `color-scheme` (`prefer-dark` substring) and case-insensitive `dark` substrings in the GTK theme name or `GTK_THEME` environment variable. All failures degrade to the fallback path.
- @return {bool} `True` when the detected desktop palette is dark.
- @satisfies REQ-163

### fn `def build_xml(sid, name, dark_palette=None)` (L223-286)
- @brief Build the serialized `<id>-highlight` XML payload for one scheme.
- @details Creates a `style-scheme` root with `id="<sid>-highlight"`, `_name="<name> Highlight"`, `parent-scheme="<sid>"`, `version="1.0"`, an `author` element `Custom Script`, and a `_description` element `<name> con evidenziazione inline rossa`. When `dark_palette` is supplied, deep-copies every direct `meld:*` and `map-overlay` style except `meld:inline`, aborts on any missing required Meld style, and inserts deep copies of every palette `<color>` whose name is referenced by an inherited style attribute at child index `2`. Finally appends the fixed `meld:inline` style, indents the tree with two spaces, serializes with the UTF-8 XML declaration, and validates that inheritance is preserved and no `text` style leaked into the output.
- @param sid {str} Source scheme identifier; MUST match `_SCHEME_ID_PATTERN`.
- @param name {str} Source scheme display name.
- @param dark_palette {Element|None} `meld-dark` root element whose styles are inherited; `None` produces the plain light payload.
- @return {bytes} Complete XML document bytes terminated by a newline.
- @throws {ValueError} When the dark palette lacks a required Meld style or the serialized payload loses `parent-scheme` inheritance or contains a `text` style.
- @satisfies REQ-159, REQ-160, REQ-161, REQ-162, REQ-165

### fn `def print_help(version)` (L287-309)
- @brief Print command-specific help text.
- @details Renders usage line, option list, and a behavioral summary in English, following the shared command help layout.
- @param version {str} Current CLI version token rendered in the usage line.
- @return {None} Writes to stdout.
- @satisfies PRJ-002, REQ-156

### fn `def run(args)` (L310-390)
- @brief Execute the highlight-theme generation pipeline.
- @details Parses palette arguments, discovers schemes, resolves the dark flag from explicit selectors or desktop auto-detection, validates the `meld-base`/`meld-dark` preconditions, builds and plans one payload per selected scheme, prints the English report block, then writes every planned destination with timestamped backup and same-directory atomic replace before printing the English summary. Exit code `2` is raised via `parser.error` on invalid arguments or missing precondition schemes.
- @param args {list[str]} Command arguments (without the command token).
- @return {int} `0` after a completed generation run.
- @throws {SystemExit} Exit code `2` via `parser.error` when `--dark` and `--light` are combined, `--only-meld-base` finds no `meld-base` scheme, or the dark palette applies while `meld-dark` is missing.
- @throws {ValueError} Propagated from `build_xml` on payload integrity failure.
- @satisfies REQ-156, REQ-157, REQ-158, REQ-159, REQ-160, REQ-161, REQ-162, REQ-163, REQ-164, REQ-165, REQ-166, REQ-167, REQ-168

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|25||
|`DESCRIPTION`|var|pub|26||
|`TARGET_SUBDIRS`|var|pub|33||
|`SOURCE_SYSTEM_SUBDIRS`|var|pub|49||
|`TARGET_DIRS`|var|pub|62||
|`SOURCE_DIRS`|var|pub|70||
|`RED_BG`|var|pub|76||
|`WHITE_FG`|var|pub|82||
|`_build_parser`|fn|priv|104-131|def _build_parser()|
|`all_schemes`|fn|pub|132-162|def all_schemes()|
|`setting`|fn|pub|163-183|def setting(schema, key)|
|`using_dark_theme`|fn|pub|184-222|def using_dark_theme()|
|`build_xml`|fn|pub|223-286|def build_xml(sid, name, dark_palette=None)|
|`print_help`|fn|pub|287-309|def print_help(version)|
|`run`|fn|pub|310-390|def run(args)|


---

# net_cmd.py | Python | 278L | 20 symbols | 3 imports | 54 comments
> Path: `src/shell_scripts/commands/net_cmd.py`

## Imports
```
import re
import subprocess
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L16)
- var `DESCRIPTION = "Print network status and manage VLAN connections."` (L17)
- var `GREEN = "\x1b[1;32m"` (L23)
- @brief ANSI bright-green SGR prefix for status box borders.
- @details Replicates the legacy script color `\e[1;32m`.
- @satisfies REQ-171
- var `BLUE = "\x1b[1;34m"` (L29)
- @brief ANSI bright-blue SGR prefix for the DNS section box.
- @details Replicates the legacy script color `\e[1;34m`.
- @satisfies REQ-171
- var `MAGENTA = "\x1b[1;35m"` (L35)
- @brief ANSI bright-magenta SGR prefix for the routing section box.
- @details Replicates the legacy script color `\e[1;35m`.
- @satisfies REQ-171
- var `LIGHT_GRAY = "\x1b[0;37m"` (L41)
- @brief ANSI light-gray SGR prefix for the journal section box.
- @details Replicates the legacy script color `\e[0;37m`.
- @satisfies REQ-171
- var `WHITE = "\x1b[1;37m"` (L47)
- @brief ANSI bright-white SGR prefix for box titles and usage header.
- @details Replicates the legacy script color `\e[1;37m`.
- @satisfies REQ-171
- var `RESET = "\x1b[0m"` (L53)
- @brief ANSI SGR reset suffix restoring default attributes.
- @details Replicates the legacy script color `\e[0m`.
- @satisfies REQ-171
- var `RED = "\x1b[1;31m"` (L59)
- @brief ANSI bright-red SGR prefix for error lines.
- @details Replicates the legacy script color `\e[1;31m`.
- @satisfies REQ-173
- var `YELLOW = "\x1b[1;33m"` (L65)
- @brief ANSI bright-yellow SGR prefix for deactivation notice lines.
- @details Replicates the legacy script color `\e[1;33m`.
- @satisfies REQ-172
- var `BOX_WIDTH = 70` (L72)
- @brief Fixed inner width in dash glyphs for every section box.
- @details Replicates the legacy script width `70`; title centering is
computed against this value.
- @satisfies REQ-171
- var `JOURNAL_TAIL_LINES = 15` (L78)
- @brief Number of trailing journal lines printed by the status report.
- @details Replicates the legacy `journalctl ... | tail -n 15` behavior.
- @satisfies REQ-171
- var `VLAN_ADDRESS_AFTER_LINES = 2` (L84)
- @brief Context lines printed after each matching VLAN address line.
- @details Replicates the legacy `grep -E ... -A 2` behavior.
- @satisfies REQ-172
### fn `def print_box(title, color)` (L87-111)
- @brief Print one centered-title ASCII box header.
- @details Replicates the legacy `print_box` layout: a leading blank line, `┌` plus 70 `─` glyphs plus `┐` borders in `color`, a title row with the title wrapped in `WHITE` and padded to `BOX_WIDTH` using the split `padding = (BOX_WIDTH - len(title) - 2) // 2` left and the remainder right, and a closing `└...┘` border row.
- @param title {str} ASCII section title rendered inside the box.
- @param color {str} ANSI SGR prefix applied to the border glyphs.
- @return {None} Writes to stdout.
- @satisfies REQ-171

### fn `def cmd_status()` (L112-153)
- @brief Print the full network status report.
- @details Emits boxed English section headers followed by, in order: `nmcli device status`, `nmcli -f NAME,TYPE,AUTOCONNECT,DEVICE connection show`, `resolvectl status`, `ip route`, and the last `JOURNAL_TAIL_LINES` lines of `journalctl -b -u networking.service no-pager` captured output. Each external tool is validated immediately before its section and a missing tool terminates with exit code `1`.
- @return {int} `0` after printing every section; `1` when a required executable is unavailable.
- @throws {SystemExit} Exit code `1` via `require_commands` when a required executable is not executable.
- @satisfies REQ-171, REQ-056

### fn `def _print_vlan_addresses(vlan_id)` `priv` (L154-175)
- @brief Print current addresses of one VLAN, mirroring `grep -A 2`.
- @details Runs `ip addr show` with captured stdout, selects every line matching `vlan<vlan_id>` or `enp.*\.<vlan_id>`, and prints each match plus the following `VLAN_ADDRESS_AFTER_LINES` context lines without duplicating overlapping context windows.
- @param vlan_id {str} Numeric VLAN identifier used in match patterns.
- @return {None} Writes matching address blocks to stdout.
- @satisfies REQ-172

### fn `def cmd_vlan(vlan_id, action)` (L176-217)
- @brief Activate or deactivate one VLAN connection.
- @details Rejects missing parameters and unknown actions with the English usage text and exit code `1`; otherwise runs `sudo nmcli connection up|down vlan<vlan_id>` with inherited stdio and blocking wait, and after a successful activation prints the current VLAN address blocks. The return code propagates the `sudo nmcli` result.
- @param vlan_id {str|None} VLAN identifier token (e.g. `50`).
- @param action {str|None} Requested action; only `up` and `down` are valid.
- @return {int} `0` on success; the `sudo nmcli` return code on activation or deactivation failure; `1` on parameter or action validation failure.
- @satisfies REQ-172, REQ-173

### fn `def print_usage()` (L218-232)
- @brief Print the English command usage block.
- @details Renders the bright-white script title, the available-command list, and no return value; callers combine it with return code `1`.
- @return {None} Writes to stdout.
- @satisfies REQ-173

### fn `def print_help(version)` (L233-252)
- @brief Print command-specific help text.
- @details Renders usage line, option list, and subcommand summary in English, following the shared command help layout.
- @param version {str} Current CLI version token rendered in the usage line.
- @return {None} Writes to stdout.
- @satisfies PRJ-002, REQ-171

### fn `def run(args)` (L253-279)
- @brief Route `net` subcommands.
- @details Dispatches `status` to `cmd_status` and `vlan` with two positional arguments to `cmd_vlan`; any missing, unknown, or malformed subcommand prints the English usage block and returns exit code `1`.
- @param args {list[str]} Command arguments (without the command token).
- @return {int} `0` on successful subcommand completion; `1` on usage errors or propagated VLAN command failure.
- @satisfies REQ-171, REQ-172, REQ-173

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|16||
|`DESCRIPTION`|var|pub|17||
|`GREEN`|var|pub|23||
|`BLUE`|var|pub|29||
|`MAGENTA`|var|pub|35||
|`LIGHT_GRAY`|var|pub|41||
|`WHITE`|var|pub|47||
|`RESET`|var|pub|53||
|`RED`|var|pub|59||
|`YELLOW`|var|pub|65||
|`BOX_WIDTH`|var|pub|72||
|`JOURNAL_TAIL_LINES`|var|pub|78||
|`VLAN_ADDRESS_AFTER_LINES`|var|pub|84||
|`print_box`|fn|pub|87-111|def print_box(title, color)|
|`cmd_status`|fn|pub|112-153|def cmd_status()|
|`_print_vlan_addresses`|fn|priv|154-175|def _print_vlan_addresses(vlan_id)|
|`cmd_vlan`|fn|pub|176-217|def cmd_vlan(vlan_id, action)|
|`print_usage`|fn|pub|218-232|def print_usage()|
|`print_help`|fn|pub|233-252|def print_help(version)|
|`run`|fn|pub|253-279|def run(args)|


---

# npm_bootstrap_trust.py | Python | 378L | 19 symbols | 8 imports | 46 comments
> Path: `src/shell_scripts/commands/npm_bootstrap_trust.py`

## Imports
```
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L23)
- var `DESCRIPTION = "Bootstrap a new npm package and register its GitHub trusted publisher."` (L24)
- var `REGISTRY = "https://registry.npmjs.org/"` (L31)
- @brief Canonical npm registry URL used by every npm invocation.
- @details Passed as `--registry=<value>` so operations never depend on the
ambient npm registry configuration.
- @satisfies REQ-177
- var `MIN_NODE_VERSION = (22, 14, 0)` (L37)
- @brief Minimum supported Node.js version tuple `(22, 14, 0)`.
- @details Versions comparing lower abort the command.
- @satisfies REQ-176
- var `MIN_NPM_VERSION = (11, 15, 0)` (L43)
- @brief Minimum supported npm version tuple `(11, 15, 0)`.
- @details Versions comparing lower abort the command.
- @satisfies REQ-176
- var `NPM_NAME_PATTERN = (` (L51)
- @brief Conservative npm-name validation patterns.
- @details Tuple of two anchored regexes: unscoped `^[a-z0-9][a-z0-9._~-]*$`
and scoped `^@[a-z0-9][a-z0-9._~-]*/[a-z0-9][a-z0-9._~-]*$`; the first
full match accepts the name.
- @satisfies REQ-175
- var `GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$")` (L61)
- @brief Anchored `owner/repo` validation regex
`^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$`.
- @details Repository tokens MUST NOT be URLs or carry extra slashes.
- @satisfies REQ-175
- var `WORKFLOW_FILE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$")` (L68)
- @brief Anchored bare workflow-filename regex
`^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$`.
- @details Rejects paths, directory components, and unsupported extensions.
- @satisfies REQ-175
- var `VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")` (L75)
- @brief Anchored strict `X.Y.Z` semantic-version regex.
- @details Used to parse both `node --version` and `npm --version` output;
malformed values abort the version gate.
- @satisfies REQ-176
### class `class _UsageParser(argparse.ArgumentParser)` : argparse.ArgumentParser `priv` (L78-101)
- @brief `argparse` parser variant preserving the legacy exit code.
- @details Overrides `error` so usage errors print the message plus usage text to stderr and terminate with exit code `1`, matching the legacy script `usage(1)`/`die` semantics instead of the argparse default `2`.
- @satisfies REQ-174
- fn `def error(self, message)` (L87-101)
  - @brief `argparse` parser variant preserving the legacy exit code.
  - @brief Terminate argument parsing with the legacy failure contract.
  - @details Overrides `error` so usage errors print the message plus usage
text to stderr and terminate with exit code `1`, matching the legacy
script `usage(1)`/`die` semantics instead of the argparse default `2`.
  - @details Prints the bare message to stderr, then the usage text, then raises `SystemExit(1)`.
  - @param message {str} Parsing error description.
  - @return {None} Never returns; raises `SystemExit`.
  - @throws {SystemExit} Always exit code `1`.
  - @satisfies REQ-174
  - @satisfies REQ-174

### fn `def _build_parser()` `priv` (L102-128)
- @brief Build the `npm-bootstrap-trust` argument parser.
- @details Registers required `-p/--package`, `-r/--repo`, and `-f/--workflow` options plus the default `-h/--help` action on the `_UsageParser` variant.
- @return {_UsageParser} Configured parser instance.
- @satisfies REQ-174

### fn `def _die(message)` `priv` (L129-143)
- @brief Print an error line and terminate with exit code `1`.
- @details Mirrors the legacy `die` helper using the shared `[ERROR]` stderr renderer.
- @param message {str} Failure description rendered after the `[ERROR]` prefix.
- @return {None} Never returns; raises `SystemExit`.
- @throws {SystemExit} Always exit code `1`.
- @satisfies REQ-174, REQ-175, REQ-176, REQ-177, REQ-178, REQ-179, REQ-180

### fn `def _validate_inputs(package_name, github_repo, workflow_file)` `priv` (L144-172)
- @brief Validate the conservative package, repository, and workflow tokens.
- @details Applies `NPM_NAME_PATTERN` plus the 214-character limit, the `GITHUB_REPO_PATTERN` plus owner length at most 39 and owner not ending with `-`, and `WORKFLOW_FILE_PATTERN`, aborting with the legacy English diagnostics on the first failure.
- @param package_name {str} npm package name token.
- @param github_repo {str} GitHub `owner/repo` token.
- @param workflow_file {str} Bare workflow filename token.
- @return {None} Returns on full validation.
- @throws {SystemExit} Exit code `1` via `_die` on the first invalid token.
- @satisfies REQ-175

### fn `def _parse_version(text)` `priv` (L173-188)
- @brief Parse one strict `X.Y.Z` version string.
- @details Applies `VERSION_PATTERN` after stripping an optional leading `v` and surrounding whitespace.
- @param text {str} Raw version output token.
- @return {tuple[int, int, int]|None} Numeric version tuple, or `None` when the token does not match the strict format.
- @satisfies REQ-176

### fn `def _require_toolchain()` `priv` (L189-220)
- @brief Validate Node.js and npm presence plus minimum versions.
- @details Checks `node` and `npm` executables via `require_commands`, captures `node --version` and `npm --version`, parses both with `_parse_version`, and aborts when either executable reports a version lower than `MIN_NODE_VERSION` or `MIN_NPM_VERSION` respectively or an unparseable value.
- @return {None} Returns when the toolchain satisfies the version gate.
- @throws {SystemExit} Exit code `1` via `require_commands` on missing executables or via `_die` on incompatible versions.
- @satisfies REQ-176, CTN-003, REQ-056

### fn `def _write_placeholder_package(temp_dir, package_name, github_repo)` `priv` (L221-255)
- @brief Write the placeholder `package.json` and `index.js` files.
- @details Creates a version `0.0.0` package declaring the placeholder description, the GitHub repository URL `git+https://github.com/<repo>.git`, the `index.js` file list, and public publishConfig pinned to `REGISTRY`; writes `module.exports = {};` into `index.js`.
- @param temp_dir {str|Path} Existing temporary package directory.
- @param package_name {str} Validated npm package name.
- @param github_repo {str} Validated GitHub `owner/repo` token.
- @return {None} Writes two files into `temp_dir`.
- @throws {OSError} Propagated on filesystem write failure.
- @satisfies REQ-179

### fn `def print_help(version)` (L256-276)
- @brief Print command-specific help text.
- @details Renders usage line, option list, and behavioral summary in English, following the shared command help layout.
- @param version {str} Current CLI version token rendered in the usage line.
- @return {None} Writes to stdout.
- @satisfies PRJ-002, REQ-174

### fn `def run(args)` (L277-379)
- @brief Execute the five-phase npm bootstrap and trust pipeline.
- @details Phase order: `[1/5]` npmjs authentication via `npm whoami`; `[2/5]` package availability via `npm view <package>@* versions --json`, aborting on existing versions or a failure without an `E404` marker; `[3/5]` placeholder package creation in a fresh temporary directory; `[4/5]` publication with dist-tag `bootstrap` and public access; `[5/5]` GitHub trusted-publisher creation via `npm trust github` plus trust-list verification. The temporary directory is removed on every exit path; every failure aborts with exit code `1` and the exact legacy diagnostic semantics.
- @param args {list[str]} Command arguments (without the command token).
- @return {int} `0` after successful publication and trust verification.
- @throws {SystemExit} Exit code `1` on usage errors, invalid inputs, missing or incompatible toolchain, failed authentication, taken or unverifiable package name, failed publication, or failed trust creation/verification.
- @satisfies REQ-174, REQ-175, REQ-176, REQ-177, REQ-178, REQ-179, REQ-180, REQ-181

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|23||
|`DESCRIPTION`|var|pub|24||
|`REGISTRY`|var|pub|31||
|`MIN_NODE_VERSION`|var|pub|37||
|`MIN_NPM_VERSION`|var|pub|43||
|`NPM_NAME_PATTERN`|var|pub|51||
|`GITHUB_REPO_PATTERN`|var|pub|61||
|`WORKFLOW_FILE_PATTERN`|var|pub|68||
|`VERSION_PATTERN`|var|pub|75||
|`_UsageParser`|class|priv|78-101|class _UsageParser(argparse.ArgumentParser)|
|`_UsageParser.error`|fn|pub|87-101|def error(self, message)|
|`_build_parser`|fn|priv|102-128|def _build_parser()|
|`_die`|fn|priv|129-143|def _die(message)|
|`_validate_inputs`|fn|priv|144-172|def _validate_inputs(package_name, github_repo, workflow_...|
|`_parse_version`|fn|priv|173-188|def _parse_version(text)|
|`_require_toolchain`|fn|priv|189-220|def _require_toolchain()|
|`_write_placeholder_package`|fn|priv|221-255|def _write_placeholder_package(temp_dir, package_name, gi...|
|`print_help`|fn|pub|256-276|def print_help(version)|
|`run`|fn|pub|277-379|def run(args)|


---

# opencode.py | Python | 49L | 4 symbols | 1 imports | 10 comments
> Path: `src/shell_scripts/commands/opencode.py`

## Imports
```
from shell_scripts.commands._yolo_common import (
```

## Definitions

- var `DESCRIPTION = "Launch OpenCode CLI in the project context."` (L19)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
- var `SPEC = get_yolo_spec("opencode")` (L23)
- @brief Declarative YOLO CLI record bound to the `opencode` command token.
- @satisfies DES-030, REQ-018
### fn `def print_help(version: str) -> None` (L26-38)
- @brief Print command-specific help for `opencode`.
- @details Delegates to the shared YOLO help renderer, which emits the executed option documentation and the alphabetical YOLO CLI registry. Time complexity O(n) over registered YOLO CLI record count.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-086, REQ-092

### fn `def run(args: list[str]) -> int` (L39-50)
- @brief Launch OpenCode CLI in auto-approval mode after validation.
- @details Delegates to the shared YOLO runner executing `opencode --auto` plus pass-through args through blocking subprocess run with inherited stdio. Time complexity O(n) over forwarded argument count.
- @param args {list[str]} Additional CLI args forwarded to OpenCode.
- @return {int} Child process return code.
- @satisfies REQ-018, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`DESCRIPTION`|var|pub|19||
|`SPEC`|var|pub|23||
|`print_help`|fn|pub|26-38|def print_help(version: str) -> None|
|`run`|fn|pub|39-50|def run(args: list[str]) -> int|


---

# pdf_crop.py | Python | 520L | 27 symbols | 7 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_crop.py`

## Imports
```
import os
import sys
import re
import subprocess
import time
from typing import NoReturn
from shell_scripts.utils import (
```

## Definitions

- var `PROGRAM = "shellscripts"` (L23)
- var `DESCRIPTION = "Crop PDF pages using Ghostscript with auto or manual bounding box."` (L24)
- var `LABEL_WIDTH = 19` (L26)
- var `TERM_COLS = 80` (L27)
### fn `def _init_ui()` `priv` (L30-38)

- var `TERM_COLS = os.get_terminal_size().columns` (L33)
- var `TERM_COLS = 80` (L35)
- var `TERM_COLS = max(60, min(120, TERM_COLS))` (L36)
### fn `def _use_unicode()` `priv` (L39-45)

### fn `def _icons()` `priv` (L46-65)

### fn `def print_help(version)` (L66-78)

### fn `def _fmt(n)` `priv` (L79-82)

### fn `def _fmt_quad(a, b, cc, d)` `priv` (L83-86)

### fn `def _fmt_size(w, h)` `priv` (L87-90)

### fn `def _fmt_bbox_line(left, bottom, right, top)` `priv` (L91-94)

### fn `def _hr(char)` `priv` (L95-99)

### fn `def _section(title)` `priv` (L100-106)

### fn `def _kv(key, value)` `priv` (L107-115)

### fn `def _die(msg) -> NoReturn` `priv` (L116-120)

### fn `def _warn(msg)` `priv` (L121-125)

### fn `def _parse_page_range(spec, max_pages, opt_name)` `priv` (L126-165)

### fn `def _get_page_count(pdf)` `priv` (L166-173)

### fn `def _get_mediabox(pdf, page=1)` `priv` (L174-186)

### fn `def _compute_auto_bbox(pdf, first_page, last_page)` `priv` (L187-230)

### fn `def _render_progress(current, total, label)` `priv` (L231-270)

### fn `def _convert_pdf_with_progress(input_f, output_f, first, last, cw, ch, cl, cb, total)` `priv` (L271-313)

### fn `def run(args)` (L314-513)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|23||
|`DESCRIPTION`|var|pub|24||
|`LABEL_WIDTH`|var|pub|26||
|`TERM_COLS`|var|pub|27||
|`_init_ui`|fn|priv|30-38|def _init_ui()|
|`TERM_COLS`|var|pub|33||
|`TERM_COLS`|var|pub|35||
|`TERM_COLS`|var|pub|36||
|`_use_unicode`|fn|priv|39-45|def _use_unicode()|
|`_icons`|fn|priv|46-65|def _icons()|
|`print_help`|fn|pub|66-78|def print_help(version)|
|`_fmt`|fn|priv|79-82|def _fmt(n)|
|`_fmt_quad`|fn|priv|83-86|def _fmt_quad(a, b, cc, d)|
|`_fmt_size`|fn|priv|87-90|def _fmt_size(w, h)|
|`_fmt_bbox_line`|fn|priv|91-94|def _fmt_bbox_line(left, bottom, right, top)|
|`_hr`|fn|priv|95-99|def _hr(char)|
|`_section`|fn|priv|100-106|def _section(title)|
|`_kv`|fn|priv|107-115|def _kv(key, value)|
|`_die`|fn|priv|116-120|def _die(msg) -> NoReturn|
|`_warn`|fn|priv|121-125|def _warn(msg)|
|`_parse_page_range`|fn|priv|126-165|def _parse_page_range(spec, max_pages, opt_name)|
|`_get_page_count`|fn|priv|166-173|def _get_page_count(pdf)|
|`_get_mediabox`|fn|priv|174-186|def _get_mediabox(pdf, page=1)|
|`_compute_auto_bbox`|fn|priv|187-230|def _compute_auto_bbox(pdf, first_page, last_page)|
|`_render_progress`|fn|priv|231-270|def _render_progress(current, total, label)|
|`_convert_pdf_with_progress`|fn|priv|271-313|def _convert_pdf_with_progress(input_f, output_f, first, ...|
|`run`|fn|pub|314-513|def run(args)|


---

# pdf_merge.py | Python | 180L | 6 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_merge.py`

## Imports
```
import os
import subprocess
import tempfile
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Merge multiple PDF files preserving table of contents."` (L9)
### fn `def print_help(version)` (L12-22)

### fn `def _parse_bookmarks(dump_file)` `priv` (L23-43)

### fn `def _get_num_pages(dump_file)` `priv` (L44-51)

### fn `def run(args)` (L52-181)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-22|def print_help(version)|
|`_parse_bookmarks`|fn|priv|23-43|def _parse_bookmarks(dump_file)|
|`_get_num_pages`|fn|priv|44-51|def _get_num_pages(dump_file)|
|`run`|fn|pub|52-181|def run(args)|


---

# pdf_split_by_format.py | Python | 286L | 10 symbols | 7 imports | 3 comments
> Path: `src/shell_scripts/commands/pdf_split_by_format.py`

## Imports
```
import errno
import os
import re
import shutil
import subprocess
import tempfile
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L11)
- var `DESCRIPTION = "Split PDF into parts by page format changes."` (L12)
### fn `def print_help(version)` (L15-24)

### fn `def _get_page_formats(pdf, total_pages)` `priv` (L25-39)

### fn `def _get_total_pages(pdf)` `priv` (L40-52)

### fn `def _has_toc(pdf)` `priv` (L53-71)

### fn `def _extract_toc_for_range(data_file, start, end)` `priv` (L72-106)

### fn `def _promote_temp_output(temp_output, output_file)` `priv` (L107-130)
- @brief Promote one pdftk-produced temporary artifact onto the final output path.
- @details Attempts same-device atomic replacement via `os.replace`. On `OSError` with `errno.EXDEV` (temporary directory and output directory located on different filesystems), falls back to `shutil.move`, which copies the artifact content and removes the temporary source. All other `OSError` values propagate unchanged to preserve pre-existing failure semantics. Time complexity O(1) for same-device renames, O(n) over file size for the cross-device copy fallback.
- @param temp_output {str} Temporary artifact path produced by the external tool chain.
- @param output_file {str} Final chunk path that must receive the artifact content.
- @return {None} Applies destination filesystem mutation.
- @throws {OSError} Propagated for non-EXDEV replacement failures.
- @satisfies REQ-031, REQ-032

### fn `def _apply_toc(output_file, toc_content)` `priv` (L131-180)
- @brief Reapply in-range TOC data to one generated chunk file.
- @details Writes `toc_content` into a temporary `.info` payload, prepares temporary PDF artifacts, strips object streams from `output_file` via `qpdf`, rebuilds the chunk with TOC metadata via `pdftk update_info`, and promotes the artifact onto `output_file` through `_promote_temp_output` so a temporary directory on a different filesystem cannot silently drop the chunk TOC. Tool-chain failures are contained without aborting the split loop. Time complexity O(m) over TOC content size plus external process latency.
- @param output_file {str} Generated chunk path receiving the TOC metadata.
- @param toc_content {str} Range-filtered pdftk dump-data bookmark payload.
- @return {None} Mutates `output_file` content on success.
- @throws {OSError} Propagated when temporary payload creation, unlink, or non-EXDEV promotion fails.
- @satisfies REQ-032

### fn `def run(args)` (L181-287)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|11||
|`DESCRIPTION`|var|pub|12||
|`print_help`|fn|pub|15-24|def print_help(version)|
|`_get_page_formats`|fn|priv|25-39|def _get_page_formats(pdf, total_pages)|
|`_get_total_pages`|fn|priv|40-52|def _get_total_pages(pdf)|
|`_has_toc`|fn|priv|53-71|def _has_toc(pdf)|
|`_extract_toc_for_range`|fn|priv|72-106|def _extract_toc_for_range(data_file, start, end)|
|`_promote_temp_output`|fn|priv|107-130|def _promote_temp_output(temp_output, output_file)|
|`_apply_toc`|fn|priv|131-180|def _apply_toc(output_file, toc_content)|
|`run`|fn|pub|181-287|def run(args)|


---

# pdf_split_by_toc.py | Python | 240L | 9 symbols | 7 imports | 3 comments
> Path: `src/shell_scripts/commands/pdf_split_by_toc.py`

## Imports
```
import errno
import os
import re
import shutil
import subprocess
import tempfile
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L11)
- var `DESCRIPTION = "Split PDF into chapters by TOC level-1 entries."` (L12)
### fn `def print_help(version)` (L15-22)

### fn `def _parse_level1_toc(dump_content)` `priv` (L23-41)

### fn `def _extract_toc_for_range(dump_content, start, end)` `priv` (L42-74)

### fn `def _sanitize_title(title)` `priv` (L75-80)

### fn `def _promote_temp_output(temp_output, output_file)` `priv` (L81-104)
- @brief Promote one pdftk-produced temporary artifact onto the final output path.
- @details Attempts same-device atomic replacement via `os.replace`. On `OSError` with `errno.EXDEV` (temporary directory and output directory located on different filesystems), falls back to `shutil.move`, which copies the artifact content and removes the temporary source. All other `OSError` values propagate unchanged to preserve pre-existing failure semantics. Time complexity O(1) for same-device renames, O(n) over file size for the cross-device copy fallback.
- @param temp_output {str} Temporary artifact path produced by the external tool chain.
- @param output_file {str} Final chunk path that must receive the artifact content.
- @return {None} Applies destination filesystem mutation.
- @throws {OSError} Propagated for non-EXDEV replacement failures.
- @satisfies REQ-031, REQ-032

### fn `def _apply_toc_to_file(output_file, toc_content)` `priv` (L105-151)
- @brief Reapply rebased TOC data to one generated chunk file.
- @details Writes `toc_content` into a temporary `.info` payload, strips object streams from `output_file` via `qpdf`, rebuilds the chunk with TOC metadata via `pdftk update_info`, and promotes the artifact onto `output_file` through `_promote_temp_output` so a temporary directory on a different filesystem cannot crash chunk generation. Emits a warning and keeps the original chunk when the tool chain fails. Time complexity O(m) over TOC content size plus external process latency.
- @param output_file {str} Generated chunk path receiving the TOC metadata.
- @param toc_content {str} Rebased pdftk dump-data bookmark payload.
- @return {None} Mutates `output_file` content on success.
- @throws {OSError} Propagated when temporary payload creation, unlink, or non-EXDEV promotion fails.
- @satisfies REQ-031

### fn `def run(args)` (L152-241)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|11||
|`DESCRIPTION`|var|pub|12||
|`print_help`|fn|pub|15-22|def print_help(version)|
|`_parse_level1_toc`|fn|priv|23-41|def _parse_level1_toc(dump_content)|
|`_extract_toc_for_range`|fn|priv|42-74|def _extract_toc_for_range(dump_content, start, end)|
|`_sanitize_title`|fn|priv|75-80|def _sanitize_title(title)|
|`_promote_temp_output`|fn|priv|81-104|def _promote_temp_output(temp_output, output_file)|
|`_apply_toc_to_file`|fn|priv|105-151|def _apply_toc_to_file(output_file, toc_content)|
|`run`|fn|pub|152-241|def run(args)|


---

# pdf_tiler_090.py | Python | 61L | 4 symbols | 3 imports | 2 comments
> Path: `src/shell_scripts/commands/pdf_tiler_090.py`

## Imports
```
import subprocess
from pathlib import Path
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Tile PDF to A4 pages at 90% scale using plakativ."` (L8)
### fn `def print_help(version)` (L11-20)

### fn `def run(args)` (L21-62)
- @brief Execute `pdf-tiler-090` command with blocking subprocess launch.
- @details Validates input argument and file presence, builds `plakativ` command vector with fixed A4/0.90 parameters, then executes it via `subprocess.run` while inheriting stdio streams.
- @param args {list[str]} Command arguments excluding command token.
- @return {int} `1` on validation failure; child process return code otherwise.
- @satisfies REQ-029, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-20|def print_help(version)|
|`run`|fn|pub|21-62|def run(args)|


---

# pdf_tiler_100.py | Python | 61L | 4 symbols | 3 imports | 2 comments
> Path: `src/shell_scripts/commands/pdf_tiler_100.py`

## Imports
```
import subprocess
from pathlib import Path
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Tile PDF to A4 pages at original A1 size using plakativ."` (L8)
### fn `def print_help(version)` (L11-20)

### fn `def run(args)` (L21-62)
- @brief Execute `pdf-tiler-100` command with blocking subprocess launch.
- @details Validates input argument and file presence, builds `plakativ` command vector with fixed A1 source size and A4 tiling parameters, then executes it via `subprocess.run` while inheriting stdio streams.
- @param args {list[str]} Command arguments excluding command token.
- @return {int} `1` on validation failure; child process return code otherwise.
- @satisfies REQ-029, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-20|def print_help(version)|
|`run`|fn|pub|21-62|def run(args)|


---

# pdf_toc_clean.py | Python | 175L | 8 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_toc_clean.py`

## Imports
```
import os
import subprocess
import tempfile
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Remove out-of-range TOC entries from PDF files."` (L9)
### fn `def print_help(version)` (L12-22)

### fn `def _filter_bookmarks(dump_content, max_pages)` `priv` (L23-48)

### fn `def _get_num_pages(dump_content)` `priv` (L49-55)

### fn `def _has_out_of_range(dump_content, max_pages)` `priv` (L56-73)

### fn `def _clean_one(input_pdf)` `priv` (L74-161)

### fn `def run(args)` (L162-176)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-22|def print_help(version)|
|`_filter_bookmarks`|fn|priv|23-48|def _filter_bookmarks(dump_content, max_pages)|
|`_get_num_pages`|fn|priv|49-55|def _get_num_pages(dump_content)|
|`_has_out_of_range`|fn|priv|56-73|def _has_out_of_range(dump_content, max_pages)|
|`_clean_one`|fn|priv|74-161|def _clean_one(input_pdf)|
|`run`|fn|pub|162-176|def run(args)|


---

# tests_cmd.py | Python | 87L | 4 symbols | 4 imports | 3 comments
> Path: `src/shell_scripts/commands/tests_cmd.py`

## Imports
```
import os
import sys
import subprocess
from shell_scripts.utils import (
```

## Definitions

- var `PROGRAM = "shellscripts"` (L20)
- var `DESCRIPTION = "Run pytest test suite in a Python virtual environment."` (L21)
### fn `def print_help(version)` (L24-31)

### fn `def run(args)` (L32-88)
- @brief Execute managed pytest workflow with executable pre-checks.
- @details Validates `sys.executable` and flow-conditional executables (`pip`, `playwright`, `.venv/bin/python3`) before each subprocess invocation.
- @param args {list[str]} Additional arguments forwarded to pytest.
- @return {int} Subprocess return code from pytest execution.
- @satisfies REQ-036, REQ-037, REQ-055, REQ-056

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|20||
|`DESCRIPTION`|var|pub|21||
|`print_help`|fn|pub|24-31|def print_help(version)|
|`run`|fn|pub|32-88|def run(args)|


---

# ubuntu_dark_theme.py | Python | 64L | 4 symbols | 3 imports | 3 comments
> Path: `src/shell_scripts/commands/ubuntu_dark_theme.py`

## Imports
```
import subprocess
from shell_scripts.utils import print_info, command_exists, print_error, require_commands
import os
```

## Definitions

- var `PROGRAM = "shellscripts"` (L12)
- var `DESCRIPTION = "Apply GNOME and Qt dark theme settings."` (L13)
### fn `def print_help(version)` (L16-25)

### fn `def run(args)` (L26-65)
- @brief Apply dark-theme settings with conditional executable checks.
- @details For each available theme tool (`gsettings`, `gtk-chtheme`, `qt5ct`, `qt6ct`), validates command executability before subprocess invocation.
- @param args {list[str]} Unused command arguments.
- @return {int} `0` on completion.
- @satisfies REQ-022, REQ-055, REQ-056

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|12||
|`DESCRIPTION`|var|pub|13||
|`print_help`|fn|pub|16-25|def print_help(version)|
|`run`|fn|pub|26-65|def run(args)|


---

# venv_cmd.py | Python | 82L | 4 symbols | 5 imports | 3 comments
> Path: `src/shell_scripts/commands/venv_cmd.py`

## Imports
```
import os
import sys
import shutil
import subprocess
from shell_scripts.utils import (
```

## Definitions

- var `PROGRAM = "shellscripts"` (L21)
- var `DESCRIPTION = "Create or recreate Python virtual environment with requirements."` (L22)
### fn `def print_help(version)` (L25-32)

### fn `def run(args)` (L33-83)
- @brief Recreate virtual environment with executable pre-checks.
- @details Validates `sys.executable` and flow-conditional `pip` executable before corresponding subprocess invocations.
- @param args {list[str]} Command arguments (`--force` accepted).
- @return {int} `0` on successful execution.
- @satisfies REQ-038, REQ-055, REQ-056

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|21||
|`DESCRIPTION`|var|pub|22||
|`print_help`|fn|pub|25-32|def print_help(version)|
|`run`|fn|pub|33-83|def run(args)|


---

# video2h264.py | Python | 89L | 4 symbols | 3 imports | 10 comments
> Path: `src/shell_scripts/commands/video2h264.py`

## Imports
```
import subprocess
from pathlib import Path
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L18)
- @brief CLI program identifier used in usage text.
- @satisfies DES-008
- var `DESCRIPTION = "Convert one video to H.264 MP4 via ffmpeg."` (L22)
- @brief Command description exposed in global help index.
- @satisfies PRJ-002, DES-008, REQ-057
### fn `def print_help(version)` (L25-43)
- @brief Print command usage for `video2h264`.
- @details Emits deterministic help text describing required positional input and output naming semantics.
- @param version {str} CLI version string for usage suffix.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-057

### fn `def run(args)` (L44-90)
- @brief Execute H.264 transcode command with fixed FFmpeg parameters.
- @details Validates input argument presence and file existence, then executes `ffmpeg` using required libx264 profile, level, CRF, pixel format, and AAC audio bitrate options through blocking subprocess invocation.
- @param args {list[str]} Expected single positional input-video path.
- @return {int} `1` on argument/validation failure; child return code otherwise.
- @satisfies REQ-057, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|18||
|`DESCRIPTION`|var|pub|22||
|`print_help`|fn|pub|25-43|def print_help(version)|
|`run`|fn|pub|44-90|def run(args)|


---

# video2h265.py | Python | 87L | 4 symbols | 3 imports | 10 comments
> Path: `src/shell_scripts/commands/video2h265.py`

## Imports
```
import subprocess
from pathlib import Path
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L18)
- @brief CLI program identifier used in usage text.
- @satisfies DES-008
- var `DESCRIPTION = "Convert one video to H.265 MP4 via ffmpeg."` (L22)
- @brief Command description exposed in global help index.
- @satisfies PRJ-002, DES-008, REQ-058
### fn `def print_help(version)` (L25-43)
- @brief Print command usage for `video2h265`.
- @details Emits deterministic help text describing required positional input and output naming semantics.
- @param version {str} CLI version string for usage suffix.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-058

### fn `def run(args)` (L44-88)
- @brief Execute H.265 transcode command with fixed FFmpeg parameters.
- @details Validates input argument presence and file existence, then executes `ffmpeg` using required libx265 CRF, codec tag, pixel format, and AAC audio bitrate options through blocking subprocess invocation.
- @param args {list[str]} Expected single positional input-video path.
- @return {int} `1` on argument/validation failure; child return code otherwise.
- @satisfies REQ-058, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|18||
|`DESCRIPTION`|var|pub|22||
|`print_help`|fn|pub|25-43|def print_help(version)|
|`run`|fn|pub|44-88|def run(args)|


---

# view_cmd.py | Python | 50L | 4 symbols | 3 imports | 4 comments
> Path: `src/shell_scripts/commands/view_cmd.py`

## Imports
```
import sys
from shell_scripts.config import get_dispatch_profile
from shell_scripts.commands._dc_common import dispatch
```

## Definitions

- var `PROGRAM = "shellscripts"` (L14)
- var `DESCRIPTION = "File viewer dispatcher by MIME type."` (L15)
### fn `def print_help(version)` (L18-34)
- @brief Render command help for `view`.
- @details Prints usage, required file argument semantics, and argument forwarding contract for the selected external viewer executable.
- @param version {str} Version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L35-51)
- @brief Execute MIME-routed view dispatch.
- @details Validates that a file argument exists; on missing argument prints error plus help and returns status code `2`; otherwise resolves runtime dispatch profile and delegates by file category through shared `_dc_common`.
- @param args {list[str]} CLI args where `args[0]` is file path.
- @return {int} Return code `2` on missing file; otherwise delegated dispatch result.
- @satisfies REQ-023, REQ-024

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|14||
|`DESCRIPTION`|var|pub|15||
|`print_help`|fn|pub|18-34|def print_help(version)|
|`run`|fn|pub|35-51|def run(args)|


---

# vscode_cmd.py | Python | 39L | 4 symbols | 2 imports | 3 comments
> Path: `src/shell_scripts/commands/vscode_cmd.py`

## Imports
```
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L13)
- var `DESCRIPTION = "Open VS Code in the project root."` (L14)
### fn `def print_help(version)` (L17-24)

### fn `def run(args)` (L25-40)
- @brief Launch VS Code after executable validation.
- @details Validates executable availability for VS Code binary and executes the command with project-root working directory.
- @param args {list[str]} Additional CLI args forwarded to VS Code.
- @return {int} Child process return code.
- @satisfies REQ-020, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|13||
|`DESCRIPTION`|var|pub|14||
|`print_help`|fn|pub|17-24|def print_help(version)|
|`run`|fn|pub|25-40|def run(args)|


---

# vsinsider_cmd.py | Python | 39L | 4 symbols | 2 imports | 3 comments
> Path: `src/shell_scripts/commands/vsinsider_cmd.py`

## Imports
```
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L13)
- var `DESCRIPTION = "Open VS Code Insiders in the project root."` (L14)
### fn `def print_help(version)` (L17-24)

### fn `def run(args)` (L25-40)
- @brief Launch VS Code Insiders after executable validation.
- @details Validates executable availability for VS Code Insiders binary and executes the command with project-root working directory.
- @param args {list[str]} Additional CLI args forwarded to VS Code Insiders.
- @return {int} Child process return code.
- @satisfies REQ-020, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|13||
|`DESCRIPTION`|var|pub|14||
|`print_help`|fn|pub|17-24|def print_help(version)|
|`run`|fn|pub|25-40|def run(args)|


---

# config.py | Python | 263L | 9 symbols | 6 imports | 20 comments
> Path: `src/shell_scripts/config.py`

## Imports
```
from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Any
from shell_scripts.utils import print_warn
```

## Definitions

### fn `def get_config_path() -> Path` (L79-90)
- @brief In-memory runtime configuration snapshot.
- @brief Return canonical runtime config location.
- @details Initialized from defaults; updated only by `load_runtime_config`.
- @details Resolves path as `$HOME/.config/shellScripts/config.json` using `Path.home()` for user directory abstraction.
- @return {Path} Absolute config file path.
- @satisfies DES-011, REQ-045
- @satisfies DES-011, DES-012, REQ-045, REQ-046

### fn `def get_default_runtime_config() -> dict[str, Any]` (L91-102)
- @brief Return deep-copied default configuration payload.
- @details Produces an isolated copy to avoid external mutation of the global defaults constant and to keep write/load operations deterministic.
- @return {dict[str, Any]} Fresh deep copy of `DEFAULT_RUNTIME_CONFIG`.
- @satisfies DES-011, DES-012

### fn `def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]` `priv` (L103-122)
- @brief Recursively merge nested mapping values.
- @details For keys where both base and override values are dictionaries, recursively merges child keys; otherwise replaces base value with override. Time complexity O(N) over override node count.
- @param base {dict[str, Any]} Target mapping mutated in place.
- @param override {dict[str, Any]} Source mapping with overriding values.
- @return {dict[str, Any]} The mutated `base` reference.
- @satisfies DES-011, REQ-045

### fn `def _normalize_command_vector(value: Any) -> list[str] | None` `priv` (L123-139)
- @brief Validate and normalize an executable argv vector.
- @details Accepts only non-empty lists of non-empty strings and returns a cloned list for defensive immutability.
- @param value {Any} Candidate command vector.
- @return {list[str]|None} Sanitized vector or `None` if invalid.
- @satisfies DES-011, REQ-045

### fn `def _normalize_categories(value: Any) -> dict[str, list[str]] | None` `priv` (L140-162)
- @brief Validate category-to-command mapping payload.
- @details Keeps only entries with string keys and valid command vectors. Invalid entries are dropped and can trigger fallback usage upstream.
- @param value {Any} Candidate category map payload.
- @return {dict[str, list[str]]|None} Sanitized category map or `None`.
- @satisfies DES-011, REQ-024, REQ-045

### fn `def load_runtime_config(path: Path | None = None) -> dict[str, Any]` (L163-202)
- @brief Load runtime configuration file and merge into defaults.
- @details Resets in-memory state to defaults for each call, then attempts to read and parse JSON payload from target path and recursively merge override keys. Missing file, invalid JSON, non-object root, or read errors preserve defaults and emit warnings.
- @param path {Path|None} Optional override path; default is canonical path.
- @return {dict[str, Any]} Active in-memory runtime configuration snapshot.
- @exception {json.JSONDecodeError} Handled internally and downgraded to warn.
- @exception {OSError} Handled internally and downgraded to warn.
- @satisfies DES-011, REQ-045

### fn `def get_management_command(name: str) -> str` (L203-219)
- @brief Resolve management command string with safe default fallback.
- @details Reads runtime key under `management.<name>`; returns default value when key is absent or not a non-empty string.
- @param name {str} Management operation key (`upgrade` or `uninstall`).
- @return {str} Shell command string to execute.
- @satisfies REQ-004, REQ-005, REQ-045

### fn `def get_dispatch_profile(name: str) -> tuple[dict[str, list[str]], list[str]]` (L220-245)
- @brief Resolve dispatch profile for diff/edit/view command wrappers.
- @details Builds profile from `dispatch.<name>` runtime payload with typed normalization and per-section fallback to hardcoded defaults for missing or invalid values.
- @param name {str} Dispatch command key (`diff`, `edit`, or `view`).
- @return {tuple[dict[str, list[str]], list[str]]} `(categories, fallback)`.
- @satisfies DES-007, REQ-024, REQ-045

### fn `def write_default_runtime_config(path: Path | None = None) -> Path` (L246-264)
- @brief Write default runtime configuration file to disk.
- @details Creates parent directories when missing and writes canonical JSON payload using sorted keys and indentation for deterministic content.
- @param path {Path|None} Optional override path; default is canonical path.
- @return {Path} Path where the file has been written.
- @exception {OSError} Propagated when filesystem write fails.
- @satisfies DES-012, REQ-046

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_config_path`|fn|pub|79-90|def get_config_path() -> Path|
|`get_default_runtime_config`|fn|pub|91-102|def get_default_runtime_config() -> dict[str, Any]|
|`_deep_merge_dict`|fn|priv|103-122|def _deep_merge_dict(base: dict[str, Any], override: dict...|
|`_normalize_command_vector`|fn|priv|123-139|def _normalize_command_vector(value: Any) -> list[str] | ...|
|`_normalize_categories`|fn|priv|140-162|def _normalize_categories(value: Any) -> dict[str, list[s...|
|`load_runtime_config`|fn|pub|163-202|def load_runtime_config(path: Path | None = None) -> dict...|
|`get_management_command`|fn|pub|203-219|def get_management_command(name: str) -> str|
|`get_dispatch_profile`|fn|pub|220-245|def get_dispatch_profile(name: str) -> tuple[dict[str, li...|
|`write_default_runtime_config`|fn|pub|246-264|def write_default_runtime_config(path: Path | None = None...|


---

# config_cli.py | Python | 2314L | 65 symbols | 11 imports | 94 comments
> Path: `src/shell_scripts/config_cli.py`

## Imports
```
from __future__ import annotations
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from shell_scripts.config import (
from shell_scripts.utils import print_error, print_info, print_success
```

## Definitions

- var `PROGRAM = "shellscripts"` (L49)
- @brief CLI program token used in inline usage help output.
- var `ROOT_LABEL = "shellScripts_Configuration"` (L55)
- var `NAME_COLUMN_WIDTH = 24` (L61)
- var `VALUE_COLUMN_WIDTH = 34` (L67)
- var `PATH_SEPARATOR = ":"` (L71)
- @brief Hierarchical path separator accepted by the configuration commands.
- var `APPEND_TOKENS = ("append", "+")` (L75)
- @brief Reserved array path tokens that append one validated item.
- var `INSERT_TOKEN = "insert"` (L79)
- @brief Reserved array path token introducing an insert index.
- var `INDEX_TOKEN_RE = re.compile(r"^-?[0-9]+$")` (L83)
- @brief Pattern matching one optional-sign decimal integer path token.
- var `SCALAR_KINDS = ("string", "integer", "float", "boolean", "selection")` (L87)
- @brief Schema kinds whose JSON value is a scalar.
### class `class ChoiceSpec` `@dataclass(frozen=True)` (L95-107)
- @brief One allowed value of a selection-type option.
- @details Immutable registry record pairing an accepted value token with its meaning, rendered in `Sel`/`Value` and `Value`/`Default`/`Meaning` tables by `--print` and `--info`.
- @satisfies REQ-097, REQ-108

### class `class FieldSpec` `@dataclass(frozen=True)` (L109-125)
- @brief One declared field of an object-row item schema.
- @details Describes one column of an `Array[Dictionary]` option consumed by row validation, cell coercion, cell reset, `--print` row tables, and the `--info` Item Schema table.
- @satisfies REQ-120, REQ-127, REQ-130

### class `class OptionSpec` `@dataclass(frozen=True)` (L127-148)
- @brief Declarative metadata of one configurable leaf option.
- @details Binds one configuration key to its value kind, short description, optional allowed choices, input-example token, constraint label, array item kind, object-row item fields, and dynamic map value kind; drives `--info` rendering, `--print` value rendering, `--get` resolution, and `--set`/`--unset` coercion plus validation.
- @satisfies DES-032, DES-036, DES-038, REQ-096, REQ-097, REQ-098, REQ-101, REQ-102, REQ-107, REQ-110, REQ-118, REQ-119, REQ-120

### class `class GroupSpec` `@dataclass(frozen=True)` (L150-161)
- @brief Declarative metadata of one configuration subtree group.
- @details Orders child schema nodes and carries the group description rendered by `--info` and the tree structure rendered by `--print`.
- @satisfies DES-032, REQ-095, REQ-107, REQ-117

### class `class TargetSpec` `@dataclass(frozen=True)` (L163-182)
- @brief One resolved CLI path target.
- @details Encodes the schema node addressed by the static path prefix and the operation selected by the trailing dynamic tokens: `value` reads or replaces the whole option, `append`/`insert` add array rows, `row` targets one 0-based array row, `cell` targets one field of an object row, `key` targets one dynamic map key, `field` targets one field of a fixed object, and `group` addresses a whole schema subtree.
- @satisfies DES-038, REQ-122, REQ-124, REQ-125, REQ-126, REQ-127

### fn `def _split_path(path: str) -> list[str] | None` `priv` (L325-343)
- @brief Declarative configuration schema registry.
- @brief Split one hierarchical configuration path.
- @details Single source of truth for the configuration CLI surface; mirrors
the `DEFAULT_RUNTIME_CONFIG` tree and MUST be updated in the same change
whenever any configuration option, default, type, or allowed value changes
(DES-033). Parity with defaults is verified at import time by
`find_schema_mismatches` and enforced per command (DES-034).
- @details Splits by `PATH_SEPARATOR` and rejects empty paths and empty segments, returning `None` for malformed input so callers can emit inline usage help. Time complexity O(n) over path length.
- @param path {str} Raw path token, for example `management:upgrade`.
- @return {list[str]|None} Non-empty path segments or `None` when malformed.
- @satisfies DES-032, DES-033, DES-034
- @satisfies REQ-099, REQ-109

### fn `def _walk_schema(parts: list[str]) -> "tuple[OptionSpec | GroupSpec | None, int]"` `priv` (L344-373)
- @brief Walk the schema registry along a path prefix.
- @details Consumes the longest prefix of `parts` that matches schema node names and returns the reached node plus the consumed depth; stops at the first unmatched segment so trailing tokens stay available for dynamic resolution. Time complexity O(n*m) over path depth and sibling count.
- @param parts {list[str]} Non-empty path segments.
- @return {tuple} `(node, depth)` where `node` is `None` when no segment matches.
- @satisfies DES-038

### fn `def _find_schema_node(parts: list[str]) -> "OptionSpec | GroupSpec | None"` `priv` (L374-390)
- @brief Resolve one full path against the schema registry.
- @details Returns the schema record only when every segment matches the registry, or `None` for unknown or non-configurable paths. Time complexity O(n*m) over path depth and sibling count.
- @param parts {list[str]} Non-empty path segments from `_split_path`.
- @return {OptionSpec|GroupSpec|None} Schema record or `None` when absent.
- @satisfies DES-032, REQ-100

### fn `def _is_index_token(token: str) -> bool` `priv` (L391-404)
- @brief Test whether one path token is a decimal integer index.
- @details Accepts an optional leading minus sign so negative indexes reach bounds checking and produce explicit out-of-bounds errors. Time complexity O(1).
- @param token {str} Path token candidate.
- @return {bool} `True` when the token parses as a decimal integer.
- @satisfies DES-038, REQ-122

### fn `def _resolve_target(path: str) -> "tuple[TargetSpec | None, str | None]"` `priv` (L405-496)
- @brief Resolve one CLI path into a typed operation target.
- @details Splits the path, walks the schema for the static prefix, and classifies trailing tokens per option kind: array kinds accept `append`/`+`, `insert:<Idx>`, `<Idx>`, and `<Idx>:<Field>`; map kinds accept exactly one `<Key>`; object kinds accept exactly one `<Field>`; scalar kinds accept no trailing tokens. Time complexity O(n*m) over path depth and sibling count.
- @param path {str} Raw hierarchical path token.
- @return {tuple} `(TargetSpec, None)` on success or `(None, error_message)` for unknown or malformed paths.
- @satisfies DES-038, REQ-122, REQ-123, REQ-124, REQ-125, REQ-126, REQ-127, REQ-128

### fn `def _resolve_value(container: Any, parts: list[str]) -> Any` `priv` (L497-515)
- @brief Navigate a nested mapping by path segments.
- @details Returns `_MISSING` when any segment is absent or crosses a non-mapping value. Time complexity O(n) over path depth.
- @param container {Any} Nested mapping candidate, usually a config dict.
- @param parts {list[str]} Non-empty path segments.
- @return {Any} Resolved value or the `_MISSING` sentinel.
- @satisfies REQ-099

### fn `def _set_nested(container: dict[str, Any], parts: list[str], value: Any) -> None` `priv` (L516-537)
- @brief Write one value into a nested mapping by path segments.
- @details Creates intermediate mappings for absent parents, replacing non-mapping parents with fresh mappings. Time complexity O(n) over depth.
- @param container {dict[str,Any]} Target mapping mutated in place.
- @param parts {list[str]} Non-empty path segments ending at the leaf key.
- @param value {Any} Coerced value to persist.
- @return {None} Mutates `container` in place.
- @satisfies REQ-101, REQ-103, DES-039

### fn `def _pop_nested(container: dict[str, Any], parts: list[str]) -> Any` `priv` (L538-559)
- @brief Remove one key from a nested mapping by path segments.
- @details Returns the removed value or `_MISSING` when any segment is absent or crosses a non-mapping value. Time complexity O(n) over depth.
- @param container {dict[str,Any]} Target mapping mutated in place.
- @param parts {list[str]} Non-empty path segments ending at the target key.
- @return {Any} Removed value or the `_MISSING` sentinel.
- @satisfies REQ-105, REQ-106

### fn `def _iter_schema_leaf_paths(` `priv` (L560-562)

### fn `def _iter_default_leaf_paths(` `priv` (L582-584)
- @brief Enumerate every schema leaf path.
- @details Depth-first recursion yielding tuples of path segments for every
`OptionSpec` node. Time complexity O(n) over schema node count.
- @param children {tuple} Sibling nodes being expanded.
- @param prefix {tuple[str,...]} Parent path segments.
- @return {Iterator[tuple[str,...]]} Leaf path segment tuples.
- @satisfies DES-034

### fn `def find_schema_mismatches() -> list[str]` (L605-635)
- @brief Enumerate every default configuration leaf path.
- @brief Verify schema registry parity with configuration defaults.
- @details Depth-first recursion yielding tuples of path segments for every
non-mapping value, expanding nested mappings as intermediate groups.
Time complexity O(n) over default node count.
- @details Fails when any default leaf is not covered by a schema leaf (equal path or schema-leaf prefix) or when any schema leaf path cannot be resolved inside `DEFAULT_RUNTIME_CONFIG`. Time complexity O(n*m) over default leaves and schema leaves.
- @param node {dict[str,Any]} Mapping being expanded.
- @param prefix {tuple[str,...]} Parent path segments.
- @return {Iterator[tuple[str,...]]} Leaf path segment tuples.
- @return {list[str]} Human-readable divergence descriptions; empty when the registry and defaults are aligned.
- @satisfies DES-034
- @satisfies DES-033, DES-034

### fn `def _fail_on_schema_mismatch() -> bool` `priv` (L641-659)
- @brief Import-time snapshot of schema/defaults divergence descriptions.
- @brief Enforce schema parity before configuration command execution.
- @details Prints one bright-red error describing every divergence detected at import time and reports whether the calling command must abort. Time complexity O(n) over mismatch count.
- @return {bool} `True` when the caller must fail with return code `1`.
- @satisfies DES-034

### fn `def _render_box_table(` `priv` (L660-661)

### fn `def _row(cells: list[str]) -> str` `priv` (L681-692)
- @brief Render one box-drawing table.
- @brief Render one padded table row line.
- @details Builds column widths from headers and rows, then emits top,
header, separator, body, and bottom lines using `┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘ ─`
and `│` glyphs, prefixing every line with `indent`. Time complexity
O(n*m) over table cells.
- @param headers {list[str]} Column header cells.
- @param rows {list[list[str]]} Body rows with one cell per column.
- @param indent {str} Left padding applied to every rendered line.
- @param cells {list[str]} Cell texts for the row.
- @return {list[str]} Fully rendered table lines.
- @return {str} Indented line framed by `│` glyphs.
- @satisfies REQ-097, REQ-108, REQ-118, REQ-119, REQ-120

### fn `def _render_json(value: Any) -> str` `priv` (L702-714)
- @brief Render one configuration value as compact JSON.
- @details Scalars, lists, and mappings serialize deterministically with sorted keys and no ASCII escaping. Time complexity O(n) over value size.
- @param value {Any} Configuration value to serialize.
- @return {str} Single-line JSON representation.
- @satisfies REQ-096, REQ-099

### fn `def _render_default_value(parts: tuple[str, ...]) -> Any` `priv` (L715-729)
- @brief Resolve one schema default value by path segments.
- @details Navigates `DEFAULT_RUNTIME_CONFIG` by the supplied tuple and returns `None` when the path is absent, so rendering always has a comparable default. Time complexity O(n) over path depth.
- @param parts {tuple[str,...]} Canonical path segments of one option.
- @return {Any} Declared default value or `None`.
- @satisfies REQ-096

### fn `def _render_indicator(parts: tuple[str, ...], value: Any) -> str` `priv` (L730-748)
- @brief Render the default or custom indicator for one leaf value.
- @details Emits `(default)` when the active value equals the schema default and `(custom | default: <Default_Value>)` otherwise. Time complexity O(1) plus default resolution.
- @param parts {tuple[str,...]} Canonical path segments of one option.
- @param value {Any} Active effective value of the option.
- @return {str} Indicator token without surrounding parentheses content markers.
- @satisfies REQ-096

### fn `def _render_print_leaf(` `priv` (L749-757)

### fn `def _render_print_children(` `priv` (L857-862)
- @brief Render one `--print` leaf option block.
- @details Emits the leaf line with the `= <JSON>` value, the default or
custom indicator, the selection action hint, and the collection summary
headers; appends the selection `Sel`/`Value` table, map `Key`/`Value`
table, primitive-array `Idx`/`Value` table, or object-array
`Idx`-plus-field-columns table, and renders explicit empty-collection
hints for zero-length collections. Time complexity O(n) over rendered
collection size.
- @param prefix {str} Ancestor connector prefix for this level.
- @param branch {str} Branch connector (`├── ` or `└── `).
- @param node_prefix {str} Tree continuation prefix for child lines.
- @param key {str} Schema node name printed verbatim.
- @param node {OptionSpec} Schema record of the leaf.
- @param value {Any} Effective value of the leaf.
- @param lines {list[str]} Output accumulator mutated in place.
- @param parts {tuple[str,...]} Canonical path segments of the leaf.
- @return {None} Appends rendered lines to `lines`.
- @satisfies REQ-096, REQ-097, REQ-115, REQ-118, REQ-119, REQ-120,
REQ-121, REQ-133

### fn `def _plain_kind_label(kind: str) -> str` `priv` (L908-927)
- @brief Render one `--print` tree level.
- @brief Render one capitalized schema kind label.
- @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
connectors, node names printed verbatim as CLI path tokens, and the
`[Path: ...]` badge on every group; delegates leaf rendering to
`_render_print_leaf`. Time complexity O(n) over subtree node count.
- @details Maps internal kind tokens to the capitalized labels used inside composite type labels. Time complexity O(1).
- @param prefix {str} Ancestor connector prefix for this level.
- @param children {tuple} Sibling schema nodes being rendered.
- @param values {Any} Effective configuration subtree for this level.
- @param lines {list[str]} Output accumulator mutated in place.
- @param base_parts {tuple[str,...]} Canonical path segments of this level.
- @param kind {str} Internal schema kind token.
- @return {None} Appends rendered lines to `lines`.
- @return {str} Capitalized kind label.
- @satisfies REQ-095, REQ-096, REQ-097, REQ-098, REQ-115, REQ-117,
REQ-118, REQ-119, REQ-120, REQ-121, REQ-133
- @satisfies REQ-107

### fn `def _render_kind_label(node: OptionSpec) -> str` `priv` (L928-963)
- @brief Render the composite `--info` type label of one option.
- @details Produces `[String]`, `[Integer]`, `[Float]`, `[Boolean]`, `[Selection]`, `[Array[<Item>]]`, `[Array[Dictionary]]`, `[Map[String, <Value>]]`, and `[Dictionary]` labels, appending the schema-declared constraint after a colon when declared. Time complexity O(1).
- @param node {OptionSpec} Schema record of the option.
- @return {str} Bracketed type label without the surrounding brackets content markers applied by the caller.
- @satisfies REQ-107, REQ-112, REQ-113

### fn `def _first_default_collection_sample(node: OptionSpec, parts: tuple[str, ...]) -> tuple[str, str]` `priv` (L964-987)
- @brief Derive one concrete copy-pasteable collection sample.
- @details Reads the schema default collection and returns the first list element JSON token or the first map key and JSON value token, falling back to placeholder tokens when the default collection is empty. Time complexity O(1) over the first entry.
- @param node {OptionSpec} Schema record of the collection option.
- @param parts {tuple[str,...]} Canonical path segments of the option.
- @return {tuple[str,str]} `(item_or_key_token, value_token)`.
- @satisfies REQ-110, REQ-113, REQ-133

### fn `def _render_info_leaf(` `priv` (L988-995)

### fn `def _render_object_row_template(node: OptionSpec) -> str` `priv` (L1128-1150)
- @brief Render one `--info` leaf option block.
- @brief Build one ready-to-use JSON row template for an object array.
- @details Emits the `[<Type>] <description>` header line and the
structured multi-line metadata: `Default` and `Set cmd` lines for
scalars, the `Value`/`Default`/`Meaning` allowed-value table plus
`Set cmd`/`Reset cmd` lines for selections, add/insert/update/delete/
overwrite/clear command lines for arrays, set/remove/overwrite/clear
command lines for maps, and full-overwrite/reset lines for objects.
Time complexity O(n) over declared choices and item fields.
- @details Emits required fields as uppercase placeholder tokens and optional fields as their schema defaults, producing a complete copy-pasteable JSON object template. Time complexity O(n) over item fields.
- @param prefix {str} Ancestor connector prefix for this level.
- @param branch {str} Branch connector (`├── ` or `└── `).
- @param node_prefix {str} Tree continuation prefix for child lines.
- @param key {str} Schema node name printed verbatim.
- @param node {OptionSpec} Schema record of the leaf.
- @param lines {list[str]} Output accumulator mutated in place.
- @param parts {tuple[str,...]} Canonical path segments of the leaf.
- @param node {OptionSpec} Schema record of the `Array[Dictionary]` option.
- @return {None} Appends rendered lines to `lines`.
- @return {str} Compact JSON object template token.
- @satisfies REQ-107, REQ-108, REQ-110, REQ-111, REQ-112, REQ-113,
REQ-117, REQ-133
- @satisfies REQ-112, REQ-133

### fn `def _render_info_children(` `priv` (L1151-1155)

### fn `def _atomic_write_text(target: Path, content: str) -> None` `priv` (L1190-1227)
- @brief Render one `--info` hierarchy level.
- @brief Write one text file atomically via a same-directory temporary.
- @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
connectors, node names printed verbatim as CLI path tokens, and the
`[Path: ...]` badge on every group; delegates leaf rendering to
`_render_info_leaf`. Time complexity O(n) over subtree node count.
- @details Creates the parent directory, writes `content` into a temporary file in the target directory, flushes and fsyncs the stream, then atomically renames the temporary onto the target so crashes never leave truncated or partial JSON content. The temporary file is removed when any step fails. Time complexity O(n) over content size.
- @param prefix {str} Ancestor connector prefix for this level.
- @param children {tuple} Sibling schema nodes being rendered.
- @param lines {list[str]} Output accumulator mutated in place.
- @param base_parts {tuple[str,...]} Canonical path segments of this level.
- @param target {Path} Destination file path.
- @param content {str} Full file content to persist.
- @return {None} Appends rendered lines to `lines`.
- @return {None} Applies the destination filesystem mutation.
- @throws {OSError} Propagated when directory creation, writing, flushing, or the atomic replacement fails.
- @satisfies REQ-107, REQ-108, REQ-110, REQ-111, REQ-112, REQ-113,
REQ-117, REQ-133
- @satisfies DES-037, REQ-103, REQ-105

### fn `def _render_default_config_text() -> str` `priv` (L1228-1245)
- @brief Render the system default configuration file content.
- @details Serializes `DEFAULT_RUNTIME_CONFIG` with sorted keys, two-space indentation, and a trailing newline for deterministic bootstrapped content. Time complexity O(n) over configuration size.
- @return {str} Canonical default configuration JSON text.
- @satisfies REQ-116

### fn `def _ensure_bootstrap() -> bool` `priv` (L1246-1269)
- @brief Initialize the configuration file with defaults when missing.
- @details Creates the configuration parent directory and writes the default JSON payload when `config.json` does not exist, so every configuration command executes against an initialized file; existing files are left untouched. Time complexity O(n) over configuration size on the initialization path, O(1) otherwise.
- @return {bool} `True` when the configuration file exists or was initialized; `False` when initialization failed.
- @satisfies REQ-116

### fn `def _load_overrides() -> "tuple[dict[str, Any] | None, str | None]"` `priv` (L1270-1295)
- @brief Load on-disk configuration overrides.
- @details Reads the canonical config file and returns its object payload; a missing file yields an empty mapping, while unreadable files, invalid JSON, and non-object roots yield an error message. Time complexity O(n) over file size.
- @return {tuple[dict|None, str|None]} `(payload, None)` on success or `(None, error_message)` on failure.
- @satisfies REQ-101, REQ-103, REQ-105

### fn `def _write_overrides(payload: dict[str, Any]) -> None` `priv` (L1296-1314)
- @brief Persist configuration overrides to the canonical config file.
- @details Writes sorted-key, two-space-indented JSON with a trailing newline through the atomic same-directory temporary-file write. Time complexity O(n) over payload size.
- @param payload {dict[str,Any]} Full on-disk override mapping.
- @return {None} Applies destination filesystem mutation.
- @throws {OSError} Propagated when the atomic write fails.
- @satisfies DES-037, REQ-103, REQ-105

### fn `def _validate_scalar_kind(value: Any, kind: str, spec: OptionSpec) -> str | None` `priv` (L1315-1358)
- @brief Validate one already-typed scalar against a schema kind.
- @details Enforces strict Python/JSON type separation: booleans are not integers, integers are not floats, strings are non-empty, and selection values must be declared choices when choices exist. Time complexity O(1).
- @param value {Any} Typed candidate value.
- @param kind {str} Schema kind token.
- @param spec {OptionSpec} Owning schema record providing choices.
- @return {str|None} `None` when valid; the error explanation otherwise.
- @satisfies REQ-101, REQ-102

### fn `def _validate_array_payload(payload: Any, spec: OptionSpec) -> str | None` `priv` (L1359-1383)
- @brief Validate one decoded array payload against its item schema.
- @details For object arrays validates every row as a dictionary whose present fields match the declared `FieldSpec` kinds and whose required fields are present; for primitive arrays validates every element against the declared item kind. Time complexity O(n) over array length.
- @param payload {Any} Decoded JSON array candidate.
- @param spec {OptionSpec} Schema record of the array option.
- @return {str|None} `None` when valid; the error explanation otherwise.
- @satisfies REQ-102, REQ-124, REQ-128

### fn `def _validate_object_row(item: Any, index: int, spec: OptionSpec) -> str | None` `priv` (L1384-1413)
- @brief Validate one object-array row against its declared fields.
- @details Requires a dictionary, rejects undeclared keys when fields are declared, enforces required-field presence, and validates each present field kind. Time complexity O(n) over row field count.
- @param item {Any} Decoded row candidate.
- @param index {int} 0-based row position used in error messages.
- @param spec {OptionSpec} Schema record declaring `item_fields`.
- @return {str|None} `None` when valid; the error explanation otherwise.
- @satisfies REQ-102, REQ-124, REQ-128

### fn `def _validate_map_payload(payload: Any, spec: OptionSpec) -> str | None` `priv` (L1414-1440)
- @brief Validate one decoded map payload against its value kind.
- @details Requires a JSON object with non-empty string keys and validates every value against the declared map value kind; `list` value kinds denote vectors of non-empty strings. Time complexity O(n) over entry count.
- @param payload {Any} Decoded JSON object candidate.
- @param spec {OptionSpec} Schema record of the map option.
- @return {str|None} `None` when valid; the error explanation otherwise.
- @satisfies REQ-102, REQ-127, REQ-128

### fn `def _validate_string_vector(value: Any) -> str | None` `priv` (L1441-1458)
- @brief Validate one vector of non-empty strings.
- @details Accepts only JSON arrays whose elements are non-empty strings, matching the runtime command-vector normalization contract. Time complexity O(n) over vector length.
- @param value {Any} Decoded JSON array candidate.
- @return {str|None} `None` when valid; the error explanation otherwise.
- @satisfies REQ-102, REQ-127

### fn `def _coerce_token(raw: str, kind: str, spec: OptionSpec) -> "tuple[bool, Any, str | None]"` `priv` (L1459-1517)
- @brief Coerce one raw CLI token into a strict schema-typed value.
- @details s Maps `boolean` tokens to JSON booleans, `integer` tokens to JSON numbers, `float` tokens to finite JSON numbers, `selection` and `string` tokens to non-empty strings, and JSON-parses `list`, `map`, and `object` tokens before payload validation. Time complexity O(n) over token length.
- @param raw {str} Raw value token from the CLI.
- @param kind {str} Target schema kind token.
- @param spec {OptionSpec} Owning schema record providing choices, item kinds, and value kinds.
- @return {tuple[bool, Any, str|None]} `(ok, value, error)` triple.
- @satisfies REQ-101, REQ-102

### fn `def _coerce_value(raw: str, spec: OptionSpec) -> "tuple[bool, Any, str | None]"` `priv` (L1518-1531)
- @brief Coerce one raw CLI token by the option schema kind.
- @details Thin adapter delegating to `_coerce_token` with the option's own kind. Time complexity O(n) over token length.
- @param raw {str} Raw value token from the CLI.
- @param spec {OptionSpec} Target option schema record.
- @return {tuple[bool, Any, str|None]} `(ok, value, error)` triple.
- @satisfies REQ-101, REQ-102

### fn `def _ensure_choice_allowed(path: str, spec: OptionSpec, value: Any) -> str | None` `priv` (L1532-1556)
- @brief Validate one value against declared selection choices.
- @details Returns an explanatory error listing every allowed choice when the value is not declared and choices exist. Time complexity O(n) over choice count.
- @param path {str} Raw CLI path used in the error message.
- @param spec {OptionSpec} Schema record providing choices.
- @param value {Any} Coerced candidate value.
- @return {str|None} `None` when allowed; the error explanation otherwise.
- @satisfies REQ-102

### fn `def _index_out_of_bounds_message(` `priv` (L1557-1558)

### fn `def _find_item_field(node: OptionSpec, name: str) -> "FieldSpec | None"` `priv` (L1584-1600)
- @brief Build one explicit out-of-bounds index error message.
- @brief Locate one declared item field by name.
- @details States the valid index range and the `:append` alternative for
row operations; insert operations state the valid insert-position range
`0..length`. Time complexity O(1).
- @details Performs a linear scan over the declared `item_fields` of an object-array schema record. Time complexity O(n) over field count.
- @param index {int} Rejected 0-based index.
- @param length {int} Current array length.
- @param leaf_name {str} Schema leaf name used in the message.
- @param insert_mode {bool} Selects the insert-position wording.
- @param node {OptionSpec} Schema record of the `Array[Dictionary]` option.
- @param name {str} Field name token from the CLI path.
- @return {str} Complete error message without severity decoration.
- @return {FieldSpec|None} Declared field record or `None` when undeclared.
- @satisfies REQ-122, REQ-126, REQ-131
- @satisfies REQ-127, REQ-130

### fn `def _coerce_array_item(` `priv` (L1601-1602)

### fn `def _overwrite_message_array(leaf_name: str, items: Any) -> str` `priv` (L1629-1648)
- @brief Coerce one raw CLI token as one array item.
- @brief Build the whole-array overwrite confirmation message.
- @details For object arrays JSON-parses the token and validates the row
against the declared item fields; for primitive arrays coerces the token
against the declared item kind. Time complexity O(n) over token length.
- @details Reports the new item count and the covered 0-based index range; omits the range when the array is empty. Time complexity O(1).
- @param raw {str} Raw item token from the CLI.
- @param node {OptionSpec} Schema record of the array option.
- @param leaf_name {str} Schema leaf name used in the message.
- @param items {Any} Persisted replacement array.
- @return {tuple[bool, Any, str|None]} `(ok, item, error)` triple.
- @return {str} Complete confirmation message.
- @satisfies REQ-124, REQ-125, REQ-126
- @satisfies REQ-128

### fn `def _append_message(leaf_name: str, item: Any, index: int) -> str` `priv` (L1649-1665)
- @brief Build the append confirmation message with the assigned index.
- @details Object rows use the object wording; primitive items embed the JSON-encoded value. Time complexity O(n) over item size.
- @param leaf_name {str} Schema leaf name used in the message.
- @param item {Any} Validated appended item.
- @param index {int} Assigned 0-based index.
- @return {str} Complete confirmation message.
- @satisfies REQ-124

### fn `def print_config_cli_help(command: str) -> None` (L1666-1737)
- @brief Print command-specific inline usage help.
- @details Documents the `:` hierarchical path syntax, the array and map path tokens, accepted value formats, environment acquisition, and per-command examples for one of `--get`, `--set`, or `--unset`. Time complexity O(1).
- @param command {str} Command token requesting inline help.
- @return {None} Writes help text to stdout.
- @satisfies REQ-109, DES-038

### fn `def _resolve_subtree_node(` `priv` (L1738-1739)

### fn `def do_print_raw() -> int` (L1762-1789)
- @brief Resolve one `--print`/`--info` sub-path into a render unit.
- @brief Print the on-disk configuration file verbatim.
- @details Walks the schema by the full path and wraps the reached node as
a single-child render tuple so subtree rendering reuses the standard
level renderers. Time complexity O(n*m) over path depth and sibling
count.
- @details Enforces schema registry parity with `DEFAULT_RUNTIME_CONFIG` before emitting output (DES-034), bootstraps the missing configuration file (REQ-116), then emits the raw bytes of the canonical config file without parsing, or a bright-red error naming the path when the file is unreadable. Time complexity O(n) over file size.
- @param path {str} Raw hierarchical sub-path token.
- @return {tuple} `(children, None)` on success where `children` is the
one-entry render tuple, or `(None, error_message)` on failure.
- @return {int} `0` on success; `1` on schema divergence or when the file is unreadable.
- @satisfies REQ-095, REQ-107
- @satisfies DES-032, DES-034, REQ-094, REQ-098, REQ-114, REQ-116, REQ-132

### fn `def do_print(path: str | None = None) -> int` (L1790-1841)
- @brief Render the effective configuration as an options tree.
- @details Bootstraps the missing configuration file, deep-merges on-disk overrides onto hardcoded defaults, then renders the schema-ordered tree with branch connectors, `[Path: ...]` badges, `= <JSON>` scalar leaves carrying default or custom indicators, selection tables with action hints, and collection summary tables; an optional `:`-separated sub-path restricts rendering to that subtree or leaf. The root annotation reports `ACTIVE` when the config file exists and `DEFAULT` otherwise. Time complexity O(n) over configuration size.
- @param path {str|None} Optional sub-path restricting the rendered subtree, for example `dispatch:diff`.
- @return {int} `0` on success; `1` on schema divergence or unknown paths.
- @satisfies DES-034, REQ-095, REQ-096, REQ-097, REQ-098, REQ-115, REQ-116, REQ-117, REQ-118, REQ-119, REQ-120, REQ-121, REQ-132, REQ-133

### fn `def do_info(path: str | None = None) -> int` (L1842-1878)
- @brief Render the configurable parameter hierarchy with descriptions.
- @details Emits the schema-ordered tree with per-group descriptions and `[Path: ...]` badges, per-option type labels and short descriptions, `Default` and full-path `Set cmd` lines for scalars, `Value`/`Default`/`Meaning` allowed-value tables with `Set cmd` and `Reset cmd` lines for selections, add/insert/update/delete/overwrite clear command lines for arrays, set/remove/overwrite/clear command lines for maps, and full-overwrite/reset lines for objects; an optional `:`-separated sub-path restricts rendering to that subtree or leaf. Time complexity O(n) over schema node count.
- @param path {str|None} Optional sub-path restricting the rendered documentation subtree, for example `management`.
- @return {int} `0` on success; `1` on schema divergence or unknown paths.
- @satisfies DES-034, DES-036, REQ-107, REQ-108, REQ-110, REQ-111, REQ-112, REQ-113, REQ-116, REQ-117, REQ-132, REQ-133

### fn `def do_get(path: str | None) -> int` (L1879-1972)
- @brief Read one configuration value by hierarchical path.
- @details Bootstraps the missing configuration file, resolves the `:`-separated path against the schema registry and the effective configuration, supports array rows by 0-based index, object-row cells by field name, and dynamic map keys by key token, prints scalars as clean single-line JSON and object or array subtrees as indented JSON, and fails with explicit stderr errors for unknown paths, out-of-bounds indexes, and missing keys or fields. Time complexity O(n) over subtree size.
- @param path {str|None} Hierarchical path token, for example `management:upgrade` or `dispatch:diff:fallback:0`.
- @return {int} `0` on success; `1` for missing arguments, unknown paths, out-of-bounds indexes, or absent values, keys, or fields.
- @satisfies DES-034, DES-038, REQ-098, REQ-099, REQ-100, REQ-109, REQ-116, REQ-122, REQ-123, REQ-131, REQ-132

### fn `def do_set(path: str | None, value: str | None) -> int` (L1973-2169)
- @brief Set one configuration value by hierarchical path.
- @details Bootstraps the missing configuration file, resolves the target operation from the path tokens, resolves `$NAME` tokens from the environment, coerces the value to the strict schema type, validates schema constraints, applies the mutation to the effective configuration (defaults merged with overrides), persists the resulting collection or scalar as one override value through the atomic write, and prints an operation-specific confirmation. Time complexity O(n) over configuration size.
- @param path {str|None} Hierarchical path token optionally ending with array or map operation tokens.
- @param value {str|None} Raw value token or `$NAME` environment token.
- @return {int} `0` on success; `1` for missing arguments, unknown paths, invalid values, disallowed choices, out-of-bounds indexes, undefined environment variables, or unreadable config files.
- @satisfies DES-034, DES-037, DES-038, DES-039, REQ-101, REQ-102, REQ-103, REQ-104, REQ-109, REQ-116, REQ-124, REQ-125, REQ-126, REQ-127, REQ-128, REQ-131, REQ-132

### fn `def do_unset(path: str | None) -> int` (L2170-2298)
- @brief Remove one configuration override by hierarchical path.
- @details Bootstraps the missing configuration file, resolves the target operation from the path tokens, removes the override key (leaf or subtree), deletes one array row with immediate contiguous re-indexing, resets one object-row field to its declared default or removes the undeclared key, removes one dynamic map key, persists atomically, and prints the operation-specific confirmation. Time complexity O(n) over configuration size.
- @param path {str|None} Hierarchical path token optionally ending with array or map removal tokens.
- @return {int} `0` on success; `1` for missing arguments, unknown paths, out-of-bounds indexes, absent overrides, keys, or fields, or unreadable config files.
- @satisfies DES-034, DES-037, DES-038, DES-039, REQ-105, REQ-106, REQ-109, REQ-116, REQ-129, REQ-130, REQ-131, REQ-132

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|49||
|`ROOT_LABEL`|var|pub|55||
|`NAME_COLUMN_WIDTH`|var|pub|61||
|`VALUE_COLUMN_WIDTH`|var|pub|67||
|`PATH_SEPARATOR`|var|pub|71||
|`APPEND_TOKENS`|var|pub|75||
|`INSERT_TOKEN`|var|pub|79||
|`INDEX_TOKEN_RE`|var|pub|83||
|`SCALAR_KINDS`|var|pub|87||
|`ChoiceSpec`|class|pub|95-107|class ChoiceSpec|
|`FieldSpec`|class|pub|109-125|class FieldSpec|
|`OptionSpec`|class|pub|127-148|class OptionSpec|
|`GroupSpec`|class|pub|150-161|class GroupSpec|
|`TargetSpec`|class|pub|163-182|class TargetSpec|
|`_split_path`|fn|priv|325-343|def _split_path(path: str) -> list[str] | None|
|`_walk_schema`|fn|priv|344-373|def _walk_schema(parts: list[str]) -> "tuple[OptionSpec |...|
|`_find_schema_node`|fn|priv|374-390|def _find_schema_node(parts: list[str]) -> "OptionSpec | ...|
|`_is_index_token`|fn|priv|391-404|def _is_index_token(token: str) -> bool|
|`_resolve_target`|fn|priv|405-496|def _resolve_target(path: str) -> "tuple[TargetSpec | Non...|
|`_resolve_value`|fn|priv|497-515|def _resolve_value(container: Any, parts: list[str]) -> Any|
|`_set_nested`|fn|priv|516-537|def _set_nested(container: dict[str, Any], parts: list[st...|
|`_pop_nested`|fn|priv|538-559|def _pop_nested(container: dict[str, Any], parts: list[st...|
|`_iter_schema_leaf_paths`|fn|priv|560-562|def _iter_schema_leaf_paths(|
|`_iter_default_leaf_paths`|fn|priv|582-584|def _iter_default_leaf_paths(|
|`find_schema_mismatches`|fn|pub|605-635|def find_schema_mismatches() -> list[str]|
|`_fail_on_schema_mismatch`|fn|priv|641-659|def _fail_on_schema_mismatch() -> bool|
|`_render_box_table`|fn|priv|660-661|def _render_box_table(|
|`_row`|fn|priv|681-692|def _row(cells: list[str]) -> str|
|`_render_json`|fn|priv|702-714|def _render_json(value: Any) -> str|
|`_render_default_value`|fn|priv|715-729|def _render_default_value(parts: tuple[str, ...]) -> Any|
|`_render_indicator`|fn|priv|730-748|def _render_indicator(parts: tuple[str, ...], value: Any)...|
|`_render_print_leaf`|fn|priv|749-757|def _render_print_leaf(|
|`_render_print_children`|fn|priv|857-862|def _render_print_children(|
|`_plain_kind_label`|fn|priv|908-927|def _plain_kind_label(kind: str) -> str|
|`_render_kind_label`|fn|priv|928-963|def _render_kind_label(node: OptionSpec) -> str|
|`_first_default_collection_sample`|fn|priv|964-987|def _first_default_collection_sample(node: OptionSpec, pa...|
|`_render_info_leaf`|fn|priv|988-995|def _render_info_leaf(|
|`_render_object_row_template`|fn|priv|1128-1150|def _render_object_row_template(node: OptionSpec) -> str|
|`_render_info_children`|fn|priv|1151-1155|def _render_info_children(|
|`_atomic_write_text`|fn|priv|1190-1227|def _atomic_write_text(target: Path, content: str) -> None|
|`_render_default_config_text`|fn|priv|1228-1245|def _render_default_config_text() -> str|
|`_ensure_bootstrap`|fn|priv|1246-1269|def _ensure_bootstrap() -> bool|
|`_load_overrides`|fn|priv|1270-1295|def _load_overrides() -> "tuple[dict[str, Any] | None, st...|
|`_write_overrides`|fn|priv|1296-1314|def _write_overrides(payload: dict[str, Any]) -> None|
|`_validate_scalar_kind`|fn|priv|1315-1358|def _validate_scalar_kind(value: Any, kind: str, spec: Op...|
|`_validate_array_payload`|fn|priv|1359-1383|def _validate_array_payload(payload: Any, spec: OptionSpe...|
|`_validate_object_row`|fn|priv|1384-1413|def _validate_object_row(item: Any, index: int, spec: Opt...|
|`_validate_map_payload`|fn|priv|1414-1440|def _validate_map_payload(payload: Any, spec: OptionSpec)...|
|`_validate_string_vector`|fn|priv|1441-1458|def _validate_string_vector(value: Any) -> str | None|
|`_coerce_token`|fn|priv|1459-1517|def _coerce_token(raw: str, kind: str, spec: OptionSpec) ...|
|`_coerce_value`|fn|priv|1518-1531|def _coerce_value(raw: str, spec: OptionSpec) -> "tuple[b...|
|`_ensure_choice_allowed`|fn|priv|1532-1556|def _ensure_choice_allowed(path: str, spec: OptionSpec, v...|
|`_index_out_of_bounds_message`|fn|priv|1557-1558|def _index_out_of_bounds_message(|
|`_find_item_field`|fn|priv|1584-1600|def _find_item_field(node: OptionSpec, name: str) -> "Fie...|
|`_coerce_array_item`|fn|priv|1601-1602|def _coerce_array_item(|
|`_overwrite_message_array`|fn|priv|1629-1648|def _overwrite_message_array(leaf_name: str, items: Any) ...|
|`_append_message`|fn|priv|1649-1665|def _append_message(leaf_name: str, item: Any, index: int...|
|`print_config_cli_help`|fn|pub|1666-1737|def print_config_cli_help(command: str) -> None|
|`_resolve_subtree_node`|fn|priv|1738-1739|def _resolve_subtree_node(|
|`do_print_raw`|fn|pub|1762-1789|def do_print_raw() -> int|
|`do_print`|fn|pub|1790-1841|def do_print(path: str | None = None) -> int|
|`do_info`|fn|pub|1842-1878|def do_info(path: str | None = None) -> int|
|`do_get`|fn|pub|1879-1972|def do_get(path: str | None) -> int|
|`do_set`|fn|pub|1973-2169|def do_set(path: str | None, value: str | None) -> int|
|`do_unset`|fn|pub|2170-2298|def do_unset(path: str | None) -> int|


---

# core.py | Python | 393L | 10 symbols | 8 imports | 25 comments
> Path: `src/shell_scripts/core.py`

## Imports
```
import sys
import subprocess
from shell_scripts import __version__
from shell_scripts.config import (
from shell_scripts.version_check import (
from shell_scripts.commands import get_command
from shell_scripts.utils import (
from shell_scripts import config_cli
```

## Definitions

- var `PROGRAM = "shellscripts"` (L40)
- var `HELP_COMMAND_COLUMN_WIDTH = 16` (L46)
- @brief Fixed command-name column width for grouped help rendering.
- @details Forces deterministic spacing for all command rows across grouped
global help sections.
- @satisfies REQ-066
- var `FORCED_REINSTALL_OPTIONS = "--force --reinstall --refresh"` (L54)
- @brief Option suffix appended to upgrade commands when `--force` is active.
- @details Standard forced-reinstall options for `uv tool install`: replace
the installed tool entry, reinstall the package, and refresh cached remote
metadata so the upgrade performs a full re-download and reinstallation.
- @satisfies REQ-088, REQ-089
- var `HELP_SECTION_COMMANDS = (` (L62)
- @brief Ordered command groups for global help rendering.
- @details Defines deterministic section order and command-token order used by
`print_help` when emitting grouped command help. Ordering is normative and
maps directly to REQ-066 output expectations.
- @satisfies DES-014, REQ-066
### fn `def print_help(command_name=None)` (L132-196)
- @brief Print global or command-specific help text.
- @details Renders command module help for known command names; otherwise exits with explicit unknown-command error. Global help includes management options and grouped command sections using deterministic section and command order, with descriptions sourced from each command module `DESCRIPTION` constant.
- @param command_name {str|None} Optional command token for scoped help.
- @return {None} Writes to stdout/stderr; may terminate process on invalid command.
- @throws {SystemExit} Raised when unknown command name is requested.
- @satisfies PRJ-002, DES-014, REQ-001, REQ-002, REQ-066, REQ-068, REQ-069

### fn `def _build_develop_upgrade_command(latest_tag: str) -> str` `priv` (L197-212)
- @brief Compose the develop upgrade command for one GitHub release tag.
- @details Resolves the `management.upgrade_develop` runtime-config template, substitutes the `{tag}` placeholder with the supplied tag, and returns the shell command that installs the package from the GitHub tag archive. Complexity O(n) over template length.
- @param latest_tag {str} GitHub release tag token preserving its `v` prefix.
- @return {str} Fully substituted shell upgrade command.
- @satisfies REQ-076, DES-019

### fn `def do_upgrade(develop: bool = False, force: bool = False) -> int` (L213-252)
- @brief Execute Linux-only upgrade command resolved from runtime config.
- @details Reads management command string from runtime config key `management.upgrade` (PyPI default) or, when `develop` is set, resolves the latest GitHub release tag and composes the tag-pinned upgrade command; appends ` --force --reinstall --refresh` to the resolved command when `force` is set; executes the composed command on Linux via shell invocation and prints the manual fallback command on non-Linux systems. Complexity O(n) over the composed command string length.
- @param develop {bool} Select upgrade from the latest GitHub release tag.
- @param force {bool} Append forced-reinstall options to the upgrade command.
- @return {int} `1` when develop tag resolution fails; subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-004, REQ-076, REQ-078, REQ-087, REQ-088, REQ-089, REQ-045, REQ-056

### fn `def do_uninstall()` (L253-275)
- @brief Execute Linux-only uninstall command resolved from runtime config.
- @details Reads management command string from runtime config key `management.uninstall`, executes it on Linux via shell invocation, and prints manual fallback command on non-Linux systems.
- @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-005, REQ-045, REQ-056

### fn `def do_write_config()` (L276-291)
- @brief Persist default runtime configuration file to disk.
- @details Writes canonical config JSON to `$HOME/.config/shellScripts/config.json` and logs destination path.
- @return {int} `0` on successful write.
- @throws {OSError} Propagated on filesystem write failure.
- @satisfies REQ-046

### fn `def main()` (L292-394)
- @brief Entrypoint for shellscripts argument dispatch.
- @details Performs runtime OS detection, update check, runtime configuration load, and argument dispatch through management flags (`--version` prints the aligned three-line report with installed plus PyPI/GitHub latest versions; `--upgrade` upgrades from PyPI or, with `--develop`/`--dev`, from the latest GitHub release tag; `--force` appends forced-reinstall options to the selected upgrade command; bare `--develop`/`--dev`/`--force` selectors are rejected; `--print` and `--info` accept an optional ':'-separated sub-path restricting the rendered subtree) and subcommands, then restores terminal raw/cbreak and disables legacy+xterm mouse-tracking modes (`?9l`, `?1000l`, `?1001l`, `?1002l`, `?1003l`, `?1004l`, `?1005l`, `?1006l`, `?1007l`, `?1015l`, `?1016l`) before exit.
- @return {int} Process-compatible return code for caller (`sys.exit`).
- @satisfies PRJ-001, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047, REQ-064, REQ-065, REQ-066, REQ-068, REQ-069, REQ-075, REQ-076, REQ-077, REQ-078, REQ-087, REQ-088, REQ-089, REQ-090, REQ-091, REQ-094, REQ-095, REQ-096, REQ-097, REQ-098, REQ-099, REQ-100, REQ-101, REQ-102, REQ-103, REQ-104, REQ-105, REQ-106, REQ-107, REQ-108, REQ-109, REQ-114, REQ-115, REQ-116, REQ-117, REQ-118, REQ-119, REQ-120, REQ-121, REQ-122, REQ-123, REQ-124, REQ-125, REQ-126, REQ-127, REQ-128, REQ-129, REQ-130, REQ-131, REQ-132, REQ-133

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|40||
|`HELP_COMMAND_COLUMN_WIDTH`|var|pub|46||
|`FORCED_REINSTALL_OPTIONS`|var|pub|54||
|`HELP_SECTION_COMMANDS`|var|pub|62||
|`print_help`|fn|pub|132-196|def print_help(command_name=None)|
|`_build_develop_upgrade_command`|fn|priv|197-212|def _build_develop_upgrade_command(latest_tag: str) -> str|
|`do_upgrade`|fn|pub|213-252|def do_upgrade(develop: bool = False, force: bool = False...|
|`do_uninstall`|fn|pub|253-275|def do_uninstall()|
|`do_write_config`|fn|pub|276-291|def do_write_config()|
|`main`|fn|pub|292-394|def main()|


---

# utils.py | Python | 455L | 42 symbols | 8 imports | 26 comments
> Path: `src/shell_scripts/utils.py`

## Imports
```
import os
import sys
import subprocess
import shutil
import shlex
from pathlib import Path
from typing import overload
import termios
```

## Definitions

- var `RESET = "\033[0m"` (L23)
- var `BOLD = "\033[1m"` (L24)
- var `RED = "\033[31m"` (L25)
- var `GREEN = "\033[32m"` (L26)
- var `YELLOW = "\033[33m"` (L27)
- var `BLUE = "\033[34m"` (L28)
- var `MAGENTA = "\033[35m"` (L29)
- var `CYAN = "\033[36m"` (L30)
- var `WHITE = "\033[37m"` (L31)
- var `BRIGHT_RED = "\033[91m"` (L32)
- var `BRIGHT_GREEN = "\033[92m"` (L33)
- var `BRIGHT_YELLOW = "\033[93m"` (L34)
- var `BRIGHT_BLUE = "\033[94m"` (L35)
- var `BRIGHT_CYAN = "\033[96m"` (L36)
- var `BRIGHT_WHITE = "\033[97m"` (L37)
### fn `def color_enabled()` (L66-71)
- @brief Escape-sequence payload that disables known xterm mouse-reporting modes.
- @details Concatenates CSI mode-off controls for legacy X10 mode (`?9l`) and
common xterm mouse tracking modes (`?1000l`..`?1016l`).
- @satisfies REQ-064, REQ-065

### fn `def c(text, color)` (L72-77)

### fn `def print_info(msg)` (L78-81)

### fn `def print_error(msg)` (L82-85)

### fn `def print_warn(msg)` (L86-89)

### fn `def print_success(msg)` (L90-93)

### fn `def get_project_root()` (L94-106)

### fn `def require_project_root()` (L107-115)

### fn `def detect_runtime_os()` (L116-138)
- @brief Detect and cache runtime operating-system token.
- @details Normalizes `sys.platform` into deterministic categories (`windows`, `linux`, `darwin`, `other`) and stores the result in module cache for subsequent calls. Time complexity O(1).
- @return {str} Normalized runtime operating-system token.
- @satisfies DES-002, REQ-047

### fn `def get_runtime_os()` (L139-152)
- @brief Return cached runtime operating-system token.
- @details Lazily initializes the cache via `detect_runtime_os` when unset, preserving a single startup-consistent OS classification.
- @return {str} Normalized runtime operating-system token.
- @satisfies DES-002, REQ-047

### fn `def is_windows()` (L153-163)
- @brief Check whether runtime operating system is Windows.
- @details Evaluates cached runtime token from `get_runtime_os`.
- @return {bool} `True` when runtime OS is Windows; otherwise `False`.
- @satisfies REQ-047

### fn `def is_linux()` (L164-174)
- @brief Check whether runtime operating system is Linux.
- @details Evaluates cached runtime token from `get_runtime_os`.
- @return {bool} `True` when runtime OS is Linux; otherwise `False`.
- @satisfies CTN-004, REQ-004, REQ-005, REQ-047

### fn `def _is_executable_file(path: Path) -> bool` `priv` (L175-188)
- @brief Validate executable-file capability for a filesystem path.
- @details Expands user-home markers, checks path kind, and applies platform executable checks. On Windows, missing-extension candidates are validated against `PATHEXT` suffixes.
- @param path {Path} Candidate executable filesystem path.
- @return {bool} `True` when the path resolves to an executable file.
- @satisfies CTN-003, REQ-055

### fn `def _resolve_executable_file(path: Path) -> Path | None` `priv` (L189-218)
- @brief Resolve an executable filesystem path for the runtime OS.
- @details Expands user-home markers and resolves Windows extension-less candidates through `PATHEXT` fallback checks.
- @param path {Path} Candidate executable filesystem path.
- @return {Path | None} Resolved executable path when runnable, else `None`.
- @satisfies CTN-003, REQ-055

### fn `def resolve_executable_command(command: str) -> str | None` (L219-240)
- @brief Resolve a runnable command token to an executable path.
- @details Accepts command names or executable paths and returns the concrete runnable executable path when available on the current runtime platform.
- @param command {str} Command token or filesystem path to executable.
- @return {str | None} Resolved executable path or `None` when not runnable.
- @satisfies CTN-003, REQ-055

### fn `def is_executable_command(command: str) -> bool` (L241-254)
- @brief Determine whether an external command is executable on runtime OS.
- @details Accepts command names or executable paths. Name-based checks use `PATH` resolution via `shutil.which`; path-based checks verify executable file metadata, including Windows `PATHEXT` variants.
- @param command {str} Command token or filesystem path to executable.
- @return {bool} `True` when command is executable; otherwise `False`.
- @satisfies CTN-003, REQ-055

### fn `def command_exists(cmd)` (L255-258)

### fn `def require_commands(cmd: str, /) -> str` `@overload` (L260-263)

### fn `def require_commands(cmd1: str, cmd2: str, /, *cmds: str) -> list[str]` `@overload` (L265-268)

### fn `def require_commands(*cmds: str) -> str | list[str]` (L269-281)

### fn `def _is_shell_assignment_token(token)` `priv` (L282-297)
- @brief Check whether a token is a shell variable assignment.
- @details Matches `NAME=value` form where `NAME` obeys shell identifier syntax and therefore does not represent an executable token.
- @param token {str} Shell token candidate.
- @return {bool} `True` when token is an assignment expression.
- @satisfies REQ-056

### fn `def extract_shell_executables(command_line)` (L298-341)
- @brief Extract executable tokens from a shell command line.
- @details Tokenizes command line using runtime-OS splitting mode and returns ordered unique executable candidates at command boundaries (`&&`, `||`, `;`, `|`) including wrapper commands such as `sudo`.
- @param command_line {str} Raw shell command line.
- @return {list[str]} Ordered executable token list.
- @satisfies REQ-056

### fn `def require_shell_command_executables(command_line)` (L342-358)
- @brief Validate executable availability for a shell command line.
- @details Extracts executable tokens from `command_line`, validates each token via `is_executable_command`, prints deterministic error with missing command name, and terminates process on first failure.
- @param command_line {str} Raw shell command line.
- @return {None} Process exits on validation failure.
- @satisfies REQ-056

### fn `def _is_tty_stream(stream)` `priv` (L359-378)
- @brief Determine whether a stream is an attached TTY.
- @details Performs capability checks (`isatty`, callable) and returns deterministic boolean without raising on unsupported stream objects. Time complexity O(1).
- @param stream {object} Stream-like object (stdin/stdout/stderr candidate).
- @return {bool} `True` when stream supports and reports TTY attachment.
- @satisfies REQ-064

### fn `def capture_terminal_state()` (L379-403)
- @brief Capture current stdin terminal attributes when available.
- @details Reads current TTY attributes via `termios.tcgetattr` only on runtimes exposing `termios` and when stdin is a TTY. Returns `None` when attributes are unavailable. Time complexity O(1).
- @return {list[object] | None} Saved TTY attributes for later restoration.
- @satisfies REQ-064

### fn `def reset_terminal_state(saved_tty=None)` (L404-453)
- @brief Restore terminal raw/cbreak and mouse-tracking state.
- @details Restores previously captured stdin termios attributes when present, writes `_MOUSE_OFF_ESCAPE_SEQUENCE` (`?9l`, `?1000l`, `?1001l`, `?1002l`, `?1003l`, `?1004l`, `?1005l`, `?1006l`, `?1007l`, `?1015l`, `?1016l`) to TTY stdout, and best-effort runs `stty sane` for Git Bash/Unix-compatible terminals. Failures are ignored to preserve wrapper exit semantics. Time complexity O(1).
- @param saved_tty {list[object] | None} Attributes from `capture_terminal_state`.
- @return {None} Performs best-effort terminal-state restoration.
- @satisfies REQ-064, REQ-065

### fn `def run_cmd(cmd, **kwargs)` (L454-456)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`RESET`|var|pub|23||
|`BOLD`|var|pub|24||
|`RED`|var|pub|25||
|`GREEN`|var|pub|26||
|`YELLOW`|var|pub|27||
|`BLUE`|var|pub|28||
|`MAGENTA`|var|pub|29||
|`CYAN`|var|pub|30||
|`WHITE`|var|pub|31||
|`BRIGHT_RED`|var|pub|32||
|`BRIGHT_GREEN`|var|pub|33||
|`BRIGHT_YELLOW`|var|pub|34||
|`BRIGHT_BLUE`|var|pub|35||
|`BRIGHT_CYAN`|var|pub|36||
|`BRIGHT_WHITE`|var|pub|37||
|`color_enabled`|fn|pub|66-71|def color_enabled()|
|`c`|fn|pub|72-77|def c(text, color)|
|`print_info`|fn|pub|78-81|def print_info(msg)|
|`print_error`|fn|pub|82-85|def print_error(msg)|
|`print_warn`|fn|pub|86-89|def print_warn(msg)|
|`print_success`|fn|pub|90-93|def print_success(msg)|
|`get_project_root`|fn|pub|94-106|def get_project_root()|
|`require_project_root`|fn|pub|107-115|def require_project_root()|
|`detect_runtime_os`|fn|pub|116-138|def detect_runtime_os()|
|`get_runtime_os`|fn|pub|139-152|def get_runtime_os()|
|`is_windows`|fn|pub|153-163|def is_windows()|
|`is_linux`|fn|pub|164-174|def is_linux()|
|`_is_executable_file`|fn|priv|175-188|def _is_executable_file(path: Path) -> bool|
|`_resolve_executable_file`|fn|priv|189-218|def _resolve_executable_file(path: Path) -> Path | None|
|`resolve_executable_command`|fn|pub|219-240|def resolve_executable_command(command: str) -> str | None|
|`is_executable_command`|fn|pub|241-254|def is_executable_command(command: str) -> bool|
|`command_exists`|fn|pub|255-258|def command_exists(cmd)|
|`require_commands`|fn|pub|260-263|def require_commands(cmd: str, /) -> str|
|`require_commands`|fn|pub|265-268|def require_commands(cmd1: str, cmd2: str, /, *cmds: str)...|
|`require_commands`|fn|pub|269-281|def require_commands(*cmds: str) -> str | list[str]|
|`_is_shell_assignment_token`|fn|priv|282-297|def _is_shell_assignment_token(token)|
|`extract_shell_executables`|fn|pub|298-341|def extract_shell_executables(command_line)|
|`require_shell_command_executables`|fn|pub|342-358|def require_shell_command_executables(command_line)|
|`_is_tty_stream`|fn|priv|359-378|def _is_tty_stream(stream)|
|`capture_terminal_state`|fn|pub|379-403|def capture_terminal_state()|
|`reset_terminal_state`|fn|pub|404-453|def reset_terminal_state(saved_tty=None)|
|`run_cmd`|fn|pub|454-456|def run_cmd(cmd, **kwargs)|


---

# version_check.py | Python | 353L | 31 symbols | 8 imports | 21 comments
> Path: `src/shell_scripts/version_check.py`

## Imports
```
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
```

## Definitions

- var `PROGRAM = "shellscripts"` (L22)
- var `OWNER = "Ogekuri"` (L23)
- var `REPOSITORY = "shellScripts"` (L24)
- var `IDLE_DELAY = 3600` (L25)
- var `HTTP_ERROR_IDLE_DELAY = 86400` (L26)
- var `HTTP_TIMEOUT = 2` (L27)
- var `GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"` (L28)
- var `PYPI_API_URL = f"https://pypi.org/pypi/{PROGRAM}/json"` (L29)
- var `CACHE_DIR = Path.home() / ".cache" / PROGRAM` (L30)
- var `IDLE_TIME_FILE = CACHE_DIR / "check_version_idle-time.json"` (L31)
- var `BRIGHT_GREEN = "\033[92m"` (L33)
- var `BRIGHT_RED = "\033[91m"` (L34)
- var `RESET = "\033[0m"` (L35)
### fn `def _read_idle_config() -> dict[str, object] | None` `priv` (L38-56)
- @brief Load cached cooldown metadata for the version check.
- @details Reads the cooldown JSON payload from the user cache directory. Absent files and unreadable JSON payloads resolve to `None`. Complexity: O(1) for fixed-size payload parsing.
- @return {dict[str, object] | None} Cached cooldown payload or `None`.
- @satisfies DES-003, REQ-059

### fn `def _write_idle_config(last_check_ts: float, idle_delay_seconds: int) -> None` `priv` (L57-86)
- @brief Persist cooldown timestamps for the next version-check gate.
- @details Derives the idle-until timestamp from the supplied delay, writes both machine-readable timestamps and UTC-rendered strings, and stores the applied delay for downstream inspection. Complexity: O(1).
- @param last_check_ts {float} UNIX timestamp recorded for the current check.
- @param idle_delay_seconds {int} Cooldown duration applied after the check.
- @return {None} No return value.
- @throws {OSError} Propagated when cache directory creation or file write fails.
- @satisfies DES-003, DES-004, DES-005, REQ-061

### fn `def _is_forced_version_check() -> bool` `priv` (L87-99)
- @brief Detect CLI flags that force the version-check HTTP request.
- @details Evaluates the live process argument vector and returns `True` when the current invocation requested `--version` or `--ver`. Complexity: O(N) where N is the number of CLI arguments.
- @return {bool} `True` when the request must bypass cooldown gating.
- @satisfies REQ-003, REQ-059

### fn `def _format_request_error(error: Exception) -> str` `priv` (L100-122)
- @brief Convert a request exception into terminal output detail text.
- @details Returns a stable, parser-friendly error descriptor for HTTP and non-HTTP request failures. HTTP errors preserve the status code. Non-HTTP errors expose the exception type and optional message. Complexity: O(1).
- @param error {Exception} Request failure captured during update checking.
- @return {str} Error detail suffix without terminal color codes.
- @satisfies DES-005, DES-006, REQ-061

### fn `def _handle_request_error(last_check_ts: float, error: Exception) -> None` `priv` (L123-139)
- @brief Persist cooldown metadata and print the request error line.
- @details Applies the fixed HTTP-error cooldown, updates the cooldown JSON, and emits a bright-red terminal line for the supplied request failure. Complexity: O(1) excluding filesystem latency.
- @param last_check_ts {float} UNIX timestamp recorded for the failed check.
- @param error {Exception} Request failure captured during update checking.
- @return {None} No return value.
- @throws {OSError} Propagated when cache directory creation or file write fails.
- @satisfies DES-003, DES-005, DES-006, REQ-061

### fn `def _should_check(force_check: bool = False) -> bool` `priv` (L140-161)
- @brief Evaluate whether the GitHub version-check request should run.
- @details Forces execution when `force_check` is `True`; otherwise reads the cached idle-until timestamp and compares it against the current wall-clock time. Complexity: O(1).
- @param force_check {bool} Cooldown-bypass flag derived from CLI arguments.
- @return {bool} `True` when the HTTP request is allowed or forced.
- @satisfies REQ-003, REQ-059

### fn `def _parse_version(version_value: str) -> tuple[int, ...]` `priv` (L162-175)
- @brief Convert a semantic-version string into an integer tuple.
- @details Strips a leading `v` prefix, splits by `.`, and converts each segment to `int`. Complexity: O(N) where N is the number of segments.
- @param version_value {str} Raw semantic version token.
- @return {tuple[int, ...]} Parsed numeric version segments.
- @throws {ValueError} Propagated when a segment is not numeric.
- @satisfies PRJ-004

### fn `def _compare_versions(current: str, latest: str) -> bool` `priv` (L176-193)
- @brief Compare installed and latest semantic versions.
- @details Parses both version strings into integer tuples and returns `True` only when `latest` is newer than `current`. Invalid inputs collapse to `False`. Complexity: O(N).
- @param current {str} Installed package version.
- @param latest {str} Latest GitHub release version.
- @return {bool} `True` when the remote version is newer.
- @satisfies PRJ-004, REQ-060

### fn `def _fetch_json_payload(` `priv` (L194-195)

### fn `def fetch_pypi_latest_version(current_version: str) -> str` (L219-239)
- @brief Fetch and decode one JSON payload over HTTP.
- @brief Resolve the latest published version from the PyPI registry.
- @details Issues a GET request with caller-supplied `Accept` header and a
program/version `User-Agent`, then decodes the response body as a JSON
object. Time complexity O(n) over payload size.
- @details Queries the PyPI JSON API for this program and extracts field `info.version`. Complexity O(1) over response object size.
- @param url {str} Remote JSON endpoint URL.
- @param current_version {str} Installed package version used in User-Agent.
- @param accept_header {str} Value of the HTTP `Accept` header.
- @param current_version {str} Installed package version used in User-Agent.
- @return {dict[str, Any]} Parsed JSON response object.
- @return {str} Latest published version token (for example `1.2.3`).
- @throws {urllib.error.HTTPError} On HTTP error responses.
- @throws {urllib.error.URLError} On connection failures.
- @throws {json.JSONDecodeError} On malformed payload bodies.
- @throws {urllib.error.HTTPError} On HTTP error responses.
- @throws {urllib.error.URLError} On connection failures.
- @throws {json.JSONDecodeError} On malformed payload bodies.
- @throws {KeyError} When `info.version` fields are absent.
- @satisfies DES-018, DES-019
- @satisfies DES-018, PRJ-004

### fn `def fetch_github_latest_release(current_version: str) -> str` (L240-260)
- @brief Resolve the latest GitHub release tag regardless of its branch.
- @details Queries the GitHub Releases API `latest` endpoint and extracts field `tag_name`, which tracks the newest published tagged release across any branch. Complexity O(1) over response object size.
- @param current_version {str} Installed package version used in User-Agent.
- @return {str} Latest release tag token preserving its `v` prefix.
- @throws {urllib.error.HTTPError} On HTTP error responses.
- @throws {urllib.error.URLError} On connection failures.
- @throws {json.JSONDecodeError} On malformed payload bodies.
- @throws {KeyError} When `tag_name` field is absent.
- @satisfies DES-019, REQ-076

- var `BRIGHT_GREEN = "\033[92m"` (L261)
- var `BRIGHT_RED = "\033[91m"` (L262)
- var `RESET = "\033[0m"` (L263)
- var `REPORT_LABEL_WIDTH = 18` (L270)
- @brief Fixed label column width for aligned `--version` report lines.
- @details Left-justifies every report label (`Current Installed`,
`Latest @ PyPI`, `Latest @ GitHub`) before the `: ` value separator so all
version tokens start at the same output column.
- @satisfies REQ-091
### fn `def format_version_report_line(label: str, value: str) -> str` (L273-287)
- @brief Render one aligned `--version` report line.
- @details Left-justifies the report label to `REPORT_LABEL_WIDTH` characters, then appends `: ` and the raw value without color codes so callers keep control of terminal coloring. Time complexity O(1).
- @param label {str} Report label token (for example `Latest @ PyPI`).
- @param value {str} Report value token (version string or `unknown (<reason>)`).
- @return {str} Aligned report line shaped as `<label>: <value>`.
- @satisfies REQ-075, REQ-091

### fn `def print_remote_latest_versions(current_version: str) -> None` (L288-317)
- @brief Print PyPI and GitHub latest-version report lines.
- @details Emits one aligned `Latest @ <source>` line per remote source in fixed order (PyPI, GitHub), left-justifying each label to `REPORT_LABEL_WIDTH` characters. A failed source lookup prints one bright-red aligned line whose value is `unknown (<reason>)` where `<reason>` is the `_format_request_error` descriptor of the actual failure, and the remaining source is still processed. Complexity O(1) excluding network latency.
- @param current_version {str} Installed package version used in User-Agent.
- @return {None} Writes two report or error lines to stdout.
- @satisfies REQ-003, REQ-075, REQ-084, REQ-091, DES-020

### fn `def check_for_updates(current_version: str) -> None` (L318-354)
- @brief Execute the startup PyPI registry version check.
- @details Applies cooldown gating unless the current CLI invocation requests `--version` or `--ver`, performs the PyPI latest-version HTTP request, prints a bright-green update line for newer releases, persists a 3600-second success cooldown or an 86400-second request-error cooldown for every request outcome, prints bright-red request errors, and suppresses propagation of non-HTTP request exceptions. Complexity O(1) excluding network latency and JSON parsing.
- @param current_version {str} Installed package version string.
- @return {None} No return value.
- @throws {urllib.error.HTTPError} Internally handled and converted to output.
- @satisfies PRJ-004, DES-004, DES-005, DES-006, DES-018, REQ-003, REQ-059, REQ-060, REQ-061

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|22||
|`OWNER`|var|pub|23||
|`REPOSITORY`|var|pub|24||
|`IDLE_DELAY`|var|pub|25||
|`HTTP_ERROR_IDLE_DELAY`|var|pub|26||
|`HTTP_TIMEOUT`|var|pub|27||
|`GITHUB_API_URL`|var|pub|28||
|`PYPI_API_URL`|var|pub|29||
|`CACHE_DIR`|var|pub|30||
|`IDLE_TIME_FILE`|var|pub|31||
|`BRIGHT_GREEN`|var|pub|33||
|`BRIGHT_RED`|var|pub|34||
|`RESET`|var|pub|35||
|`_read_idle_config`|fn|priv|38-56|def _read_idle_config() -> dict[str, object] | None|
|`_write_idle_config`|fn|priv|57-86|def _write_idle_config(last_check_ts: float, idle_delay_s...|
|`_is_forced_version_check`|fn|priv|87-99|def _is_forced_version_check() -> bool|
|`_format_request_error`|fn|priv|100-122|def _format_request_error(error: Exception) -> str|
|`_handle_request_error`|fn|priv|123-139|def _handle_request_error(last_check_ts: float, error: Ex...|
|`_should_check`|fn|priv|140-161|def _should_check(force_check: bool = False) -> bool|
|`_parse_version`|fn|priv|162-175|def _parse_version(version_value: str) -> tuple[int, ...]|
|`_compare_versions`|fn|priv|176-193|def _compare_versions(current: str, latest: str) -> bool|
|`_fetch_json_payload`|fn|priv|194-195|def _fetch_json_payload(|
|`fetch_pypi_latest_version`|fn|pub|219-239|def fetch_pypi_latest_version(current_version: str) -> str|
|`fetch_github_latest_release`|fn|pub|240-260|def fetch_github_latest_release(current_version: str) -> str|
|`BRIGHT_GREEN`|var|pub|261||
|`BRIGHT_RED`|var|pub|262||
|`RESET`|var|pub|263||
|`REPORT_LABEL_WIDTH`|var|pub|270||
|`format_version_report_line`|fn|pub|273-287|def format_version_report_line(label: str, value: str) ->...|
|`print_remote_latest_versions`|fn|pub|288-317|def print_remote_latest_versions(current_version: str) ->...|
|`check_for_updates`|fn|pub|318-354|def check_for_updates(current_version: str) -> None|

