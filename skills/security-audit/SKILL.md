---
name: security-audit
description: >
  This skill MUST be invoked when user says "security audit", "vulnerability scan", "pentest", "security review".
  SHOULD also invoke when reviewing code for OWASP vulnerabilities or hardening applications.
category: workflow-bundle
risk: safe
source: personal
date_added: "2026-02-27"
---

# Security Auditing Workflow Bundle

## Overview

Comprehensive security auditing workflow for web applications, APIs, and infrastructure. Orchestrates skills for penetration testing, vulnerability assessment, security scanning, and remediation.

## When to Use This Workflow

- Performing security audits on web applications
- Testing API security
- Conducting penetration tests
- Scanning for vulnerabilities
- Hardening application security
- Compliance security assessments

## Workflow Phases

### Phase 1: Reconnaissance

#### Actions
1. Identify target scope
2. Gather intelligence
3. Map attack surface
4. Identify technologies
5. Document findings

```bash
# Technology fingerprinting
curl -I https://target.com

# DNS enumeration
nslookup target.com
dig target.com ANY

# Port scanning (with permission)
nmap -sV -sC -p- target.com
```

### Phase 2: Vulnerability Scanning

#### Actions
1. Run automated scanners
2. Perform static analysis (SAST)
3. Scan dependencies for CVEs
4. Identify misconfigurations
5. Document vulnerabilities

```bash
# Dependency audit
npm audit
pip-audit
bundle audit

# SAST tools
semgrep --config=auto ./src
bandit -r ./src  # Python
```

### Phase 3: Web Application Testing

#### OWASP Top 10 Tests

| Vulnerability | Test Method |
|---------------|-------------|
| SQL Injection | `' OR '1'='1`, parameterized query bypass |
| XSS | `<script>alert(1)</script>` in all inputs |
| CSRF | Check for CSRF tokens on state-changing requests |
| XXE | XML input with `<!ENTITY xxe SYSTEM "file:///etc/passwd">` |
| Broken Auth | Session fixation, brute force, credential stuffing |
| IDOR | Increment/change resource IDs in requests |
| Security Misconfig | Check headers, default credentials, error verbosity |
| Path Traversal | `../../etc/passwd` in file path parameters |

#### Security Headers Check
```bash
curl -I https://target.com | grep -i "x-frame\|x-content\|strict-transport\|content-security\|x-xss"

# Expected headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy: default-src 'self'
# X-XSS-Protection: 1; mode=block
```

### Phase 4: API Security Testing

#### Actions
1. Enumerate API endpoints
2. Test authentication/authorization
3. Test rate limiting
4. Test input validation
5. Test error handling

```bash
# Test auth bypass
curl -H "Authorization: Bearer invalid" https://api.target.com/users

# Test IDOR
curl -H "Authorization: Bearer $TOKEN" https://api.target.com/users/1  # try other IDs
curl -H "Authorization: Bearer $TOKEN" https://api.target.com/users/2

# Test rate limiting
for i in {1..20}; do curl https://api.target.com/auth/login -d '{"email":"x","password":"x"}'; done

# Test mass assignment
curl -X PATCH https://api.target.com/users/me \
  -d '{"role":"admin","isVerified":true}'
```

### Phase 5: Penetration Testing

#### Methodology

1. **Planning** — Define scope, rules of engagement, success criteria
2. **Reconnaissance** — Passive + active information gathering
3. **Scanning** — Automated vulnerability detection
4. **Exploitation** — Controlled exploitation of findings
5. **Post-exploitation** — Assess impact, privilege escalation
6. **Reporting** — Document findings, CVSS scores, remediation

#### CVSS Scoring Reference
| Score | Severity |
|-------|----------|
| 9.0-10.0 | Critical |
| 7.0-8.9 | High |
| 4.0-6.9 | Medium |
| 0.1-3.9 | Low |

### Phase 6: Security Hardening

#### Actions
1. Implement security controls
2. Configure security headers
3. Set up authentication
4. Implement authorization
5. Configure logging
6. Apply patches

```nginx
# Nginx security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
server_tokens off;
```

### Phase 7: Reporting

#### Report Structure
1. Executive summary (risk level, top findings)
2. Scope and methodology
3. Findings (ordered by severity)
   - Description
   - Proof of concept
   - CVSS score
   - Remediation steps
4. Remediation roadmap

## Security Testing Checklist

### OWASP Top 10
- [ ] Injection (SQL, NoSQL, OS, LDAP)
- [ ] Broken Authentication
- [ ] Sensitive Data Exposure
- [ ] XML External Entities (XXE)
- [ ] Broken Access Control
- [ ] Security Misconfiguration
- [ ] Cross-Site Scripting (XSS)
- [ ] Insecure Deserialization
- [ ] Using Components with Known Vulnerabilities
- [ ] Insufficient Logging & Monitoring

### API Security
- [ ] Authentication mechanisms tested
- [ ] Authorization (IDOR) checked
- [ ] Rate limiting verified
- [ ] Input validation tested
- [ ] Error handling reviewed (no info leakage)
- [ ] Security headers present

### Infrastructure
- [ ] TLS configuration (no SSLv3, TLS 1.0)
- [ ] Open ports minimized
- [ ] Default credentials changed
- [ ] Unnecessary services disabled
- [ ] Patch level current

## Quality Gates

- [ ] All planned tests executed
- [ ] Vulnerabilities documented with PoC
- [ ] Risk assessments completed (CVSS)
- [ ] Remediation steps provided
- [ ] Report generated

## Related Skills

- `api-security-best-practices` - API security implementation
- `postgresql-best-practices` - Database security
