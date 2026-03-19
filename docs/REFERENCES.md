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
        │   ├── dc_differ.py
        │   ├── dc_editor.py
        │   ├── dc_viewer.py
        │   ├── dicom2jpg.py
        │   ├── dicomviewer.py
        │   ├── doxygen_cmd.py
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
        │   ├── vscode_cmd.py
        │   └── vsinsider_cmd.py
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

# __init__.py | Python | 46L | 2 symbols | 1 imports | 0 comments
> Path: `src/shell_scripts/commands/__init__.py`

## Imports
```
import importlib
```

## Definitions

### fn `def get_command(name)` (L34-40)

### fn `def get_all_commands()` (L41-46)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`get_command`|fn|pub|34-40|def get_command(name)|
|`get_all_commands`|fn|pub|41-46|def get_all_commands()|


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

# ai_install.py | Python | 150L | 11 symbols | 10 imports | 1 comments
> Path: `src/shell_scripts/commands/ai_install.py`

## Imports
```
import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
from pathlib import Path
from shell_scripts.utils import print_info, print_error, print_success
import urllib.request
import urllib.request
```

## Definitions

- var `PROGRAM = "shellscripts"` (L12)
- var `DESCRIPTION = "Install AI CLI tools (Codex, Copilot, Gemini, OpenCode, Claude, Kiro)."` (L13)
- var `TOOLS = {` (L15)
- var `CLAUDE_BUCKET = (` (L34)
- var `KIRO_URL = "https://desktop-release.q.us-east-1.amazonaws.com/latest/kirocli-x86_64-linux.zip"` (L38)
### fn `def print_help(version)` (L41-54)

### fn `def _install_npm_tool(tool_key)` `priv` (L55-65)

### fn `def _install_claude()` `priv` (L66-87)

### fn `def _install_kiro()` `priv` (L88-116)

- var `ALL_INSTALLERS = {` (L117)
### fn `def run(args)` (L127-150)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|12||
|`DESCRIPTION`|var|pub|13||
|`TOOLS`|var|pub|15||
|`CLAUDE_BUCKET`|var|pub|34||
|`KIRO_URL`|var|pub|38||
|`print_help`|fn|pub|41-54|def print_help(version)|
|`_install_npm_tool`|fn|priv|55-65|def _install_npm_tool(tool_key)|
|`_install_claude`|fn|priv|66-87|def _install_claude()|
|`_install_kiro`|fn|priv|88-116|def _install_kiro()|
|`ALL_INSTALLERS`|var|pub|117||
|`run`|fn|pub|127-150|def run(args)|


---

# bin_links.py | Python | 77L | 4 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/bin_links.py`

## Imports
```
import os
import sys
from pathlib import Path
from shell_scripts.utils import print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Create or update command symlinks in $HOME/bin."` (L9)
### fn `def print_help(version)` (L12-20)

### fn `def run(args)` (L21-77)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-20|def print_help(version)|
|`run`|fn|pub|21-77|def run(args)|


---

# clean.py | Python | 99L | 5 symbols | 5 imports | 1 comments
> Path: `src/shell_scripts/commands/clean.py`

