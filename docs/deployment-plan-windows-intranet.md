# Deployment Plan: Windows PC + Docker on Closed Network

## 목적

이 문서는 SignCheck를 사내 폐쇄망 환경에서 Windows PC를 서버 호스트로 사용해 Docker 기반으로 배포하기 위한 실행 계획이다.

목표는 아래와 같다.

- 사내 고정 IP 기반 내부 접속 제공
- 클라우드 비용 없이 내부 시범 운영 가능
- 현재 개발 구조를 크게 바꾸지 않고 운영 환경으로 전환
- 프런트엔드, 백엔드, DB, Ollama를 일관된 방식으로 관리

## 배포 목표

- 사용자 접속 주소: `http://<사내고정IP>`
- 배포 환경: Windows 10/11 또는 Windows Server + Docker Desktop
- 네트워크 범위: 사내 내부망 전용
- 런타임: Docker Compose
- 서비스 구성:
  - `nginx`: 진입점 및 reverse proxy
  - `frontend`: Next.js 운영 서버
  - `backend`: FastAPI 운영 서버
  - `postgres`: 판정 규칙/로그 저장소
  - `ollama`: 임베딩/RAG 지원

## 권장 아키텍처

```text
사내 사용자 브라우저
        |
        v
http://<사내고정IP>
        |
        v
      nginx
   /         \
  /           \
frontend      backend (/api)
                 |
          -----------------
          |               |
       postgres         ollama
```

운영 원칙은 아래와 같다.

- 외부에서 직접 접근 가능한 포트는 `80`만 연다.
- `postgres`, `ollama`, `backend`는 내부 Docker 네트워크에서만 통신한다.
- 앱 구성은 운영용 `docker-compose.prod.yml`로 분리한다.

## 현재 구조 기준 판단

현재 프로젝트는 이미 컨테이너 중심 구조다.

- [`docker-compose.yml`](/home/jinkui/dev/SignCheck/docker-compose.yml)
- [`backend/Dockerfile`](/home/jinkui/dev/SignCheck/backend/Dockerfile)
- [`frontend/Dockerfile`](/home/jinkui/dev/SignCheck/frontend/Dockerfile)

다만 현재 상태는 개발용에 가깝다.

- `frontend`는 `npm run dev`를 사용한다.
- `backend`는 `uvicorn --reload`를 사용한다.
- 개발용 소스 마운트가 포함되어 있다.
- 운영용 reverse proxy가 없다.

따라서 배포 전에는 운영 전환 작업이 선행되어야 한다.

## 배포 방식 선택

이번 배포의 기본 선택은 아래와 같다.

- 운영 모델: 단일 Windows PC 호스트
- 컨테이너 오케스트레이션: Docker Compose
- 노출 방식: 사내 IP 기반 HTTP 접근
- DNS: 선택 사항
  - 초기에는 IP 직접 접근
  - 추후 사내 DNS가 가능하면 내부 도메인 연결

이 방식이 적합한 이유는 다음과 같다.

- 클라우드 비용이 들지 않는다.
- 현재 레포 구조를 거의 유지할 수 있다.
- 폐쇄망 내부 시범 운영에 충분하다.
- Ollama 같은 무거운 구성요소를 한 호스트에서 제어하기 쉽다.

## 배포 전제조건

### 인프라 전제

- 사내 고정 IP가 부여된 Windows PC 1대
- PC 상시 전원 유지 가능
- 사내망 내 다른 사용자 PC에서 해당 IP 접근 가능
- 방화벽에서 HTTP 포트 허용 가능
- Docker Desktop 사용 가능

### 시스템 권장 사양

- CPU: 4코어 이상
- RAM: 최소 8GB, 권장 16GB
- 디스크: 최소 50GB 여유 공간
- 네트워크: 사내 고정 IP

권장 사양을 높게 보는 이유는 Ollama와 Postgres가 함께 메모리/디스크를 사용하기 때문이다.

### 운영 정책 전제

