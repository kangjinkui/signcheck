# Sign Rule Expansion Handoff

## 목적

이 문서는 `docs/sign-rule-expansion-plan.md` 기반 확장 작업을 다음 세션에서 빠르게 이어가기 위한 인수인계 요약이다.

## 이번 세션 완료 범위

- `TASK-A1` 완료
  - 요청/응답 스키마 확장
  - 돌출간판 확장 입력 필드 추가
  - 결과에 `administrative_action`, `safety_check`, `matched_rule_id`, `missing_fields`, `fallback_reason` 추가
- `TASK-A2` 완료
  - 엔진 fallback 정책 분리
  - `missing_input` vs `missing_rule` 구분
- `TASK-A3` 완료
  - 돌출간판 전용 다단계 판정 흐름 구현
  - 업종 특례, 테헤란로, 층수/규격/이격/수량/심의 특례/안전점검 반영
- `TASK-A4` 완료
  - `rule_condition`, `rule_effect` 스키마 확장
  - ORM 모델과 `db/init.sql` 일치시킴
- `TASK-A6` 완료
  - `scripts/seed_rules.sql`의 돌출간판 시드를 새 컬럼 기준으로 재작성
  - 금지/특례/심의 특례 규칙 분리
- `TASK-A7` 완료
  - 돌출간판 엔진 회귀 테스트 18건 추가
  - `missing_input`, `missing_rule`, 특례 업종, 심의 특례 포함
- `TASK-A5` 완료
  - 업종 특례, 수량 특례, 테헤란로 금지 규칙을 보조 테이블로 분리
  - 엔진 보조 규칙 조회 순서 고정
- `TASK-B1` 완료
  - 공통 입력/출력 타입 구조 정리
  - `install_subtype`, `form_type`, `content_type`, `display_orientation`, `special_zone` 필드 이름 정리
- `TASK-B2` 완료
  - 돌출간판 판정 단계를 별도 함수와 컨텍스트 객체로 분리
  - 후속 광고물 유형 확장을 위한 엔진 파이프라인 형태 정리
- `TASK-C1` 완료
  - `rule_condition.install_subtype` 추가
  - 벽면이용간판을 `wall_sign_general_under_5f`, `wall_sign_top_building`으로 분리
  - API/엔진/프런트에서 벽면 하위 유형 입력 연결
- `TASK-C2` 완료
  - 일반 벽면이용간판 전용 입력 필드 추가
  - `1업소 1개`, 곡각/전후면 도로 예외 `2개`, `3층 이하 판류형`, `4층 이상 입체형만` 판정 구현
  - `무신고 가능`을 `decision=permit`, `administrative_action=none`으로 매핑
- `TASK-C3` 완료
  - 건물 상단간판 전용 입력 필드 추가
  - 최상단 여부, 상단 3면 제한, 입체형 전용, 표시 내용 제한, 가로형/세로형 규격 계산 구현
  - 상단간판 허용 케이스는 항상 `review_type`을 반환하도록 고정
- `TASK-D1` 완료
  - 규칙 분해표 템플릿 문서 작성
  - 돌출간판 규칙 분해표 상세본 작성
- `TASK-D2` 완료
  - `draft_rule` 검수용 중간 테이블 설계
  - 관리자 API에 초안 생성/조회/수정/승인 흐름 추가
- `TASK-D3` 완료
  - `law_chunk` / RAG 검색 결과를 `draft_rule`로 적재하는 실제 import 경로 추가
  - 추출된 `condition_payload`, `effect_payload`, `auxiliary_payload`를 검수용 초안으로 함께 저장 가능
- `TASK-D4` 완료
  - `draft_rule` 승인 시 `industry_exception_rule`, `sign_count_rule`, `special_zone_rule` 자동 승격 추가
  - 승인 결과로 생성된 보조 규칙 ID를 `draft_rule`에 기록
- DB 마이그레이션 완료
  - 개발 DB(`adjudge-postgres`)에 A4/A5 스키마 변경을 실제 적용
  - 돌출간판 규칙 시드 재적재 완료

상태 기준 문서는 [`docs/sign-rule-expansion-plan.md`](/home/jinkui/dev/SignCheck/docs/sign-rule-expansion-plan.md)를 확인하면 된다.

## 실제 변경 파일

