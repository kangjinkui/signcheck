"""
PrivateGPT API 클라이언트
Docker 서비스: http://privategpt:8080

사용 엔드포인트:
  POST /v1/completions    — RAG 질의응답
  POST /v1/ingest/file    — 문서 임베딩
  POST /v1/ingest/text    — 텍스트 직접 임베딩
  GET  /v1/ingest/list    — 임베딩 문서 목록
  DELETE /v1/ingest/{id}  — 문서 삭제
  GET  /health            — 상태 확인
"""
import httpx
import os
from typing import Optional

PRIVATEGPT_URL = os.getenv("PRIVATEGPT_URL", "http://privategpt:8080")
TIMEOUT = 30.0


async def query_rag(
    question: str,
    context_filter: Optional[dict] = None,
) -> dict:
    """판정 근거 조문 검색 및 챗봇 답변"""
    payload = {
        "prompt": question,
        "use_context": True,
        "include_sources": True,
        "stream": False,
        "context_filter": context_filter,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{PRIVATEGPT_URL}/v1/completions",
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def ingest_file(file_path: str) -> dict:
    """법령 문서 파일 임베딩"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                f"{PRIVATEGPT_URL}/v1/ingest/file",
                files={"file": (os.path.basename(file_path), f)},
            )
            response.raise_for_status()
            return response.json()


async def ingest_text(text: str, filename: str = "law.txt") -> dict:
    """법령 텍스트 직접 임베딩"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{PRIVATEGPT_URL}/v1/ingest/text",
            json={"file_name": filename, "text": text},
        )
        response.raise_for_status()
        return response.json()


async def list_ingested() -> list:
    """임베딩된 문서 목록"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(f"{PRIVATEGPT_URL}/v1/ingest/list")
        response.raise_for_status()
        return response.json().get("data", [])


async def delete_document(doc_id: str) -> bool:
    """임베딩 문서 삭제"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.delete(f"{PRIVATEGPT_URL}/v1/ingest/{doc_id}")
        return response.status_code == 200


async def health_check() -> bool:
    """PrivateGPT 서비스 상태 확인"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{PRIVATEGPT_URL}/health")
            return response.status_code == 200
    except Exception:
        return False
