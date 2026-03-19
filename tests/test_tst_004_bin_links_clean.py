"""
@brief Validate bin-links and clean command behaviors.
@details Verifies symlink naming/creation semantics, mismatched symlink update
  behavior, regular-file overwrite protection, and clean confirmation gates.
@satisfies TST-004, REQ-011, REQ-012, REQ-013
@return {None} Pytest module scope.
"""

import shell_scripts.commands.bin_links as bin_links
import shell_scripts.commands.clean as clean


def test_bin_links_creates_destination_and_strips_sh_suffix(tmp_path):
    """
    @brief Validate destination creation and .sh suffix stripping.
    @details Creates a source script file, runs bin-links with explicit source
      and destination directories, and verifies generated link basename mapping.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-004, REQ-011
    """

    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest-bin"
    src_dir.mkdir()
    (src_dir / "tool.sh").write_text("#!/bin/sh\n")

    result = bin_links.run([str(src_dir), "--dest", str(dest_dir)])

    assert result == 0
    link_path = dest_dir / "tool"
    assert link_path.is_symlink()
    assert link_path.resolve() == (src_dir / "tool.sh").resolve()


def test_bin_links_updates_mismatched_symlink(tmp_path):
    """
    @brief Validate symlink retargeting semantics.
    @details Precreates a destination symlink pointing at an incorrect file and
      verifies bin-links replaces it with the source file target.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-004, REQ-012
    """

    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest-bin"
    src_dir.mkdir()
    dest_dir.mkdir()

    correct = src_dir / "runner.sh"
    wrong = src_dir / "wrong.sh"
    correct.write_text("#!/bin/sh\n")
    wrong.write_text("#!/bin/sh\n")

    link_path = dest_dir / "runner"
    link_path.symlink_to(wrong)

    result = bin_links.run([str(src_dir), "--dest", str(dest_dir)])

    assert result == 0
    assert link_path.is_symlink()
    assert link_path.resolve() == correct.resolve()


def test_bin_links_does_not_overwrite_regular_file(tmp_path):
    """
    @brief Validate regular-file overwrite guard.
    @details Places a regular file at the destination link path and confirms
      bin-links preserves file content and does not replace it with a symlink.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-004, REQ-012
    """

    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest-bin"
    src_dir.mkdir()
    dest_dir.mkdir()

    (src_dir / "app.sh").write_text("#!/bin/sh\n")
    regular_path = dest_dir / "app"
    regular_path.write_text("keep-me")

    result = bin_links.run([str(src_dir), "--dest", str(dest_dir)])

    assert result == 0
    assert regular_path.exists()
    assert not regular_path.is_symlink()
    assert regular_path.read_text() == "keep-me"


def test_clean_requires_confirmation_without_yes(monkeypatch, tmp_path):
    """
    @brief Validate clean confirmation gate.
    @details Mocks project root detection and user prompt response to ensure
      cache directories are preserved when confirmation is declined.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-004, REQ-013
    """

    cache_dir = tmp_path / "module" / "__pycache__"
    cache_dir.mkdir(parents=True)

    monkeypatch.setattr(clean, "require_project_root", lambda: tmp_path)
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    result = clean.run([])

    assert result == 0
    assert cache_dir.exists()


def test_clean_deletes_discovered_cache_dirs_with_yes(monkeypatch, tmp_path):
    """
    @brief Validate non-interactive cache deletion path.
    @details Mocks project root detection, executes clean with --yes, and
      verifies predefined cache directory names are removed.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-004, REQ-013
    """

    pycache_dir = tmp_path / "module" / "__pycache__"
    pytest_cache_dir = tmp_path / "module" / ".pytest_cache"
    pycache_dir.mkdir(parents=True)
    pytest_cache_dir.mkdir(parents=True)

    monkeypatch.setattr(clean, "require_project_root", lambda: tmp_path)

    result = clean.run(["--yes"])

    assert result == 0
    assert not pycache_dir.exists()
    assert not pytest_cache_dir.exists()
