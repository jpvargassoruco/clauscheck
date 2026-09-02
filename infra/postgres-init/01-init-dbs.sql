-- Runs once, on first init of an empty postgres data dir (mounted at
-- /docker-entrypoint-initdb.d/). Creates the two databases used by
-- ClausCheck (app) and paperless-ngx, plus the pgvector extension on the
-- app DB. See docs/HLD.md section 1.

CREATE DATABASE clauscheck;
CREATE DATABASE paperless;

\connect clauscheck
CREATE EXTENSION IF NOT EXISTS vector;
