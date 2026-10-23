-- TimeThread reference schema for PostgreSQL 16+ and pgvector.
-- Apply with: CREATE EXTENSION IF NOT EXISTS pgcrypto; CREATE EXTENSION IF NOT EXISTS vector;
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS branches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  parent_branch_id uuid, fork_message_id uuid, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (conversation_id, id),
  CONSTRAINT branches_parent_fk FOREIGN KEY (conversation_id, parent_branch_id)
    REFERENCES branches (conversation_id, id) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  branch_id uuid NOT NULL, sequence_no bigint NOT NULL CHECK (sequence_no >= 0),
  speaker text NOT NULL, content text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb, UNIQUE (conversation_id, id, branch_id),
  UNIQUE (branch_id, sequence_no),
  CONSTRAINT messages_branch_fk FOREIGN KEY (conversation_id, branch_id)
    REFERENCES branches (conversation_id, id) DEFERRABLE INITIALLY DEFERRED
);
ALTER TABLE branches DROP CONSTRAINT IF EXISTS branches_fork_source_fk;
ALTER TABLE branches ADD CONSTRAINT branches_fork_source_fk
  FOREIGN KEY (conversation_id, fork_message_id, parent_branch_id)
  REFERENCES messages (conversation_id, id, branch_id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE IF NOT EXISTS workflow_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  branch_id uuid NOT NULL, workflow_id text NOT NULL, schema_version text NOT NULL DEFAULT '1.0',
  status text NOT NULL CHECK (status IN ('in_progress','blocked','ready_for_approval','released')),
  payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (conversation_id, branch_id, workflow_id),
  FOREIGN KEY (conversation_id, branch_id) REFERENCES branches (conversation_id, id) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), workflow_record_id uuid NOT NULL REFERENCES workflow_records(id) ON DELETE CASCADE,
  source_id text NOT NULL, title text NOT NULL, publisher text, url text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (workflow_record_id, source_id)
);
CREATE TABLE IF NOT EXISTS claims (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), workflow_record_id uuid NOT NULL REFERENCES workflow_records(id) ON DELETE CASCADE,
  claim_id text NOT NULL, statement text NOT NULL, support_status text NOT NULL CHECK (support_status IN ('supported','qualified','unsupported')),
  analysis_type text CHECK (analysis_type IN ('source_statement','corroborated','inference')),
  UNIQUE (workflow_record_id, claim_id)
);
CREATE TABLE IF NOT EXISTS claim_sources (
  claim_uuid uuid NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
  source_uuid uuid NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
  PRIMARY KEY (claim_uuid, source_uuid)
);
CREATE TABLE IF NOT EXISTS embedding_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), source_uuid uuid NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  chunk_index integer NOT NULL CHECK (chunk_index >= 0), content text NOT NULL,
  embedding vector(1536), created_at timestamptz NOT NULL DEFAULT now(), UNIQUE (source_uuid, chunk_index)
);
CREATE INDEX IF NOT EXISTS embedding_chunks_hnsw_idx ON embedding_chunks USING hnsw (embedding vector_cosine_ops);
CREATE TABLE IF NOT EXISTS outbox_events (
  id bigserial PRIMARY KEY, aggregate_type text NOT NULL, aggregate_id uuid NOT NULL,
  event_type text NOT NULL, payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(), processed_at timestamptz,
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0)
);
CREATE INDEX IF NOT EXISTS outbox_pending_idx ON outbox_events (created_at) WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS messages_conversation_time_idx ON messages (conversation_id, occurred_at);
COMMIT;
