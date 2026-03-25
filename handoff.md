# Session Handoff

## 이번 세션 완료 범위

- `TASK-C1` 완료
  - `rule_condition.install_subtype` 도입
  - `벽면이용간판`을 `wall_sign_general_under_5f`, `wall_sign_top_building`으로 분리
  - API/엔진/프런트에서 subtype 분기 연결
- `TASK-C2` 완료
  - 일반 벽면이용간판 입력 필드 추가
  - `1업소 1개`, 예외 시 `2개`, `3층 이하 판류형 허용`, `4층 이상 입체형만`, 무신고 가능 분기 구현
- `TASK-C3` 완료
  - 건물 상단간판 입력 필드 추가
  - `4층 이상`, `최상단`, `최대 3면`, `입체형만`, 가로형/세로형 규격 계산, 표시 내용 제한 구현
  - 허용 시에도 `review_type`이 항상 반환되도록 처리
- `TASK-D1` 완료
  - `docs/rule-breakdown-template.md` 작성
  - `docs/rule-breakdown-projecting-sign.md` 작성
- `TASK-D2` 완료
  - `draft_rule` 검수용 중간 테이블 추가
  - 관리자 API에 `draft_rule` 생성/조회/수정/승인 엔드포인트 추가

## 이번 세션 주요 변경 파일

- `backend/api/judge.py`
- `backend/api/admin.py`
- `backend/engine/rule_engine.py`
- `backend/db/models.py`
- `backend/tests/test_rule_engine_wall_sign_subtypes.py`
- `frontend/components/JudgeForm.tsx`
- `frontend/lib/api.ts`
- `db/init.sql`
- `db/migrations/20260325_add_install_subtype_to_rule_condition.sql`
- `db/migrations/20260325_add_draft_rule_table.sql`
- `scripts/seed_rules.sql`
- `docs/rule-breakdown-template.md`
- `docs/rule-breakdown-projecting-sign.md`
- `docs/sign-rule-expansion-plan.md`
- `docs/handoff-sign-rule-expansion.md`

## DB 반영 상태

- 적용 완료:
  - `db/migrations/20260325_add_install_subtype_to_rule_condition.sql`
  - `db/migrations/20260325_add_draft_rule_table.sql`
- 재적재 완료:
  - `scripts/seed_rules.sql`

## 검증 결과

- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile backend/api/judge.py backend/engine/rule_engine.py backend/db/models.py backend/api/admin.py backend/tests/test_rule_engine_wall_sign_subtypes.py`
- `python3 -m unittest backend.tests.test_rule_engine_projecting_sign backend.tests.test_rule_engine_wall_sign_subtypes`
- 결과:
  - 벽면/상단간판 포함 회귀 테스트 30건 통과

## 현재 상태 요약

- 돌출간판 기준 모델 완료
- 벽면이용간판 일반/상단 분리 및 규칙 구현 완료
- 규칙 분해표 템플릿과 돌출간판 상세 분해표 작성 완료
- `law_chunk -> draft_rule -> rule_condition/rule_effect`로 이어지는 검수용 중간 단계 구조 완료

## 다음 세션 추천 시작점

1. `draft_rule` 실제 적재 경로 연결
   - RAG 검색 결과 또는 수동 추출 결과를 `draft_rule`로 저장하는 서비스/API 연결
2. 관리자 검수 UX 보강
   - draft 목록/상세/승인 흐름을 프런트 또는 운영 화면에 노출
3. 승인 시 보조 규칙 테이블(`industry_exception_rule`, `sign_count_rule`, `special_zone_rule`)까지 다룰지 범위 결정

## 주의사항

- `draft_rule` 승인 API는 현재 기본 `rule_condition` / `rule_effect` 승격만 처리한다.
- 보조 규칙 테이블 승격은 아직 미구현이다.
- 루트 디렉터리는 git 워크트리가 아니라 `git status`로 변경 파일 확인이 안 됐다.
- 상세 백로그 상태는 `docs/sign-rule-expansion-plan.md`와 `docs/handoff-sign-rule-expansion.md`를 같이 보는 편이 안전하다.
