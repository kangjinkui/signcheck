# 돌출간판 규칙 분해표

## 1. 기본 정보

- 광고물 유형: `돌출간판`
- 하위 유형: 없음
- 작성 일자: `2026-03-25`
- 작성자: Codex
- 검토 상태: `reviewed`

## 2. 근거 조문

| 구분 | 문서 | 조문 | 요약 | 우선순위 메모 |
| --- | --- | --- | --- | --- |
| 시행령 | 옥외광고물법 시행령 | 제4조, 제5조 | 허가/신고 기준과 유형별 기본 제한 | 상위 법령 기준 |
| 조례 | 서울특별시 옥외광고물 조례 | 제4조 | 세로, 돌출폭, 두께, 이격, 높이 기준의 핵심 출처 | 엔진 기본 수치의 주 근거 |
| 심의기준 | 강남구 옥외광고물 심의기준 | 돌출간판 기준 | 테헤란로, 업종 특례, 심의 특례 운용 기준 | 지역 운영기준 |
| 예외/특례 | 강남구 심의기준 / 운영 해석 | 이미용업, 의료기관/약국 | 업종별 수량 및 규격 완화 | 보조 규칙으로 분리 |

## 3. 필수 입력 필드

| 필드 | 타입 | 필수 여부 | 설명 | 현재 코드 반영 여부 |
| --- | --- | --- | --- | --- |
| sign_type | string | Y | `돌출간판` 고정 | Y |
| floor | int | Y | 설치 층수 | Y |
| area | float | Y | 기본 면적 | Y |
| zone | string | Y | 용도지역 | Y |
| ad_type | string | Y | 자사/타사 | Y |
| business_category | string | Y | 업종 특례 분기 | Y |
| height | float | Y | 세로 길이 | Y |
| width | float | Y | 가로 길이 | Y |
| protrusion | float | Y | 돌출폭 | Y |
| thickness | float | Y | 두께 | Y |
| bottom_clearance | float | Y | 지면 이격 | Y |
| top_height_from_ground | float | Y | 지면 기준 상단 높이 | Y |
| face_area | float | Y | 1면 면적 | Y |
| building_height | float | Y | 건물 높이 | Y |
| floor_height | float | Y | 층고 | Y |
| existing_sign_count_for_business | int | Y | 업소당 기설치 수량 | Y |
| existing_sign_types | list[string] | N | 기존 간판 종류 | Y |
| has_sidewalk | bool | Y | 보도 유무 | Y |
| special_zone | string | N | 특수구역 | Y |
| exception_review_approved | bool | Y | 심의 특례 승인 여부 | Y |

## 4. 규칙 분해표

### 4.1 위치 규정

| 규칙 ID | 설명 | 입력 필드 | 판정 결과 | DB 표현 |
| --- | --- | --- | --- | --- |
| PS-LOC-01 | 5층 초과 설치 금지 | `floor` | `prohibited` | 엔진 전용 위치 판정 |
| PS-LOC-02 | 간판 상단은 건물 높이 초과 금지 | `top_height_from_ground`, `building_height` | `prohibited` | `rule_effect.max_top_height_relative_building` |
| PS-LOC-03 | 지면 기준 상단 높이 상한 | `top_height_from_ground` | `prohibited` | `rule_effect.max_top_height_from_ground` |

### 4.2 규격 규정

| 규칙 ID | 설명 | 입력 필드 | 판정 결과 | DB 표현 |
| --- | --- | --- | --- | --- |
| PS-SPEC-01 | 세로 길이 상한 | `height`, `floor_height` | 초과 시 `prohibited` | `rule_effect.max_height` |
| PS-SPEC-02 | 돌출폭 상한 | `protrusion` | 초과 시 `prohibited` | `rule_effect.max_protrusion` |
| PS-SPEC-03 | 두께 상한 | `thickness` | 초과 시 `prohibited` | `rule_effect.max_thickness` |
| PS-SPEC-04 | 보도 유무별 지면 이격 | `bottom_clearance`, `has_sidewalk` | 미달 시 `prohibited` | `rule_effect.min_bottom_clearance`, `min_bottom_clearance_no_sidewalk` |

### 4.3 수량 규정

| 규칙 ID | 설명 | 입력 필드 | 판정 결과 | DB 표현 |
| --- | --- | --- | --- | --- |
| PS-CNT-01 | 업소당 기본 1개 | `existing_sign_count_for_business` | 초과 시 `prohibited` | `rule_effect.max_count_per_business` |
| PS-CNT-02 | 기존 벽면간판과 총량 충돌 | `existing_sign_types` | 충돌 시 `prohibited` | `rule_effect.requires_no_existing_wall_sign` |
| PS-CNT-03 | 의료기관/약국 수량 완화 | `business_category`, `existing_sign_count_for_business` | 2개까지 허용 | `sign_count_rule` |

### 4.4 특례/예외

| 규칙 ID | 설명 | 입력 필드 | 판정 결과 | DB 표현 |
| --- | --- | --- | --- | --- |
| PS-EX-01 | 이·미용업 규격 특례 | `business_category` | 규격 상한 교체 | `industry_exception_rule` |
| PS-EX-02 | 의료기관/약국 수량 특례 | `business_category` | 수량 기준 완화 | `sign_count_rule` |
| PS-EX-03 | 테헤란로 금지 | `special_zone`, `tehranro` | 즉시 `prohibited` | `special_zone_rule` |
| PS-EX-04 | 심의 특례 승인 | `exception_review_approved` | 규격 초과를 경고로 완화 | 엔진 전용 예외 흐름 |

