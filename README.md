# MQP-Dashboard-Backend

[![Documentation](https://img.shields.io/badge/Documentation-Read%20the%20Docs-blue)](https://munich-quantum-software-stack.github.io/MQP-Dashboard-Backend/index.html)

## Overview

The MQP-Dashboard-Backend is a part of MQSS Client. It provides a unified platform for secure user authentication, access token management, and data retrieval from Quantum Database and QDMI proxy telemetry services.

## Getting started

1. Clone this repository
2. Install dependencies and developer tools
```sh
git clone https://github.com/Munich-Quantum-Software-Stack/MQP-Dashboard-Backend.git
cd MQP-Dashboard-Backend
pdm install
```

## Environment Variables

Use `.env.example` as a template for local configuration, then set environment-specific secret values before running project and tests.

### Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

### Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

### License

Licensed under the Apache License v2.0 with LLVM Exceptions.


## Commit Message Guidelines

Examples:
```sh
<short_author_name>/feat: add JWT authentication
<short_author_name>/fix: resolve docker startup issue
<short_author_name>/docs: update API documentation
```

## Pull Request Process

Before submitting a PR:
- Ensure tests pass
- Ensure lint checks pass
- Add tests for new functionality
- Update documentation where needed

PRs should include:
- Summary of changes
- Related issue references
- Screenshots/examples if applicable

### Coding Standards

#### Python
- Follow PEP 8
- Use type hints when possible
- Keep functions focused and testable
- Add docstrings for public APIs

## Reporting Issues

Please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs/screenshots if applicable
