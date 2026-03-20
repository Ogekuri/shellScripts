"""
@brief Validate AI installer selector and installer behaviors.
@details Verifies selector parsing, unknown-selector rejection, npm-based
  installer command construction, Claude binary installation flow, and Kiro ZIP
  extraction/copy flow. External network/process boundaries are mocked.
@satisfies TST-003, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-047
@return {None} Pytest module scope.
"""

import types
import zipfile

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
        ("codex", ["sudo", "npm", "install", "-g", "@openai/codex"]),
        (
            "copilot",
            ["sudo", "npm", "install", "-g", "@github/copilot"],
        ),
        (
            "gemini",
            ["sudo", "npm", "install", "-g", "@google/gemini-cli"],
        ),
        (
            "opencode",
            ["sudo", "npm", "install", "-g", "opencode-ai"],
        ),
    ],
)
def test_install_npm_tool_uses_expected_command(
    monkeypatch,
    tool_key,
    expected_cmd,
):
    """
    @brief Validate npm installer command vectors.
    @details Intercepts subprocess invocation on non-Windows path and asserts
      exact command tokens with `sudo` prefix for each npm-based installer.
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
    monkeypatch.setattr(ai_install, "is_windows", lambda: False)

    ai_install._install_npm_tool(tool_key)

    assert observed["command"] == expected_cmd


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
    monkeypatch.setattr(ai_install, "is_windows", lambda: True)

    ai_install._install_npm_tool("copilot")

    assert observed["command"] == ["npm", "install", "-g", "@github/copilot"]


def test_install_claude_downloads_latest_and_installs_binary(monkeypatch, tmp_path):
    """
    @brief Validate Claude installer download/install flow.
    @details Mocks metadata fetch and binary download operations, redirects
      home directory to temporary storage, and validates output path and mode.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-009
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
        @brief Mock urllib.request.urlretrieve for Claude binary.
        @details Writes deterministic executable payload at destination path.
        @param url {str} Binary source URL.
        @param destination {str} Destination path.
        @return {tuple[str, None]} Destination and placeholder headers.
        """

        assert "/v9.9.9/" in url
        with open(destination, "wb") as handle:
            handle.write(b"#!/bin/sh\nexit 0\n")
        return destination, None

    monkeypatch.setattr(ai_install.Path, "home", lambda: tmp_path)
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("urllib.request.urlretrieve", _fake_urlretrieve)

    ai_install._install_claude()

    target = tmp_path / ".claude" / "bin" / "claude"
    assert target.exists()
    assert target.stat().st_mode & 0o111


def test_install_kiro_extracts_and_copies_executables(monkeypatch, tmp_path):
    """
    @brief Validate Kiro installer ZIP extraction and copy flow.
    @details Mocks ZIP download by generating an in-memory archive containing
      expected binaries and verifies final installation under ~/.local/bin.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-003, REQ-010
    """

    def _fake_urlretrieve(url, destination):
        """
        @brief Mock Kiro ZIP download.
        @details Writes a deterministic ZIP archive with expected binaries.
        @param url {str} Download URL.
        @param destination {str} Destination archive path.
        @return {tuple[str, None]} Destination and placeholder headers.
        """

        assert url == ai_install.KIRO_URL
        with zipfile.ZipFile(destination, "w") as archive:
            archive.writestr("kirocli/bin/kiro-cli", "#!/bin/sh\n")
            archive.writestr("kirocli/bin/kiro-cli-chat", "#!/bin/sh\n")
            archive.writestr("kirocli/bin/kiro-cli-term", "#!/bin/sh\n")
        return destination, None

    monkeypatch.setattr(ai_install.Path, "home", lambda: tmp_path)
    monkeypatch.setattr("urllib.request.urlretrieve", _fake_urlretrieve)

    ai_install._install_kiro()

    install_dir = tmp_path / ".local" / "bin"
    for name in ("kiro-cli", "kiro-cli-chat", "kiro-cli-term"):
        path = install_dir / name
        assert path.exists()
        assert path.stat().st_mode & 0o111
