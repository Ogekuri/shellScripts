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
        │   ├── opencode.py
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

# __init__.py | Python | 78L | 2 symbols | 2 imports | 8 comments
> Path: `src/shell_scripts/commands/__init__.py`

## Imports
```
import importlib
from types import ModuleType
```

## Definitions

### fn `def get_command(name: str) -> ModuleType | None` (L48-63)
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

### fn `def get_all_commands() -> dict[str, str]` (L64-79)
- @brief Build command-description index for help rendering.
- @details Iterates sorted command keys for stable output ordering; imports each module via `get_command`; extracts `DESCRIPTION` or empty string. Time complexity O(N log N) for N commands due to key sorting.
- @return {dict[str, str]} Mapping `command_name -> description`.
- @throws {ImportError} If any mapped command module import fails.
- @satisfies PRJ-002, DES-001, DES-008, REQ-057, REQ-058

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_command`|fn|pub|48-63|def get_command(name: str) -> ModuleType | None|
|`get_all_commands`|fn|pub|64-79|def get_all_commands() -> dict[str, str]|


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

### fn `def run(args)` (L22-79)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-21|def print_help(version)|
|`run`|fn|pub|22-79|def run(args)|


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

# req_cmd.py | Python | 362L | 13 symbols | 6 imports | 13 comments
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
### fn `def _is_hidden_path(path: Path, base_dir: Path) -> bool` `priv` (L59-73)
- @brief Determine whether path contains hidden segments below base.
- @details Computes relative parts from `base_dir` and returns `True` when any path segment starts with a dot-prefix, preventing accidental traversal of hidden metadata directories (for example `.git`).
- @param path {Path} Candidate directory path.
- @param base_dir {Path} Root directory used for relative-segment evaluation.
- @return {bool} `True` when candidate has hidden relative segments.
- @satisfies REQ-052, REQ-053

### fn `def print_help(version: str) -> None` (L74-91)
- @brief Render command help for `req`.
- @details Prints selector options and behavior contract for target directory discovery and external `req` invocation flow.
- @param version {str} CLI version string appended in usage output.
- @return {None} Writes help text to stdout.
- @satisfies DES-008

### fn `def _iter_first_level_dirs(base_dir: Path) -> list[Path]` `priv` (L92-111)
- @brief Collect first-level child directories in deterministic order.
- @details Enumerates direct children of `base_dir`, keeps only directories, and sorts by path string for stable command behavior.
- @param base_dir {Path} Directory whose first-level children are listed.
- @return {list[Path]} Sorted first-level child directories.
- @satisfies REQ-052

### fn `def _iter_descendant_dirs(base_dir: Path) -> list[Path]` `priv` (L112-131)
- @brief Collect descendant directories recursively in deterministic order.
- @details Traverses all descendants via glob expansion, excludes `base_dir` itself, keeps only directories, and sorts by path string.
- @param base_dir {Path} Directory whose descendants are listed.
- @return {list[Path]} Sorted descendant directory list excluding `base_dir`.
- @satisfies REQ-053

### fn `def _build_req_args(target_dir: Path) -> list[str]` `priv` (L132-167)
- @brief Build external `req` argument vector for one target directory.
- @details Uses hardcoded non-overridable arguments and appends repeated runtime-configured providers/static-check entries sourced from `get_req_profile`.
- @param target_dir {Path} Target directory used to parameterize path flags.
- @return {list[str]} External `req` argv vector.
- @satisfies REQ-049, REQ-050

### fn `def _delete_cleanup_path(cleanup_path: Path) -> tuple[str, str]` `priv` (L168-190)
- @brief Remove one predefined cleanup path when it exists.
- @details Evaluates one cleanup candidate path, returns `skip` when the path is absent, removes directories with `shutil.rmtree`, removes non-directory filesystem entries with `Path.unlink`, and classifies deleted entries as `dir` or `file`. Time complexity is O(n) for directory trees and O(1) for non-directory entries.
- @param cleanup_path {Path} Absolute candidate cleanup path for one target.
- @return {tuple[str, str]} Status-kind pair shaped as (`deleted`, `dir`), (`deleted`, `file`), or (`skip`, `missing`).
- @satisfies REQ-048, REQ-062, REQ-063

### fn `def _print_cleanup_evidence(evidence: CleanupEvidence) -> None` `priv` (L191-207)
- @brief Emit one cleanup evidence line in deterministic token order.
- @details Prints a parser-friendly line using fixed `clean | <status> | <kind> | <path>` tokens so downstream checks can differentiate deleted files, deleted directories, and skipped missing paths without reading surrounding prose. Time complexity is O(1).
- @param evidence {CleanupEvidence} Tuple `(status, kind, path)` produced by cleanup preparation logic.
- @return {None} Writes one stdout line.
- @satisfies REQ-062, REQ-063

### fn `def _prepare_target_directory(target_dir: Path) -> list[CleanupEvidence]` `priv` (L208-231)
- @brief Apply cleanup and scaffold operations for one target directory.
- @details Evaluates every predefined cleanup path, records deterministic cleanup evidence tuples, removes existing filesystem entries, and ensures required project subdirectories exist before external `req` call. Time complexity is O(m + d) where `m` is cleanup-path count and `d` is total removed directory-tree entries.
- @param target_dir {Path} Target directory to mutate.
- @return {list[CleanupEvidence]} Cleanup evidence entries in configured path order.
- @satisfies REQ-048, REQ-062, REQ-063

### fn `def _is_git_repository_root(target_dir: Path) -> bool` `priv` (L232-257)
- @brief Check whether target directory is a Git repository root.
- @details Executes `git -C <target> rev-parse --show-toplevel`, returns `False` on command failure, and compares normalized absolute paths to ensure the target directory matches the repository root exactly. Time complexity is O(1) excluding external process startup overhead.
- @param target_dir {Path} Candidate target directory.
- @return {bool} `True` when target directory is Git root; otherwise `False`.
- @satisfies REQ-070, REQ-071

### fn `def _print_install_skipped(target_dir: Path) -> None` `priv` (L258-274)
- @brief Emit skip evidence when target directory is not Git root.
- @details Prints one parser-stable line containing `skip` and token `skipped` to document installation omission for non-root directories in current-directory and `--dirs` modes. Time complexity is O(1).
- @param target_dir {Path} Directory skipped from cleanup and installation.
- @return {None} Writes one stdout line.
- @satisfies REQ-070, REQ-071

### fn `def run(args: list[str]) -> int` (L275-363)
- @brief Execute `req` orchestration for selected directory targets.
- @details Parses mutually exclusive selector options, resolves target set, applies cleanup/scaffold phase with per-path evidence emission, and executes external `req` for each target. Returns `1` on invalid option combinations or unknown options. Converts external `req` non-zero exits into explicit error output and propagated return codes.
- @param args {list[str]} Command arguments excluding `req` token.
- @return {int} `0` on success; non-zero for option or subprocess failures.
- @exception {subprocess.CalledProcessError} Internally handled and converted to deterministic return code + error output.
- @satisfies REQ-048, REQ-049, REQ-051, REQ-052, REQ-053, REQ-054, REQ-056, REQ-062, REQ-063, REQ-070, REQ-071

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|23||
|`DESCRIPTION`|var|pub|24||
|`_is_hidden_path`|fn|priv|59-73|def _is_hidden_path(path: Path, base_dir: Path) -> bool|
|`print_help`|fn|pub|74-91|def print_help(version: str) -> None|
|`_iter_first_level_dirs`|fn|priv|92-111|def _iter_first_level_dirs(base_dir: Path) -> list[Path]|
|`_iter_descendant_dirs`|fn|priv|112-131|def _iter_descendant_dirs(base_dir: Path) -> list[Path]|
|`_build_req_args`|fn|priv|132-167|def _build_req_args(target_dir: Path) -> list[str]|
|`_delete_cleanup_path`|fn|priv|168-190|def _delete_cleanup_path(cleanup_path: Path) -> tuple[str...|
|`_print_cleanup_evidence`|fn|priv|191-207|def _print_cleanup_evidence(evidence: CleanupEvidence) ->...|
|`_prepare_target_directory`|fn|priv|208-231|def _prepare_target_directory(target_dir: Path) -> list[C...|
|`_is_git_repository_root`|fn|priv|232-257|def _is_git_repository_root(target_dir: Path) -> bool|
|`_print_install_skipped`|fn|priv|258-274|def _print_install_skipped(target_dir: Path) -> None|
|`run`|fn|pub|275-363|def run(args: list[str]) -> int|


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

### fn `def run(args)` (L26-43)
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
|`run`|fn|pub|26-43|def run(args)|


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

### fn `def run(args)` (L26-43)
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
|`run`|fn|pub|26-43|def run(args)|


---

# config.py | Python | 328L | 11 symbols | 6 imports | 22 comments
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

### fn `def get_config_path() -> Path` (L99-110)
- @brief In-memory runtime configuration snapshot.
- @brief Return canonical runtime config location.
- @details Initialized from defaults; updated only by `load_runtime_config`.
- @details Resolves path as `$HOME/.config/shellScripts/config.json` using `Path.home()` for user directory abstraction.
- @return {Path} Absolute config file path.
- @satisfies DES-011, REQ-045
- @satisfies DES-011, DES-012, REQ-045, REQ-046

### fn `def get_default_runtime_config() -> dict[str, Any]` (L111-122)
- @brief Return deep-copied default configuration payload.
- @details Produces an isolated copy to avoid external mutation of the global defaults constant and to keep write/load operations deterministic.
- @return {dict[str, Any]} Fresh deep copy of `DEFAULT_RUNTIME_CONFIG`.
- @satisfies DES-011, DES-012

### fn `def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]` `priv` (L123-142)
- @brief Recursively merge nested mapping values.
- @details For keys where both base and override values are dictionaries, recursively merges child keys; otherwise replaces base value with override. Time complexity O(N) over override node count.
- @param base {dict[str, Any]} Target mapping mutated in place.
- @param override {dict[str, Any]} Source mapping with overriding values.
- @return {dict[str, Any]} The mutated `base` reference.
- @satisfies DES-011, REQ-045

### fn `def _normalize_command_vector(value: Any) -> list[str] | None` `priv` (L143-159)
- @brief Validate and normalize an executable argv vector.
- @details Accepts only non-empty lists of non-empty strings and returns a cloned list for defensive immutability.
- @param value {Any} Candidate command vector.
- @return {list[str]|None} Sanitized vector or `None` if invalid.
- @satisfies DES-011, REQ-045

### fn `def _normalize_string_list(value: Any) -> list[str] | None` `priv` (L160-176)
- @brief Validate and normalize a list of non-empty strings.
- @details Accepts only list payloads containing non-empty string elements and returns a cloned list for defensive immutability. Empty lists are valid.
- @param value {Any} Candidate list payload.
- @return {list[str]|None} Sanitized list or `None` if invalid.
- @satisfies DES-011, REQ-045, REQ-050

### fn `def _normalize_categories(value: Any) -> dict[str, list[str]] | None` `priv` (L177-199)
- @brief Validate category-to-command mapping payload.
- @details Keeps only entries with string keys and valid command vectors. Invalid entries are dropped and can trigger fallback usage upstream.
- @param value {Any} Candidate category map payload.
- @return {dict[str, list[str]]|None} Sanitized category map or `None`.
- @satisfies DES-011, REQ-024, REQ-045

### fn `def load_runtime_config(path: Path | None = None) -> dict[str, Any]` (L200-239)
- @brief Load runtime configuration file and merge into defaults.
- @details Resets in-memory state to defaults for each call, then attempts to read and parse JSON payload from target path and recursively merge override keys. Missing file, invalid JSON, non-object root, or read errors preserve defaults and emit warnings.
- @param path {Path|None} Optional override path; default is canonical path.
- @return {dict[str, Any]} Active in-memory runtime configuration snapshot.
- @exception {json.JSONDecodeError} Handled internally and downgraded to warn.
- @exception {OSError} Handled internally and downgraded to warn.
- @satisfies DES-011, REQ-045

### fn `def get_management_command(name: str) -> str` (L240-256)
- @brief Resolve management command string with safe default fallback.
- @details Reads runtime key under `management.<name>`; returns default value when key is absent or not a non-empty string.
- @param name {str} Management operation key (`upgrade` or `uninstall`).
- @return {str} Shell command string to execute.
- @satisfies REQ-004, REQ-005, REQ-045

### fn `def get_dispatch_profile(name: str) -> tuple[dict[str, list[str]], list[str]]` (L257-282)
- @brief Resolve dispatch profile for diff/edit/view command wrappers.
- @details Builds profile from `dispatch.<name>` runtime payload with typed normalization and per-section fallback to hardcoded defaults for missing or invalid values.
- @param name {str} Dispatch command key (`diff`, `edit`, or `view`).
- @return {tuple[dict[str, list[str]], list[str]]} `(categories, fallback)`.
- @satisfies DES-007, REQ-024, REQ-045

### fn `def get_req_profile() -> tuple[list[str], list[str]]` (L283-310)
- @brief Resolve `req` providers and static checks from runtime config.
- @details Builds profile from `req.providers` and `req.static_checks` runtime payload with typed normalization and per-section fallback to hardcoded defaults for missing or invalid values.
- @return {tuple[list[str], list[str]]} `(providers, static_checks)`.
- @satisfies DES-011, REQ-045, REQ-050

### fn `def write_default_runtime_config(path: Path | None = None) -> Path` (L311-329)
- @brief Write default runtime configuration file to disk.
- @details Creates parent directories when missing and writes canonical JSON payload using sorted keys and indentation for deterministic content.
- @param path {Path|None} Optional override path; default is canonical path.
- @return {Path} Path where the file has been written.
- @exception {OSError} Propagated when filesystem write fails.
- @satisfies DES-012, REQ-046

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_config_path`|fn|pub|99-110|def get_config_path() -> Path|
|`get_default_runtime_config`|fn|pub|111-122|def get_default_runtime_config() -> dict[str, Any]|
|`_deep_merge_dict`|fn|priv|123-142|def _deep_merge_dict(base: dict[str, Any], override: dict...|
|`_normalize_command_vector`|fn|priv|143-159|def _normalize_command_vector(value: Any) -> list[str] | ...|
|`_normalize_string_list`|fn|priv|160-176|def _normalize_string_list(value: Any) -> list[str] | None|
|`_normalize_categories`|fn|priv|177-199|def _normalize_categories(value: Any) -> dict[str, list[s...|
|`load_runtime_config`|fn|pub|200-239|def load_runtime_config(path: Path | None = None) -> dict...|
|`get_management_command`|fn|pub|240-256|def get_management_command(name: str) -> str|
|`get_dispatch_profile`|fn|pub|257-282|def get_dispatch_profile(name: str) -> tuple[dict[str, li...|
|`get_req_profile`|fn|pub|283-310|def get_req_profile() -> tuple[list[str], list[str]]|
|`write_default_runtime_config`|fn|pub|311-329|def write_default_runtime_config(path: Path | None = None...|


---

# config_cli.py | Python | 1119L | 35 symbols | 7 imports | 59 comments
> Path: `src/shell_scripts/config_cli.py`

## Imports
```
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any
from shell_scripts.config import (
from shell_scripts.utils import print_error, print_info, print_success
```

## Definitions

- var `PROGRAM = "shellscripts"` (L33)
- @brief CLI program token used in inline usage help output.
- var `ROOT_LABEL = "shellScripts_Configuration"` (L37)
- @brief Root node label rendered by `--print` and `--params` trees.
- var `NAME_COLUMN_WIDTH = 24` (L43)
- var `PATH_SEPARATOR = ":"` (L47)
- @brief Hierarchical path separator accepted by `--get`/`--set`/`--unset`.
- var `MASKED_SECRET = "********"` (L51)
- @brief Mask rendered in place of secret option values.
- var `KIND_LABELS = {` (L57)
### class `class ChoiceSpec` `@dataclass(frozen=True)` (L72-84)
- @brief One allowed value of a selection-type option.
- @details Immutable registry record pairing an accepted value token with its meaning, rendered in `Sel`/`Value` and `Value`/`Meaning` tables by `--print` and `--params`.
- @satisfies REQ-097, REQ-108

### class `class OptionSpec` `@dataclass(frozen=True)` (L86-103)
- @brief Declarative metadata of one configurable leaf option.
- @details Binds one configuration key to its value kind, short description, optional allowed choices, secret flag, and input-example token; drives `--params` rendering, `--print` value rendering, `--get` masking, and `--set` coercion plus choice validation.
- @satisfies DES-032, DES-036, REQ-096, REQ-097, REQ-098, REQ-101, REQ-102, REQ-107, REQ-110

### class `class GroupSpec` `@dataclass(frozen=True)` (L105-116)
- @brief Declarative metadata of one configuration subtree group.
- @details Orders child schema nodes and carries the group description rendered by `--params` and the tree structure rendered by `--print`.
- @satisfies DES-032, REQ-095, REQ-107

### fn `def _split_path(path: str) -> list[str] | None` `priv` (L273-291)
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

### fn `def _find_schema_node(parts: list[str]) -> "OptionSpec | GroupSpec | None"` `priv` (L292-317)
- @brief Resolve one path against the schema registry.
- @details Walks `CONFIG_SCHEMA` by segments and returns the matching leaf or group record, or `None` for unknown or non-configurable paths. Time complexity O(n*m) over path depth and sibling count.
- @param parts {list[str]} Non-empty path segments from `_split_path`.
- @return {OptionSpec|GroupSpec|None} Schema record or `None` when absent.
- @satisfies DES-032, REQ-100

### fn `def _resolve_value(container: Any, parts: list[str]) -> Any` `priv` (L318-336)
- @brief Navigate a nested mapping by path segments.
- @details Returns `_MISSING` when any segment is absent or crosses a non-mapping value. Time complexity O(n) over path depth.
- @param container {Any} Nested mapping candidate, usually a config dict.
- @param parts {list[str]} Non-empty path segments.
- @return {Any} Resolved value or the `_MISSING` sentinel.
- @satisfies REQ-099

### fn `def _set_nested(container: dict[str, Any], parts: list[str], value: Any) -> None` `priv` (L337-358)
- @brief Write one value into a nested mapping by path segments.
- @details Creates intermediate mappings for absent parents, replacing non-mapping parents with fresh mappings. Time complexity O(n) over depth.
- @param container {dict[str,Any]} Target mapping mutated in place.
- @param parts {list[str]} Non-empty path segments ending at the leaf key.
- @param value {Any} Coerced value to persist.
- @return {None} Mutates `container` in place.
- @satisfies REQ-101, REQ-103

### fn `def _pop_nested(container: dict[str, Any], parts: list[str]) -> Any` `priv` (L359-380)
- @brief Remove one key from a nested mapping by path segments.
- @details Returns the removed value or `_MISSING` when any segment is absent or crosses a non-mapping value. Time complexity O(n) over depth.
- @param container {dict[str,Any]} Target mapping mutated in place.
- @param parts {list[str]} Non-empty path segments ending at the target key.
- @return {Any} Removed value or the `_MISSING` sentinel.
- @satisfies REQ-105, REQ-106

### fn `def _iter_schema_leaf_paths(` `priv` (L381-383)

### fn `def _iter_default_leaf_paths(` `priv` (L403-405)
- @brief Enumerate every schema leaf path.
- @details Depth-first recursion yielding tuples of path segments for every
`OptionSpec` node. Time complexity O(n) over schema node count.
- @param children {tuple} Sibling nodes being expanded.
- @param prefix {tuple[str,...]} Parent path segments.
- @return {Iterator[tuple[str,...]]} Leaf path segment tuples.
- @satisfies DES-034

### fn `def find_schema_mismatches() -> list[str]` (L426-456)
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

### fn `def _fail_on_schema_mismatch() -> bool` `priv` (L462-480)
- @brief Import-time snapshot of schema/defaults divergence descriptions.
- @brief Enforce schema parity before configuration command execution.
- @details Prints one bright-red error describing every divergence detected at import time and reports whether the calling command must abort. Time complexity O(n) over mismatch count.
- @return {bool} `True` when the caller must fail with return code `1`.
- @satisfies DES-034

### fn `def _render_box_table(` `priv` (L481-482)

### fn `def _row(cells: list[str]) -> str` `priv` (L502-513)
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
- @satisfies REQ-097, REQ-108

### fn `def _render_json(value: Any) -> str` `priv` (L523-535)
- @brief Render one configuration value as compact JSON.
- @details Scalars, lists, and mappings serialize deterministically with sorted keys and no ASCII escaping. Time complexity O(n) over value size.
- @param value {Any} Configuration value to serialize.
- @return {str} Single-line JSON representation.
- @satisfies REQ-096

### fn `def _mask_secrets(node: "OptionSpec | GroupSpec | None", value: Any) -> Any` `priv` (L536-557)
- @brief Replace secret leaf values with the mask constant.
- @details Recursively walks schema groups and returns `MASKED_SECRET` for secret leaf values, leaving non-secret data unchanged. Time complexity O(n) over subtree size.
- @param node {OptionSpec|GroupSpec|None} Schema record for `value`.
- @param value {Any} Configuration value to mask.
- @return {Any} Masked copy of `value`.
- @satisfies REQ-098

### fn `def _render_print_children(` `priv` (L558-562)

### fn `def _describe_value_shape(value: Any) -> str` `priv` (L641-666)
- @brief Render one `--print` tree level.
- @brief Map one default configuration value to its shape label.
- @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
connectors, left-justified names, `= <JSON>` scalar leaves, `Sel`/`Value`
selection tables for choice leaves with the active choice marked `[*]`,
`Key`/`Value` box tables for object-shaped leaves (one sorted row per
entry, JSON-encoded cell values), and `#`/`Value` box tables for
list-shaped leaves (one row per element, JSON-encoded cell values).
Table lines carry the `│` tree continuation of `node_prefix` for
non-final siblings. Masked secrets bypass table rendering and fall
back to the scalar line.
Time complexity O(n) over subtree node count.
- @details Normalizes Python runtime types into stable shape tokens consumed by the `--params` `object` default-structure table (REQ-112). The boolean check precedes the integer check because `bool` subclasses `int`. Time complexity O(1).
- @param prefix {str} Ancestor connector prefix for this level.
- @param children {tuple} Sibling schema nodes being rendered.
- @param values {Any} Effective configuration subtree for this level.
- @param lines {list[str]} Output accumulator mutated in place.
- @param value {Any} Default configuration value to classify.
- @return {None} Appends rendered lines to `lines`.
- @return {str} Shape token: `string`, `integer`, `boolean`, `list of strings`, `object`, or `value` for unclassified payloads.
- @satisfies DES-032, REQ-095, REQ-096, REQ-097, REQ-098
- @satisfies REQ-112

### fn `def _render_params_children(` `priv` (L667-671)

### fn `def _load_overrides() -> "tuple[dict[str, Any] | None, str | None]"` `priv` (L765-790)
- @brief Render one `--params` hierarchy level.
- @brief Load on-disk configuration overrides.
- @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
connectors, left-justified names with `-` annotations, and kind labels
for leaves. Scalar leaves append the schema-declared input example;
selection leaves append a `Value`/`Meaning` allowed-value table
followed by an example continuation line; `object` leaves append a
JSON-object input note, a `Key`/`Format` default-structure table
resolved from `DEFAULT_RUNTIME_CONFIG`, and an example continuation
line; `list` leaves append a JSON-array input note, an element-format
table, and an example continuation line. Table and example lines carry
the `│` tree continuation of `node_prefix` for non-final siblings.
Time complexity O(n) over subtree node count.
- @details Reads the canonical config file and returns its object payload; a missing file yields an empty mapping, while unreadable files, invalid JSON, and non-object roots yield an error message. Time complexity O(n) over file size.
- @param prefix {str} Ancestor connector prefix for this level.
- @param children {tuple} Sibling schema nodes being rendered.
- @param lines {list[str]} Output accumulator mutated in place.
- @param prefix_parts {tuple[str,...]} Schema path segments of this level,
used to resolve `object` defaults for the structure table.
- @return {None} Appends rendered lines to `lines`.
- @return {tuple[dict|None, str|None]} `(payload, None)` on success or `(None, error_message)` on failure.
- @satisfies DES-036, REQ-107, REQ-108, REQ-110, REQ-111, REQ-112, REQ-113
- @satisfies REQ-101, REQ-103, REQ-105

### fn `def _write_overrides(payload: dict[str, Any]) -> None` `priv` (L791-810)
- @brief Persist configuration overrides to the canonical config file.
- @details Creates parent directories when missing and writes sorted-key, two-space-indented JSON with a trailing newline for deterministic content. Time complexity O(n) over payload size.
- @param payload {dict[str,Any]} Full on-disk override mapping.
- @return {None} Applies destination filesystem mutation.
- @throws {OSError} Propagated when filesystem write fails.
- @satisfies REQ-103, REQ-105

### fn `def _coerce_value(` `priv` (L811-812)

### fn `def print_config_cli_help(command: str) -> None` (L859-897)
- @brief Coerce one raw CLI token by schema kind.
- @brief Print command-specific inline usage help.
- @details Maps `boolean` tokens to `true`/`false` (case-insensitive),
`integer` tokens to `int`, `list` tokens to JSON arrays of non-empty
strings, `object` tokens to JSON objects, and leaves `string` and
`selection` tokens as non-empty strings. Time complexity O(n) over token
length.
- @details Documents the `:` hierarchical path syntax, accepted value formats, environment acquisition, and per-command examples for one of `--get`, `--set`, or `--unset`. Time complexity O(1).
- @param raw {str} Raw value token from the CLI.
- @param spec {OptionSpec} Target option schema record.
- @param command {str} Command token requesting inline help.
- @return {tuple[bool, Any, str|None]} `(ok, value, error)` triple.
- @return {None} Writes help text to stdout.
- @satisfies REQ-101
- @satisfies REQ-109

### fn `def do_print_raw() -> int` (L898-925)
- @brief Print the on-disk configuration file verbatim.
- @details Enforces schema registry parity with `DEFAULT_RUNTIME_CONFIG` before emitting output (DES-034, DES-032 surface membership), then emits the raw bytes of the canonical config file without parsing, or a bright-red error naming the path when the file is missing or unreadable. Time complexity O(n) over file size.
- @return {int} `0` on success; `1` on schema divergence or when the file is missing or unreadable.
- @satisfies DES-032, DES-034, REQ-094

### fn `def do_print() -> int` (L926-947)
- @brief Render the effective configuration as an options tree.
- @details Deep-merges on-disk overrides onto hardcoded defaults, then renders the schema-ordered tree with branch connectors, `= <JSON>` scalar leaves, masked secrets, and `Sel`/`Value` selection tables. The root annotation reports `ACTIVE` when the config file exists and `DEFAULT` otherwise. Time complexity O(n) over configuration size.
- @return {int} `0` on success; `1` on schema divergence.
- @satisfies REQ-095, REQ-096, REQ-097, REQ-098, DES-034

### fn `def do_params() -> int` (L948-970)
- @brief Render the configurable parameter hierarchy with descriptions.
- @details Emits the schema-ordered tree with per-group descriptions, per-option kind labels and short descriptions, schema-declared input examples on scalar lines and continuation lines, `Value`/`Meaning` allowed-value tables for selection options, `Key`/`Format` default-structure tables for `object` options, and element-format tables for `list` options. Time complexity O(n) over schema node count.
- @return {int} `0` on success; `1` on schema divergence.
- @satisfies DES-034, DES-036, REQ-107, REQ-108, REQ-110, REQ-111, REQ-112, REQ-113

### fn `def do_get(path: str | None) -> int` (L971-1006)
- @brief Read one configuration value by hierarchical path.
- @details Resolves the `:`-separated path against the schema registry and the effective configuration, masks secret leaves, prints scalars and lists as single-line JSON and object subtrees as indented JSON. Time complexity O(n) over subtree size.
- @param path {str|None} Hierarchical path token, for example `management:upgrade`.
- @return {int} `0` on success; `1` for missing arguments, unknown paths, or absent values.
- @satisfies REQ-098, REQ-099, REQ-100, REQ-109, DES-034

### fn `def do_set(path: str | None, value: str | None) -> int` (L1007-1067)
- @brief Set one configuration value by hierarchical path.
- @details Resolves `$NAME` tokens from the environment, coerces the value by schema kind, validates schema-allowed choices, then loads the on-disk overrides, writes only the target key, and persists sorted-key indented JSON without touching unrelated keys. Time complexity O(n) over configuration size.
- @param path {str|None} Hierarchical path token ending at a schema leaf.
- @param value {str|None} Raw value token or `$NAME` environment token.
- @return {int} `0` on success; `1` for missing arguments, unknown paths, invalid values, disallowed choices, undefined environment variables, or unreadable config files.
- @satisfies REQ-101, REQ-102, REQ-103, REQ-104, REQ-109, DES-034

### fn `def do_unset(path: str | None) -> int` (L1068-1105)
- @brief Remove one configuration override by hierarchical path.
- @details Loads the on-disk overrides, removes the target key (leaf or object subtree), persists the result so hardcoded defaults reactivate, and prints the subtree-removal warning for object payloads. Time complexity O(n) over configuration size.
- @param path {str|None} Hierarchical path token to remove.
- @return {int} `0` on success; `1` for missing arguments, unknown paths, absent overrides, or unreadable config files.
- @satisfies REQ-105, REQ-106, REQ-109, DES-034

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|33||
|`ROOT_LABEL`|var|pub|37||
|`NAME_COLUMN_WIDTH`|var|pub|43||
|`PATH_SEPARATOR`|var|pub|47||
|`MASKED_SECRET`|var|pub|51||
|`KIND_LABELS`|var|pub|57||
|`ChoiceSpec`|class|pub|72-84|class ChoiceSpec|
|`OptionSpec`|class|pub|86-103|class OptionSpec|
|`GroupSpec`|class|pub|105-116|class GroupSpec|
|`_split_path`|fn|priv|273-291|def _split_path(path: str) -> list[str] | None|
|`_find_schema_node`|fn|priv|292-317|def _find_schema_node(parts: list[str]) -> "OptionSpec | ...|
|`_resolve_value`|fn|priv|318-336|def _resolve_value(container: Any, parts: list[str]) -> Any|
|`_set_nested`|fn|priv|337-358|def _set_nested(container: dict[str, Any], parts: list[st...|
|`_pop_nested`|fn|priv|359-380|def _pop_nested(container: dict[str, Any], parts: list[st...|
|`_iter_schema_leaf_paths`|fn|priv|381-383|def _iter_schema_leaf_paths(|
|`_iter_default_leaf_paths`|fn|priv|403-405|def _iter_default_leaf_paths(|
|`find_schema_mismatches`|fn|pub|426-456|def find_schema_mismatches() -> list[str]|
|`_fail_on_schema_mismatch`|fn|priv|462-480|def _fail_on_schema_mismatch() -> bool|
|`_render_box_table`|fn|priv|481-482|def _render_box_table(|
|`_row`|fn|priv|502-513|def _row(cells: list[str]) -> str|
|`_render_json`|fn|priv|523-535|def _render_json(value: Any) -> str|
|`_mask_secrets`|fn|priv|536-557|def _mask_secrets(node: "OptionSpec | GroupSpec | None", ...|
|`_render_print_children`|fn|priv|558-562|def _render_print_children(|
|`_describe_value_shape`|fn|priv|641-666|def _describe_value_shape(value: Any) -> str|
|`_render_params_children`|fn|priv|667-671|def _render_params_children(|
|`_load_overrides`|fn|priv|765-790|def _load_overrides() -> "tuple[dict[str, Any] | None, st...|
|`_write_overrides`|fn|priv|791-810|def _write_overrides(payload: dict[str, Any]) -> None|
|`_coerce_value`|fn|priv|811-812|def _coerce_value(|
|`print_config_cli_help`|fn|pub|859-897|def print_config_cli_help(command: str) -> None|
|`do_print_raw`|fn|pub|898-925|def do_print_raw() -> int|
|`do_print`|fn|pub|926-947|def do_print() -> int|
|`do_params`|fn|pub|948-970|def do_params() -> int|
|`do_get`|fn|pub|971-1006|def do_get(path: str | None) -> int|
|`do_set`|fn|pub|1007-1067|def do_set(path: str | None, value: str | None) -> int|
|`do_unset`|fn|pub|1068-1105|def do_unset(path: str | None) -> int|


---

# core.py | Python | 385L | 10 symbols | 8 imports | 25 comments
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
### fn `def print_help(command_name=None)` (L126-190)
- @brief Print global or command-specific help text.
- @details Renders command module help for known command names; otherwise exits with explicit unknown-command error. Global help includes management options and grouped command sections using deterministic section and command order, with descriptions sourced from each command module `DESCRIPTION` constant.
- @param command_name {str|None} Optional command token for scoped help.
- @return {None} Writes to stdout/stderr; may terminate process on invalid command.
- @throws {SystemExit} Raised when unknown command name is requested.
- @satisfies PRJ-002, DES-014, REQ-001, REQ-002, REQ-066, REQ-068, REQ-069

### fn `def _build_develop_upgrade_command(latest_tag: str) -> str` `priv` (L191-206)
- @brief Compose the develop upgrade command for one GitHub release tag.
- @details Resolves the `management.upgrade_develop` runtime-config template, substitutes the `{tag}` placeholder with the supplied tag, and returns the shell command that installs the package from the GitHub tag archive. Complexity O(n) over template length.
- @param latest_tag {str} GitHub release tag token preserving its `v` prefix.
- @return {str} Fully substituted shell upgrade command.
- @satisfies REQ-076, DES-019

### fn `def do_upgrade(develop: bool = False, force: bool = False) -> int` (L207-246)
- @brief Execute Linux-only upgrade command resolved from runtime config.
- @details Reads management command string from runtime config key `management.upgrade` (PyPI default) or, when `develop` is set, resolves the latest GitHub release tag and composes the tag-pinned upgrade command; appends ` --force --reinstall --refresh` to the resolved command when `force` is set; executes the composed command on Linux via shell invocation and prints the manual fallback command on non-Linux systems. Complexity O(n) over the composed command string length.
- @param develop {bool} Select upgrade from the latest GitHub release tag.
- @param force {bool} Append forced-reinstall options to the upgrade command.
- @return {int} `1` when develop tag resolution fails; subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-004, REQ-076, REQ-078, REQ-087, REQ-088, REQ-089, REQ-045, REQ-056

### fn `def do_uninstall()` (L247-269)
- @brief Execute Linux-only uninstall command resolved from runtime config.
- @details Reads management command string from runtime config key `management.uninstall`, executes it on Linux via shell invocation, and prints manual fallback command on non-Linux systems.
- @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
- @satisfies REQ-005, REQ-045, REQ-056

### fn `def do_write_config()` (L270-285)
- @brief Persist default runtime configuration file to disk.
- @details Writes canonical config JSON to `$HOME/.config/shellScripts/config.json` and logs destination path.
- @return {int} `0` on successful write.
- @throws {OSError} Propagated on filesystem write failure.
- @satisfies REQ-046

### fn `def main()` (L286-386)
- @brief Entrypoint for shellscripts argument dispatch.
- @details Performs runtime OS detection, update check, runtime configuration load, and argument dispatch through management flags (`--version` prints the aligned three-line report with installed plus PyPI/GitHub latest versions; `--upgrade` upgrades from PyPI or, with `--develop`/`--dev`, from the latest GitHub release tag; `--force` appends forced-reinstall options to the selected upgrade command; bare `--develop`/`--dev`/`--force` selectors are rejected) and subcommands, then restores terminal raw/cbreak and disables legacy+xterm mouse-tracking modes (`?9l`, `?1000l`, `?1001l`, `?1002l`, `?1003l`, `?1004l`, `?1005l`, `?1006l`, `?1007l`, `?1015l`, `?1016l`) before exit.
- @return {int} Process-compatible return code for caller (`sys.exit`).
- @satisfies PRJ-001, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-064, REQ-065, REQ-066, REQ-068, REQ-069, REQ-075, REQ-076, REQ-077, REQ-078, REQ-087, REQ-088, REQ-089, REQ-090, REQ-091, REQ-094, REQ-095, REQ-096, REQ-097, REQ-098, REQ-099, REQ-100, REQ-101, REQ-102, REQ-103, REQ-104, REQ-105, REQ-106, REQ-107, REQ-108, REQ-109

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|40||
|`HELP_COMMAND_COLUMN_WIDTH`|var|pub|46||
|`FORCED_REINSTALL_OPTIONS`|var|pub|54||
|`HELP_SECTION_COMMANDS`|var|pub|62||
|`print_help`|fn|pub|126-190|def print_help(command_name=None)|
|`_build_develop_upgrade_command`|fn|priv|191-206|def _build_develop_upgrade_command(latest_tag: str) -> str|
|`do_upgrade`|fn|pub|207-246|def do_upgrade(develop: bool = False, force: bool = False...|
|`do_uninstall`|fn|pub|247-269|def do_uninstall()|
|`do_write_config`|fn|pub|270-285|def do_write_config()|
|`main`|fn|pub|286-386|def main()|


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

