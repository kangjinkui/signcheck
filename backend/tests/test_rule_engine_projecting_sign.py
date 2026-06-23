import os
import sys
import types
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

db_module = types.ModuleType("db")
db_models_module = types.ModuleType("db.models")


class RuleCondition:
    pass


class RuleEffect:
    pass


class ZoneRule:
    pass


class IndustryExceptionRule:
    pass


class SignCountRule:
    pass


class SpecialZoneRule:
    pass


db_models_module.RuleCondition = RuleCondition
db_models_module.RuleEffect = RuleEffect
db_models_module.ZoneRule = ZoneRule
db_models_module.IndustryExceptionRule = IndustryExceptionRule
db_models_module.SignCountRule = SignCountRule
db_models_module.SpecialZoneRule = SpecialZoneRule
db_module.models = db_models_module
sys.modules.setdefault("db", db_module)
sys.modules.setdefault("db.models", db_models_module)

from engine.rule_engine import JudgeInput, RuleEngine  # noqa: E402


def make_input(**overrides):
    data = {
        "sign_type": "돌출간판",
        "floor": 3,
        "area": 1.2,
        "light_type": "none",
        "zone": "일반상업지역",
        "ad_type": "self",
        "tehranro": False,
        "has_sidewalk": True,
        "business_category": "일반음식점",
        "height": 2.5,
        "width": 0.8,
        "protrusion": 0.8,
        "thickness": 0.25,
        "bottom_clearance": 3.2,
        "top_height_from_ground": 4.8,
        "face_area": 0.9,
        "building_height": 20.0,
        "floor_height": 3.5,
        "existing_sign_count_for_business": 0,
        "existing_sign_types": [],
        "exception_review_approved": False,
    }
    data.update(overrides)
    return JudgeInput(**data)


