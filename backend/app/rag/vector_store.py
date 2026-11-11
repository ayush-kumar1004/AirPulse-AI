"""
AirPulse AI - Vector Store & Regulatory Retrieval Engine
Provides:
1. PostgreSQL + pgvector persistence with automatic table initialization.
2. Hybrid retrieval: executes native pgvector cosine search when PostgreSQL is online;
   seamlessly falls back to fast in-memory vectorized cosine similarity when DB is offline.
3. Ingestion pipeline: chunks, embeds (768-d), and persists all regulatory documents.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np

from sqlalchemy import select, text
from app.database import AsyncSessionLocal, engine
from app.models.db_models import RegulationChunk
from app.rag.corpus import REGULATORY_DOCUMENTS
from app.rag.embeddings import get_embedding, cosine_similarity
from app.observability import log_rag_retrieval

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_FILE = CACHE_DIR / "regulation_vectors.json"


async def init_vector_table():
    """Ensure pgvector extension and regulation_chunks table exist in PostgreSQL."""
    try:
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as ext_err:
                logger.warning(f"pgvector extension check notice: {ext_err}")
            # Create tables
            from app.database import Base
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Regulation chunks table verified in PostgreSQL.")
    except Exception as e:
        logger.warning(f"PostgreSQL vector table initialization deferred ({e}). Operating with local vector cache.")


def save_local_vector_cache(data: List[Dict[str, Any]]):
    """Save chunk metadata and embeddings to local JSON cache for offline resilience."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    serializable = []
    for item in data:
        row = dict(item)
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
        serializable.append(row)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)


def load_local_vector_cache() -> List[Dict[str, Any]]:
    """Load chunks and embeddings from local cache if present, else build them."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading local vector cache: {e}")
    return []


async def ingest_regulations(force_refresh: bool = False, sync_to_db: bool = True) -> int:
    """Ingest, embed, and store all regulatory documents.
    Stores into PostgreSQL if available, and always maintains local vector cache.
    """
    logger.info("Beginning regulatory document ingestion...")
    existing_cache = load_local_vector_cache() if not force_refresh else []

    if existing_cache and len(existing_cache) == len(REGULATORY_DOCUMENTS) and not force_refresh:
        logger.info(f"Loaded {len(existing_cache)} existing embedded chunks from cache.")
        cached_records = existing_cache
    else:
        cached_records = []
        for doc in REGULATORY_DOCUMENTS:
            content_to_embed = f"{doc['title']}\n{doc['section']}\n{doc['content']}"
            emb = get_embedding(content_to_embed)
            record = {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "category": doc["category"],
                "section": doc["section"],
                "legal_citation": doc["legal_citation"],
                "metadata_json": doc["metadata_json"],
                "content": doc["content"],
                "embedding": emb,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            cached_records.append(record)
        save_local_vector_cache(cached_records)
        logger.info(f"Successfully generated embeddings for {len(cached_records)} regulatory chunks.")

    # Attempt PostgreSQL persistence only if sync_to_db is True
    if sync_to_db:
        try:
            await init_vector_table()
            async with AsyncSessionLocal() as session:
                # Check existing count
                res = await session.execute(select(RegulationChunk.id).limit(1))
                if not res.first() or force_refresh:
                    for item in cached_records:
                        chunk = RegulationChunk(
                            doc_id=item["doc_id"],
                            title=item["title"],
                            category=item["category"],
                            section=item["section"],
                            content=item["content"],
                            legal_citation=item["legal_citation"],
                            metadata_json=item["metadata_json"],
                            embedding=item["embedding"],
                        )
                        session.add(chunk)
                    await session.commit()
                    logger.info(f"Committed {len(cached_records)} regulatory chunks to PostgreSQL.")
        except Exception as e:
            logger.warning(f"PostgreSQL sync skipped ({e}); vector cache is ready in-memory.")

    return len(cached_records)


async def similarity_search_db(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Execute semantic vector similarity search.
    Tries PostgreSQL pgvector first; falls back to in-memory vectorized search.
    """
    import time
    t0 = time.monotonic()
    query_vec = get_embedding(query)

    # 1. Attempt PostgreSQL pgvector query
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(RegulationChunk)
            if category:
                stmt = stmt.where(RegulationChunk.category == category)
            # Use pgvector cosine distance operator if available
            try:
                stmt = stmt.order_by(RegulationChunk.embedding.cosine_distance(query_vec)).limit(top_k)
                result = await session.execute(stmt)
                rows = result.scalars().all()
                if rows:
                    output = []
                    for r in rows:
                        score = cosine_similarity(query_vec, r.embedding) if r.embedding else 0.5
                        output.append({
                            "doc_id": r.doc_id,
                            "title": r.title,
                            "category": r.category,
                            "section": r.section,
                            "content": r.content,
                            "legal_citation": r.legal_citation,
                            "metadata_json": r.metadata_json,
                            "similarity_score": round(score, 4),
                        })
                    dur_ms = (time.monotonic() - t0) * 1000.0
                    log_rag_retrieval(
                        query=query,
                        category_filter=category,
                        chunks_returned=len(output),
                        top_similarity_score=output[0]["similarity_score"] if output else 0.0,
                        citations=[o["legal_citation"] for o in output if o.get("legal_citation")],
                        duration_ms=dur_ms,
                        status="SUCCESS",
                    )
                    return output
            except Exception as pg_err:
                logger.debug(f"pgvector query operator fallback: {pg_err}")
    except Exception as db_err:
        logger.debug(f"DB vector query fallback: {db_err}")

    # 2. Resilient In-Memory Vector Search
    cached = load_local_vector_cache()
    if not cached:
        # Ingest on the fly if cache is missing
        await ingest_regulations()
        cached = load_local_vector_cache()

    if not cached:
        dur_ms = (time.monotonic() - t0) * 1000.0
        log_rag_retrieval(
            query=query,
            category_filter=category,
            chunks_returned=0,
            top_similarity_score=0.0,
            citations=[],
            duration_ms=dur_ms,
            status="EMPTY",
        )
        return []

    scored_chunks = []
    for item in cached:
        if category and item.get("category") != category:
            continue
        emb = item.get("embedding", [])
        score = cosine_similarity(query_vec, emb)
        scored_chunks.append({
            "doc_id": item["doc_id"],
            "title": item["title"],
            "category": item["category"],
            "section": item["section"],
            "content": item["content"],
            "legal_citation": item["legal_citation"],
            "metadata_json": item.get("metadata_json", {}),
            "similarity_score": round(score, 4),
        })

    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
    res = scored_chunks[:top_k]

    dur_ms = (time.monotonic() - t0) * 1000.0
    log_rag_retrieval(
        query=query,
        category_filter=category,
        chunks_returned=len(res),
        top_similarity_score=res[0]["similarity_score"] if res else 0.0,
        citations=[r["legal_citation"] for r in res if r.get("legal_citation")],
        duration_ms=dur_ms,
        status="SUCCESS",
    )
    return res

