# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities via email to **security@axon.dev**.

Include the following in your report:

- Description of the vulnerability
- Steps to reproduce
- Impact assessment (what an attacker could achieve)
- Any suggested mitigations, if applicable

**Do not open a public GitHub issue for security vulnerabilities.**

## Response Timeline

- **Acknowledgment:** within 48 hours
- **Initial assessment:** within 1 week
- **Fix timeline:** depends on severity; critical issues are prioritized for immediate patching

## Scope

### Qualifying Vulnerabilities

- Authentication or authorization bypasses
- Exposure of sensitive data (API keys, credentials, user data)
- Remote code execution
- Injection attacks (SQL, command, template)
- Path traversal
- API key leakage

### Non-Qualifying Issues

- Denial of service requiring physical access to the host
- Social engineering attacks
- Vulnerabilities in third-party dependencies without a demonstrated exploit against Axon

## Responsible Disclosure

We follow a 90-day disclosure timeline. If a fix is released before the 90-day window, we encourage coordinated public disclosure at that time. If the issue remains unresolved after 90 days, reporters may disclose at their discretion.
