#!/usr/bin/env python3
"""@brief Shared CLI utility helpers for platform, subprocess, and output handling.

@details Provides reusable terminal formatting utilities, project-root
resolution, platform detection with runtime OS caching, command availability
checks, and terminal-state restoration primitives used by CLI command wrappers.
@satisfies CTN-003, CTN-005, DES-002, REQ-047, REQ-055, REQ-056, REQ-064, REQ-065
"""

import os
import sys
import subprocess
import shutil
import shlex
from pathlib import Path
from typing import overload

try:
    import termios
except ImportError:
    termios = None

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

## @var _RUNTIME_OS
#  @brief Cached normalized runtime operating-system token.
#  @details Initialized on first detection and reused to guarantee stable
#  startup-level OS semantics across command execution flow.
#  @satisfies DES-002, REQ-047
_RUNTIME_OS = None

## @var _MOUSE_OFF_ESCAPE_SEQUENCE
#  @brief Escape-sequence payload that disables known xterm mouse-reporting modes.
#  @details Concatenates CSI mode-off controls for legacy X10 mode (`?9l`) and
#  common xterm mouse tracking modes (`?1000l`..`?1016l`).
#  @satisfies REQ-064, REQ-065
_MOUSE_OFF_ESCAPE_SEQUENCE = (
    "\x1b[?9l"
    "\x1b[?1000l"
    "\x1b[?1001l"
    "\x1b[?1002l"
    "\x1b[?1003l"
    "\x1b[?1004l"
    "\x1b[?1005l"
    "\x1b[?1006l"
    "\x1b[?1007l"
    "\x1b[?1015l"
    "\x1b[?1016l"
)


def color_enabled():
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def c(text, color):
    if color_enabled():
        return f"{color}{text}{RESET}"
    return str(text)


def print_info(msg):
    print(c(f"[INFO] {msg}", BRIGHT_BLUE + BOLD))


def print_error(msg):
    print(c(f"[ERROR] {msg}", BRIGHT_RED + BOLD), file=sys.stderr)


def print_warn(msg):
    print(c(f"[WARN] {msg}", BRIGHT_YELLOW + BOLD), file=sys.stderr)


def print_success(msg):
    print(c(f"[OK] {msg}", BRIGHT_GREEN + BOLD))


def get_project_root():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def require_project_root():
    require_commands("git")
    root = get_project_root()
    if root is None:
        print_error("Cannot determine the project root. Are you inside a git repository?")
        sys.exit(1)
    return root


def detect_runtime_os():
    """@brief Detect and cache runtime operating-system token.

    @details Normalizes `sys.platform` into deterministic categories
    (`windows`, `linux`, `darwin`, `other`) and stores the result in module
    cache for subsequent calls. Time complexity O(1).
    @return {str} Normalized runtime operating-system token.
    @satisfies DES-002, REQ-047
    """

    global _RUNTIME_OS
    platform_token = sys.platform.lower()
    if platform_token.startswith("win"):
        _RUNTIME_OS = "windows"
    elif platform_token.startswith("linux"):
        _RUNTIME_OS = "linux"
    elif platform_token.startswith("darwin"):
        _RUNTIME_OS = "darwin"
    else:
        _RUNTIME_OS = "other"
    return _RUNTIME_OS


def get_runtime_os():
    """@brief Return cached runtime operating-system token.

    @details Lazily initializes the cache via `detect_runtime_os` when unset,
    preserving a single startup-consistent OS classification.
    @return {str} Normalized runtime operating-system token.
    @satisfies DES-002, REQ-047
    """

    if _RUNTIME_OS is None:
        return detect_runtime_os()
    return _RUNTIME_OS


def is_windows():
    """@brief Check whether runtime operating system is Windows.

    @details Evaluates cached runtime token from `get_runtime_os`.
    @return {bool} `True` when runtime OS is Windows; otherwise `False`.
    @satisfies DES-013, REQ-008, REQ-047
    """

    return get_runtime_os() == "windows"


def is_linux():
    """@brief Check whether runtime operating system is Linux.

    @details Evaluates cached runtime token from `get_runtime_os`.
    @return {bool} `True` when runtime OS is Linux; otherwise `False`.
    @satisfies CTN-004, REQ-004, REQ-005, REQ-047
    """

    return get_runtime_os() == "linux"


