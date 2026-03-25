# 📘 PRD: AI 기반 옥외광고 인허가 자문 웹앱 (광고판정)

## 1. 제품 개요

### 1.1 제품명
광고판정 (AdJudge)

### 1.2 제품 정의
본 서비스는 강남구 옥외광고 민원 응대 담당자를 위한 내부형 AI 보조 웹앱으로서,  
광고물 설치 조건 입력 시 허가·신고·불가 판정과 근거 조문, 행정 절차, 수수료를 일관된 형식으로 제공하는 시스템이다.

### 1.3 제품 목표
- 민원 응대 시간 단축
- 동일 조건에 대한 답변 표준화
- 법령 근거 기반 응답 제공
- NotebookLM 기반 수작업 검색 대체

### 1.4 서비스 포지션
- 시작: 참고용 실무 자문 보조도구
- 목표: 준공식 자문도구 수준
- 원칙: 최종 판단은 담당자 수행

---

## 2. 핵심 설계 원칙

1. 판정은 규칙 엔진이 수행한다  
2. 설명은 조문 기반으로 생성한다  
3. 모든 결과에는 출처와 버전이 포함된다  
4. 동일 입력 → 동일 결과 보장  
5. 법령은 계층 구조로 처리한다  
6. 데이터 업데이트는 코드가 아닌 관리자 UI에서 수행

---

## 3. 데이터 아키텍처

### 구조
API 기준원본 + PDF 보조원본 + 내부 규칙테이블

---

## 4. 데이터 스키마 (요약)

### document_master
- id, name, type, jurisdiction, effective_date, version, source_type, file_url

### provision
- id, document_id, article, paragraph, item, content, effective_date

### legal_relation
- id, from_provision, to_provision, relation_type

### rule_condition
- id, sign_type, floor_min, floor_max, light_type, digital, area_min, area_max, zone

### rule_effect
- id, rule_id, decision, review_type, safety_check, max_size, provision_id

### fee_rule
- id, sign_type, area_range, base_fee, light_weight, digital_weight, rounding_rule, provision_id

### checklist_rule
- id, work_type, required_docs, optional_docs, condition

### zone_rule
- id, name, restriction, prohibited_types, provision_id

### case_log
- id, input_data, output_data, rule_version, user, created_at

---

## 5. 기능 요구사항

### FR-1 입력 모듈
- 폼 + 챗봇 혼합
- 필수 입력 후 추가 질문 방식

### FR-2 판정 엔진
- 허가 / 신고 / 불가 판정

### FR-3 심의 분류
- 본심의 / 소심의 / 서울시심의

### FR-4 결과 출력
- 결론 + 근거 + 규격 + 수수료 + 서류

### FR-5 근거 표시
- 조문 링크 + 버전

### FR-6 수수료 계산
- 면적 + 가중치

### FR-7 체크리스트
- 작업 유형별 자동 생성

### FR-8 저장 및 공유
- PDF 생성
- 로그 저장

### FR-9 관리자 기능
- 법령 및 규칙 관리

---

## 6. 비기능 요구사항

- 응답 속도: 1초 이내
- 정확도: 95% 이상
- 동일 입력 동일 결과 보장
- 로그 저장 필수

---

## 7. MVP 범위

### 포함
- 강남구 기준
- 주요 광고물 4종
- 판정 + 수수료 + 서류

### 제외
- 이미지 분석
- 전국 확장
- GIS 기능

---

## 8. 실행 계획

1. 법령 API 연동
2. 조문 DB 구축
3. 규칙 정의
4. 판정 엔진 개발
5. UI 개발
6. 관리자 기능 구축

---

## 최종 정의

이 시스템은 법령 API 기반 조문 구조와 내부 규칙 엔진을 활용하여  
민원 응답을 자동 생성하는 행정 의사결정 보조 시스템이다.
