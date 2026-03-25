#!/usr/bin/env python3
"""
국가법령정보공단 Open API 법령 수집 스크립트

수집 대상:
  - 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 법률 (옥외광고물법)
  - 옥외광고물법 시행령
  - 서울특별시 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 조례
  - 서울특별시 강남구 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 조례

결과: law_documents/ 디렉터리에 JSON 파일 저장
사용법: python3 scripts/fetch_laws.py
"""

import os
import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

# ── 경로 설정 ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
LAW_DOCS_DIR = BASE_DIR / "law_documents"
ENV_FILE = BASE_DIR / ".env"

# ── API 키 로드 ──────────────────────────────────────────
def load_api_key() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("LAW_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key:
                    return key
    key = os.environ.get("LAW_API_KEY", "")
    if key:
        return key
    raise ValueError("LAW_API_KEY를 찾을 수 없습니다. .env 파일에 LAW_API_KEY=키값 형식으로 입력하세요.")

API_KEY = load_api_key()
BASE_URL = "https://www.law.go.kr/DRF"

# ── 수집 대상 법령 목록 ──────────────────────────────────
TARGETS = [
    {
        "name": "옥외광고물법",
        "short": "옥외광고물법",
        "mst": "273367",
        "target": "law",
        "type": "법률",
    },
    {
        "name": "옥외광고물법_시행령",
        "short": "옥외광고물법 시행령",
        "mst": "282903",
        "target": "law",
        "type": "대통령령",
    },
    {
        "name": "서울시_옥외광고물_조례",
        "short": "서울특별시 옥외광고물 조례",
        "mst": "2099885",
        "target": "ordin",
        "type": "조례",
    },
    {
        "name": "강남구_옥외광고물_조례",
        "short": "강남구 옥외광고물 조례",
        "mst": "2023185",
        "target": "ordin",
        "type": "조례",
    },
]

# ── API 호출 ─────────────────────────────────────────────
def fetch_law_json(mst: str, target: str) -> dict:
    params = urlencode({
        "OC": API_KEY,
        "target": target,
        "MST": mst,
        "type": "JSON",
    })
    url = f"{BASE_URL}/lawService.do?{params}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)

# ── 조문 추출 ─────────────────────────────────────────────
def extract_articles(data: dict, law_name: str, law_type: str) -> list:
    articles = []

    if law_type in ("법률", "대통령령"):
        # 구조: data["법령"]["조문"]["조문단위"]
        법령 = data.get("법령", {})
        기본정보 = 법령.get("기본정보", {})
        법령명 = 기본정보.get("법령명_한글", law_name)
        약칭 = 기본정보.get("법령명약칭", law_name)
        시행일 = 기본정보.get("시행일자", "")
        공포일 = 기본정보.get("공포일자", "")

        조문단위 = 법령.get("조문", {}).get("조문단위", [])
        for 조문 in 조문단위:
            articles.append({
                "법령명": 법령명,
                "법령약칭": 약칭,
                "법령종류": law_type,
                "시행일자": 시행일,
                "공포일자": 공포일,
                "조문번호": 조문.get("조문번호", ""),
                "조문제목": 조문.get("조문제목", ""),
                "조문내용": 조문.get("조문내용", ""),
                "조문시행일자": 조문.get("조문시행일자", ""),
                "조문여부": 조문.get("조문여부", "조문"),
            })

    elif law_type == "조례":
        # 구조: data["LawService"]["조문"]["조"]
        ls = data.get("LawService", {})
        기본정보 = ls.get("자치법규기본정보", {})
        법령명 = 기본정보.get("자치법규명", law_name)
        시행일 = 기본정보.get("시행일자", "")
        공포일 = 기본정보.get("공포일자", "")

        조_목록 = ls.get("조문", {}).get("조", [])
        if isinstance(조_목록, dict):
            조_목록 = [조_목록]

        for 조 in 조_목록:
            조문번호_raw = 조.get("조문번호", "")
            # 조례는 조문번호가 [시작, 끝] 리스트로 올 수 있음
            if isinstance(조문번호_raw, list):
                조문번호 = 조문번호_raw[0]
            else:
                조문번호 = 조문번호_raw

            articles.append({
                "법령명": 법령명,
                "법령약칭": 법령명,
                "법령종류": law_type,
                "시행일자": 시행일,
                "공포일자": 공포일,
                "조문번호": 조문번호,
                "조문제목": 조.get("조제목", ""),
                "조문내용": 조.get("조내용", ""),
                "조문시행일자": 시행일,
                "조문여부": "조문" if 조.get("조문여부") == "Y" else "기타",
            })

    return articles

# ── 파일 저장 ─────────────────────────────────────────────
def save_result(name: str, raw_data: dict, articles: list) -> tuple:
    LAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = LAW_DOCS_DIR / f"{name}_raw.json"
    articles_path = LAW_DOCS_DIR / f"{name}_articles.json"

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "법령명": articles[0]["법령명"] if articles else name,
                "법령종류": articles[0]["법령종류"] if articles else "",
                "시행일자": articles[0]["시행일자"] if articles else "",
                "총조문수": len(articles),
                "articles": articles,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return raw_path, articles_path

# ── 메인 ─────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("법령 수집 시작")
    print(f"저장 위치: {LAW_DOCS_DIR}")
    print("=" * 50)

    results = []

    for t in TARGETS:
        print(f"\n[{t['type']}] {t['short']} 수집 중...")
        try:
            raw = fetch_law_json(t["mst"], t["target"])
            articles = extract_articles(raw, t["short"], t["type"])

            if not articles:
                raise ValueError("조문이 0개입니다. API 응답 구조를 확인하세요.")

            raw_path, articles_path = save_result(t["name"], raw, articles)

            print(f"  ✓ 조문 {len(articles)}개 수집 완료")
            print(f"    원문: {raw_path.name}")
            print(f"    조문: {articles_path.name}")

            results.append({
                "name": t["name"],
                "short": t["short"],
                "type": t["type"],
                "mst": t["mst"],
                "article_count": len(articles),
                "status": "success",
            })

        except (HTTPError, URLError) as e:
            print(f"  ✗ 네트워크 오류: {e}")
            results.append({"name": t["name"], "type": t["type"], "status": "error", "error": str(e)})
        except Exception as e:
            print(f"  ✗ 실패: {e}")
            results.append({"name": t["name"], "type": t["type"], "status": "error", "error": str(e)})

        time.sleep(0.5)

    # 수집 요약 저장
    summary = {
        "fetch_date": "2026-03-22",
        "total": len(results),
        "success": sum(1 for r in results if r["status"] == "success"),
        "results": results,
    }
    summary_path = LAW_DOCS_DIR / "fetch_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"완료: {summary['success']}/{summary['total']} 성공")
    for r in results:
        mark = "✓" if r["status"] == "success" else "✗"
        count = f"  ({r.get('article_count', 0)}개 조문)" if r["status"] == "success" else f"  ERROR: {r.get('error','')}"
        print(f"  {mark} {r['name']}{count}")
    print(f"\n요약 파일: {summary_path.name}")

if __name__ == "__main__":
    main()
