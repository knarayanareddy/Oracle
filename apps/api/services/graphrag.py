# ════════════════════════════════════════════════════════════════
# ORACLE — GraphRAG Memory Engine (L9)  §12, §Module 5
# Genuine pgvector-based knowledge graph with:
#   - Embedding generation (OpenAI text-embedding-3-small, 1536 dim)
#   - HNSW vector similarity search (semantic retrieval)
#   - Knowledge graph traversal (nodes + typed edges)
#   - Entity extraction & linking
#
# Uses Supabase pgvector (already in schema: memory_nodes.embedding).
# This replaces the relational stub and implements the design doc's
# "genuine Neo4j/pgvector GraphRAG for L9 Memory" requirement.
# ════════════════════════════════════════════════════════════════
import asyncio
import json
import re
from typing import Any

import httpx
from supabase import create_client, Client

from config import settings
from logging_config import logger
from services.resilience import resilient_call, llm_breaker

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
# Cosine similarity threshold below which results are not semantically relevant
SIMILARITY_THRESHOLD = 0.72
MAX_RETRIEVAL_RESULTS = 5

# Known financial entities for linking (includes crypto shorthand)
KNOWN_TICKERS = {
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM",
    "SPY", "QQQ", "VTI", "AMD", "NFLX", "BABA", "UBER", "COIN",
    "TLT", "GLD", "VIX",
    "BTC", "BTC-USD", "ETH", "ETH-USD",  # crypto shorthand
}
KNOWN_CONCEPTS = {
    "interest rate", "inflation", "recession", "earnings", "fed",
    "rate hike", "rate cut", "yield curve", "bull market", "bear market",
    "gdp", "unemployment", "cpi", "fomc", "quantitative easing",
}


