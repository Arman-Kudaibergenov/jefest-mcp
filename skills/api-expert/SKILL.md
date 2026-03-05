---
name: api-expert
description: >
  This skill MUST be invoked when designing REST/GraphQL APIs or implementing API security.
  Two modes: design (endpoints, REST, resource modeling) and security (auth, JWT, CORS, rate limiting).
  TRIGGER on: "API design", "endpoint", "REST", "resource modeling", "API security", "JWT", "OAuth", "rate limiting", "CORS".
risk: safe
source: personal
date_added: "2026-03-04"
---

# API Expert

## Overview

Unified API expertise covering design principles, security hardening, and production patterns.

**Mode: design** — endpoint structure, REST/GraphQL, versioning, pagination, error formats
**Mode: security** — authentication, authorization, JWT, OAuth, rate limiting, CORS, OWASP API Top 10

---

## MODE: DESIGN

### Core Design Process

1. **Identify consumers** — who uses this API, their use cases, technical constraints
2. **Select style** — REST or GraphQL, model resources/types
3. **Plan cross-cutting concerns** — errors, versioning, pagination, auth
4. **Validate design** — test with concrete examples, verify consistency

### REST Resource Naming
- Use nouns, not verbs: `/users`, not `/getUsers`
- Use plural: `/users/{id}`, not `/user/{id}`
- Nest for relationships: `/users/{id}/posts`
- Keep hierarchy shallow (max 2-3 levels)

### HTTP Methods
| Method | Use | Idempotent |
|--------|-----|------------|
| GET | Read | Yes |
| POST | Create | No |
| PUT | Replace | Yes |
| PATCH | Partial update | No |
| DELETE | Delete | Yes |

### Status Codes
| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Versioning
- URL path: `/api/v1/users` (most common)
- Header: `Accept: application/vnd.api+json;version=1`
- Query param: `/users?version=1` (avoid)

### Pagination
- Cursor-based: `?cursor=abc&limit=20` (preferred for large datasets)
- Offset-based: `?page=2&per_page=20` (simple, predictable)
- Always include `total`, `next`, `prev` in response

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      { "field": "email", "message": "Invalid format" }
    ]
  }
}
```

### GraphQL Design
- Type names: PascalCase (`UserProfile`)
- Fields: camelCase (`firstName`)
- Enums: SCREAMING_SNAKE_CASE (`USER_STATUS`)
- Input types for mutations: `createUser(input: CreateUserInput!)`
- Return mutated object: `createUser { user { id } }`
- Avoid N+1 with DataLoader pattern

### Authentication Method Selection
| Method | Use Case |
|--------|----------|
| JWT Bearer | Stateless, distributed systems |
| API Key | Server-to-server, simple integrations |
| OAuth 2.0 | Third-party access delegation |
| Session Cookie | Web apps with server-side sessions |

### Design Checklist
- [ ] Resources are nouns, not verbs
- [ ] HTTP methods used correctly
- [ ] Status codes meaningful and consistent
- [ ] Error format standardized
- [ ] Versioning strategy defined
- [ ] Pagination implemented for lists
- [ ] Authentication documented
- [ ] Rate limiting documented
- [ ] Breaking vs non-breaking changes defined

---

## MODE: SECURITY

### Step 1: Authentication & Authorization

#### JWT Implementation
```javascript
// Generate JWT
const token = jwt.sign(
  { userId: user.id, email: user.email, role: user.role },
  process.env.JWT_SECRET,
  { expiresIn: '1h', issuer: 'your-app', audience: 'your-app-users' }
);

// Verify middleware
function authenticateToken(req, res, next) {
  const token = req.headers['authorization']?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Access token required' });

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
}
```

#### Authorization Check (always verify both authn + authz)
```javascript
app.delete('/api/posts/:id', authenticateToken, async (req, res) => {
  const post = await prisma.post.findUnique({ where: { id: req.params.id } });
  if (!post) return res.status(404).json({ error: 'Not found' });

  if (post.userId !== req.user.userId && req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Not authorized' });
  }

  await prisma.post.delete({ where: { id: req.params.id } });
  res.json({ success: true });
});
```

### Step 2: Input Validation
```javascript
const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).regex(/[A-Z]/).regex(/[a-z]/).regex(/[0-9]/),
  name: z.string().min(2).max(100)
});

function validateRequest(schema) {
  return (req, res, next) => {
    try {
      schema.parse(req.body);
      next();
    } catch (error) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
  };
}
```

### Step 3: Rate Limiting
```javascript
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  keyGenerator: (req) => req.user?.userId || req.ip
});

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  skipSuccessfulRequests: true
});

app.use('/api/', apiLimiter);
app.use('/api/auth/login', authLimiter);
```

### Do / Don't

**Do:**
- HTTPS everywhere
- Hash passwords with bcrypt (salt rounds >= 10)
- Short-lived JWT access tokens (1h)
- Schema validation for all inputs
- Parameterized queries or ORM
- CORS allowlist (not wildcard)
- Security headers (Helmet.js)
- Log security events (not sensitive data)

**Don't:**
- Store passwords in plain text
- Hardcode secrets
- Expose stack traces in production
- String concatenation for SQL
- Store sensitive data in JWT payload
- Disable CORS completely
- Log passwords or tokens

### OWASP API Top 10
1. **Broken Object Level Authorization** — verify user can access resource
2. **Broken Authentication** — strong auth implementation
3. **Broken Object Property Level Authorization** — validate accessible properties
4. **Unrestricted Resource Consumption** — rate limiting + quotas
5. **Broken Function Level Authorization** — verify role per function
6. **Unrestricted Access to Sensitive Business Flows** — protect critical workflows
7. **Server Side Request Forgery (SSRF)** — validate/sanitize URLs
8. **Security Misconfiguration** — follow security best practices
9. **Improper Inventory Management** — document all endpoints
10. **Unsafe Consumption of APIs** — validate third-party API data

### Security Checklist

**Authentication & Authorization:**
- [ ] Strong authentication (JWT, OAuth 2.0)
- [ ] HTTPS on all endpoints
- [ ] Passwords hashed with bcrypt >= 10 rounds
- [ ] Token expiration set
- [ ] Refresh token mechanism
- [ ] Authorization verified per request
- [ ] RBAC implemented

**Input Validation:**
- [ ] All inputs validated
- [ ] Parameterized queries or ORM
- [ ] HTML content sanitized
- [ ] File uploads validated

**Rate Limiting:**
- [ ] Rate limiting per user/IP
- [ ] Stricter limits for auth endpoints
- [ ] Redis for distributed rate limiting
- [ ] Rate limit headers returned

**Data Protection:**
- [ ] HTTPS/TLS for all traffic
- [ ] Sensitive data encrypted at rest
- [ ] Error messages sanitized
- [ ] CORS configured properly (allowlist)
- [ ] Security headers implemented