def _is_executable_file(path: Path) -> bool:
    """@brief Validate executable-file capability for a filesystem path.

    @details Expands user-home markers, checks path kind, and applies platform
    executable checks. On Windows, missing-extension candidates are validated
    against `PATHEXT` suffixes.
    @param path {Path} Candidate executable filesystem path.
    @return {bool} `True` when the path resolves to an executable file.
    @satisfies CTN-003, REQ-055
    """

    return _resolve_executable_file(path) is not None


def _resolve_executable_file(path: Path) -> Path | None:
    """@brief Resolve an executable filesystem path for the runtime OS.

    @details Expands user-home markers and resolves Windows extension-less
    candidates through `PATHEXT` fallback checks.
    @param path {Path} Candidate executable filesystem path.
    @return {Path | None} Resolved executable path when runnable, else `None`.
    @satisfies CTN-003, REQ-055
    """

    expanded = path.expanduser()
    if expanded.suffix:
        if expanded.is_file() and os.access(str(expanded), os.X_OK):
            return expanded
        return None

    if expanded.is_file() and os.access(str(expanded), os.X_OK):
        return expanded

    if get_runtime_os() != "windows":
        return None

    path_ext = os.environ.get("PATHEXT", ".EXE;.CMD;.BAT;.COM")
    for ext in [item for item in path_ext.split(";") if item]:
        candidate = Path(f"{expanded}{ext}")
        if candidate.is_file() and os.access(str(candidate), os.X_OK):
            return candidate
    return None


def resolve_executable_command(command: str) -> str | None:
    """@brief Resolve a runnable command token to an executable path.

    @details Accepts command names or executable paths and returns the concrete
    runnable executable path when available on the current runtime platform.
    @param command {str} Command token or filesystem path to executable.
    @return {str | None} Resolved executable path or `None` when not runnable.
    @satisfies CTN-003, REQ-055
    """

    if not isinstance(command, str) or not command.strip():
        return None

    normalized = command.strip()
    path_like = os.sep in normalized or (os.altsep is not None and os.altsep in normalized)
    if path_like or Path(normalized).is_absolute():
        resolved_path = _resolve_executable_file(Path(normalized))
        return str(resolved_path) if resolved_path is not None else None

    return shutil.which(normalized)


def is_executable_command(command: str) -> bool:
    """@brief Determine whether an external command is executable on runtime OS.

    @details Accepts command names or executable paths. Name-based checks use
    `PATH` resolution via `shutil.which`; path-based checks verify executable
    file metadata, including Windows `PATHEXT` variants.
    @param command {str} Command token or filesystem path to executable.
    @return {bool} `True` when command is executable; otherwise `False`.
    @satisfies CTN-003, REQ-055
    """

    return resolve_executable_command(command) is not None


def command_exists(cmd):
    return is_executable_command(cmd)


@overload
def require_commands(cmd: str, /) -> str:
    ...


@overload
def require_commands(cmd1: str, cmd2: str, /, *cmds: str) -> list[str]:
    ...


def require_commands(*cmds: str) -> str | list[str]:
    resolved = []
    for cmd in cmds:
        resolved_cmd = resolve_executable_command(cmd)
        if resolved_cmd is None:
            print_error(f"Command not executable: {cmd}")
            sys.exit(1)
        resolved.append(resolved_cmd)
    if len(resolved) == 1:
        return resolved[0]
    return resolved


def _is_shell_assignment_token(token):
    """@brief Check whether a token is a shell variable assignment.

    @details Matches `NAME=value` form where `NAME` obeys shell identifier
    syntax and therefore does not represent an executable token.
    @param token {str} Shell token candidate.
    @return {bool} `True` when token is an assignment expression.
    @satisfies REQ-056
    """

    if "=" not in token:
        return False
    key = token.split("=", 1)[0]
    return key.replace("_", "a").isalnum() and not key[0].isdigit()


