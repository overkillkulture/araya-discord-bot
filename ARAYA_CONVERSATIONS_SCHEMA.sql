-- ARAYA Conversations Schema for Supabase
-- Run this in Supabase SQL Editor
-- Created: Jan 11, 2026

-- Drop if exists (for fresh start)
DROP TABLE IF EXISTS araya_conversations;

-- Main conversations table
CREATE TABLE araya_conversations (
    id BIGSERIAL PRIMARY KEY,
    user_message TEXT NOT NULL,
    araya_response TEXT NOT NULL,
    source_ai VARCHAR(50) DEFAULT 'fallback',
    user_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster user queries
CREATE INDEX idx_araya_conversations_user_id ON araya_conversations(user_id);
CREATE INDEX idx_araya_conversations_created_at ON araya_conversations(created_at DESC);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE araya_conversations ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for service role
CREATE POLICY "Service role full access" ON araya_conversations
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Grant permissions
GRANT ALL ON araya_conversations TO service_role;
GRANT USAGE, SELECT ON SEQUENCE araya_conversations_id_seq TO service_role;
