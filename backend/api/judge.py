from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, model_validator
from typing import Optional
import uuid

from db import get_db
from db.models import CaseLog, DocumentMaster, Provision
from engine.rule_engine import RuleEngine, JudgeInput
from engine.fee_calculator import calculate as calc_fee
from engine.checklist import generate as gen_checklist
from services import rag_service

router = APIRouter(prefix="/api/v1", tags=["judge"])
_engine = RuleEngine()


class JudgeCommonRequestFields(BaseModel):
    sign_type: str = Field(..., examples=["돌출간판"])
    floor: int = Field(..., ge=1, examples=[3])
    area: float = Field(..., gt=0, examples=[4.5])
    light_type: str = Field(default="none", examples=["internal"])
    zone: str = Field(..., examples=["일반상업지역"])
    ad_type: str = Field(default="self", examples=["self"])
    install_subtype: Optional[str] = None
    form_type: Optional[str] = None
    content_type: Optional[str] = None
    display_orientation: Optional[str] = None
    special_zone: Optional[str] = None
    tehranro: bool = Field(default=False)
    vendor_count: Optional[int] = None
    has_sidewalk: Optional[bool] = None
    shop_front_width: Optional[float] = Field(default=None, gt=0)
    sign_width: Optional[float] = Field(default=None, gt=0)
    sign_height: Optional[float] = Field(default=None, gt=0)
    sign_area: Optional[float] = Field(default=None, gt=0)
    is_corner_lot: Optional[bool] = None
    has_front_and_rear_roads: Optional[bool] = None
    building_floor_count: Optional[int] = Field(default=None, ge=1)
    install_at_top_floor: Optional[bool] = None
    building_width: Optional[float] = Field(default=None, gt=0)
    requested_faces: Optional[int] = Field(default=None, ge=1)
    horizontal_distance_to_other_sign: Optional[float] = Field(default=None, ge=0)
    has_performance_hall: Optional[bool] = None
    base_width: Optional[float] = Field(default=None, gt=0)
    base_depth: Optional[float] = Field(default=None, gt=0)
    distance_from_building: Optional[float] = Field(default=None, ge=0)


class JudgeProjectingSignRequestFields(BaseModel):
    business_category: Optional[str] = None
    height: Optional[float] = Field(default=None, gt=0)
    width: Optional[float] = Field(default=None, gt=0)
    protrusion: Optional[float] = Field(default=None, gt=0)
    thickness: Optional[float] = Field(default=None, gt=0)
    bottom_clearance: Optional[float] = Field(default=None, gt=0)
    top_height_from_ground: Optional[float] = Field(default=None, gt=0)
    face_area: Optional[float] = Field(default=None, gt=0)
    building_height: Optional[float] = Field(default=None, gt=0)
    floor_height: Optional[float] = Field(default=None, gt=0)
    existing_sign_count_for_business: Optional[int] = Field(default=None, ge=0)
    existing_sign_types: list[str] = Field(default_factory=list)
    exception_review_approved: Optional[bool] = None


class JudgeRequest(JudgeCommonRequestFields, JudgeProjectingSignRequestFields):
    @model_validator(mode="after")
    def normalize_optional_strings(self):
        optional_string_fields = (
            "install_subtype",
            "form_type",
            "content_type",
            "display_orientation",
            "special_zone",
            "business_category",
        )
        for field_name in optional_string_fields:
            value = getattr(self, field_name)
            if isinstance(value, str) and not value.strip():
                setattr(self, field_name, None)
        return self

    @model_validator(mode="after")
    def validate_sign_specific_fields(self):
        if self.sign_type == "선전탑":
            raise ValueError("선전탑은 현재 지원하지 않는 광고물 유형입니다.")
        return self


class JudgeMaxSpec(BaseModel):
    area: Optional[str] = None
    height: Optional[str] = None
    protrusion: Optional[str] = None
    width: Optional[str] = None


class JudgeFeeSummary(BaseModel):
    base: int
    light_weight: float
    total: int