def make_effect(**overrides):
    data = {
        "decision": "permit",
        "administrative_action": "permit",
        "review_type": "소심의",
        "safety_check": False,
        "max_area": None,
        "max_height": 3.0,
        "max_protrusion": 1.0,
        "max_width": None,
        "max_thickness": 0.30,
        "min_bottom_clearance": 3.0,
        "min_bottom_clearance_no_sidewalk": 4.0,
        "max_top_height_relative_building": 0.0,
        "max_top_height_from_ground": None,
        "max_count_per_business": 1,
        "requires_no_existing_wall_sign": True,
        "requires_alignment": False,
        "safety_check_min_height": 5.0,
        "safety_check_min_area": 1.0,
        "display_period": "3년",
        "warnings": ["기본 돌출간판 규칙"],
        "provision_id": uuid.uuid4(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_condition():
    return SimpleNamespace(id=uuid.uuid4())


class ProjectingSignRuleEngineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = RuleEngine()
        self.db = object()

    async def _run_judge(self, input_data, effect=None, fetch_side_effect=None):
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)
        self.engine._check_special_zone_restriction = AsyncMock(return_value=None)
        self.engine._get_projecting_sign_exception_rule = AsyncMock(return_value=None)
        self.engine._get_projecting_sign_sign_count_rule = AsyncMock(return_value=None)
        if fetch_side_effect is not None:
            self.engine._fetch_matching_rules = AsyncMock(side_effect=fetch_side_effect)
        else:
            self.engine._fetch_matching_rules = AsyncMock(
                return_value=[(make_condition(), effect or make_effect())]
            )
        return await self.engine.judge(self.db, input_data)

    async def test_projecting_sign_permit_under_limits(self):
        result = await self._run_judge(make_input())
        self.assertEqual(result.decision, "permit")
        self.assertEqual(result.administrative_action, "permit")
        self.assertFalse(result.safety_check)

    async def test_projecting_sign_prohibited_over_sixth_floor(self):
        result = await self._run_judge(make_input(floor=6))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("5층 이하", result.warnings[0])

    async def test_projecting_sign_prohibited_when_protrusion_exceeds_limit(self):
        result = await self._run_judge(make_input(protrusion=1.2))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("돌출폭 1.2m", result.warnings[-1])

    async def test_projecting_sign_prohibited_when_width_exceeds_protrusion_limit(self):
        result = await self._run_judge(make_input(width=3.0))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("가로 길이 3.0m", result.warnings[-1])

    async def test_projecting_sign_prohibited_when_height_exceeds_limit(self):
        result = await self._run_judge(make_input(height=3.3))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("세로 길이 3.3m", result.warnings[-1])

    async def test_projecting_sign_prohibited_when_thickness_exceeds_rule_effect(self):
        effect = make_effect(max_thickness=0.20)
        result = await self._run_judge(make_input(thickness=0.25), effect=effect)
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("두께 0.25m", result.warnings[-1])

    async def test_projecting_sign_prohibited_when_clearance_with_sidewalk_is_low(self):
        result = await self._run_judge(make_input(bottom_clearance=2.8))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("보도 있음", result.warnings[-1])

    async def test_projecting_sign_prohibited_when_clearance_without_sidewalk_is_low(self):
        result = await self._run_judge(
            make_input(has_sidewalk=False, bottom_clearance=3.5)
        )
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("보도 없음", result.warnings[-1])

    async def test_projecting_sign_prohibited_when_business_count_exceeds_limit(self):
        result = await self._run_judge(make_input(existing_sign_count_for_business=1))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("업소당 허용 간판 수 1개", result.warnings[-1])

    async def test_projecting_sign_prohibited_when_existing_wall_sign_conflicts(self):
        result = await self._run_judge(
            make_input(existing_sign_types=["벽면이용간판"])
        )
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("기존 벽면이용간판", result.warnings[-1])

    async def test_projecting_sign_prohibited_in_tehranro(self):
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)
        self.engine._check_special_zone_restriction = AsyncMock(
            return_value=SimpleNamespace(
                decision="prohibited",
                review_type=None,
                administrative_action=None,
                warnings=["테헤란로변 대지는 돌출간판 설치 불가"],
                provision_id=None,
            )
        )
        result = await self.engine.judge(self.db, make_input(tehranro=True))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("테헤란로변", result.warnings[0])

    async def test_projecting_sign_beauty_exception_uses_exception_rule(self):
        beauty_exception = SimpleNamespace(
            max_height=0.8,
            max_protrusion=0.5,
            max_thickness=None,
            review_type=None,
            warnings=["이미용 특례"],
        )
        beauty_sign_count = SimpleNamespace(
            max_count_per_business=2,
            requires_no_existing_wall_sign=False,
            warnings=[],
        )

        self.engine._check_zone_prohibited = AsyncMock(return_value=None)
        self.engine._check_special_zone_restriction = AsyncMock(return_value=None)
        self.engine._get_projecting_sign_exception_rule = AsyncMock(return_value=beauty_exception)
        self.engine._get_projecting_sign_sign_count_rule = AsyncMock(return_value=beauty_sign_count)
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect())]
        )
        result = await self.engine.judge(
            self.db,
            make_input(
                business_category="미용실",
                height=0.7,
                width=0.4,
                protrusion=0.4,
                existing_sign_count_for_business=1,
            ),
        )
        self.assertEqual(result.decision, "permit")
        self.assertIn("이·미용업 특례", result.warnings[-1])

    async def test_projecting_sign_medical_exception_allows_existing_wall_sign(self):
        medical_sign_count = SimpleNamespace(
            max_count_per_business=2,
            requires_no_existing_wall_sign=False,
            warnings=[],
        )
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)
        self.engine._check_special_zone_restriction = AsyncMock(return_value=None)
        self.engine._get_projecting_sign_exception_rule = AsyncMock(return_value=None)
        self.engine._get_projecting_sign_sign_count_rule = AsyncMock(return_value=medical_sign_count)
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect())]
        )
        result = await self.engine.judge(
            self.db,
            make_input(
                business_category="치과의원",
                existing_sign_types=["벽면이용간판"],
            ),
        )
        self.assertEqual(result.decision, "permit")
        self.assertIn("의료기관/약국 특례", result.warnings[-1])

    async def test_projecting_sign_special_zone_rule_blocks_tehranro(self):
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)
        self.engine._check_special_zone_restriction = AsyncMock(
            return_value=SimpleNamespace(
                decision="prohibited",
                review_type=None,
                administrative_action=None,
                warnings=["테헤란로 특수구역 금지"],
                provision_id=None,
            )
        )
        result = await self.engine.judge(self.db, make_input(tehranro=True))
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("테헤란로", result.warnings[0])

    async def test_projecting_sign_sets_safety_check_from_rule_effect_threshold(self):
        result = await self._run_judge(
            make_input(top_height_from_ground=5.2, face_area=1.1)
        )
        self.assertTrue(result.safety_check)

    async def test_projecting_sign_exception_review_approved_allows_spec_violation(self):
        result = await self._run_judge(
            make_input(height=3.2, exception_review_approved=True)
        )
        self.assertEqual(result.decision, "permit")
        self.assertEqual(result.review_type, "심의특례")
        self.assertIn("심의 특례 승인값", result.warnings[-1])

    async def test_projecting_sign_exception_review_missing_approval_still_prohibits(self):
        result = await self._run_judge(
            make_input(height=3.2, exception_review_approved=False)
        )
        self.assertEqual(result.decision, "prohibited")
        self.assertIn("세로 길이 3.2m", result.warnings[-1])

    async def test_projecting_sign_returns_missing_rule_fallback(self):
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)
        self.engine._check_special_zone_restriction = AsyncMock(return_value=None)
        self.engine._get_projecting_sign_exception_rule = AsyncMock(return_value=None)
        self.engine._get_projecting_sign_sign_count_rule = AsyncMock(return_value=None)
        self.engine._fetch_matching_rules = AsyncMock(return_value=[])
        result = await self.engine.judge(self.db, make_input())
        self.assertEqual(result.fallback_reason, "missing_rule")
        self.assertEqual(result.decision, "report")

    async def test_projecting_sign_returns_missing_input_fallback(self):
        result = await self.engine.judge(
            self.db,
            make_input(height=None),
        )
        self.assertEqual(result.fallback_reason, "missing_input")
        self.assertIn("height", result.missing_fields)


if __name__ == "__main__":
    unittest.main()