### 4.5 안전점검 / 심의 / 절차

| 규칙 ID | 설명 | 입력 필드 | 판정 결과 | DB 표현 |
| --- | --- | --- | --- | --- |
| PS-PROC-01 | 타사광고 대심의 | `ad_type` | `review_type=대심의` | `rule_effect.review_type` |
| PS-PROC-02 | 안전점검 대상 계산 | `top_height_from_ground`, `face_area` | `safety_check=true` | `rule_effect.safety_check_min_height`, `safety_check_min_area` |
| PS-PROC-03 | 행정절차 축 분리 | `decision` | `permit/report` 매핑 | `administrative_action` |

## 5. DB 매핑

### 5.1 `rule_condition`

| 컬럼 | 값/조건 | 비고 |
| --- | --- | --- |
| sign_type | `돌출간판` | 기본 규칙 키 |
| ad_type | `self`, `third_party`, `both` | 자사/타사 분기 |
| special_zone | `tehranro` | 특수구역 규칙 연결 |
| existing_sign_count_for_business | nullable | 직접 비교보다는 보조 규칙과 병행 |
| has_sidewalk | nullable | 이격 기준 분기 |
| exception_review_approved | nullable | 심의 특례 승인값 분기 |
| priority | 낮을수록 우선 | 기본 규칙 매칭 순서 |

### 5.2 `rule_effect`

| 컬럼 | 값/조건 | 비고 |
| --- | --- | --- |
| decision | `permit` 또는 `report` | 기본 판정축 |
| administrative_action | `permit`, `report`, `none` | 사용자 안내용 절차 축 |
| review_type | `소심의`, `대심의`, `심의특례` | 심의 분기 |
| max_height | 기본 3.0m | 층고와 함께 비교 |
| max_protrusion | 기본 1.0m | 특례 시 교체 가능 |
| max_thickness | 기본 0.3m | 특례 시 교체 가능 |
| min_bottom_clearance | 3.0m | 보도 있음 |
| min_bottom_clearance_no_sidewalk | 4.0m | 보도 없음 |
| max_top_height_relative_building | 0.0m | 건물 높이 초과 금지 |
| max_count_per_business | 기본 1 | 업소당 수량 |
| requires_no_existing_wall_sign | bool | 벽면간판 총량 충돌 검토 |
| safety_check_min_height | 5.0m | 안전점검 기준 |
| safety_check_min_area | 1.0㎡ | 안전점검 기준 |

### 5.3 보조 규칙 / 보조 테이블

| 테이블 | 필요 여부 | 이유 |
| --- | --- | --- |
| industry_exception_rule | Y | 이미용업 규격 특례 |
| sign_count_rule | Y | 의료기관/약국 수량 특례 |
| special_zone_rule | Y | 테헤란로 금지 |
| draft_rule | Y | 조문 추출 초안과 운영 규칙을 분리하기 위한 검수 단계 |

## 6. 엔진 판정 순서

1. 용도지역 금지 여부 확인
2. 특수구역 금지 여부 확인
3. 기본 규칙과 업종/수량 특례 컨텍스트 로드
4. 층수와 건물 높이 기준 확인
5. 규격 및 지면 이격 기준 확인
6. 수량과 기존 벽면간판 충돌 확인
7. 심의 특례 승인값 반영
8. 안전점검 대상 여부 계산
9. 최종 `decision`, `administrative_action`, `review_type` 반환

## 7. 테스트 케이스

| 케이스 | 입력 요약 | 기대 결과 | 구현 테스트 |
| --- | --- | --- | --- |
| 정상 허용 | 3층, 규격 이내, 자사 | `permit` 또는 `report` | `test_projecting_sign_permit_under_limits` |
| 6층 금지 | `floor=6` | `prohibited` | `test_projecting_sign_prohibited_over_sixth_floor` |
| 돌출폭/두께 초과 | 규격 초과 | `prohibited` | 관련 개별 테스트 존재 |
| 업종 특례 | 미용실, 치과의원 | 특례 기준 허용 | `beauty_exception`, `medical_exception` 테스트 |
| 심의 특례 | 규격 초과 + 승인값 | 경고와 함께 허용 | `test_projecting_sign_exception_review_approved_allows_spec_violation` |
| 누락 입력 | `height=None` | `fallback_reason=missing_input` | `test_projecting_sign_returns_missing_input_fallback` |
| 규칙 미정의 | 규칙 조회 결과 없음 | `fallback_reason=missing_rule` | `test_projecting_sign_returns_missing_rule_fallback` |

## 8. 운영 검수 메모

- 초안 출처: 시행령, 서울시 조례, 강남구 심의기준, 현재 시드/엔진 구현
- 검수 포인트:
  - 업종 분류 키워드 매칭을 코드 테이블로 바꿀지
  - 심의 특례 승인 범위를 규격 초과 전부로 볼지 일부 항목으로 제한할지
  - 테헤란로 외 특수구역이 추가되면 `special_zone_rule` 확장으로 충분한지
- 운영 반영 전 확인사항:
  - 조문별 근거 UUID 연결 정합성
  - 보조 규칙 테이블과 기본 규칙의 우선순위 재검토
