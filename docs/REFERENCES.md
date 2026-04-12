# Files Structure
```
.
├── scripts
│   └── s.sh
└── src
    └── shell_scripts
        ├── __init__.py
        ├── __main__.py
        ├── commands
        │   ├── __init__.py
        │   ├── _dc_common.py
        │   ├── ai_install.py
        │   ├── bin_links.py
        │   ├── claude.py
        │   ├── clean.py
        │   ├── codex.py
        │   ├── copilot.py
        │   ├── dicom2jpg.py
        │   ├── dicomviewer.py
        │   ├── diff_cmd.py
        │   ├── doxygen_cmd.py
        │   ├── edit_cmd.py
        │   ├── gemini.py
        │   ├── kiro.py
        │   ├── opencode.py
        │   ├── pdf_crop.py
        │   ├── pdf_merge.py
        │   ├── pdf_split_by_format.py
        │   ├── pdf_split_by_toc.py
        │   ├── pdf_tiler_090.py
        │   ├── pdf_tiler_100.py
        │   ├── pdf_toc_clean.py
        │   ├── pi.py
        │   ├── req_cmd.py
        │   ├── tests_cmd.py
        │   ├── ubuntu_dark_theme.py
        │   ├── venv_cmd.py
        │   ├── video2h264.py
        │   ├── video2h265.py
        │   ├── view_cmd.py
        │   ├── vscode_cmd.py
        │   └── vsinsider_cmd.py
        ├── config.py
        ├── core.py
        ├── utils.py
        └── version_check.py
```

# s.sh | Shell | 51L | 6 symbols | 0 imports | 9 comments
> Path: `scripts/s.sh`

## Definitions

- fn `normalize_path() {` (L11)
- @brief Normalize a path for cross-platform comparison.
- @details Uses cygpath when available (Git Bash/MSYS) and falls back to
canonical directory resolution via cd/pwd -P.
- @param $1 Raw path to normalize.
- @return Prints the normalized path to stdout.
- var `SCRIPT_PATH=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd -P)` (L32)
- var `BASE_DIR=$(CDPATH= cd -- "${SCRIPT_PATH}/.." 2>/dev/null && pwd -P)` (L33)
- var `PROJECT_ROOT=$(git -C "${BASE_DIR}" rev-parse --show-toplevel 2>/dev/null)` (L35)
- var `PROJECT_ROOT=$(normalize_path "${PROJECT_ROOT}")` (L41)
- var `BASE_DIR=$(normalize_path "${BASE_DIR}")` (L42)
## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`normalize_path`|fn||11|normalize_path()|
|`SCRIPT_PATH`|var||32||
|`BASE_DIR`|var||33||
|`PROJECT_ROOT`|var||35||
|`PROJECT_ROOT`|var||41||
|`BASE_DIR`|var||42||


---

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

# __init__.py | Python | 81L | 2 symbols | 2 imports | 8 comments
> Path: `src/shell_scripts/commands/__init__.py`

## Imports
```
import importlib
from types import ModuleType
```

## Definitions

### fn `def get_command(name: str) -> ModuleType | None` (L51-66)
- @brief Static map from CLI command names to importable module paths.
- @brief Resolve one CLI command token to its command module.
- @details Enables lazy command loading and deterministic command exposure.
Removing an entry removes command discoverability and dispatch reachability.
- @details Performs O(1) dictionary lookup on `_COMMAND_MODULES`; returns `None` for unknown tokens; imports target module lazily only on hit.
- @param name {str} CLI command token.
- @return {ModuleType|None} Imported command module for known token; `None` otherwise.
- @throws {ImportError} If module path exists in map but import fails.
- @satisfies PRJ-003, DES-001
- @satisfies PRJ-001, DES-001, DES-008, REQ-057, REQ-058

