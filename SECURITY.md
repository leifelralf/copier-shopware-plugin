# Security Policy

Thank you for helping make copier-shopware-plugin more secure.

## Supported Versions

Currently, only the latest release series is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| v0.1.x  | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

Please do **not** report security vulnerabilities through public GitHub issues.

Instead, report vulnerabilities privately via:

- GitHub Security Advisories
- or email: ralf@leifel.de

Please include:

- a clear description of the issue
- reproduction steps or a proof of concept
- potential impact
- affected versions

## What to Expect

After a report is submitted:

1. You will receive an acknowledgment within a reasonable timeframe.
2. The issue will be investigated and validated.
3. A fix will be prepared as quickly as possible.
4. A new release will be published if necessary.

## Scope

This project primarily consists of:

- Copier templates
- generated project scaffolding
- Docker-based tooling

Please note:

- Generated projects may require additional hardening depending on deployment context.
- Users are responsible for securely configuring secrets, credentials, CI/CD pipelines, and infrastructure.

## Dependency Security

Dependencies are regularly updated through:

- Dependabot
- container base image updates
- manual maintenance

## Disclosure Policy

Please allow reasonable time for remediation before public disclosure.
