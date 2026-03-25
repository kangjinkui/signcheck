#!/usr/bin/env python3
"""
LlamaIndex 임베딩 파이프라인

law_documents/ 에서 법령 조문을 읽어:
  1. document_master 테이블에 법령 메타정보 저장
  2. provision 테이블에 조문 원문 저장
  3. law_chunk 테이블에 pgvector 임베딩 저장 (LlamaIndex 사용)

전제조건:
  - Docker Compose 실행 중 (postgres + ollama)
  - ollama에 nomic-embed-text 모델 설치됨
    → docker exec adjudge-ollama ollama pull nomic-embed-text
  - pip install llama-index-core llama-index-embeddings-ollama psycopg2-binary

사용법:
  python3 scripts/embed_laws.py           # 전체 실행
  python3 scripts/embed_laws.py --init-db # DB 테이블 생성 후 실행
  python3 scripts/embed_laws.py --dry-run # DB 저장 없이 미리보기
"""

import os
import sys
import json
import uuid
import argparse
from pathlib import Path
from datetime import datetime

# ── 경로 설정 ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
LAW_DOCS_DIR = BASE_DIR / "law_documents"
ENV_FILE = BASE_DIR / ".env"

# ── 설정 ─────────────────────────────────────────────────
DB_URL = "postgresql://adjudge:adjudge@localhost:5432/adjudge"
OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768

# 수집된 law_documents 파일 목록
ARTICLES_FILES = [
    ("옥외광고물법_articles.json",       "국가",   "법률"),
    ("옥외광고물법_시행령_articles.json", "국가",   "대통령령"),
    ("서울시_옥외광고물_조례_articles.json", "서울시", "조례"),
    ("강남구_옥외광고물_조례_articles.json", "강남구", "조례"),
]

# ── DB 연결 ──────────────────────────────────────────────
def get_conn():
    try:
        import psycopg2
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        return conn
    except ImportError:
        print("ERROR: psycopg2 미설치 → pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: DB 연결 실패 → {e}")
        print("  Docker 실행 여부 확인: docker ps | grep adjudge-postgres")
        sys.exit(1)

# ── law_chunk 테이블 생성 ────────────────────────────────
CREATE_LAW_CHUNK_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS law_chunk (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id   UUID REFERENCES document_master(id) ON DELETE CASCADE,
    provision_id  UUID REFERENCES provision(id) ON DELETE CASCADE,
    content       TEXT NOT NULL,
    embedding     vector({dim}),
    chunk_index   INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS law_chunk_embedding_idx
    ON law_chunk USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);
""".format(dim=EMBED_DIM)

def init_db(conn):
    with conn.cursor() as cur:
        cur.execute(CREATE_LAW_CHUNK_SQL)
    conn.commit()
    print("✓ law_chunk 테이블 생성 완료")

# ── Ollama 임베딩 ────────────────────────────────────────
def get_embedding(text: str) -> list:
    """Ollama REST API로 임베딩 벡터 생성"""
    try:
        from urllib.request import urlopen, Request
        from urllib.error import URLError
        import json as _json

        payload = _json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
        req = Request(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=60) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
        return result["embedding"]

    except URLError as e:
        print(f"ERROR: Ollama 연결 실패 → {e}")
        print(f"  Ollama 실행 여부 확인: docker ps | grep adjudge-ollama")
        print(f"  모델 설치 확인: docker exec adjudge-ollama ollama list")
        sys.exit(1)

# ── document_master upsert ───────────────────────────────
def upsert_document(cur, name: str, law_type: str, jurisdiction: str,
                    effective_date: str) -> str:
    """법령명이 같으면 update, 없으면 insert. doc_id 반환"""
    cur.execute(
        "SELECT id FROM document_master WHERE name = %s",
        (name,)
    )
    row = cur.fetchone()
    if row:
        doc_id = str(row[0])
        cur.execute(
            """UPDATE document_master
               SET effective_date=%s, version=%s
               WHERE id=%s""",
            (effective_date, effective_date, doc_id)
        )
        return doc_id

    doc_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO document_master
           (id, name, type, jurisdiction, effective_date, version, source_type)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (doc_id, name, law_type, jurisdiction, effective_date, effective_date, "api")
    )
    return doc_id

# ── provision upsert ────────────────────────────────────
def upsert_provision(cur, doc_id: str, article_num: str, title: str,
                     content: str, effective_date: str) -> str:
    """(document_id, article) 기준으로 upsert. provision_id 반환"""
    cur.execute(
        "SELECT id FROM provision WHERE document_id=%s AND article=%s",
        (doc_id, article_num)
    )
    row = cur.fetchone()
    if row:
        provision_id = str(row[0])
        cur.execute(
            "UPDATE provision SET content=%s, effective_date=%s WHERE id=%s",
            (content, effective_date, provision_id)
        )
        return provision_id

    provision_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO provision
           (id, document_id, article, paragraph, item, content, effective_date)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (provision_id, doc_id, article_num, "", "", content, effective_date)
    )
    return provision_id

# ── law_chunk upsert ─────────────────────────────────────
def upsert_chunk(cur, doc_id: str, provision_id: str,
                 content: str, embedding: list, chunk_index: int):
    cur.execute(
        "SELECT id FROM law_chunk WHERE provision_id=%s AND chunk_index=%s",
        (provision_id, chunk_index)
    )
    row = cur.fetchone()
    vec_str = "[" + ",".join(str(v) for v in embedding) + "]"

    if row:
        cur.execute(
            "UPDATE law_chunk SET content=%s, embedding=%s WHERE id=%s",
            (content, vec_str, str(row[0]))
        )
    else:
        cur.execute(
            """INSERT INTO law_chunk
               (id, document_id, provision_id, content, embedding, chunk_index)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (str(uuid.uuid4()), doc_id, provision_id, content, vec_str, chunk_index)
        )

