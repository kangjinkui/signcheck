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
        "sign_type": "입간판",
        "floor": 1,
        "area": 1.0,
        "light_type": "none",
        "zone": "일반상업지역",
        "ad_type": "self",
        "tehranro": False,
        "has_sidewalk": False,
        "sign_height": 1.0,
        "base_width": 0.4,
        "base_depth": 0.6,
        "distance_from_building": 0.5,
    }
    data.update(overrides)
    return JudgeInput(**data)


def make_condition():
    return SimpleNamespace(id=uuid.uuid4())


def make_effect(**overrides):
    data = {
        "decision": "report",
        "administrative_action": "report",
        "review_type": "소심의",
        "safety_check": False,
        "max_area": 1.2,
        "max_height": None,
        "max_protrusion": None,
        "max_width": None,
        "display_period": "1년",
        "warnings": ["입간판 기본 규칙"],
        "provision_id": uuid.uuid4(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class StandingSignRuleEngineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = RuleEngine()
        self.db = object()
        self.engine._check_zone_prohibited = AsyncMock(return_value=None)

    async def test_standing_sign_prohibited_above_first_floor(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[
                (
                    make_condition(),
                    make_effect(
                        decision="prohibited",
                        administrative_action=None,
                        review_type=None,
                        max_area=None,
                        display_period="해당없음",
                        warnings=["입간판은 건물 부지 내 1층(지상)에만 설치할 수 있습니다."],
                    ),
                )
            ]
        )

        result = await self.engine.judge(self.db, make_input(floor=11, area=30.0))

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("1층", " ".join(result.warnings))

    async def test_standing_sign_prohibited_when_area_exceeds_limit(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[
                (
                    make_condition(),
                    make_effect(
                        decision="prohibited",
                        administrative_action=None,
                        review_type=None,
                        display_period="해당없음",
                        warnings=["입간판의 합계면적은 1.2㎡ 이하여야 합니다."],
                    ),
                )
            ]
        )

        result = await self.engine.judge(self.db, make_input(area=30.0))

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("1.2", " ".join(result.warnings))

    async def test_standing_sign_prohibited_when_height_exceeds_limit(self):
        self.engine._fetch_matching_rules = AsyncMock(
            return_value=[
                (
                    make_condition(),
                    make_effect(
                        max_height=1.2,
                        warnings=["입간판 기본 규칙"],
                    ),
                )
            ]
        )

        result = await self.engine.judge(self.db, make_input(sign_height=1.4))

        self.assertEqual(result.decision, "prohibited")
        self.assertIn("1.4m", " ".join(result.warnings))