## Imports
```
import os
import sys
import shutil
from pathlib import Path
from shell_scripts.utils import require_project_root, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L9)
- var `DESCRIPTION = "Find and delete cache directories under the project root."` (L10)
- var `CACHE_DIRS = [` (L12)
### fn `def print_help(version)` (L26-34)

### fn `def run(args)` (L35-99)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|9||
|`DESCRIPTION`|var|pub|10||
|`CACHE_DIRS`|var|pub|12||
|`print_help`|fn|pub|26-34|def print_help(version)|
|`run`|fn|pub|35-99|def run(args)|


---

# cli_claude.py | Python | 24L | 4 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/cli_claude.py`

## Imports
```
import os
import sys
from pathlib import Path
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."` (L9)
### fn `def print_help(version)` (L12-19)

### fn `def run(args)` (L20-24)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-19|def print_help(version)|
|`run`|fn|pub|20-24|def run(args)|


---

# cli_codex.py | Python | 24L | 4 symbols | 3 imports | 1 comments
> Path: `src/shell_scripts/commands/cli_codex.py`

## Imports
```
import os
import sys
from shell_scripts.utils import require_project_root
```

## Definitions

- var `PROGRAM = "shellscripts"` (L7)
- var `DESCRIPTION = "Launch OpenAI Codex CLI in the project context."` (L8)
### fn `def print_help(version)` (L11-18)

### fn `def run(args)` (L19-24)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|7||
|`DESCRIPTION`|var|pub|8||
|`print_help`|fn|pub|11-18|def print_help(version)|
|`run`|fn|pub|19-24|def run(args)|


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

# dc_differ.py | Python | 34L | 6 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/dc_differ.py`

## Imports
```
import sys
from shell_scripts.commands._dc_common import dispatch
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "File differ dispatcher by MIME type for Double Commander."` (L7)
- var `CATEGORY_CMDS = {` (L9)
- var `FALLBACK = ["bcompare"]` (L17)
### fn `def print_help(version)` (L20-28)

### fn `def run(args)` (L29-34)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`CATEGORY_CMDS`|var|pub|9||
|`FALLBACK`|var|pub|17||
|`print_help`|fn|pub|20-28|def print_help(version)|
|`run`|fn|pub|29-34|def run(args)|


---

# dc_editor.py | Python | 34L | 6 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/dc_editor.py`

## Imports
```
import sys
from shell_scripts.commands._dc_common import dispatch
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "File editor dispatcher by MIME type for Double Commander."` (L7)
- var `CATEGORY_CMDS = {` (L9)
- var `FALLBACK = ["/opt/sublime_text/sublime_text", "-n", "-wait"]` (L17)
### fn `def print_help(version)` (L20-28)

### fn `def run(args)` (L29-34)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`CATEGORY_CMDS`|var|pub|9||
|`FALLBACK`|var|pub|17||
|`print_help`|fn|pub|20-28|def print_help(version)|
|`run`|fn|pub|29-34|def run(args)|


---

# dc_viewer.py | Python | 34L | 6 symbols | 2 imports | 1 comments
> Path: `src/shell_scripts/commands/dc_viewer.py`

## Imports
```
import sys
from shell_scripts.commands._dc_common import dispatch
```

## Definitions

- var `PROGRAM = "shellscripts"` (L6)
- var `DESCRIPTION = "File viewer dispatcher by MIME type for Double Commander."` (L7)
- var `CATEGORY_CMDS = {` (L9)
- var `FALLBACK = ["sushi"]` (L17)
### fn `def print_help(version)` (L20-28)

### fn `def run(args)` (L29-34)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|6||
|`DESCRIPTION`|var|pub|7||
|`CATEGORY_CMDS`|var|pub|9||
|`FALLBACK`|var|pub|17||
|`print_help`|fn|pub|20-28|def print_help(version)|
|`run`|fn|pub|29-34|def run(args)|


---

# dicom2jpg.py | Python | 76L | 7 symbols | 5 imports | 1 comments
> Path: `src/shell_scripts/commands/dicom2jpg.py`

## Imports
```
import os
import sys
import subprocess
import shutil
from shell_scripts.utils import print_error, require_commands
```

## Definitions

- var `PROGRAM = "shellscripts"` (L9)
- var `DESCRIPTION = "Convert DICOM images to JPEG using PixelMed."` (L10)
- var `JAVA_WRAPPERS = "/usr/lib/java-wrappers/java-wrappers.sh"` (L12)
### fn `def print_help(version)` (L15-23)

### fn `def _find_java()` `priv` (L24-30)

### fn `def _find_jars(*jar_names)` `priv` (L31-42)

### fn `def run(args)` (L43-76)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|9||
|`DESCRIPTION`|var|pub|10||
|`JAVA_WRAPPERS`|var|pub|12||
|`print_help`|fn|pub|15-23|def print_help(version)|
|`_find_java`|fn|priv|24-30|def _find_java()|
|`_find_jars`|fn|priv|31-42|def _find_jars(*jar_names)|
|`run`|fn|pub|43-76|def run(args)|


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

# doxygen_cmd.py | Python | 155L | 7 symbols | 9 imports | 2 comments
> Path: `src/shell_scripts/commands/doxygen_cmd.py`

## Imports
```
import os
import sys
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from shell_scripts.utils import require_project_root, require_commands, print_error
from shell_scripts.utils import command_exists
```

## Definitions

- var `PROGRAM = "shellscripts"` (L12)
- var `DESCRIPTION = "Generate Doxygen documentation (HTML, PDF, Markdown)."` (L13)
### fn `def print_help(version)` (L16-25)

### fn `def _supports_generate_markdown()` `priv` (L26-36)

### fn `def _write_doxyfile(path, project_root, src_dir, doxygen_dir, has_md)` `priv` (L37-38)

### fn `def _generate_markdown_fallback(xml_dir, markdown_dir)` `priv` (L74-96)

### fn `def run(args)` (L97-155)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|12||
|`DESCRIPTION`|var|pub|13||
|`print_help`|fn|pub|16-25|def print_help(version)|
|`_supports_generate_markdown`|fn|priv|26-36|def _supports_generate_markdown()|
|`_write_doxyfile`|fn|priv|37-38|def _write_doxyfile(path, project_root, src_dir, doxygen_...|
|`_generate_markdown_fallback`|fn|priv|74-96|def _generate_markdown_fallback(xml_dir, markdown_dir)|
|`run`|fn|pub|97-155|def run(args)|


---

# pdf_crop.py | Python | 409L | 27 symbols | 7 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_crop.py`

## Imports
```
import os
import sys
import re
import subprocess
import time
from pathlib import Path
from shell_scripts.utils import (
```

## Definitions

- var `PROGRAM = "shellscripts"` (L15)
- var `DESCRIPTION = "Crop PDF pages using Ghostscript with auto or manual bounding box."` (L16)
- var `LABEL_WIDTH = 19` (L18)
- var `TERM_COLS = 80` (L19)
### fn `def _init_ui()` `priv` (L22-30)

- var `TERM_COLS = os.get_terminal_size().columns` (L25)
- var `TERM_COLS = 80` (L27)
- var `TERM_COLS = max(60, min(120, TERM_COLS))` (L28)
### fn `def _use_unicode()` `priv` (L31-35)

### fn `def _icons()` `priv` (L36-43)

### fn `def print_help(version)` (L44-56)

### fn `def _fmt(n)` `priv` (L57-60)

### fn `def _fmt_quad(a, b, cc, d)` `priv` (L61-64)

### fn `def _fmt_size(w, h)` `priv` (L65-68)

### fn `def _fmt_bbox_line(l, b, r, t)` `priv` (L69-72)

### fn `def _hr(char)` `priv` (L73-77)

### fn `def _section(title)` `priv` (L78-84)

### fn `def _kv(key, value)` `priv` (L85-91)

### fn `def _die(msg)` `priv` (L92-96)

### fn `def _warn(msg)` `priv` (L97-101)

### fn `def _parse_page_range(spec, max_pages, opt_name)` `priv` (L102-129)

### fn `def _get_page_count(pdf)` `priv` (L130-137)

### fn `def _get_mediabox(pdf, page=1)` `priv` (L138-149)

### fn `def _compute_auto_bbox(pdf, first_page, last_page)` `priv` (L150-178)

### fn `def _render_progress(current, total, label)` `priv` (L179-216)

### fn `def _convert_pdf_with_progress(input_f, output_f, first, last, cw, ch, cl, cb, total)` `priv` (L217-244)

### fn `def run(args)` (L245-409)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|15||
|`DESCRIPTION`|var|pub|16||
|`LABEL_WIDTH`|var|pub|18||
|`TERM_COLS`|var|pub|19||
|`_init_ui`|fn|priv|22-30|def _init_ui()|
|`TERM_COLS`|var|pub|25||
|`TERM_COLS`|var|pub|27||
|`TERM_COLS`|var|pub|28||
|`_use_unicode`|fn|priv|31-35|def _use_unicode()|
|`_icons`|fn|priv|36-43|def _icons()|
|`print_help`|fn|pub|44-56|def print_help(version)|
|`_fmt`|fn|priv|57-60|def _fmt(n)|
|`_fmt_quad`|fn|priv|61-64|def _fmt_quad(a, b, cc, d)|
|`_fmt_size`|fn|priv|65-68|def _fmt_size(w, h)|
|`_fmt_bbox_line`|fn|priv|69-72|def _fmt_bbox_line(l, b, r, t)|
|`_hr`|fn|priv|73-77|def _hr(char)|
|`_section`|fn|priv|78-84|def _section(title)|
|`_kv`|fn|priv|85-91|def _kv(key, value)|
|`_die`|fn|priv|92-96|def _die(msg)|
|`_warn`|fn|priv|97-101|def _warn(msg)|
|`_parse_page_range`|fn|priv|102-129|def _parse_page_range(spec, max_pages, opt_name)|
|`_get_page_count`|fn|priv|130-137|def _get_page_count(pdf)|
|`_get_mediabox`|fn|priv|138-149|def _get_mediabox(pdf, page=1)|
|`_compute_auto_bbox`|fn|priv|150-178|def _compute_auto_bbox(pdf, first_page, last_page)|
|`_render_progress`|fn|priv|179-216|def _render_progress(current, total, label)|
|`_convert_pdf_with_progress`|fn|priv|217-244|def _convert_pdf_with_progress(input_f, output_f, first, ...|
|`run`|fn|pub|245-409|def run(args)|


---

# pdf_merge.py | Python | 165L | 6 symbols | 7 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_merge.py`

## Imports
```
import os
import sys
import re
import subprocess
import tempfile
import shutil
from shell_scripts.utils import require_commands, print_error, print_info, print_success
```

## Definitions

- var `PROGRAM = "shellscripts"` (L11)
- var `DESCRIPTION = "Merge multiple PDF files preserving table of contents."` (L12)
### fn `def print_help(version)` (L15-23)

### fn `def _parse_bookmarks(dump_file)` `priv` (L24-44)

### fn `def _get_num_pages(dump_file)` `priv` (L45-52)

### fn `def run(args)` (L53-165)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|11||
|`DESCRIPTION`|var|pub|12||
|`print_help`|fn|pub|15-23|def print_help(version)|
|`_parse_bookmarks`|fn|priv|24-44|def _parse_bookmarks(dump_file)|
|`_get_num_pages`|fn|priv|45-52|def _get_num_pages(dump_file)|
|`run`|fn|pub|53-165|def run(args)|


---

# pdf_split_by_format.py | Python | 215L | 9 symbols | 6 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_split_by_format.py`

## Imports
```
import os
import sys
import re
import subprocess
import tempfile
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L10)
- var `DESCRIPTION = "Split PDF into parts by page format changes."` (L11)
### fn `def print_help(version)` (L14-21)

### fn `def _get_page_formats(pdf, total_pages)` `priv` (L22-34)

### fn `def _get_total_pages(pdf)` `priv` (L35-44)

### fn `def _has_toc(pdf)` `priv` (L45-62)

### fn `def _extract_toc_for_range(data_file, start, end)` `priv` (L63-98)

### fn `def _apply_toc(output_file, toc_content)` `priv` (L99-131)

### fn `def run(args)` (L132-215)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|10||
|`DESCRIPTION`|var|pub|11||
|`print_help`|fn|pub|14-21|def print_help(version)|
|`_get_page_formats`|fn|priv|22-34|def _get_page_formats(pdf, total_pages)|
|`_get_total_pages`|fn|priv|35-44|def _get_total_pages(pdf)|
|`_has_toc`|fn|priv|45-62|def _has_toc(pdf)|
|`_extract_toc_for_range`|fn|priv|63-98|def _extract_toc_for_range(data_file, start, end)|
|`_apply_toc`|fn|priv|99-131|def _apply_toc(output_file, toc_content)|
|`run`|fn|pub|132-215|def run(args)|


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

# pdf_tiler_090.py | Python | 42L | 4 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_tiler_090.py`

## Imports
```
import os
import sys
from pathlib import Path
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Tile PDF to A4 pages at 90% scale using plakativ."` (L9)
### fn `def print_help(version)` (L12-21)

### fn `def run(args)` (L22-42)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-21|def print_help(version)|
|`run`|fn|pub|22-42|def run(args)|


---

# pdf_tiler_100.py | Python | 42L | 4 symbols | 4 imports | 1 comments
> Path: `src/shell_scripts/commands/pdf_tiler_100.py`

## Imports
```
import os
import sys
from pathlib import Path
from shell_scripts.utils import require_commands, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L8)
- var `DESCRIPTION = "Tile PDF to A4 pages at original A1 size using plakativ."` (L9)
### fn `def print_help(version)` (L12-21)

### fn `def run(args)` (L22-42)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|8||
|`DESCRIPTION`|var|pub|9||
|`print_help`|fn|pub|12-21|def print_help(version)|
|`run`|fn|pub|22-42|def run(args)|


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

# tests_cmd.py | Python | 63L | 4 symbols | 5 imports | 1 comments
> Path: `src/shell_scripts/commands/tests_cmd.py`

## Imports
```
import os
import sys
import subprocess
from pathlib import Path
from shell_scripts.utils import require_project_root, print_info, print_success, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L9)
- var `DESCRIPTION = "Run pytest test suite in a Python virtual environment."` (L10)
### fn `def print_help(version)` (L13-20)

### fn `def run(args)` (L21-63)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|9||
|`DESCRIPTION`|var|pub|10||
|`print_help`|fn|pub|13-20|def print_help(version)|
|`run`|fn|pub|21-63|def run(args)|


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

# venv_cmd.py | Python | 60L | 4 symbols | 6 imports | 1 comments
> Path: `src/shell_scripts/commands/venv_cmd.py`

## Imports
```
import os
import sys
import shutil
import subprocess
from pathlib import Path
from shell_scripts.utils import require_project_root, print_info, print_success, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L10)
- var `DESCRIPTION = "Create or recreate Python virtual environment with requirements."` (L11)
### fn `def print_help(version)` (L14-21)

### fn `def run(args)` (L22-60)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|10||
|`DESCRIPTION`|var|pub|11||
|`print_help`|fn|pub|14-21|def print_help(version)|
|`run`|fn|pub|22-60|def run(args)|


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

# core.py | Python | 109L | 7 symbols | 6 imports | 1 comments
> Path: `src/shell_scripts/core.py`

## Imports
```
import sys
import subprocess
from shell_scripts import __version__
from shell_scripts.version_check import check_for_updates
from shell_scripts.commands import get_command, get_all_commands
from shell_scripts.utils import is_linux, print_error
```

## Definitions

- var `PROGRAM = "shellscripts"` (L10)
- var `OWNER = "Ogekuri"` (L11)
- var `REPOSITORY = "shellScripts"` (L12)
### fn `def print_help(command_name=None)` (L15-40)

### fn `def do_upgrade()` (L41-56)

### fn `def do_uninstall()` (L57-69)

### fn `def main()` (L70-109)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|10||
|`OWNER`|var|pub|11||
|`REPOSITORY`|var|pub|12||
|`print_help`|fn|pub|15-40|def print_help(command_name=None)|
|`do_upgrade`|fn|pub|41-56|def do_upgrade()|
|`do_uninstall`|fn|pub|57-69|def do_uninstall()|
|`main`|fn|pub|70-109|def main()|


---

# utils.py | Python | 90L | 27 symbols | 5 imports | 1 comments
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

- var `RESET = "\033[0m"` (L8)
- var `BOLD = "\033[1m"` (L9)
- var `RED = "\033[31m"` (L10)
- var `GREEN = "\033[32m"` (L11)
- var `YELLOW = "\033[33m"` (L12)
- var `BLUE = "\033[34m"` (L13)
- var `MAGENTA = "\033[35m"` (L14)
- var `CYAN = "\033[36m"` (L15)
- var `WHITE = "\033[37m"` (L16)
- var `BRIGHT_RED = "\033[91m"` (L17)
- var `BRIGHT_GREEN = "\033[92m"` (L18)
- var `BRIGHT_YELLOW = "\033[93m"` (L19)
- var `BRIGHT_BLUE = "\033[94m"` (L20)
- var `BRIGHT_CYAN = "\033[96m"` (L21)
- var `BRIGHT_WHITE = "\033[97m"` (L22)
### fn `def color_enabled()` (L25-30)

### fn `def c(text, color)` (L31-36)

### fn `def print_info(msg)` (L37-40)

### fn `def print_error(msg)` (L41-44)

### fn `def print_warn(msg)` (L45-48)

### fn `def print_success(msg)` (L49-52)

### fn `def get_project_root()` (L53-65)

### fn `def require_project_root()` (L66-73)

### fn `def is_linux()` (L74-77)

### fn `def command_exists(cmd)` (L78-81)

### fn `def require_commands(*cmds)` (L82-88)

### fn `def run_cmd(cmd, **kwargs)` (L89-90)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`RESET`|var|pub|8||
|`BOLD`|var|pub|9||
|`RED`|var|pub|10||
|`GREEN`|var|pub|11||
|`YELLOW`|var|pub|12||
|`BLUE`|var|pub|13||
|`MAGENTA`|var|pub|14||
|`CYAN`|var|pub|15||
|`WHITE`|var|pub|16||
|`BRIGHT_RED`|var|pub|17||
|`BRIGHT_GREEN`|var|pub|18||
|`BRIGHT_YELLOW`|var|pub|19||
|`BRIGHT_BLUE`|var|pub|20||
|`BRIGHT_CYAN`|var|pub|21||
|`BRIGHT_WHITE`|var|pub|22||
|`color_enabled`|fn|pub|25-30|def color_enabled()|
|`c`|fn|pub|31-36|def c(text, color)|
|`print_info`|fn|pub|37-40|def print_info(msg)|
|`print_error`|fn|pub|41-44|def print_error(msg)|
|`print_warn`|fn|pub|45-48|def print_warn(msg)|
|`print_success`|fn|pub|49-52|def print_success(msg)|
|`get_project_root`|fn|pub|53-65|def get_project_root()|
|`require_project_root`|fn|pub|66-73|def require_project_root()|
|`is_linux`|fn|pub|74-77|def is_linux()|
|`command_exists`|fn|pub|78-81|def command_exists(cmd)|
|`require_commands`|fn|pub|82-88|def require_commands(*cmds)|
|`run_cmd`|fn|pub|89-90|def run_cmd(cmd, **kwargs)|


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

