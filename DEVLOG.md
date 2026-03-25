# SignCheck - 개발 로그

AI 코딩 도구와 함께 진행한 개발 작업 기록입니다.

---

## 2026-03-20 (Day 1)

### 1. 프로젝트 기획 분석 및 구체화

```
'/home/jinkui/dev/SignCheck/광고판정_PRD.md'이거 분석해서 보고 해줘. 좀더 구체화 해보자
```

**Claude Code 작업:**
- 기존 PRD 문서 분석 및 피드백 제공
- 옥외광고물 허가/신고 판정 시스템의 핵심 기능 명세 구체화
- 판정 대상 간판 유형, 입력값, 출력값 구조 정의

---

### 2. 간판 대상 범위 확대

```
'/home/jinkui/dev/SignCheck/2025 옥외광고물 설치가이드(최최종)(수정).pdf'
4종으로 제한을 두지 말고 여기 파일에 있는 광고물은 다 대상이다
```

**Claude Code 작업:**
- PDF (2025 옥외광고물 설치가이드) 파싱 및 분석
- 기존 4종 제한 → 파일 내 전체 광고물 유형으로 확대 (돌출간판, 벽면이용간판, 옥상간판, 지주이용간판, 입간판, 현수막, 애드벌룬, 선전탑, 창문이용광고물 등)
- 확장된 간판 유형 목록 기반으로 PRD 업데이트

---

### 3. 기술 스택 확정

```
프론트엔드 Next.js (React 기반, SSR 가능, 추천)
백엔드는 내가 db를 백터db로 만든 거야. 법령 정보를 api로 불러와서 백터 db로 임베딩 하기 적당한 백엔드로 구성
db는 PostgreSQL
배포환경은 강남구 내부망 (인터넷 차단된 내부 서버)
```

**Claude Code 작업:**
- 기술 스택 분석 및 적합성 검토
- **프론트**: Next.js (App Router)
- **백엔드**: FastAPI (Python) — 내부망 배포 환경 고려
- **DB**: PostgreSQL (규칙 데이터) + pgvector (법령 임베딩)
- **AI**: LlamaIndex + Ollama (내부망 환경, 외부 API 불필요)
- 강남구 내부망 폐쇄망 환경 대응 아키텍처 설계

---

### 4. RAG 구조 설계 및 LlamaIndex 결정

```
아니 내 계획은 법령 api를 불러서 법령을 벡터db로 임베딩 하겠다는 의미다
아직 만들지는 않았다. RAG 챗봇 오픈소스, 깃허브 3개의 단어를 키워드로
sdk를 설치해서 작업하고 싶다.
```

```
내 생각도 LlamaIndex
```

**Claude Code 작업:**
- LlamaIndex SDK 선택 결정 (사용자 직관과 일치)
- 국가법령정보공단 Open API → 법령 수집 → 임베딩 파이프라인 설계
- `scripts/fetch_laws.py`, `scripts/embed_laws.py` 구조 설계
- Docker Compose 기반 전체 서비스 구성 설계

---

## 2026-03-22 (Day 2)

### 5. 국가법령정보공단 Open API 연동

```
자 그럼 이제 법령 api스크립트 만들어 보자 내가 어떤 것을 알려주면 될까?
```

**Claude Code 작업:**
- 수집 대상 확정: 옥외광고물법 + 시행령 + 서울시 조례 + 강남구 조례
- `scripts/fetch_laws.py` 작성 — 국가법령정보공단 API 연동
- `.env` 파일에 API 키 설정 가이드

---

### 6. 서울시 조례 법령 정확 지정

```
서울시 조례는 이거 아니야.
서울특별시 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 조례(서울특별시조례)(제9936호)(20260105)
요거 찾아라
```

**Claude Code 작업:**
- 국가법령정보공단 API에서 정확한 법령명 검색
- 법령 4종 최종 확정:
  - 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 법률 시행령
  - 서울특별시 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 조례 (제9936호)
  - 서울특별시 강남구 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 조례
- `law_documents/` 폴더에 JSON 형태로 저장

---

### 7. LlamaIndex 임베딩 파이프라인 구축

```
LlamaIndex 임베딩 파이프라인 (scripts/embed_laws.py)
```

**Claude Code 작업:**
- `scripts/embed_laws.py` 작성
- 법령 JSON → 조문 단위 청킹 → pgvector 임베딩 저장
- Ollama 로컬 모델 연동 (내부망 환경 대응)
- Docker Compose 서비스 구성: `adjudge-postgres`, `adjudge-ollama`, `adjudge-backend`