- [`backend/api/judge.py`](/home/jinkui/dev/SignCheck/backend/api/judge.py)
- [`backend/api/admin.py`](/home/jinkui/dev/SignCheck/backend/api/admin.py)
- [`backend/engine/rule_engine.py`](/home/jinkui/dev/SignCheck/backend/engine/rule_engine.py)
- [`backend/db/models.py`](/home/jinkui/dev/SignCheck/backend/db/models.py)
- [`backend/tests/test_rule_engine_projecting_sign.py`](/home/jinkui/dev/SignCheck/backend/tests/test_rule_engine_projecting_sign.py)
- [`backend/tests/test_draft_rule_service.py`](/home/jinkui/dev/SignCheck/backend/tests/test_draft_rule_service.py)
- [`backend/tests/test_admin_draft_rule_approval.py`](/home/jinkui/dev/SignCheck/backend/tests/test_admin_draft_rule_approval.py)
- [`backend/services/rag_service.py`](/home/jinkui/dev/SignCheck/backend/services/rag_service.py)
- [`backend/services/draft_rule_service.py`](/home/jinkui/dev/SignCheck/backend/services/draft_rule_service.py)
- [`db/migrations/20260325_add_draft_rule_aux_approval_tracking.sql`](/home/jinkui/dev/SignCheck/db/migrations/20260325_add_draft_rule_aux_approval_tracking.sql)
- [`frontend/lib/api.ts`](/home/jinkui/dev/SignCheck/frontend/lib/api.ts)
- [`frontend/components/JudgeForm.tsx`](/home/jinkui/dev/SignCheck/frontend/components/JudgeForm.tsx)
- [`frontend/components/JudgeResult.tsx`](/home/jinkui/dev/SignCheck/frontend/components/JudgeResult.tsx)
- [`db/init.sql`](/home/jinkui/dev/SignCheck/db/init.sql)
- [`db/migrations/20260325_expand_sign_rule_schema.sql`](/home/jinkui/dev/SignCheck/db/migrations/20260325_expand_sign_rule_schema.sql)
- [`scripts/seed_rules.sql`](/home/jinkui/dev/SignCheck/scripts/seed_rules.sql)
- [`docs/sign-rule-expansion-plan.md`](/home/jinkui/dev/SignCheck/docs/sign-rule-expansion-plan.md)

## 현재 중요한 상태

- 백로그 문서는 작업할 때마다 업데이트하도록 규칙이 이미 [`CLAUDE.md`](/home/jinkui/dev/SignCheck/CLAUDE.md)에 반영되어 있다.
- `TASK-A1` ~ `TASK-A7`, `TASK-B1`, `TASK-B2`, `TASK-D1` ~ `TASK-D4`는 `done` 상태다.
- 다음 추천 시작점은 `draft_rule` payload 표준안 정리와 법령 개정 시 영향 규칙 자동 식별 쪽이다.
- 개발 DB에는 `20260325_expand_sign_rule_schema.sql` 적용 후 `scripts/seed_rules.sql` 재적재까지 끝났다.
- 확인된 현재 규칙 개수:
  - `rule_condition`: 21
  - `industry_exception_rule`: 2
  - `sign_count_rule`: 3
  - `special_zone_rule`: 1

## 다음 세션 추천 순서

1. `draft_rule`의 `auxiliary_payload` 표준 스키마를 문서로 고정
2. 법령 개정 시 영향 받는 `draft_rule` / 운영 규칙 자동 식별 설계
3. 추가 스키마 변경이 나오면 새 증분 마이그레이션 파일로 이어서 누적

## 임시 구현 사항

- `TASK-A3` 당시 넣었던 돌출간판 임시 상수 중 두께, 이격, 수량, 안전점검 기준은 이번 세션에서 `rule_effect` 컬럼 조회로 치환했다.
- 업종 특례, 수량 특례, 테헤란로 금지 규칙은 보조 테이블 조회로 옮겼다.
- 업종 분류 자체는 아직 문자열 키워드 매칭이라, 향후 정책 운영 단계에서는 코드 테이블 또는 관리자 매핑으로 교체하는 편이 낫다.

## DB 적용 상태

- 개발 DB 기준 아래 순서로 실제 반영 완료:
  - `db/migrations/20260325_expand_sign_rule_schema.sql`
  - `scripts/seed_rules.sql`
- 동일 환경 재적용 명령:

```bash
docker compose exec -T postgres psql -U adjudge -d adjudge -f /dev/stdin < db/migrations/20260325_expand_sign_rule_schema.sql
docker compose exec -T postgres psql -U adjudge -d adjudge -f /dev/stdin < scripts/seed_rules.sql
```
- 주의:
  - `scripts/seed_rules.sql`은 `rule_condition`과 보조 규칙 테이블을 `TRUNCATE` 후 재적재한다.
  - 운영/공유 DB에는 동일 방식을 그대로 쓰지 말고, 데이터 보존 기준을 먼저 정해야 한다.

## 검증 방법

- 파이썬 문법 검증은 아래 방식 사용

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile backend/api/judge.py backend/engine/rule_engine.py backend/db/models.py
```

- 이유:
  - 저장소 내부 `backend/api/__pycache__`, `backend/engine/__pycache__`가 `root:root`라 기본 `py_compile`가 실패할 수 있다.
  - `/tmp`로 캐시를 돌리면 정상 검증 가능하다.

## 주의점

- `backend/api/judge.py`는 돌출간판일 때 확장 필드를 서버 validation으로 강제한다.
- `missing_input`은 엔진 레벨에서도 별도로 존재한다.
- 다음 세션에서 API 테스트를 할 때는 돌출간판 요청에 확장 필드를 전부 넣어야 한다.

## 빠른 재시작용 문장

다음 세션에서는 `docs/sign-rule-expansion-plan.md`와 이 문서를 함께 읽고, `draft_rule`의 `auxiliary_payload` 표준 스키마와 법령 개정 영향 분석 흐름을 정리하면 된다. 돌출간판 기준 모델, 벽면이용간판 규칙 구현, 규칙 문서화, 검수용 중간 테이블, `law_chunk`/RAG -> `draft_rule` 적재 연결, 보조 규칙 자동 승격은 끝났다.
