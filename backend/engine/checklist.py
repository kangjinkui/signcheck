"""서류 체크리스트 생성 — work_type + sign_type 기반"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from db.models import ChecklistRule


async def generate(
    db: AsyncSession,
    decision: str,
    sign_type: str,
) -> dict:
    work_type = "permit" if decision == "permit" else "report"

    result = await db.execute(
        select(ChecklistRule).where(
            ChecklistRule.work_type == work_type,
            or_(
                ChecklistRule.sign_type == sign_type,
                ChecklistRule.sign_type.is_(None),
            )
        ).order_by(ChecklistRule.sign_type.desc())  # 유형별 규칙 우선
    )
    rules = result.scalars().all()

    required, optional = [], []
    for rule in rules:
        for doc in (rule.required_docs or []):
            if doc not in required:
                required.append(doc)
        for doc in (rule.optional_docs or []):
            if doc not in optional:
                optional.append(doc)

    return {"required": required, "optional": optional}
