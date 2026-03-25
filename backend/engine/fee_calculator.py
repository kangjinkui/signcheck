"""
수수료 계산 엔진 (PDF p.13 수수료표 기준)

공식:
  기본 수수료 = base_fee + max(0, area - threshold) * extra_fee
  최종 수수료 = 기본 수수료 × 조명가중치  (100원 단위 올림)

조명가중치:
  none        → 1.0
  internal    → 1.5  (형광등, LED)
  neon_digital → 2.0 (네온, 전광류, 디지털)
"""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import FeeRule
import math


LIGHT_WEIGHT = {
    "none": 1.0,
    "internal": 1.5,
    "neon_digital": 2.0,
}


@dataclass
class FeeResult:
    base_fee: int
    light_weight: float
    total: int
    sign_type: str
    area: float
    light_type: str


async def calculate(
    db: AsyncSession,
    sign_type: str,
    area: float,
    light_type: str,
    ad_type: str = "self",
) -> FeeResult:
    result = await db.execute(
        select(FeeRule).where(
            FeeRule.sign_type == sign_type,
            FeeRule.ad_type == ad_type,
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        # 규칙 없음 → 0원 반환 (관리자가 등록 필요)
        return FeeResult(
            base_fee=0, light_weight=1.0, total=0,
            sign_type=sign_type, area=area, light_type=light_type
        )

    threshold = float(rule.area_threshold)
    base = rule.base_fee
    if area > threshold and rule.extra_fee:
        base += math.ceil(area - threshold) * rule.extra_fee

    weight = LIGHT_WEIGHT.get(light_type, 1.0)
    raw_total = base * weight
    total = math.ceil(raw_total / 100) * 100  # 100원 단위 올림

    return FeeResult(
        base_fee=base,
        light_weight=weight,
        total=total,
        sign_type=sign_type,
        area=area,
        light_type=light_type,
    )
