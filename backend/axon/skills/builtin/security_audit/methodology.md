# Security Audit Methodology

You are performing a comprehensive security audit combining OWASP Top 10 analysis with STRIDE threat modeling across up to 14 phases.

## Confidence Gating

Not all findings are equal. Apply confidence gating to reduce noise:

- **Daily scan mode** (confidence_threshold >= 8): Only report findings with 8/10+ confidence. High precision, low noise. Suitable for CI/CD integration.
- **Comprehensive audit mode** (confidence_threshold >= 2): Report findings with 2/10+ confidence. High recall, more noise. Suitable for quarterly reviews.

For every finding, state your confidence level (1-10) and the evidence supporting it. Never report speculation as fact.

## Hard Exclusions

The following 22 categories are auto-filtered from results to reduce noise:

1. Generic "use HTTPS" advice (unless HTTP is actually detected)
2. Theoretical timing attacks without measurable evidence
3. Missing security headers in development environments
4. Test fixture credentials (clearly marked as test data)
5. Development-only debug endpoints (behind feature flags or env guards)
6. Outdated but unexploitable dependency versions
7. CSRF on GET-only endpoints
8. Missing rate limiting on internal-only APIs
9. X-Powered-By header disclosure (low impact)
10. Cookie without SameSite on same-origin-only cookies
11. Missing Referrer-Policy header (informational only)
12. Feature-Policy/Permissions-Policy on non-applicable features
13. DNS rebinding without demonstrable impact
14. Clickjacking on non-sensitive pages
15. Missing HSTS on localhost
16. Self-signed certificates in development
17. Open redirects to same-domain targets
18. Email enumeration on public registration forms
19. Password complexity rules (subjective, not a vulnerability)
20. Generic "keep dependencies updated" without specific CVE
21. Theoretical race conditions without reproduction steps
22. Missing audit logging on read-only operations

## Phase 0: Stack Detection

Identify the technology stack before diving into vulnerabilities:

- **Languages**: primary and secondary (e.g., TypeScript, Python, Go)
- **Frameworks**: web framework, ORM, testing framework
- **Databases**: primary store, caches, search engines
- **Cloud providers**: hosting, CDN, DNS, email, storage
- **CI/CD systems**: GitHub Actions, GitLab CI, Jenkins, etc.
- **Package managers**: npm, pip, cargo, etc. and their lockfile status
- **Runtime**: Node version, Python version, container base image

This determines which phases are relevant. Skip phases that do not apply to the detected stack.

## Phase 1: Attack Surface Mapping

Enumerate every entry point into the system:

| Entry Point | Type | Auth Required | Input Validation | Risk |
|-------------|------|---------------|-----------------|------|
| {endpoint} | API/Form/Upload/Webhook/CLI/ENV | Yes/No | {description} | {H/M/L} |

Categories:
- **API endpoints**: REST, GraphQL, gRPC, WebSocket
- **Web forms**: login, registration, search, file upload, contact
- **File uploads**: accepted types, size limits, storage location
- **Webhooks**: incoming webhook endpoints, signature validation
- **CLI inputs**: command-line arguments, stdin, configuration files
- **Environment variables**: secrets, configuration, feature flags

For each entry point, document:
- What data it accepts
- What validation exists
- What happens with malformed input
- Who can access it (public, authenticated, admin)

## Phase 2: Secrets Archaeology

Scan for exposed credentials:

1. **Current codebase**: hardcoded API keys, passwords, tokens, connection strings
2. **Git history**: secrets committed and then "removed" (still in history)
3. **Environment files**: .env files committed to repository, .env.example with real values
4. **Configuration files**: database URLs, SMTP credentials, cloud provider keys
5. **Logs and comments**: secrets in log output, credentials in code comments
6. **CI/CD configs**: secrets exposed in build logs, unmasked variables

Pattern detection:
- `AKIA[0-9A-Z]{16}` — AWS access key
- `sk-[a-zA-Z0-9]{48}` — API keys (various services)
- `ghp_[a-zA-Z0-9]{36}` — GitHub personal access token
- `-----BEGIN (RSA |EC )?PRIVATE KEY-----` — private keys
- Base64-encoded strings that decode to credential formats
- High-entropy strings (>4.5 Shannon entropy) in configuration context

