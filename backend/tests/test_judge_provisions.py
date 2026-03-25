import os
import sys
import types
import unittest
import uuid
from unittest.mock import AsyncMock


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _APIRouter:
    def __init__(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        return self._decorator

    @staticmethod
    def _decorator(fn):
        return fn


fastapi_module = types.ModuleType("fastapi")
fastapi_module.APIRouter = _APIRouter
fastapi_module.Depends = lambda value: value
fastapi_module.HTTPException = Exception
sys.modules["fastapi"] = fastapi_module

class _SelectStmt:
    def join(self, *args, **kwargs):
        return self

    def where(self, *args, **kwargs):
        return self


sqlalchemy_module = types.ModuleType("sqlalchemy")
sqlalchemy_module.select = lambda *args, **kwargs: _SelectStmt()
sys.modules["sqlalchemy"] = sqlalchemy_module

sqlalchemy_ext_module = types.ModuleType("sqlalchemy.ext")
sqlalchemy_asyncio_module = types.ModuleType("sqlalchemy.ext.asyncio")
sqlalchemy_asyncio_module.AsyncSession = object
sys.modules["sqlalchemy.ext"] = sqlalchemy_ext_module
sys.modules["sqlalchemy.ext.asyncio"] = sqlalchemy_asyncio_module

db_module = types.ModuleType("db")
db_module.get_db = lambda: None
db_models_module = types.ModuleType("db.models")


class CaseLog:
    pass


class _Field:
    id = object()
    document_id = object()
    article = object()


class DocumentMaster(_Field):
    name = object()


class Provision(_Field):
    content = object()


db_models_module.CaseLog = CaseLog
db_models_module.DocumentMaster = DocumentMaster
db_models_module.Provision = Provision
db_module.models = db_models_module
sys.modules["db"] = db_module
sys.modules["db.models"] = db_models_module

engine_rule_engine_module = types.ModuleType("engine.rule_engine")
engine_rule_engine_module.RuleEngine = type("RuleEngine", (), {})
engine_rule_engine_module.JudgeInput = type("JudgeInput", (), {})
sys.modules["engine.rule_engine"] = engine_rule_engine_module

engine_fee_module = types.ModuleType("engine.fee_calculator")
engine_fee_module.calculate = AsyncMock()
sys.modules["engine.fee_calculator"] = engine_fee_module

engine_checklist_module = types.ModuleType("engine.checklist")
engine_checklist_module.generate = AsyncMock()
sys.modules["engine.checklist"] = engine_checklist_module

services_module = types.ModuleType("services")
services_module.rag_service = types.SimpleNamespace(search=AsyncMock())
sys.modules["services"] = services_module

from api import judge as judge_module  # noqa: E402


class _FakeResult:
    def __init__(self, provision_id=None):
        self.provision_id = provision_id


class _FakeExecuteResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class JudgeProvisionResolutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_provisions_prefers_rule_provision(self):
        provision_id = str(uuid.uuid4())
        db = types.SimpleNamespace(
            execute=AsyncMock(
                return_value=_FakeExecuteResult(
                    (
                        types.SimpleNamespace(
                            id=uuid.UUID(provision_id),
                            article="제9조의2",
                            content="입간판은 자사광고만 가능하다.",
                            document_id=uuid.uuid4(),
                        ),
                        types.SimpleNamespace(
                            name="서울특별시 옥외광고물 조례",
                        ),
                    )
                )
            )
        )
        judge_module.rag_service.search = AsyncMock(return_value=[
            {"법령명": "무관한 조례", "조문번호": "제99조", "조문내용": "무관", "similarity": 0.3}
        ])
        req = types.SimpleNamespace(sign_type="입간판", zone="일반상업지역", floor=11, area=30.0)

        provisions, rag_chunks = await judge_module._resolve_provisions(
            db,
            req,
            _FakeResult(provision_id=provision_id),
        )

        self.assertEqual(len(provisions), 1)
        self.assertEqual(provisions[0]["law"], "서울특별시 옥외광고물 조례")
        self.assertEqual(provisions[0]["article"], "제9조의2")
        self.assertEqual(provisions[0]["similarity"], 1.0)
        self.assertEqual(rag_chunks, ["제9조의2"])
        judge_module.rag_service.search.assert_not_awaited()

    async def test_resolve_provisions_falls_back_to_rag_when_rule_provision_missing(self):
        db = types.SimpleNamespace(
            execute=AsyncMock(return_value=_FakeExecuteResult(None))
        )
        judge_module.rag_service.search = AsyncMock(return_value=[
            {
                "법령명": "서울특별시 옥외광고물 조례",
                "조문번호": "제9조의2",
                "조문내용": "입간판은 자사광고만 가능하다.",
                "similarity": 0.91,
            }
        ])
        req = types.SimpleNamespace(sign_type="입간판", zone="일반상업지역", floor=1, area=1.0)

        provisions, rag_chunks = await judge_module._resolve_provisions(
            db,
            req,
            _FakeResult(provision_id=None),
        )

        self.assertEqual(len(provisions), 1)
        self.assertEqual(provisions[0]["article"], "제9조의2")
        self.assertEqual(rag_chunks, ["제9조의2"])
        judge_module.rag_service.search.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
