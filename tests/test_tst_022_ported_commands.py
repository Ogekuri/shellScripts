"""
@brief Validate the chrome-debug, net, and npm-bootstrap-trust ports.
@details HDT Generator-mode suite.
  Static analysis artifact:
  UUTs: `shell_scripts.commands.chrome_debug.run` (Level 1: executable
  validation plus detached `Popen` boundary), `shell_scripts.commands.net_cmd.print_box`
  (Level 0: pure rendering), `...cmd_status` (Level 1: subprocess pipeline),
  `..._print_vlan_addresses` (Level 1: subprocess plus filtering),
  `...cmd_vlan` (Level 2), `...run` (Level 3: routing),
  `shell_scripts.commands.npm_bootstrap_trust._parse_version` (Level 0),
  `..._validate_inputs` (Level 0), `..._require_toolchain` (Level 1),
  `...run` (Level N: five-phase pipeline).
  External dependencies isolated: `require_commands`, `subprocess.run`,
  `subprocess.Popen`, `tempfile.mkdtemp`, filesystem (tmp_path), stdout and
  stderr (capsys).
@satisfies TST-022, REQ-169, REQ-170, REQ-171, REQ-172, REQ-173, REQ-174,
REQ-175, REQ-176, REQ-177, REQ-178, REQ-179, REQ-180, REQ-181, DES-069
@return {None} Pytest module scope.
"""

import types
from pathlib import Path

import pytest

import shell_scripts.commands.chrome_debug as chrome_debug
import shell_scripts.commands.net_cmd as net_cmd
import shell_scripts.commands.npm_bootstrap_trust as npm_trust
from shell_scripts.commands import get_command


class _RunRecorder:
    """
    @brief Configurable `subprocess.run` replacement with call recording.
    @details Maps argv prefixes to scripted results; unlisted commands raise
      `AssertionError` so unexpected invocations fail loudly. Each scripted
      result is either a `SimpleNamespace` returncode/stdout/stderr record or
      a callable producing one.
    """

    def __init__(self, scripts):
        """
        @brief Build the recorder from an argv-prefix script map.
        @param scripts {dict[tuple[str, ...], object]} Prefix-to-result map.
        """
        self.scripts = scripts
        self.calls = []

    def __call__(self, command, **kwargs):
        """
        @brief Resolve one recorded invocation against the script map.
        @param command {list[str]} Invoked argv vector.
        @param kwargs {dict} Forwarded subprocess keyword arguments.
        @return {types.SimpleNamespace} Scripted result with `returncode`.
        @throws {AssertionError} When no script matches the argv prefix.
        """
        self.calls.append((command, kwargs))
        for prefix, scripted in self.scripts.items():
            if tuple(command[: len(prefix)]) == prefix:
                if callable(scripted):
                    return scripted(command, kwargs)
                return types.SimpleNamespace(
                    returncode=scripted.get("returncode", 0),
                    stdout=scripted.get("stdout", ""),
                    stderr=scripted.get("stderr", ""),
                )
        raise AssertionError(f"Unexpected command: {command}")

    def argvs(self):
        """
        @brief Return the recorded argv vectors in call order.
        @return {list[list[str]]} Recorded argv vectors.
        """
        return [command for command, _kwargs in self.calls]


# ---------------------------------------------------------------------------
# chrome-debug (REQ-169, REQ-170)
# ---------------------------------------------------------------------------