## Phase 3: Dependency Supply Chain

Evaluate third-party dependency risk:

1. **Known vulnerabilities**: check all dependencies against CVE databases
2. **Install scripts**: review pre/post-install scripts for suspicious behavior
3. **Lockfile integrity**: verify lockfile exists and is committed
4. **Version pinning**: flag unpinned or wildcard version ranges
5. **Abandoned packages**: check last publish date, maintainer activity
6. **Typosquatting**: verify package names against known typosquat patterns
7. **Dependency depth**: flag deeply nested transitive dependencies

| Package | Version | Latest | CVEs | Last Updated | Risk |
|---------|---------|--------|------|-------------|------|
| {name} | {version} | {latest} | {count} | {date} | {H/M/L} |

## Phase 4: CI/CD Security

Audit the build and deployment pipeline:

1. **Unpinned actions**: GitHub Actions using `@main` or `@v1` instead of SHA pins
2. **Dangerous triggers**: `pull_request_target`, `workflow_dispatch` without input validation
3. **Secret exposure**: secrets printed in build logs, secrets available to fork PRs
4. **Workflow injection**: untrusted input interpolated into `run:` commands
5. **Artifact security**: build artifacts accessible to unauthorized parties
6. **Deployment keys**: overly permissive deployment credentials

## Phase 5: Infrastructure Hardening

Evaluate infrastructure security:

### Container Security
- Running as root (should be non-root user)
- Unnecessary packages installed (attack surface)
- Base image freshness (outdated base = known vulnerabilities)
- Multi-stage builds (build tools not in production image)
- Secrets baked into image layers

### Infrastructure as Code
- Open ports (only expose what is needed)
- Default credentials (databases, admin panels)
- Public S3 buckets or storage
- Overly permissive IAM roles
- Missing encryption at rest

### TLS Configuration
- Certificate validity and expiration
- Protocol versions (TLS 1.2+ only)
- Cipher suite strength
- HSTS configuration

## Phase 6: LLM Vulnerabilities

If the system uses language models, audit AI-specific attack vectors:

1. **Prompt injection**: Can user input manipulate system prompts?
   - Direct injection (user input contains instructions)
   - Indirect injection (fetched content contains instructions)
2. **Output sanitization**: Is LLM output rendered as HTML, executed as code, or used in database queries without sanitization?
3. **Tool call validation**: Are LLM-requested tool calls validated for authorization and parameter bounds?
4. **Context window manipulation**: Can an attacker fill the context window to push out safety instructions?
5. **Data exfiltration**: Can the LLM be tricked into revealing system prompts, user data, or internal APIs?
6. **Model denial of service**: Can crafted inputs cause excessive token usage or infinite loops?

## Phase 7: Skill/Plugin Supply Chain

If the system supports plugins, skills, or extensions:

1. **Untrusted sources**: Are skills loaded from unverified sources?
2. **Permission model**: Do skills have unbounded access or sandboxed permissions?
3. **Code execution**: Can skills execute arbitrary code?
4. **Data access**: Can skills access data from other users or sessions?
5. **Update mechanism**: Can skills auto-update without user approval?

## Phases 8-9: OWASP Top 10

Evaluate against the current OWASP Top 10:

### A01: Broken Access Control
- Bypassing access controls via URL manipulation, API parameter tampering
- CORS misconfiguration allowing unauthorized origins
- Accessing other users' data by modifying identifiers
- Missing function-level access control

### A02: Cryptographic Failures
- Sensitive data transmitted in cleartext
- Weak or deprecated cryptographic algorithms
- Hard-coded or default encryption keys
- Missing encryption for data at rest

### A03: Injection
- SQL injection (string concatenation in queries)
- NoSQL injection (operator injection in MongoDB queries)
- Command injection (user input in shell commands)
- LDAP, XPath, template injection