# ── 청크 텍스트 생성 ─────────────────────────────────────
def build_chunk_text(article: dict) -> str:
    """RAG 검색 품질을 위해 법령명 + 조문제목 + 조문내용을 하나의 텍스트로 합칩니다."""
    parts = []
    약칭 = article.get("법령약칭") or article.get("법령명", "")
    제목 = article.get("조문제목", "")
    내용 = article.get("조문내용", "")

    if 약칭:
        parts.append(f"[{약칭}]")
    if 제목:
        parts.append(제목)
    if 내용:
        parts.append(내용)

    return " ".join(parts).strip()

# ── 메인 파이프라인 ──────────────────────────────────────
def run(dry_run: bool = False):
    conn = None if dry_run else get_conn()

    total_docs = 0
    total_provisions = 0
    total_chunks = 0

    for filename, jurisdiction, law_type in ARTICLES_FILES:
        filepath = LAW_DOCS_DIR / filename
        if not filepath.exists():
            print(f"  SKIP: {filename} 없음 (fetch_laws.py 먼저 실행)")
            continue

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        law_name = data.get("법령명", filename)
        effective_date = data.get("시행일자", "")
        articles = data.get("articles", [])

        print(f"\n[{jurisdiction}] {law_name}")
        print(f"  조문 수: {len(articles)}개 | 시행일: {effective_date}")

        if dry_run:
            # 첫 조문만 미리보기
            if articles:
                sample = articles[0]
                chunk_text = build_chunk_text(sample)
                print(f"  샘플 청크 텍스트 ({len(chunk_text)}자):")
                print(f"    {chunk_text[:120]}...")
            continue

        cur = conn.cursor()
        doc_id = upsert_document(cur, law_name, law_type, jurisdiction, effective_date)
        total_docs += 1

        for i, article in enumerate(articles):
            조문번호 = article.get("조문번호", str(i))
            조문내용 = article.get("조문내용", "")
            조문제목 = article.get("조문제목", "")

            if not 조문내용.strip():
                continue

            provision_id = upsert_provision(
                cur, doc_id, 조문번호, 조문제목, 조문내용, effective_date
            )
            total_provisions += 1

            chunk_text = build_chunk_text(article)
            print(f"  [{i+1}/{len(articles)}] 제{조문번호}조 임베딩 중...", end="\r")

            embedding = get_embedding(chunk_text)
            upsert_chunk(cur, doc_id, provision_id, chunk_text, embedding, 0)
            total_chunks += 1

        conn.commit()
        cur.close()
        print(f"  ✓ {len(articles)}개 조문 → {total_chunks}개 청크 저장 완료      ")

    if conn:
        conn.close()

    print("\n" + "=" * 50)
    if dry_run:
        print("DRY RUN 완료 (DB 저장 없음)")
    else:
        print(f"완료: 법령 {total_docs}개 | 조문 {total_provisions}개 | 청크 {total_chunks}개")

# ── 진입점 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="법령 임베딩 파이프라인")
    parser.add_argument("--init-db", action="store_true", help="law_chunk 테이블 생성")
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 미리보기")
    args = parser.parse_args()

    print("=" * 50)
    print("LlamaIndex 임베딩 파이프라인")
    print(f"DB:     {DB_URL}")
    print(f"Ollama: {OLLAMA_BASE_URL} ({EMBED_MODEL})")
    print("=" * 50)

    if args.init_db:
        conn = get_conn()
        init_db(conn)
        conn.close()

    run(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
