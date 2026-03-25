import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import CaseLog
from engine.checklist import generate as gen_checklist
from engine.fee_calculator import calculate as calc_fee
from engine.rule_engine import JudgeInput, RuleEngine
from services import privategpt_client

router = APIRouter(prefix="/api/v1", tags=["chat"])
_engine = RuleEngine()


class ChatRequest(BaseModel):
    case_id: Optional[str] = None
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list


def _format_max_spec(result) -> dict:
    return {
        "area": f"{result.max_area}㎡ 이하" if result.max_area else None,
        "height": f"{result.max_height}m 이하" if result.max_height else None,
        "protrusion": f"{result.max_protrusion}m 이내" if result.max_protrusion else None,
        "width": f"{result.max_width}m 이내" if result.max_width else None,
    }


def _build_fallback_answer(message: str, summary: dict) -> str:
    text = message.lower()
    specs = summary["max_spec"]

    if any(keyword in message for keyword in ["세로", "높이", "height"]):
        if specs["height"]:
            return f"현재 판정 기준 최대 높이는 {specs['height']}입니다."
    if any(keyword in message for keyword in ["가로", "폭", "너비", "width"]):
        if specs["width"]:
            return f"현재 판정 기준 최대 폭은 {specs['width']}입니다."
    if any(keyword in message for keyword in ["돌출", "protrusion"]):
        if specs["protrusion"]:
            return f"현재 판정 기준 최대 돌출폭은 {specs['protrusion']}입니다."
    if any(keyword in message for keyword in ["면적", "넓이", "area"]):
        if specs["area"]:
            return f"현재 판정 기준 최대 면적은 {specs['area']}입니다."
    if any(keyword in message for keyword in ["수수료", "비용", "fee"]):
        return f"현재 계산된 수수료는 {summary['fee_total']:,}원입니다."
    if any(keyword in message for keyword in ["서류", "문서", "준비물"]):
        docs = summary["required_docs"]
        if docs:
            return "필수 서류는 " + ", ".join(docs[:5]) + "입니다."

    answer = [
        f"현재 판정 결과는 {summary['decision_label']}입니다.",
    ]
    if summary["review_type"]:
        answer.append(f"심의 유형은 {summary['review_type']}입니다.")
    if summary["display_period"]:
        answer.append(f"표시기간은 {summary['display_period']}입니다.")

    spec_parts = [value for value in specs.values() if value]
    if spec_parts:
        answer.append("확인된 최대 규격은 " + ", ".join(spec_parts) + "입니다.")
    if summary["warnings"]:
        answer.append("주의사항: " + " / ".join(summary["warnings"][:2]))

    return " ".join(answer)


async def _build_case_summary(case_id: str, db: AsyncSession) -> Optional[dict]:
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        return None

    result = await db.execute(select(CaseLog).where(CaseLog.id == case_uuid))
    case = result.scalar_one_or_none()
    if not case:
        return None

    input_data = case.input_data or {}
    judge_input = JudgeInput(**input_data)
    judge_result = await _engine.judge(db, judge_input)
    fee = await calc_fee(
        db,
        judge_input.sign_type,
        judge_input.area,
        judge_input.light_type,
        judge_input.ad_type,
    )
    docs = await gen_checklist(db, judge_result.decision, judge_input.sign_type)

    decision_label = {
        "permit": "허가",
        "report": "신고",
        "prohibited": "설치불가",
    }.get(judge_result.decision, judge_result.decision)

    return {
        "decision_label": decision_label,
        "review_type": judge_result.review_type,
        "display_period": judge_result.display_period,
        "max_spec": _format_max_spec(judge_result),
        "warnings": judge_result.warnings or [],
        "fee_total": fee.total,
        "required_docs": docs["required"],
        "input_data": input_data,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    ctx_hint = ""
    if req.context:
        sign = req.context.get("sign_type", "")
        zone = req.context.get("zone", "")
        ctx_hint = f"[{sign} / {zone} 관련 질문] "

    case_summary = None
    if req.case_id:
        case_summary = await _build_case_summary(req.case_id, db)
        if case_summary and not ctx_hint:
            sign = case_summary["input_data"].get("sign_type", "")
            zone = case_summary["input_data"].get("zone", "")
            ctx_hint = f"[{sign} / {zone} 관련 질문] "

    try:
        result = await asyncio.wait_for(
            privategpt_client.query_rag(
                question=f"{ctx_hint}{req.message}",
            ),
            timeout=3.0,
        )

        choices = result.get("choices", [{}])
        answer = choices[0].get("message", {}).get("content", "") if choices else ""
        sources = []
        for src in choices[0].get("sources", [])[:3] if choices else []:
            meta = src.get("document", {}).get("doc_metadata", {})
            sources.append({
                "law": meta.get("file_name", ""),
                "page": meta.get("page_label", ""),
                "content": src.get("text", "")[:200],
            })

        if answer:
            return ChatResponse(answer=answer, sources=sources)
    except Exception:
        pass

    if case_summary:
        return ChatResponse(
            answer=_build_fallback_answer(req.message, case_summary),
            sources=[],
        )

    return ChatResponse(
        answer="현재 추가 질문 서비스를 사용할 수 없습니다. 판정 후 다시 시도해 주세요.",
        sources=[],
    )
