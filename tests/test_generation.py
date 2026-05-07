"""Tests for which files are generated under different answer combinations.

Two flavours:
1.  Logic assertions — "if X is yes, file Y must exist; if X is no, it must
    not". These are the contract tests; they fail loudly when conditional
    filenames break.
2.  Snapshot tests — pin down the content of generated files for a few
    canonical configurations. Run with `pytest --snapshot-update` to
    regenerate snapshots after intentional changes.
"""
from __future__ import annotations

import json

import pytest

from .conftest import file_tree_snapshot, list_files


# ---------------------------------------------------------------------------
# Core: files that must always exist regardless of toggles
# ---------------------------------------------------------------------------

CORE_FILES = [
    "composer.json",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    ".gitignore",
    ".editorconfig",
    "src/Resources/config/services.xml",
    "src/Resources/snippet/de_DE/messages.de-DE.json",
    "src/Resources/snippet/en_GB/messages.en-GB.json",
]


def test_core_files_always_generated(generate) -> None:
    """Even with every optional component disabled, the Core scaffold remains."""
    project = generate({"use_code_quality": False})
    files = set(list_files(project))
    for expected in CORE_FILES:
        assert expected in files, f"Missing core file: {expected}"


def test_bootstrap_class_uses_plugin_class_name(generate) -> None:
    project = generate({"plugin_name": "Cool Widget"})
    bootstrap = project / "src" / "CoolWidget.php"
    assert bootstrap.exists()
    content = bootstrap.read_text()
    assert "class CoolWidget extends Plugin" in content
    assert "namespace AcmeCorp\\CoolWidget;" in content


def test_composer_metadata_reflects_answers(generate) -> None:
    project = generate(
        {
            "vendor_name": "Webartistry",
            "plugin_name": "Product Highlights",
            "plugin_description": "Highlight specific products on category pages",
            "license": "Apache-2.0",
            "min_shopware_version": "~6.7.0",
            "php_version": "8.3",
        }
    )
    data = json.loads((project / "composer.json").read_text())

    assert data["name"] == "webartistry/product-highlights"
    assert data["description"] == "Highlight specific products on category pages"
    assert data["license"] == "Apache-2.0"
    assert data["require"]["php"] == "^8.3"
    # The constraint passes through unchanged — the template no longer prepends `~`.
    assert data["require"]["shopware/core"] == "~6.7.0"
    assert data["extra"]["shopware-plugin-class"] == (
        "Webartistry\\ProductHighlights\\ProductHighlights"
    )


@pytest.mark.parametrize(
    "constraint",
    [
        "~6.7.0",
        "^6.7",
        "6.7.*",
        ">=6.7,<7.0",
        "6.7.0.0",
    ],
)
def test_shopware_constraint_passes_through_verbatim(generate, constraint: str) -> None:
    """The template must not mangle the user's Composer constraint.

    Whatever the user typed should appear unchanged in `composer.json`.
    Composer itself validates the syntax at install time; our job is to not
    add or remove characters silently.
    """
    project = generate({"min_shopware_version": constraint})
    data = json.loads((project / "composer.json").read_text())
    assert data["require"]["shopware/core"] == constraint


# ---------------------------------------------------------------------------
# Code Quality master toggle: skipping behaviour
# ---------------------------------------------------------------------------


def test_code_quality_disabled_skips_all_quality_files(generate) -> None:
    project = generate({"use_code_quality": False})
    files = set(list_files(project))

    assert "phpstan.neon" not in files
    assert ".php-cs-fixer.dist.php" not in files
    assert "phpcs.xml.dist" not in files
    assert "rector.php" not in files


def test_code_quality_disabled_strips_composer_dev_section(generate) -> None:
    project = generate({"use_code_quality": False})
    data = json.loads((project / "composer.json").read_text())
    assert "require-dev" not in data
    assert "scripts" not in data
    assert "config" not in data


def test_code_quality_disabled_omits_subquestions_from_answers(generate) -> None:
    """Sub-questions must be skipped, not just hidden — they should not appear
    in .copier-answers.yml at all. This is what enables future updates to ask
    them fresh if the user enables the master toggle later.
    """
    import yaml as _yaml

    project = generate({"use_code_quality": False})
    answers = _yaml.safe_load((project / ".copier-answers.yml").read_text())

    assert answers["use_code_quality"] is False
    assert "phpstan_level" not in answers
    assert "code_style_tool" not in answers
    assert "use_rector" not in answers
    assert "use_shopware_dev_tools" not in answers


