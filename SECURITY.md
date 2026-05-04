# Security Policy

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Use **GitHub's private vulnerability reporting**:
<https://github.com/AntColony10086/echobox/security/advisories/new>

We will acknowledge within 5 business days and aim to provide a fix within 30 days for high-severity issues.

## Supported Versions

echobox is in pre-alpha. Only the `main` branch is currently supported. Once we tag `v1.0.0`, we will document a support matrix here.

## Scope

In scope:
- The Python packages in `packages/`
- The frontend in `frontend/`
- Default deployment configurations

Out of scope (file with upstream):
- Vulnerabilities in vendored GECO2 (`packages/ml_backend/src/echobox_ml/geco2_vendor/`) — report to <https://github.com/jerpelhan/GECO2>
- Vulnerabilities in Python deps — report to PyPI / project maintainers