### fn `def get_all_commands() -> dict[str, str]` (L67-81)
- @brief Build command-description index for help rendering.
- @details Iterates sorted command keys for stable output ordering; imports each module via `get_command`; extracts `DESCRIPTION` or empty string. Time complexity O(N log N) for N commands due to key sorting.
- @return {dict[str, str]} Mapping `command_name -> description`.
- @throws {ImportError} If any mapped command module import fails.
- @satisfies PRJ-002, DES-001, DES-008, REQ-057, REQ-058

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_command`|fn|pub|51-66|def get_command(name: str) -> ModuleType | None|
|`get_all_commands`|fn|pub|67-81|def get_all_commands() -> dict[str, str]|


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

### fn `def dispatch(category_cmds, fallback_cmd, filepath, extra_args)` (L115-138)
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
|`dispatch`|fn|pub|115-138|def dispatch(category_cmds, fallback_cmd, filepath, extra...|


---

# ai_install.py | Python | 392L | 17 symbols | 13 imports | 10 comments
> Path: `src/shell_scripts/commands/ai_install.py`

## Imports
```
import json
import os
import platform
import subprocess
import shutil
import zipfile
import tempfile
from pathlib import Path
from shell_scripts.utils import (
import urllib.error
import urllib.request
import urllib.error
import urllib.request
```

## Definitions

- var `PROGRAM = "shellscripts"` (L29)
- var `DESCRIPTION = "Install AI CLI tools (Codex, Copilot, Gemini, OpenCode, Claude, Kiro)."` (L30)
- var `TOOLS = {` (L32)
- var `CLAUDE_BUCKET = (` (L51)
- var `CLAUDE_ARTIFACT_CANDIDATES = {` (L55)
- var `KIRO_CHANNEL_BASE_URL = "https://prod.download.cli.kiro.dev/stable"` (L60)
- var `KIRO_MANIFEST_URL = f"{KIRO_CHANNEL_BASE_URL}/latest/manifest.json"` (L61)
- var `KIRO_LINUX_VARIANT = "headless"` (L62)
### fn `def print_help(version)` (L65-87)
- @brief Render command help for `ai-install`.
- @details Prints supported selectors and execution contract for installer dispatch.
- @param version {str} CLI version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def _install_npm_tool(tool_key)` `priv` (L88-130)
- @brief Execute npm-based installer command for selected tool.
- @details Resolves base npm command from static tool mapping, prepends `sudo` when runtime OS is not Windows, and uses resolved `npm.cmd` path on Windows when available to avoid process-launch failures. For Windows Copilot installs, retries once after a non-zero first attempt to mitigate transient file-lock failures during binary replacement.
- @param tool_key {str} Tool identifier key from `TOOLS`.
- @return {None} Executes side effects and prints result messages.
- @satisfies DES-013, REQ-008, REQ-047, REQ-056

### fn `def _normalize_kiro_linux_arch(machine_token)` `priv` (L131-152)
- @brief Normalize machine architecture token for Kiro Linux packages.
- @details Maps runtime machine names into manifest architecture keys accepted by Kiro headless Linux ZIP entries. Raises explicit error for unknown architecture to avoid ambiguous package selection.
- @param machine_token {str} Raw `platform.machine()` token.
- @return {str} Normalized architecture token (`x86_64` or `aarch64`).
- @throws {RuntimeError} When architecture is not supported by Kiro installer.
- @satisfies REQ-010, REQ-067

### fn `def _detect_kiro_linux_libc()` `priv` (L153-168)
- @brief Detect Linux libc class token for Kiro package selection.
- @details Uses `platform.libc_ver()` to classify runtime libc as `musl` or `gnu`. Unknown or empty values default to `gnu` to keep deterministic package selection for glibc environments.
- @return {str} libc class token (`musl` or `gnu`).
- @satisfies REQ-010

### fn `def _resolve_kiro_linux_download_path(manifest, arch_token, libc_token)` `priv` (L169-214)
- @brief Resolve Kiro Linux ZIP download path from manifest metadata.
- @details Filters manifest packages by Linux OS, headless ZIP variant, runtime architecture, and runtime libc class reflected in target triple. Returns first matching `download` path and fails explicitly when no match exists.
- @param manifest {dict[str, object]} Parsed Kiro manifest JSON payload.
- @param arch_token {str} Normalized architecture token (`x86_64|aarch64`).
- @param libc_token {str} Normalized libc token (`gnu|musl`).
- @return {str} Relative download path from manifest `packages[].download`.
- @throws {RuntimeError} When no manifest package matches runtime filters.
- @satisfies DES-013, REQ-010

### fn `def _install_claude()` `priv` (L215-268)
- @brief Install Claude CLI by direct binary download.
- @details Downloads latest version metadata from configured bucket, resolves OS-specific Claude artifact candidates from runtime OS token, downloads the first available artifact, writes executable into `~/.claude/bin/claude`, and sets execute permissions on non-Windows runtimes.
- @return {None} Executes side effects and prints result messages.
- @throws {RuntimeError} When runtime OS has no configured package candidates.
- @throws {urllib.error.URLError} When metadata or artifact download fails.
- @throws {OSError} When destination write or permission update fails.
- @satisfies DES-013, REQ-009

### fn `def _install_kiro()` `priv` (L269-349)
- @brief Install Kiro CLI binaries by ZIP extraction flow.
- @details Rejects unsupported runtime OS values (`windows`, `darwin`) with explicit errors. On Linux, resolves runtime architecture/libc package from official stable manifest, downloads selected ZIP archive, extracts `kiro-cli*` binaries, and installs them into `~/.local/bin`.
- @return {None} Executes side effects and prints result messages.
- @throws {RuntimeError} When runtime OS is unsupported or manifest has no matching package.
- @throws {urllib.error.URLError} When archive download fails.
- @throws {json.JSONDecodeError} When manifest payload is malformed.
- @throws {zipfile.BadZipFile} When downloaded archive is invalid.
- @throws {OSError} When extraction/copy/permission updates fail.
- @satisfies DES-013, REQ-010, REQ-067

- var `ALL_INSTALLERS = {` (L350)
### fn `def run(args)` (L360-392)
- @brief Parse selectors and execute selected AI installer routines.
- @details Accepts explicit selectors or defaults to full installer set when omitted; rejects unknown selectors with return code `1`.
- @param args {list[str]} CLI selector tokens for installer filtering.
- @return {int} `0` on successful dispatch; `1` on unknown selector.
- @satisfies REQ-006, REQ-007

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|29||
|`DESCRIPTION`|var|pub|30||
|`TOOLS`|var|pub|32||
|`CLAUDE_BUCKET`|var|pub|51||
|`CLAUDE_ARTIFACT_CANDIDATES`|var|pub|55||
|`KIRO_CHANNEL_BASE_URL`|var|pub|60||
|`KIRO_MANIFEST_URL`|var|pub|61||
|`KIRO_LINUX_VARIANT`|var|pub|62||
|`print_help`|fn|pub|65-87|def print_help(version)|
|`_install_npm_tool`|fn|priv|88-130|def _install_npm_tool(tool_key)|
|`_normalize_kiro_linux_arch`|fn|priv|131-152|def _normalize_kiro_linux_arch(machine_token)|
|`_detect_kiro_linux_libc`|fn|priv|153-168|def _detect_kiro_linux_libc()|
|`_resolve_kiro_linux_download_path`|fn|priv|169-214|def _resolve_kiro_linux_download_path(manifest, arch_toke...|
|`_install_claude`|fn|priv|215-268|def _install_claude()|
|`_install_kiro`|fn|priv|269-349|def _install_kiro()|
|`ALL_INSTALLERS`|var|pub|350||
|`run`|fn|pub|360-392|def run(args)|


---

# bin_links.py | Python | 78L | 4 symbols | 3 imports | 1 comments
> Path: `src/shell_scripts/commands/bin_links.py`

## Imports
```
import sys
from pathlib import Path
from shell_scripts.utils import print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Create or update command symlinks in $HOME/bin."` (L8)
### fn `def print_help(version)` (L11-21)

### fn `def run(args)` (L22-78)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-21|def print_help(version)|
|`run`|fn|pub|22-78|def run(args)|


---

# claude.py | Python | 56L | 4 symbols | 3 imports | 10 comments
> Path: `src/shell_scripts/commands/claude.py`

## Imports
```
import subprocess
from pathlib import Path
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L17)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."` (L21)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version)` (L24-40)
- @brief Print command-specific help for `claude`.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; does not mutate process state.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L41-56)
- @brief Launch Claude CLI after external executable validation.
- @details Resolves project root, resolves user-local Claude executable path, validates executable availability, then executes command via subprocess.
- @param args {list[str]} Additional CLI args forwarded to Claude.
- @return {int} Child process return code.
- @satisfies REQ-017, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|17||
|`DESCRIPTION`|var|pub|21||
|`print_help`|fn|pub|24-40|def print_help(version)|
|`run`|fn|pub|41-56|def run(args)|


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

### fn `def run(args)` (L34-98)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`CACHE_DIRS`|var|pub|11||
|`print_help`|fn|pub|25-33|def print_help(version)|
|`run`|fn|pub|34-98|def run(args)|


---

# codex.py | Python | 107L | 5 symbols | 5 imports | 11 comments
> Path: `src/shell_scripts/commands/codex.py`

## Imports
```
import os
import shutil
import subprocess
from pathlib import Path
from shell_scripts.utils import print_info, require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L23)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch OpenAI Codex CLI in the project context."` (L27)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version: str) -> None` (L30-45)
- @brief Print command-specific help for `codex`.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; does not mutate process state.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def _copy_auth_file(` `priv` (L46-49)

### fn `def run(args: list[str]) -> int` (L74-107)
- @brief Copy Codex auth file while replacing destination file or symlink.
- @brief Launch Codex CLI with project-scoped environment preparation.
- @details Ensures destination parent directory exists, removes an existing
destination entry when it is a file or symbolic link, then copies source
bytes to destination preserving metadata with `shutil.copy2`, then emits
one informational output line for copy evidence. Time complexity O(n) where
n is auth file size.
- @details Resolves project root, copies auth from home into project auth file, emits copy evidence output, sets `CODEX_HOME=<project-root>/.codex`, executes `codex --yolo` plus pass-through args through blocking subprocess run, then copies project auth back to home path in a `finally` block with reverse-direction copy evidence output.
- @param source_path {Path} Existing auth file source path.
- @param destination_path {Path} Auth file destination path to overwrite.
- @param direction_label {str} Copy direction descriptor shown in info output.
- @param args {list[str]} Additional CLI args forwarded to Codex.
- @return {None} Applies destination filesystem mutation.
- @return {int} Child process return code.
- @throws {OSError} If source read, destination unlink, or copy operation fails.
- @throws {OSError} Propagated for auth-file copy or process-launch failures.
- @satisfies REQ-043, REQ-044
- @satisfies REQ-014, REQ-043, REQ-044, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|23||
|`DESCRIPTION`|var|pub|27||
|`print_help`|fn|pub|30-45|def print_help(version: str) -> None|
|`_copy_auth_file`|fn|priv|46-49|def _copy_auth_file(|
|`run`|fn|pub|74-107|def run(args: list[str]) -> int|


---

# copilot.py | Python | 54L | 4 symbols | 2 imports | 10 comments
> Path: `src/shell_scripts/commands/copilot.py`

## Imports
```
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L16)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch GitHub Copilot CLI in the project context."` (L20)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version)` (L23-39)
- @brief Print command-specific help for `copilot`.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; does not mutate process state.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L40-54)
- @brief Launch Copilot CLI after external executable validation.
- @details Resolves project root, checks executable availability for `copilot`, then executes pass-through args through blocking subprocess run.
- @param args {list[str]} Additional CLI args forwarded to Copilot.
- @return {int} Child process return code.
- @satisfies REQ-015, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|16||
|`DESCRIPTION`|var|pub|20||
|`print_help`|fn|pub|23-39|def print_help(version)|
|`run`|fn|pub|40-54|def run(args)|


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

### fn `def run(args)` (L49-98)
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
|`run`|fn|pub|49-98|def run(args)|


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

### fn `def run(args)` (L48-83)
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
|`run`|fn|pub|48-83|def run(args)|


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

### fn `def run(args)` (L35-50)
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
|`run`|fn|pub|35-50|def run(args)|


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

### fn `def run(args)` (L99-159)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|11||
|`DESCRIPTION`|var|pub|12||
|`print_help`|fn|pub|15-24|def print_help(version)|
|`_supports_generate_markdown`|fn|priv|25-38|def _supports_generate_markdown()|
|`_write_doxyfile`|fn|priv|39-40|def _write_doxyfile(path, project_root, src_dir, doxygen_...|
|`_generate_markdown_fallback`|fn|priv|76-98|def _generate_markdown_fallback(xml_dir, markdown_dir)|
|`run`|fn|pub|99-159|def run(args)|


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

### fn `def run(args)` (L35-50)
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
|`run`|fn|pub|35-50|def run(args)|


---

# gemini.py | Python | 54L | 4 symbols | 2 imports | 10 comments
> Path: `src/shell_scripts/commands/gemini.py`

## Imports
```
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L16)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch Google Gemini CLI in the project context."` (L20)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version)` (L23-39)
- @brief Print command-specific help for `gemini`.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; does not mutate process state.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L40-54)
- @brief Launch Gemini CLI after external executable validation.
- @details Resolves project root, checks executable availability for `gemini`, then executes pass-through args through blocking subprocess run.
- @param args {list[str]} Additional CLI args forwarded to Gemini.
- @return {int} Child process return code.
- @satisfies REQ-016, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|16||
|`DESCRIPTION`|var|pub|20||
|`print_help`|fn|pub|23-39|def print_help(version)|
|`run`|fn|pub|40-54|def run(args)|


---

# kiro.py | Python | 54L | 4 symbols | 2 imports | 10 comments
> Path: `src/shell_scripts/commands/kiro.py`

## Imports
```
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L16)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch Kiro CLI in the project context."` (L20)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version)` (L23-39)
- @brief Print command-specific help for `kiro`.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; does not mutate process state.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L40-54)
- @brief Launch Kiro CLI after external executable validation.
- @details Resolves project root, validates executable availability for `kiro-cli`, then executes pass-through args through blocking subprocess run.
- @param args {list[str]} Additional CLI args forwarded to Kiro.
- @return {int} Child process return code.
- @satisfies REQ-019, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|16||
|`DESCRIPTION`|var|pub|20||
|`print_help`|fn|pub|23-39|def print_help(version)|
|`run`|fn|pub|40-54|def run(args)|


