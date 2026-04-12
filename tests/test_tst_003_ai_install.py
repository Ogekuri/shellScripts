"""
@brief Validate AI installer selector and installer behaviors.
@details Verifies selector parsing, unknown-selector rejection, npm-based
  installer command construction, Claude binary installation flow, and Kiro ZIP
  extraction/copy flow. External network/process boundaries are mocked.
@satisfies TST-003, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-047, REQ-067
@return {None} Pytest module scope.
"""

import types
import urllib.error
import zipfile
from email.message import Message

import pytest

import shell_scripts.commands.ai_install as ai_install


def test_run_without_selector_executes_all_installers(monkeypatch):
    """
    @brief Validate default selector behavior.
    @details Replaces installer registry with deterministic call trackers and
      asserts that empty CLI args execute all registered installers.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-006
    """

    called = []
    fake_installers = {
        "codex": lambda: called.append("codex"),
        "copilot": lambda: called.append("copilot"),
        "gemini": lambda: called.append("gemini"),
        "opencode": lambda: called.append("opencode"),
        "claude": lambda: called.append("claude"),
        "kiro": lambda: called.append("kiro"),
    }
    monkeypatch.setattr(ai_install, "ALL_INSTALLERS", fake_installers)

    result = ai_install.run([])

    assert result == 0
    assert called == list(fake_installers.keys())


def test_run_unknown_selector_returns_one(monkeypatch):
    """
    @brief Validate rejection of unknown ai-install selectors.
    @details Executes parser with an unsupported selector token and asserts
      immediate non-zero status.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-007
    """

    monkeypatch.setattr(ai_install, "ALL_INSTALLERS", {"codex": lambda: None})

    result = ai_install.run(["--unknown-selector"])

    assert result == 1


@pytest.mark.parametrize(
    "tool_key, expected_cmd",
    [
        ("codex", ["npm", "install", "-g", "@openai/codex"]),
        (
            "copilot",
            ["npm", "install", "-g", "@github/copilot"],
        ),
        (
            "gemini",
            ["npm", "install", "-g", "@google/gemini-cli"],
        ),
        (
            "opencode",
            ["npm", "install", "-g", "opencode-ai"],
        ),
    ],
)
def test_install_npm_tool_uses_linux_non_sudo_command(
    monkeypatch,
    tool_key,
    expected_cmd,
):
    """
    @brief Validate npm installer command vectors on Linux.
    @details Intercepts subprocess invocation on Linux runtime path and asserts
      exact command tokens without `sudo` prefix for each npm-based installer.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tool_key {str} Installer key in ai_install.TOOLS.
    @param expected_cmd {list[str]} Expected subprocess command tokens.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-008
    """

    observed = {}

    def _fake_run(command):
        """
        @brief Mock subprocess.run for npm installer.
        @details Captures command list and returns successful exit status.
        @param command {list[str]} Command token vector.
        @return {types.SimpleNamespace} Object with returncode field.
        """

        observed["command"] = command
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(ai_install.subprocess, "run", _fake_run)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(ai_install, "require_commands", lambda *_cmds: None)

    ai_install._install_npm_tool(tool_key)

    assert observed["command"] == expected_cmd


def test_install_npm_tool_uses_sudo_on_macos(monkeypatch):
    """
    @brief Validate npm installer command prefix on macOS.
    @details Forces macOS runtime branch and verifies npm command executes with
      `sudo` prefix.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-008, REQ-047
    """

    observed = {}

    def _fake_run(command):
        """
        @brief Mock subprocess.run for macOS npm install path.
        @details Captures command payload and returns successful status.
        @param command {list[str]} Command token vector.
        @return {types.SimpleNamespace} Object with returncode field.
        """

        observed["command"] = command
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(ai_install.subprocess, "run", _fake_run)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: "darwin")
    monkeypatch.setattr(ai_install, "require_commands", lambda *_cmds: None)

    ai_install._install_npm_tool("copilot")

    assert observed["command"] == [
        "sudo",
        "npm",
        "install",
        "-g",
        "@github/copilot",
    ]