def extract_shell_executables(command_line):
    """@brief Extract executable tokens from a shell command line.

    @details Tokenizes command line using runtime-OS splitting mode and returns
    ordered unique executable candidates at command boundaries (`&&`, `||`,
    `;`, `|`) including wrapper commands such as `sudo`.
    @param command_line {str} Raw shell command line.
    @return {list[str]} Ordered executable token list.
    @satisfies REQ-056
    """

    if not command_line.strip():
        return []
    try:
        tokens = shlex.split(command_line, posix=get_runtime_os() != "windows")
    except ValueError:
        tokens = command_line.split()

    boundaries = {"&&", "||", ";", "|"}
    wrapper_commands = {"sudo", "env", "command", "nohup", "time"}
    executables = []
    expect_executable = True

    for token in tokens:
        if token in boundaries:
            expect_executable = True
            continue
        if not expect_executable:
            continue
        if _is_shell_assignment_token(token):
            continue
        executables.append(token)
        expect_executable = token in wrapper_commands

    seen = set()
    ordered = []
    for token in executables:
        if token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered


def require_shell_command_executables(command_line):
    """@brief Validate executable availability for a shell command line.

    @details Extracts executable tokens from `command_line`, validates each
    token via `is_executable_command`, prints deterministic error with missing
    command name, and terminates process on first failure.
    @param command_line {str} Raw shell command line.
    @return {None} Process exits on validation failure.
    @satisfies REQ-056
    """

    for token in extract_shell_executables(command_line):
        if not is_executable_command(token):
            print_error(f"Command not executable: {token}")
            sys.exit(1)


def _is_tty_stream(stream):
    """@brief Determine whether a stream is an attached TTY.

    @details Performs capability checks (`isatty`, callable) and returns
    deterministic boolean without raising on unsupported stream objects.
    Time complexity O(1).
    @param stream {object} Stream-like object (stdin/stdout/stderr candidate).
    @return {bool} `True` when stream supports and reports TTY attachment.
    @satisfies REQ-064
    """

    isatty = getattr(stream, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty())
    except OSError:
        return False


def capture_terminal_state():
    """@brief Capture current stdin terminal attributes when available.

    @details Reads current TTY attributes via `termios.tcgetattr` only on
    runtimes exposing `termios` and when stdin is a TTY. Returns `None` when
    attributes are unavailable. Time complexity O(1).
    @return {list[object] | None} Saved TTY attributes for later restoration.
    @satisfies REQ-064
    """

    if termios is None or not _is_tty_stream(sys.stdin):
        return None
    try:
        stdin_fd = sys.stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return None
    tcgetattr = getattr(termios, "tcgetattr", None)
    if not callable(tcgetattr):
        return None
    try:
        return tcgetattr(stdin_fd)
    except OSError:
        return None


def reset_terminal_state(saved_tty=None):
    """@brief Restore terminal raw/cbreak and mouse-tracking state.

    @details Restores previously captured stdin termios attributes when present,
    writes `_MOUSE_OFF_ESCAPE_SEQUENCE` (`?9l`, `?1000l`, `?1001l`, `?1002l`,
    `?1003l`, `?1004l`, `?1005l`, `?1006l`, `?1007l`, `?1015l`, `?1016l`) to
    TTY stdout, and best-effort runs `stty sane` for Git Bash/Unix-compatible
    terminals. Failures are ignored to preserve wrapper exit semantics. Time
    complexity O(1).
    @param saved_tty {list[object] | None} Attributes from `capture_terminal_state`.
    @return {None} Performs best-effort terminal-state restoration.
    @satisfies REQ-064, REQ-065
    """

    tcsetattr = None
    tcsa_drain = None
    if saved_tty is not None and termios is not None and _is_tty_stream(sys.stdin):
        tcsetattr = getattr(termios, "tcsetattr", None)
        tcsa_drain = getattr(termios, "TCSADRAIN", None)
    if (
        saved_tty is not None
        and _is_tty_stream(sys.stdin)
        and callable(tcsetattr)
        and tcsa_drain is not None
    ):
        try:
            tcsetattr(sys.stdin.fileno(), tcsa_drain, saved_tty)
        except (AttributeError, OSError, ValueError):
            pass

    if _is_tty_stream(sys.stdout):
        try:
            sys.stdout.write(_MOUSE_OFF_ESCAPE_SEQUENCE)
            sys.stdout.flush()
        except OSError:
            pass

    if _is_tty_stream(sys.stdin):
        try:
            subprocess.run(
                ["stty", "sane"],
                stdin=sys.stdin,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            pass


def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)
