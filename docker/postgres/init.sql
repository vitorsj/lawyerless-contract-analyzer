-- PostgreSQL initialization script for Lawyerless development database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Set timezone
SET timezone = 'America/Sao_Paulo';

-- Create schemas
CREATE SCHEMA IF NOT EXISTS contracts;
CREATE SCHEMA IF NOT EXISTS analyses;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT USAGE ON SCHEMA contracts TO lawyerless;
GRANT USAGE ON SCHEMA analyses TO lawyerless;
GRANT USAGE ON SCHEMA users TO lawyerless;
GRANT USAGE ON SCHEMA audit TO lawyerless;

GRANT CREATE ON SCHEMA contracts TO lawyerless;
GRANT CREATE ON SCHEMA analyses TO lawyerless;
GRANT CREATE ON SCHEMA users TO lawyerless;
GRANT CREATE ON SCHEMA audit TO lawyerless;

-- Future tables for contract storage (if needed)
-- This is optional for the current implementation but prepared for future features

-- Contracts table
CREATE TABLE IF NOT EXISTS contracts.contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    file_hash VARCHAR(64),
    contract_type VARCHAR(50),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Contract analyses table
CREATE TABLE IF NOT EXISTS analyses.contract_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID REFERENCES contracts.contracts(id) ON DELETE CASCADE,
    overall_risk VARCHAR(10),
    total_clauses INTEGER,
    processing_time_seconds INTEGER,
    analysis_data JSONB,
    summary_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Clause analyses table
CREATE TABLE IF NOT EXISTS analyses.clause_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_analysis_id UUID REFERENCES analyses.contract_analyses(id) ON DELETE CASCADE,
    clause_id VARCHAR(50),
    original_text TEXT,
    summary TEXT,
    explanation TEXT,
    risk_flag VARCHAR(10),
    negotiation_questions JSONB,
    coordinates JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_contracts_upload_date ON contracts.contracts(upload_date);
CREATE INDEX IF NOT EXISTS idx_contracts_contract_type ON contracts.contracts(contract_type);
CREATE INDEX IF NOT EXISTS idx_contracts_processing_status ON contracts.contracts(processing_status);
CREATE INDEX IF NOT EXISTS idx_analyses_contract_id ON analyses.contract_analyses(contract_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses.contract_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_clause_analyses_contract_analysis_id ON analyses.clause_analyses(contract_analysis_id);
CREATE INDEX IF NOT EXISTS idx_clause_analyses_risk_flag ON analyses.clause_analyses(risk_flag);

-- Full text search indexes
CREATE INDEX IF NOT EXISTS idx_clause_analyses_text_search ON analyses.clause_analyses USING GIN(to_tsvector('portuguese', original_text || ' ' || summary || ' ' || explanation));

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers
CREATE TRIGGER update_contracts_updated_at 
    BEFORE UPDATE ON contracts.contracts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analyses_updated_at 
    BEFORE UPDATE ON analyses.contract_analyses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create sample data for development (optional)
-- INSERT INTO contracts.contracts (filename, contract_type) 
-- VALUES ('sample_safe_agreement.pdf', 'SAFE');

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA contracts TO lawyerless;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analyses TO lawyerless;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA contracts TO lawyerless;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analyses TO lawyerless;

-- Create a view for contract summaries
CREATE OR REPLACE VIEW analyses.contract_summary_view AS
SELECT 
    c.id as contract_id,
    c.filename,
    c.contract_type,
    c.upload_date,
    ca.overall_risk,
    ca.total_clauses,
    ca.processing_time_seconds,
    COUNT(cla.id) as analyzed_clauses,
    COUNT(CASE WHEN cla.risk_flag = 'Vermelho' THEN 1 END) as high_risk_clauses,
    COUNT(CASE WHEN cla.risk_flag = 'Amarelo' THEN 1 END) as medium_risk_clauses,
    COUNT(CASE WHEN cla.risk_flag = 'Verde' THEN 1 END) as low_risk_clauses
FROM contracts.contracts c
LEFT JOIN analyses.contract_analyses ca ON c.id = ca.contract_id
LEFT JOIN analyses.clause_analyses cla ON ca.id = cla.contract_analysis_id
GROUP BY c.id, c.filename, c.contract_type, c.upload_date, ca.overall_risk, ca.total_clauses, ca.processing_time_seconds;

-- Grant view permissions
GRANT SELECT ON analyses.contract_summary_view TO lawyerless;

-- Log successful initialization
INSERT INTO audit.initialization_log (message, created_at) 
VALUES ('Lawyerless database initialized successfully', NOW())
ON CONFLICT DO NOTHING;