---

# opencode.py | Python | 54L | 4 symbols | 2 imports | 10 comments
> Path: `src/shell_scripts/commands/opencode.py`

## Imports
```
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L16)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch OpenCode CLI in the project context."` (L20)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version)` (L23-39)
- @brief Print command-specific help for `opencode`.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; does not mutate process state.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def run(args)` (L40-54)
- @brief Launch OpenCode CLI after external executable validation.
- @details Resolves project root, checks executable availability for `opencode`, then executes pass-through args through blocking subprocess run.
- @param args {list[str]} Additional CLI args forwarded to OpenCode.
- @return {int} Child process return code.
- @satisfies REQ-018, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|16||
|`DESCRIPTION`|var|pub|20||
|`print_help`|fn|pub|23-39|def print_help(version)|
|`run`|fn|pub|40-54|def run(args)|


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

### fn `def run(args)` (L52-180)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-22|def print_help(version)|
|`_parse_bookmarks`|fn|priv|23-43|def _parse_bookmarks(dump_file)|
|`_get_num_pages`|fn|priv|44-51|def _get_num_pages(dump_file)|
|`run`|fn|pub|52-180|def run(args)|


---

# pdf_split_by_format.py | Python | 243L | 9 symbols | 5 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_split_by_format.py`

## Imports
```
import os
import re
import subprocess
import tempfile
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L9)
- var `DESCRIPTION = "Split PDF into parts by page format changes."` (L10)
### fn `def print_help(version)` (L13-22)

### fn `def _get_page_formats(pdf, total_pages)` `priv` (L23-37)

### fn `def _get_total_pages(pdf)` `priv` (L38-50)

### fn `def _has_toc(pdf)` `priv` (L51-69)

### fn `def _extract_toc_for_range(data_file, start, end)` `priv` (L70-104)

### fn `def _apply_toc(output_file, toc_content)` `priv` (L105-137)

### fn `def run(args)` (L138-243)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|9||
|`DESCRIPTION`|var|pub|10||
|`print_help`|fn|pub|13-22|def print_help(version)|
|`_get_page_formats`|fn|priv|23-37|def _get_page_formats(pdf, total_pages)|
|`_get_total_pages`|fn|priv|38-50|def _get_total_pages(pdf)|
|`_has_toc`|fn|priv|51-69|def _has_toc(pdf)|
|`_extract_toc_for_range`|fn|priv|70-104|def _extract_toc_for_range(data_file, start, end)|
|`_apply_toc`|fn|priv|105-137|def _apply_toc(output_file, toc_content)|
|`run`|fn|pub|138-243|def run(args)|


---

# pdf_split_by_toc.py | Python | 197L | 8 symbols | 5 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_split_by_toc.py`

