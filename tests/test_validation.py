"""Tests for `copier.yml` validators.

Each test feeds intentionally bad input and asserts that Copier exits
non-zero with the expected error message in stderr.
"""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_substring"),
    [
        # PHP class names must be StudlyCaps
        ("vendor_namespace", "lowercase", "must be a valid PHP class name in StudlyCaps"),
        ("vendor_namespace", "Has Spaces", "must be a valid PHP class name in StudlyCaps"),
        ("vendor_namespace", "1StartsWithDigit", "must be a valid PHP class name in StudlyCaps"),
        ("plugin_class", "lower_case", "must be a valid PHP class name in StudlyCaps"),
        ("plugin_class", "kebab-case", "must be a valid PHP class name in StudlyCaps"),
        # Composer name must be vendor/package, lowercase
        ("composer_name", "no-slash", "must follow vendor/package format"),
        ("composer_name", "UPPER/CASE", "must follow vendor/package format"),
        ("composer_name", "vendor/", "must follow vendor/package format"),
        # Email format
        ("author_email", "not-an-email", "is not a valid email address"),
        ("author_email", "missing@dot", "is not a valid email address"),
        # Semver
        ("plugin_version", "1.0", "must follow semantic versioning"),
        ("plugin_version", "v1.0.0", "must follow semantic versioning"),
        ("plugin_version", "latest", "must follow semantic versioning"),
        # Shopware version constraint — must reference 6.x with valid Composer syntax
        ("min_shopware_version", "5.7.0", "Use Composer constraint syntax"),
        ("min_shopware_version", "5.7.0.0", "Use Composer constraint syntax"),
        ("min_shopware_version", "latest", "Use Composer constraint syntax"),
        ("min_shopware_version", "v6.7.0", "Use Composer constraint syntax"),
        ("min_shopware_version", "~6.7.0 garbage", "Use Composer constraint syntax"),
    ],
)
def test_validator_rejects_bad_input(
    generate_expecting_failure, field: str, bad_value: str, expected_substring: str
) -> None:
    result = generate_expecting_failure({field: bad_value})

    assert result.returncode != 0, (
        f"Expected validation failure for {field}={bad_value!r}, but copier succeeded.\n"
        f"stdout:\n{result.stdout}"
    )
    assert expected_substring in result.stderr, (
        f"Expected error message containing {expected_substring!r}, "
        f"got stderr:\n{result.stderr}"
    )


@pytest.mark.parametrize(
    ("field", "good_value"),
    [
        ("vendor_namespace", "AcmeCorp"),
        ("vendor_namespace", "WebArtistry"),
        ("plugin_class", "MyPlugin"),
        ("plugin_class", "Plugin42"),
        ("composer_name", "acmecorp/my-plugin"),
        ("composer_name", "vendor.with-dots/package_with_underscores"),
        ("author_email", "user@example.com"),
        ("author_email", "user.name+tag@sub.example.co.uk"),
        ("plugin_version", "0.1.0"),
        ("plugin_version", "10.20.30"),
        ("plugin_version", "1.0.0-rc.1"),
        # Shopware version constraints — exact, tilde, caret, range, wildcard
        ("min_shopware_version", "6.7.0.0"),
        ("min_shopware_version", "6.7"),
        ("min_shopware_version", "~6.7.0"),
        ("min_shopware_version", "~6.6.10.4"),
        ("min_shopware_version", "^6.7"),
        ("min_shopware_version", "^6.7.0"),
        ("min_shopware_version", "6.7.*"),
        ("min_shopware_version", ">=6.7"),
        ("min_shopware_version", ">=6.7.0"),
        ("min_shopware_version", ">=6.6,<7.0"),
        ("min_shopware_version", ">=6.6.0,<7.0.0"),
    ],
)
def test_validator_accepts_good_input(generate, field: str, good_value: str) -> None:
    """Sanity check the positive path — without these, false positives in the
    rejection tests would go unnoticed.
    """
    project = generate({field: good_value})
    assert (project / "composer.json").exists()