# ---------------------------------------------------------------------------
# Code Quality enabled: file matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("style_tool", "expected_file", "forbidden_file"),
    [
        ("php-cs-fixer", ".php-cs-fixer.dist.php", "phpcs.xml.dist"),
        ("phpcs", "phpcs.xml.dist", ".php-cs-fixer.dist.php"),
    ],
)
def test_code_style_tool_generates_correct_config(
    generate, style_tool: str, expected_file: str, forbidden_file: str
) -> None:
    project = generate({"use_code_quality": True, "code_style_tool": style_tool})
    files = set(list_files(project))
    assert expected_file in files
    assert forbidden_file not in files


@pytest.mark.parametrize("use_rector", [True, False])
def test_rector_toggle(generate, use_rector: bool) -> None:
    project = generate({"use_code_quality": True, "use_rector": use_rector})
    rector_present = "rector.php" in set(list_files(project))
    assert rector_present == use_rector


def test_phpstan_level_propagates(generate) -> None:
    project = generate({"use_code_quality": True, "phpstan_level": "max"})
    content = (project / "phpstan.neon").read_text()
    assert "level: max" in content


def test_shopware_dev_tools_toggle_changes_phpstan_includes(generate) -> None:
    with_tools = generate({"use_code_quality": True, "use_shopware_dev_tools": True})
    without_tools = generate({"use_code_quality": True, "use_shopware_dev_tools": False})

    with_content = (with_tools / "phpstan.neon").read_text()
    without_content = (without_tools / "phpstan.neon").read_text()

    assert "shopware/dev-tools/phpstan/extension.neon" in with_content
    assert "shopware/dev-tools/phpstan/extension.neon" not in without_content


def test_code_quality_adds_composer_scripts(generate) -> None:
    project = generate({"use_code_quality": True})
    data = json.loads((project / "composer.json").read_text())
    assert "scripts" in data
    assert "lint" in data["scripts"]
    assert "lint:fix" in data["scripts"]
    assert "phpstan" in data["scripts"]


def test_code_quality_dev_deps_match_choices(generate) -> None:
    project = generate(
        {
            "use_code_quality": True,
            "code_style_tool": "phpcs",
            "use_rector": False,
            "use_shopware_dev_tools": False,
        }
    )
    data = json.loads((project / "composer.json").read_text())
    deps = data.get("require-dev", {})

    assert "phpstan/phpstan" in deps
    assert "squizlabs/php_codesniffer" in deps
    assert "friendsofphp/php-cs-fixer" not in deps
    assert "rector/rector" not in deps
    assert "shopware/dev-tools" not in deps


# ---------------------------------------------------------------------------
# License switching
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("license_choice", "fingerprint"),
    [
        ("MIT", "MIT License"),
        ("Apache-2.0", "Apache License"),
        ("GPL-3.0-or-later", "GNU General Public License"),
        ("proprietary", "All rights reserved"),
    ],
)
def test_license_content(generate, license_choice: str, fingerprint: str) -> None:
    project = generate({"license": license_choice})
    license_text = (project / "LICENSE").read_text()
    assert fingerprint in license_text


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------


@pytest.mark.snapshot
def test_file_tree_minimal_snapshot(generate, snapshot) -> None:
    """Minimal config: no Code Quality. Pins down the bare Core scaffold."""
    project = generate({"use_code_quality": False})
    assert file_tree_snapshot(project) == snapshot


@pytest.mark.snapshot
def test_file_tree_full_snapshot(generate, snapshot) -> None:
    """Maximal config: every toggle on, php-cs-fixer style."""
    project = generate(
        {
            "use_code_quality": True,
            "phpstan_level": "8",
            "use_shopware_dev_tools": True,
            "code_style_tool": "php-cs-fixer",
            "use_rector": True,
        }
    )
    assert file_tree_snapshot(project) == snapshot


@pytest.mark.snapshot
def test_file_tree_phpcs_no_rector_snapshot(generate, snapshot) -> None:
    project = generate(
        {
            "use_code_quality": True,
            "code_style_tool": "phpcs",
            "use_rector": False,
            "use_shopware_dev_tools": False,
        }
    )
    assert file_tree_snapshot(project) == snapshot


@pytest.mark.snapshot
def test_bootstrap_class_snapshot(generate, snapshot) -> None:
    project = generate()
    assert (project / "src" / "ExamplePlugin.php").read_text() == snapshot


@pytest.mark.snapshot
def test_phpstan_neon_snapshot(generate, snapshot) -> None:
    project = generate({"use_code_quality": True, "phpstan_level": "max"})
    assert (project / "phpstan.neon").read_text() == snapshot