## Imports
```
import os
import re
import subprocess
import tempfile
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L9)
- var `DESCRIPTION = "Split PDF into chapters by TOC level-1 entries."` (L10)
### fn `def print_help(version)` (L13-20)

### fn `def _parse_level1_toc(dump_content)` `priv` (L21-39)

### fn `def _extract_toc_for_range(dump_content, start, end)` `priv` (L40-72)

### fn `def _sanitize_title(title)` `priv` (L73-78)

### fn `def _apply_toc_to_file(output_file, toc_content)` `priv` (L79-108)

### fn `def run(args)` (L109-197)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|9||
|`DESCRIPTION`|var|pub|10||
|`print_help`|fn|pub|13-20|def print_help(version)|
|`_parse_level1_toc`|fn|priv|21-39|def _parse_level1_toc(dump_content)|
|`_extract_toc_for_range`|fn|priv|40-72|def _extract_toc_for_range(dump_content, start, end)|
|`_sanitize_title`|fn|priv|73-78|def _sanitize_title(title)|
|`_apply_toc_to_file`|fn|priv|79-108|def _apply_toc_to_file(output_file, toc_content)|
|`run`|fn|pub|109-197|def run(args)|


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

### fn `def run(args)` (L21-61)
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
|`run`|fn|pub|21-61|def run(args)|


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

### fn `def run(args)` (L21-61)
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
|`run`|fn|pub|21-61|def run(args)|


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

### fn `def run(args)` (L162-175)

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
|`run`|fn|pub|162-175|def run(args)|


---

# pi.py | Python | 84L | 5 symbols | 2 imports | 16 comments
> Path: `src/shell_scripts/commands/pi.py`

## Imports
```
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L17)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch pi.dev CLI in the project context."` (L22)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version)` (L32-51)
- @brief Default `--tools` payload for `pi` command invocations.
- @brief Print command-specific help for `pi`.
- @details Applied only when no `--tools` option token is present in forwarded
arguments.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; documents default `--tools` append semantics and override behavior when `--tools` is explicitly provided.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies REQ-068, REQ-069
- @satisfies DES-008, REQ-068, REQ-069

### fn `def _has_tools_option(args)` `priv` (L52-66)
- @brief Detect whether forwarded args include a `--tools` option token.
- @details Detects both tokenized forms `--tools <value>` and single-token form `--tools=<value>` using exact prefix matching on each argument element. Time complexity O(n), where n is the argument count.
- @param args {list[str]} Forwarded CLI args for `pi` launcher.
- @return {bool} `True` when any argument token provides `--tools`; `False` otherwise.
- @satisfies REQ-068, REQ-069

### fn `def run(args)` (L67-84)
- @brief Launch pi.dev CLI after external executable validation.
- @details Resolves project root, checks executable availability for `pi`, forwards all CLI arguments unchanged, and appends default tools option only when no `--tools` token exists in input args.
- @param args {list[str]} Additional CLI args forwarded to pi.dev.
- @return {int} Child process return code.
- @satisfies REQ-055, REQ-056, REQ-064, REQ-068, REQ-069

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|17||
|`DESCRIPTION`|var|pub|22||
|`print_help`|fn|pub|32-51|def print_help(version)|
|`_has_tools_option`|fn|priv|52-66|def _has_tools_option(args)|
|`run`|fn|pub|67-84|def run(args)|


---

# req_cmd.py | Python | 298L | 11 symbols | 6 imports | 11 comments
> Path: `src/shell_scripts/commands/req_cmd.py`

## Imports
```
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from shell_scripts.config import get_req_profile
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L23)
- var `DESCRIPTION = "Run useReq bootstrap on current or discovered directories."` (L24)
### fn `def _is_hidden_path(path: Path, base_dir: Path) -> bool` `priv` (L57-71)
- @brief Determine whether path contains hidden segments below base.
- @details Computes relative parts from `base_dir` and returns `True` when any path segment starts with a dot-prefix, preventing accidental traversal of hidden metadata directories (for example `.git`).
- @param path {Path} Candidate directory path.
- @param base_dir {Path} Root directory used for relative-segment evaluation.
- @return {bool} `True` when candidate has hidden relative segments.
- @satisfies REQ-052, REQ-053

### fn `def print_help(version: str) -> None` (L72-89)
- @brief Render command help for `req`.
- @details Prints selector options and behavior contract for target directory discovery and external `req` invocation flow.
- @param version {str} CLI version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def _iter_first_level_dirs(base_dir: Path) -> list[Path]` `priv` (L90-109)
- @brief Collect first-level child directories in deterministic order.
- @details Enumerates direct children of `base_dir`, keeps only directories, and sorts by path string for stable command behavior.
- @param base_dir {Path} Directory whose first-level children are listed.
- @return {list[Path]} Sorted first-level child directories.
- @satisfies REQ-052

