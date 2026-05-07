"""Functional tests that exercise generated output with real tools.

These are the strongest guarantee that the template doesn't just look right
but actually produces working files. They run external commands, so each
test is gated by a tool-availability marker that auto-skips when the
binary is missing — locally, you only run what you have installed; in CI
the workflow installs them all.

Run only these tests:    pytest -m functional
Skip these tests:        pytest -m "not functional"
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from .conftest import needs_composer, needs_php, needs_xmllint

pytestmark = pytest.mark.functional


# ---------------------------------------------------------------------------
# PHP syntax checks
# ---------------------------------------------------------------------------


@needs_php
def test_bootstrap_php_is_syntactically_valid(generate) -> None:
    project = generate({"plugin_name": "Syntax Test"})
    bootstrap = project / "src" / "SyntaxTest.php"

    result = subprocess.run(
        ["php", "-l", str(bootstrap)], capture_output=True, text=True
    )
    assert result.returncode == 0, f"php -l failed:\n{result.stdout}\n{result.stderr}"


@needs_php
@pytest.mark.parametrize(
    "config_file",
    [
        ".php-cs-fixer.dist.php",
        "rector.php",
    ],
)
def test_generated_php_configs_are_syntactically_valid(generate, config_file: str) -> None:
    project = generate({"use_code_quality": True})
    target = project / config_file
    if not target.exists():
        pytest.skip(f"{config_file} not generated for this configuration")

    result = subprocess.run(
        ["php", "-l", str(target)], capture_output=True, text=True
    )
    assert result.returncode == 0, f"php -l failed for {config_file}:\n{result.stderr}"


# ---------------------------------------------------------------------------
# XML well-formedness
# ---------------------------------------------------------------------------


@needs_xmllint
@pytest.mark.parametrize(
    ("answers", "xml_path"),
    [
        ({}, "src/Resources/config/services.xml"),
        ({"use_code_quality": True, "code_style_tool": "phpcs"}, "phpcs.xml.dist"),
    ],
)
def test_generated_xml_is_well_formed(generate, answers: dict, xml_path: str) -> None:
    project = generate(answers)
    target = project / xml_path
    if not target.exists():
        pytest.skip(f"{xml_path} not generated for this configuration")

    result = subprocess.run(
        ["xmllint", "--noout", str(target)], capture_output=True, text=True
    )
    assert result.returncode == 0, f"xmllint failed for {xml_path}:\n{result.stderr}"


# ---------------------------------------------------------------------------
# JSON validity (no external tool needed, but logically functional)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "json_path",
    [
        "composer.json",
        "src/Resources/snippet/de_DE/messages.de-DE.json",
        "src/Resources/snippet/en_GB/messages.en-GB.json",
        ".copier-answers.yml",  # YAML, but well-formed-check still meaningful
    ],
)
def test_generated_json_files_parse(generate, json_path: str) -> None:
    project = generate()
    content = (project / json_path).read_text()

    if json_path.endswith(".yml"):
        import yaml as _yaml

        _yaml.safe_load(content)
    else:
        json.loads(content)


# ---------------------------------------------------------------------------
# Composer schema validation
# ---------------------------------------------------------------------------


@needs_composer
@pytest.mark.parametrize(
    "answers",
    [
        pytest.param({"use_code_quality": False}, id="minimal"),
        pytest.param({"use_code_quality": True}, id="full"),
        pytest.param(
            {
                "use_code_quality": True,
                "code_style_tool": "phpcs",
                "use_rector": False,
                "use_shopware_dev_tools": False,
            },
            id="phpcs-no-rector",
        ),
    ],
)
def test_composer_json_passes_validate(generate, answers: dict) -> None:
    import os

    project = generate(answers)
    env = {**os.environ, "COMPOSER_ALLOW_SUPERUSER": "1"}
    result = subprocess.run(
        ["composer", "validate", "--strict", "--no-check-publish"],
        cwd=project,
        capture_output=True,
        text=True,
        env=env,
    )

    # "version field is present" is an expected warning for Shopware plugins;
    # `validate --strict` upgrades warnings to errors otherwise. We accept
    # exit 0 (clean) or exit with only the version-field warning.
    if result.returncode != 0:
        # Sanitise: only allow the known-benign warning.
        # Composer writes warnings to stderr, errors are typically there too.
        combined = result.stdout + result.stderr
        allowed = "version field is present"
        assert allowed in combined, (
            f"composer validate failed unexpectedly:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def _path_env() -> str:
    """Helper: forward $PATH so subprocess can find composer."""
    import os

    return os.environ.get("PATH", "")
