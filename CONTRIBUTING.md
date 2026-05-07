# Contributing Guide

First off: thank you for considering contributing to copier-shopware-plugin ❤️

This project aims to provide a modern, opinionated, and production-ready foundation for Shopware 6 plugin development using Copier.

## Ways to Contribute

Contributions of all kinds are welcome, including:

- bug reports
- feature requests
- documentation improvements
- CI/CD improvements
- template enhancements
- security fixes
- developer experience improvements

## Before You Start

Please:

1. Search existing issues first.
2. Open an issue for larger changes before implementing them.
3. Keep pull requests focused and small when possible.

## Development Setup

### Requirements

- Docker
- Git
- Python 3.12+ (optional for local development)
- Copier v9+

### Clone the Repository

```bash
git clone https://github.com/leifelralf/copier-shopware-plugin.git
cd copier-shopware-plugin
```

### Build the Docker Image

```bash
docker build -t copier-shopware-plugin .
```

### Run the Template

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  copier-shopware-plugin \
  my-plugin
```

## Project Structure

```text
.
├── copier.yml
├── template/
│   ├── ...
│   └── {{ plugin_name }}/
└── Dockerfile
```

## Style Guidelines

### General

- Prefer readability over cleverness.
- Keep generated output maintainable.
- Avoid unnecessary abstraction.
- Favor explicit configuration.

### Shopware

Generated plugins should:

- follow Shopware best practices
- support modern Shopware versions
- work with PHPStan/Psalm where possible
- be CI-friendly
- support automated testing

### Docker

- Keep images minimal.
- Prefer reproducible builds.
- Avoid unnecessary runtime dependencies.

## Commit Messages

Conventional commits are appreciated, but not strictly required.

Examples:

```text
feat: add phpstan baseline support
fix: resolve docker runtime issue
docs: improve README examples
```

## Pull Request Process

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request.
5. Ensure CI passes.

Please include:

- a clear description
- reasoning behind the change
- screenshots/examples if applicable

## Security

If you discover a security vulnerability, please do not open a public issue.

See:

- SECURITY.md

## Code of Conduct

Be respectful and constructive.

Harassment, discrimination, or toxic behavior will not be tolerated.

## License

By contributing, you agree that your contributions will be licensed under the project's MIT license.
