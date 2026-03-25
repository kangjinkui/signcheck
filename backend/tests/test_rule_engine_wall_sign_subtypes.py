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
        "sign_type": "벽면이용간판",
        "install_subtype": "wall_sign_general_under_5f",
        "floor": 3,
        "area": 4.0,
        "light_type": "none",
        "zone": "일반상업지역",
        "ad_type": "self",
        "tehranro": False,
        "form_type": "solid",
        "shop_front_width": 8.0,
        "sign_width": 5.0,
        "sign_height": 0.4,
        "sign_area": 4.0,
        "is_corner_lot": False,
        "has_front_and_rear_roads": False,
        "existing_sign_count_for_business": 0,
    }
    data.update(overrides)
    return JudgeInput(**data)


def make_top_input(**overrides):
    data = {
        "sign_type": "벽면이용간판",
        "install_subtype": "wall_sign_top_building",
        "floor": 10,
        "area": 120.0,
        "light_type": "none",
        "zone": "일반상업지역",
        "ad_type": "self",
        "tehranro": False,
        "form_type": "solid",
        "content_type": "building_name",
        "display_orientation": "horizontal",
        "building_floor_count": 10,
        "install_at_top_floor": True,
        "building_width": 20.0,
        "building_height": 40.0,
        "requested_faces": 3,
        "sign_width": 9.0,
        "sign_height": 1.2,
    }
    data.update(overrides)
    return JudgeInput(**data)


def make_condition():
    return SimpleNamespace(id=uuid.uuid4())


def make_effect(**overrides):
    data = {
        "decision": "report",
        "administrative_action": None,
        "review_type": "소심의",
        "safety_check": False,
        "max_area": None,
        "max_height": 0.8,
        "max_protrusion": 0.3,
        "max_width": 10.0,
        "display_period": "3년",
        "warnings": ["기본 벽면 규칙"],
        "provision_id": uuid.uuid4(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class WallSignSubtypeRuleEngineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = RuleEngine()
        self.db = object()
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)

    async def test_wall_sign_requires_install_subtype(self):
        result = await self.engine.judge(
            self.db,
            make_input(install_subtype=None),
        )
        self.assertEqual(result.fallback_reason, "missing_input")
        self.assertIn("install_subtype", result.missing_fields)

    async def test_wall_sign_general_under_5f_uses_general_rule_set(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(review_type="소심의", max_height=0.8))]
        )

        result = await self.engine.judge(self.db, make_input(install_subtype="wall_sign_general_under_5f"))

        self.assertEqual(result.decision, "permit")
        self.assertEqual(result.administrative_action, "none")
        self.assertIsNone(result.review_type)
        self.assertEqual(result.max_height, 0.45)
        self.assertEqual(result.max_width, 6.4)
        self.assertIn("무신고 가능", result.warnings[-1])

    async def test_wall_sign_top_building_uses_top_building_rule_set(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", review_type="대심의", max_area=225.0))]
        )

        result = await self.engine.judge(self.db, make_top_input())

        self.assertEqual(result.decision, "permit")
        self.assertEqual(result.review_type, "대심의")
        self.assertEqual(result.max_area, 225.0)
        self.assertEqual(result.max_width, 10.0)
        self.assertEqual(result.max_height, 1.2)
        self.assertIn("심의가 필수", " ".join(result.warnings))

    async def test_wall_sign_top_building_requires_top_floor(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", review_type="대심의", max_area=225.0))]
        )

        result = await self.engine.judge(
            self.db,
            make_top_input(install_at_top_floor=False),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("최상단", " ".join(result.warnings))

    async def test_wall_sign_top_building_blocks_more_than_three_faces(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", review_type="대심의", max_area=225.0))]
        )

        result = await self.engine.judge(
            self.db,
            make_top_input(requested_faces=4),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("최대 3면", " ".join(result.warnings))

    async def test_wall_sign_top_building_vertical_spec_uses_half_building_height_and_width_cap(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", review_type="대심의", max_area=225.0))]
        )

        result = await self.engine.judge(
            self.db,
            make_top_input(display_orientation="vertical", sign_width=1.1, sign_height=9.0),
        )

        self.assertEqual(result.decision, "permit")
        self.assertEqual(result.max_width, 1.2)
        self.assertEqual(result.max_height, 10.0)

    async def test_wall_sign_top_building_blocks_non_allowed_content_type(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect(decision="permit", review_type="대심의", max_area=225.0))]
        )

        result = await self.engine.judge(
            self.db,
            make_top_input(content_type="third_party_brand"),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("표시 내용", " ".join(result.warnings))

    async def test_wall_sign_general_requires_solid_form_on_fourth_floor(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect())]
        )

        result = await self.engine.judge(
            self.db,
            make_input(floor=4, form_type="plate", sign_area=6.0, area=6.0),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("4층 이상", result.warnings[0])

    async def test_wall_sign_general_reports_when_exemption_conditions_not_met(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect())]
        )

        result = await self.engine.judge(
            self.db,
            make_input(sign_area=5.5, area=5.5),
        )

        self.assertEqual(result.decision, "report")
        self.assertEqual(result.administrative_action, "report")
        self.assertEqual(result.review_type, "소심의")

    async def test_wall_sign_general_allows_two_signs_for_corner_lot_exception(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect())]
        )

        result = await self.engine.judge(
            self.db,
            make_input(is_corner_lot=True, existing_sign_count_for_business=1),
        )

        self.assertEqual(result.decision, "permit")
        self.assertIn("2개까지 허용", " ".join(result.warnings))

    async def test_wall_sign_general_blocks_when_quantity_exceeded(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect())]
        )

        result = await self.engine.judge(
            self.db,
            make_input(existing_sign_count_for_business=1),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("업소당 허용 간판 수 1개", result.warnings[-1])

    async def test_wall_sign_general_blocks_when_width_exceeds_shop_front_limit(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[(make_condition(), make_effect())]
        )

        result = await self.engine.judge(
            self.db,
            make_input(sign_width=7.0),
        )

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("허용 기준 6.4m", result.warnings[-1])


if __name__ == "__main__":
    unittest.main()
