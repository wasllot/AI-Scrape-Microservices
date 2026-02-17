-- Migration: Fix vector dimensions from 768 to 3072
-- Date: 2026-02-17
-- Reason: Changed embedding model to gemini-embedding-001 (3072 dims)

-- Drop old table with incorrect dimensions
DROP TABLE IF EXISTS embeddings CASCADE;

-- Ensure vector extension is available
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with correct 3072 dimensions for gemini-embedding-001
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(3072),  -- Updated dimension
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast similarity search using cosine distance
CREATE INDEX idx_embeddings_vector ON embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Note: After migration, re-run ingestion script:
-- docker compose exec ai-service python scripts/ingest_cv.py