def test_install_npm_tool_omits_sudo_on_windows(monkeypatch):
    """
    @brief Validate npm installer command prefix on Windows.
    @details Forces Windows runtime branch and verifies npm command executes
      without `sudo` prefix.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-008, REQ-047
    """

    observed = {}

    def _fake_run(command):
        """
        @brief Mock subprocess.run for Windows npm install path.
        @details Captures command payload and returns successful status.
        @param command {list[str]} Command token vector.
        @return {types.SimpleNamespace} Object with returncode field.
        """

        observed["command"] = command
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(ai_install.subprocess, "run", _fake_run)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: "windows")
    monkeypatch.setattr(ai_install, "require_commands", lambda *_cmds: None)

    ai_install._install_npm_tool("copilot")

    assert observed["command"][1:] == ["install", "-g", "@github/copilot"]
    assert all(token != "sudo" for token in observed["command"])


def test_install_npm_tool_uses_npm_cmd_on_windows(monkeypatch):
    """
    @brief Reproduce Windows npm executable resolution defect.
    @details Simulates a Windows PATH where only `npm.cmd` exists and asserts
      installer execution must use that executable without raising.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-008, REQ-047
    """

    observed = {}

    def _fake_run(command):
        """
        @brief Mock subprocess.run for Windows npm-cmd path.
        @details Captures command payload and raises when unresolved `npm` token
          is used to mirror WinError 2 behavior.
        @param command {list[str]} Command token vector.
        @return {types.SimpleNamespace} Object with returncode field.
        @throws {FileNotFoundError} When command executable is unresolved.
        """

        observed["command"] = command
        if command[0] == "npm":
            raise FileNotFoundError("[WinError 2] npm not found")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(ai_install.subprocess, "run", _fake_run)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: "windows")
    monkeypatch.setattr(ai_install, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(
        ai_install.shutil,
        "which",
        lambda name: "C:/Program Files/nodejs/npm.cmd" if name == "npm.cmd" else None,
    )

    ai_install._install_npm_tool("codex")

    assert observed["command"][0].endswith("npm.cmd")


def test_install_npm_tool_retries_copilot_once_on_windows_failure(monkeypatch):
    """
    @brief Reproduce Windows Copilot npm EPERM transient install failure.
    @details Simulates a first failed npm install attempt followed by success
      and asserts the installer retries Copilot exactly once on Windows.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-008, REQ-047
    """

    observed = {"commands": []}

    def _fake_run(command):
        """
        @brief Mock subprocess.run for retry-path assertions.
        @details Records each invocation and returns a non-zero result on the
          first attempt, then success on the second attempt.
        @param command {list[str]} Command token vector.
        @return {types.SimpleNamespace} Object with returncode field.
        """

        observed["commands"].append(list(command))
        if len(observed["commands"]) == 1:
            return types.SimpleNamespace(returncode=1)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(ai_install.subprocess, "run", _fake_run)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: "windows")
    monkeypatch.setattr(ai_install, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(
        ai_install.shutil,
        "which",
        lambda name: "C:/Program Files/nodejs/npm.cmd" if name == "npm.cmd" else None,
    )

    ai_install._install_npm_tool("copilot")

    assert len(observed["commands"]) == 2
    assert observed["commands"][0] == observed["commands"][1]


@pytest.mark.parametrize(
    "runtime_os, expected_artifact_segment",
    [
        ("linux", "/linux-x64/claude"),
        ("windows", "/windows-x64/claude.exe"),
        ("darwin", "/darwin-arm64/claude"),
    ],
)
def test_install_claude_downloads_runtime_os_artifact(
    monkeypatch,
    tmp_path,
    runtime_os,
    expected_artifact_segment,
):
    """
    @brief Validate Claude installer runtime-OS package selection.
    @details Mocks metadata fetch and binary download operations, redirects
      home directory to temporary storage, and verifies installer requests
      runtime-OS specific artifact paths.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @param runtime_os {str} Simulated runtime OS token.
    @param expected_artifact_segment {str} Expected Claude artifact URL suffix.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-009, DES-013
    """

    class _FakeResponse:
        """
        @brief Minimal urlopen response stub.
        @details Exposes context-manager API and deterministic read payload.
        @return {None} Helper type for unit tests.
        """

        def __enter__(self):
            """
            @brief Enter context.
            @details Returns self for with-statement compatibility.
            @return {_FakeResponse} Self instance.
            """

            return self

        def __exit__(self, exc_type, exc, tb):
            """
            @brief Exit context.
            @details Propagates exceptions unchanged.
            @param exc_type {type | None} Exception class.
            @param exc {BaseException | None} Exception value.
            @param tb {TracebackType | None} Traceback object.
            @return {bool} False to avoid exception suppression.
            """

            del exc_type, exc, tb
            return False

        def read(self):
            """
            @brief Return deterministic latest tag payload.
            @details Encodes a static version string used by installer logic.
            @return {bytes} UTF-8 byte payload.
            """

            return b"v9.9.9"

    def _fake_urlopen(url, timeout=0):
        """
        @brief Mock urllib.request.urlopen.
        @details Validates metadata endpoint shape and returns fake response.
        @param url {str} Requested URL.
        @param timeout {int | float} Timeout seconds.
        @return {_FakeResponse} Fake context-manager response.
        """

        del timeout
        assert url.endswith("/latest")
        return _FakeResponse()

    def _fake_urlretrieve(url, destination):
        """
        @brief Mock Claude artifact download.
        @details Asserts URL uses expected runtime-OS artifact segment and writes
          deterministic executable payload at destination path.
        @param url {str} Binary source URL.
        @param destination {str} Destination path.
        @return {tuple[str, None]} Destination and placeholder headers.
        """

        assert "/v9.9.9/" in url
        assert expected_artifact_segment in url
        with open(destination, "wb") as handle:
            handle.write(b"#!/bin/sh\nexit 0\n")
        return destination, None

    chmod_calls = []

    def _fake_chmod(path_obj, mode):
        """
        @brief Mock Path.chmod for permission assertions.
        @details Captures chmod calls because Windows test filesystems do not
          reliably expose POSIX execute bits in stat mode checks.
        @param path_obj {pathlib.Path} Target path receiving chmod.
        @param mode {int} Permission mode argument.
        @return {None} Side-effect capture only.
        """

        chmod_calls.append((str(path_obj), mode))

    monkeypatch.setattr(ai_install.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(ai_install.Path, "chmod", _fake_chmod)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: runtime_os)
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("urllib.request.urlretrieve", _fake_urlretrieve)

    ai_install._install_claude()

    target = tmp_path / ".claude" / "bin" / "claude"
    assert target.exists()
    if runtime_os != "windows":
        assert chmod_calls == [(str(target), 0o755)]
    else:
        assert not chmod_calls


def test_install_claude_falls_back_to_second_artifact_candidate(monkeypatch, tmp_path):
    """
    @brief Validate Claude artifact fallback for the same runtime OS.
    @details Simulates a missing first candidate for Windows and verifies
      installer retries next configured candidate URL before succeeding.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-009, DES-013
    """

    class _FakeResponse:
        """
        @brief Minimal urlopen response stub.
        @details Exposes context-manager API and deterministic read payload.
        @return {None} Helper type for unit tests.
        """

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def read(self):
            return b"v9.9.9"

    calls = []

    def _fake_urlretrieve(url, destination):
        """
        @brief Mock Claude artifact download with fallback behavior.
        @details Fails the first Windows URL and succeeds on fallback candidate.
        @param url {str} Artifact source URL.
        @param destination {str} Destination path.
        @return {tuple[str, None]} Destination and placeholder headers.
        @throws {urllib.error.HTTPError} Simulated 404 for first candidate.
        """

        calls.append(url)
        if url.endswith("/windows-x64/claude.exe"):
            raise urllib.error.HTTPError(
                url, 404, "not found", hdrs=Message(), fp=None
            )
        assert url.endswith("/win32-x64/claude.exe")
        with open(destination, "wb") as handle:
            handle.write(b"MZ")
        return destination, None

    monkeypatch.setattr(ai_install.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: "windows")
    monkeypatch.setattr("urllib.request.urlopen", lambda _url, timeout=0: _FakeResponse())
    monkeypatch.setattr("urllib.request.urlretrieve", _fake_urlretrieve)

    ai_install._install_claude()

    assert len(calls) == 2
    assert calls[0].endswith("/windows-x64/claude.exe")
    assert calls[1].endswith("/win32-x64/claude.exe")


@pytest.mark.parametrize(
    "machine_token, libc_token, expected_download",
    [
        ("x86_64", "gnu", "1.29.5/kirocli-x86_64-linux.zip"),
        ("amd64", "musl", "1.29.5/kirocli-x86_64-linux-musl.zip"),
        ("aarch64", "gnu", "1.29.5/kirocli-aarch64-linux.zip"),
        ("arm64", "musl", "1.29.5/kirocli-aarch64-linux-musl.zip"),
    ],
)
def test_install_kiro_resolves_linux_manifest_package_and_copies_binaries(
    monkeypatch,
    tmp_path,
    machine_token,
    libc_token,
    expected_download,
):
    """
    @brief Validate Kiro Linux manifest package resolution and install flow.
    @details Mocks upstream manifest payload and ZIP download, resolves package
      from runtime architecture/libc selectors, and verifies copied binaries.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @param machine_token {str} Simulated machine architecture token.
    @param libc_token {str} Simulated Linux libc class token.
    @param expected_download {str} Expected manifest download path.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-010, DES-013
    """

    binary_names = ("kiro-cli", "kiro-cli-chat", "kiro-cli-term")
    manifest_payload = {
        "version": "1.29.5",
        "packages": [
            {
                "os": "linux",
                "fileType": "zip",
                "variant": "headless",
                "architecture": "x86_64",
                "targetTriple": "x86_64-unknown-linux-gnu",
                "download": "1.29.5/kirocli-x86_64-linux.zip",
            },
            {
                "os": "linux",
                "fileType": "zip",
                "variant": "headless",
                "architecture": "x86_64",
                "targetTriple": "x86_64-unknown-linux-musl",
                "download": "1.29.5/kirocli-x86_64-linux-musl.zip",
            },
            {
                "os": "linux",
                "fileType": "zip",
                "variant": "headless",
                "architecture": "aarch64",
                "targetTriple": "aarch64-unknown-linux-gnu",
                "download": "1.29.5/kirocli-aarch64-linux.zip",
            },
            {
                "os": "linux",
                "fileType": "zip",
                "variant": "headless",
                "architecture": "aarch64",
                "targetTriple": "aarch64-unknown-linux-musl",
                "download": "1.29.5/kirocli-aarch64-linux-musl.zip",
            },
            {
                "os": "macos",
                "fileType": "dmg",
                "variant": "full",
                "architecture": "universal",
                "targetTriple": "universal-apple-darwin",
                "download": "1.29.5/Kiro CLI.dmg",
            },
        ],
    }
    observed = {"urlopen": None, "download": None}

    class _FakeManifestResponse:
        """
        @brief Mock HTTP response for manifest endpoint.
        @details Returns deterministic JSON payload for package selection logic.
        @return {None} Context-manager helper for tests.
        """

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def read(self):
            return ai_install.json.dumps(manifest_payload).encode()

    def _fake_urlopen(url, timeout=0):
        """
        @brief Mock manifest fetch endpoint.
        @details Captures URL and returns deterministic payload.
        @param url {str} Download URL.
        @param timeout {int | float} Timeout value.
        @return {_FakeManifestResponse} Context-manager response.
        """

        del timeout
        observed["urlopen"] = url
        assert url == ai_install.KIRO_MANIFEST_URL
        return _FakeManifestResponse()

    def _fake_urlretrieve(url, destination):
        """
        @brief Mock Kiro ZIP download.
        @details Asserts resolved package URL and writes deterministic archive.
        @param url {str} Download URL.
        @param destination {str} Destination archive path.
        @return {tuple[str, None]} Destination and placeholder headers.
        """

        observed["download"] = url
        assert url == f"{ai_install.KIRO_CHANNEL_BASE_URL}/{expected_download}"
        with zipfile.ZipFile(destination, "w") as archive:
            for name in binary_names:
                archive.writestr(f"kirocli/bin/{name}", "#!/bin/sh\n")
        return destination, None

    chmod_calls = []

    def _fake_chmod(path_obj, mode):
        """
        @brief Mock Path.chmod for permission assertions.
        @details Captures chmod calls because Windows test filesystems do not
          reliably expose POSIX execute bits in stat mode checks.
        @param path_obj {pathlib.Path} Target path receiving chmod.
        @param mode {int} Permission mode argument.
        @return {None} Side-effect capture only.
        """

        chmod_calls.append((str(path_obj), mode))

    monkeypatch.setattr(ai_install.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(ai_install.Path, "chmod", _fake_chmod)
    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(ai_install.platform, "machine", lambda: machine_token)
    if libc_token == "musl":
        monkeypatch.setattr(ai_install.platform, "libc_ver", lambda: ("musl", "1.2.5"))
    else:
        monkeypatch.setattr(ai_install.platform, "libc_ver", lambda: ("glibc", "2.39"))
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("urllib.request.urlretrieve", _fake_urlretrieve)

    ai_install._install_kiro()

    install_dir = tmp_path / ".local" / "bin"
    for name in binary_names:
        path = install_dir / name
        assert path.exists()
    assert len(chmod_calls) == len(binary_names)
    assert all(mode == 0o755 for _, mode in chmod_calls)
    assert observed["urlopen"] == ai_install.KIRO_MANIFEST_URL
    assert observed["download"] == f"{ai_install.KIRO_CHANNEL_BASE_URL}/{expected_download}"


@pytest.mark.parametrize(
    "runtime_os, expected_fragment",
    [
        ("windows", "unsupported runtime OS windows"),
        ("darwin", "unsupported runtime OS darwin"),
    ],
)
def test_install_kiro_rejects_unsupported_runtime_os(
    monkeypatch,
    capsys,
    runtime_os,
    expected_fragment,
):
    """
    @brief Validate explicit unsupported-platform handling for Kiro installer.
    @details Forces unsupported runtime OS values and verifies installer emits
      explicit errors without performing network download operations.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Output capture fixture.
    @param runtime_os {str} Simulated unsupported runtime OS token.
    @param expected_fragment {str} Expected stderr fragment.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-067
    """

    called = {"urlopen": 0, "urlretrieve": 0}

    def _unexpected_urlopen(*_args, **_kwargs):
        called["urlopen"] += 1
        raise AssertionError("urlopen must not be called on unsupported platforms")

    def _unexpected_urlretrieve(*_args, **_kwargs):
        called["urlretrieve"] += 1
        raise AssertionError("urlretrieve must not be called on unsupported platforms")

    monkeypatch.setattr(ai_install, "get_runtime_os", lambda: runtime_os)
    monkeypatch.setattr("urllib.request.urlopen", _unexpected_urlopen)
    monkeypatch.setattr("urllib.request.urlretrieve", _unexpected_urlretrieve)

    ai_install._install_kiro()

    captured = capsys.readouterr()
    assert expected_fragment in captured.err
    assert called["urlopen"] == 0
    assert called["urlretrieve"] == 0
