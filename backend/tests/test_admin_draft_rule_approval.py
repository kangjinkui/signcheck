import os
import sys
import types
import unittest
import uuid


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _APIRouter:
    def __init__(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        return self._decorator

    def post(self, *args, **kwargs):
        return self._decorator

    def patch(self, *args, **kwargs):
        return self._decorator

    def put(self, *args, **kwargs):
        return self._decorator

    def delete(self, *args, **kwargs):
        return self._decorator

    @staticmethod
    def _decorator(fn):
        return fn


fastapi_module = types.ModuleType("fastapi")
fastapi_module.APIRouter = _APIRouter
fastapi_module.Depends = lambda value: value
fastapi_module.HTTPException = _HTTPException
fastapi_module.UploadFile = object
fastapi_module.File = lambda *args, **kwargs: None
sys.modules["fastapi"] = fastapi_module

sqlalchemy_module = types.ModuleType("sqlalchemy")
sqlalchemy_module.select = lambda *args, **kwargs: None
sqlalchemy_module.desc = lambda *args, **kwargs: None
sys.modules["sqlalchemy"] = sqlalchemy_module

sqlalchemy_ext_module = types.ModuleType("sqlalchemy.ext")
sqlalchemy_asyncio_module = types.ModuleType("sqlalchemy.ext.asyncio")
sqlalchemy_asyncio_module.AsyncSession = object
sys.modules["sqlalchemy.ext"] = sqlalchemy_ext_module
sys.modules["sqlalchemy.ext.asyncio"] = sqlalchemy_asyncio_module

db_module = types.ModuleType("db")
db_module.get_db = lambda: None
db_models_module = types.ModuleType("db.models")


class _BaseRule:
    def __init__(self, **kwargs):
        self.id = uuid.uuid4()
        for key, value in kwargs.items():
            setattr(self, key, value)


class CaseLog:
    pass


class DraftRule:
    pass


class FeeRule:
    pass


class RuleCondition(_BaseRule):
    pass


class RuleEffect(_BaseRule):
    pass


class IndustryExceptionRule(_BaseRule):
    pass


class SignCountRule(_BaseRule):
    pass


class SpecialZoneRule(_BaseRule):
    pass


db_models_module.CaseLog = CaseLog
db_models_module.DraftRule = DraftRule
db_models_module.FeeRule = FeeRule
db_models_module.RuleCondition = RuleCondition
db_models_module.RuleEffect = RuleEffect
db_models_module.IndustryExceptionRule = IndustryExceptionRule
db_models_module.SignCountRule = SignCountRule
db_models_module.SpecialZoneRule = SpecialZoneRule
db_module.models = db_models_module
sys.modules["db"] = db_module
sys.modules["db.models"] = db_models_module

services_module = types.ModuleType("services")
services_module.draft_rule_service = types.SimpleNamespace()
services_module.privategpt_client = types.SimpleNamespace()
sys.modules["services"] = services_module

from api import admin  # noqa: E402


class _FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None


class AdminDraftRuleApprovalTests(unittest.IsolatedAsyncioTestCase):
    async def test_approve_auxiliary_rules_creates_three_rule_types(self):
        draft = types.SimpleNamespace(
            sign_type="돌출간판",
            source_provision_id=uuid.uuid4(),
            auxiliary_payload={
                "industry_exception_rules": [
                    {
                        "exception_type": "beauty_shop",
                        "max_height": 4.0,
                        "max_protrusion": 1.2,
                    }
                ],
                "sign_count_rules": [
                    {
                        "exception_type": "medical",
                        "max_count_per_business": 2,
                    }
                ],
                "special_zone_rules": [
                    {
                        "special_zone": "tehranro",
                        "decision": "prohibited",
                    }
                ],
            },
        )
        db = _FakeDB()

        summary = await admin._approve_auxiliary_rules(draft, db)

        self.assertEqual(len(db.added), 3)
        self.assertEqual(len(summary["industry_exception_rule_ids"]), 1)
        self.assertEqual(len(summary["sign_count_rule_ids"]), 1)
        self.assertEqual(len(summary["special_zone_rule_ids"]), 1)
        self.assertEqual(db.added[0].sign_type, "돌출간판")
        self.assertEqual(db.added[1].max_count_per_business, 2)
        self.assertEqual(db.added[2].special_zone, "tehranro")

    async def test_approve_auxiliary_rules_validates_required_fields(self):
        draft = types.SimpleNamespace(
            sign_type="돌출간판",
            source_provision_id=None,
            auxiliary_payload={
                "special_zone_rules": [
                    {
                        "special_zone": "tehranro",
                    }
                ]
            },
        )

        with self.assertRaises(_HTTPException) as exc_info:
            await admin._approve_auxiliary_rules(draft, _FakeDB())

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("special_zone_rules[].decision", exc_info.exception.detail)


if __name__ == "__main__":
    unittest.main()
