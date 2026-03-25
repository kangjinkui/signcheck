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


def make_condition():
    return SimpleNamespace(id=uuid.uuid4())


def make_effect(**overrides):
    data = {
        "decision": "report",
        "administrative_action": "report",
        "review_type": "소심의",
        "safety_check": False,
        "max_area": None,
        "max_height": None,
        "max_protrusion": None,
        "max_width": None,
        "display_period": "1년",
        "warnings": ["기본 규칙"],
        "provision_id": uuid.uuid4(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class GenericSpecRuleEngineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = RuleEngine()
        self.db = object()
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)

    async def test_window_sign_prohibited_when_width_exceeds_limit(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(max_width=0.3, max_height=0.3))]
        )

        result = await self.engine.judge(
            self.db,
            JudgeInput(
                sign_type="창문이용광고물",
                floor=2,
                area=0.2,
                light_type="none",
                zone="일반상업지역",
                ad_type="self",
                sign_width=0.5,
                sign_height=0.2,
            ),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("가로 길이 0.5m", " ".join(result.warnings))

    async def test_banner_prohibited_when_height_exceeds_limit(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(max_width=0.7, max_height=2.0))]
        )

        result = await self.engine.judge(
            self.db,
            JudgeInput(
                sign_type="현수막",
                floor=1,
                area=1.0,
                light_type="none",
                zone="일반상업지역",
                ad_type="self",
                sign_width=0.7,
                sign_height=2.5,
            ),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("세로 길이 2.5m", " ".join(result.warnings))

    async def test_rooftop_balloon_prohibited_when_height_exceeds_half_building_height(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(max_height=10.0, max_area=100.0))]
        )

        result = await self.engine.judge(
            self.db,
            JudgeInput(
                sign_type="애드벌룬",
                floor=10,
                area=80.0,
                light_type="none",
                zone="일반상업지역",
                ad_type="self",
                sign_height=9.0,
                building_height=16.0,
            ),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("건물 높이의 1/2 기준 8.0m", " ".join(result.warnings))

    async def test_performance_sign_prohibited_when_protrusion_exceeds_limit(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", max_protrusion=0.3))]
        )

        result = await self.engine.judge(
            self.db,
            JudgeInput(
                sign_type="공연간판",
                floor=2,
                area=2.0,
                light_type="none",
                zone="일반상업지역",
                ad_type="self",
                vendor_count=2,
                sign_width=2.0,
                building_width=9.0,
                protrusion=0.5,
                has_performance_hall=True,
            ),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("돌출폭 0.5m", " ".join(result.warnings))

    async def test_rooftop_sign_prohibited_when_horizontal_distance_is_short(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", max_height=3.5))]
        )

        result = await self.engine.judge(
            self.db,
            JudgeInput(
                sign_type="옥상간판",
                floor=15,
                area=5.0,
                light_type="none",
                zone="일반상업지역",
                ad_type="self",
                sign_height=3.0,
                building_height=20.0,
                building_floor_count=15,
                horizontal_distance_to_other_sign=30.0,
            ),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("수평거리 30.0m", " ".join(result.warnings))

    async def test_standing_sign_prohibited_when_distance_from_building_exceeds_limit(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(max_height=1.2, max_area=1.2))]
        )

        result = await self.engine.judge(
            self.db,
            JudgeInput(
                sign_type="입간판",
                floor=1,
                area=1.0,
                light_type="none",
                zone="일반상업지역",
                ad_type="self",
                has_sidewalk=False,
                sign_height=1.0,
                base_width=0.4,
                base_depth=0.6,
                distance_from_building=1.5,
            ),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("1.5m", " ".join(result.warnings))

    async def test_performance_sign_prohibited_without_performance_hall(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", max_protrusion=0.3))]
        )

        result = await self.engine.judge(
            self.db,
            JudgeInput(
                sign_type="공연간판",
                floor=2,
                area=2.0,
                light_type="none",
                zone="일반상업지역",
                ad_type="self",
                vendor_count=1,
                sign_width=2.0,
                building_width=9.0,
                protrusion=0.2,
                has_performance_hall=False,
            ),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("공연장이 있는 건물", " ".join(result.warnings))