### A04: Insecure Design
- Missing threat modeling
- No abuse case testing
- Missing rate limiting on sensitive operations
- Business logic flaws

### A05: Security Misconfiguration
- Default configurations unchanged
- Unnecessary features enabled
- Error messages exposing stack traces
- Missing security headers

### A06: Vulnerable and Outdated Components
- Components with known CVEs (cross-reference Phase 3)
- Unsupported or end-of-life frameworks
- Missing patch management process

### A07: Identification and Authentication Failures
- Weak password policies (no minimum entropy)
- Missing brute force protection
- Session fixation or session ID exposure
- Missing MFA on sensitive operations

### A08: Software and Data Integrity Failures
- Deserialization of untrusted data
- Missing integrity verification on updates
- Unsigned or unverified CI/CD artifacts
- Missing Subresource Integrity (SRI) for CDN resources

### A09: Security Logging and Monitoring Failures
- Missing audit logs for authentication events
- Missing logs for authorization failures
- Logs not monitored or alerted
- Log injection vulnerabilities

### A10: Server-Side Request Forgery (SSRF)
- User-controlled URLs fetched by the server
- Internal service access via SSRF
- Cloud metadata endpoint access

## Phase 10: STRIDE Threat Model

For each major component, evaluate six threat categories:

| Component | Spoofing | Tampering | Repudiation | Info Disclosure | DoS | Elevation |
|-----------|----------|-----------|-------------|-----------------|-----|-----------|
| {component} | {risk} | {risk} | {risk} | {risk} | {risk} | {risk} |

For each identified threat:
- **Threat**: Description of the attack
- **Likelihood**: Low / Medium / High
- **Impact**: Low / Medium / High / Critical
- **Current mitigation**: What exists
- **Gap**: What is missing
- **Remediation**: Specific fix

## Finding Format

Every reported finding must include:

| Field | Description |
|-------|-------------|
| ID | Unique identifier (e.g., SEC-001) |
| Title | One-line summary |
| Severity | Critical / High / Medium / Low / Info |
| Confidence | 1-10 |
| Phase | Which audit phase discovered this |
| Description | What the vulnerability is |
| Exploit scenario | How an attacker would exploit this |
| Evidence | Specific file, line, configuration, or pattern |
| Remediation | Step-by-step fix with code examples where applicable |
| Effort | Estimated fix effort (minutes / hours / days) |

## Risk Score Calculation

Calculate overall risk score (0-100, lower is better):

| Severity | Weight per Finding |
|----------|-------------------|
| Critical | +25 |
| High | +15 |
| Medium | +5 |
| Low | +1 |
| Info | +0 |

Cap at 100. Subtract points for existing mitigations:
- WAF in place: -5
- Automated dependency scanning: -5
- Security headers configured: -3
- Rate limiting on auth endpoints: -3
- Audit logging enabled: -2

## Output Structure

```markdown
## Security Audit: {Subject}

**Scope**: {infra/code/supply-chain/owasp/full}
**Confidence threshold**: {N}/10
**Risk score**: {0-100}

### Stack Detection
- **Languages**: {list}
- **Frameworks**: {list}
- **Databases**: {list}
- **Cloud**: {list}
- **CI/CD**: {list}

### Severity Summary
| Severity | Count |
|----------|-------|
| Critical | {n} |
| High | {n} |
| Medium | {n} |
| Low | {n} |
| Info | {n} |

### Findings

#### SEC-{NNN}: {Title}
- **Severity**: {level}
- **Confidence**: {N}/10
- **Phase**: {phase name}
- **Description**: {what}
- **Exploit scenario**: {how an attacker would use this}
- **Evidence**: {file:line or configuration}
- **Remediation**: {step-by-step fix}
- **Effort**: {time estimate}

{Repeat for all findings}

### STRIDE Threat Model
| Component | S | T | R | I | D | E |
|-----------|---|---|---|---|---|---|
| {component} | {risk} | {risk} | {risk} | {risk} | {risk} | {risk} |

### Recommendations
1. {highest priority fix}
2. {second priority fix}
3. {third priority fix}
```
