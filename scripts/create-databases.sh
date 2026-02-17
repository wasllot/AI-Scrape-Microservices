#!/bin/bash
set -e

# This script creates multiple databases and enables pgvector extension

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Create app_db for Laravel
    CREATE DATABASE app_db;
    
    -- Create vector_db for AI service
    CREATE DATABASE vector_db;
    
    -- Enable pgvector extension on vector_db
    \c vector_db
    CREATE EXTENSION IF NOT EXISTS vector;
    
    -- Create embeddings table
    CREATE TABLE IF NOT EXISTS embeddings (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        embedding vector(768),
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create index for fast similarity search
    CREATE INDEX IF NOT EXISTS embeddings_embedding_idx ON embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
    
    GRANT ALL PRIVILEGES ON DATABASE app_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE vector_db TO $POSTGRES_USER;
EOSQL

echo "Databases created successfully with pgvector enabled!"