---

### 8. Docker 환경 구동 및 DB 초기화

```
도커 실행 중이다. 이 순서로 진행해라
Docker 실행 후 --init-db 테스트, 이후 FastAPI 판정 엔진 연동
```

**Claude Code 작업:**
- `docker compose up -d` 실행 및 컨테이너 상태 확인
- DB 스키마 초기화 (`--init-db` 플래그)
- 테이블 생성 확인: `rule_condition`, `rule_effect`, `fee_rule`, `zone_rule`, `checklist_rule`, `law_chunk`, `provision`, `document_master`
- FastAPI 서버 (`adjudge-backend`) 연동 테스트

---

### 9. /api/v1/judge 엔드포인트 테스트 및 버그 발견

```
백엔드가 정상 시작됐습니다. 이제 /api/v1/judge 테스트합니다.
```

**Claude Code 작업:**
- 돌출간판 허가 판정 API 첫 호출
- **버그 발견**: `max_spec` 모든 값이 `null` 반환
- 원인 추적: `rule_condition`, `rule_effect` 테이블이 완전히 비어있음 (0건)
- 엔진이 항상 기본 fallback 경로 진입 → `decision: "report"` (오류)

---

### 10. 법령 원문 분석 — 간판별 최대 규격 추출

```
추가테스트 필요하다. 돌출간판의 경우 가로 세로 최대 규격이 정해져 있다.
법규 목록에 모든 간판의 규격이 있다. 이건 매우 중요한 데이터다
```

**Claude Code 작업:**
- `law_documents/서울시_옥외광고물_조례_articles.json` 전수 분석
- 서울시 조례 제6조(돌출간판의 표시방법) 핵심 규격 추출:
  - 돌출폭(가로): 벽면으로부터 **1미터 이내**
  - 세로길이: **3.5미터 이내**
- 시행령 원문에서 허가/신고 분류 체계 확인:
  - 돌출간판 → 시행령 **제4조 허가** 대상 (기존 `"report"` 판정은 오류)
  - 의료기관·약국·이용업소 표지등 → 제5조 신고 대상 예외

---

### 11. 전체 간판 유형 규칙 DB 삽입 (15건)

```
다른 간판의 규칙도 추가해. 이건 아주 중요한 작업이다.
```

**Claude Code 작업:**
- 법령 조문별 provision ID 조회 및 매핑
- `rule_condition` + `rule_effect` 15개 규칙 삽입 (서울시 조례 기준)

| 간판 유형 | 판정 | 심의 | 핵심 규격 |
|-----------|------|------|-----------|
| 돌출간판 (자사) | 허가 | 소심의 | 돌출 1m, 세로 3.5m |
| 돌출간판 (타사) | 허가 | 대심의 | 돌출 1m, 세로 3.5m |
| 벽면이용간판 (1-5층) | 신고 | 소심의 | 가로 10m, 세로 80cm, 돌출 30cm |
| 벽면이용간판 (4-15층) | 허가 | 대심의 | 면적 225㎡, 돌출 40cm |
| 옥상간판 | 허가 | 대심의 | 수평거리 50m 이상 |
| 지주이용간판 (소형) | 신고 | 소심의 | 높이 5m, 1면 3㎡ |
| 지주이용간판 (일반) | 허가 | 소심의 | 높이 5m, 1면 3㎡ |
| 입간판 | 신고 | 소심의 | 자사광고만, 조명불가 |
| 현수막 | 신고 | 소심의 | 가로 70cm, 세로 2m |
| 애드벌룬 | 신고 | 소심의 | 높이 10m, 면적 100㎡ |
| 창문이용광고물 | 신고 | 소심의 | 가로·세로 30cm |
| 선전탑 | 허가 | 대심의 | 상업지역, 지정 장소만 |

---

### 12. API 재검증 — 전 유형 정상 확인

**Claude Code 작업:**
- 5개 간판 유형 API 호출 및 결과 검증

```
벽면이용간판(5층): permit | 대심의 | area: 225.0㎡ 이하 | protrusion: 0.4m 이내  ✓
지주이용간판(1층): report | 소심의 | height: 5.0m 이하  | area: 3.0㎡ 이하       ✓
창문이용광고물:    report | 소심의 | width: 0.3m 이내   | height: 0.3m 이하      ✓
애드벌룬:          report | 소심의 | height: 10.0m 이하 | area: 100.0㎡ 이하     ✓
현수막:            report | 소심의 | width: 0.7m 이내   | height: 2.0m 이하      ✓
```

