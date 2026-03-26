"""
LlamaIndex RAG 서비스 (pgvector + Ollama)

흐름:
  1. 쿼리 텍스트 → Ollama nomic-embed-text → 768차원 벡터
  2. pgvector cosine 유사도 검색 → law_chunk 상위 k개
  3. provision / document_master 조인 → 조문 원문 + 출처 반환

FastAPI async 완전 지원 (httpx + SQLAlchemy async)
"""
import json
import os
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBED_MODEL = "nomic-embed-text"
DEFAULT_TOP_K = 3


# ── 임베딩 ───────────────────────────────────────────────
async def _embed(query: str) -> list[float]:
    """Ollama REST API로 쿼리 임베딩 벡터 생성"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": query},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


# ── pgvector 유사도 검색 ─────────────────────────────────
_SEARCH_SQL = """
SELECT
    c.id            AS chunk_id,
    c.document_id   AS document_id,
    c.provision_id  AS provision_id,
    c.content       AS chunk_content,
    c.chunk_index,
    p.article       AS 조문번호,
    p.content       AS 조문원문,
    d.name          AS 법령명,
    d.jurisdiction  AS 관할,
    d.effective_date AS 시행일자,
    1 - (c.embedding <=> :vec) AS similarity
FROM law_chunk c
JOIN provision      p ON p.id = c.provision_id
JOIN document_master d ON d.id = c.document_id
ORDER BY c.embedding <=> :vec
LIMIT :k
"""


async def search_with_metadata(
    db: AsyncSession,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_similarity: float = 0.3,
) -> list[dict]:
    """유사도 검색 결과를 원본 참조 메타데이터와 함께 반환."""
    embedding = await _embed(query)
    vec_str = "[" + ",".join(str(v) for v in embedding) + "]"

    result = await db.execute(
        text(_SEARCH_SQL),
        {"vec": vec_str, "k": top_k},
    )
    rows = result.mappings().all()

    provisions = []
    for row in rows:
        sim = float(row["similarity"])
        if sim < min_similarity:
            continue
        provisions.append({
            "chunk_id": str(row["chunk_id"]) if row["chunk_id"] else None,
            "document_id": str(row["document_id"]) if row["document_id"] else None,
            "provision_id": str(row["provision_id"]) if row["provision_id"] else None,
            "law_name": row["법령명"],
            "jurisdiction": row["관할"],
            "article": row["조문번호"],
            "provision_content": row["조문원문"],
            "chunk_content": row["chunk_content"],
            "similarity": round(sim, 4),
        })

    return provisions

async def search(
    db: AsyncSession,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_similarity: float = 0.3,
) -> list[dict]:
    """
    유사도 검색 결과 반환.
    각 항목: {법령명, 관할, 조문번호, 조문원문, chunk_content, similarity}
    """
    hits = await search_with_metadata(
        db,
        query=query,
        top_k=top_k,
        min_similarity=min_similarity,
    )
    return [
        {
            "법령명": hit["law_name"],
            "관할": hit["jurisdiction"],
            "조문번호": hit["article"],
            "조문내용": hit["provision_content"],
            "similarity": hit["similarity"],
        }
        for hit in hits
    ]


# ── 헬스체크 ─────────────────────────────────────────────
async def health_check() -> bool:
    """Ollama 연결 상태 확인"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
