from collections.abc import Iterable
from typing import Optional
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DraftRule
from services import rag_service


_LAW_CHUNK_BASE_SQL = """
SELECT
    c.id AS chunk_id,
    c.document_id AS document_id,
    c.provision_id AS provision_id,
    c.content AS chunk_content,
    c.chunk_index AS chunk_index,
    COALESCE(c.article, p.article) AS article,
    p.content AS provision_content,
    d.name AS law_name,
    d.jurisdiction AS jurisdiction,
    d.effective_date AS effective_date
FROM law_chunk c
LEFT JOIN provision p ON p.id = c.provision_id
LEFT JOIN document_master d ON d.id = c.document_id
"""


def build_source_summary(hit: dict) -> str:
    law_name = hit.get("law_name") or "법령"
    article = hit.get("article") or "조문 미상"
    return f"{law_name} {article}"


def parse_uuid_or_none(value: Optional[str]):
    if not value:
        return None
    return uuid.UUID(str(value))


def build_draft_title(
    sign_type: str,
    install_subtype: Optional[str],
    hit: Optional[dict] = None,
    title_prefix: Optional[str] = None,
) -> str:
    base = title_prefix or sign_type
    if install_subtype:
        base = f"{base} {install_subtype}"
    if not hit:
        return f"{base} 규칙 초안"
    return f"{base} {build_source_summary(hit)} 초안"


def build_extracted_payload(
    *,
    hit: Optional[dict],
    existing_payload: Optional[dict] = None,
    source_hits: Optional[Iterable[dict]] = None,
) -> dict:
    payload = dict(existing_payload or {})
    if hit:
        payload.setdefault(
            "source_summary",
            {
                "law_name": hit.get("law_name"),
                "article": hit.get("article"),
                "jurisdiction": hit.get("jurisdiction"),
                "effective_date": hit.get("effective_date"),
                "chunk_content": hit.get("chunk_content"),
                "provision_content": hit.get("provision_content"),
                "similarity": hit.get("similarity"),
            },
        )
    if source_hits is not None:
        payload.setdefault(
            "source_hits",
            [
                {
                    "chunk_id": source_hit.get("chunk_id"),
                    "document_id": source_hit.get("document_id"),
                    "provision_id": source_hit.get("provision_id"),
                    "law_name": source_hit.get("law_name"),
                    "article": source_hit.get("article"),
                    "similarity": source_hit.get("similarity"),
                }
                for source_hit in source_hits
            ],
        )
    return payload


async def fetch_rag_hits(
    db: AsyncSession,
    *,
    query: str,
    top_k: int,
    min_similarity: float,
) -> list[dict]:
    return await rag_service.search_with_metadata(
        db,
        query=query,
        top_k=top_k,
        min_similarity=min_similarity,
    )


async def fetch_law_chunk_hits(
    db: AsyncSession,
    *,
    chunk_ids: Optional[list[str]] = None,
    provision_id: Optional[str] = None,
    document_id: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    conditions = []
    params: dict[str, object] = {"limit": limit}

    if chunk_ids:
        chunk_placeholders = []
        for index, chunk_id in enumerate(chunk_ids):
            key = f"chunk_id_{index}"
            chunk_placeholders.append(f":{key}")
            params[key] = chunk_id
        conditions.append(f"c.id IN ({', '.join(chunk_placeholders)})")
    if provision_id:
        conditions.append("c.provision_id = CAST(:provision_id AS UUID)")
        params["provision_id"] = provision_id
    if document_id:
        conditions.append("c.document_id = CAST(:document_id AS UUID)")
        params["document_id"] = document_id
    if not conditions:
        raise ValueError("law_chunk 조회에는 chunk_ids, provision_id, document_id 중 하나가 필요합니다.")

    sql = (
        _LAW_CHUNK_BASE_SQL
        + "\nWHERE "
        + " AND ".join(conditions)
        + "\nORDER BY COALESCE(c.article, p.article), c.chunk_index\nLIMIT :limit"
    )
    result = await db.execute(text(sql), params)
    rows = result.mappings().all()
    return [
        {
            "chunk_id": str(row["chunk_id"]) if row["chunk_id"] else None,
            "document_id": str(row["document_id"]) if row["document_id"] else None,
            "provision_id": str(row["provision_id"]) if row["provision_id"] else None,
            "law_name": row["law_name"],
            "jurisdiction": row["jurisdiction"],
            "effective_date": row["effective_date"],
            "article": row["article"],
            "chunk_content": row["chunk_content"],
            "provision_content": row["provision_content"],
            "chunk_index": row["chunk_index"],
        }
        for row in rows
    ]


def build_draft_from_hit(
    *,
    sign_type: str,
    install_subtype: Optional[str],
    source_type: str,
    hit: dict,
    title_prefix: Optional[str] = None,
) -> DraftRule:
    return DraftRule(
        sign_type=sign_type,
        install_subtype=install_subtype,
        title=build_draft_title(
            sign_type=sign_type,
            install_subtype=install_subtype,
            hit=hit,
            title_prefix=title_prefix,
        ),
        source_type=source_type,
        source_document_id=parse_uuid_or_none(hit.get("document_id")),
        source_provision_id=parse_uuid_or_none(hit.get("provision_id")),
        source_chunk_ids=[hit["chunk_id"]] if hit.get("chunk_id") else [],
        summary=build_source_summary(hit),
        extracted_payload=build_extracted_payload(hit=hit),
        condition_payload={},
        effect_payload={},
        auxiliary_payload={},
    )


def build_draft_from_extracted_item(
    *,
    sign_type: str,
    install_subtype: Optional[str],
    source_type: str,
    item: dict,
    source_hits: Optional[list[dict]] = None,
    title_prefix: Optional[str] = None,
) -> DraftRule:
    source_hits = source_hits or []
    unique_document_ids = {hit.get("document_id") for hit in source_hits if hit.get("document_id")}
    unique_provision_ids = {hit.get("provision_id") for hit in source_hits if hit.get("provision_id")}
    aggregated_chunk_ids = [hit["chunk_id"] for hit in source_hits if hit.get("chunk_id")]
    primary_hit = source_hits[0] if source_hits else None

    return DraftRule(
        sign_type=sign_type,
        install_subtype=install_subtype,
        title=item.get("title")
        or build_draft_title(
            sign_type=sign_type,
            install_subtype=install_subtype,
            hit=primary_hit,
            title_prefix=title_prefix,
        ),
        source_type=source_type,
        source_document_id=parse_uuid_or_none(item.get("source_document_id"))
        or parse_uuid_or_none(next(iter(unique_document_ids)) if len(unique_document_ids) == 1 else None),
        source_provision_id=parse_uuid_or_none(item.get("source_provision_id"))
        or parse_uuid_or_none(next(iter(unique_provision_ids)) if len(unique_provision_ids) == 1 else None),
        source_chunk_ids=item.get("source_chunk_ids") or aggregated_chunk_ids,
        summary=item.get("summary")
        or (build_source_summary(primary_hit) if primary_hit else f"{sign_type} 추출 초안"),
        extracted_payload=build_extracted_payload(
            hit=primary_hit,
            existing_payload=item.get("extracted_payload"),
            source_hits=source_hits,
        ),
        condition_payload=item.get("condition_payload") or {},
        effect_payload=item.get("effect_payload") or {},
        auxiliary_payload=item.get("auxiliary_payload") or {},
    )