- Before/After 비교 (돌출간판):
  - `decision`: `"report"` (오류) → `"permit"` (정상)
  - `max_spec.height`: `null` → `"3.5m 이하"`
  - `max_spec.protrusion`: `null` → `"1.0m 이내"`

---

## 기술 스택

- **Frontend**: Next.js (App Router, SSR)
- **Backend**: FastAPI (Python), Docker Compose
- **Database**: PostgreSQL + pgvector
- **AI/RAG**: LlamaIndex, Ollama (로컬 LLM)
- **법령 데이터**: 국가법령정보공단 Open API
- **배포**: 강남구 내부망 (폐쇄망)
- **AI 도구**: Claude Code (claude-sonnet-4-6)

---

## 주요 기능

1. **옥외광고물 허가/신고 판정 엔진**
   - 간판 유형, 층수, 면적, 조명 방식, 용도지역 등 입력
   - 허가(permit) / 신고(report) / 불가(prohibited) 자동 판정
   - 테헤란로 특수 조건 별도 처리

2. **최대 규격(max_spec) 자동 반환**
   - 서울시 조례 기준 간판별 최대 규격 (돌출폭, 높이, 면적, 가로)
   - 12개 간판 유형 15건 규칙 DB 탑재

3. **법령 RAG 근거 조문 검색**
   - 판정 결과와 함께 관련 법령 조문 3건 반환
   - 유사도 점수 포함

4. **수수료 자동 계산**
   - 간판 유형, 면적, 조명 방식에 따른 허가 수수료 산정

5. **필요 서류 목록 자동 생성**
   - 허가/신고 유형별 제출 서류 목록 반환

---

## 잔여 과제 (Day 2 기준)

- [x] 공연간판 규칙 추가 → Day 3에서 처리
- [x] 프론트엔드 구현 → Day 3에서 완료
- [ ] 옥상간판 세부 규격 보완 (시행령 별표 기준)
- [ ] 규칙 데이터를 시드 스크립트로 관리 (현재는 직접 SQL)
- [ ] 내부망 배포 환경 설정

---

## 2026-03-25 (Day 3) — Codex (GPT-5.4)

> 이날은 Claude Code 대신 **Codex (GPT-5.4)** 와 함께 9개 세션에 걸쳐 작업했습니다.

---

### 13. 프론트엔드 채팅 API 오류 수정

```
자 이제 구축된 프론트에서 실험을 하고 있는데, 추가질문을 했는데, 오류가 발생했습니다.
다시 시도해주세요라는 문구가 뜬다. 이거 고치고 싶다.
Failed to load resource: the server responded with a status of 404 (Not Found)
Access to fetch at 'http://localhost:8000/api/v1/chat' from origin 'http://localhost:3000' has been blocked
```

**Codex 작업:**
- `/api/v1/chat` 엔드포인트 404 원인 분석
- CORS 정책 오류 수정 (origin 허용 설정)
- 채팅 기능 정상화 확인

---

### 14. 판정 불가(prohibited) 누락 문제 발견

```
db를 확인하고 싶다. 지금 문제가 예를 들어 돌출간판이 설치층수 제한과 면적(가로, 세로)
제한을 규격을 바탕으로 불가 판정을 해줘야 하는데, 지금은 층수제한을 넘어도
"설치불가" 판정을 안해준다.
```

**Codex 작업:**
- DB 규칙 테이블 전수 검토
- 층수 제한 초과 시 prohibited 판정 미반영 원인 파악
- rule_condition 조건 로직 수정 설계

---

### 15. 벡터 DB 법령 내용 보강

```
지금 법률에서 벡터db로 옮긴 내용에 아래와 같은 정보가 포함되어 있어야 한다.
돌출간판
1. 일반적인 규격 제한
돌출 폭(가로): 벽면으로부터 1m 이내로 표시해야 합니다.
세로 길이: 3.5m 이내가 원칙이며, 건물의 1개 층 높이 이내로 표시해야 합니다.
두께: 30cm 이내여야 합니다...
```

**Codex 작업:**
- 기존 벡터 DB 청킹 내용 부족 확인
- 설치 위치, 세부 규격 등 상세 정보 law_chunk 재임베딩
- 판정 엔진과 벡터 DB 연계 목표 정의

```
내가 원하는 것은 벡터DB가 판정DB로 연계되어서 실제로 사용자에게 도움이 되는 것이다.
돌출간판처럼 설치불가이면 설치 불가 판정을 해줘야 한다.
```

