#!/usr/bin/env python3
"""@brief NPM bootstrap and Trusted Publishing registration command.

@details Python port of the legacy `bin/npm-bootstrap-trust.sh` script.
Executes the five-phase pipeline: npmjs authentication check, package-name
availability check, temporary placeholder package creation, `bootstrap`
dist-tag publication, and GitHub trusted-publisher registration followed by
trust-list verification. Every mutating step fails fast and the temporary
directory is removed on every exit path.
@satisfies PRJ-008, DES-069, REQ-174, REQ-175, REQ-176, REQ-177, REQ-178,
REQ-179, REQ-180, REQ-181
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from shell_scripts.utils import print_error, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Bootstrap a new npm package and register its GitHub trusted publisher."

## @var REGISTRY
#  @brief Canonical npm registry URL used by every npm invocation.
#  @details Passed as `--registry=<value>` so operations never depend on the
#  ambient npm registry configuration.
#  @satisfies REQ-177
REGISTRY = "https://registry.npmjs.org/"

## @var MIN_NODE_VERSION
#  @brief Minimum supported Node.js version tuple `(22, 14, 0)`.
#  @details Versions comparing lower abort the command.
#  @satisfies REQ-176
MIN_NODE_VERSION = (22, 14, 0)

## @var MIN_NPM_VERSION
#  @brief Minimum supported npm version tuple `(11, 15, 0)`.
#  @details Versions comparing lower abort the command.
#  @satisfies REQ-176
MIN_NPM_VERSION = (11, 15, 0)

## @var NPM_NAME_PATTERN
#  @brief Conservative npm-name validation patterns.
#  @details Tuple of two anchored regexes: unscoped `^[a-z0-9][a-z0-9._~-]*$`
#  and scoped `^@[a-z0-9][a-z0-9._~-]*/[a-z0-9][a-z0-9._~-]*$`; the first
#  full match accepts the name.
#  @satisfies REQ-175
NPM_NAME_PATTERN = (
    re.compile(r"^[a-z0-9][a-z0-9._~-]*$"),
    re.compile(r"^@[a-z0-9][a-z0-9._~-]*/[a-z0-9][a-z0-9._~-]*$"),
)

## @var GITHUB_REPO_PATTERN
#  @brief Anchored `owner/repo` validation regex
#  `^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$`.
#  @details Repository tokens MUST NOT be URLs or carry extra slashes.
#  @satisfies REQ-175
GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$")

## @var WORKFLOW_FILE_PATTERN
#  @brief Anchored bare workflow-filename regex
#  `^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$`.
#  @details Rejects paths, directory components, and unsupported extensions.
#  @satisfies REQ-175
WORKFLOW_FILE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.(yml|yaml)$")

## @var VERSION_PATTERN
#  @brief Anchored strict `X.Y.Z` semantic-version regex.
#  @details Used to parse both `node --version` and `npm --version` output;
#  malformed values abort the version gate.
#  @satisfies REQ-176
VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class _UsageParser(argparse.ArgumentParser):
    """@brief `argparse` parser variant preserving the legacy exit code.

    @details Overrides `error` so usage errors print the message plus usage
    text to stderr and terminate with exit code `1`, matching the legacy
    script `usage(1)`/`die` semantics instead of the argparse default `2`.
    @satisfies REQ-174
    """

    def error(self, message):
        """@brief Terminate argument parsing with the legacy failure contract.

        @details Prints the bare message to stderr, then the usage text, then
        raises `SystemExit(1)`.
        @param message {str} Parsing error description.
        @return {None} Never returns; raises `SystemExit`.
        @throws {SystemExit} Always exit code `1`.
        @satisfies REQ-174
        """
        self.print_usage(sys.stderr)
        print_error(message)
        self.exit(1)


def _build_parser():
    """@brief Build the `npm-bootstrap-trust` argument parser.

    @details Registers required `-p/--package`, `-r/--repo`, and
    `-f/--workflow` options plus the default `-h/--help` action on the
    `_UsageParser` variant.
    @return {_UsageParser} Configured parser instance.
    @satisfies REQ-174
    """
    parser = _UsageParser(
        description=(
            "Bootstrap a new npm package with a placeholder publish and register"
            " its GitHub Trusted Publisher configuration."
        ),
    )
    parser.add_argument("-p", "--package", required=True, help="New npm package name.")
    parser.add_argument(
        "-r", "--repo", required=True,
        help="GitHub repository in owner/repo format.",
    )
    parser.add_argument(
        "-f", "--workflow", required=True,
        help="Workflow file name inside .github/workflows/ (with .yml or .yaml).",
    )
    return parser


def _die(message):
    """@brief Print an error line and terminate with exit code `1`.

    @details Mirrors the legacy `die` helper using the shared `[ERROR]`
    stderr renderer.
    @param message {str} Failure description rendered after the `[ERROR]`
      prefix.
    @return {None} Never returns; raises `SystemExit`.
    @throws {SystemExit} Always exit code `1`.
    @satisfies REQ-174, REQ-175, REQ-176, REQ-177, REQ-178, REQ-179, REQ-180
    """
    print_error(message)
    sys.exit(1)


def _validate_inputs(package_name, github_repo, workflow_file):
    """@brief Validate the conservative package, repository, and workflow tokens.

    @details Applies `NPM_NAME_PATTERN` plus the 214-character limit, the
    `GITHUB_REPO_PATTERN` plus owner length at most 39 and owner not ending
    with `-`, and `WORKFLOW_FILE_PATTERN`, aborting with the legacy English
    diagnostics on the first failure.
    @param package_name {str} npm package name token.
    @param github_repo {str} GitHub `owner/repo` token.
    @param workflow_file {str} Bare workflow filename token.
    @return {None} Returns on full validation.
    @throws {SystemExit} Exit code `1` via `_die` on the first invalid token.
    @satisfies REQ-175
    """
    if not any(pattern.fullmatch(package_name) for pattern in NPM_NAME_PATTERN):
        _die("Invalid npm name (use lowercase letters, digits, dots, _, ~ and -; optional scope).")
    if len(package_name) > 214:
        _die("npm name too long (maximum 214 characters).")

    if not GITHUB_REPO_PATTERN.fullmatch(github_repo):
        _die("Invalid GitHub repository: use owner/repo, without URLs or extra slashes.")
    gh_owner = github_repo.split("/", 1)[0]
    if len(gh_owner) > 39 or gh_owner.endswith("-"):
        _die("Invalid GitHub owner.")

    if not WORKFLOW_FILE_PATTERN.fullmatch(workflow_file):
        _die("Invalid workflow: pass only the file name, e.g. publish.yml.")


def _parse_version(text):
    """@brief Parse one strict `X.Y.Z` version string.

    @details Applies `VERSION_PATTERN` after stripping an optional leading
    `v` and surrounding whitespace.
    @param text {str} Raw version output token.
    @return {tuple[int, int, int]|None} Numeric version tuple, or `None` when
      the token does not match the strict format.
    @satisfies REQ-176
    """
    match = VERSION_PATTERN.fullmatch(text.strip().lstrip("v"))
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _require_toolchain():
    """@brief Validate Node.js and npm presence plus minimum versions.

    @details Checks `node` and `npm` executables via `require_commands`,
    captures `node --version` and `npm --version`, parses both with
    `_parse_version`, and aborts when either executable reports a version
    lower than `MIN_NODE_VERSION` or `MIN_NPM_VERSION` respectively or an
    unparseable value.
    @return {None} Returns when the toolchain satisfies the version gate.
    @throws {SystemExit} Exit code `1` via `require_commands` on missing
      executables or via `_die` on incompatible versions.
    @satisfies REQ-176, CTN-003, REQ-056
    """
    require_commands("node", "npm")

    node_result = subprocess.run(
        ["node", "--version"], capture_output=True, text=True, check=False,
    )
    npm_result = subprocess.run(
        ["npm", "--version"], capture_output=True, text=True, check=False,
    )
    node_version = _parse_version(node_result.stdout) if node_result.returncode == 0 else None
    npm_version = _parse_version(npm_result.stdout) if npm_result.returncode == 0 else None
    node_ok = node_version is not None and node_version >= MIN_NODE_VERSION
    npm_ok = npm_version is not None and npm_version >= MIN_NPM_VERSION
    if not (node_ok and npm_ok):
        _die(
            "Incompatible versions: Node >= 22.14.0 and npm >= 11.15.0 required"
            f" (found Node {node_result.stdout.strip()}, npm {npm_result.stdout.strip()})."
        )


def _write_placeholder_package(temp_dir, package_name, github_repo):
    """@brief Write the placeholder `package.json` and `index.js` files.

    @details Creates a version `0.0.0` package declaring the placeholder
    description, the GitHub repository URL `git+https://github.com/<repo>.git`,
    the `index.js` file list, and public publishConfig pinned to `REGISTRY`;
    writes `module.exports = {};` into `index.js`.
    @param temp_dir {str|Path} Existing temporary package directory.
    @param package_name {str} Validated npm package name.
    @param github_repo {str} Validated GitHub `owner/repo` token.
    @return {None} Writes two files into `temp_dir`.
    @throws {OSError} Propagated on filesystem write failure.
    @satisfies REQ-179
    """
    package_json = (
        "{\n"
        f'  "name": "{package_name}",\n'
        '  "version": "0.0.0",\n'
        '  "description": "Initial placeholder to enable npm Trusted Publishing",\n'
        '  "main": "index.js",\n'
        '  "repository": {\n'
        '    "type": "git",\n'
        f'    "url": "git+https://github.com/{github_repo}.git"\n'
        "  },\n"
        '  "files": ["index.js"],\n'
        '  "publishConfig": {\n'
        '    "access": "public",\n'
        f'    "registry": "{REGISTRY}"\n'
        "  }\n"
        "}\n"
    )
    (Path(temp_dir) / "package.json").write_text(package_json, encoding="utf-8")
    (Path(temp_dir) / "index.js").write_text("module.exports = {};\n", encoding="utf-8")


def print_help(version):
    """@brief Print command-specific help text.

    @details Renders usage line, option list, and behavioral summary in
    English, following the shared command help layout.
    @param version {str} Current CLI version token rendered in the usage line.
    @return {None} Writes to stdout.
    @satisfies PRJ-002, REQ-174
    """
    print(f"Usage: {PROGRAM} npm-bootstrap-trust ({version})")
    print()
    print("npm-bootstrap-trust options:")
    print("  --help        - Show this help message.")
    print("  -p <package>  - New npm package name.")
    print("  -r <owner/repo> - GitHub repository in owner/repo format.")
    print("  -f <workflow.yml> - Workflow file name inside .github/workflows/.")
    print()
    print("Publishes a temporary 0.0.0 placeholder with dist-tag 'bootstrap' and")
    print("registers the GitHub Trusted Publisher for the package on npmjs.")


def run(args):
    """@brief Execute the five-phase npm bootstrap and trust pipeline.

    @details Phase order: `[1/5]` npmjs authentication via `npm whoami`;
    `[2/5]` package availability via `npm view <package>@* versions --json`,
    aborting on existing versions or a failure without an `E404` marker;
    `[3/5]` placeholder package creation in a fresh temporary directory;
    `[4/5]` publication with dist-tag `bootstrap` and public access;
    `[5/5]` GitHub trusted-publisher creation via `npm trust github` plus
    trust-list verification. The temporary directory is removed on every
    exit path; every failure aborts with exit code `1` and the exact legacy
    diagnostic semantics.
    @param args {list[str]} Command arguments (without the command token).
    @return {int} `0` after successful publication and trust verification.
    @throws {SystemExit} Exit code `1` on usage errors, invalid inputs,
      missing or incompatible toolchain, failed authentication, taken or
      unverifiable package name, failed publication, or failed trust
      creation/verification.
    @satisfies REQ-174, REQ-175, REQ-176, REQ-177, REQ-178, REQ-179, REQ-180,
    REQ-181
    """
    parser = _build_parser()
    opts = parser.parse_args(args)

    _validate_inputs(opts.package, opts.repo, opts.workflow)
    _require_toolchain()

    temp_dir = None
    try:
        print("[1/5] Verifying npmjs authentication...")
        whoami = subprocess.run(
            ["npm", "whoami", f"--registry={REGISTRY}"],
            capture_output=True, text=True, check=False,
        )
        if whoami.returncode != 0:
            _die(f"npmjs authentication unavailable. Run: npm login --registry={REGISTRY}")
        npm_user = whoami.stdout.strip()
        print(f"npm account: {npm_user}")
        print("NOTE: npm trust requires 2FA on the account and write permission on the package.")

        temp_dir = tempfile.mkdtemp(prefix="npm-bootstrap.")

        print("[2/5] Verifying that the package does not exist yet...")
        view = subprocess.run(
            ["npm", "view", f"{opts.package}@*", "versions", "--json", f"--registry={REGISTRY}"],
            capture_output=True, text=True, check=False,
        )
        if view.returncode == 0:
            _die(f"Package '{opts.package}' already exists: aborting to avoid unwanted publications.")
        if "E404" not in view.stderr:
            print(view.stderr, file=sys.stderr, end="")
            _die("Unable to reliably verify that the name is available.")

        print("[3/5] Creating the temporary placeholder package...")
        _write_placeholder_package(temp_dir, opts.package, opts.repo)

        print(f"[4/5] Publishing {opts.package}@0.0.0 with dist-tag bootstrap...")
        publish = subprocess.run(
            ["npm", "publish", "--tag=bootstrap", "--access=public", f"--registry={REGISTRY}"],
            cwd=temp_dir, check=False,
        )
        if publish.returncode != 0:
            _die("Initial publish failed. The trust was not created.")

        print("[5/5] Creating the GitHub Trusted Publisher...")
        trust = subprocess.run(
            [
                "npm", "trust", "github", opts.package,
                "--repo", opts.repo,
                "--file", opts.workflow,
                "--allow-publish",
                f"--registry={REGISTRY}",
            ],
            check=False,
        )
        if trust.returncode != 0:
            _die(
                f"Package '{opts.package}' published, but the trust was NOT created."
                " Configure it manually on npmjs.com or retry only the npm trust command."
            )

        print()
        print(f"Trust registered for {opts.package}:")
        trust_list = subprocess.run(
            ["npm", "trust", "list", opts.package, f"--registry={REGISTRY}"],
            check=False,
        )
        if trust_list.returncode != 0:
            _die(
                "Trust created by the command, but the configuration could not be"
                " read for later verification."
            )
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

    print()
    print(f"Operation completed: {opts.package}@0.0.0 published; trust creation command succeeded.")
    print("WARNING: the trust will be validated only after a successful OIDC publish")
    print("from the workflow within 2 days.")
    print("The GitHub repository/workflow are not created by this command.")
    return 0
