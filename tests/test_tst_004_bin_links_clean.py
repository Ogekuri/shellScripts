"""
@brief Validate clean command behaviors.
@details Verifies clean confirmation gates for cache-directory deletion.
@satisfies TST-004, REQ-013
@return {None} Pytest module scope.
"""

import shell_scripts.commands.clean as clean


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
