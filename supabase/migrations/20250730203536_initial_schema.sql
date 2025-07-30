-- Supabase Database Setup for RAG System
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Users table
CREATE TABLE IF NOT EXISTS "user" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    avatar_url VARCHAR(500),
    bio VARCHAR(1000),
    preferences JSONB DEFAULT '{}',
    workspace_id VARCHAR(255),
    last_login TIMESTAMP,
    total_queries INTEGER DEFAULT 0,
    total_documents_uploaded INTEGER DEFAULT 0,
    total_conversations INTEGER DEFAULT 0,
    favorite_topics JSONB DEFAULT '[]',
    recent_searches JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create Documents table
CREATE TABLE IF NOT EXISTS document (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size INTEGER NOT NULL,
    content_preview VARCHAR(500),
    full_text TEXT,
    doc_metadata JSONB DEFAULT '{}',
    file_path VARCHAR(500) NOT NULL,
    upload_status VARCHAR(20) DEFAULT 'processing',
    is_active BOOLEAN DEFAULT true,
    uploaded_by UUID REFERENCES "user"(id),
    department VARCHAR(100),
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create Document Chunks table
CREATE TABLE IF NOT EXISTS documentchunk (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_char INTEGER DEFAULT 0,
    end_char INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    embedding JSONB DEFAULT '{}',
    embedding_model VARCHAR(100),
    chunk_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create Conversations table
CREATE TABLE IF NOT EXISTS conversation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255),
    session_id VARCHAR(255),
    user_id UUID REFERENCES "user"(id),
    language VARCHAR(5) DEFAULT 'tr',
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT NOW(),
    context_window INTEGER DEFAULT 10,
    summary TEXT,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create Conversation Messages table
CREATE TABLE IF NOT EXISTS conversationmessage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    message_order INTEGER NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    model_used VARCHAR(100),
    response_time_ms INTEGER DEFAULT 0,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    sources_used JSONB DEFAULT '[]',
    attachments JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create Query Log table
CREATE TABLE IF NOT EXISTS querylog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    user_session VARCHAR(255),
    department VARCHAR(100),
    conversation_id UUID REFERENCES conversation(id),
    user_id UUID REFERENCES "user"(id),
    user_ip VARCHAR(45),
    response_text TEXT,
    model_used VARCHAR(100),
    response_time_ms INTEGER DEFAULT 0,
    retrieved_chunks JSONB DEFAULT '[]',
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_document_uploaded_by ON document(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_document_department ON document(department);
CREATE INDEX IF NOT EXISTS idx_documentchunk_document_id ON documentchunk(document_id);
CREATE INDEX IF NOT EXISTS idx_conversation_user_id ON conversation(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_session_id ON conversation(session_id);
CREATE INDEX IF NOT EXISTS idx_conversationmessage_conversation_id ON conversationmessage(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversationmessage_order ON conversationmessage(message_order);
CREATE INDEX IF NOT EXISTS idx_querylog_user_id ON querylog(user_id);
CREATE INDEX IF NOT EXISTS idx_querylog_conversation_id ON querylog(conversation_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_updated_at BEFORE UPDATE ON document FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversation_updated_at BEFORE UPDATE ON conversation FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a default admin user (password: admin123)
INSERT INTO "user" (email, full_name, hashed_password, role, department) 
VALUES (
    'admin@rag-system.com', 
    'System Administrator', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflHQrxK', -- admin123
    'admin',
    'IT'
) ON CONFLICT (email) DO NOTHING;

-- Success message
SELECT 'Supabase database setup completed successfully!' as status;