- 업무용 PC와 서버 역할을 동시에 수행할 경우 재부팅/절전 리스크를 감수해야 한다.
- Windows 자동 업데이트 정책을 확인해야 한다.
- 장애 시 수동 재시작 담당자가 명확해야 한다.

## 운영용 배포 구성

### 필수 구성요소

1. `nginx`
- 80 포트로 요청 수신
- `/` 경로를 프런트엔드로 전달
- `/api` 경로를 백엔드로 전달

2. `frontend`
- Next.js production build 사용
- `npm run build` 후 `npm run start`

3. `backend`
- FastAPI production mode 사용
- `--reload` 제거
- 필요 시 worker 수 조정

4. `postgres`
- 데이터 영속 볼륨 사용
- 외부 포트 미노출 권장

5. `ollama`
- 모델 저장 볼륨 사용
- 외부 포트 미노출 권장

### 환경변수

운영용 `.env`는 별도 분리한다.

예시:

```env
POSTGRES_DB=adjudge
POSTGRES_USER=adjudge
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql+asyncpg://adjudge:<strong-password>@postgres:5432/adjudge
OLLAMA_BASE_URL=http://ollama:11434
NEXT_PUBLIC_API_URL=http://<사내고정IP>/api
PRIVATEGPT_URL=http://privategpt:8080
```

주의:

- `NEXT_PUBLIC_API_URL`은 운영에서는 `http://localhost:8000`이면 안 된다.
- 프런트가 브라우저에서 접근할 주소 기준으로 설정해야 한다.

## 네트워크 및 포트 정책

권장 포트 정책은 다음과 같다.

- 외부 개방:
  - `80/tcp`

- 외부 비개방:
  - `3000`
  - `8000`
  - `5432`
  - `11434`

초기 테스트를 위해 임시로 `3000`, `8000`을 열 수는 있지만, 운영 전환 시에는 `nginx` 하나만 공개하는 것이 맞다.

## 데이터 및 영속화 정책

### 반드시 영속화할 데이터

- Postgres 데이터 디렉터리
- Ollama 모델 디렉터리

### 백업 대상

- Postgres dump
- `scripts/seed_rules.sql`
- 법령 원문/가공 데이터
- 운영용 `.env`
- nginx 설정
- 운영용 compose 파일

### 백업 주기 권장

- DB dump: 일 1회
- 운영 설정 파일: 변경 시 즉시 백업
- 법령/규칙 데이터: 변경 시 즉시 백업

## 배포 단계

### 1단계: 운영용 파일 분리

작업 항목:

- 운영용 `frontend/Dockerfile` 작성
- 운영용 `backend/Dockerfile` 또는 실행 명령 정리
- `docker-compose.prod.yml` 작성
- `nginx.conf` 작성
- `.env.example` 작성

목표:

- 개발용 설정과 운영용 설정을 분리
- 운영 환경에서 hot-reload가 동작하지 않도록 고정

### 2단계: 애플리케이션 운영 모드 전환

작업 항목:

- `frontend`를 `build + start` 구조로 변경
- `backend`에서 `--reload` 제거
- 개발용 소스 볼륨 제거
- `container_name` 의존성 최소화
- healthcheck 추가 검토

목표:

- 재현 가능한 운영 컨테이너 구성 확보

### 3단계: Windows 호스트 준비

작업 항목:

- Docker Desktop 설치
- WSL2 활성화
- Docker Desktop의 리소스 제한 설정 확인
- 프로젝트 폴더를 고정 경로에 배치
- Windows Defender Firewall 인바운드 규칙 설정
- 절전 모드 해제
- 자동 재부팅 정책 확인

목표:

- 서버 역할에 필요한 호스트 조건 확보

### 4단계: 내부망 배포

작업 항목:

- 이미지 빌드
- `docker compose -f docker-compose.prod.yml up -d`
- DB 초기화 및 시드 적재
- Ollama 모델 다운로드
- 접속 확인

검증 항목:

- `http://<사내고정IP>` 접속 성공
- 메인 화면 표시
- `/api/v1/judge` 요청 성공
- 로그 저장 정상 동작
- RAG 검색 실패 시에도 판정은 정상 반환

