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
        │   ├── clean.py
        │   ├── cli_claude.py
        │   ├── cli_codex.py
        │   ├── cli_copilot.py
        │   ├── cli_gemini.py
        │   ├── cli_kiro.py
        │   ├── cli_opencode.py
        │   ├── dicom2jpg.py
        │   ├── dicomviewer.py
        │   ├── diff_cmd.py
        │   ├── dng2hdr2jpg.py
        │   ├── doxygen_cmd.py
        │   ├── edit_cmd.py
        │   ├── pdf_crop.py
        │   ├── pdf_merge.py
        │   ├── pdf_split_by_format.py
        │   ├── pdf_split_by_toc.py
        │   ├── pdf_tiler_090.py
        │   ├── pdf_tiler_100.py
        │   ├── pdf_toc_clean.py
        │   ├── req_cmd.py
        │   ├── tests_cmd.py
        │   ├── ubuntu_dark_theme.py
        │   ├── venv_cmd.py
        │   ├── view_cmd.py
        │   ├── vscode_cmd.py
        │   └── vsinsider_cmd.py
        ├── config.py
        ├── core.py
        ├── utils.py
        └── version_check.py
```

# s.sh | Shell | 23L | 4 symbols | 0 imports | 4 comments
> Path: `scripts/s.sh`

## Definitions

- var `FULL_PATH=$(readlink -f "$0")` (L6)
- var `SCRIPT_PATH=$(dirname "$FULL_PATH")` (L7)
- var `BASE_DIR=$(dirname "$SCRIPT_PATH")` (L8)
- var `PROJECT_ROOT=$(git -C "${BASE_DIR}" rev-parse --show-toplevel 2>/dev/null)` (L10)
## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`FULL_PATH`|var||6||
|`SCRIPT_PATH`|var||7||
|`BASE_DIR`|var||8||
|`PROJECT_ROOT`|var||10||


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

# __init__.py | Python | 79L | 2 symbols | 2 imports | 8 comments
> Path: `src/shell_scripts/commands/__init__.py`

## Imports
```
import importlib
from types import ModuleType
```

## Definitions

### fn `def get_command(name: str) -> ModuleType | None` (L49-64)
- @brief Static map from CLI command names to importable module paths.
- @brief Resolve one CLI command token to its command module.
- @details Enables lazy command loading and deterministic command exposure.
Removing an entry removes command discoverability and dispatch reachability.
- @details Performs O(1) dictionary lookup on `_COMMAND_MODULES`; returns `None` for unknown tokens; imports target module lazily only on hit.
- @param name {str} CLI command token.
- @return {ModuleType|None} Imported command module for known token; `None` otherwise.
- @throws {ImportError} If module path exists in map but import fails.
- @satisfies PRJ-003, DES-001
- @satisfies PRJ-001, DES-001, DES-008

### fn `def get_all_commands() -> dict[str, str]` (L65-79)
- @brief Build command-description index for help rendering.
- @details Iterates sorted command keys for stable output ordering; imports each module via `get_command`; extracts `DESCRIPTION` or empty string. Time complexity O(N log N) for N commands due to key sorting.
- @return {dict[str, str]} Mapping `command_name -> description`.
- @throws {ImportError} If any mapped command module import fails.
- @satisfies PRJ-002, DES-001, DES-008

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_command`|fn|pub|49-64|def get_command(name: str) -> ModuleType | None|
|`get_all_commands`|fn|pub|65-79|def get_all_commands() -> dict[str, str]|


---

# _dc_common.py | Python | 99L | 9 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/_dc_common.py`

## Imports
```
import os
import sys
import subprocess
import shutil
```

## Definitions

- var `CODE_EXTENSIONS = {` (L7)
- var `MARKDOWN_EXTENSIONS = {"md", "markdown", "mdown", "mkd"}` (L15)
- var `HTML_EXTENSIONS = {"html", "htm", "xhtml"}` (L16)
- var `IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "svg"}` (L17)
### fn `def get_extension(filepath)` (L20-26)

### fn `def detect_mime(filepath)` (L27-44)

### fn `def categorize(filepath)` (L45-82)

### fn `def pick_cmd(primary, fallback)` (L83-88)

