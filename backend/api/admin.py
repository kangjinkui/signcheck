from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime, UTC
from db import get_db
from db.models import (
    CaseLog,
    DraftRule,
    FeeRule,
    IndustryExceptionRule,
    RuleCondition,
    RuleEffect,
    SignCountRule,
    SpecialZoneRule,
)
from services import draft_rule_service, privategpt_client
import tempfile, os


class RuleEffectUpdate(BaseModel):
    decision: Optional[str] = None
    review_type: Optional[str] = None
    max_area: Optional[float] = None
    max_height: Optional[float] = None
    max_protrusion: Optional[float] = None
    max_width: Optional[float] = None
    display_period: Optional[str] = None
    warnings: Optional[list] = None


class RuleConditionCreate(BaseModel):
    sign_type: str
    floor_min: Optional[int] = None
    floor_max: Optional[int] = None
    light_type: Optional[str] = None
    digital: Optional[bool] = False
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    zone: Optional[str] = None
    ad_type: Optional[str] = None
    tehranro: Optional[bool] = None
    vendor_count_min: Optional[int] = None
    has_sidewalk: Optional[bool] = None
    priority: Optional[int] = 100


class RuleCreate(BaseModel):
    condition: RuleConditionCreate
    effect: RuleEffectUpdate


class DraftRuleCreate(BaseModel):
    sign_type: str
    install_subtype: Optional[str] = None
    title: str
    source_type: str
    source_document_id: Optional[str] = None
    source_provision_id: Optional[str] = None
    source_chunk_ids: list[str] = []
    summary: Optional[str] = None
    extracted_payload: dict = {}
    condition_payload: dict = {}
    effect_payload: dict = {}
    auxiliary_payload: dict = {}


class DraftRuleUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    extracted_payload: Optional[dict] = None
    condition_payload: Optional[dict] = None
    effect_payload: Optional[dict] = None
    auxiliary_payload: Optional[dict] = None
    status: Optional[str] = None
    reviewer_note: Optional[str] = None
    reviewer_id: Optional[str] = None