### fn `def _iter_descendant_dirs(base_dir: Path) -> list[Path]` `priv` (L110-129)
- @brief Collect descendant directories recursively in deterministic order.
- @details Traverses all descendants via glob expansion, excludes `base_dir` itself, keeps only directories, and sorts by path string.
- @param base_dir {Path} Directory whose descendants are listed.
- @return {list[Path]} Sorted descendant directory list excluding `base_dir`.
- @satisfies REQ-053

### fn `def _build_req_args(target_dir: Path) -> list[str]` `priv` (L130-165)
- @brief Build external `req` argument vector for one target directory.
- @details Uses hardcoded non-overridable arguments and appends repeated runtime-configured providers/static-check entries sourced from `get_req_profile`.
- @param target_dir {Path} Target directory used to parameterize path flags.
- @return {list[str]} External `req` argv vector.
- @satisfies REQ-049, REQ-050

### fn `def _delete_cleanup_path(cleanup_path: Path) -> tuple[str, str]` `priv` (L166-188)
- @brief Remove one predefined cleanup path when it exists.
- @details Evaluates one cleanup candidate path, returns `skip` when the path is absent, removes directories with `shutil.rmtree`, removes non-directory filesystem entries with `Path.unlink`, and classifies deleted entries as `dir` or `file`. Time complexity is O(n) for directory trees and O(1) for non-directory entries.
- @param cleanup_path {Path} Absolute candidate cleanup path for one target.
- @return {tuple[str, str]} Status-kind pair shaped as (`deleted`, `dir`), (`deleted`, `file`), or (`skip`, `missing`).
- @satisfies REQ-048, REQ-062, REQ-063

### fn `def _print_cleanup_evidence(evidence: CleanupEvidence) -> None` `priv` (L189-205)
- @brief Emit one cleanup evidence line in deterministic token order.
- @details Prints a parser-friendly line using fixed `clean | <status> | <kind> | <path>` tokens so downstream checks can differentiate deleted files, deleted directories, and skipped missing paths without reading surrounding prose. Time complexity is O(1).
- @param evidence {CleanupEvidence} Tuple `(status, kind, path)` produced by cleanup preparation logic.
- @return {None} Writes one stdout line.
- @satisfies REQ-062, REQ-063

### fn `def _prepare_target_directory(target_dir: Path) -> list[CleanupEvidence]` `priv` (L206-229)
- @brief Apply cleanup and scaffold operations for one target directory.
- @details Evaluates every predefined cleanup path, records deterministic cleanup evidence tuples, removes existing filesystem entries, and ensures required project subdirectories exist before external `req` call. Time complexity is O(m + d) where `m` is cleanup-path count and `d` is total removed directory-tree entries.
- @param target_dir {Path} Target directory to mutate.
- @return {list[CleanupEvidence]} Cleanup evidence entries in configured path order.
- @satisfies REQ-048, REQ-062, REQ-063

