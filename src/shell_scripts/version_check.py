#!/usr/bin/env python3
"""@brief Update-check orchestration for shellscripts startup.

@details Performs cooldown-gated GitHub release checks, persists cache metadata
for every request outcome, and prints terminal-visible update or error status
lines. Successful requests apply the default cooldown. Request errors apply the
enlarged cooldown without aborting CLI startup continuity.
@satisfies PRJ-004, DES-002, DES-003, DES-004, DES-005, DES-006, REQ-003, REQ-059, REQ-060, REQ-061
"""

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROGRAM = "shellscripts"
OWNER = "Ogekuri"
REPOSITORY = "shellScripts"
IDLE_DELAY = 3600
HTTP_ERROR_IDLE_DELAY = 86400
HTTP_TIMEOUT = 2
GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"
CACHE_DIR = Path.home() / ".cache" / PROGRAM
IDLE_TIME_FILE = CACHE_DIR / "check_version_idle-time.json"

BRIGHT_GREEN = "\033[92m"
BRIGHT_RED = "\033[91m"
RESET = "\033[0m"


def _read_idle_config() -> dict[str, object] | None:
    """@brief Load cached cooldown metadata for the version check.

    @details Reads the cooldown JSON payload from the user cache directory.
    Absent files and unreadable JSON payloads resolve to `None`. Complexity:
    O(1) for fixed-size payload parsing.
    @return {dict[str, object] | None} Cached cooldown payload or `None`.
    @satisfies DES-003, REQ-059
    """

    if not IDLE_TIME_FILE.exists():
        return None
    try:
        with open(IDLE_TIME_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_idle_config(last_check_ts: float, idle_delay_seconds: int) -> None:
    """@brief Persist cooldown timestamps for the next version-check gate.

    @details Derives the idle-until timestamp from the supplied delay, writes
    both machine-readable timestamps and UTC-rendered strings, and stores the
    applied delay for downstream inspection. Complexity: O(1).
    @param last_check_ts {float} UNIX timestamp recorded for the current check.
    @param idle_delay_seconds {int} Cooldown duration applied after the check.
    @return {None} No return value.
    @throws {OSError} Propagated when cache directory creation or file write fails.
    @satisfies DES-003, DES-004, DES-005, REQ-061
    """

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    idle_until_ts = last_check_ts + idle_delay_seconds
    data = {
        "last_check_timestamp": last_check_ts,
        "last_check_human": datetime.fromtimestamp(
            last_check_ts, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "idle_delay_seconds": idle_delay_seconds,
        "idle_until_timestamp": idle_until_ts,
        "idle_until_human": datetime.fromtimestamp(
            idle_until_ts, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    with open(IDLE_TIME_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _is_forced_version_check() -> bool:
    """@brief Detect CLI flags that force the version-check HTTP request.

    @details Evaluates the live process argument vector and returns `True` when
    the current invocation requested `--version` or `--ver`. Complexity: O(N)
    where N is the number of CLI arguments.
    @return {bool} `True` when the request must bypass cooldown gating.
    @satisfies REQ-003, REQ-059
    """

    return any(arg in ("--version", "--ver") for arg in sys.argv[1:])


def _format_request_error(error: Exception) -> str:
    """@brief Convert a request exception into terminal output detail text.

    @details Returns a stable, parser-friendly error descriptor for HTTP and
    non-HTTP request failures. HTTP errors preserve the status code. Non-HTTP
    errors expose the exception type and optional message. Complexity: O(1).
    @param error {Exception} Request failure captured during update checking.
    @return {str} Error detail suffix without terminal color codes.
    @satisfies DES-005, DES-006, REQ-061
    """

    if isinstance(error, urllib.error.HTTPError):
        if error.code in (403, 429):
            return f"rate limit exceeded (HTTP {error.code})"
        return f"HTTP {error.code}"

    error_type = type(error).__name__
    error_message = str(error).strip()
    if error_message:
        return f"{error_type}: {error_message}"
    return error_type


def _handle_request_error(last_check_ts: float, error: Exception) -> None:
    """@brief Persist cooldown metadata and print the request error line.

    @details Applies the fixed HTTP-error cooldown, updates the cooldown JSON,
    and emits a bright-red terminal line for the supplied request failure.
    Complexity: O(1) excluding filesystem latency.
    @param last_check_ts {float} UNIX timestamp recorded for the failed check.
    @param error {Exception} Request failure captured during update checking.
    @return {None} No return value.
    @throws {OSError} Propagated when cache directory creation or file write fails.
    @satisfies DES-003, DES-005, DES-006, REQ-061
    """

    _write_idle_config(last_check_ts, HTTP_ERROR_IDLE_DELAY)
    print(f"{BRIGHT_RED}Update check failed: {_format_request_error(error)}.{RESET}")


def _should_check(force_check: bool = False) -> bool:
    """@brief Evaluate whether the GitHub version-check request should run.

    @details Forces execution when `force_check` is `True`; otherwise reads the
    cached idle-until timestamp and compares it against the current wall-clock
    time. Complexity: O(1).
    @param force_check {bool} Cooldown-bypass flag derived from CLI arguments.
    @return {bool} `True` when the HTTP request is allowed or forced.
    @satisfies REQ-003, REQ-059
    """

    if force_check:
        return True
    config = _read_idle_config()
    if config is None:
        return True
    idle_until = config.get("idle_until_timestamp", 0)
    if not isinstance(idle_until, (int, float)):
        return True
    return time.time() >= idle_until


def _parse_version(version_value: str) -> tuple[int, ...]:
    """@brief Convert a semantic-version string into an integer tuple.

    @details Strips a leading `v` prefix, splits by `.`, and converts each
    segment to `int`. Complexity: O(N) where N is the number of segments.
    @param version_value {str} Raw semantic version token.
    @return {tuple[int, ...]} Parsed numeric version segments.
    @throws {ValueError} Propagated when a segment is not numeric.
    @satisfies PRJ-004
    """

    return tuple(int(part) for part in version_value.strip().lstrip("v").split("."))


def _compare_versions(current: str, latest: str) -> bool:
    """@brief Compare installed and latest semantic versions.

    @details Parses both version strings into integer tuples and returns
    `True` only when `latest` is newer than `current`. Invalid inputs collapse
    to `False`. Complexity: O(N).
    @param current {str} Installed package version.
    @param latest {str} Latest GitHub release version.
    @return {bool} `True` when the remote version is newer.
    @satisfies PRJ-004, REQ-060
    """

    try:
        return _parse_version(latest) > _parse_version(current)
    except (ValueError, AttributeError):
        return False


def check_for_updates(current_version: str) -> None:
    """@brief Execute the startup GitHub release version check.

    @details Applies cooldown gating unless the current CLI invocation requests
    `--version` or `--ver`, performs the latest-release HTTP request, prints a
    bright-green update line for newer releases, persists a 3600-second success
    cooldown or an 86400-second request-error cooldown for every request
    outcome, prints bright-red request errors, and suppresses propagation of
    non-HTTP request exceptions. Complexity: O(1) excluding network latency and
    JSON parsing.
    @param current_version {str} Installed package version string.
    @return {None} No return value.
    @throws {urllib.error.HTTPError} Internally handled and converted to output.
    @satisfies PRJ-004, DES-004, DES-005, DES-006, REQ-003, REQ-059, REQ-060, REQ-061
    """

    if not _should_check(force_check=_is_forced_version_check()):
        return

    now = time.time()

    try:
        req = urllib.request.Request(GITHUB_API_URL)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", f"{PROGRAM}/{current_version}")
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            latest = data.get("tag_name", "").lstrip("v")

            if latest and _compare_versions(current_version, latest):
                print(
                    f"{BRIGHT_GREEN}Versione Disponibile: {latest} | "
                    f"Versione Installata: {current_version}{RESET}"
                )

            _write_idle_config(now, IDLE_DELAY)

    except urllib.error.HTTPError as error:
        _handle_request_error(now, error)
    except Exception as error:
        _handle_request_error(now, error)
