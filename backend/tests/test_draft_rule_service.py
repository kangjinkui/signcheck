import os
import sys
import types
import unittest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

db_module = types.ModuleType("db")
db_models_module = types.ModuleType("db.models")


class DraftRule:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


db_models_module.DraftRule = DraftRule
db_module.models = db_models_module
httpx_module = types.ModuleType("httpx")
httpx_module.AsyncClient = object
sys.modules.setdefault("db", db_module)
sys.modules.setdefault("db.models", db_models_module)
sys.modules.setdefault("httpx", httpx_module)

from services import draft_rule_service  # noqa: E402


class DraftRuleServiceTests(unittest.TestCase):
    def test_build_draft_from_hit_preserves_source_metadata(self):
        hit = {
            "chunk_id": "11111111-1111-1111-1111-111111111111",
            "document_id": "22222222-2222-2222-2222-222222222222",
            "provision_id": "33333333-3333-3333-3333-333333333333",
            "law_name": "강남구 옥외광고물 조례",
            "jurisdiction": "강남구",
            "effective_date": "2026-03-25",
            "article": "제5조",
            "chunk_content": "돌출간판은 5층 이하에 설치한다.",
            "provision_content": "돌출간판은 5층 이하에 설치하여야 한다.",
            "similarity": 0.9123,
        }

        draft = draft_rule_service.build_draft_from_hit(
            sign_type="돌출간판",
            install_subtype=None,
            source_type="rag",
            hit=hit,
        )

        self.assertEqual(draft.sign_type, "돌출간판")
        self.assertEqual(draft.source_type, "rag")
        self.assertEqual(draft.source_chunk_ids, [hit["chunk_id"]])
        self.assertEqual(str(draft.source_document_id), hit["document_id"])
        self.assertEqual(str(draft.source_provision_id), hit["provision_id"])
        self.assertIn("강남구 옥외광고물 조례 제5조", draft.title)
        self.assertEqual(
            draft.extracted_payload["source_summary"]["chunk_content"],
            hit["chunk_content"],
        )

    def test_build_draft_from_extracted_item_merges_source_hits(self):
        source_hits = [
            {
                "chunk_id": "11111111-1111-1111-1111-111111111111",
                "document_id": "22222222-2222-2222-2222-222222222222",
                "provision_id": "33333333-3333-3333-3333-333333333333",
                "law_name": "강남구 옥외광고물 조례",
                "article": "제5조",
                "similarity": 0.9,
                "jurisdiction": "강남구",
                "effective_date": "2026-03-25",
                "chunk_content": "돌출간판은 5층 이하",
                "provision_content": "돌출간판은 5층 이하에 설치",
            },
            {
                "chunk_id": "44444444-4444-4444-4444-444444444444",
                "document_id": "22222222-2222-2222-2222-222222222222",
                "provision_id": "55555555-5555-5555-5555-555555555555",
                "law_name": "강남구 옥외광고물 조례 시행규칙",
                "article": "제2조",
                "similarity": 0.82,
                "jurisdiction": "강남구",
                "effective_date": "2026-03-25",
                "chunk_content": "돌출폭은 1미터 이하",
                "provision_content": "돌출폭은 1미터 이하로 한다",
            },
        ]
        item = {
            "title": "돌출간판 층수 규칙 초안",
            "summary": "5층 이하 허용 규칙",
            "extracted_payload": {"rule_kind": "floor_limit"},
            "condition_payload": {"floor_max": 5},
            "effect_payload": {"decision": "permit"},
            "auxiliary_payload": {"needs_review": True},
        }

        draft = draft_rule_service.build_draft_from_extracted_item(
            sign_type="돌출간판",
            install_subtype=None,
            source_type="import",
            item=item,
            source_hits=source_hits,
        )

        self.assertEqual(draft.title, item["title"])
        self.assertEqual(draft.summary, item["summary"])
        self.assertEqual(
            draft.source_chunk_ids,
            [source_hits[0]["chunk_id"], source_hits[1]["chunk_id"]],
        )
        self.assertEqual(str(draft.source_document_id), source_hits[0]["document_id"])
        self.assertIsNone(draft.source_provision_id)
        self.assertEqual(draft.condition_payload, item["condition_payload"])
        self.assertEqual(draft.effect_payload, item["effect_payload"])
        self.assertEqual(draft.auxiliary_payload, item["auxiliary_payload"])
        self.assertEqual(draft.extracted_payload["rule_kind"], "floor_limit")
        self.assertEqual(len(draft.extracted_payload["source_hits"]), 2)


if __name__ == "__main__":
    unittest.main()