---

### 16. 규칙 확장 계획 수립 — sign-rule-expansion-plan.md

```
돌출간판에서 시작해서 모든 간판으로 판정을 확장하는 계획을 세우고 보고해줘
```

**Codex 작업:**
- 전체 간판 유형별 규칙 확장 로드맵 수립
- `docs/sign-rule-expansion-plan.md` 작성 (Epic A~D 구조)
- 백로그 태스크 분류: TASK-A1~A5, TASK-B1~B2, TASK-C1~C3, Epic D

---

### 17. 개발 태스크 실행 및 병렬 작업 설정

```
docs/sign-rule-expansion-plan.md에 따라 개발 태스크를 만들어 보자
개발 백로그를 수행할 때마다 업데이트를 해줬으면 좋겠어.
그리고 개발속도를 빠르게 하기 위해서 멀티에이전트를 병렬로 할 수 있을까?
```

**Codex 작업:**
- CLAUDE.md에 백로그 자동 업데이트 규칙 설정
- "단일 에이전트 + 병렬 작업" 방식 결정
- TASK-A1 시작: 판정 엔진 기반 리팩터링
- TASK-A2 → A3 → A4 순차 실행

| 태스크 | 내용 |
|--------|------|
| TASK-A1 | 판정 엔진 prohibited 판정 로직 구현 |
| TASK-A2 | 돌출간판 층수/규격 초과 조건 rule_condition 반영 |
| TASK-A3 | 벽면이용간판 층수 기반 조건 추가 |
| TASK-A4 | 나머지 간판 유형 기본 prohibited 조건 추가 |

---

### 18. 컨텍스트 관리 — handoff.md 도입

```
컨텍스트 관리를 위해 이번 세션은 종료하고 새로운 세션으로 작업하려고 하는데,
docs/sign-rule-expansion-plan.md 이거만 다음 세션에 제공해주면 이어서 작업하나?
아님 추가로 인수인계를 위한 handoff.md를 만드는 게 나을까?
```

**Codex 작업:**
- 세션 간 컨텍스트 유실 문제 해결 방안 논의
- `docs/handoff-sign-rule-expansion.md` 생성
- 세션 종료 시마다 진행 상황, 완료 태스크, 다음 작업 기록

---

### 19. TASK-A5, B1, B2 — 예외 규칙 분리 및 DB 마이그레이션

```
TASK-A5로 예외 규칙을 보조 테이블로 분리 후에 TASK-B1 시작
TASK-B2 진행하자. DB 마이그레이션 언제 하는 게 좋을까?
```

**Codex 작업:**
- TASK-A5: 업종 예외 규칙을 `industry_exception_rule` 테이블로 분리
- TASK-B1: 업종 예외 적용 로직 판정 엔진에 연동
- TASK-B2: DB 마이그레이션 실행 (`db/migrations/20260325_fix_standing_sign_rules.sql`)
- handoff.md 업데이트

---

### 20. TASK-C1~C3, Epic D — RAG 연계 및 전체 완성

```
docs/handoff-sign-rule-expansion.md, docs/sign-rule-expansion-plan.md 참고해서
현재 상황 파악하고, TASK-C1 개발 시작하자
```

**Codex 작업:**
- TASK-C1: law_chunk RAG 추출 결과 → draft_rule 자동 적재 연결
- TASK-C2: draft_rule 승인 시 `industry_exception_rule`, `sign_count_rule`, `special_zone_rule` 자동 승격 흐름 구현
- TASK-C3: 관리자 UI에서 초안 규칙 검토/승인 기능 연동
- Epic D: 전체 마무리 구현

---

### 21. 422 오류 수정 및 판정 정확도 검증

```
사이트 테스트해보니까, Failed to load resource: the server responded with a status of 422 (Unprocessable Entity)
판정하기 누르면 아래와 같은 에러 뜬다.
db에 정보에 따르면 돌출간판은 5층 이상은 설치불가 판정이 나와야 하는데.
```

**Codex 작업:**
- API 요청 스키마 불일치(422) 원인 수정
- 돌출간판 5층 이상 `prohibited` 판정 정상화 확인
- 입간판 11층, 30㎡ 설치불가 판정 수정

```
좋네 잘 반영되네, 좋은데
```

---

### 22. Git 초기화 및 GitHub 원격 저장소 연결

```
깃 초기화해주세요
https://github.com/kangjinkui/signcheck.git 여기 원격 저장소로 푸시하고 싶다
```