### 5단계: 운영 안정화

작업 항목:

- 장애 대응 절차 문서화
- 정기 백업 스크립트 작성
- 로그 점검 절차 정리
- 재배포 절차 정리

목표:

- 담당자가 바뀌어도 유지 가능한 운영 문서 확보

## 운영 절차

### 최초 배포 절차

1. 레포 최신본 반영
2. 운영용 `.env` 작성
3. `docker compose -f docker-compose.prod.yml build`
4. `docker compose -f docker-compose.prod.yml up -d`
5. DB 마이그레이션/초기화 적용
6. 규칙 시드 적재
7. Ollama 모델 pull
8. 웹/UI/API 확인

### 업데이트 배포 절차

1. 코드 pull
2. 변경 영향 확인
3. 필요 시 이미지 rebuild
4. `docker compose -f docker-compose.prod.yml up -d --build`
5. API/UI smoke test

### 장애 복구 절차

1. `docker compose ps`로 상태 확인
2. `docker compose logs`로 에러 확인
3. 문제 컨테이너 재시작
4. DB 이상 시 백업에서 복구
5. 필요한 경우 전체 스택 재기동

## 보안 고려사항

폐쇄망이라도 아래는 지켜야 한다.

- `postgres` 외부 직접 노출 금지
- `ollama` 외부 직접 노출 금지
- 관리자용 기능 접근 범위 확인
- `.env` 파일 Git 제외 유지
- 강한 DB 비밀번호 사용
- 운영 PC에 불필요한 포트 개방 금지

가능하면 추가로 고려할 항목:

- 사내 IP 대역만 허용하는 방화벽 정책
- 관리자 화면 접근 제어
- 운영자 계정 분리

## 리스크 및 대응

### 리스크 1: Windows PC 재부팅/절전

영향:

- 서비스 중단

대응:

- 절전 해제
- 자동 로그인/자동 시작 정책 검토
- Docker Desktop 시작 정책 확인

### 리스크 2: Ollama 자원 사용량

영향:

- 응답 지연
- 메모리 부족

대응:

- 초기에는 최소 모델만 사용
- 메모리 사용량 모니터링
- 필요 시 별도 호스트 분리 검토

### 리스크 3: 업무용 PC와 서버 역할 충돌

영향:

- 성능 저하
- 예기치 않은 종료

대응:

- 가급적 서버 전용 PC 사용
- 최소한 장시간 절전/종료 금지

### 리스크 4: 운영자 의존성

영향:

- 문제 발생 시 대응 지연

대응:

- 배포/복구 절차 문서화
- 백업 위치와 명령어 표준화

## 권장 운영 판단

이번 프로젝트의 현재 단계에서는 아래 방향이 적절하다.

- 1차 목표: 사내 폐쇄망 시범 운영
- 배포 형태: Windows PC 단일 호스트
- 접속 방식: 사내 고정 IP
- 구성 방식: Docker Compose + nginx

이는 비용, 구현 난이도, 현재 코드 구조를 모두 고려했을 때 가장 현실적인 선택이다.

다만 정식 운영으로 확대되면 아래를 재검토해야 한다.

- Linux 전용 서버 전환
- DB 백업 자동화
- Ollama 분리 호스팅
- HTTPS 또는 사내 인증 프록시 연동
- 관리자 접근 통제 강화

## 이번 계획의 실행 범위

즉시 수행 가능한 범위:

- 운영용 Docker 구성 파일 작성
- 운영용 Nginx 구성 작성
- Windows 배포 절차 문서화

후속 확장 범위:

- 백업 스크립트 작성
- 자동 기동 스크립트 작성
- 사내 DNS 또는 내부 도메인 연동

## 다음 작업 제안

다음 구현 순서는 아래가 적절하다.

1. `docker-compose.prod.yml` 작성
2. `nginx.conf` 작성
3. `frontend/Dockerfile` 운영 모드 전환
4. `backend` 운영 실행 명령 정리
5. `DEPLOYMENT.md` 또는 운영 절차 문서 보강
6. Windows 실제 배포 테스트