class GraphRAGEngine:
    """
    Graph-based Retrieval Augmented Generation over the pgvector store.

    Two-phase retrieval:
      1. Vector search: find memory_nodes semantically similar to query
      2. Graph expansion: traverse edges from those nodes to find
         related entities (assets, events, strategies)
    """

    def __init__(self):
        self._supabase: Client | None = None
        self._openai: Any = None

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            if not settings.supabase_url or not settings.supabase_service_role_key:
                raise RuntimeError("Supabase not configured for GraphRAG")
            self._supabase = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key,
            )
        return self._supabase

    def _get_openai(self):
        if self._openai is None:
            if not settings.openai_api_key:
                return None
            from openai import AsyncOpenAI
            self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai

    # ════════════════════════════════════════════════════════════════
    # Embedding generation
    # ════════════════════════════════════════════════════════════════
    async def embed(self, text: str) -> list[float] | None:
        """Generate a 1536-dim embedding via OpenAI. Returns None on failure."""
        client = self._get_openai()
        if client is None:
            return None

        async def _embed():
            resp = await client.embeddings.create(model=EMBEDDING_MODEL, input=text[:8000])
            return resp.data[0].embedding

        return await resilient_call(
            _embed,
            breaker=llm_breaker,
            fallback=lambda: None,
            max_retries=2,
        )

    # ════════════════════════════════════════════════════════════════
    # Vector similarity search (uses pgvector HNSW index)
    # ════════════════════════════════════════════════════════════════
    async def vector_search(
        self,
        user_id: str,
        query_embedding: list[float],
        node_type: str | None = None,
        limit: int = MAX_RETRIEVAL_RESULTS,
    ) -> list[dict]:
        """
        Semantic similarity search over memory_nodes using pgvector.

        Uses the Supabase RPC `match_memory_nodes` which performs:
          SELECT * FROM memory_nodes
          WHERE user_id = $1
            AND ($2::text IS NULL OR node_type = $2)
            AND embedding <=> $3 < (1 - threshold)   -- cosine distance
          ORDER BY embedding <=> $3
          LIMIT $4
        """
        try:
            params = {
                "query_user_id": user_id,
                "query_embedding": query_embedding,
                "query_node_type": node_type,
                "match_threshold": SIMILARITY_THRESHOLD,
                "match_count": limit,
            }
            result = self.supabase.rpc("match_memory_nodes", params).execute()
            return result.data or []
        except Exception as e:
            logger.warning("vector_search_rpc_failed", error=str(e))
            return []

    # ════════════════════════════════════════════════════════════════
    # Graph expansion — traverse edges from seed nodes
    # ════════════════════════════════════════════════════════════════
    async def graph_expand(self, user_id: str, seed_node_ids: list[str], max_depth: int = 1) -> list[dict]:
        """Traverse edges from seed nodes to find related entities."""
        if not seed_node_ids:
            return []
        try:
            # Fetch edges where source is one of our seed nodes
            id_list = ",".join(f'"{nid}"' for nid in seed_node_ids)
            result = self.supabase.table("memory_edges").select(
                "relation, weight, source_id, target_id, "
                "target:memory_nodes!memory_edges_target_id_fkey(id, node_type, label, properties)"
            ).filter("source_id", "in", f"({id_list})").execute()

            related = []
            seen = set(seed_node_ids)
            for edge in result.data or []:
                target = edge.get("target")
                if target and target["id"] not in seen:
                    seen.add(target["id"])
                    target["_relation"] = edge.get("relation")
                    target["_weight"] = edge.get("weight")
                    related.append(target)
            return related[:10]
        except Exception as e:
            logger.warning("graph_expand_failed", error=str(e))
            return []

    # ════════════════════════════════════════════════════════════════
    # Entity extraction & linking
    # ════════════════════════════════════════════════════════════════
    def extract_entities(self, text: str) -> list[dict]:
        """
        Extract financial entities from text for knowledge graph construction.
        Detects tickers, macro concepts, and event types.
        """
        entities: list[dict] = []
        text_upper = text.upper()
        text_lower = text.lower()

        # Tickers
        for ticker in KNOWN_TICKERS:
            # Word-boundary match
            if re.search(r'\b' + re.escape(ticker) + r'\b', text_upper):
                is_crypto = ticker in ("BTC", "ETH", "BTC-USD", "ETH-USD")
                entities.append({
                    "type": "asset",
                    "label": ticker,
                    "properties": {"class": "crypto" if is_crypto else "equity"},
                })

        # Macro concepts
        for concept in KNOWN_CONCEPTS:
            if concept in text_lower:
                entities.append({
                    "type": "concept",
                    "label": concept,
                    "properties": {},
                })

        # Event type detection
        if re.search(r'\b(earnings|eps|revenue|beat|miss)\b', text_lower):
            entities.append({"type": "event", "label": "earnings", "properties": {}})
        elif re.search(r'\b(fed|fomc|powell|rate (?:hike|cut))\b', text_lower):
            entities.append({"type": "event", "label": "fed_statement", "properties": {}})
        elif re.search(r'\b(cpi|inflation|gdp|recession)\b', text_lower):
            entities.append({"type": "event", "label": "macro", "properties": {}})

        return entities

    # ════════════════════════════════════════════════════════════════
    # Knowledge graph ingestion
    # ════════════════════════════════════════════════════════════════
    async def ingest(
        self,
        user_id: str,
        text: str,
        source_type: str = "simulation",
        source_id: str | None = None,
    ) -> list[str]:
        """
        Ingest text into the knowledge graph:
          1. Extract entities
          2. Embed the text
          3. Upsert nodes with embeddings
          4. Link co-occurring entities via edges
        Returns the node IDs created/updated.
        """
        entities = self.extract_entities(text)
        embedding = await self.embed(text)

        node_ids: list[str] = []
        # Create a "memory" node for the source text itself
        try:
            mem_node = {
                "user_id": user_id,
                "node_type": "memory",
                "label": text[:80],
                "properties": {"source_type": source_type, "source_id": source_id, "full_text": text[:1000]},
                "embedding": embedding,
            }
            result = self.supabase.table("memory_nodes").insert(mem_node).execute()
            if result.data:
                node_ids.append(result.data[0]["id"])
        except Exception as e:
            logger.warning("graphrag_ingest_memory_node_failed", error=str(e))

        # Upsert entity nodes
        entity_ids: list[str] = []
        for entity in entities:
            try:
                result = self.supabase.table("memory_nodes").upsert(
                    {
                        "user_id": user_id,
                        "node_type": entity["type"],
                        "label": entity["label"],
                        "properties": entity["properties"],
                    },
                    on_conflict="user_id,node_type,label",
                ).execute()
                if result.data:
                    entity_ids.append(result.data[0]["id"])
            except Exception as e:
                logger.debug("graphrag_entity_upsert_failed", label=entity["label"], error=str(e))

        node_ids.extend(entity_ids)

        # Link co-occurring entities (they appeared in the same text → related)
        await self._link_co_occurrence(user_id, node_ids, entity_ids)

        logger.info(
            "graphrag_ingested",
            user_id=user_id,
            entities=len(entities),
            nodes=len(node_ids),
            has_embedding=embedding is not None,
        )
        return node_ids

    async def _link_co_occurrence(self, user_id: str, all_ids: list[str], entity_ids: list[str]) -> None:
        """Create edges between the memory node and each entity, and between co-occurring entities."""
        if len(all_ids) < 2:
            return
        memory_id = all_ids[0]
        edges = []
        # memory → entity
        for eid in entity_ids:
            edges.append({
                "source_id": memory_id, "target_id": eid,
                "relation": "mentions", "weight": 1.0,
            })
        # entity ↔ entity (co-occurrence)
        for i, a in enumerate(entity_ids):
            for b in entity_ids[i + 1:]:
                edges.append({
                    "source_id": a, "target_id": b,
                    "relation": "co_occurs_with", "weight": 0.5,
                })
        if edges:
            try:
                self.supabase.table("memory_edges").upsert(
                    edges, on_conflict="source_id,target_id,relation"
                ).execute()
            except Exception as e:
                logger.debug("graphrag_edge_insert_failed", error=str(e))

    # ════════════════════════════════════════════════════════════════
    # Full retrieval: vector search + graph expansion
    # ════════════════════════════════════════════════════════════════
    async def retrieve(self, user_id: str, query: str, limit: int = MAX_RETRIEVAL_RESULTS) -> dict:
        """
        Full GraphRAG retrieval:
          1. Embed the query
          2. Vector search for similar memory nodes
          3. Graph expand to find related entities
          4. Return structured context for the LLM

        If embedding fails (no OpenAI key / circuit open), falls back to
        keyword-based retrieval so the system never hard-fails.
        """
        embedding = await self.embed(query)

        if embedding:
            nodes = await self.vector_search(user_id, embedding, limit=limit)
            if nodes:
                seed_ids = [n["id"] for n in nodes]
                related = await self.graph_expand(user_id, seed_ids)
                return {
                    "method": "vector_graphrag",
                    "seed_nodes": nodes,
                    "related_entities": related,
                    "query_embedding_dim": len(embedding),
                }

        # Fallback: keyword-based retrieval (no vector search available)
        return await self._keyword_fallback(user_id, query, limit)

    async def _keyword_fallback(self, user_id: str, query: str, limit: int) -> dict:
        """Keyword-based fallback when embeddings unavailable."""
        entities = self.extract_entities(query)
        results: list[dict] = []
        for entity in entities:
            try:
                r = self.supabase.table("memory_nodes").select("*").eq(
                    "user_id", user_id
                ).ilike("label", f"%{entity['label']}%").limit(limit).execute()
                results.extend(r.data or [])
            except Exception:
                pass
        return {
            "method": "keyword_fallback",
            "seed_nodes": results[:limit],
            "related_entities": [],
        }


# Singleton
graphrag_engine = GraphRAGEngine()
