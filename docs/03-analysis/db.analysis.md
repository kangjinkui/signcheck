# Gap Analysis Report: db (광고판정 백엔드 + 프론트엔드)

> **Feature**: db (AdJudge — 규칙 엔진, DB, Admin API, Frontend UI)
> **Analysis Date**: 2026-03-25
> **Iteration**: Iter-3
> **Overall Match Rate**: 98%

---

## 전체 스코어 요약

| 카테고리 | 항목 | 매칭 | 갭 | 점수 | 상태 |
|----------|:----:|:----:|:--:|:----:|:----:|
| DB Schema (Section 4) | 10 | 10 | 0 | **100%** | ✅ |
| 규칙 엔진 (Section 7) | 7 | 7 | 0 | **100%** | ✅ |
| 수수료 계산 (Section 8) | 3 | 3 | 0 | **100%** | ✅ |
| FastAPI 엔드포인트 (Section 5) | 7 | 7 | 0 | **100%** | ✅ |
| Docker Compose (Section 2) | 5 | 4 | 1 | **80%** | ⚠️ |
| PrivateGPT/RAG (Section 6) | 3 | 3 | 0 | **100%** | ✅ |
| Checklist Engine | 2 | 2 | 0 | **100%** | ✅ |
| Seed Data | 4 | 4 | 0 | **100%** | ✅ |
| Dev Checklist 1-4단계 (Backend) | 17 | 17 | 0 | **100%** | ✅ |
| Dev Checklist 5단계 (Next.js UI) | 4 | 4 | 0 | **100%** | ✅ |
| Dev Checklist 6단계 (Admin UI) | 3 | 3 | 0 | **100%** | ✅ |
| **전체** | **65** | **64** | **1** | **98%** | ✅ |

> 잔여 갭 1건: PrivateGPT Docker 서비스 (의도적 아키텍처 변경 — 설계 문서 업데이트 필요)

---

## Match Rate 변화 이력

| 날짜 | Iteration | Match Rate | Delta | 주요 변경 |
|------|-----------|:----------:|:-----:|-----------|
| 2026-03-24 | Iter-0 | 84% | -- | 초기 분석 |
| 2026-03-24 | Iter-1 | 92% | +8% | law_chunk, _check_spec() 구현 |
| 2026-03-25 | Iter-2 | 88% | 재산정 | G-1/G-2/G-3 해소, 항목 확대(65개) |
| **2026-03-25** | **Iter-3** | **98%** | **+10%** | **Frontend Stage 5-6 전체 구현** |

---

## 해소된 갭 전체 이력

| Gap ID | 항목 | 해소 Iteration | 파일 |
|--------|------|:-------------:|------|
| ~~G-1~~ | Admin rules CRUD API | Iter-2 | `backend/api/admin.py` |
| ~~G-2~~ | `_check_spec()` 미구현 | Iter-2 | `backend/engine/rule_engine.py` |
| ~~G-3~~ | `law_chunk` 테이블 누락 | Iter-2 | `db/init.sql` |
| ~~G-5~~ | Frontend Stage 5-6 미착수 | Iter-3 | `frontend/**` |
| ~~G-11~~ | 임베딩 트리거 버튼 | Iter-3 | `frontend/app/admin/page.tsx`, `frontend/lib/api.ts` |

---

## Stage 5: Next.js UI 상세 검증

### JudgeForm.tsx (Section 9.1)

| 설계 요구 | 구현 | 상태 |
|---------|------|:----:|
| 간판 유형 드롭다운 (13종) | `SIGN_TYPES` 13개 목록 | ✅ |
| 설치 층수 입력 | number input | ✅ |
| 면적 입력 (㎡) | number input step=0.1 | ✅ |
| 조명 라디오 (없음/내부/디지털) | 3-option radio | ✅ |
| 용도지역 드롭다운 (6개) | `ZONES` 6개 목록 | ✅ |
| 광고 종류 라디오 (자사/타사) | 2-option radio | ✅ |
| 테헤란로 접면 체크박스 | checkbox | ✅ |
| 판정하기 버튼 | submit button | ✅ |
| 업체 수 (지주이용/공연간판) | 조건부 렌더링 | ✅ |

### JudgeResult.tsx (Section 9.1)

