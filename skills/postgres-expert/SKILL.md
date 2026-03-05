---
name: postgres-expert
description: >
  This skill MUST be invoked when user says "postgres", "postgresql", "SQL", "database performance",
  "slow query", "query tuning", "index", "EXPLAIN ANALYZE", "schema design".
  Two modes: design (schema, patterns) and optimize (query tuning, EXPLAIN ANALYZE).
risk: safe
source: personal
date_added: "2026-03-04"
---

# PostgreSQL Expert

## Overview

Unified PostgreSQL expertise covering schema design, query patterns, performance analysis, and production tuning.

**Mode: design** — schema design, data types, constraints, query patterns, connection management
**Mode: optimize** — slow query diagnosis, EXPLAIN ANALYZE, index strategy, configuration tuning

---

## MODE: DESIGN

### Data Types
| Situation | Type |
|-----------|------|
| IDs | `BIGSERIAL` or `UUID` |
| Money | `NUMERIC(12,2)` not `FLOAT` |
| Timestamps | `TIMESTAMPTZ` (with timezone) |
| Short strings | `VARCHAR(n)` |
| Long text | `TEXT` |
| Flags | `BOOLEAN` |
| JSON data | `JSONB` (not `JSON`) |

### Schema Design

#### Foreign Keys and Constraints
```sql
CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'paid', 'cancelled')),
  total NUMERIC(12,2) NOT NULL CHECK (total >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### JSONB Best Practices
```sql
-- Index JSONB fields you query
CREATE INDEX idx_metadata_type ON events USING GIN(metadata);
-- Indexed JSONB path query
CREATE INDEX idx_event_type ON events ((metadata->>'event_type'));
SELECT * FROM events WHERE metadata->>'event_type' = 'purchase';
```

### Query Patterns

#### Avoid SELECT *
```sql
-- Bad
SELECT * FROM users WHERE id = 1;
-- Good
SELECT id, email, name FROM users WHERE id = 1;
```

#### Avoid N+1 Queries
```sql
-- Bad: separate query per user
SELECT * FROM users;
-- then for each user: SELECT * FROM orders WHERE user_id = ?

-- Good: single JOIN
SELECT u.id, u.name, o.id as order_id, o.total
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;
```

#### Use CTEs for Readability
```sql
WITH recent_orders AS (
  SELECT user_id, COUNT(*) as order_count
  FROM orders
  WHERE created_at > NOW() - INTERVAL '30 days'
  GROUP BY user_id
)
SELECT u.name, r.order_count
FROM users u
JOIN recent_orders r ON r.user_id = u.id;
```

#### Cursor-Based Pagination
```sql
-- Bad: OFFSET becomes slow at large pages
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 10000;
-- Good: cursor-based
SELECT * FROM orders WHERE id > :last_id ORDER BY id LIMIT 20;
```

#### UPSERT
```sql
INSERT INTO user_stats (user_id, login_count)
VALUES ($1, 1)
ON CONFLICT (user_id)
DO UPDATE SET login_count = user_stats.login_count + 1;
```

### Connection Management

#### PgBouncer
```
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```
- Default max_connections = 100 (often too low)
- Each connection uses ~5-10MB RAM

#### Connection String
```
postgresql://user:pass@host:5432/db?connect_timeout=10&sslmode=require
```

### Design Checklist
- [ ] TIMESTAMPTZ for all timestamps
- [ ] JSONB not JSON
- [ ] Indexes on all foreign keys
- [ ] CHECK constraints on enums/ranges
- [ ] No SELECT * in production queries
- [ ] Cursor-based pagination for large datasets
- [ ] Connection pooling configured

---

## MODE: OPTIMIZE

### Phase 1: Identify Slow Queries
```sql
-- Requires pg_stat_statements extension
SELECT query, calls, total_exec_time/calls AS avg_ms, rows/calls AS avg_rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Check table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;
```

### Phase 2: EXPLAIN ANALYZE
```sql
-- Full analysis with buffers
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT ...;