### fn `def dispatch(category_cmds, fallback_cmd, filepath, extra_args)` (L89-99)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`CODE_EXTENSIONS`|var|pub|7||
|`MARKDOWN_EXTENSIONS`|var|pub|15||
|`HTML_EXTENSIONS`|var|pub|16||
|`IMAGE_EXTENSIONS`|var|pub|17||
|`get_extension`|fn|pub|20-26|def get_extension(filepath)|
|`detect_mime`|fn|pub|27-44|def detect_mime(filepath)|
|`categorize`|fn|pub|45-82|def categorize(filepath)|
|`pick_cmd`|fn|pub|83-88|def pick_cmd(primary, fallback)|
|`dispatch`|fn|pub|89-99|def dispatch(category_cmds, fallback_cmd, filepath, extra...|


---

# ai_install.py | Python | 216L | 11 symbols | 9 imports | 7 comments
> Path: `src/shell_scripts/commands/ai_install.py`

## Imports
```
import os
import subprocess
import shutil
import zipfile
import tempfile
from pathlib import Path
from shell_scripts.utils import is_windows, print_info, print_error, print_success
import urllib.request
import urllib.request
```

## Definitions

- var `PROGRAM = "shellscripts"` (L19)
- var `DESCRIPTION = "Install AI CLI tools (Codex, Copilot, Gemini, OpenCode, Claude, Kiro)."` (L20)
- var `TOOLS = {` (L22)
- var `CLAUDE_BUCKET = (` (L41)
- var `KIRO_URL = (` (L45)
### fn `def print_help(version)` (L50-72)
- @brief Render command help for `ai-install`.
- @details Prints supported selectors and execution contract for installer dispatch.
- @param version {str} CLI version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def _install_npm_tool(tool_key)` `priv` (L73-101)
- @brief Execute npm-based installer command for selected tool.
- @details Resolves base npm command from static tool mapping, prepends `sudo` when runtime OS is not Windows, and uses resolved `npm.cmd` path on Windows when available to avoid process-launch failures. Executes subprocess and emits status messages.
- @param tool_key {str} Tool identifier key from `TOOLS`.
- @return {None} Executes side effects and prints result messages.
- @satisfies DES-013, REQ-008, REQ-047

### fn `def _install_claude()` `priv` (L102-134)
- @brief Install Claude CLI by direct binary download.
- @details Downloads latest version metadata and Linux binary from configured bucket, writes executable into `~/.claude/bin/claude`, and sets execute permissions.
- @return {None} Executes side effects and prints result messages.
- @throws {Exception} Handled internally and logged as installer failure.
- @satisfies REQ-009

### fn `def _install_kiro()` `priv` (L135-173)
- @brief Install Kiro CLI binaries by ZIP extraction flow.
- @details Downloads platform ZIP package, extracts binaries, copies `kiro-cli*` executables into `~/.local/bin`, and applies executable mode.
- @return {None} Executes side effects and prints result messages.
- @throws {Exception} Handled internally and logged as installer failure.
- @satisfies REQ-010

- var `ALL_INSTALLERS = {` (L174)
### fn `def run(args)` (L184-216)
- @brief Parse selectors and execute selected AI installer routines.
- @details Accepts explicit selectors or defaults to full installer set when omitted; rejects unknown selectors with return code `1`.
- @param args {list[str]} CLI selector tokens for installer filtering.
- @return {int} `0` on successful dispatch; `1` on unknown selector.
- @satisfies REQ-006, REQ-007

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|19||
|`DESCRIPTION`|var|pub|20||
|`TOOLS`|var|pub|22||
|`CLAUDE_BUCKET`|var|pub|41||
|`KIRO_URL`|var|pub|45||
|`print_help`|fn|pub|50-72|def print_help(version)|
|`_install_npm_tool`|fn|priv|73-101|def _install_npm_tool(tool_key)|
|`_install_claude`|fn|priv|102-134|def _install_claude()|
|`_install_kiro`|fn|priv|135-173|def _install_kiro()|
|`ALL_INSTALLERS`|var|pub|174||
|`run`|fn|pub|184-216|def run(args)|


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

# cli_claude.py | Python | 23L | 4 symbols | 3 imports | 1 comments
> Path: `src/shell_scripts/commands/cli_claude.py`

## Imports
```
import os
from pathlib import Path
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."` (L8)
### fn `def print_help(version)` (L11-18)

### fn `def run(args)` (L19-23)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-18|def print_help(version)|
|`run`|fn|pub|19-23|def run(args)|


---

# cli_codex.py | Python | 99L | 6 symbols | 3 imports | 12 comments
> Path: `src/shell_scripts/commands/cli_codex.py`

## Imports
```
import os
from pathlib import Path
from shell_scripts.utils import print_info, require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L19)
- @brief Base CLI program name used in help output.
- @details Constant identifier for usage-line rendering in command help.
- var `DESCRIPTION = "Launch OpenAI Codex CLI in the project context."` (L23)
- @brief One-line command description for dispatcher help surfaces.
- @details Exposed by command registry introspection (`get_all_commands`).
### fn `def print_help(version: str) -> None` (L26-41)
- @brief Print command-specific help for `cli-codex`.
- @details Emits usage and pass-through argument behavior for deterministic terminal rendering; does not mutate process state.
- @param version {str} CLI version string propagated by dispatcher.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def _is_expected_auth_link(link_path: Path, target_path: Path) -> bool` `priv` (L42-57)
- @brief Determine whether auth link already targets expected home file.
- @details Evaluates symlink kind and resolved destination with `strict=False` to support not-yet-materialized target files. Time complexity O(1) excluding filesystem metadata lookup costs.
- @param link_path {Path} Candidate project-local auth link path.
- @param target_path {Path} Expected user-home auth file path.
- @return {bool} True only when `link_path` is symlink resolving to `target_path`.
- @satisfies REQ-043

### fn `def _ensure_auth_symlink(project_root: Path) -> None` `priv` (L58-81)
- @brief Ensure project Codex auth path is symlinked to user auth file.
- @details Computes `<project-root>/.codex/auth.json` and verifies it points to `~/.codex/auth.json`. If not compliant, creates parent directories, replaces existing path entry, creates expected symlink, and emits one info message announcing link creation. Time complexity O(1).
- @param project_root {Path} Git project root used by command runtime context.
- @return {None} Applies filesystem mutations when compliance is absent.
- @throws {OSError} If directory creation, unlink, or symlink creation fails.
- @satisfies REQ-043, REQ-044

### fn `def run(args: list[str]) -> None` (L82-99)
- @brief Launch Codex CLI with project-scoped environment preparation.
- @details Resolves project root, guarantees codex auth symlink compliance, sets `CODEX_HOME=<project-root>/.codex`, then replaces process image with `/usr/bin/codex --yolo` plus pass-through args.
- @param args {list[str]} Additional CLI args forwarded to Codex.
- @return {None} Function does not return on successful `os.execvp`.
- @throws {SystemExit} Propagated in tests when `os.execvp` is monkeypatched.
- @throws {OSError} Propagated for filesystem or process-launch failures.
- @satisfies REQ-014, REQ-043, REQ-044

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|19||
|`DESCRIPTION`|var|pub|23||
|`print_help`|fn|pub|26-41|def print_help(version: str) -> None|
|`_is_expected_auth_link`|fn|priv|42-57|def _is_expected_auth_link(link_path: Path, target_path: ...|
|`_ensure_auth_symlink`|fn|priv|58-81|def _ensure_auth_symlink(project_root: Path) -> None|
|`run`|fn|pub|82-99|def run(args: list[str]) -> None|


---

# cli_copilot.py | Python | 21L | 4 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/cli_copilot.py`

## Imports
```
import os
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "Launch GitHub Copilot CLI in the project context."` (L7)
### fn `def print_help(version)` (L10-17)

### fn `def run(args)` (L18-21)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`print_help`|fn|pub|10-17|def print_help(version)|
|`run`|fn|pub|18-21|def run(args)|


---

# cli_gemini.py | Python | 21L | 4 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/cli_gemini.py`

## Imports
```
import os
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "Launch Google Gemini CLI in the project context."` (L7)
### fn `def print_help(version)` (L10-17)

### fn `def run(args)` (L18-21)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`print_help`|fn|pub|10-17|def print_help(version)|
|`run`|fn|pub|18-21|def run(args)|


---

# cli_kiro.py | Python | 23L | 4 symbols | 3 imports | 1 comments
> Path: `src/shell_scripts/commands/cli_kiro.py`

## Imports
```
import os
from pathlib import Path
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Launch Kiro CLI in the project context."` (L8)
### fn `def print_help(version)` (L11-18)

### fn `def run(args)` (L19-23)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-18|def print_help(version)|
|`run`|fn|pub|19-23|def run(args)|


---

# cli_opencode.py | Python | 21L | 4 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/cli_opencode.py`

## Imports
```
import os
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "Launch OpenCode CLI in the project context."` (L7)
### fn `def print_help(version)` (L10-17)

### fn `def run(args)` (L18-21)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`print_help`|fn|pub|10-17|def print_help(version)|
|`run`|fn|pub|18-21|def run(args)|


---

# dicom2jpg.py | Python | 81L | 7 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/dicom2jpg.py`

## Imports
```
import os
import subprocess
import shutil
from shell_scripts.utils import print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Convert DICOM images to JPEG using PixelMed."` (L9)
- var `JAVA_WRAPPERS = "/usr/lib/java-wrappers/java-wrappers.sh"` (L11)
### fn `def print_help(version)` (L14-22)

### fn `def _find_java()` `priv` (L23-29)

### fn `def _find_jars(*jar_names)` `priv` (L30-41)

### fn `def run(args)` (L42-81)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`JAVA_WRAPPERS`|var|pub|11||
|`print_help`|fn|pub|14-22|def print_help(version)|
|`_find_java`|fn|priv|23-29|def _find_java()|
|`_find_jars`|fn|priv|30-41|def _find_jars(*jar_names)|
|`run`|fn|pub|42-81|def run(args)|


---

# dicomviewer.py | Python | 66L | 7 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/dicomviewer.py`

## Imports
```
import os
import subprocess
import shutil
from shell_scripts.utils import print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Launch PixelMed DICOM image viewer."` (L9)
- var `JAVA_WRAPPERS = "/usr/lib/java-wrappers/java-wrappers.sh"` (L11)
### fn `def print_help(version)` (L14-21)

### fn `def _find_java()` `priv` (L22-28)

### fn `def _find_jars(*jar_names)` `priv` (L29-40)

### fn `def run(args)` (L41-66)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`JAVA_WRAPPERS`|var|pub|11||
|`print_help`|fn|pub|14-21|def print_help(version)|
|`_find_java`|fn|priv|22-28|def _find_java()|
|`_find_jars`|fn|priv|29-40|def _find_jars(*jar_names)|
|`run`|fn|pub|41-66|def run(args)|


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

# dng2hdr2jpg.py | Python | 1983L | 64 symbols | 15 imports | 46 comments
> Path: `src/shell_scripts/commands/dng2hdr2jpg.py`

## Imports
```
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shell_scripts.utils import (
import rawpy  # type: ignore
import imageio.v3 as imageio  # type: ignore
import imageio  # type: ignore
from PIL import Image as pil_image  # type: ignore
from PIL import ImageEnhance as pil_enhance  # type: ignore
import cv2  # type: ignore
import numpy as numpy_module  # type: ignore
```

## Definitions

- var `PROGRAM = "shellscripts"` (L27)
- var `DESCRIPTION = "Convert DNG to HDR-merged JPG with optional luminance-hdr-cli backend."` (L28)
- var `DEFAULT_EV = 2.0` (L29)
- var `DEFAULT_GAMMA = (2.222, 4.5)` (L30)
- var `DEFAULT_POST_GAMMA = 1.0` (L31)
- var `DEFAULT_BRIGHTNESS = 1.0` (L32)
- var `DEFAULT_CONTRAST = 1.0` (L33)
- var `DEFAULT_SATURATION = 1.0` (L34)
- var `DEFAULT_JPG_COMPRESSION = 15` (L35)
- var `DEFAULT_LUMINANCE_HDR_MODEL = "debevec"` (L36)
- var `DEFAULT_LUMINANCE_HDR_WEIGHT = "flat"` (L37)
- var `DEFAULT_LUMINANCE_HDR_RESPONSE_CURVE = "srgb"` (L38)
- var `DEFAULT_LUMINANCE_TMO = "reinhard02"` (L39)
- var `DEFAULT_REINHARD02_BRIGHTNESS = 1.25` (L40)
- var `DEFAULT_REINHARD02_CONTRAST = 0.85` (L41)
- var `DEFAULT_REINHARD02_SATURATION = 0.55` (L42)
- var `SUPPORTED_EV_VALUES = (0.5, 1.0, 1.5, 2.0)` (L43)
### class `class PostprocessOptions` `@dataclass(frozen=True)` (L183-205)
- @brief Hold deterministic postprocessing option values.
- @details Encapsulates correction factors and JPEG compression level used by shared TIFF-to-JPG postprocessing for both HDR backends.
- @param post_gamma {float} Gamma correction factor for postprocessing stage.
- @param brightness {float} Brightness enhancement factor.
- @param contrast {float} Contrast enhancement factor.
- @param saturation {float} Saturation enhancement factor.
- @param jpg_compression {int} JPEG compression level in range `[0, 100]`.
- @param wow_mode {str|None} Optional wow implementation selector (`ImageMagick` or `OpenCV`).
- @return {None} Immutable dataclass container.
- @satisfies REQ-065, REQ-066, REQ-069, REQ-071, REQ-072, REQ-073, REQ-075

### class `class LuminanceOptions` `@dataclass(frozen=True)` (L207-227)
- @brief Hold deterministic luminance-hdr-cli option values.
- @details Encapsulates luminance backend model and tone-mapping parameters forwarded to `luminance-hdr-cli` command generation.
- @param hdr_model {str} Luminance HDR model (`--hdrModel`).
- @param hdr_weight {str} Luminance weighting function (`--hdrWeight`).
- @param hdr_response_curve {str} Luminance response curve (`--hdrResponseCurve`).
- @param tmo {str} Tone-mapping operator (`--tmo`).
- @param tmo_extra_args {tuple[str, ...]} Explicit passthrough `--tmo*` option pairs in CLI order.
- @return {None} Immutable dataclass container.
- @satisfies REQ-061, REQ-067, REQ-068

### fn `def _print_box_table(headers, rows, header_rows=())` `priv` (L228-264)
- @brief Print one Unicode box-drawing table.
- @details Computes deterministic column widths from headers and rows, then prints aligned borders and cells using Unicode line-drawing glyphs.
- @param headers {tuple[str, ...]} Table header labels in fixed output order.
- @param header_rows {tuple[tuple[str, ...], ...]} Additional physical header rows rendered before header/body separator.
- @param rows {tuple[tuple[str, ...], ...]} Table body rows with one value per column.
- @return {None} Writes formatted table to stdout.
- @satisfies REQ-070

### fn `def _border(left, middle, right)` `priv` (L248-250)
- @brief Print one Unicode box-drawing table.
- @details Computes deterministic column widths from headers and rows, then
prints aligned borders and cells using Unicode line-drawing glyphs.
- @param headers {tuple[str, ...]} Table header labels in fixed output order.
- @param header_rows {tuple[tuple[str, ...], ...]} Additional physical header rows rendered before header/body separator.
- @param rows {tuple[tuple[str, ...], ...]} Table body rows with one value per column.
- @return {None} Writes formatted table to stdout.
- @satisfies REQ-070

### fn `def _line(values)` `priv` (L251-254)

### fn `def _build_two_line_operator_rows(operator_entries)` `priv` (L265-281)
- @brief Build two-line physical rows for luminance operator table.
- @details Expands each logical operator entry into two physical rows while preserving the bordered three-column layout used by help rendering.
- @param operator_entries {tuple[tuple[str, str, str, str, str], ...]} Logical operator rows in `(operator, family, character, neutrality, when_to_use)` format.
- @return {tuple[tuple[str, str, str], ...]} Expanded physical rows for `_print_box_table`.
- @satisfies REQ-070

### fn `def print_help(version)` (L282-361)
- @brief Print help text for the `dng2hdr2jpg` command.
- @details Documents required positional arguments, optional EV/RAW gamma controls, shared postprocessing controls, backend selection, and luminance-hdr-cli tone-mapping options.
- @param version {str} CLI version label to append in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008, REQ-063, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-075

### fn `def _parse_ev_option(ev_raw)` `priv` (L362-386)
- @brief Parse and validate one EV option value.
- @details Converts the raw token to `float` and validates membership against the supported EV value set used by bracket multiplier computation.
- @param ev_raw {str} EV token extracted from command arguments.
- @return {float|None} Parsed EV value when valid; `None` otherwise.
- @satisfies REQ-056

### fn `def _parse_luminance_text_option(option_name, option_raw)` `priv` (L387-407)
- @brief Parse and validate non-empty luminance string option value.
- @details Normalizes surrounding spaces, lowercases token, rejects empty values, and rejects ambiguous values that start with option prefix marker.
- @param option_name {str} Long-option identifier used in error messages.
- @param option_raw {str} Raw option token value from CLI args.
- @return {str|None} Parsed normalized option token when valid; `None` otherwise.
- @satisfies REQ-061

### fn `def _parse_gamma_option(gamma_raw)` `priv` (L408-444)
- @brief Parse and validate one gamma option value pair.
- @details Accepts comma-separated positive float pair in `a,b` format with optional surrounding parentheses, normalizes to `(a, b)` tuple, and rejects malformed, non-numeric, or non-positive values.
- @param gamma_raw {str} Raw gamma token extracted from CLI args.
- @return {tuple[float, float]|None} Parsed gamma tuple when valid; `None` otherwise.
- @satisfies REQ-064

### fn `def _parse_positive_float_option(option_name, option_raw)` `priv` (L445-468)
- @brief Parse and validate one positive float option value.
- @details Converts option token to `float`, requires value greater than zero, and emits deterministic parse errors on malformed values.
- @param option_name {str} Long-option identifier used in error messages.
- @param option_raw {str} Raw option token value from CLI args.
- @return {float|None} Parsed positive float value when valid; `None` otherwise.
- @satisfies REQ-065

### fn `def _parse_tmo_passthrough_value(option_name, option_raw)` `priv` (L469-485)
- @brief Parse and validate one luminance `--tmo*` passthrough value.
- @details Rejects empty values and preserves original payload for transparent forwarding to `luminance-hdr-cli`.
- @param option_name {str} Long-option identifier used in error messages.
- @param option_raw {str} Raw option token value from CLI args.
- @return {str|None} Original value when valid; `None` otherwise.
- @satisfies REQ-067

### fn `def _parse_jpg_compression_option(compression_raw)` `priv` (L486-508)
- @brief Parse and validate JPEG compression option value.
- @details Converts option token to `int`, requires inclusive range `[0, 100]`, and emits deterministic parse errors on malformed values.
- @param compression_raw {str} Raw compression token value from CLI args.
- @return {int|None} Parsed JPEG compression level when valid; `None` otherwise.
- @satisfies REQ-065

### fn `def _parse_wow_mode_option(wow_raw)` `priv` (L509-532)
- @brief Parse wow implementation selector option value.
- @details Accepts case-insensitive wow implementation names and normalizes to canonical values for runtime dispatch.
- @param wow_raw {str} Raw wow implementation token.
- @return {str|None} Canonical wow mode (`ImageMagick` or `OpenCV`) or `None` on parse failure.
- @satisfies REQ-065, REQ-073, REQ-075

### fn `def _resolve_default_postprocess(enable_luminance, luminance_tmo)` `priv` (L533-567)
- @brief Resolve backend-specific postprocess defaults.
- @details Selects neutral defaults for enfuse and non-`reinhard02` luminance operators, and selects tuned defaults for luminance `reinhard02`.
- @param enable_luminance {bool} Backend selector state.
- @param luminance_tmo {str} Selected luminance tone-mapping operator.
- @return {tuple[float, float, float, float]} Defaults in `(post_gamma, brightness, contrast, saturation)` order.
- @satisfies REQ-069, REQ-071, REQ-072

### fn `def _parse_run_options(args)` `priv` (L568-767)
- @brief Parse CLI args into input, output, and EV parameters.
- @details Supports positional file arguments, optional `--ev=<value>` or `--ev <value>`, optional `--gamma=<a,b>` or `--gamma <a,b>`, optional postprocess controls, required backend selector (`--enable-enfuse` or `--enable-luminance`), and luminance backend controls including explicit `--tmo*` passthrough options, optional wow implementation selector (`--wow <ImageMagick|OpenCV>`); rejects unknown options and invalid arity.
- @param args {list[str]} Raw command argument vector.
- @return {tuple[Path, Path, float, tuple[float, float], PostprocessOptions, bool, LuminanceOptions]|None} Parsed `(input, output, ev, gamma, postprocess, enable_luminance, luminance_options)` tuple; `None` on parse failure.
- @satisfies REQ-055, REQ-056, REQ-060, REQ-061, REQ-064, REQ-065, REQ-067, REQ-069, REQ-071, REQ-072, REQ-073, REQ-075

### fn `def _load_image_dependencies()` `priv` (L953-989)
- @brief Load optional Python dependencies required by `dng2hdr2jpg`.
- @details Imports `rawpy` for RAW decoding and `imageio` for image IO using `imageio.v3` when available with fallback to top-level `imageio` module.
- @return {tuple[ModuleType, ModuleType, ModuleType, ModuleType]|None} `(rawpy_module, imageio_module, pil_image_module, pil_enhance_module)` on success; `None` on missing dependency.
- @satisfies REQ-059, REQ-066, REQ-074

### fn `def _parse_exif_datetime_to_timestamp(datetime_raw)` `priv` (L990-1014)
- @brief Parse one EXIF datetime token into POSIX timestamp.
- @details Normalizes scalar EXIF datetime input (`str` or `bytes`) and parses strict EXIF format `YYYY:MM:DD HH:MM:SS` to generate filesystem timestamp.
- @param datetime_raw {str|bytes|object} EXIF datetime scalar.
- @return {float|None} Parsed POSIX timestamp; `None` when value is missing or invalid.
- @satisfies REQ-074

### fn `def _extract_dng_exif_payload_and_timestamp(pil_image_module, input_dng)` `priv` (L1015-1046)
- @brief Extract DNG EXIF payload bytes and preferred datetime timestamp.
- @details Opens input DNG via Pillow, reads EXIF mapping, serializes payload for JPEG `exif` save parameter, and resolves filesystem timestamp priority: `DateTimeOriginal`(36867) > `DateTimeDigitized`(36868) > `DateTime`(306).
- @param pil_image_module {ModuleType} Imported Pillow Image module.
- @param input_dng {Path} Source DNG path.
- @return {tuple[bytes|None, float|None]} `(exif_payload, exif_timestamp)` with `None` for unavailable components.
- @satisfies REQ-066, REQ-074

### fn `def _set_output_file_timestamps(output_jpg, exif_timestamp)` `priv` (L1047-1061)
- @brief Set output JPG atime and mtime from EXIF timestamp.
- @details Applies EXIF-derived POSIX timestamp to both access and modification times using `os.utime`.
- @param output_jpg {Path} Output JPG path.
- @param exif_timestamp {float} Source EXIF-derived POSIX timestamp.
- @return {None} Side effects only.
- @exception OSError Raised when filesystem metadata update fails.
- @satisfies REQ-074

### fn `def _build_exposure_multipliers(ev_value)` `priv` (L1062-1074)
- @brief Compute bracketing brightness multipliers from EV value.
- @details Produces exactly three multipliers mapped to exposure stops `[-ev, 0, +ev]` as powers of two for RAW postprocess brightness control.
- @param ev_value {float} Exposure bracket EV delta.
- @return {tuple[float, float, float]} Multipliers in order `(under, base, over)`.
- @satisfies REQ-057

### fn `def _write_bracket_images(raw_handle, imageio_module, multipliers, gamma_value, temp_dir)` `priv` (L1075-1108)
- @brief Materialize three bracket TIFF files from one RAW handle.
- @details Invokes `raw.postprocess` with `output_bps=16`, `use_camera_wb=True`, `no_auto_bright=True`, and configurable gamma pair for deterministic HDR-oriented bracket extraction before merge.
- @param raw_handle {Any} Opened RAW handle from `rawpy.imread`.
- @param imageio_module {ModuleType} Imported imageio module with `imwrite`.
- @param multipliers {tuple[float, float, float]} Ordered exposure multipliers.
- @param gamma_value {tuple[float, float]} Gamma pair forwarded to RAW postprocess.
- @param temp_dir {Path} Directory for intermediate TIFF artifacts.
- @return {list[Path]} Ordered temporary TIFF file paths.
- @satisfies REQ-057

### fn `def _order_bracket_paths(bracket_paths)` `priv` (L1109-1134)
- @brief Validate and reorder bracket TIFF paths for deterministic backend argv.
- @details Enforces exact exposure order `<ev_minus.tif> <ev_zero.tif> <ev_plus.tif>` required by luminance-hdr-cli command generation and raises on missing labels.
- @param bracket_paths {list[Path]} Temporary bracket TIFF paths generated from RAW.
- @return {list[Path]} Reordered bracket path list in deterministic exposure order.
- @exception ValueError Raised when any expected bracket label is missing.
- @satisfies REQ-062

### fn `def _run_enfuse(bracket_paths, merged_tiff)` `priv` (L1135-1155)
- @brief Merge bracket TIFF files into one HDR TIFF via `enfuse`.
- @details Builds deterministic enfuse argv with LZW compression and executes subprocess in checked mode to propagate command failures.
- @param bracket_paths {list[Path]} Ordered intermediate exposure TIFF paths.
- @param merged_tiff {Path} Output merged TIFF target path.
- @return {None} Side effects only.
- @exception subprocess.CalledProcessError Raised when `enfuse` returns non-zero exit status.
- @satisfies REQ-058

### fn `def _run_luminance_hdr_cli(bracket_paths, output_hdr_tiff, ev_value, luminance_options)` `priv` (L1156-1195)
- @brief Merge bracket TIFF files into one HDR TIFF via `luminance-hdr-cli`.
- @details Builds deterministic luminance-hdr-cli argv using EV sequence, HDR model controls, tone-mapper controls, mandatory `--ldrTiff 16b`, optional explicit `--tmo*` passthrough arguments, and ordered exposure inputs (`ev_minus`, `ev_zero`, `ev_plus`), then writes to TIFF output path used by shared postprocess conversion.
- @param bracket_paths {list[Path]} Ordered intermediate exposure TIFF paths.
- @param output_hdr_tiff {Path} Output HDR TIFF target path.
- @param ev_value {float} EV bracket delta used to generate exposure files.
- @param luminance_options {LuminanceOptions} Luminance backend command controls.
- @return {None} Side effects only.
- @exception subprocess.CalledProcessError Raised when `luminance-hdr-cli` returns non-zero exit status.
- @satisfies REQ-060, REQ-061, REQ-062, REQ-067, REQ-068

### fn `def _convert_compression_to_quality(jpg_compression)` `priv` (L1196-1208)
- @brief Convert JPEG compression level to Pillow quality value.
- @details Maps inclusive compression range `[0, 100]` to inclusive quality range `[100, 1]` preserving deterministic inverse relation.
- @param jpg_compression {int} JPEG compression level.
- @return {int} Pillow quality value in `[1, 100]`.
- @satisfies REQ-065, REQ-066

### fn `def _resolve_imagemagick_command()` `priv` (L1209-1226)
- @brief Resolve ImageMagick executable name for current runtime.
- @details Probes `magick` first (ImageMagick 7+ preferred CLI), then `convert` (legacy-compatible CLI alias) to preserve wow-stage compatibility across distributions that package ImageMagick under different executable names.
- @return {str|None} Resolved executable token (`magick` or `convert`) or `None` when no supported executable is available.
- @satisfies REQ-059, REQ-073

### fn `def _resolve_wow_opencv_dependencies()` `priv` (L1227-1250)
- @brief Resolve OpenCV wow runtime dependencies.
- @details Imports `cv2` and `numpy` modules required by OpenCV wow pipeline execution and returns `None` with deterministic error output when missing.
- @return {tuple[ModuleType, ModuleType]|None} `(cv2_module, numpy_module)` when available; `None` on dependency failure.
- @satisfies REQ-059, REQ-073, REQ-075

### fn `def _apply_validated_wow_pipeline(postprocessed_input, wow_output, imagemagick_command)` `priv` (L1251-1328)
- @brief Execute validated wow pipeline over temporary lossless 16-bit TIFF files.
- @details Uses ImageMagick to normalize source data to 16-bit-per-channel TIFF, applies deterministic denoise/level/sigmoidal/vibrance/high-pass overlay stages, and writes lossless wow output artifact consumed by JPG encoder.
- @param postprocessed_input {Path} Temporary postprocess image input path.
- @param wow_output {Path} Temporary wow output TIFF path.
- @param imagemagick_command {str} Resolved ImageMagick executable token.
- @return {None} Side effects only.
- @exception subprocess.CalledProcessError Raised when ImageMagick returns non-zero.
- @satisfies REQ-073

### fn `def _clamp01(np_module, values)` `priv` (L1329-1342)
- @brief Clamp numeric image tensor values into `[0.0, 1.0]` interval.
- @details Applies vectorized clipping to ensure deterministic bounded values for OpenCV wow pipeline float-domain operations.
- @param np_module {ModuleType} Imported numpy module.
- @param values {object} Numeric tensor-like payload.
- @return {object} Clipped tensor payload.
- @satisfies REQ-075

### fn `def _gaussian_kernel_2d(np_module, sigma, radius=None)` `priv` (L1343-1365)
- @brief Build normalized 2D Gaussian kernel.
- @details Creates deterministic Gaussian kernel used by selective blur stage; returns identity kernel when `sigma <= 0`.
- @param np_module {ModuleType} Imported numpy module.
- @param sigma {float} Gaussian sigma value.
- @param radius {int|None} Optional kernel radius override.
- @return {object} Normalized 2D kernel tensor.
- @satisfies REQ-075

### fn `def _rgb_to_hsl(np_module, rgb)` `priv` (L1366-1397)
- @brief Convert RGB float tensor to HSL channels.
- @details Implements explicit HSL conversion for OpenCV wow saturation-gamma stage without delegating to external color-space helpers.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB tensor in `[0.0, 1.0]`.
- @return {tuple[object, object, object]} `(h, s, l)` channel tensors.
- @satisfies REQ-075

### fn `def _hue_to_rgb(np_module, p_values, q_values, t_values)` `priv` (L1398-1423)
- @brief Convert one hue-shift channel to RGB component.
- @details Evaluates piecewise hue interpolation branch used by HSL-to-RGB conversion in OpenCV wow pipeline.
- @param np_module {ModuleType} Imported numpy module.
- @param p_values {object} Lower chroma interpolation boundary.
- @param q_values {object} Upper chroma interpolation boundary.
- @param t_values {object} Hue-shifted channel tensor.
- @return {object} RGB component tensor.
- @satisfies REQ-075

### fn `def _hsl_to_rgb(np_module, hue, saturation, lightness)` `priv` (L1424-1458)
- @brief Convert HSL channels to RGB float tensor.
- @details Reconstructs RGB tensor with explicit achromatic/chromatic branches for OpenCV wow saturation-gamma stage.
- @param np_module {ModuleType} Imported numpy module.
- @param hue {object} Hue channel tensor.
- @param saturation {object} Saturation channel tensor.
- @param lightness {object} Lightness channel tensor.
- @return {object} RGB tensor in `[0.0, 1.0]`.
- @satisfies REQ-075

### fn `def _selective_blur_contrast_gated_vectorized(np_module, rgb, sigma=2.0, threshold_percent=10.0)` `priv` (L1459-1496)
- @brief Execute contrast-gated selective blur stage.
- @details Applies vectorized contrast-gated neighborhood accumulation over Gaussian kernel offsets to emulate selective blur behavior.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
- @param sigma {float} Gaussian sigma.
- @param threshold_percent {float} Luma-difference threshold percent.
- @return {object} Blurred RGB float tensor.
- @satisfies REQ-075

### fn `def _level_per_channel_adaptive(np_module, rgb, low_pct=0.1, high_pct=99.9)` `priv` (L1497-1519)
- @brief Execute adaptive per-channel level normalization.
- @details Applies percentile-based level stretching independently for each RGB channel.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
- @param low_pct {float} Low percentile threshold.
- @param high_pct {float} High percentile threshold.
- @return {object} Level-normalized RGB float tensor.
- @satisfies REQ-075

### fn `def _sigmoidal_contrast(np_module, rgb, contrast=3.0, midpoint=0.5)` `priv` (L1520-1542)
- @brief Execute sigmoidal contrast stage.
- @details Applies logistic remapping with bounded normalization for each RGB channel.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
- @param contrast {float} Logistic slope.
- @param midpoint {float} Logistic midpoint.
- @return {object} Contrast-adjusted RGB float tensor.
- @satisfies REQ-075

### fn `def logistic(z_values)` (L1534-1535)
- @brief Execute sigmoidal contrast stage.
- @details Applies logistic remapping with bounded normalization for each RGB
channel.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
- @param contrast {float} Logistic slope.
- @param midpoint {float} Logistic midpoint.
- @return {object} Contrast-adjusted RGB float tensor.
- @satisfies REQ-075

### fn `def _vibrance_hsl_gamma(np_module, rgb, saturation_gamma=0.8)` `priv` (L1543-1560)
- @brief Execute HSL saturation gamma stage.
- @details Converts RGB to HSL, applies saturation gamma transform, and converts back to RGB.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
- @param saturation_gamma {float} Saturation gamma denominator value.
- @return {object} Saturation-adjusted RGB float tensor.
- @satisfies REQ-075

### fn `def _gaussian_blur_rgb(cv2_module, np_module, rgb, sigma)` `priv` (L1561-1584)
- @brief Execute RGB Gaussian blur with reflected border mode.
- @details Computes odd kernel size from sigma and applies OpenCV Gaussian blur preserving reflected border behavior.
- @param cv2_module {ModuleType} Imported cv2 module.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
- @param sigma {float} Gaussian sigma.
- @return {object} Blurred RGB float tensor.
- @satisfies REQ-075

### fn `def _high_pass_math_gray(cv2_module, np_module, rgb, blur_sigma=2.5)` `priv` (L1585-1604)
- @brief Execute high-pass math grayscale stage.
- @details Computes high-pass response as `A - B + 0.5` over RGB channels and converts to luminance grayscale tensor.
- @param cv2_module {ModuleType} Imported cv2 module.
- @param np_module {ModuleType} Imported numpy module.
- @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
- @param blur_sigma {float} Gaussian blur sigma for high-pass base.
- @return {object} Grayscale float tensor in `[0.0, 1.0]`.
- @satisfies REQ-075

### fn `def _overlay_composite(np_module, base_rgb, overlay_gray)` `priv` (L1605-1626)
- @brief Execute overlay composite stage.
- @details Applies conditional overlay blend equation over RGB base and grayscale overlay tensors.
- @param np_module {ModuleType} Imported numpy module.
- @param base_rgb {object} Base RGB float tensor in `[0.0, 1.0]`.
- @param overlay_gray {object} Overlay grayscale tensor in `[0.0, 1.0]`.
- @return {object} Overlay-composited RGB float tensor.
- @satisfies REQ-075

### fn `def _apply_validated_wow_pipeline_opencv(input_file, output_file, cv2_module, np_module)` `priv` (L1627-1665)
- @brief Execute validated wow pipeline using OpenCV and numpy.
- @details Reads 16-bit RGB image, performs explicit 16-bit-to-float normalization, executes selective blur, adaptive levels, sigmoidal contrast, HSL saturation gamma, high-pass/overlay stages, then restores float payload to 16-bit-per-channel RGB TIFF output.
- @param input_file {Path} Source TIFF path.
- @param output_file {Path} Output TIFF path.
- @param cv2_module {ModuleType} Imported cv2 module.
- @param np_module {ModuleType} Imported numpy module.
- @return {None} Side effects only.
- @exception OSError Raised when source file is missing.
- @exception RuntimeError Raised when OpenCV read/write fails.
- @satisfies REQ-073, REQ-075

### fn `def _encode_jpg(` `priv` (L1666-1675)

### fn `def _collect_processing_errors(rawpy_module)` `priv` (L1794-1822)
- @brief Encode merged HDR TIFF payload into final JPG output.
- @brief Build deterministic tuple of recoverable processing exceptions.
- @details Loads merged image payload, down-converts to `uint8` when source
dynamic range exceeds JPEG-native depth, applies shared gamma/brightness/
contrast/saturation postprocessing, optionally executes wow stage over
temporary lossless 16-bit TIFF intermediates, and writes JPEG with
configured compression level for both HDR backends.
- @details Combines common IO/value/subprocess errors with rawpy-specific decoding error classes when present in runtime module version.
- @param imageio_module {ModuleType} Imported imageio module with `imread` and `imwrite`.
- @param pil_image_module {ModuleType} Imported Pillow image module.
- @param pil_enhance_module {ModuleType} Imported Pillow ImageEnhance module.
- @param merged_tiff {Path} Merged TIFF source path produced by `enfuse`.
- @param output_jpg {Path} Final JPG output path.
- @param postprocess_options {PostprocessOptions} Shared TIFF-to-JPG correction settings.
- @param imagemagick_command {str|None} Optional pre-resolved ImageMagick executable.
- @param wow_opencv_dependencies {tuple[ModuleType, ModuleType]|None} Optional `(cv2, numpy)` modules for OpenCV wow implementation.
- @param source_exif_payload {bytes|None} Serialized EXIF payload copied from input DNG.
- @param rawpy_module {ModuleType} Imported rawpy module.
- @return {None} Side effects only.
- @return {tuple[type[BaseException], ...]} Ordered deduplicated exception class tuple.
- @exception RuntimeError Raised when wow mode dependencies are missing or wow mode value is unsupported.
- @satisfies REQ-058, REQ-066, REQ-069, REQ-073, REQ-074, REQ-075
- @satisfies REQ-059

### fn `def _is_supported_runtime_os()` `priv` (L1823-1842)
- @brief Validate runtime platform support for `dng2hdr2jpg`.
- @details Accepts Linux runtime only; emits explicit non-Linux unsupported message that includes OS label (`Windows` or `MacOS`) for deterministic UX.
- @return {bool} `True` when runtime OS is Linux; `False` otherwise.
- @satisfies REQ-055, REQ-059

### fn `def run(args)` (L1843-1983)
- @brief Execute `dng2hdr2jpg` command pipeline.
- @details Parses command options, validates dependencies, extracts three RAW brackets, executes selected `enfuse` flow or selected luminance-hdr-cli flow, writes JPG output, and guarantees temporary artifact cleanup through isolated temporary directory lifecycle.
- @param args {list[str]} Command argument vector excluding command token.
- @return {int} `0` on success; `1` on parse/validation/dependency/processing failure.
- @satisfies REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|27||
|`DESCRIPTION`|var|pub|28||
|`DEFAULT_EV`|var|pub|29||
|`DEFAULT_GAMMA`|var|pub|30||
|`DEFAULT_POST_GAMMA`|var|pub|31||
|`DEFAULT_BRIGHTNESS`|var|pub|32||
|`DEFAULT_CONTRAST`|var|pub|33||
|`DEFAULT_SATURATION`|var|pub|34||
|`DEFAULT_JPG_COMPRESSION`|var|pub|35||
|`DEFAULT_LUMINANCE_HDR_MODEL`|var|pub|36||
|`DEFAULT_LUMINANCE_HDR_WEIGHT`|var|pub|37||
|`DEFAULT_LUMINANCE_HDR_RESPONSE_CURVE`|var|pub|38||
|`DEFAULT_LUMINANCE_TMO`|var|pub|39||
|`DEFAULT_REINHARD02_BRIGHTNESS`|var|pub|40||
|`DEFAULT_REINHARD02_CONTRAST`|var|pub|41||
|`DEFAULT_REINHARD02_SATURATION`|var|pub|42||
|`SUPPORTED_EV_VALUES`|var|pub|43||
|`PostprocessOptions`|class|pub|183-205|class PostprocessOptions|
|`LuminanceOptions`|class|pub|207-227|class LuminanceOptions|
|`_print_box_table`|fn|priv|228-264|def _print_box_table(headers, rows, header_rows=())|
|`_border`|fn|priv|248-250|def _border(left, middle, right)|
|`_line`|fn|priv|251-254|def _line(values)|
|`_build_two_line_operator_rows`|fn|priv|265-281|def _build_two_line_operator_rows(operator_entries)|
|`print_help`|fn|pub|282-361|def print_help(version)|
|`_parse_ev_option`|fn|priv|362-386|def _parse_ev_option(ev_raw)|
|`_parse_luminance_text_option`|fn|priv|387-407|def _parse_luminance_text_option(option_name, option_raw)|
|`_parse_gamma_option`|fn|priv|408-444|def _parse_gamma_option(gamma_raw)|
|`_parse_positive_float_option`|fn|priv|445-468|def _parse_positive_float_option(option_name, option_raw)|
|`_parse_tmo_passthrough_value`|fn|priv|469-485|def _parse_tmo_passthrough_value(option_name, option_raw)|
|`_parse_jpg_compression_option`|fn|priv|486-508|def _parse_jpg_compression_option(compression_raw)|
|`_parse_wow_mode_option`|fn|priv|509-532|def _parse_wow_mode_option(wow_raw)|
|`_resolve_default_postprocess`|fn|priv|533-567|def _resolve_default_postprocess(enable_luminance, lumina...|
|`_parse_run_options`|fn|priv|568-767|def _parse_run_options(args)|
|`_load_image_dependencies`|fn|priv|953-989|def _load_image_dependencies()|
|`_parse_exif_datetime_to_timestamp`|fn|priv|990-1014|def _parse_exif_datetime_to_timestamp(datetime_raw)|
|`_extract_dng_exif_payload_and_timestamp`|fn|priv|1015-1046|def _extract_dng_exif_payload_and_timestamp(pil_image_mod...|
|`_set_output_file_timestamps`|fn|priv|1047-1061|def _set_output_file_timestamps(output_jpg, exif_timestamp)|
|`_build_exposure_multipliers`|fn|priv|1062-1074|def _build_exposure_multipliers(ev_value)|
|`_write_bracket_images`|fn|priv|1075-1108|def _write_bracket_images(raw_handle, imageio_module, mul...|
|`_order_bracket_paths`|fn|priv|1109-1134|def _order_bracket_paths(bracket_paths)|
|`_run_enfuse`|fn|priv|1135-1155|def _run_enfuse(bracket_paths, merged_tiff)|
|`_run_luminance_hdr_cli`|fn|priv|1156-1195|def _run_luminance_hdr_cli(bracket_paths, output_hdr_tiff...|
|`_convert_compression_to_quality`|fn|priv|1196-1208|def _convert_compression_to_quality(jpg_compression)|
|`_resolve_imagemagick_command`|fn|priv|1209-1226|def _resolve_imagemagick_command()|
|`_resolve_wow_opencv_dependencies`|fn|priv|1227-1250|def _resolve_wow_opencv_dependencies()|
|`_apply_validated_wow_pipeline`|fn|priv|1251-1328|def _apply_validated_wow_pipeline(postprocessed_input, wo...|
|`_clamp01`|fn|priv|1329-1342|def _clamp01(np_module, values)|
|`_gaussian_kernel_2d`|fn|priv|1343-1365|def _gaussian_kernel_2d(np_module, sigma, radius=None)|
|`_rgb_to_hsl`|fn|priv|1366-1397|def _rgb_to_hsl(np_module, rgb)|
|`_hue_to_rgb`|fn|priv|1398-1423|def _hue_to_rgb(np_module, p_values, q_values, t_values)|
|`_hsl_to_rgb`|fn|priv|1424-1458|def _hsl_to_rgb(np_module, hue, saturation, lightness)|
|`_selective_blur_contrast_gated_vectorized`|fn|priv|1459-1496|def _selective_blur_contrast_gated_vectorized(np_module, ...|
|`_level_per_channel_adaptive`|fn|priv|1497-1519|def _level_per_channel_adaptive(np_module, rgb, low_pct=0...|
|`_sigmoidal_contrast`|fn|priv|1520-1542|def _sigmoidal_contrast(np_module, rgb, contrast=3.0, mid...|
|`logistic`|fn|pub|1534-1535|def logistic(z_values)|
|`_vibrance_hsl_gamma`|fn|priv|1543-1560|def _vibrance_hsl_gamma(np_module, rgb, saturation_gamma=...|
|`_gaussian_blur_rgb`|fn|priv|1561-1584|def _gaussian_blur_rgb(cv2_module, np_module, rgb, sigma)|
|`_high_pass_math_gray`|fn|priv|1585-1604|def _high_pass_math_gray(cv2_module, np_module, rgb, blur...|
|`_overlay_composite`|fn|priv|1605-1626|def _overlay_composite(np_module, base_rgb, overlay_gray)|
|`_apply_validated_wow_pipeline_opencv`|fn|priv|1627-1665|def _apply_validated_wow_pipeline_opencv(input_file, outp...|
|`_encode_jpg`|fn|priv|1666-1675|def _encode_jpg(|
|`_collect_processing_errors`|fn|priv|1794-1822|def _collect_processing_errors(rawpy_module)|
|`_is_supported_runtime_os`|fn|priv|1823-1842|def _is_supported_runtime_os()|
|`run`|fn|pub|1843-1983|def run(args)|


---

# doxygen_cmd.py | Python | 157L | 7 symbols | 8 imports | 2 comments
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

### fn `def _supports_generate_markdown()` `priv` (L25-37)

### fn `def _write_doxyfile(path, project_root, src_dir, doxygen_dir, has_md)` `priv` (L38-39)

### fn `def _generate_markdown_fallback(xml_dir, markdown_dir)` `priv` (L75-97)

### fn `def run(args)` (L98-157)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|11||
|`DESCRIPTION`|var|pub|12||
|`print_help`|fn|pub|15-24|def print_help(version)|
|`_supports_generate_markdown`|fn|priv|25-37|def _supports_generate_markdown()|
|`_write_doxyfile`|fn|priv|38-39|def _write_doxyfile(path, project_root, src_dir, doxygen_...|
|`_generate_markdown_fallback`|fn|priv|75-97|def _generate_markdown_fallback(xml_dir, markdown_dir)|
|`run`|fn|pub|98-157|def run(args)|


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

# pdf_crop.py | Python | 522L | 27 symbols | 7 imports | 1 comments
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

### fn `def _convert_pdf_with_progress(input_f, output_f, first, last, cw, ch, cl, cb, total)` `priv` (L271-315)

### fn `def run(args)` (L316-515)

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
|`_convert_pdf_with_progress`|fn|priv|271-315|def _convert_pdf_with_progress(input_f, output_f, first, ...|
|`run`|fn|pub|316-515|def run(args)|


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

# pdf_tiler_090.py | Python | 49L | 4 symbols | 3 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_tiler_090.py`

## Imports
```
import os
from pathlib import Path
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Tile PDF to A4 pages at 90% scale using plakativ."` (L8)
### fn `def print_help(version)` (L11-20)

### fn `def run(args)` (L21-49)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-20|def print_help(version)|
|`run`|fn|pub|21-49|def run(args)|


---

# pdf_tiler_100.py | Python | 49L | 4 symbols | 3 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_tiler_100.py`

## Imports
```
import os
from pathlib import Path
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Tile PDF to A4 pages at original A1 size using plakativ."` (L8)
### fn `def print_help(version)` (L11-20)

### fn `def run(args)` (L21-49)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-20|def print_help(version)|
|`run`|fn|pub|21-49|def run(args)|


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

# req_cmd.py | Python | 242L | 9 symbols | 6 imports | 9 comments
> Path: `src/shell_scripts/commands/req_cmd.py`

## Imports
```
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from shell_scripts.config import get_req_profile
from shell_scripts.utils import print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L21)
- var `DESCRIPTION = "Run useReq bootstrap on current or discovered directories."` (L22)
### fn `def _is_hidden_path(path: Path, base_dir: Path) -> bool` `priv` (L53-67)
- @brief Determine whether path contains hidden segments below base.
- @details Computes relative parts from `base_dir` and returns `True` when any path segment starts with a dot-prefix, preventing accidental traversal of hidden metadata directories (for example `.git`).
- @param path {Path} Candidate directory path.
- @param base_dir {Path} Root directory used for relative-segment evaluation.
- @return {bool} `True` when candidate has hidden relative segments.
- @satisfies REQ-052, REQ-053

### fn `def print_help(version: str) -> None` (L68-85)
- @brief Render command help for `req`.
- @details Prints selector options and behavior contract for target directory discovery and external `req` invocation flow.
- @param version {str} CLI version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def _iter_first_level_dirs(base_dir: Path) -> list[Path]` `priv` (L86-105)
- @brief Collect first-level child directories in deterministic order.
- @details Enumerates direct children of `base_dir`, keeps only directories, and sorts by path string for stable command behavior.
- @param base_dir {Path} Directory whose first-level children are listed.
- @return {list[Path]} Sorted first-level child directories.
- @satisfies REQ-052

### fn `def _iter_descendant_dirs(base_dir: Path) -> list[Path]` `priv` (L106-125)
- @brief Collect descendant directories recursively in deterministic order.
- @details Traverses all descendants via glob expansion, excludes `base_dir` itself, keeps only directories, and sorts by path string.
- @param base_dir {Path} Directory whose descendants are listed.
- @return {list[Path]} Sorted descendant directory list excluding `base_dir`.
- @satisfies REQ-053

### fn `def _build_req_args(target_dir: Path) -> list[str]` `priv` (L126-161)
- @brief Build external `req` argument vector for one target directory.
- @details Uses hardcoded non-overridable arguments and appends repeated runtime-configured providers/static-check entries sourced from `get_req_profile`.
- @param target_dir {Path} Target directory used to parameterize path flags.
- @return {list[str]} External `req` argv vector.
- @satisfies REQ-049, REQ-050

### fn `def _prepare_target_directory(target_dir: Path) -> None` `priv` (L162-177)
- @brief Apply cleanup and scaffold operations for one target directory.
- @details Removes each predefined integration directory if present and ensures required project subdirectories exist before external `req` call.
- @param target_dir {Path} Target directory to mutate.
- @return {None} Performs filesystem side effects.
- @satisfies REQ-048

### fn `def run(args: list[str]) -> int` (L178-242)
- @brief Execute `req` orchestration for selected directory targets.
- @details Parses mutually exclusive selector options, resolves target set, applies cleanup/scaffold phase, and executes external `req` for each target. Returns `1` on invalid option combinations or unknown options. Converts external `req` non-zero exits into explicit error output and propagated return codes.
- @param args {list[str]} Command arguments excluding `req` token.
- @return {int} `0` on success; non-zero for option or subprocess failures.
- @exception {subprocess.CalledProcessError} Internally handled and converted to deterministic return code + error output.
- @satisfies REQ-048, REQ-049, REQ-051, REQ-052, REQ-053, REQ-054

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|21||
|`DESCRIPTION`|var|pub|22||
|`_is_hidden_path`|fn|priv|53-67|def _is_hidden_path(path: Path, base_dir: Path) -> bool|
|`print_help`|fn|pub|68-85|def print_help(version: str) -> None|
|`_iter_first_level_dirs`|fn|priv|86-105|def _iter_first_level_dirs(base_dir: Path) -> list[Path]|
|`_iter_descendant_dirs`|fn|priv|106-125|def _iter_descendant_dirs(base_dir: Path) -> list[Path]|
|`_build_req_args`|fn|priv|126-161|def _build_req_args(target_dir: Path) -> list[str]|
|`_prepare_target_directory`|fn|priv|162-177|def _prepare_target_directory(target_dir: Path) -> None|
|`run`|fn|pub|178-242|def run(args: list[str]) -> int|


---

# tests_cmd.py | Python | 62L | 4 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/tests_cmd.py`

## Imports
```
import os
import sys
import subprocess
from shell_scripts.utils import require_project_root, print_info, print_success
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Run pytest test suite in a Python virtual environment."` (L9)
### fn `def print_help(version)` (L12-19)

### fn `def run(args)` (L20-62)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-19|def print_help(version)|
|`run`|fn|pub|20-62|def run(args)|


---

# ubuntu_dark_theme.py | Python | 45L | 4 symbols | 3 imports | 1 comments
> Path: `src/shell_scripts/commands/ubuntu_dark_theme.py`

## Imports
```
import subprocess
from shell_scripts.utils import print_info, command_exists, print_error
import os
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "Apply GNOME and Qt dark theme settings."` (L7)
### fn `def print_help(version)` (L10-19)

### fn `def run(args)` (L20-45)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`print_help`|fn|pub|10-19|def print_help(version)|
|`run`|fn|pub|20-45|def run(args)|


---

# venv_cmd.py | Python | 59L | 4 symbols | 5 imports | 1 comments
> Path: `src/shell_scripts/commands/venv_cmd.py`

## Imports
```
import os
import sys
import shutil
import subprocess
from shell_scripts.utils import require_project_root, print_info, print_success
```

## Definitions

- var `PROGRAM = "shellscripts"` (L9)
- var `DESCRIPTION = "Create or recreate Python virtual environment with requirements."` (L10)
### fn `def print_help(version)` (L13-20)

### fn `def run(args)` (L21-59)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|9||
|`DESCRIPTION`|var|pub|10||
|`print_help`|fn|pub|13-20|def print_help(version)|
|`run`|fn|pub|21-59|def run(args)|


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

# vscode_cmd.py | Python | 24L | 4 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/vscode_cmd.py`

## Imports
```
import os
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "Open VS Code in the project root with Codex integration."` (L7)
### fn `def print_help(version)` (L10-17)

### fn `def run(args)` (L18-24)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`print_help`|fn|pub|10-17|def print_help(version)|
|`run`|fn|pub|18-24|def run(args)|


---

# vsinsider_cmd.py | Python | 24L | 4 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/vsinsider_cmd.py`

## Imports
```
import os
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "Open VS Code Insiders in the project root with Codex integration."` (L7)
### fn `def print_help(version)` (L10-17)

### fn `def run(args)` (L18-24)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`print_help`|fn|pub|10-17|def print_help(version)|
|`run`|fn|pub|18-24|def run(args)|


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

# core.py | Python | 181L | 6 symbols | 7 imports | 7 comments
> Path: `src/shell_scripts/core.py`

## Imports
```
import sys
import subprocess
from shell_scripts import __version__
from shell_scripts.config import (
from shell_scripts.version_check import check_for_updates
from shell_scripts.commands import get_command, get_all_commands
from shell_scripts.utils import detect_runtime_os, is_linux, print_error, print_info
```

## Definitions

- var `PROGRAM = "shellscripts"` (L23)
### fn `def print_help(command_name=None)` (L26-69)
- @brief Print global or command-specific help text.
- @details Renders command module help for known command names; otherwise exits with explicit unknown-command error. Global help includes management options and all command descriptions sorted by registry key.
- @param command_name {str|None} Optional command token for scoped help.
- @return {None} Writes to stdout/stderr; may terminate process on invalid command.
- @throws {SystemExit} Raised when unknown command name is requested.
- @satisfies PRJ-002, REQ-001, REQ-002

### fn `def do_upgrade()` (L70-91)
- @brief Execute Linux-only upgrade command resolved from runtime config.
- @details Reads management command string from runtime config key `management.upgrade`, executes it on Linux via shell invocation, and prints manual fallback command on non-Linux systems.
- @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-004, REQ-045

### fn `def do_uninstall()` (L92-113)
- @brief Execute Linux-only uninstall command resolved from runtime config.
- @details Reads management command string from runtime config key `management.uninstall`, executes it on Linux via shell invocation, and prints manual fallback command on non-Linux systems.
- @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-005, REQ-045

### fn `def do_write_config()` (L114-128)
- @brief Persist default runtime configuration file to disk.
- @details Writes canonical config JSON to `$HOME/.config/shellScripts/config.json` and logs destination path.
- @return {int} `0` on successful write.
- @throws {OSError} Propagated on filesystem write failure.
- @satisfies REQ-046

### fn `def main()` (L129-181)
- @brief Entrypoint for shellscripts argument dispatch.
- @details Performs runtime OS detection, update check, runtime configuration load, and argument dispatch through management flags and subcommands.
- @return {int} Process-compatible return code for caller (`sys.exit`).
- @satisfies PRJ-001, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|23||
|`print_help`|fn|pub|26-69|def print_help(command_name=None)|
|`do_upgrade`|fn|pub|70-91|def do_upgrade()|
|`do_uninstall`|fn|pub|92-113|def do_uninstall()|
|`do_write_config`|fn|pub|114-128|def do_write_config()|
|`main`|fn|pub|129-181|def main()|


---

# utils.py | Python | 160L | 30 symbols | 5 imports | 11 comments
> Path: `src/shell_scripts/utils.py`

## Imports
```
import os
import sys
import subprocess
import shutil
from pathlib import Path
```

## Definitions

- var `RESET = "\033[0m"` (L16)
- var `BOLD = "\033[1m"` (L17)
- var `RED = "\033[31m"` (L18)
- var `GREEN = "\033[32m"` (L19)
- var `YELLOW = "\033[33m"` (L20)
- var `BLUE = "\033[34m"` (L21)
- var `MAGENTA = "\033[35m"` (L22)
- var `CYAN = "\033[36m"` (L23)
- var `WHITE = "\033[37m"` (L24)
- var `BRIGHT_RED = "\033[91m"` (L25)
- var `BRIGHT_GREEN = "\033[92m"` (L26)
- var `BRIGHT_YELLOW = "\033[93m"` (L27)
- var `BRIGHT_BLUE = "\033[94m"` (L28)
- var `BRIGHT_CYAN = "\033[96m"` (L29)
- var `BRIGHT_WHITE = "\033[97m"` (L30)
### fn `def color_enabled()` (L40-45)
- @brief Cached normalized runtime operating-system token.
- @details Initialized on first detection and reused to guarantee stable
startup-level OS semantics across command execution flow.
- @satisfies DES-002, REQ-047

### fn `def c(text, color)` (L46-51)

### fn `def print_info(msg)` (L52-55)

### fn `def print_error(msg)` (L56-59)

### fn `def print_warn(msg)` (L60-63)

### fn `def print_success(msg)` (L64-67)

### fn `def get_project_root()` (L68-80)

### fn `def require_project_root()` (L81-88)

### fn `def detect_runtime_os()` (L89-111)
- @brief Detect and cache runtime operating-system token.
- @details Normalizes `sys.platform` into deterministic categories (`windows`, `linux`, `darwin`, `other`) and stores the result in module cache for subsequent calls. Time complexity O(1).
- @return {str} Normalized runtime operating-system token.
- @satisfies DES-002, REQ-047

### fn `def get_runtime_os()` (L112-125)
- @brief Return cached runtime operating-system token.
- @details Lazily initializes the cache via `detect_runtime_os` when unset, preserving a single startup-consistent OS classification.
- @return {str} Normalized runtime operating-system token.
- @satisfies DES-002, REQ-047

### fn `def is_windows()` (L126-136)
- @brief Check whether runtime operating system is Windows.
- @details Evaluates cached runtime token from `get_runtime_os`.
- @return {bool} `True` when runtime OS is Windows; otherwise `False`.
- @satisfies DES-013, REQ-008, REQ-047

### fn `def is_linux()` (L137-147)
- @brief Check whether runtime operating system is Linux.
- @details Evaluates cached runtime token from `get_runtime_os`.
- @return {bool} `True` when runtime OS is Linux; otherwise `False`.
- @satisfies CTN-004, REQ-004, REQ-005, REQ-047

### fn `def command_exists(cmd)` (L148-151)

### fn `def require_commands(*cmds)` (L152-158)

### fn `def run_cmd(cmd, **kwargs)` (L159-160)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`RESET`|var|pub|16||
|`BOLD`|var|pub|17||
|`RED`|var|pub|18||
|`GREEN`|var|pub|19||
|`YELLOW`|var|pub|20||
|`BLUE`|var|pub|21||
|`MAGENTA`|var|pub|22||
|`CYAN`|var|pub|23||
|`WHITE`|var|pub|24||
|`BRIGHT_RED`|var|pub|25||
|`BRIGHT_GREEN`|var|pub|26||
|`BRIGHT_YELLOW`|var|pub|27||
|`BRIGHT_BLUE`|var|pub|28||
|`BRIGHT_CYAN`|var|pub|29||
|`BRIGHT_WHITE`|var|pub|30||
|`color_enabled`|fn|pub|40-45|def color_enabled()|
|`c`|fn|pub|46-51|def c(text, color)|
|`print_info`|fn|pub|52-55|def print_info(msg)|
|`print_error`|fn|pub|56-59|def print_error(msg)|
|`print_warn`|fn|pub|60-63|def print_warn(msg)|
|`print_success`|fn|pub|64-67|def print_success(msg)|
|`get_project_root`|fn|pub|68-80|def get_project_root()|
|`require_project_root`|fn|pub|81-88|def require_project_root()|
|`detect_runtime_os`|fn|pub|89-111|def detect_runtime_os()|
|`get_runtime_os`|fn|pub|112-125|def get_runtime_os()|
|`is_windows`|fn|pub|126-136|def is_windows()|
|`is_linux`|fn|pub|137-147|def is_linux()|
|`command_exists`|fn|pub|148-151|def command_exists(cmd)|
|`require_commands`|fn|pub|152-158|def require_commands(*cmds)|
|`run_cmd`|fn|pub|159-160|def run_cmd(cmd, **kwargs)|


---

# version_check.py | Python | 119L | 17 symbols | 6 imports | 1 comments
> Path: `src/shell_scripts/version_check.py`

## Imports
```
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
```

## Definitions

- var `PROGRAM = "shellscripts"` (L9)
- var `OWNER = "Ogekuri"` (L10)
- var `REPOSITORY = "shellScripts"` (L11)
- var `IDLE_DELAY = 300` (L12)
- var `HTTP_TIMEOUT = 2` (L13)
- var `GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"` (L14)
- var `CACHE_DIR = Path.home() / ".cache" / PROGRAM` (L15)
- var `IDLE_TIME_FILE = CACHE_DIR / "check_version_idle-time.json"` (L16)
- var `BRIGHT_GREEN = "\033[92m"` (L18)
- var `BRIGHT_RED = "\033[91m"` (L19)
- var `RESET = "\033[0m"` (L20)
### fn `def _read_idle_config()` `priv` (L23-32)

### fn `def _write_idle_config(last_check_ts, idle_until_ts)` `priv` (L33-48)

### fn `def _should_check()` `priv` (L49-56)

### fn `def _compare_versions(current, latest)` `priv` (L57-65)

### fn `def parse(v)` (L58-59)

### fn `def check_for_updates(current_version)` (L66-119)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|9||
|`OWNER`|var|pub|10||
|`REPOSITORY`|var|pub|11||
|`IDLE_DELAY`|var|pub|12||
|`HTTP_TIMEOUT`|var|pub|13||
|`GITHUB_API_URL`|var|pub|14||
|`CACHE_DIR`|var|pub|15||
|`IDLE_TIME_FILE`|var|pub|16||
|`BRIGHT_GREEN`|var|pub|18||
|`BRIGHT_RED`|var|pub|19||
|`RESET`|var|pub|20||
|`_read_idle_config`|fn|priv|23-32|def _read_idle_config()|
|`_write_idle_config`|fn|priv|33-48|def _write_idle_config(last_check_ts, idle_until_ts)|
|`_should_check`|fn|priv|49-56|def _should_check()|
|`_compare_versions`|fn|priv|57-65|def _compare_versions(current, latest)|
|`parse`|fn|pub|58-59|def parse(v)|
|`check_for_updates`|fn|pub|66-119|def check_for_updates(current_version)|

