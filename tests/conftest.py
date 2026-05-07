"""Shared pytest fixtures and helpers.

The fixtures here let individual test files focus on assertions instead
of orchestrating Copier invocations and tempdir cleanup.
"""
from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

import pytest
import yaml

# Locate the template root relative to this file (tests/conftest.py is one
# level inside the template repository).
TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
COPIER_YML = TEMPLATE_ROOT / "copier.yml"

# Sensible answer set used as a baseline. Individual tests override
# specific keys via the `generate` fixture's `answers` argument.
DEFAULT_ANSWERS: dict[str, object] = {
    "vendor_name": "AcmeCorp",
    "plugin_name": "Example Plugin",
    "plugin_description": "A Shopware 6 plugin",
    "author_name": "Jane Doe",
    "author_email": "jane@example.com",
    "author_github": "janedoe",
    "plugin_version": "0.1.0",
    "min_shopware_version": "~6.7.0",
    "php_version": "8.2",
    "license": "MIT",
    "use_code_quality": True,
    "phpstan_level": "8",
    "use_shopware_dev_tools": True,
    "code_style_tool": "php-cs-fixer",
    "use_rector": True,
}


def _run_copier(dst: Path, answers: dict[str, object]) -> subprocess.CompletedProcess:
    """Invoke Copier as a subprocess.

    We shell out instead of using copier's Python API because the API has
    moved several times across versions; the CLI is the stable surface.
    """
    cmd = [
        "copier",
        "copy",
        "--defaults",
        "--trust",
        "--quiet",
        "--vcs-ref=HEAD",
    ]
    for key, value in answers.items():
        if isinstance(value, bool):
            value = "true" if value else "false"
        cmd.extend(["--data", f"{key}={value}"])
    cmd.extend([str(TEMPLATE_ROOT), str(dst)])
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


@pytest.fixture
def generate(tmp_path: Path) -> Callable[..., Path]:
    """Return a function that generates a project with the given answers.

    Each call gets its own subdirectory so a single test can generate
    multiple projects (e.g. for cross-comparing two configurations).

    Usage:
        def test_something(generate):
            project = generate({"plugin_name": "MyPlugin"})
            assert (project / "composer.json").exists()
    """
    counter = {"n": 0}

    def _generate(overrides: dict[str, object] | None = None) -> Path:
        answers = {**DEFAULT_ANSWERS, **(overrides or {})}
        counter["n"] += 1
        dst = tmp_path / f"project-{counter['n']}"
        result = _run_copier(dst, answers)
        if result.returncode != 0:
            pytest.fail(
                f"copier failed (exit {result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return dst

    return _generate


@pytest.fixture
def generate_expecting_failure(tmp_path: Path) -> Callable[..., subprocess.CompletedProcess]:
    """Like `generate`, but for cases where Copier should reject the input.

    Returns the CompletedProcess so the caller can inspect stderr for the
    expected validation message.
    """
    counter = {"n": 0}

    def _generate(overrides: dict[str, object] | None = None) -> subprocess.CompletedProcess:
        answers = {**DEFAULT_ANSWERS, **(overrides or {})}
        counter["n"] += 1
        dst = tmp_path / f"project-{counter['n']}"
        return _run_copier(dst, answers)

    return _generate


# ---------------------------------------------------------------------------
# Helpers used by snapshot tests
# ---------------------------------------------------------------------------


def list_files(root: Path) -> list[str]:
    """Return all files under `root` as POSIX-style paths, sorted.

    Excludes the answers file because it embeds an absolute path
    (`_src_path`) that varies between machines.
    """
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p.name != ".copier-answers.yml"
    )


def file_tree_snapshot(root: Path) -> str:
    """Render a stable, human-readable file listing for snapshotting."""
    return "\n".join(list_files(root)) + "\n"


def read_text_files(root: Path, paths: Iterable[str]) -> dict[str, str]:
    """Read multiple files, returning {path: content}.

    Useful for snapshotting a curated set of files without polluting
    snapshots with binary blobs or huge generated content.
    """
    return {p: (root / p).read_text() for p in paths}


# ---------------------------------------------------------------------------
# Tool availability detection (used by functional tests)
# ---------------------------------------------------------------------------


def _has_tool(name: str) -> bool:
    return shutil.which(name) is not None


HAS_PHP = _has_tool("php")
HAS_COMPOSER = _has_tool("composer")
HAS_XMLLINT = _has_tool("xmllint")


# Module-level skip markers. Imported by individual functional tests so each
# test can declare exactly which tools it depends on.
needs_php = pytest.mark.skipif(not HAS_PHP, reason="php not installed")
needs_composer = pytest.mark.skipif(not HAS_COMPOSER, reason="composer not installed")
needs_xmllint = pytest.mark.skipif(not HAS_XMLLINT, reason="xmllint not installed")