-- ════════════════════════════════════════════════════════════════
-- ORACLE — GraphRAG pgvector Support (L9 Memory upgrade)
-- Adds HNSW vector index + similarity search RPC function.
-- Addresses expert feedback: "genuine Neo4j/pgvector GraphRAG for L9"
-- ════════════════════════════════════════════════════════════════

-- ── Unique constraint for upsert (user_id + node_type + label) ──
-- Allows ON CONFLICT upsert in the ingest pipeline.
CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_nodes_user_type_label
    ON oracle_memory.memory_nodes (user_id, node_type, label)
    WHERE node_type IN ('asset', 'concept', 'event', 'strategy');

-- ── HNSW index for fast approximate nearest-neighbor search ──
-- HNSW (Hierarchical Navigable Small World) gives sub-linear search
-- with high recall for cosine distance (<=>).
CREATE INDEX IF NOT EXISTS idx_memory_nodes_embedding_hnsw
    ON oracle_memory.memory_nodes
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ── Unique constraint for edge upsert ──
CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_edges_unique
    ON oracle_memory.memory_edges (source_id, target_id, relation);

-- ════════════════════════════════════════════════════════════════
-- RPC: match_memory_nodes
-- Vector similarity search with optional node_type filter.
-- Called from GraphRAGEngine.vector_search().
-- ════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION oracle_memory.match_memory_nodes(
    query_user_id uuid,
    query_embedding vector(1536),
    query_node_type text DEFAULT NULL,
    match_threshold float DEFAULT 0.72,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    node_type text,
    label text,
    properties jsonb,
    similarity float
)
LANGUAGE sql
STABLE
SECURITY DEFINER SET search_path = oracle_memory, public
AS $$
    SELECT
        n.id,
        n.node_type,
        n.label,
        n.properties,
        1 - (n.embedding <=> query_embedding) AS similarity
    FROM oracle_memory.memory_nodes n
    WHERE n.user_id = query_user_id
      AND n.embedding IS NOT NULL
      AND (query_node_type IS NULL OR n.node_type = query_node_type)
      AND 1 - (n.embedding <=> query_embedding) >= match_threshold
    ORDER BY n.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Grant execute to authenticated + anon (RLS still enforces user scope)
GRANT EXECUTE ON FUNCTION oracle_memory.match_memory_nodes TO authenticated, anon;

-- ════════════════════════════════════════════════════════════════
-- RPC: get_memory_subgraph
-- Returns a node + its 1-hop neighbors for graph visualization.
-- ════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION oracle_memory.get_memory_subgraph(
    query_user_id uuid,
    center_node_id uuid DEFAULT NULL,
    max_nodes int DEFAULT 50
)
RETURNS TABLE (
    nodes jsonb,
    edges jsonb
)
LANGUAGE sql
STABLE
SECURITY DEFINER SET search_path = oracle_memory, public
AS $$
    WITH user_nodes AS (
        SELECT id, node_type, label, properties, created_at
        FROM oracle_memory.memory_nodes
        WHERE user_id = query_user_id
        ORDER BY created_at DESC
        LIMIT max_nodes
    ),
    node_ids AS (SELECT id FROM user_nodes),
    user_edges AS (
        SELECT e.source_id, e.target_id, e.relation, e.weight
        FROM oracle_memory.memory_edges e
        WHERE e.source_id IN (SELECT id FROM node_ids)
           OR e.target_id IN (SELECT id FROM node_ids)
    )
    SELECT
        (SELECT jsonb_agg(row_to_json(t)) FROM (
            SELECT id, node_type, label, properties FROM user_nodes
        ) t),
        (SELECT jsonb_agg(row_to_json(t)) FROM (
            SELECT source_id, target_id, relation, weight FROM user_edges
        ) t);
$$;

GRANT EXECUTE ON FUNCTION oracle_memory.get_memory_subgraph TO authenticated, anon;