**Codex 작업:**
- `git init` 및 `.gitignore` 설정
- GitHub 원격 저장소 연결 및 초기 푸시

---

### 23. 배포 방안 논의

```
이제 배포를 하고 싶은데, 어떤 방법이 좋을까?
그럼 나한테 디지털오션 VM이 있어. 거기에 올리는 형태로 할 수도 있겠네
4 vCPU / 8GB RAM 이 정도 하려면 요금제가 얼마지?
너무 비싸서 안 되겠다. 회사에 폐쇄망에 내 IP가 있는데, 내 PC를 서버로 해서
IP 주소 기반으로 배포 가능할까? PC는 윈도우를 사용하고 있고, Docker를 사용해서 배포할 계획이다.
```

**Codex 작업:**
- DigitalOcean 비용 분석 ($48/월 — 예산 초과로 포기)
- Windows PC + Docker 기반 폐쇄망 내부 배포 방안 설계
- `docker-compose.prod.yml`, `backend/Dockerfile.prod`, `frontend/Dockerfile.prod` 작성
- `docs/deployment-plan-windows-intranet.md` 배포 가이드 작성

---

### 24. 간판 유형별 세부 조건 추가

```
돌출간판은 추가 조건이 있다. 벽면이용간판 상단간판도 추가 조건이 있다.
다른 간판도 규격이 개별 규격이 있는데 그것도 반영해줘
```

**Codex 작업:**
- 간판별 세부 조건 추가:
  - 벽면이용간판: 가로 길이가 건물 벽면 폭의 1/3 초과 시 불가
  - 입간판: 바닥면 가로 0.5m × 세로 0.7m 초과 불가, 건물면에서 1m 초과 불가, 보행로 설치 불가
  - 옥상간판: 지상 구조물 설치 위치 제한 조건 추가
  - 지주이용간판: 도로변 이격 거리 조건 추가
- 선전탑: 실무 비사용 사유로 제외 결정

```
선전탑은 아예 실무에서 잘 사용되지 않으니까 빼버려
```

---

### 25. 프론트엔드 세부 조건 입력 필드 추가

```
추가한 세부 조건들이 지금 프론트 서버에 반영이 안되어 있어.
옥상간판, 지주이용간판, 입간판 등 말이야
```

**Codex 작업:**
- `frontend/components/JudgeForm.tsx` — 간판 유형별 조건부 입력 필드 추가
- 옥상간판, 지주이용간판, 입간판 전용 입력 UI 구현
- Docker 재빌드 없이 핫리로드로 프론트 반영

---

## 커밋 히스토리

| 날짜 | 커밋 | 설명 |
|------|------|------|
| 03/25 | `44952a2` | Ignore local metadata and embedded repo |
| 03/20 | `4f207d8` | Initial commit |

---

## 기술 스택

- **Frontend**: Next.js (App Router, SSR)
- **Backend**: FastAPI (Python), Docker Compose
- **Database**: PostgreSQL + pgvector
- **AI/RAG**: LlamaIndex, Ollama (로컬 LLM)
- **법령 데이터**: 국가법령정보공단 Open API
- **배포**: Windows PC + Docker (폐쇄망 내부 IP 기반)
- **AI 도구**: Claude Code (claude-sonnet-4-6) → Codex (GPT-5.4)

---

## 주요 기능 (완성 기준)

1. **옥외광고물 허가/신고/불가 판정 엔진**
   - 간판 유형, 층수, 면적, 조명 방식, 용도지역 등 입력
   - 허가(permit) / 신고(report) / 불가(prohibited) 자동 판정
   - 층수·규격 초과 시 prohibited 판정 포함

2. **세부 조건 판정**
   - 돌출간판: 돌출폭, 세로 길이, 두께 초과 조건
   - 벽면이용간판: 벽면 폭 1/3 초과 조건
   - 입간판: 바닥면 규격, 보행로 설치 금지

3. **법령 RAG 근거 조문 연계**
   - 판정 결과와 함께 관련 법령 조문 반환
   - draft_rule → 실제 rule 자동 승격 흐름

4. **업종 예외 처리**
   - 의료기관, 약국, 이용업소 등 업종별 예외 규칙 별도 테이블 관리

5. **관리자 도구**
   - 규칙 초안(draft_rule) 검토 및 승인 UI
   - 실시간 규칙 CRUD

6. **배포 환경**
   - Windows PC + Docker Compose (폐쇄망 내부 배포)
   - 프로덕션용 Dockerfile 분리