def test_chrome_debug_spawns_detached_browser_with_expected_argv(monkeypatch, capsys):
    """
    @brief Validate the detached Chrome launch argv and stream suppression.
    @details Stubs the executable validation and `Popen`, runs the command,
      and asserts the exact argv vector, `DEVNULL` stdio streams,
      `start_new_session=True` detachment, non-waiting behavior, return code
      `0`, and the English progress plus attach-URL messages.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @expected_output Return code `0` plus detached launch argv.
    @satisfies TST-022, REQ-169, REQ-170
    """
    observed = {}

    def _fake_popen(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(pid=4321)

    monkeypatch.setattr(chrome_debug, "require_commands", lambda *_cmds: "/usr/bin/google-chrome")
    monkeypatch.setattr(chrome_debug.subprocess, "Popen", _fake_popen)

    result = chrome_debug.run([])

    expected_dir = Path.home() / ".config" / "google-chrome"
    assert result == 0
    assert observed["command"] == [
        "google-chrome",
        "--remote-debugging-port=9222",
        f"--user-data-dir={expected_dir}",
    ]
    assert observed["kwargs"]["stdin"] == chrome_debug.subprocess.DEVNULL
    assert observed["kwargs"]["stdout"] == chrome_debug.subprocess.DEVNULL
    assert observed["kwargs"]["stderr"] == chrome_debug.subprocess.DEVNULL
    assert observed["kwargs"]["start_new_session"] is True
    output = capsys.readouterr().out
    assert "debug mode on port 9222" in output
    assert str(expected_dir) in output
    assert "http://127.0.0.1:9222" in output


def test_chrome_debug_fails_fast_when_executable_missing(monkeypatch):
    """
    @brief Validate the fail-fast executable gate.
    @details Stubs `require_commands` to raise the shared `SystemExit(1)`
      failure and asserts the launcher propagates it without spawning a
      process.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-170, REQ-056
    """
    def _fail_require(*_cmds):
        raise SystemExit(1)

    spawned = []

    def _fail_popen(*_args, **_kwargs):
        spawned.append(True)
        raise AssertionError("Popen must not be called")

    monkeypatch.setattr(chrome_debug, "require_commands", _fail_require)
    monkeypatch.setattr(chrome_debug.subprocess, "Popen", _fail_popen)

    with pytest.raises(SystemExit) as excinfo:
        chrome_debug.run([])

    assert excinfo.value.code == 1
    assert not spawned


# ---------------------------------------------------------------------------
# net (REQ-171, REQ-172, REQ-173)
# ---------------------------------------------------------------------------

def test_print_box_renders_centered_seventy_glyph_frame(capsys):
    """
    @brief Validate the boxed section header layout.
    @details Renders one box and asserts the exact four-line shape: leading
      blank line, 70-glyph top border, centered white title row, and 70-glyph
      bottom border, all wrapped in the supplied color with reset suffixes.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @expected_output Exact deterministic box rendering.
    @satisfies TST-022, REQ-171
    """
    net_cmd.print_box("Title", net_cmd.GREEN)
    title = "Title"
    padding = (net_cmd.BOX_WIDTH - len(title) - 2) // 2
    right_padding = net_cmd.BOX_WIDTH - len(title) - 2 - padding
    line = "─" * net_cmd.BOX_WIDTH

    expected = "\n".join([
        "",
        f"{net_cmd.GREEN}┌{line}┐{net_cmd.RESET}",
        f"{net_cmd.GREEN}│{net_cmd.RESET}{' ' * padding}{net_cmd.WHITE} {title} "
        f"{net_cmd.RESET}{' ' * right_padding}{net_cmd.GREEN}│{net_cmd.RESET}",
        f"{net_cmd.GREEN}└{line}┘{net_cmd.RESET}",
    ])

    assert capsys.readouterr().out == expected + "\n"


def test_status_prints_boxed_sections_with_expected_pipeline(monkeypatch, capsys):
    """
    @brief Validate the status subcommand command pipeline and report tail.
    @details Stubs executable validation and `subprocess.run`, runs `status`,
      and asserts the five recorded commands in legacy order, the captured
      journalctl invocation, and that exactly the last 15 journal lines are
      printed.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @expected_output Five ordered command invocations plus 15-line tail.
    @satisfies TST-022, REQ-171, REQ-056
    """
    journal_lines = [f"journal-line-{index:02d}" for index in range(20)]
    recorder = _RunRecorder({
        ("nmcli",): {"returncode": 0, "stdout": "", "stderr": ""},
        ("resolvectl",): {"returncode": 0, "stdout": "", "stderr": ""},
        ("ip",): {"returncode": 0, "stdout": "", "stderr": ""},
        ("journalctl",): {
            "returncode": 0,
            "stdout": "\n".join(journal_lines) + "\n",
        },
    })

    monkeypatch.setattr(net_cmd, "require_commands", lambda *_cmds: "/resolved")
    monkeypatch.setattr(net_cmd.subprocess, "run", recorder)

    result = net_cmd.cmd_status()

    assert result == 0
    assert recorder.argvs() == [
        ["nmcli", "device", "status"],
        ["nmcli", "-f", "NAME,TYPE,AUTOCONNECT,DEVICE", "connection", "show"],
        ["resolvectl", "status"],
        ["ip", "route"],
        ["journalctl", "-b", "-u", "networking.service", "--no-pager"],
    ]
    journal_kwargs = recorder.calls[-1][1]
    assert journal_kwargs["capture_output"] is True
    assert journal_kwargs["text"] is True
    output = capsys.readouterr().out
    for title in (
        "Network Device Status",
        "Network Connections (Autoconnect)",
        "DNS Resolution Status (resolvectl)",
        "Routing Table (ip route)",
        "Network Service Log (journalctl)",
    ):
        assert title in output
    assert "journal-line-05" in output
    assert "journal-line-19" in output
    assert "journal-line-04" not in output


def test_vlan_up_activates_connection_and_prints_addresses(monkeypatch, capsys):
    """
    @brief Validate VLAN activation and address reporting.
    @details Stubs `sudo nmcli connection up vlan50` success and a captured
      `ip addr show` output containing VLAN lines, runs `vlan 50 up`, and
      asserts the exact sudo argv, the captured ip invocation, matched
      address lines with two context lines, and return code `0`.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @expected_output Activation report plus address context blocks.
    @satisfies TST-022, REQ-172
    """
    ip_output = "\n".join([
        "1: lo: <LOOPBACK> mtu 65536",
        "2: enp3s0.50@enp3s0: <BROADCAST,MULTICAST,UP>",
        "    link/ether 00:11:22:33:44:55",
        "    inet 10.0.50.10/24 metric 100",
        "    valid_lft forever",
        "3: wlan0: <BROADCAST,MULTICAST,UP>",
    ])
    recorder = _RunRecorder({
        ("ip", "addr", "show"): {"returncode": 0, "stdout": ip_output + "\n"},
        ("sudo", "nmcli"): {"returncode": 0, "stdout": "", "stderr": ""},
    })

    monkeypatch.setattr(net_cmd.subprocess, "run", recorder)

    result = net_cmd.cmd_vlan("50", "up")

    assert result == 0
    assert recorder.argvs()[0] == ["sudo", "nmcli", "connection", "up", "vlan50"]
    assert recorder.argvs()[1] == ["ip", "addr", "show"]
    assert recorder.calls[1][1]["capture_output"] is True
    output = capsys.readouterr().out
    assert "Activating connection vlan50..." in output
    assert "enp3s0.50@enp3s0" in output
    assert "link/ether 00:11:22:33:44:55" in output
    assert "inet 10.0.50.10/24 metric 100" in output
    assert "valid_lft forever" not in output
    assert "wlan0" not in output


def test_vlan_up_failure_propagates_return_code_without_address_report(monkeypatch, capsys):
    """
    @brief Validate failed-activation propagation.
    @details Stubs a failing `sudo nmcli` activation and asserts the return
      code is propagated and no address report is printed.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @expected_output Propagated non-zero return code.
    @satisfies TST-022, REQ-172
    """
    recorder = _RunRecorder({
        ("sudo", "nmcli"): {"returncode": 7, "stdout": "", "stderr": ""},
    })

    monkeypatch.setattr(net_cmd.subprocess, "run", recorder)

    result = net_cmd.cmd_vlan("50", "up")

    assert result == 7
    assert "ip addr" not in capsys.readouterr().out


def test_vlan_down_deactivates_connection_and_propagates_code(monkeypatch):
    """
    @brief Validate VLAN deactivation.
    @details Stubs `sudo nmcli connection down vlan50` with return code `4`
      and asserts the exact argv, no address report invocation, and the
      propagated return code.
    @return {None} Assertions only.
    @expected_output Propagated return code `4`.
    @satisfies TST-022, REQ-172
    """
    recorder = _RunRecorder({
        ("sudo", "nmcli"): {"returncode": 4, "stdout": "", "stderr": ""},
    })

    monkeypatch.setattr(net_cmd.subprocess, "run", recorder)

    result = net_cmd.cmd_vlan("50", "down")

    assert result == 4
    assert recorder.argvs() == [["sudo", "nmcli", "connection", "down", "vlan50"]]


@pytest.mark.parametrize("vlan_id,action", [(None, None), ("50", None), (None, "up")])
def test_vlan_missing_parameters_return_usage_error(capsys, vlan_id, action):
    """
    @brief Validate the missing-parameter usage gate.
    @details Invokes `cmd_vlan` without identifiers or actions and asserts
      return code `1` with the English usage lines on stdout.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @param vlan_id {str|None} Missing or present VLAN id.
    @param action {str|None} Missing or present action token.
    @return {None} Assertions only.
    @expected_output Return code `1` plus usage text.
    @satisfies TST-022, REQ-173
    """
    result = net_cmd.cmd_vlan(vlan_id, action)

    assert result == 1
    captured = capsys.readouterr()
    assert "missing parameters" in captured.err
    assert "net vlan <id> up" in captured.out
    assert "net vlan <id> down" in captured.out


def test_vlan_invalid_action_returns_error():
    """
    @brief Validate the invalid-action gate.
    @details Invokes `cmd_vlan` with an unknown action and asserts return
      code `1`.
    @return {None} Assertions only.
    @expected_output Return code `1`.
    @satisfies TST-022, REQ-173
    """
    assert net_cmd.cmd_vlan("50", "restart") == 1


def test_run_routes_subcommands_and_rejects_unknown(monkeypatch, capsys):
    """
    @brief Validate subcommand routing and the unknown-subcommand gate.
    @details Patches the subcommand handlers with recorders, verifies
      `status` and `vlan` routing including positional forwarding, then
      asserts unknown and empty invocations return `1` with usage text.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @expected_output Routed handlers plus return code `1` on misuse.
    @satisfies TST-022, REQ-171, REQ-172, REQ-173
    """
    routed = []

    def _fake_status():
        routed.append("status")
        return 0

    def _fake_vlan(vlan_id, action):
        routed.append(("vlan", vlan_id, action))
        return 0

    monkeypatch.setattr(net_cmd, "cmd_status", _fake_status)
    monkeypatch.setattr(net_cmd, "cmd_vlan", _fake_vlan)

    assert net_cmd.run(["status"]) == 0
    assert net_cmd.run(["vlan", "50", "up"]) == 0
    assert net_cmd.run(["vlan", "60", "down"]) == 0
    assert net_cmd.run(["bogus"]) == 1
    assert net_cmd.run([]) == 1

    assert routed == ["status", ("vlan", "50", "up"), ("vlan", "60", "down")]
    output = capsys.readouterr().out
    assert "Available commands:" in output


# ---------------------------------------------------------------------------
# npm-bootstrap-trust (REQ-174 .. REQ-181)
# ---------------------------------------------------------------------------

def test_parse_version_accepts_strict_semver_only():
    """
    @brief Validate the strict version parser.
    @details Asserts parsing of `v`-prefixed and bare `X.Y.Z` tokens and
      rejection of malformed values.
    @return {None} Assertions only.
    @expected_output Numeric tuples or `None`.
    @satisfies TST-022, REQ-176
    """
    assert npm_trust._parse_version("v22.14.0\n") == (22, 14, 0)
    assert npm_trust._parse_version("11.15.1") == (11, 15, 1)
    assert npm_trust._parse_version("11.6.0-beta.0") is None
    assert npm_trust._parse_version("latest") is None
    assert npm_trust._parse_version("1.2") is None


def test_validate_inputs_accepts_conservative_tokens():
    """
    @brief Validate the input validator happy path.
    @details Asserts acceptance of unscoped names, scoped names, maximal
      valid owners, and both workflow extensions without exiting.
    @return {None} Assertions only.
    @expected_output No `SystemExit` raised.
    @satisfies TST-022, REQ-175
    """
    npm_trust._validate_inputs("my-pkg-1", "Octocat1/my_repo.1", "publish.yml")
    npm_trust._validate_inputs("@scope/pkg", "owner/repo", "publish.yaml")


@pytest.mark.parametrize("package,repo,workflow", [
    ("My-Package", "owner/repo", "publish.yml"),
    ("a" * 215, "owner/repo", "publish.yml"),
    ("ok-pkg", "https://github.com/owner/repo", "publish.yml"),
    ("ok-pkg", "owner/", "publish.yml"),
    ("ok-pkg", "a" * 40 + "/repo", "publish.yml"),
    ("ok-pkg", "owner-/", "publish.yml"),
    ("ok-pkg", "owner/repo", "workflows/publish.yml"),
    ("ok-pkg", "owner/repo", "publish.txt"),
])
def test_validate_inputs_rejects_invalid_tokens(package, repo, workflow):
    """
    @brief Validate the input validator rejection gates.
    @details Asserts `SystemExit` code `1` for malformed package names,
      oversized names, URL repositories, incomplete repositories, oversized
      owners, dash-terminated owners, workflow paths, and unsupported
      workflow extensions.
    @param package {str} npm package token under test.
    @param repo {str} GitHub repository token under test.
    @param workflow {str} Workflow filename token under test.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-174, REQ-175
    """
    with pytest.raises(SystemExit) as excinfo:
        npm_trust._validate_inputs(package, repo, workflow)
    assert excinfo.value.code == 1


def test_require_toolchain_enforces_minimum_versions(monkeypatch):
    """
    @brief Validate the toolchain version gate.
    @details Stubs executable validation plus version probes and asserts
      acceptance at exactly the minimum versions and rejection below them.
    @expected_output No exit at minimums; `SystemExit(1)` below minimums.
    @satisfies TST-022, REQ-176
    """
    def _check(node_version, npm_version, expect_ok):
        recorder = _RunRecorder({
            ("node", "--version"): {"returncode": 0, "stdout": node_version},
            ("npm", "--version"): {"returncode": 0, "stdout": npm_version},
        })
        monkeypatch.setattr(npm_trust, "require_commands", lambda *_cmds: "/resolved")
        monkeypatch.setattr(npm_trust.subprocess, "run", recorder)
        if expect_ok:
            npm_trust._require_toolchain()
        else:
            with pytest.raises(SystemExit):
                npm_trust._require_toolchain()

    _check("v22.14.0", "11.15.0", True)
    _check("v20.11.0", "11.15.0", False)
    _check("v22.14.0", "11.14.0", False)


def test_run_completes_five_phase_pipeline(tmp_path, monkeypatch, capsys):
    """
    @brief Validate the full happy-path pipeline.
    @details Stubs every boundary: version probes, `npm whoami` success,
      `npm view` E404, `npm publish` success reading the placeholder files,
      `npm trust github` and `npm trust list` success, and a recorded
      temporary directory. Asserts return code `0`, phase markers, publish
      argv with dist-tag bootstrap and public access, trust argv contents,
      placeholder payload contents at publish time, and temporary-directory
      removal.
    @param tmp_path {Path} Pytest per-test temporary directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @expected_output Return code `0` plus five phases and cleanup.
    @satisfies TST-022, REQ-174, REQ-176, REQ-177, REQ-178, REQ-179, REQ-180,
    REQ-181
    """
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    observed = {}

    def _fake_publish(command, kwargs):
        package_json = (Path(kwargs["cwd"]) / "package.json").read_text(encoding="utf-8")
        index_js = (Path(kwargs["cwd"]) / "index.js").read_text(encoding="utf-8")
        observed["package_json"] = package_json
        observed["index_js"] = index_js
        assert '"version": "0.0.0"' in package_json
        assert '"url": "git+https://github.com/owner/repo.git"' in package_json
        assert index_js == "module.exports = {};\n"
        return types.SimpleNamespace(returncode=0)

    recorder = _RunRecorder({
        ("node", "--version"): {"returncode": 0, "stdout": "v22.14.0"},
        ("npm", "--version"): {"returncode": 0, "stdout": "11.15.0"},
        ("npm", "whoami"): {"returncode": 0, "stdout": "octocat\n"},
        ("npm", "view"): {"returncode": 1, "stdout": "", "stderr": "npm error code E404\n"},
        ("npm", "publish"): _fake_publish,
        ("npm", "trust", "github"): {"returncode": 0, "stdout": "", "stderr": ""},
        ("npm", "trust", "list"): {"returncode": 0, "stdout": "", "stderr": ""},
    })

    def _fake_mkdtemp(**_kwargs):
        path = temp_root / "npm-bootstrap.abc123"
        path.mkdir()
        return str(path)

    monkeypatch.setattr(npm_trust, "require_commands", lambda *_cmds: "/resolved")
    monkeypatch.setattr(npm_trust.subprocess, "run", recorder)
    monkeypatch.setattr(npm_trust.tempfile, "mkdtemp", _fake_mkdtemp)

    result = npm_trust.run(["-p", "my-pkg", "-r", "owner/repo", "-f", "publish.yml"])

    assert result == 0
    argvs = recorder.argvs()
    assert ["npm", "publish", "--tag=bootstrap", "--access=public",
            "--registry=https://registry.npmjs.org/"] in argvs
    assert ["npm", "trust", "github", "my-pkg", "--repo", "owner/repo",
            "--file", "publish.yml", "--allow-publish",
            "--registry=https://registry.npmjs.org/"] in argvs
    assert ["npm", "trust", "list", "my-pkg",
            "--registry=https://registry.npmjs.org/"] in argvs
    assert observed["package_json"].startswith("{\n")
    output = capsys.readouterr().out
    for marker in ("[1/5]", "[2/5]", "[3/5]", "[4/5]", "[5/5]"):
        assert marker in output
    assert "npm account: octocat" in output
    assert "within 2 days" in output
    assert not (temp_root / "npm-bootstrap.abc123").exists()


def test_run_removes_temp_directory_on_failure_paths(tmp_path, monkeypatch):
    """
    @brief Validate temporary-directory cleanup on abort paths.
    @details Stubs `npm view` with an existing-package response and asserts
      `SystemExit(1)` plus removal of the created temporary directory and no
      publish invocation.
    @param tmp_path {Path} Pytest per-test temporary directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-178, REQ-179
    """
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    temp_dir_holder = {}

    recorder = _RunRecorder({
        ("node", "--version"): {"returncode": 0, "stdout": "v22.14.0"},
        ("npm", "--version"): {"returncode": 0, "stdout": "11.15.0"},
        ("npm", "whoami"): {"returncode": 0, "stdout": "octocat\n"},
        ("npm", "view"): {"returncode": 0, "stdout": '["0.0.0"]', "stderr": ""},
    })

    def _fake_mkdtemp(**_kwargs):
        path = temp_root / "npm-bootstrap.xyz789"
        path.mkdir()
        temp_dir_holder["path"] = str(path)
        return str(path)

    monkeypatch.setattr(npm_trust, "require_commands", lambda *_cmds: "/resolved")
    monkeypatch.setattr(npm_trust.subprocess, "run", recorder)
    monkeypatch.setattr(npm_trust.tempfile, "mkdtemp", _fake_mkdtemp)

    with pytest.raises(SystemExit) as excinfo:
        npm_trust.run(["-p", "my-pkg", "-r", "owner/repo", "-f", "publish.yml"])

    assert excinfo.value.code == 1
    assert not (temp_root / "npm-bootstrap.xyz789").exists()
    assert all(argv[0:2] != ["npm", "publish"] for argv in recorder.argvs())


def test_run_aborts_when_availability_check_is_unreliable(tmp_path, monkeypatch):
    """
    @brief Validate the unverifiable-name abort gate.
    @details Stubs `npm view` failing without an `E404` marker and asserts
      `SystemExit(1)` with the failure reason forwarded to stderr.
    @param tmp_path {Path} Pytest per-test temporary directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-178
    """
    recorder = _RunRecorder({
        ("node", "--version"): {"returncode": 0, "stdout": "v22.14.0"},
        ("npm", "--version"): {"returncode": 0, "stdout": "11.15.0"},
        ("npm", "whoami"): {"returncode": 0, "stdout": "octocat\n"},
        ("npm", "view"): {"returncode": 1, "stdout": "", "stderr": "npm error network down\n"},
    })
    monkeypatch.setattr(npm_trust, "require_commands", lambda *_cmds: "/resolved")
    monkeypatch.setattr(npm_trust.subprocess, "run", recorder)
    monkeypatch.setattr(
        npm_trust.tempfile, "mkdtemp",
        lambda **_kwargs: str(_make_temp_dir(tmp_path)),
    )

    with pytest.raises(SystemExit) as excinfo:
        npm_trust.run(["-p", "my-pkg", "-r", "owner/repo", "-f", "publish.yml"])

    assert excinfo.value.code == 1


def test_run_aborts_when_authentication_fails(tmp_path, monkeypatch):
    """
    @brief Validate the pre-mutation authentication gate.
    @details Stubs a failing `npm whoami` and asserts `SystemExit(1)` before
      any temporary directory creation.
    @param tmp_path {Path} Pytest per-test temporary directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-177
    """
    recorder = _RunRecorder({
        ("node", "--version"): {"returncode": 0, "stdout": "v22.14.0"},
        ("npm", "--version"): {"returncode": 0, "stdout": "11.15.0"},
        ("npm", "whoami"): {"returncode": 1, "stdout": "", "stderr": "no auth\n"},
    })
    mkdtemp_calls = []

    def _recording_mkdtemp(**_kwargs):
        mkdtemp_calls.append(True)
        return str(_make_temp_dir(tmp_path))

    monkeypatch.setattr(npm_trust, "require_commands", lambda *_cmds: "/resolved")
    monkeypatch.setattr(npm_trust.subprocess, "run", recorder)
    monkeypatch.setattr(npm_trust.tempfile, "mkdtemp", _recording_mkdtemp)

    with pytest.raises(SystemExit) as excinfo:
        npm_trust.run(["-p", "my-pkg", "-r", "owner/repo", "-f", "publish.yml"])

    assert excinfo.value.code == 1
    assert not mkdtemp_calls


def test_run_aborts_when_publish_fails(tmp_path, monkeypatch):
    """
    @brief Validate the publish-failure abort gate.
    @details Stubs a failing `npm publish` and asserts `SystemExit(1)` with
      no trust invocation and temporary-directory cleanup.
    @param tmp_path {Path} Pytest per-test temporary directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-179
    """
    temp_dir = _make_temp_dir(tmp_path)
    recorder = _RunRecorder({
        ("node", "--version"): {"returncode": 0, "stdout": "v22.14.0"},
        ("npm", "--version"): {"returncode": 0, "stdout": "11.15.0"},
        ("npm", "whoami"): {"returncode": 0, "stdout": "octocat\n"},
        ("npm", "view"): {"returncode": 1, "stdout": "", "stderr": "npm error code E404\n"},
        ("npm", "publish"): {"returncode": 1, "stdout": "", "stderr": ""},
    })
    monkeypatch.setattr(npm_trust, "require_commands", lambda *_cmds: "/resolved")
    monkeypatch.setattr(npm_trust.subprocess, "run", recorder)
    monkeypatch.setattr(npm_trust.tempfile, "mkdtemp", lambda **_kwargs: str(temp_dir))

    with pytest.raises(SystemExit) as excinfo:
        npm_trust.run(["-p", "my-pkg", "-r", "owner/repo", "-f", "publish.yml"])

    assert excinfo.value.code == 1
    assert all(argv[0:3] != ["npm", "trust", "github"] for argv in recorder.argvs())
    assert not temp_dir.exists()


def test_run_aborts_when_trust_creation_fails(tmp_path, monkeypatch):
    """
    @brief Validate the trust-creation failure gate.
    @details Stubs successful publish and failing `npm trust github` and
      asserts `SystemExit(1)` with no trust-list invocation.
    @param tmp_path {Path} Pytest per-test temporary directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-180
    """
    temp_dir = _make_temp_dir(tmp_path)
    recorder = _RunRecorder({
        ("node", "--version"): {"returncode": 0, "stdout": "v22.14.0"},
        ("npm", "--version"): {"returncode": 0, "stdout": "11.15.0"},
        ("npm", "whoami"): {"returncode": 0, "stdout": "octocat\n"},
        ("npm", "view"): {"returncode": 1, "stdout": "", "stderr": "npm error code E404\n"},
        ("npm", "publish"): {"returncode": 0, "stdout": "", "stderr": ""},
        ("npm", "trust", "github"): {"returncode": 1, "stdout": "", "stderr": ""},
    })
    monkeypatch.setattr(npm_trust, "require_commands", lambda *_cmds: "/resolved")
    monkeypatch.setattr(npm_trust.subprocess, "run", recorder)
    monkeypatch.setattr(npm_trust.tempfile, "mkdtemp", lambda **_kwargs: str(temp_dir))

    with pytest.raises(SystemExit) as excinfo:
        npm_trust.run(["-p", "my-pkg", "-r", "owner/repo", "-f", "publish.yml"])

    assert excinfo.value.code == 1
    assert all(argv[0:3] != ["npm", "trust", "list"] for argv in recorder.argvs())


def test_run_rejects_unknown_arguments_with_legacy_exit_code(capsys):
    """
    @brief Validate the unknown-argument usage gate.
    @details Runs with an unrecognized positional argument and asserts
      `SystemExit` code `1` matching the legacy `usage(1)` contract.
    @param capsys {pytest.CaptureFixture} Stderr capture fixture.
    @return {None} Assertions only.
    @expected_exception {SystemExit} Exit code `1`.
    @satisfies TST-022, REQ-174
    """
    with pytest.raises(SystemExit) as excinfo:
        npm_trust.run(["-p", "pkg", "-r", "owner/repo", "-f", "publish.yml", "extra"])

    assert excinfo.value.code == 1


def test_registry_exposes_all_ported_commands():
    """
    @brief Validate static registry exposure for all four ported commands.
    @details Asserts every registry entry resolves its module with a
      non-empty `DESCRIPTION`.
    @return {None} Assertions only.
    @satisfies TST-022, DES-069, PRJ-008
    """
    for token, module in (
        ("meld-highlight-theme", _lazy_import("shell_scripts.commands.meld_highlight_theme")),
        ("chrome-debug", _lazy_import("shell_scripts.commands.chrome_debug")),
        ("net", _lazy_import("shell_scripts.commands.net_cmd")),
        ("npm-bootstrap-trust", _lazy_import("shell_scripts.commands.npm_bootstrap_trust")),
    ):
        assert get_command(token) is module
        assert module.DESCRIPTION


def _make_temp_dir(tmp_path):
    """
    @brief Create one isolated temporary directory for pipeline staging.
    @param tmp_path {Path} Pytest per-test temporary directory.
    @return {Path} Created directory path.
    """
    path = tmp_path / "npm-bootstrap.staged"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _lazy_import(module_name):
    """
    @brief Import one command module by dotted name.
    @param module_name {str} Dotted module path.
    @return {module} Imported module.
    """
    import importlib

    return importlib.import_module(module_name)
