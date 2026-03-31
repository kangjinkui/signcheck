"""
규칙 엔진 — 허가/신고/불가 판정 (100% 결정론적)
LLM 없음. PostgreSQL rule_condition/rule_effect 테이블 기반.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from db.models import (
    IndustryExceptionRule,
    RuleCondition,
    RuleEffect,
    SignCountRule,
    SpecialZoneRule,
    ZoneRule,
)


@dataclass
class JudgeInput:
    sign_type: str
    floor: int
    area: float
    light_type: str          # 'none' | 'internal' | 'neon_digital'
    zone: str
    ad_type: str             # 'self' | 'third_party'
    install_subtype: Optional[str] = None
    form_type: Optional[str] = None
    content_type: Optional[str] = None
    display_orientation: Optional[str] = None
    special_zone: Optional[str] = None
    tehranro: bool = False
    vendor_count: Optional[int] = None
    has_sidewalk: Optional[bool] = None
    shop_front_width: Optional[float] = None
    sign_width: Optional[float] = None
    sign_height: Optional[float] = None
    sign_area: Optional[float] = None
    is_corner_lot: Optional[bool] = None
    has_front_and_rear_roads: Optional[bool] = None
    building_floor_count: Optional[int] = None
    install_at_top_floor: Optional[bool] = None
    building_width: Optional[float] = None
    requested_faces: Optional[int] = None
    horizontal_distance_to_other_sign: Optional[float] = None
    has_performance_hall: Optional[bool] = None
    base_width: Optional[float] = None
    base_depth: Optional[float] = None
    distance_from_building: Optional[float] = None
    business_category: Optional[str] = None
    height: Optional[float] = None
    width: Optional[float] = None
    protrusion: Optional[float] = None
    thickness: Optional[float] = None
    bottom_clearance: Optional[float] = None
    top_height_from_ground: Optional[float] = None
    face_area: Optional[float] = None
    building_height: Optional[float] = None
    floor_height: Optional[float] = None
    existing_sign_count_for_business: Optional[int] = None
    existing_sign_types: list[str] = field(default_factory=list)
    exception_review_approved: Optional[bool] = None


@dataclass
class JudgeResult:
    decision: str            # 'permit' | 'report' | 'prohibited'
    review_type: Optional[str] = None
    administrative_action: Optional[str] = None
    safety_check: bool = False
    max_area: Optional[float] = None
    max_height: Optional[float] = None
    max_protrusion: Optional[float] = None
    max_width: Optional[float] = None
    display_period: Optional[str] = None
    warnings: list = field(default_factory=list)
    matched_rule_id: Optional[str] = None
    provision_id: Optional[str] = None
    missing_fields: list[str] = field(default_factory=list)
    fallback_reason: str = "none"


@dataclass
class ProjectingSignContext:
    condition: RuleCondition
    effect: RuleEffect
    warnings: list[str]
    review_type: Optional[str]
    exception_category: Optional[str]
    exception_rule: Optional[IndustryExceptionRule]
    sign_count_rule: Optional[SignCountRule]


class RuleEngine:
    """
    판정 흐름:
    1. 절대 불가 조건 체크 (priority 낮을수록 우선, 불가 = 1)
    2. 규격 초과 체크
    3. 허가 vs 신고 분기
    4. 심의 분류
    """

    async def judge(self, db: AsyncSession, input: JudgeInput) -> JudgeResult:
        missing_input = self._check_missing_input(input)
        if missing_input:
            return missing_input

        if input.sign_type == "돌출간판":
            return await self._judge_projecting_sign(db, input)

        if (
            input.sign_type == "벽면이용간판"
            and input.install_subtype == "wall_sign_general_under_5f"
        ):
            return await self._judge_wall_sign_general_under_5f(db, input)

        if (
            input.sign_type == "벽면이용간판"
            and input.install_subtype == "wall_sign_top_building"
        ):
            return await self._judge_wall_sign_top_building(db, input)

        if input.sign_type == "옥상간판":
            return await self._judge_rooftop_sign(db, input)

        if input.sign_type == "공연간판":
            return await self._judge_performance_sign(db, input)

        if input.sign_type == "입간판":
            return await self._judge_standing_sign(db, input)

        # 1. 용도지역 금지 유형 체크
        zone_check = await self._check_zone_prohibited(db, input)
        if zone_check:
            return zone_check

        # 2. 테헤란로 특수 조건 (돌출간판 절대 불가)
        if input.tehranro and input.sign_type == "돌출간판":
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                warnings=["테헤란로변 대지는 돌출간판 설치 불가 (지구단위계획 시행지침)"]
            )

        # 3. DB 규칙 매칭 (priority 순)
        rules = await self._fetch_matching_rules(db, input)
        if rules:
            condition, effect = rules[0]

            # 4. 규격 초과 체크 — 입력값이 허용 최대값을 초과하면 prohibited
            spec_check = self._check_spec(input, effect)
            if spec_check:
                return spec_check

            return JudgeResult(
                decision=effect.decision,
                review_type=effect.review_type,
                administrative_action=self._map_administrative_action(effect.decision),
                safety_check=effect.safety_check or False,
                max_area=float(effect.max_area) if effect.max_area else None,
                max_height=float(effect.max_height) if effect.max_height else None,
                max_protrusion=float(effect.max_protrusion) if effect.max_protrusion else None,
                max_width=float(effect.max_width) if effect.max_width else None,
                display_period=effect.display_period,
                warnings=effect.warnings or [],
                matched_rule_id=str(condition.id),
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )

        # 5. 기본값 (매칭 규칙 없음 → 신고 + 소심의)
        return JudgeResult(
            decision="report",
            review_type="소심의",
            administrative_action="report",
            display_period="3년",
            warnings=["해당 조건의 상세 규칙을 담당자가 직접 확인하세요."],
            fallback_reason="missing_rule",
        )

    async def _judge_projecting_sign(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> JudgeResult:
        prohibition_result = await self._run_projecting_sign_prohibition_checks(db, input)
        if prohibition_result:
            return prohibition_result

        context = await self._build_projecting_sign_context(db, input)
        if isinstance(context, JudgeResult):
            return context

        floor_check = self._check_projecting_sign_floor_and_height(input, context.effect)
        if floor_check:
            self._attach_projecting_sign_metadata(floor_check, context)
            return floor_check

        spec_violations = self._collect_projecting_sign_spec_violations(
            input,
            context.effect,
            context.exception_rule,
        )
        spec_violations.extend(
            self._collect_projecting_sign_clearance_violations(input, context.effect)
        )

        quantity_violation = self._check_projecting_sign_quantity(
            input,
            context.effect,
            context.sign_count_rule,
            context.exception_category,
        )
        if quantity_violation:
            return self._build_projecting_sign_failure(
                context.warnings + [quantity_violation],
                context,
            )

        safety_check = self._requires_projecting_sign_safety_check(input, context.effect)

        if spec_violations and not input.exception_review_approved:
            return self._build_projecting_sign_failure(
                context.warnings + spec_violations,
                context,
                safety_check=safety_check,
            )

        warnings = list(context.warnings)
        if spec_violations and input.exception_review_approved:
            warnings.extend(spec_violations)
            warnings.append("심의 특례 승인값을 근거로 규격 초과 항목을 예외 처리했습니다.")

        if context.exception_category == "medical":
            warnings.append("의료기관/약국 특례는 수량 규칙 완화 기준으로 우선 적용했습니다.")
        elif context.exception_category == "beauty":
            warnings.append("이·미용업 특례 규칙을 우선 적용했습니다.")

        return self._build_projecting_sign_success(
            input,
            context,
            warnings=warnings,
            safety_check=safety_check,
        )

    async def _judge_wall_sign_general_under_5f(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> JudgeResult:
        zone_check = await self._check_zone_prohibited(db, input)
        if zone_check:
            return zone_check

        # 5층 이하 일반 벽면이용간판: 6층 이상 설치는 규칙 존재 여부와 무관하게 불가
        if input.floor is not None and input.floor > 5:
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                warnings=["5층 이하 일반 벽면이용간판은 1층부터 5층까지만 설치할 수 있습니다."],
            )

        rules = await self._fetch_matching_rules(db, input)
        if not rules:
            return JudgeResult(
                decision="report",
                review_type="소심의",
                administrative_action="report",
                display_period="3년",
                warnings=["일반 벽면이용간판 규칙이 아직 정의되지 않아 확정 판정을 할 수 없습니다."],
                fallback_reason="missing_rule",
            )

        condition, effect = rules[0]
        spec_violations = self._collect_wall_sign_general_spec_violations(input)
        quantity_violation = self._check_wall_sign_general_quantity(input)

        if quantity_violation:
            spec_violations.append(quantity_violation)

        if spec_violations:
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                review_type=effect.review_type,
                max_area=float(effect.max_area) if effect.max_area else None,
                max_height=self._wall_sign_general_max_height(input.form_type),
                max_width=self._wall_sign_general_max_width(input),
                display_period=effect.display_period,
                warnings=spec_violations,
                matched_rule_id=str(condition.id),
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )

        warnings = list(effect.warnings or [])
        allowed_count = self._wall_sign_general_allowed_count(input)
        if allowed_count == 2:
            warnings.append("곡각지점 또는 전후면 도로 접면 조건으로 업소당 2개까지 허용할 수 있습니다.")

        if self._is_wall_sign_general_exempt_from_report(input):
            warnings.append("3층 이하, 면적 5㎡ 미만, 가로 10m 미만 조건을 충족해 무신고 가능 기준으로 처리했습니다.")
            return JudgeResult(
                decision="permit",
                administrative_action="none",
                review_type=None,
                max_area=5.0,
                max_height=self._wall_sign_general_max_height(input.form_type),
                max_width=self._wall_sign_general_max_width(input),
                display_period=effect.display_period,
                warnings=warnings,
                matched_rule_id=str(condition.id),
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )

        return JudgeResult(
            decision=effect.decision,
            administrative_action=effect.administrative_action or self._map_administrative_action(effect.decision),
            review_type=effect.review_type,
            max_area=float(effect.max_area) if effect.max_area else None,
            max_height=self._wall_sign_general_max_height(input.form_type),
            max_width=self._wall_sign_general_max_width(input),
            display_period=effect.display_period,
            warnings=warnings,
            matched_rule_id=str(condition.id),
            provision_id=str(effect.provision_id) if effect.provision_id else None,
        )

    async def _judge_wall_sign_top_building(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> JudgeResult:
        zone_check = await self._check_zone_prohibited(db, input)
        if zone_check:
            return zone_check

        # 건물 상단간판은 rule_condition의 floor 범위가 건물 층수 기준이므로
        # install floor 대신 building_floor_count로 조회
        lookup_input = input
        if input.building_floor_count is not None and input.building_floor_count != input.floor:
            from dataclasses import replace
            lookup_input = replace(input, floor=input.building_floor_count)
        rules = await self._fetch_matching_rules(db, lookup_input)
        if not rules:
            return JudgeResult(
                decision="report",
                review_type="대심의",
                administrative_action="permit",
                display_period="3년",
                warnings=["건물 상단간판 규칙이 아직 정의되지 않아 확정 판정을 할 수 없습니다."],
                fallback_reason="missing_rule",
            )

        condition, effect = rules[0]
        violations = self._collect_wall_sign_top_building_violations(input)
        max_width, max_height = self._wall_sign_top_building_max_specs(input)
        if input.sign_width is not None and max_width is not None and input.sign_width > max_width:
            violations.append(
                f"간판 가로 {input.sign_width}m가 허용 기준 {max_width}m를 초과합니다."
            )
        if input.sign_height is not None and max_height is not None and input.sign_height > max_height:
            violations.append(
                f"간판 세로 {input.sign_height}m가 허용 기준 {max_height}m를 초과합니다."
            )

        # DB effect.warnings는 일반 벽면이용간판 규격을 담고 있으므로 사용하지 않음
        # orientation에 따라 적용 조문이 다름
        if input.display_orientation == "vertical":
            # 제4조제1항제3호 다목: 세로로 길게 표시
            spec_notice = (
                f"가로 {max_width}m 이내, 세로 건물 높이의 1/2(최대 10m) 이내 "
                f"(서울시 조례 제4조제1항제3호 다목)"
            )
        else:
            # 제4조제1항제3호 나목: 가로로 길게 표시
            width_desc = f"건물 폭({input.building_width}m)의 1/2 이내" if input.building_width else "건물 폭의 1/2 이내"
            spec_notice = (
                f"가로 {width_desc}, 세로 3m 이내 "
                f"(서울시 조례 제4조제1항제3호 나목)"
            )
        warnings = [
            spec_notice,
            "건물 상단간판은 옥외광고심의위원회 심의가 필수입니다.",
        ]

        if violations:
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                review_type=effect.review_type or "대심의",
                safety_check=effect.safety_check or False,
                max_area=float(effect.max_area) if effect.max_area else None,
                max_height=max_height,
                max_width=max_width,
                display_period=effect.display_period,
                warnings=warnings + violations,
                matched_rule_id=str(condition.id),
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )

        return JudgeResult(
            decision=effect.decision,
            administrative_action=effect.administrative_action or "permit",
            review_type=effect.review_type or "대심의",
            safety_check=effect.safety_check or False,
            max_area=float(effect.max_area) if effect.max_area else None,
            max_height=max_height,
            max_width=max_width,
            display_period=effect.display_period,
            warnings=warnings,
            matched_rule_id=str(condition.id),
            provision_id=str(effect.provision_id) if effect.provision_id else None,
        )

    async def _judge_rooftop_sign(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> JudgeResult:
        zone_check = await self._check_zone_prohibited(db, input)
        if zone_check:
            return zone_check

        rules = await self._fetch_matching_rules(db, input)
        if not rules:
            return JudgeResult(
                decision="report",
                review_type="대심의",
                administrative_action="permit",
                display_period="3년",
                warnings=["옥상간판 규칙이 아직 정의되지 않아 확정 판정을 할 수 없습니다."],
                fallback_reason="missing_rule",
            )

        condition, effect = rules[0]
        violations: list[str] = []
        if input.building_floor_count is not None and input.building_floor_count > 15:
            violations.append("옥상간판은 15층 이하 건물 옥상에만 표시할 수 있습니다.")
        if (
            input.horizontal_distance_to_other_sign is not None
            and input.horizontal_distance_to_other_sign < 50
        ):
            violations.append(
                f"옥상간판 간 수평거리 {input.horizontal_distance_to_other_sign}m는 최소 기준 50m에 미달합니다."
            )
        if input.sign_height is not None and input.building_height is not None:
            half_height = input.building_height / 2
            if input.sign_height > half_height:
                violations.append(
                    f"옥상간판 높이 {input.sign_height}m가 건물 높이의 1/2 기준 {half_height}m를 초과합니다."
                )

        spec_check = self._check_spec(input, effect)
        if spec_check:
            violations.extend(spec_check.warnings)

        if violations:
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                review_type=effect.review_type,
                safety_check=effect.safety_check or False,
                max_height=float(effect.max_height) if effect.max_height else None,
                display_period=effect.display_period,
                warnings=violations,
                matched_rule_id=str(condition.id),
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )

        return JudgeResult(
            decision=effect.decision,
            administrative_action=effect.administrative_action or "permit",
            review_type=effect.review_type,
            safety_check=effect.safety_check or False,
            max_height=float(effect.max_height) if effect.max_height else None,
            display_period=effect.display_period,
            warnings=list(effect.warnings or []),
            matched_rule_id=str(condition.id),
            provision_id=str(effect.provision_id) if effect.provision_id else None,
        )

    async def _judge_performance_sign(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> JudgeResult:
        zone_check = await self._check_zone_prohibited(db, input)
        if zone_check:
            return zone_check

        rules = await self._fetch_matching_rules(db, input)
        if not rules:
            return JudgeResult(
                decision="report",
                review_type="대심의",
                administrative_action="permit",
                display_period="3년",
                warnings=["공연간판 규칙이 아직 정의되지 않아 확정 판정을 할 수 없습니다."],
                fallback_reason="missing_rule",
            )

        condition, effect = rules[0]
        violations: list[str] = []
        if input.has_performance_hall is False:
            violations.append("공연간판은 공연장이 있는 건물의 벽면에만 표시할 수 있습니다.")
        if input.building_width is not None and input.sign_width is not None:
            max_width = input.building_width / 3
            if input.sign_width > max_width:
                violations.append(
                    f"공연간판 가로 {input.sign_width}m가 해당 벽면 가로폭의 1/3 기준 {max_width}m를 초과합니다."
                )

        spec_check = self._check_spec(input, effect)
        if spec_check:
            violations.extend(spec_check.warnings)

        if violations:
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                review_type=effect.review_type,
                max_protrusion=float(effect.max_protrusion) if effect.max_protrusion else None,
                display_period=effect.display_period,
                warnings=list(effect.warnings or []) + violations,
                matched_rule_id=str(condition.id),
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )

        return JudgeResult(
            decision=effect.decision,
            administrative_action=effect.administrative_action or "permit",
            review_type=effect.review_type,
            max_protrusion=float(effect.max_protrusion) if effect.max_protrusion else None,
            display_period=effect.display_period,
            warnings=list(effect.warnings or []),
            matched_rule_id=str(condition.id),
            provision_id=str(effect.provision_id) if effect.provision_id else None,
        )

    async def _judge_standing_sign(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> JudgeResult:
        zone_check = await self._check_zone_prohibited(db, input)
        if zone_check:
            return zone_check

        rules = await self._fetch_matching_rules(db, input)
        if not rules:
            return JudgeResult(
                decision="report",
                review_type="소심의",
                administrative_action="report",
                display_period="1년",
                warnings=["입간판 규칙이 아직 정의되지 않아 확정 판정을 할 수 없습니다."],
                fallback_reason="missing_rule",
            )

        condition, effect = rules[0]
        spec_check = self._check_spec(input, effect)
        violations = list(spec_check.warnings) if spec_check else []
        if input.base_width is not None and input.base_width > 0.5:
            violations.append(f"입간판 바닥면 가로 {input.base_width}m가 허용 기준 0.5m를 초과합니다.")
        if input.base_depth is not None and input.base_depth > 0.7:
            violations.append(f"입간판 바닥면 세로 {input.base_depth}m가 허용 기준 0.7m를 초과합니다.")
        if input.distance_from_building is not None and input.distance_from_building > 1.0:
            violations.append(
                f"입간판 설치 거리가 건물면으로부터 {input.distance_from_building}m로 허용 기준 1m를 초과합니다."
            )
        if input.has_sidewalk:
            violations.append("입간판은 보행자 통로에 설치할 수 없습니다.")

        if violations:
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                review_type=effect.review_type,
                max_area=float(effect.max_area) if effect.max_area else None,
                max_height=float(effect.max_height) if effect.max_height else None,
                display_period=effect.display_period,
                warnings=violations,
                matched_rule_id=str(condition.id),
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )

        return JudgeResult(
            decision=effect.decision,
            administrative_action=effect.administrative_action or self._map_administrative_action(effect.decision),
            review_type=effect.review_type,
            max_area=float(effect.max_area) if effect.max_area else None,
            max_height=float(effect.max_height) if effect.max_height else None,
            display_period=effect.display_period,
            warnings=list(effect.warnings or []),
            matched_rule_id=str(condition.id),
            provision_id=str(effect.provision_id) if effect.provision_id else None,
        )

    async def _run_projecting_sign_prohibition_checks(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> Optional[JudgeResult]:
        zone_check = await self._check_zone_prohibited(db, input)
        if zone_check:
            return zone_check
        return await self._check_special_zone_restriction(db, input)

    async def _build_projecting_sign_context(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> ProjectingSignContext | JudgeResult:
        exception_category = self._get_projecting_sign_exception_category(input.business_category)
        exception_rule = await self._get_projecting_sign_exception_rule(
            db,
            input.sign_type,
            exception_category,
        )
        sign_count_rule = await self._get_projecting_sign_sign_count_rule(
            db,
            input.sign_type,
            exception_category,
        )

        rules = await self._fetch_matching_rules(db, input, sign_type_override="돌출간판")
        if not rules:
            return JudgeResult(
                decision="report",
                review_type="소심의",
                administrative_action="report",
                display_period="3년",
                warnings=["돌출간판 규칙이 아직 정의되지 않아 확정 판정을 할 수 없습니다."],
                fallback_reason="missing_rule",
            )

        condition, effect = rules[0]
        warnings, review_type = self._merge_projecting_sign_rule_context(
            effect,
            exception_rule,
            sign_count_rule,
        )
        return ProjectingSignContext(
            condition=condition,
            effect=effect,
            warnings=warnings,
            review_type=review_type,
            exception_category=exception_category,
            exception_rule=exception_rule,
            sign_count_rule=sign_count_rule,
        )

    def _merge_projecting_sign_rule_context(
        self,
        effect,
        exception_rule: Optional[IndustryExceptionRule],
        sign_count_rule: Optional[SignCountRule],
    ) -> tuple[list[str], Optional[str]]:
        warnings = list(effect.warnings or [])
        review_type = effect.review_type
        if exception_rule:
            warnings.extend(exception_rule.warnings or [])
            if exception_rule.review_type:
                review_type = exception_rule.review_type
        if sign_count_rule:
            warnings.extend(getattr(sign_count_rule, "warnings", []) or [])
        return warnings, review_type

    def _collect_projecting_sign_clearance_violations(
        self,
        input: JudgeInput,
        effect,
    ) -> list[str]:
        violation = self._check_projecting_sign_clearance(input, effect)
        return [violation] if violation else []

    def _attach_projecting_sign_metadata(
        self,
        result: JudgeResult,
        context: ProjectingSignContext,
    ) -> JudgeResult:
        result.review_type = context.review_type
        result.display_period = context.effect.display_period
        result.matched_rule_id = str(context.condition.id)
        result.provision_id = (
            str(context.effect.provision_id) if context.effect.provision_id else None
        )
        return result

    def _build_projecting_sign_success(
        self,
        input: JudgeInput,
        context: ProjectingSignContext,
        *,
        warnings: list[str],
        safety_check: bool,
    ) -> JudgeResult:
        effect = context.effect
        return JudgeResult(
            decision=effect.decision,
            review_type="심의특례" if input.exception_review_approved else context.review_type,
            administrative_action=self._map_administrative_action(effect.decision),
            safety_check=safety_check,
            max_area=float(effect.max_area) if effect.max_area else None,
            max_height=self._projecting_sign_max_height(input, effect),
            max_protrusion=float(effect.max_protrusion) if effect.max_protrusion else 1.0,
            max_width=float(effect.max_width) if effect.max_width else None,
            display_period=effect.display_period,
            warnings=warnings,
            matched_rule_id=str(context.condition.id),
            provision_id=str(effect.provision_id) if effect.provision_id else None,
        )

    def _check_missing_input(self, input: JudgeInput) -> Optional[JudgeResult]:
        missing_fields = self._collect_missing_fields(input)
        if not missing_fields:
            return None

        return JudgeResult(
            decision="report",
            administrative_action="report",
            warnings=["필수 입력이 부족하여 확정 판정을 할 수 없습니다."],
            missing_fields=missing_fields,
            fallback_reason="missing_input",
        )

    def _collect_missing_fields(self, input: JudgeInput) -> list[str]:
        required_fields_by_sign_type: dict[str, tuple[str, ...]] = {
            "돌출간판": (
                "height",
                "width",
                "protrusion",
                "thickness",
                "bottom_clearance",
                "top_height_from_ground",
                "face_area",
                "building_height",
                "floor_height",
                "existing_sign_count_for_business",
                "has_sidewalk",
                "exception_review_approved",
            ),
            "벽면이용간판": ("install_subtype",),
            "옥상간판": ("sign_height", "building_height", "building_floor_count", "horizontal_distance_to_other_sign"),
            "지주이용간판": ("vendor_count", "sign_height"),
            "공연간판": ("vendor_count", "protrusion", "sign_width", "building_width", "has_performance_hall"),
            "입간판": ("has_sidewalk", "sign_height", "base_width", "base_depth", "distance_from_building"),
            "현수막": ("sign_width", "sign_height"),
            "애드벌룬": ("sign_height", "building_height"),
            "애드벌룬(지면)": ("sign_height",),
            "창문이용광고물": ("sign_width", "sign_height"),
        }
        required_fields = list(required_fields_by_sign_type.get(input.sign_type, ()))
        if (
            input.sign_type == "벽면이용간판"
            and input.install_subtype == "wall_sign_general_under_5f"
        ):
            required_fields.extend(
                (
                    "form_type",
                    "shop_front_width",
                    "sign_width",
                    "sign_height",
                    "sign_area",
                    "is_corner_lot",
                    "has_front_and_rear_roads",
                    "existing_sign_count_for_business",
                )
            )
        if (
            input.sign_type == "벽면이용간판"
            and input.install_subtype == "wall_sign_top_building"
        ):
            required_fields.extend(
                (
                    "form_type",
                    "content_type",
                    "display_orientation",
                    "building_floor_count",
                    "install_at_top_floor",
                    "building_width",
                    "building_height",
                    "requested_faces",
                    "sign_width",
                    "sign_height",
                )
            )
        return [
            field_name for field_name in required_fields
            if getattr(input, field_name) is None
        ]

    def _wall_sign_general_allowed_count(self, input: JudgeInput) -> int:
        if input.is_corner_lot or input.has_front_and_rear_roads:
            return 2
        return 1

    def _wall_sign_general_max_width(self, input: JudgeInput) -> Optional[float]:
        if input.shop_front_width is None:
            return None
        return min(input.shop_front_width * 0.8, 10.0)

    def _wall_sign_general_max_height(self, form_type: Optional[str]) -> Optional[float]:
        if form_type == "plate":
            return 0.8
        if form_type == "solid":
            return 0.45
        return None

    def _collect_wall_sign_general_spec_violations(self, input: JudgeInput) -> list[str]:
        violations: list[str] = []
        if input.floor < 1 or input.floor > 5:
            violations.append("5층 이하 일반 벽면이용간판은 1층부터 5층까지만 설치할 수 있습니다.")

        if input.form_type not in {"plate", "solid"}:
            violations.append("일반 벽면이용간판 형태는 plate 또는 solid 중 하나여야 합니다.")
            return violations

        if input.floor >= 4 and input.form_type != "solid":
            violations.append("4층 이상 일반 벽면이용간판은 입체형만 허용됩니다.")

        max_width = self._wall_sign_general_max_width(input)
        if max_width is not None and input.sign_width is not None and input.sign_width > max_width:
            violations.append(
                f"간판 가로 {input.sign_width}m가 허용 기준 {max_width}m를 초과합니다."
            )

        max_height = self._wall_sign_general_max_height(input.form_type)
        if max_height is not None and input.sign_height is not None and input.sign_height > max_height:
            violations.append(
                f"간판 세로 {input.sign_height}m가 허용 기준 {max_height}m를 초과합니다."
            )

        return violations

    def _check_wall_sign_general_quantity(self, input: JudgeInput) -> Optional[str]:
        allowed_count = self._wall_sign_general_allowed_count(input)
        existing_count = input.existing_sign_count_for_business or 0
        if existing_count >= allowed_count:
            return (
                f"업소당 허용 간판 수 {allowed_count}개를 초과했습니다. "
                f"현재 기설치 간판 수는 {existing_count}개입니다."
            )
        return None

    def _is_wall_sign_general_exempt_from_report(self, input: JudgeInput) -> bool:
        return (
            input.floor <= 3
            and (input.sign_area or 0) < 5
            and (input.sign_width or 0) < 10
        )

    def _collect_wall_sign_top_building_violations(self, input: JudgeInput) -> list[str]:
        violations: list[str] = []
        if (input.building_floor_count or 0) < 4:
            violations.append("건물 상단간판은 4층 이상 건물에만 설치할 수 있습니다.")
        if not input.install_at_top_floor:
            violations.append("건물 상단간판은 최상단 위치에만 설치할 수 있습니다.")
        if input.form_type != "solid":
            violations.append("건물 상단간판은 입체형만 허용됩니다.")
        if (input.requested_faces or 0) > 3:
            violations.append("건물 상단간판은 최대 3면까지만 허용됩니다.")
        if (input.requested_faces or 0) < 1:
            violations.append("건물 상단간판은 최소 1면 이상 신청해야 합니다.")
        if input.display_orientation not in {"horizontal", "vertical"}:
            violations.append("건물 상단간판 표시 방향은 horizontal 또는 vertical 이어야 합니다.")
        if input.content_type not in {"building_name", "business_name", "symbol"}:
            violations.append("건물 상단간판 표시 내용은 건물명, 상호, 상징 도형만 허용됩니다.")
        # 아랫부분 4층 이상 위치 검증 (제4조제1항제3호 다항)
        if (
            input.building_height is not None
            and input.building_floor_count is not None
            and input.building_floor_count >= 4
            and input.sign_height is not None
        ):
            avg_floor_height = input.building_height / input.building_floor_count
            sign_bottom_height = input.building_height - input.sign_height
            fourth_floor_height = 3 * avg_floor_height  # 4층 바닥 = 3개 층 높이
            if sign_bottom_height < fourth_floor_height:
                violations.append(
                    f"간판 아랫부분이 4층 미만({sign_bottom_height:.1f}m)에 위치합니다. "
                    f"4층 높이({fourth_floor_height:.1f}m) 이상이어야 합니다."
                )
        return violations

    def _wall_sign_top_building_max_specs(self, input: JudgeInput) -> tuple[Optional[float], Optional[float]]:
        if input.display_orientation == "vertical":
            # 서울시 조례 제4조제1항제3호 다목 (세로로 길게 표시)
            # 가로: 2m 이내, 세로: 건물 높이의 1/2 이내 최대 10m
            max_width = 2.0
            if input.building_height is None:
                return max_width, None
            max_height = min(input.building_height / 2, 10.0)
            return max_width, max_height
        else:
            # 서울시 조례 제4조제1항제3호 나목 (가로로 길게 표시, horizontal)
            # 가로: 건물 폭의 1/2 이내, 세로: 3m 이내
            max_width = (input.building_width / 2) if input.building_width is not None else None
            max_height = 3.0
            return max_width, max_height

    def _map_administrative_action(self, decision: str) -> Optional[str]:
        if decision in {"permit", "report"}:
            return decision
        return None

    def _get_projecting_sign_exception_category(
        self,
        business_category: Optional[str],
    ) -> Optional[str]:
        if not business_category:
            return None

        normalized = business_category.replace("·", "").replace(" ", "")
        if any(keyword in normalized for keyword in ("미용", "이용")):
            return "beauty"
        if any(keyword in normalized for keyword in ("의료", "병원", "의원", "치과", "한의원", "약국")):
            return "medical"
        return None

    def _check_projecting_sign_floor_and_height(
        self,
        input: JudgeInput,
        effect,
    ) -> Optional[JudgeResult]:
        if input.floor > 5:
            return JudgeResult(
                decision="prohibited",
                warnings=["돌출간판은 5층 이하에만 설치할 수 있습니다."],
            )

        max_top_height_relative_building = self._get_effect_float(
            effect,
            "max_top_height_relative_building",
            0.0,
        )
        if (
            input.top_height_from_ground is not None
            and input.building_height is not None
            and input.top_height_from_ground
            > input.building_height + max_top_height_relative_building
        ):
            return JudgeResult(
                decision="prohibited",
                warnings=["간판 윗부분이 건물 높이를 초과할 수 없습니다."],
            )
        max_top_height_from_ground = self._get_effect_float(
            effect,
            "max_top_height_from_ground",
        )
        if (
            max_top_height_from_ground is not None
            and input.top_height_from_ground is not None
            and input.top_height_from_ground > max_top_height_from_ground
        ):
            return JudgeResult(
                decision="prohibited",
                warnings=[
                    (
                        f"간판 윗부분 높이 {input.top_height_from_ground}m가 "
                        f"허용 기준 {max_top_height_from_ground}m를 초과합니다."
                    )
                ],
            )
        return None

    def _projecting_sign_max_height(self, input: JudgeInput, effect) -> float:
        effect_max_height = float(effect.max_height) if effect.max_height else 3.5
        floor_height_limit = input.floor_height if input.floor_height is not None else effect_max_height
        return min(effect_max_height, floor_height_limit)

    def _collect_projecting_sign_spec_violations(
        self,
        input: JudgeInput,
        effect,
        exception_rule=None,
    ) -> list[str]:
        violations: list[str] = []
        max_height = self._projecting_sign_max_height(input, effect)
        if exception_rule and getattr(exception_rule, "max_height", None) is not None:
            max_height = min(max_height, float(exception_rule.max_height))
        max_protrusion = float(effect.max_protrusion) if effect.max_protrusion else 1.0
        if exception_rule and getattr(exception_rule, "max_protrusion", None) is not None:
            max_protrusion = float(exception_rule.max_protrusion)

        if input.height is not None and input.height > max_height:
            violations.append(
                f"세로 길이 {input.height}m가 허용 기준 {max_height}m를 초과합니다."
            )

        if input.protrusion is not None and input.protrusion > max_protrusion:
            violations.append(
                f"돌출폭 {input.protrusion}m가 허용 기준 {max_protrusion}m를 초과합니다."
            )

        max_thickness = self._get_effect_float(effect, "max_thickness", 0.30)
        if exception_rule and getattr(exception_rule, "max_thickness", None) is not None:
            max_thickness = float(exception_rule.max_thickness)
        if (
            input.thickness is not None
            and input.thickness > max_thickness
        ):
            violations.append(
                f"두께 {input.thickness}m가 허용 기준 {max_thickness}m를 초과합니다."
            )

        return violations

    def _check_projecting_sign_clearance(self, input: JudgeInput, effect) -> Optional[str]:
        if input.bottom_clearance is None or input.has_sidewalk is None:
            return None

        minimum_clearance = (
            self._get_effect_float(effect, "min_bottom_clearance", 3.0)
            if input.has_sidewalk
            else self._get_effect_float(
                effect,
                "min_bottom_clearance_no_sidewalk",
                4.0,
            )
        )
        if input.bottom_clearance < minimum_clearance:
            location_label = "보도 있음" if input.has_sidewalk else "보도 없음"
            return (
                f"{location_label} 기준 지면 이격 {input.bottom_clearance}m는 "
                f"최소 기준 {minimum_clearance}m에 미달합니다."
            )
        return None

    def _check_projecting_sign_quantity(
        self,
        input: JudgeInput,
        effect,
        sign_count_rule,
        exception_category: Optional[str],
    ) -> Optional[str]:
        max_count = 2 if exception_category in {"beauty", "medical"} else 1
        requires_no_existing_wall_sign = bool(
            getattr(effect, "requires_no_existing_wall_sign", False)
        )
        if sign_count_rule:
            max_count = int(sign_count_rule.max_count_per_business)
            requires_no_existing_wall_sign = bool(
                getattr(sign_count_rule, "requires_no_existing_wall_sign", False)
            )
        else:
            effect_max_count = self._get_effect_int(effect, "max_count_per_business")
            if effect_max_count is not None:
                max_count = effect_max_count

        existing_count = input.existing_sign_count_for_business or 0
        if existing_count >= max_count:
            return (
                f"업소당 허용 간판 수 {max_count}개를 초과했습니다. "
                f"현재 기설치 간판 수는 {existing_count}개입니다."
            )

        if (
            "벽면이용간판" in (input.existing_sign_types or [])
            and requires_no_existing_wall_sign
            and exception_category not in {"beauty", "medical"}
        ):
            return "기존 벽면이용간판이 있는 경우 돌출간판 총량 기준을 추가로 검토해야 합니다."

        return None

    def _requires_projecting_sign_safety_check(self, input: JudgeInput, effect) -> bool:
        if input.top_height_from_ground is None or input.face_area is None:
            return False
        minimum_height = self._get_effect_float(effect, "safety_check_min_height", 5.0)
        minimum_area = self._get_effect_float(effect, "safety_check_min_area", 1.0)
        return (
            input.top_height_from_ground >= minimum_height
            and input.face_area >= minimum_area
        )

    def _build_projecting_sign_failure(
        self,
        warnings: list[str],
        context: ProjectingSignContext,
        *,
        safety_check: bool = False,
    ) -> JudgeResult:
        effect = context.effect
        return JudgeResult(
            decision="prohibited",
            review_type=context.review_type or effect.review_type,
            administrative_action=None,
            safety_check=safety_check,
            max_area=float(effect.max_area) if effect.max_area else None,
            max_height=self._get_effect_float(effect, "max_height"),
            max_protrusion=self._get_effect_float(effect, "max_protrusion"),
            max_width=float(effect.max_width) if effect.max_width else None,
            display_period=effect.display_period,
            warnings=warnings,
            matched_rule_id=str(context.condition.id),
            provision_id=str(effect.provision_id) if effect.provision_id else None,
        )

    def _generic_height_label(self, sign_type: str) -> str:
        return {
            "옥상간판": "간판 높이",
            "지주이용간판": "간판 높이",
            "입간판": "간판 윗부분 높이",
            "현수막": "세로 길이",
            "애드벌룬": "애드벌룬 높이",
            "애드벌룬(지면)": "애드벌룬 높이",
            "창문이용광고물": "세로 길이",
        }.get(sign_type, "간판 높이")

    def _generic_width_label(self, sign_type: str) -> str:
        return {
            "입간판": "간판 가로",
            "현수막": "가로 길이",
            "창문이용광고물": "가로 길이",
        }.get(sign_type, "간판 가로")

    def _collect_generic_spec_violations(
        self,
        input: JudgeInput,
        effect,
    ) -> list[str]:
        warnings: list[str] = []

        if effect.max_area and Decimal(str(input.area)) > effect.max_area:
            warnings.append(
                f"면적 {input.area}㎡이 허용 최대 {float(effect.max_area)}㎡를 초과하여 설치 불가"
            )

        if effect.max_height and input.sign_height is not None:
            max_height = float(effect.max_height)
            if input.sign_height > max_height:
                warnings.append(
                    f"{self._generic_height_label(input.sign_type)} {input.sign_height}m가 "
                    f"허용 기준 {max_height}m를 초과합니다."
                )

        if effect.max_width and input.sign_width is not None:
            max_width = float(effect.max_width)
            if input.sign_width > max_width:
                warnings.append(
                    f"{self._generic_width_label(input.sign_type)} {input.sign_width}m가 "
                    f"허용 기준 {max_width}m를 초과합니다."
                )

        if effect.max_protrusion and input.protrusion is not None:
            max_protrusion = float(effect.max_protrusion)
            if input.protrusion > max_protrusion:
                warnings.append(
                    f"돌출폭 {input.protrusion}m가 허용 기준 {max_protrusion}m를 초과합니다."
                )

        if (
            input.sign_type == "애드벌룬"
            and input.sign_height is not None
            and input.building_height is not None
        ):
            building_half_limit = input.building_height / 2
            if input.sign_height > building_half_limit:
                warnings.append(
                    f"애드벌룬 높이 {input.sign_height}m가 건물 높이의 1/2 기준 "
                    f"{building_half_limit}m를 초과합니다."
                )

        return warnings

    def _check_spec(self, input: JudgeInput, effect) -> Optional[JudgeResult]:
        """규격 초과 체크 — 입력 규격이 허용 최대값을 초과하면 prohibited 반환"""
        warnings = self._collect_generic_spec_violations(input, effect)
        if warnings:
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                warnings=warnings,
                provision_id=str(effect.provision_id) if effect.provision_id else None,
            )
        return None

    async def _check_zone_prohibited(
        self, db: AsyncSession, input: JudgeInput
    ) -> Optional[JudgeResult]:
        result = await db.execute(
            select(ZoneRule).where(ZoneRule.name == input.zone)
        )
        zone = result.scalar_one_or_none()
        if zone and input.sign_type in (zone.prohibited_types or []):
            return JudgeResult(
                decision="prohibited",
                administrative_action=None,
                warnings=[f"{input.zone}에서 {input.sign_type} 설치 불가"]
            )
        return None

    async def _check_special_zone_restriction(
        self,
        db: AsyncSession,
        input: JudgeInput,
    ) -> Optional[JudgeResult]:
        special_zone = input.special_zone or ("tehranro" if input.tehranro else None)
        if not special_zone:
            return None

        stmt = (
            select(SpecialZoneRule)
            .where(SpecialZoneRule.sign_type == input.sign_type)
            .where(SpecialZoneRule.special_zone == special_zone)
            .order_by(SpecialZoneRule.priority.asc())
        )
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
        if not rule:
            return None

        return JudgeResult(
            decision=rule.decision,
            review_type=rule.review_type,
            administrative_action=rule.administrative_action,
            warnings=list(rule.warnings or []),
            provision_id=str(rule.provision_id) if rule.provision_id else None,
        )

    async def _get_projecting_sign_exception_rule(
        self,
        db: AsyncSession,
        sign_type: str,
        exception_category: Optional[str],
    ) -> Optional[IndustryExceptionRule]:
        if not exception_category:
            return None

        stmt = (
            select(IndustryExceptionRule)
            .where(IndustryExceptionRule.sign_type == sign_type)
            .where(IndustryExceptionRule.exception_type == exception_category)
            .order_by(IndustryExceptionRule.priority.asc())
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_projecting_sign_sign_count_rule(
        self,
        db: AsyncSession,
        sign_type: str,
        exception_category: Optional[str],
    ) -> Optional[SignCountRule]:
        stmt = (
            select(SignCountRule)
            .where(SignCountRule.sign_type == sign_type)
            .where(
                or_(
                    SignCountRule.exception_type.is_(None),
                    SignCountRule.exception_type == exception_category,
                )
            )
            .order_by(SignCountRule.priority.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def _fetch_matching_rules(
        self,
        db: AsyncSession,
        input: JudgeInput,
        *,
        sign_type_override: Optional[str] = None,
    ) -> list[tuple[RuleCondition, RuleEffect]]:
        """조건에 맞는 규칙을 priority 순으로 반환"""
        stmt = (
            select(RuleCondition, RuleEffect)
            .join(RuleEffect, RuleCondition.id == RuleEffect.rule_id)
            .where(RuleCondition.sign_type == (sign_type_override or input.sign_type))
            .where(
                or_(
                    RuleCondition.install_subtype.is_(None),
                    RuleCondition.install_subtype == input.install_subtype,
                )
            )
            .where(
                or_(RuleCondition.floor_min.is_(None),
                    RuleCondition.floor_min <= input.floor)
            )
            .where(
                or_(RuleCondition.floor_max.is_(None),
                    RuleCondition.floor_max >= input.floor)
            )
            .where(
                or_(RuleCondition.area_min.is_(None),
                    RuleCondition.area_min <= Decimal(str(input.area)))
            )
            .where(
                or_(RuleCondition.area_max.is_(None),
                    RuleCondition.area_max >= Decimal(str(input.area)))
            )
            .where(
                or_(RuleCondition.light_type.is_(None),
                    RuleCondition.light_type == input.light_type)
            )
            .where(
                or_(RuleCondition.zone.is_(None),
                    RuleCondition.zone == input.zone)
            )
            .where(
                or_(RuleCondition.ad_type.is_(None),
                    RuleCondition.ad_type == input.ad_type,
                    RuleCondition.ad_type == 'both')
            )
            .where(
                or_(RuleCondition.tehranro.is_(None),
                    RuleCondition.tehranro == input.tehranro)
            )
            .where(
                or_(RuleCondition.has_sidewalk.is_(None),
                    RuleCondition.has_sidewalk == input.has_sidewalk)
            )
            .where(
                or_(RuleCondition.exception_review_approved.is_(None),
                    RuleCondition.exception_review_approved == input.exception_review_approved)
            )
            .order_by(RuleCondition.priority.asc())
        )
        result = await db.execute(stmt)
        return result.all()

    def _get_effect_float(
        self,
        effect,
        attribute: str,
        default: Optional[float] = None,
    ) -> Optional[float]:
        value = getattr(effect, attribute, None)
        if value is None:
            return default
        return float(value)

    def _get_effect_int(
        self,
        effect,
        attribute: str,
        default: Optional[int] = None,
    ) -> Optional[int]:
        value = getattr(effect, attribute, None)
        if value is None:
            return default
        return int(value)