class JudgeResponse(BaseModel):
    case_id: str
    decision: str
    review_type: Optional[str]
    administrative_action: Optional[str]
    safety_check: bool
    max_spec: JudgeMaxSpec
    fee: JudgeFeeSummary
    display_period: Optional[str]
    required_docs: list
    optional_docs: list
    provisions: list
    warnings: list
    matched_rule_id: Optional[str]
    missing_fields: list[str]
    fallback_reason: str


async def _resolve_provisions(
    db: AsyncSession,
    req: JudgeRequest,
    result,
) -> tuple[list[dict], list[str]]:
    provisions = []
    rag_chunks = []

    if result.provision_id:
        provision_stmt = (
            select(Provision, DocumentMaster)
            .join(DocumentMaster, Provision.document_id == DocumentMaster.id)
            .where(Provision.id == uuid.UUID(result.provision_id))
        )
        provision_row = (await db.execute(provision_stmt)).first()
        if provision_row:
            provision, document = provision_row
            provisions.append({
                "law": document.name,
                "article": provision.article,
                "content": provision.content,
                "similarity": 1.0,
            })
            rag_chunks.append(provision.article or str(provision.id))
            return provisions, rag_chunks

    try:
        query = f"{req.sign_type} {req.zone} {req.floor}층 {req.area}㎡ 설치 허가 신고 요건"
        hits = await rag_service.search(db, query, top_k=3)
        for hit in hits:
            provisions.append({
                "law":     hit["법령명"],
                "article": hit["조문번호"],
                "content": hit["조문내용"],
                "similarity": hit["similarity"],
            })
            rag_chunks.append(hit["조문번호"])
    except Exception:
        pass

    return provisions, rag_chunks


@router.post("/judge", response_model=JudgeResponse)
async def judge(req: JudgeRequest, db: AsyncSession = Depends(get_db)):
    inp = JudgeInput(**req.model_dump())

    # 1. 규칙 엔진 판정
    result = await _engine.judge(db, inp)

    # 2. 수수료 계산
    fee = await calc_fee(db, req.sign_type, req.area, req.light_type, req.ad_type)

    # 3. 서류 목록
    docs = await gen_checklist(db, result.decision, req.sign_type)

    # 4. 근거 조문: 규칙에 연결된 provision_id 우선, 없으면 RAG 보조 검색
    provisions, rag_chunks = await _resolve_provisions(db, req, result)

    # 5. 로그 저장
    case_id = str(uuid.uuid4())
    log = CaseLog(
        id=uuid.UUID(case_id),
        input_data=req.model_dump(),
        output_data={
            "decision": result.decision,
            "review_type": result.review_type,
            "administrative_action": result.administrative_action,
            "safety_check": result.safety_check,
            "missing_fields": result.missing_fields,
            "fallback_reason": result.fallback_reason,
            "fee": fee.total,
        },
        decision=result.decision,
        fee_calculated=fee.total,
        rag_chunks_used=rag_chunks,
    )
    db.add(log)
    await db.commit()

    return JudgeResponse(
        case_id=case_id,
        decision=result.decision,
        review_type=result.review_type,
        administrative_action=result.administrative_action,
        safety_check=result.safety_check,
        max_spec=JudgeMaxSpec(
            area=f"{result.max_area}㎡ 이하" if result.max_area else None,
            height=f"{result.max_height}m 이하" if result.max_height else None,
            protrusion=f"{result.max_protrusion}m 이내" if result.max_protrusion else None,
            width=f"{result.max_width}m 이내" if result.max_width else None,
        ),
        fee=JudgeFeeSummary(
            base=fee.base_fee,
            light_weight=fee.light_weight,
            total=fee.total,
        ),
        display_period=result.display_period,
        required_docs=docs["required"],
        optional_docs=docs["optional"],
        provisions=provisions,
        warnings=result.warnings,
        matched_rule_id=result.matched_rule_id,
        missing_fields=result.missing_fields,
        fallback_reason=result.fallback_reason,
    )