### fn `def run(args: list[str]) -> int` (L230-298)
- @brief Execute `req` orchestration for selected directory targets.
- @details Parses mutually exclusive selector options, resolves target set, applies cleanup/scaffold phase with per-path evidence emission, and executes external `req` for each target. Returns `1` on invalid option combinations or unknown options. Converts external `req` non-zero exits into explicit error output and propagated return codes.
- @param args {list[str]} Command arguments excluding `req` token.
- @return {int} `0` on success; non-zero for option or subprocess failures.
- @exception {subprocess.CalledProcessError} Internally handled and converted to deterministic return code + error output.
- @satisfies REQ-048, REQ-049, REQ-051, REQ-052, REQ-053, REQ-054, REQ-056, REQ-062, REQ-063

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|23||
|`DESCRIPTION`|var|pub|24||
|`_is_hidden_path`|fn|priv|57-71|def _is_hidden_path(path: Path, base_dir: Path) -> bool|
|`print_help`|fn|pub|72-89|def print_help(version: str) -> None|
|`_iter_first_level_dirs`|fn|priv|90-109|def _iter_first_level_dirs(base_dir: Path) -> list[Path]|
|`_iter_descendant_dirs`|fn|priv|110-129|def _iter_descendant_dirs(base_dir: Path) -> list[Path]|
|`_build_req_args`|fn|priv|130-165|def _build_req_args(target_dir: Path) -> list[str]|
|`_delete_cleanup_path`|fn|priv|166-188|def _delete_cleanup_path(cleanup_path: Path) -> tuple[str...|
|`_print_cleanup_evidence`|fn|priv|189-205|def _print_cleanup_evidence(evidence: CleanupEvidence) ->...|
|`_prepare_target_directory`|fn|priv|206-229|def _prepare_target_directory(target_dir: Path) -> list[C...|
|`run`|fn|pub|230-298|def run(args: list[str]) -> int|


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

### fn `def run(args)` (L32-87)
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
|`run`|fn|pub|32-87|def run(args)|


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

### fn `def run(args)` (L26-64)
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
|`run`|fn|pub|26-64|def run(args)|


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

### fn `def run(args)` (L33-82)
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
|`run`|fn|pub|33-82|def run(args)|


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

### fn `def run(args)` (L44-89)
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
|`run`|fn|pub|44-89|def run(args)|


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

### fn `def run(args)` (L44-87)
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
|`run`|fn|pub|44-87|def run(args)|


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

### fn `def run(args)` (L35-50)
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
|`run`|fn|pub|35-50|def run(args)|


---

# vscode_cmd.py | Python | 42L | 4 symbols | 3 imports | 3 comments
> Path: `src/shell_scripts/commands/vscode_cmd.py`

## Imports
```
import os
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L14)
- var `DESCRIPTION = "Open VS Code in the project root with Codex integration."` (L15)
### fn `def print_help(version)` (L18-25)

### fn `def run(args)` (L26-42)
- @brief Launch VS Code after executable validation.
- @details Sets `CODEX_HOME`, validates executable availability for VS Code binary, and executes the command with project-root working directory.
- @param args {list[str]} Additional CLI args forwarded to VS Code.
- @return {int} Child process return code.
- @satisfies REQ-020, REQ-021, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|14||
|`DESCRIPTION`|var|pub|15||
|`print_help`|fn|pub|18-25|def print_help(version)|
|`run`|fn|pub|26-42|def run(args)|


---

# vsinsider_cmd.py | Python | 42L | 4 symbols | 3 imports | 3 comments
> Path: `src/shell_scripts/commands/vsinsider_cmd.py`

## Imports
```
import os
import subprocess
from shell_scripts.utils import require_project_root, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L14)
- var `DESCRIPTION = "Open VS Code Insiders in the project root with Codex integration."` (L15)
### fn `def print_help(version)` (L18-25)

### fn `def run(args)` (L26-42)
- @brief Launch VS Code Insiders after executable validation.
- @details Sets `CODEX_HOME`, validates executable availability for VS Code Insiders binary, and executes the command with project-root working directory.
- @param args {list[str]} Additional CLI args forwarded to VS Code Insiders.
- @return {int} Child process return code.
- @satisfies REQ-020, REQ-021, REQ-055, REQ-056, REQ-064

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|14||
|`DESCRIPTION`|var|pub|15||
|`print_help`|fn|pub|18-25|def print_help(version)|
|`run`|fn|pub|26-42|def run(args)|


---

# config.py | Python | 326L | 11 symbols | 6 imports | 22 comments
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

### fn `def get_config_path() -> Path` (L97-108)
- @brief In-memory runtime configuration snapshot.
- @brief Return canonical runtime config location.
- @details Initialized from defaults; updated only by `load_runtime_config`.
- @details Resolves path as `$HOME/.config/shellScripts/config.json` using `Path.home()` for user directory abstraction.
- @return {Path} Absolute config file path.
- @satisfies DES-011, REQ-045
- @satisfies DES-011, DES-012, REQ-045, REQ-046

### fn `def get_default_runtime_config() -> dict[str, Any]` (L109-120)
- @brief Return deep-copied default configuration payload.
- @details Produces an isolated copy to avoid external mutation of the global defaults constant and to keep write/load operations deterministic.
- @return {dict[str, Any]} Fresh deep copy of `DEFAULT_RUNTIME_CONFIG`.
- @satisfies DES-011, DES-012

### fn `def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]` `priv` (L121-140)
- @brief Recursively merge nested mapping values.
- @details For keys where both base and override values are dictionaries, recursively merges child keys; otherwise replaces base value with override. Time complexity O(N) over override node count.
- @param base {dict[str, Any]} Target mapping mutated in place.
- @param override {dict[str, Any]} Source mapping with overriding values.
- @return {dict[str, Any]} The mutated `base` reference.
- @satisfies DES-011, REQ-045

### fn `def _normalize_command_vector(value: Any) -> list[str] | None` `priv` (L141-157)
- @brief Validate and normalize an executable argv vector.
- @details Accepts only non-empty lists of non-empty strings and returns a cloned list for defensive immutability.
- @param value {Any} Candidate command vector.
- @return {list[str]|None} Sanitized vector or `None` if invalid.
- @satisfies DES-011, REQ-045

### fn `def _normalize_string_list(value: Any) -> list[str] | None` `priv` (L158-174)
- @brief Validate and normalize a list of non-empty strings.
- @details Accepts only list payloads containing non-empty string elements and returns a cloned list for defensive immutability. Empty lists are valid.
- @param value {Any} Candidate list payload.
- @return {list[str]|None} Sanitized list or `None` if invalid.
- @satisfies DES-011, REQ-045, REQ-050

### fn `def _normalize_categories(value: Any) -> dict[str, list[str]] | None` `priv` (L175-197)
- @brief Validate category-to-command mapping payload.
- @details Keeps only entries with string keys and valid command vectors. Invalid entries are dropped and can trigger fallback usage upstream.
- @param value {Any} Candidate category map payload.
- @return {dict[str, list[str]]|None} Sanitized category map or `None`.
- @satisfies DES-011, REQ-024, REQ-045

### fn `def load_runtime_config(path: Path | None = None) -> dict[str, Any]` (L198-237)
- @brief Load runtime configuration file and merge into defaults.
- @details Resets in-memory state to defaults for each call, then attempts to read and parse JSON payload from target path and recursively merge override keys. Missing file, invalid JSON, non-object root, or read errors preserve defaults and emit warnings.
- @param path {Path|None} Optional override path; default is canonical path.
- @return {dict[str, Any]} Active in-memory runtime configuration snapshot.
- @exception {json.JSONDecodeError} Handled internally and downgraded to warn.
- @exception {OSError} Handled internally and downgraded to warn.
- @satisfies DES-011, REQ-045

### fn `def get_management_command(name: str) -> str` (L238-254)
- @brief Resolve management command string with safe default fallback.
- @details Reads runtime key under `management.<name>`; returns default value when key is absent or not a non-empty string.
- @param name {str} Management operation key (`upgrade` or `uninstall`).
- @return {str} Shell command string to execute.
- @satisfies REQ-004, REQ-005, REQ-045

### fn `def get_dispatch_profile(name: str) -> tuple[dict[str, list[str]], list[str]]` (L255-280)
- @brief Resolve dispatch profile for diff/edit/view command wrappers.
- @details Builds profile from `dispatch.<name>` runtime payload with typed normalization and per-section fallback to hardcoded defaults for missing or invalid values.
- @param name {str} Dispatch command key (`diff`, `edit`, or `view`).
- @return {tuple[dict[str, list[str]], list[str]]} `(categories, fallback)`.
- @satisfies DES-007, REQ-024, REQ-045

### fn `def get_req_profile() -> tuple[list[str], list[str]]` (L281-308)
- @brief Resolve `req` providers and static checks from runtime config.
- @details Builds profile from `req.providers` and `req.static_checks` runtime payload with typed normalization and per-section fallback to hardcoded defaults for missing or invalid values.
- @return {tuple[list[str], list[str]]} `(providers, static_checks)`.
- @satisfies DES-011, REQ-045, REQ-050

### fn `def write_default_runtime_config(path: Path | None = None) -> Path` (L309-326)
- @brief Write default runtime configuration file to disk.
- @details Creates parent directories when missing and writes canonical JSON payload using sorted keys and indentation for deterministic content.
- @param path {Path|None} Optional override path; default is canonical path.
- @return {Path} Path where the file has been written.
- @exception {OSError} Propagated when filesystem write fails.
- @satisfies DES-012, REQ-046

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_config_path`|fn|pub|97-108|def get_config_path() -> Path|
|`get_default_runtime_config`|fn|pub|109-120|def get_default_runtime_config() -> dict[str, Any]|
|`_deep_merge_dict`|fn|priv|121-140|def _deep_merge_dict(base: dict[str, Any], override: dict...|
|`_normalize_command_vector`|fn|priv|141-157|def _normalize_command_vector(value: Any) -> list[str] | ...|
|`_normalize_string_list`|fn|priv|158-174|def _normalize_string_list(value: Any) -> list[str] | None|
|`_normalize_categories`|fn|priv|175-197|def _normalize_categories(value: Any) -> dict[str, list[s...|
|`load_runtime_config`|fn|pub|198-237|def load_runtime_config(path: Path | None = None) -> dict...|
|`get_management_command`|fn|pub|238-254|def get_management_command(name: str) -> str|
|`get_dispatch_profile`|fn|pub|255-280|def get_dispatch_profile(name: str) -> tuple[dict[str, li...|
|`get_req_profile`|fn|pub|281-308|def get_req_profile() -> tuple[list[str], list[str]]|
|`write_default_runtime_config`|fn|pub|309-326|def write_default_runtime_config(path: Path | None = None...|


---

# core.py | Python | 279L | 8 symbols | 7 imports | 18 comments
> Path: `src/shell_scripts/core.py`

## Imports
```
import sys
import subprocess
from shell_scripts import __version__
from shell_scripts.config import (
from shell_scripts.version_check import check_for_updates
from shell_scripts.commands import get_command
from shell_scripts.utils import (
```

## Definitions

- var `PROGRAM = "shellscripts"` (L31)
- var `HELP_COMMAND_COLUMN_WIDTH = 16` (L37)
- @brief Fixed command-name column width for grouped help rendering.
- @details Forces deterministic spacing for all command rows across grouped
global help sections.
- @satisfies REQ-066
- var `HELP_SECTION_COMMANDS = (` (L45)
- @brief Ordered command groups for global help rendering.
- @details Defines deterministic section order and command-token order used by
`print_help` when emitting grouped command help. Ordering is normative and
maps directly to REQ-066 output expectations.
- @satisfies DES-014, REQ-066
### fn `def print_help(command_name=None)` (L112-158)
- @brief Print global or command-specific help text.
- @details Renders command module help for known command names; otherwise exits with explicit unknown-command error. Global help includes management options and grouped command sections using deterministic section and command order, with descriptions sourced from each command module `DESCRIPTION` constant.
- @param command_name {str|None} Optional command token for scoped help.
- @return {None} Writes to stdout/stderr; may terminate process on invalid command.
- @throws {SystemExit} Raised when unknown command name is requested.
- @satisfies PRJ-002, DES-014, REQ-001, REQ-002, REQ-066, REQ-068, REQ-069

### fn `def do_upgrade()` (L159-181)
- @brief Execute Linux-only upgrade command resolved from runtime config.
- @details Reads management command string from runtime config key `management.upgrade`, executes it on Linux via shell invocation, and prints manual fallback command on non-Linux systems.
- @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-004, REQ-045, REQ-056

### fn `def do_uninstall()` (L182-204)
- @brief Execute Linux-only uninstall command resolved from runtime config.
- @details Reads management command string from runtime config key `management.uninstall`, executes it on Linux via shell invocation, and prints manual fallback command on non-Linux systems.
- @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-005, REQ-045, REQ-056

### fn `def do_write_config()` (L205-220)
- @brief Persist default runtime configuration file to disk.
- @details Writes canonical config JSON to `$HOME/.config/shellScripts/config.json` and logs destination path.
- @return {int} `0` on successful write.
- @throws {OSError} Propagated on filesystem write failure.
- @satisfies REQ-046

### fn `def main()` (L221-279)
- @brief Entrypoint for shellscripts argument dispatch.
- @details Performs runtime OS detection, update check, runtime configuration load, and argument dispatch through management flags and subcommands, then restores terminal raw/cbreak and disables legacy+xterm mouse-tracking modes (`?9l`, `?1000l`, `?1001l`, `?1002l`, `?1003l`, `?1004l`, `?1005l`, `?1006l`, `?1007l`, `?1015l`, `?1016l`) before exit.
- @return {int} Process-compatible return code for caller (`sys.exit`).
- @satisfies PRJ-001, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-064, REQ-065, REQ-066, REQ-068, REQ-069

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|31||
|`HELP_COMMAND_COLUMN_WIDTH`|var|pub|37||
|`HELP_SECTION_COMMANDS`|var|pub|45||
|`print_help`|fn|pub|112-158|def print_help(command_name=None)|
|`do_upgrade`|fn|pub|159-181|def do_upgrade()|
|`do_uninstall`|fn|pub|182-204|def do_uninstall()|
|`do_write_config`|fn|pub|205-220|def do_write_config()|
|`main`|fn|pub|221-279|def main()|


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
- @satisfies DES-013, REQ-008, REQ-047

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

### fn `def run_cmd(cmd, **kwargs)` (L454-455)

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
|`run_cmd`|fn|pub|454-455|def run_cmd(cmd, **kwargs)|


---

# version_check.py | Python | 230L | 21 symbols | 7 imports | 11 comments
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
```

## Definitions

- var `PROGRAM = "shellscripts"` (L19)
- var `OWNER = "Ogekuri"` (L20)
- var `REPOSITORY = "shellScripts"` (L21)
- var `IDLE_DELAY = 3600` (L22)
- var `HTTP_ERROR_IDLE_DELAY = 86400` (L23)
- var `HTTP_TIMEOUT = 2` (L24)
- var `GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"` (L25)
- var `CACHE_DIR = Path.home() / ".cache" / PROGRAM` (L26)
- var `IDLE_TIME_FILE = CACHE_DIR / "check_version_idle-time.json"` (L27)
- var `BRIGHT_GREEN = "\033[92m"` (L29)
- var `BRIGHT_RED = "\033[91m"` (L30)
- var `RESET = "\033[0m"` (L31)
### fn `def _read_idle_config() -> dict[str, object] | None` `priv` (L34-52)
- @brief Load cached cooldown metadata for the version check.
- @details Reads the cooldown JSON payload from the user cache directory. Absent files and unreadable JSON payloads resolve to `None`. Complexity: O(1) for fixed-size payload parsing.
- @return {dict[str, object] | None} Cached cooldown payload or `None`.
- @satisfies DES-003, REQ-059

### fn `def _write_idle_config(last_check_ts: float, idle_delay_seconds: int) -> None` `priv` (L53-82)
- @brief Persist cooldown timestamps for the next version-check gate.
- @details Derives the idle-until timestamp from the supplied delay, writes both machine-readable timestamps and UTC-rendered strings, and stores the applied delay for downstream inspection. Complexity: O(1).
- @param last_check_ts {float} UNIX timestamp recorded for the current check.
- @param idle_delay_seconds {int} Cooldown duration applied after the check.
- @return {None} No return value.
- @throws {OSError} Propagated when cache directory creation or file write fails.
- @satisfies DES-003, DES-004, DES-005, REQ-061

### fn `def _is_forced_version_check() -> bool` `priv` (L83-95)
- @brief Detect CLI flags that force the version-check HTTP request.
- @details Evaluates the live process argument vector and returns `True` when the current invocation requested `--version` or `--ver`. Complexity: O(N) where N is the number of CLI arguments.
- @return {bool} `True` when the request must bypass cooldown gating.
- @satisfies REQ-003, REQ-059

### fn `def _format_request_error(error: Exception) -> str` `priv` (L96-118)
- @brief Convert a request exception into terminal output detail text.
- @details Returns a stable, parser-friendly error descriptor for HTTP and non-HTTP request failures. HTTP errors preserve the status code. Non-HTTP errors expose the exception type and optional message. Complexity: O(1).
- @param error {Exception} Request failure captured during update checking.
- @return {str} Error detail suffix without terminal color codes.
- @satisfies DES-005, DES-006, REQ-061

### fn `def _handle_request_error(last_check_ts: float, error: Exception) -> None` `priv` (L119-135)
- @brief Persist cooldown metadata and print the request error line.
- @details Applies the fixed HTTP-error cooldown, updates the cooldown JSON, and emits a bright-red terminal line for the supplied request failure. Complexity: O(1) excluding filesystem latency.
- @param last_check_ts {float} UNIX timestamp recorded for the failed check.
- @param error {Exception} Request failure captured during update checking.
- @return {None} No return value.
- @throws {OSError} Propagated when cache directory creation or file write fails.
- @satisfies DES-003, DES-005, DES-006, REQ-061

### fn `def _should_check(force_check: bool = False) -> bool` `priv` (L136-157)
- @brief Evaluate whether the GitHub version-check request should run.
- @details Forces execution when `force_check` is `True`; otherwise reads the cached idle-until timestamp and compares it against the current wall-clock time. Complexity: O(1).
- @param force_check {bool} Cooldown-bypass flag derived from CLI arguments.
- @return {bool} `True` when the HTTP request is allowed or forced.
- @satisfies REQ-003, REQ-059

### fn `def _parse_version(version_value: str) -> tuple[int, ...]` `priv` (L158-171)
- @brief Convert a semantic-version string into an integer tuple.
- @details Strips a leading `v` prefix, splits by `.`, and converts each segment to `int`. Complexity: O(N) where N is the number of segments.
- @param version_value {str} Raw semantic version token.
- @return {tuple[int, ...]} Parsed numeric version segments.
- @throws {ValueError} Propagated when a segment is not numeric.
- @satisfies PRJ-004

### fn `def _compare_versions(current: str, latest: str) -> bool` `priv` (L172-189)
- @brief Compare installed and latest semantic versions.
- @details Parses both version strings into integer tuples and returns `True` only when `latest` is newer than `current`. Invalid inputs collapse to `False`. Complexity: O(N).
- @param current {str} Installed package version.
- @param latest {str} Latest GitHub release version.
- @return {bool} `True` when the remote version is newer.
- @satisfies PRJ-004, REQ-060

### fn `def check_for_updates(current_version: str) -> None` (L190-230)
- @brief Execute the startup GitHub release version check.
- @details Applies cooldown gating unless the current CLI invocation requests `--version` or `--ver`, performs the latest-release HTTP request, prints a bright-green update line for newer releases, persists a 3600-second success cooldown or an 86400-second request-error cooldown for every request outcome, prints bright-red request errors, and suppresses propagation of non-HTTP request exceptions. Complexity: O(1) excluding network latency and JSON parsing.
- @param current_version {str} Installed package version string.
- @return {None} No return value.
- @throws {urllib.error.HTTPError} Internally handled and converted to output.
- @satisfies PRJ-004, DES-004, DES-005, DES-006, REQ-003, REQ-059, REQ-060, REQ-061

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|19||
|`OWNER`|var|pub|20||
|`REPOSITORY`|var|pub|21||
|`IDLE_DELAY`|var|pub|22||
|`HTTP_ERROR_IDLE_DELAY`|var|pub|23||
|`HTTP_TIMEOUT`|var|pub|24||
|`GITHUB_API_URL`|var|pub|25||
|`CACHE_DIR`|var|pub|26||
|`IDLE_TIME_FILE`|var|pub|27||
|`BRIGHT_GREEN`|var|pub|29||
|`BRIGHT_RED`|var|pub|30||
|`RESET`|var|pub|31||
|`_read_idle_config`|fn|priv|34-52|def _read_idle_config() -> dict[str, object] | None|
|`_write_idle_config`|fn|priv|53-82|def _write_idle_config(last_check_ts: float, idle_delay_s...|
|`_is_forced_version_check`|fn|priv|83-95|def _is_forced_version_check() -> bool|
|`_format_request_error`|fn|priv|96-118|def _format_request_error(error: Exception) -> str|
|`_handle_request_error`|fn|priv|119-135|def _handle_request_error(last_check_ts: float, error: Ex...|
|`_should_check`|fn|priv|136-157|def _should_check(force_check: bool = False) -> bool|
|`_parse_version`|fn|priv|158-171|def _parse_version(version_value: str) -> tuple[int, ...]|
|`_compare_versions`|fn|priv|172-189|def _compare_versions(current: str, latest: str) -> bool|
|`check_for_updates`|fn|pub|190-230|def check_for_updates(current_version: str) -> None|