-- Check for sequential scans on large tables
SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch
FROM pg_stat_user_tables
WHERE seq_scan > 100
ORDER BY seq_tup_read DESC;
```

#### Scan Type Reference
| Scan Type | Meaning | Action |
|-----------|---------|--------|
| Seq Scan | Full table scan | Add index if table is large |
| Index Scan | Using index | Good |
| Index Only Scan | Covering index | Best |
| Bitmap Heap Scan | Multiple index lookups | Acceptable |
| Hash Join | Join via hash table | Good for large sets |
| Nested Loop | Row-by-row join | Bad for large sets |

### Phase 3: Index Strategy

#### B-tree (default)
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

#### Composite (order matters: equality first, range last)
```sql
CREATE INDEX idx_orders_status_date ON orders(status, created_at DESC);
-- Works for: WHERE status = ? AND created_at > ?
-- Works for: WHERE status = ?
-- Does NOT work for: WHERE created_at > ? alone
```

#### Partial (smaller, faster)
```sql
CREATE INDEX idx_active_users ON users(email) WHERE active = true;
CREATE INDEX idx_pending_orders ON orders(created_at) WHERE status = 'pending';
```

#### GIN (JSONB, arrays, full-text)
```sql
CREATE INDEX idx_products_tags ON products USING GIN(tags);
CREATE INDEX idx_docs_search ON documents USING GIN(to_tsvector('english', content));
```

#### Find Missing / Unused Indexes
```sql
-- Tables with high seq scans and large size
SELECT schemaname, tablename, seq_scan,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_stat_user_tables
WHERE seq_scan > 50
  AND pg_total_relation_size(schemaname||'.'||tablename) > 10485760
ORDER BY seq_scan DESC;

-- Unused indexes (candidates for removal)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%_pkey'
ORDER BY schemaname, tablename;
```

### Phase 4: Query Rewrites

```sql
-- Replace correlated subquery with JOIN
-- Bad:
SELECT * FROM orders o
WHERE (SELECT COUNT(*) FROM items WHERE order_id = o.id) > 5;
-- Good:
SELECT o.* FROM orders o
JOIN (SELECT order_id, COUNT(*) AS cnt FROM items GROUP BY order_id) i
  ON i.order_id = o.id AND i.cnt > 5;

-- NOT EXISTS instead of NOT IN (handles NULLs)
-- Bad:
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM bans);
-- Good:
SELECT * FROM users u
WHERE NOT EXISTS (SELECT 1 FROM bans b WHERE b.user_id = u.id);
```

### Phase 5: Configuration (8GB RAM server)
```ini
# postgresql.conf
shared_buffers = 2GB                  # 25% of RAM
effective_cache_size = 6GB            # 75% of RAM
work_mem = 64MB                       # per sort/hash operation
maintenance_work_mem = 512MB

checkpoint_completion_target = 0.9
wal_buffers = 16MB
max_wal_size = 1GB

random_page_cost = 1.1               # for SSDs
effective_io_concurrency = 200       # for SSDs

max_parallel_workers_per_gather = 4
max_parallel_workers = 8

autovacuum_max_workers = 5
autovacuum_vacuum_cost_delay = 2ms
```

### Phase 6: Maintenance
```sql
-- Check bloat
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
       ROUND(n_dead_tup::numeric / NULLIF(n_live_tup,0) * 100, 2) AS dead_pct,
       last_vacuum, last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_pct DESC;

-- Manual vacuum
VACUUM (ANALYZE, VERBOSE) orders;
-- Full vacuum (locks table — maintenance window only)
VACUUM FULL orders;
-- Reindex without lock
REINDEX INDEX CONCURRENTLY idx_orders_created_at;
```

### Phase 7: Monitoring
```sql
-- Active connections and wait events
SELECT pid, usename, application_name, state, wait_event_type, wait_event, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- Lock waits
SELECT blocked.pid, blocked.query, blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0;
```

### Optimize Checklist
- [ ] Slow queries identified via pg_stat_statements
- [ ] EXPLAIN ANALYZE run on top slow queries
- [ ] Sequential scans on large tables investigated
- [ ] Missing indexes created
- [ ] Unused indexes removed
- [ ] Configuration tuned for available RAM
- [ ] Autovacuum running, table bloat < 20%
- [ ] Monitoring active
