"""
@brief Validate the build-artifact cleanup script structure and behavior.
@details Parses `scripts/clean.sh` and asserts repository-root resolution,
  tracked-entry preservation, intermediate-tree removal, and untracked
  generated `dist` archive removal. Validates Bash syntax via `bash -n` and
  the executable bit required by the documented invocation contract. Behavioral
  probes execute the real script inside an isolated temporary Git repository.
@satisfies TST-019, DES-055, REQ-147
@return {None} Pytest module scope.
"""

import pathlib
import subprocess

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
CLEAN_PATH = PROJECT_ROOT / "scripts" / "clean.sh"


def _read(path: pathlib.Path) -> str:
    """
    @brief Load one tracked script file as UTF-8 text.
    @details Reads the script content for token-level structural assertions.
      Time complexity O(n) over file size.
    @param path {pathlib.Path} Script path to read.
    @return {str} Full script content.
    @throws {OSError} When the script file cannot be read.
    """

    return path.read_text(encoding="utf-8")


def _git(repo: pathlib.Path, *args: str) -> None:
    """
    @brief Run one Git command inside an isolated test repository.
    @details Executes `git -C <repo> <args>` and fails the test on a non-zero
      exit status. Time complexity O(1) excluding Git startup.
    @param repo {pathlib.Path} Repository root for the Git invocation.
    @param args {tuple[str, ...]} Git argument vector after `-C <repo>`.
    @return {None} Assertions only.
    @throws {AssertionError} When the Git command exits non-zero.
    """

    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def _make_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """
    @brief Create an isolated Git repository hosting the clean script.
    @details Copies the tracked `scripts/clean.sh` into `<tmp>/scripts/`,
      initializes a Git repository, and commits the script so root resolution
      and tracked-state queries operate on a real repository. Time complexity
      O(1).
    @param tmp_path {pathlib.Path} Pytest temporary directory.
    @return {pathlib.Path} Repository root containing the clean script.
    """

    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "clean.sh").write_bytes(CLEAN_PATH.read_bytes())
    _git(repo, "init")
    _git(repo, "add", "scripts/clean.sh")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test",
         "commit", "-q", "-m", "init")
    return repo


def _run_clean(repo: pathlib.Path) -> subprocess.CompletedProcess:
    """
    @brief Execute the clean script against one isolated repository.
    @details Invokes `bash scripts/clean.sh` from the repository root and
      captures the completed process for assertion. Time complexity O(1)
      excluding script execution.
    @param repo {pathlib.Path} Repository root hosting the script.
    @return {subprocess.CompletedProcess} Completed script invocation.
    """

    return subprocess.run(
        ["bash", "scripts/clean.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_clean_script_exists_and_is_executable():
    """
    @brief Validate clean script presence and executable permission.
    @details Asserts the script exists at its required path, contains
      non-empty content, and carries the executable bit required by the
      documented invocation contract.
    @return {None} Assertions only.
    @satisfies TST-019, DES-055
    """

    assert CLEAN_PATH.is_file()
    assert _read(CLEAN_PATH).strip()
    assert CLEAN_PATH.stat().st_mode & 0o111


def test_clean_script_passes_bash_syntax_check():
    """
    @brief Validate Bash syntax of the clean script.
    @details Executes `bash -n` and passes only when the parser reports no
      syntax errors and a zero exit status.
    @return {None} Assertions only.
    @satisfies TST-019, DES-055
    """

    result = subprocess.run(
        ["bash", "-n", str(CLEAN_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_clean_script_structure_matches_contract():
    """
    @brief Validate structural tokens of the cleanup pipeline.
    @details Asserts the script resolves the Git repository root, changes into
      it, guards tracked intermediate-tree entries, enumerates untracked
      generated `dist` archives, and prints one `clean` evidence line.
    @return {None} Assertions only.
    @satisfies TST-019, DES-055, REQ-147
    """

    content = _read(CLEAN_PATH)
    assert "rev-parse --show-toplevel" in content
    assert "resolve_project_root" in content
    assert "remove_intermediate_build_trees" in content
    assert "remove_untracked_dist_archives" in content
    assert "clean_build_artifacts" in content
    assert "git ls-files -- build src/shellscripts.egg-info" in content
    assert "${DIST_DIR}\"/*.tar.gz" in content
    assert "${DIST_DIR}\"/*.whl" in content
    assert "clean: build src/shellscripts.egg-info dist:untracked-archives" in content


def test_clean_script_removes_untracked_artifacts_and_preserves_tracked(tmp_path):
    """
    @brief Validate untracked artifact removal and tracked preservation.
    @details Builds an isolated repository with one tracked dist archive, one
      untracked dist archive, a non-generated tracked dist file, and the
      intermediate build trees; executes the clean script; and asserts that
      untracked artifacts are removed while tracked entries survive.
    @param tmp_path {pathlib.Path} Pytest temporary directory.
    @return {None} Assertions only.
    @satisfies TST-019, DES-055, REQ-147
    """

    repo = _make_repo(tmp_path)
    dist_dir = repo / "dist"
    dist_dir.mkdir()
    tracked_archive = dist_dir / "shellscripts-0.26.0.tar.gz"
    untracked_archive = dist_dir / "shellscripts-9.9.9.tar.gz"
    tracked_doc = dist_dir / "RELEASE-NOTES.md"
    tracked_archive.write_bytes(b"tracked-archive")
    untracked_archive.write_bytes(b"untracked-archive")
    tracked_doc.write_text("notes", encoding="utf-8")
    (repo / "build").mkdir()
    (repo / "build" / "lib.tmp").write_text("x", encoding="utf-8")
    (repo / "src").mkdir()
    egg_info = repo / "src" / "shellscripts.egg-info"
    egg_info.mkdir()
    (egg_info / "PKG-INFO").write_text("x", encoding="utf-8")
    _git(repo, "add", "dist/shellscripts-0.26.0.tar.gz", "dist/RELEASE-NOTES.md")

    result = _run_clean(repo)

    assert result.returncode == 0, result.stderr
    assert "clean: build src/shellscripts.egg-info dist:untracked-archives" in result.stdout
    assert tracked_archive.is_file()
    assert tracked_doc.is_file()
    assert not untracked_archive.exists()
    assert not (repo / "build").exists()
    assert not egg_info.exists()


def test_clean_script_refuses_tracked_intermediate_tree(tmp_path):
    """
    @brief Validate refusal when a tracked file blocks intermediate removal.
    @details Builds an isolated repository with one tracked file inside
      `build/`, executes the clean script, and asserts a non-zero exit with an
      error naming the tracked entry and no deletion of the tracked tree.
    @param tmp_path {pathlib.Path} Pytest temporary directory.
    @return {None} Assertions only.
    @satisfies TST-019, DES-055, REQ-147
    """

    repo = _make_repo(tmp_path)
    (repo / "build").mkdir()
    tracked_file = repo / "build" / "tracked.txt"
    tracked_file.write_text("x", encoding="utf-8")
    _git(repo, "add", "build/tracked.txt")

    result = _run_clean(repo)

    assert result.returncode == 1
    assert "Tracked files exist under removable build paths" in result.stderr
    assert tracked_file.is_file()