| 설계 요구 | 구현 | 상태 |
|---------|------|:----:|
| 판정 배지 (허가/신고/불가) | `DECISION_CLASS` pill badge | ✅ |
| 심의 유형 표시 | review_type 태그 | ✅ |
| 최대 규격 (면적/높이/돌출폭) | max_spec 파싱 출력 | ✅ |
| 수수료 (기준×가중치=합계) | fee.base/light_weight/total | ✅ |
| 표시기간 | display_period | ✅ |
| 필수 서류 목록 | required_docs 배열 | ✅ |
| 근거 조문 (법명/조문번호) | provisions 목록 | ✅ |
| 추가 질문 링크 | onChatOpen 콜백 버튼 | ✅ |
| 경고 메시지 | warnings 박스 | ✅ |

### ChatBot.tsx (Section 9.2)

| 설계 요구 | 구현 | 상태 |
|---------|------|:----:|
| 하단 슬라이드 패널 | fixed-position toggle 패널 | ✅ |
| AI 초기 인사 메시지 | 기본 메시지 설정 | ✅ |
| 메시지 입력 + 전송 버튼 | input + Enter 키 지원 | ✅ |
| AI/사용자 말풍선 구분 | CSS bubble 스타일 | ✅ |
| POST /api/v1/chat 호출 | `chat()` via api.ts | ✅ |
| case_id 판정 결과 연결 | caseId props 전달 | ✅ |
| 자동 스크롤 | bottomRef scrollIntoView | ✅ |

---

## Stage 6: Admin UI 상세 검증

| 설계 요구 (Section 10, 6단계) | 구현 | 상태 |
|------------------------------|------|:----:|
| 규칙 테이블 조회 | 전체 컬럼 표시 (유형/층수/용도지역/판정/규격 등) | ✅ |
| 규칙 삭제 | 삭제 버튼 + confirm 다이얼로그 | ✅ |
| 판정 로그 조회 | 로그 탭, 날짜/유형/판정/수수료 표시 | ✅ |
| **법령 재임베딩 트리거** | 파일 업로드 버튼 → POST /api/v1/admin/ingest | ✅ |

---

## 잔여 갭

### INFO (설계 문서 동기화 권장)

| # | 항목 | 설명 |
|---|------|------|
| G-4 | PrivateGPT Docker 제거 | 실구현: 직접 Ollama 통신 → design Section 2 업데이트 |
| G-6 | 확장 컬럼 미반영 | priority, warnings, has_sidewalk → design Section 4 추가 |
| G-7 | law_chunk 테이블 누락 | design Section 4에 DDL 추가 |
| G-8 | Dual RAG 아키텍처 | rag_service.py vs privategpt_client.py → design Section 6 |
| G-9 | 추가 admin 엔드포인트 | POST/DELETE rules 등 → design Section 5.3 추가 |

---

## 구현된 파일 목록

### 백엔드
| 파일 | 상태 |
|------|:----:|
| `backend/engine/rule_engine.py` | ✅ |
| `backend/engine/fee_calculator.py` | ✅ |
| `backend/engine/checklist.py` | ✅ |
| `backend/api/judge.py` | ✅ |
| `backend/api/admin.py` | ✅ (GET/POST/PUT/DELETE rules) |
| `backend/api/chat.py` | ✅ |
| `backend/services/rag_service.py` | ✅ |
| `db/init.sql` | ✅ |
| `scripts/seed_rules.sql` | ✅ (20건 규칙) |

### 프론트엔드
| 파일 | 상태 |
|------|:----:|
| `frontend/Dockerfile` | ✅ |
| `frontend/package.json` | ✅ |
| `frontend/next.config.js` | ✅ |
| `frontend/tsconfig.json` | ✅ |
| `frontend/app/layout.tsx` | ✅ |
| `frontend/app/globals.css` | ✅ |
| `frontend/app/page.tsx` | ✅ |
| `frontend/app/admin/page.tsx` | ✅ |
| `frontend/components/JudgeForm.tsx` | ✅ |
| `frontend/components/JudgeResult.tsx` | ✅ |
| `frontend/components/ChatBot.tsx` | ✅ |
| `frontend/lib/api.ts` | ✅ |

---

**최종 결론**: Match Rate 98% — `/pdca report db` 실행 조건 충족 ✅

---
**Analysis Generated**: 2026-03-25
**Author**: gap-detector (Iter-3)