class DraftRuleImportItem(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    source_document_id: Optional[str] = None
    source_provision_id: Optional[str] = None
    source_chunk_ids: list[str] = Field(default_factory=list)
    extracted_payload: dict = Field(default_factory=dict)
    condition_payload: dict = Field(default_factory=dict)
    effect_payload: dict = Field(default_factory=dict)
    auxiliary_payload: dict = Field(default_factory=dict)


class DraftRuleImportRequest(BaseModel):
    sign_type: str
    install_subtype: Optional[str] = None
    source_type: str
    query: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=20)
    min_similarity: float = Field(default=0.3, ge=0, le=1)
    chunk_ids: list[str] = Field(default_factory=list)
    source_document_id: Optional[str] = None
    source_provision_id: Optional[str] = None
    title_prefix: Optional[str] = None
    items: list[DraftRuleImportItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_import_source(self):
        if self.source_type == "rag" and not self.query:
            raise ValueError("source_type=rag 일 때 query가 필요합니다.")
        if self.source_type == "law_chunk":
            if not (self.chunk_ids or self.source_document_id or self.source_provision_id):
                raise ValueError(
                    "source_type=law_chunk 일 때 chunk_ids, source_document_id, source_provision_id 중 하나가 필요합니다."
                )
        if self.source_type not in {"rag", "law_chunk", "import", "manual"}:
            raise ValueError("source_type은 rag, law_chunk, import, manual 중 하나여야 합니다.")
        if self.source_type in {"import", "manual"} and not self.items:
            raise ValueError("source_type=import/manual 일 때 items가 필요합니다.")
        return self


def _decimalize_condition_payload(payload: dict) -> dict:
    normalized = dict(payload)
    for field in ("area_min", "area_max"):
        if normalized.get(field) is not None:
            normalized[field] = Decimal(str(normalized[field]))
    return normalized


def _decimalize_effect_payload(payload: dict) -> dict:
    normalized = dict(payload)
    for field in (
        "max_area",
        "max_height",
        "max_protrusion",
        "max_width",
        "max_thickness",
        "min_bottom_clearance",
        "min_bottom_clearance_no_sidewalk",
        "max_top_height_relative_building",
        "max_top_height_from_ground",
        "safety_check_min_height",
        "safety_check_min_area",
    ):
        if normalized.get(field) is not None:
            normalized[field] = Decimal(str(normalized[field]))
    return normalized


def _decimalize_auxiliary_payload(payload: dict) -> dict:
    normalized = dict(payload)
    for field in ("max_height", "max_protrusion", "max_thickness"):
        if normalized.get(field) is not None:
            normalized[field] = Decimal(str(normalized[field]))
    return normalized


def _normalize_auxiliary_payload(payload: dict | None) -> dict:
    payload = dict(payload or {})
    return {
        "industry_exception_rules": list(payload.get("industry_exception_rules") or []),
        "sign_count_rules": list(payload.get("sign_count_rules") or []),
        "special_zone_rules": list(payload.get("special_zone_rules") or []),
    }


def _build_auxiliary_rule_summary(
    industry_rules: list[IndustryExceptionRule],
    sign_count_rules: list[SignCountRule],
    special_zone_rules: list[SpecialZoneRule],
) -> dict:
    return {
        "industry_exception_rule_ids": [str(rule.id) for rule in industry_rules],
        "sign_count_rule_ids": [str(rule.id) for rule in sign_count_rules],
        "special_zone_rule_ids": [str(rule.id) for rule in special_zone_rules],
    }


async def _approve_auxiliary_rules(draft: DraftRule, db: AsyncSession) -> dict:
    auxiliary_payload = _normalize_auxiliary_payload(draft.auxiliary_payload)
    default_provision_id = draft.source_provision_id

    industry_rules: list[IndustryExceptionRule] = []
    for payload in auxiliary_payload["industry_exception_rules"]:
        normalized = _decimalize_auxiliary_payload(payload)
        normalized.setdefault("sign_type", draft.sign_type)
        normalized.setdefault("priority", 100)
        normalized.setdefault("provision_id", default_provision_id)
        if not normalized.get("exception_type"):
            raise HTTPException(status_code=400, detail="industry_exception_rules[].exception_type is required")
        rule = IndustryExceptionRule(**normalized)
        db.add(rule)
        industry_rules.append(rule)

    sign_count_rules: list[SignCountRule] = []
    for payload in auxiliary_payload["sign_count_rules"]:
        normalized = dict(payload)
        normalized.setdefault("sign_type", draft.sign_type)
        normalized.setdefault("priority", 100)
        normalized.setdefault("provision_id", default_provision_id)
        if normalized.get("max_count_per_business") is None:
            raise HTTPException(status_code=400, detail="sign_count_rules[].max_count_per_business is required")
        rule = SignCountRule(**normalized)
        db.add(rule)
        sign_count_rules.append(rule)

    special_zone_rules: list[SpecialZoneRule] = []
    for payload in auxiliary_payload["special_zone_rules"]:
        normalized = dict(payload)
        normalized.setdefault("sign_type", draft.sign_type)
        normalized.setdefault("priority", 100)
        normalized.setdefault("provision_id", default_provision_id)
        if not normalized.get("special_zone"):
            raise HTTPException(status_code=400, detail="special_zone_rules[].special_zone is required")
        if not normalized.get("decision"):
            raise HTTPException(status_code=400, detail="special_zone_rules[].decision is required")
        rule = SpecialZoneRule(**normalized)
        db.add(rule)
        special_zone_rules.append(rule)

    await db.flush()
    return _build_auxiliary_rule_summary(industry_rules, sign_count_rules, special_zone_rules)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/rules")
async def get_rules(db: AsyncSession = Depends(get_db)):
    """규칙 목록 조회 (rule_condition + rule_effect JOIN)"""
    result = await db.execute(
        select(RuleCondition, RuleEffect)
        .join(RuleEffect, RuleCondition.id == RuleEffect.rule_id)
        .order_by(RuleCondition.sign_type, RuleCondition.priority)
    )
    rows = result.all()
    return [
        {
            "condition": {
                "id":         str(rc.id),
                "sign_type":  rc.sign_type,
                "floor_min":  rc.floor_min,
                "floor_max":  rc.floor_max,
                "zone":       rc.zone,
                "ad_type":    rc.ad_type,
                "priority":   rc.priority,
            },
            "effect": {
                "id":            str(re.id),
                "decision":      re.decision,
                "review_type":   re.review_type,
                "max_area":      float(re.max_area)       if re.max_area       else None,
                "max_height":    float(re.max_height)     if re.max_height     else None,
                "max_protrusion":float(re.max_protrusion) if re.max_protrusion else None,
                "max_width":     float(re.max_width)      if re.max_width      else None,
                "display_period":re.display_period,
                "warnings":      re.warnings or [],
            },
        }
        for rc, re in rows
    ]


@router.put("/rules/{effect_id}")
async def update_rule(
    effect_id: str,
    body: RuleEffectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """규칙 결과(rule_effect) 수정 — 담당자가 규격·판정 직접 조정 가능"""
    result = await db.execute(
        select(RuleEffect).where(RuleEffect.id == effect_id)
    )
    effect = result.scalar_one_or_none()
    if not effect:
        raise HTTPException(status_code=404, detail="rule_effect not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None and field in ("max_area", "max_height", "max_protrusion", "max_width"):
            value = Decimal(str(value))
        setattr(effect, field, value)

    await db.commit()
    await db.refresh(effect)
    return {"status": "updated", "id": effect_id}


@router.post("/rules", status_code=201)
async def create_rule(body: RuleCreate, db: AsyncSession = Depends(get_db)):
    """규칙 생성 — condition + effect 한 번에 삽입"""
    cond_data = _decimalize_condition_payload(body.condition.model_dump())

    condition = RuleCondition(**cond_data)
    db.add(condition)
    await db.flush()  # id 확보

    effect_data = _decimalize_effect_payload(body.effect.model_dump(exclude_unset=True))

    effect = RuleEffect(rule_id=condition.id, **effect_data)
    db.add(effect)
    await db.commit()
    return {"status": "created", "condition_id": str(condition.id), "effect_id": str(effect.id)}


@router.get("/draft-rules")
async def get_draft_rules(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DraftRule).order_by(desc(DraftRule.created_at))
    if status:
        stmt = stmt.where(DraftRule.status == status)
    result = await db.execute(stmt)
    drafts = result.scalars().all()
    return [
        {
            "id": str(draft.id),
            "sign_type": draft.sign_type,
            "install_subtype": draft.install_subtype,
            "title": draft.title,
            "source_type": draft.source_type,
            "source_document_id": str(draft.source_document_id) if draft.source_document_id else None,
            "source_provision_id": str(draft.source_provision_id) if draft.source_provision_id else None,
            "source_chunk_ids": draft.source_chunk_ids or [],
            "summary": draft.summary,
            "extracted_payload": draft.extracted_payload or {},
            "status": draft.status,
            "reviewer_note": draft.reviewer_note,
            "reviewer_id": draft.reviewer_id,
            "approved_rule_condition_id": str(draft.approved_rule_condition_id) if draft.approved_rule_condition_id else None,
            "approved_rule_effect_id": str(draft.approved_rule_effect_id) if draft.approved_rule_effect_id else None,
            "approved_auxiliary_rule_ids": draft.approved_auxiliary_rule_ids or {},
            "condition_payload": draft.condition_payload or {},
            "effect_payload": draft.effect_payload or {},
            "auxiliary_payload": draft.auxiliary_payload or {},
            "created_at": draft.created_at.isoformat() if draft.created_at else None,
            "reviewed_at": draft.reviewed_at.isoformat() if draft.reviewed_at else None,
        }
        for draft in drafts
    ]


@router.post("/draft-rules", status_code=201)
async def create_draft_rule(body: DraftRuleCreate, db: AsyncSession = Depends(get_db)):
    draft = DraftRule(**body.model_dump())
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return {"status": "created", "id": str(draft.id)}


@router.post("/draft-rules/import", status_code=201)
async def import_draft_rules(body: DraftRuleImportRequest, db: AsyncSession = Depends(get_db)):
    source_hits: list[dict] = []

    if body.source_type == "rag":
        source_hits = await draft_rule_service.fetch_rag_hits(
            db,
            query=body.query or "",
            top_k=body.top_k,
            min_similarity=body.min_similarity,
        )
        if not source_hits:
            raise HTTPException(status_code=404, detail="rag search returned no draft candidates")
    elif body.source_type == "law_chunk":
        try:
            source_hits = await draft_rule_service.fetch_law_chunk_hits(
                db,
                chunk_ids=body.chunk_ids,
                provision_id=body.source_provision_id,
                document_id=body.source_document_id,
                limit=body.top_k,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not source_hits:
            raise HTTPException(status_code=404, detail="law_chunk query returned no draft candidates")

    drafts: list[DraftRule] = []
    if body.items:
        for item in body.items:
            drafts.append(
                draft_rule_service.build_draft_from_extracted_item(
                    sign_type=body.sign_type,
                    install_subtype=body.install_subtype,
                    source_type=body.source_type,
                    item=item.model_dump(),
                    source_hits=source_hits,
                    title_prefix=body.title_prefix,
                )
            )
    else:
        for hit in source_hits:
            drafts.append(
                draft_rule_service.build_draft_from_hit(
                    sign_type=body.sign_type,
                    install_subtype=body.install_subtype,
                    source_type=body.source_type,
                    hit=hit,
                    title_prefix=body.title_prefix,
                )
            )

    for draft in drafts:
        db.add(draft)

    await db.commit()

    return {
        "status": "created",
        "count": len(drafts),
        "draft_rule_ids": [str(draft.id) for draft in drafts],
    }


@router.patch("/draft-rules/{draft_id}")
async def update_draft_rule(
    draft_id: str,
    body: DraftRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DraftRule).where(DraftRule.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="draft_rule not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(draft, field, value)
    if "status" in update_data:
        draft.reviewed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(draft)
    return {"status": "updated", "id": str(draft.id)}


@router.post("/draft-rules/{draft_id}/approve")
async def approve_draft_rule(draft_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DraftRule).where(DraftRule.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="draft_rule not found")
    if draft.status == "approved":
        raise HTTPException(status_code=400, detail="draft_rule already approved")

    condition_payload = dict(draft.condition_payload or {})
    effect_payload = dict(draft.effect_payload or {})
    auxiliary_payload = _normalize_auxiliary_payload(draft.auxiliary_payload)
    has_primary_rule = bool(condition_payload or effect_payload)
    has_auxiliary_rule = any(auxiliary_payload.values())

    condition_payload.setdefault("sign_type", draft.sign_type)
    if draft.install_subtype and condition_payload.get("install_subtype") is None:
        condition_payload["install_subtype"] = draft.install_subtype
    if not has_primary_rule and not has_auxiliary_rule:
        raise HTTPException(status_code=400, detail="draft_rule has no approvable payload")
    if has_primary_rule and not effect_payload.get("decision"):
        raise HTTPException(status_code=400, detail="effect_payload.decision is required for primary rule approval")

    condition = None
    effect = None
    if has_primary_rule:
        condition = RuleCondition(**_decimalize_condition_payload(condition_payload))
        db.add(condition)
        await db.flush()

        effect = RuleEffect(
            rule_id=condition.id,
            **_decimalize_effect_payload(effect_payload),
        )
        db.add(effect)
        await db.flush()

    approved_auxiliary_rule_ids = await _approve_auxiliary_rules(draft, db)

    draft.status = "approved"
    draft.approved_rule_condition_id = condition.id if condition else None
    draft.approved_rule_effect_id = effect.id if effect else None
    draft.approved_auxiliary_rule_ids = approved_auxiliary_rule_ids
    draft.reviewed_at = datetime.now(UTC)

    await db.commit()
    return {
        "status": "approved",
        "draft_rule_id": str(draft.id),
        "condition_id": str(condition.id) if condition else None,
        "effect_id": str(effect.id) if effect else None,
        "approved_auxiliary_rule_ids": approved_auxiliary_rule_ids,
    }


@router.delete("/rules/{condition_id}", status_code=200)
async def delete_rule(condition_id: str, db: AsyncSession = Depends(get_db)):
    """규칙 삭제 — rule_condition 삭제 시 rule_effect CASCADE 자동 삭제"""
    result = await db.execute(
        select(RuleCondition).where(RuleCondition.id == condition_id)
    )
    condition = result.scalar_one_or_none()
    if not condition:
        raise HTTPException(status_code=404, detail="rule_condition not found")

    await db.delete(condition)
    await db.commit()
    return {"status": "deleted", "id": condition_id}


@router.get("/logs")
async def get_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CaseLog).order_by(desc(CaseLog.created_at)).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "decision": log.decision,
            "fee": log.fee_calculated,
            "input": log.input_data,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseLog))
    logs = result.scalars().all()
    total = len(logs)
    by_decision = {}
    by_sign = {}
    for log in logs:
        d = log.decision or "unknown"
        by_decision[d] = by_decision.get(d, 0) + 1
        s = (log.input_data or {}).get("sign_type", "unknown")
        by_sign[s] = by_sign.get(s, 0) + 1
    return {"total": total, "by_decision": by_decision, "by_sign_type": by_sign}


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """법령 문서 PrivateGPT 임베딩"""
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        result = await privategpt_client.ingest_file(tmp_path)
        return {"status": "ok", "result": result}
    finally:
        os.unlink(tmp_path)


@router.get("/ingest/list")
async def list_documents():
    docs = await privategpt_client.list_ingested()
    return {"documents": docs}


@router.delete("/ingest/{doc_id}")
async def delete_document(doc_id: str):
    ok = await privategpt_client.delete_document(doc_id)
    return {"status": "ok" if ok else "error"}


@router.get("/health")
async def health():
    pgpt_ok = await privategpt_client.health_check()
    return {"privategpt": pgpt_ok}
