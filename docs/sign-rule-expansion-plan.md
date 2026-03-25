# 광고물 판정 확장 계획서

## 1. 목적

이 문서는 `돌출간판`을 시작점으로 하여, 법령 텍스트와 벡터 DB에 저장된 근거를 실제 판정 DB와 연결하고, 최종적으로 모든 광고물 유형에 대해 `permit / report / prohibited` 판정을 일관되게 수행하기 위한 확장 계획을 정리한 문서다.

현재 시스템은 아래 두 층으로 분리되어 있다.

- `provision`, `law_chunk`: 법령 원문 및 검색용 벡터 DB
- `rule_condition`, `rule_effect`: 실제 판정에 사용하는 구조화 규칙 DB

문제는 이 둘이 자동 또는 반자동으로 연결되지 않아, 법령 텍스트에 기준이 있어도 판정 엔진이 이를 실제로 집행하지 못한다는 점이다. 본 계획의 목표는 이 단절을 해소하는 것이다.

## 2. 목표 상태

목표 상태는 다음과 같다.

1. 법령 원문과 가이드라인에서 판정 가능한 규칙을 추출한다.
2. 추출된 규칙을 `rule_condition` / `rule_effect` 또는 보조 규칙 테이블에 구조화해 적재한다.
3. 프론트 입력값이 해당 규칙을 판정할 수 있을 만큼 충분한 정보를 받는다.
4. `RuleEngine`가 모든 핵심 규격, 위치, 수량, 예외, 안전점검 조건을 실제로 검사한다.
5. 판정 결과에는 근거 조문, 불가 사유, 심의 필요 여부가 함께 제시된다.
6. 법적 판정(`decision`)과 행정 절차(`administrative_action`)를 분리해 표현한다.

추가로, 본 계획은 `돌출간판 -> 벽면이용간판`의 단선 흐름이 아니라 다음 방향을 따른다.

- `돌출간판`을 1차 기준 모델로 먼저 완성한다.
- 여기서 검증된 입력 구조, 규칙 구조, 엔진 구조, 테스트 구조를 공통 템플릿으로 삼는다.
- 이후 이 공통 구조를 모든 광고물 유형으로 단계적으로 확장한다.
- `벽면이용간판`은 그 확장 대상 중 하나이며, 일반 벽면이용간판과 건물 상단간판으로 분리 적용한다.

## 3. 현재 문제 요약

현재 확인된 대표 문제는 다음과 같다.

- 법령 텍스트에 `돌출간판은 5층 이하` 기준이 있어도, 판정 DB에는 `5층 이하 허용` 규칙만 있고 `6층 이상 금지` 규칙이 없다.
- `max_height`, `max_protrusion`, `max_width` 같은 규격 값이 일부 저장되어 있어도 엔진이 이를 모두 강제 판정하지 않는다.
- `두께`, `지면 이격`, `기설치 간판 수`, `업종 특례`, `특정 지역 금지`, `안전점검 조건` 같은 중요한 요소가 스키마나 입력값에 충분히 반영되지 않았다.
- 벡터 DB는 현재 설명용 검색에만 사용되고 있으며 실제 판정 규칙 동기화에는 쓰이지 않는다.

## 4. 확장 원칙

확장 시 아래 원칙을 유지한다.

- 결정은 항상 구조화 규칙 DB와 엔진이 수행한다.
- 벡터 DB는 근거 검색용이지만, 규칙 추출의 원천 데이터로도 활용한다.
- 법령 원문과 판정 규칙 사이에는 검토 가능한 중간 표현이 있어야 한다.
- 예외 규정과 심의 특례는 일반 허용 규칙과 분리된 명시 규칙으로 관리한다.
- 각 광고물 유형마다 자동 검증 가능한 테스트 케이스 세트를 유지한다.

## 5. 1단계 기준 모델: 돌출간판

돌출간판은 모든 구조물형 광고물 판정의 기준 모델로 삼는다. 이유는 다음과 같다.

- 층수 제한이 명확하다.
- 규격 제한이 복수 축으로 존재한다.
- 업종별 특례가 존재한다.
- 특정 지역 금지 규정이 있다.
- 안전점검 및 심의 예외 조건이 있다.

### 5.1 돌출간판 핵심 규칙 항목

- 설치 층수: 5층 이하
- 간판 윗부분: 건물 높이 초과 금지
- 돌출폭: 1m 이하
- 세로 길이: 3.5m 이하 또는 1개 층 높이 이내
- 두께: 30cm 이하
- 지면과의 간격: 보도 있음 3m 이상, 보도 없음 4m 이상
- 업소당 수량: 1개
- 기존 벽면간판과 총수량 관계 반영
- 이·미용업소 및 의료기관/약국 완화 기준 반영
- 테헤란로 설치 금지
- 안전점검 조건: 상단 높이 5m 이상이면서 1면 면적 1㎡ 이상
- 심의 특례 시 완화 규격 반영

### 5.2 돌출간판 필수 입력

- `sign_type`
- `business_category`
- `zone`
- `floor`
- `ad_type`
- `tehranro`
- `has_sidewalk`
- `height`
- `width`
- `protrusion`
- `thickness`
- `bottom_clearance`
- `top_height_from_ground`
- `face_area`
- `building_height`
- `floor_height`
- `existing_sign_count_for_business`
- `existing_sign_types`
- `exception_review_approved`

### 5.3 돌출간판 기준 판정 로직

1. 금지구역 여부 확인
2. 업종 특례 여부 확인
3. 층수 및 건물 높이 제한 확인
4. 규격 초과 여부 확인
5. 지면 이격 기준 확인
6. 업소당 수량 및 기설치 간판 여부 확인
7. 심의 특례 승인 여부 확인
8. 안전점검 대상 여부 판정
9. 최종 `permit / report / prohibited` 결정

### 5.4 돌출간판 테스트 기준

반드시 포함할 대표 테스트 케이스:

- 5층 이하 정상 설치
- 6층 설치
- 돌출폭 초과
- 세로 길이 초과
- 두께 초과
- 보도 있음 이격 미달
- 보도 없음 이격 미달
- 업소당 수량 초과
- 기존 벽면간판과 총량 충돌
- 테헤란로 설치
- 이·미용업 특례 허용
- 의료기관 특례 허용
- 안전점검 대상
- 심의 특례 승인
- 심의 특례 미승인

## 6. 공통 판정 모델

돌출간판에서 확립한 모델을 모든 광고물로 확장하기 위해, 공통 판정 축을 정의한다.

### 6.1 공통 입력 축

- 광고물 유형
- 업종
- 자사/타사 여부
- 용도지역
- 설치 층수
- 설치 위치 유형
- 가로, 세로, 면적
- 돌출폭
- 두께
- 지면과의 간격
- 보도 유무
- 건물 높이, 층고
- 업소당 기존 간판 수
- 기존 간판 종류
- 특정 도로/특정 구역 여부
- 조명 종류
- 심의 특례 승인 여부

### 6.2 공통 판정 축

- 설치 가능 위치
- 허용 층수
- 최대 규격
- 최소 이격
- 업소당 허용 수량
- 총 허용 수량
- 금지 지역
- 업종별 예외
- 행정 절차 구분
- 심의 필요 여부
- 안전점검 필요 여부
- 연장신고/허가 전환 조건

### 6.3 공통 출력 축

- `decision`
- `administrative_action`
- `review_type`
- `warnings`
- `safety_check`
- `max_spec`
- `missing_fields`
- `fallback_reason`

## 6A. 벽면이용간판 유형 분리 원칙

벽면이용간판은 하나의 유형으로 묶지 않고 아래 두 하위 유형으로 분리해 설계해야 한다.

- `5층 이하 일반 벽면이용간판`
- `건물 상단간판`

이 둘은 설치 위치, 목적, 허용 수량, 허용 형태, 규격 계산 방식, 심의 절차가 모두 다르므로 같은 규칙셋으로 처리하면 안 된다.

### 6A.1 5층 이하 일반 벽면이용간판

주요 성격:

- 개별 업소 상호 표시용
- 건물 1층부터 5층 이하 벽면에 설치
- 1업소 1간판이 원칙
- 곡각지점 또는 전후면 도로 접한 경우 2개까지 허용 가능
- 3층 이하에서는 판류형 허용 가능
- 4층 이상은 입체형만 허용

핵심 규칙:

- 설치 위치: `1층 ~ 5층`
- 수량: 기본 `1업소 1개`, 예외 조건 충족 시 `2개`
- 형태:
  - `floor <= 3` 이면 `입체형` 또는 `판류형`
  - `floor >= 4` 이면 `입체형`만 허용
- 가로:
  - `업소 가로폭의 80% 이내`
  - `최대 10m 이내`
- 세로:
  - `입체형 45cm 이내`
  - `판류형 80cm 이내`
- 특이사항:
  - `3층 이하`
  - `면적 5㎡ 미만`
  - `가로 10m 미만`
  - 위 조건이면 허가/신고 없이 설치 가능

필수 입력 추가 예시:

- `floor`
- `form_type`
- `shop_front_width`
- `sign_width`
- `sign_height`
- `sign_area`
- `is_corner_lot`
- `has_front_and_rear_roads`

판정 관점:

- 단순 허용/불가만이 아니라 `무신고 가능`, `신고`, `허가`, `심의 필요`의 행정 절차 분기가 중요하다.
- `무신고 가능`의 표준 출력 매핑은 아래와 같이 고정한다.
  - `decision = permit`
  - `administrative_action = none`
  - `review_type = null`

### 6A.2 건물 상단간판

주요 성격:

- 건물명 또는 대표 상호 표시용
- 4층 이상 건물의 최상단 벽면 또는 옥상 난간 포함 영역
- 건물 상단 3면까지 허용
- 무조건 입체형만 허용
- 반드시 심의가 필요

핵심 규칙:

- 설치 위치: `4층 이상 건물의 최상단`
- 표시 대상:
  - 건물명
  - 건물을 사용하는 자의 성명 또는 상호
  - 이를 상징하는 도형
- 수량:
  - `건물 상단 3면`
  - `면당 1개`
- 형태:
  - `입체형만 허용`
- 규격:
  - 가로형
    - `건물 가로폭의 1/2 이내`
    - 세로는 `4층 60cm`부터 시작해 `층당 10cm 증가`
    - `최대 1.2m`
  - 세로형
    - 가로폭 `최대 1.2m`
    - 세로 길이 `건물 높이의 1/2 이내`
    - 동시에 `최대 10m`
- 절차:
  - `옥외광고심의위원회 심의 필수`

필수 입력 추가 예시:

- `building_floor_count`
- `install_at_top_floor`
- `display_orientation`
- `building_width`
- `building_height`
- `requested_faces`
- `content_type`

판정 관점:

- 일반 벽면이용간판과 달리, 상단간판은 허용되더라도 `심의 필수`가 기본값이다.
- 따라서 `review_type`이 옵션이 아니라 사실상 핵심 속성이다.

### 6A.3 벽면이용간판 데이터 모델 원칙

벽면이용간판은 최소한 `install_subtype` 또는 동등한 분기 필드로 아래를 분리해야 한다.

- `wall_sign_general_under_5f`
- `wall_sign_top_building`

이 구분 없이 `벽면이용간판` 하나의 `sign_type`만 쓰면 아래 문제가 생긴다.

- 일반 업소용 간판과 상단간판의 수량 규칙 충돌
- 판류형 허용 층수와 상단간판 입체형 전용 규칙 충돌
- 규격 계산식 충돌
- 심의 필수 여부 충돌

따라서 확장 순서상 `벽면이용간판`은 다음 두 작업으로 쪼개서 진행해야 한다.

1. `5층 이하 일반 벽면이용간판` 규칙 세트 설계
2. `건물 상단간판` 규칙 세트 설계

둘은 같은 대분류 아래에 두되, 판정 엔진과 규칙 DB에서는 별도 하위 유형으로 관리한다.

## 7. DB 확장 계획

현재 스키마만으로는 모든 광고물 규칙을 표현하기 어렵다. 아래와 같이 확장한다.

### 7.1 `rule_condition` 확장 후보

- `business_category`
- `install_location_type`
- `has_existing_wall_sign`
- `existing_sign_count_for_business`
- `special_zone`
- `exception_review_approved`

### 7.2 `rule_effect` 확장 후보

- `max_thickness`
- `min_bottom_clearance`
- `min_bottom_clearance_no_sidewalk`
- `max_top_height_relative_building`
- `max_top_height_from_ground`
- `max_count_per_business`
- `requires_no_existing_wall_sign`
- `requires_alignment`
- `safety_check_min_height`
- `safety_check_min_area`

### 7.3 보조 테이블 도입 후보

- `industry_exception_rule`
- `sign_count_rule`
- `special_zone_rule`
- `safety_check_rule`
- `review_exception_rule`

이유는 업종 특례, 수량 규칙, 안전점검, 지역 특례가 일반적인 max/min 비교 규칙과 성격이 다르기 때문이다.

## 7A. 최종 권고안

구현 착수 시 아래 방향을 기본 원칙으로 삼는다.

### 7A.1 API 마이그레이션

기존 `/api/v1/judge`를 즉시 폐기하거나 깨지 않고, 확장 필드를 점진적으로 추가한다.

권고 방식:

1. 기존 필드는 유지한다.
2. 신규 판정 필드를 optional로 추가한다.
3. 광고물 유형별로 필요한 필드는 서버 validation에서 조건부로 강제한다.
4. 프런트는 광고물 유형에 따라 필요한 입력만 노출한다.

초기 확장 필드 예시:

- `install_subtype`
- `form_type`
- `business_category`
- `height`
- `width`
- `protrusion`
- `thickness`
- `bottom_clearance`
- `top_height_from_ground`
- `building_height`
- `floor_height`
- `existing_sign_count_for_business`
- `existing_sign_types`
- `has_existing_wall_sign`
- `total_allowed_sign_count`
- `exception_review_approved`

이 접근은 기존 클라이언트와의 호환성을 유지하면서 돌출간판부터 순차 적용할 수 있게 한다.

응답 마이그레이션도 동일한 원칙을 따른다.

권고 방식:

1. 기존 응답 필드는 유지한다.
2. 신규 출력 필드는 optional로 추가한다.
3. 프런트는 신규 필드가 있을 때만 추가 표시를 한다.

초기 응답 확장 필드 예시:

- `administrative_action`
- `safety_check`
- `matched_rule_id`
- `missing_fields`
- `fallback_reason`

응답 모델 원칙:

- 기존 화면은 기존 응답만으로 계속 동작해야 한다.
- 신규 화면이나 디버깅 화면은 확장 응답 필드를 활용한다.
- 돌출간판에서 먼저 적용한 뒤, 전체 광고물로 동일한 응답 구조를 확장한다.

### 7A.2 엔진 조회 모델

기존의 `rule_condition + rule_effect` 중심 구조는 유지하되, 엔진 내부를 다단계 검사 구조로 확장한다.

권장 순서:

1. 기본 룰 매칭
2. 금지구역 검사
3. 설치 위치 검사
4. 규격 검사
5. 수량 검사
6. 예외 및 특례 검사
7. 안전점검 플래그 계산
8. `review_type` 부여
9. 최종 decision 반환

모델 원칙:

- `rule_condition`: 어떤 상황에 적용되는 규칙인지 표현
- `rule_effect`: 기본 결정값과 허용 한도 표현
- 엔진 후속 함수: 입력값과 허용 한도를 실제 비교

초기 보조 테이블 우선순위:

- `sign_count_rule`
- `special_zone_rule`
- `industry_exception_rule`

안전점검은 초기 단계에서는 `rule_effect` 확장 필드로 다루고, 필요 시 별도 테이블로 분리한다.

### 7A.3 decision 상태 모델

최종 decision 값은 단순하게 유지한다.

- `permit`
- `report`
- `prohibited`

추가 행정 상태는 별도 필드로 분리한다.

권고 필드:

- `review_type`
- `administrative_action`
- `warnings`
- `safety_check`

`administrative_action` 예시:

- `none`
- `report`
- `permit`

원칙:

- `무신고 가능`은 새로운 decision으로 만들지 않는다.
- `심의 필수`는 `review_type`만으로 표현한다.
- `permit / report / prohibited`는 법적 판정 축으로 유지한다.
- `administrative_action`은 행정 절차 축으로 유지한다.

### 7A.4 기존 설치 현황 데이터 출처

초기 단계에서는 기존 설치 현황을 사용자 입력으로 받는다.

권장 입력 필드:

- `existing_sign_count_for_business`
- `existing_sign_types`
- `has_existing_wall_sign`
- `total_allowed_sign_count`

권장 형식:

- `existing_sign_count_for_business`: 정수
- `existing_sign_types`: 문자열 배열
- `has_existing_wall_sign`: 불리언
- `total_allowed_sign_count`: 정수

이 방식은 초기 구현 속도를 높이고, 행정 시스템 연계가 없는 상태에서도 수량 규칙 판정을 먼저 가능하게 한다.

### 7A.5 fallback 정책

확장 이후에는 규칙 미매칭을 현재처럼 일괄 `report`로 처리하면 안 된다. fallback 사유를 구분해야 한다.

권고 분류:

- `fallback_reason = missing_input`
- `fallback_reason = missing_rule`
- `fallback_reason = none`

권고 정책:

1. 필수 입력 부족
   - 확정 판정 불가 상태로 간주한다.
   - `missing_fields`에 누락 필드를 명시한다.
   - `warnings`에 확정 판정 불가 사유를 남긴다.
   - 기본 반환값은 아래와 같이 고정한다.
     - `decision = report`
     - `administrative_action = report`
   - 내부적으로는 `missing_input`을 반드시 구분한다.

2. 입력은 충분하지만 규칙 없음
   - `fallback_reason = missing_rule`
   - `warnings`에 규칙 DB 미정의 사실을 명시한다.
   - 운영상 기본 대응은 `report`로 둘 수 있으나, 이것이 법적 확정 판정은 아니라는 점을 출력에 드러낸다.

3. 정상 규칙 매칭
   - `fallback_reason = none`
   - 일반 판정 흐름 적용

원칙:

- `입력 부족`과 `규칙 부재`는 반드시 구분한다.
- fallback은 임시 운영 장치이지, 정상 판정 흐름으로 간주하지 않는다.
- 돌출간판에서 먼저 적용한 뒤, 모든 광고물 유형에 동일 원칙을 확장한다.

## 7B. 1차 구현 범위와 전체 확장 전략

1차 구현은 `돌출간판`을 기준 모델로 삼는다. 다만 방향은 `돌출간판 -> 벽면이용간판` 고정 흐름이 아니다.

정확한 전략은 다음과 같다.

1. `돌출간판`에서 입력 구조, 규칙 구조, 엔진 구조, 테스트 구조를 완성한다.
2. 이 결과를 공통 템플릿으로 정리한다.
3. 이 템플릿을 모든 광고물 유형에 단계적으로 확장 적용한다.
4. `벽면이용간판`은 그 확장 대상 중 하나이며, 일반 벽면이용간판과 건물 상단간판으로 나누어 적용한다.

즉 전략의 중심은 `돌출간판에서 시작해 전체 광고물 체계로 확장`하는 것이다.

## 8. 법령 텍스트에서 판정 DB로 연결하는 흐름

### 8.1 목표 파이프라인

`document_master / provision -> law_chunk -> 규칙 후보 추출 -> 관리자 검토 -> rule_condition / rule_effect 적재 -> RuleEngine 판정`

### 8.2 규칙 추출 방식

초기에는 반자동 방식을 채택한다.

1. `provision`과 `law_chunk`에서 광고물 유형별 관련 조문을 식별
2. 조문에서 규격, 층수, 수량, 예외, 금지구역, 안전점검 조건을 추출
3. 추출 내용을 중간 구조(JSON 또는 검토 테이블)로 저장
4. 관리자 검토 후 판정 규칙 DB에 반영

완전 자동 추출은 오탐과 누락 위험이 크므로, 초기 단계에서는 검토 단계를 반드시 둔다.

## 9. 광고물 유형 확장 순서

권장 순서는 다음과 같다.

1. 돌출간판
2. 벽면이용간판(5층 이하 일반)
3. 건물 상단간판
4. 옥상간판
5. 지주이용간판
6. 입간판
7. 창문이용광고물
8. 공연간판
9. 현수막
10. 애드벌룬
11. 선전탑

이 순서는 구조물형 광고물부터 단순 규칙형, 특수형으로 확장하기 위한 것이다.

## 10. 광고물별 확장 템플릿

각 광고물 유형은 아래 템플릿으로 설계한다.

### 10.1 필수 입력

- 법령상 판정에 필요한 사용자 입력 목록

### 10.2 규칙 분해표

- 위치 규정
- 규격 규정
- 수량 규정
- 조명 규정
- 업종 특례
- 지역 특례
- 심의 특례
- 안전점검 조건

### 10.3 DB 표현 방식

- `rule_condition`에 저장할 항목
- `rule_effect`에 저장할 항목
- 보조 테이블 필요 여부

### 10.4 엔진 판정 순서

- 금지 -> 위치 -> 규격 -> 수량 -> 예외 -> 안전점검 -> 최종 결정

### 10.5 테스트 케이스

- 정상 허용
- 금지 조건 1개씩
- 예외 허용
- 심의 특례
- 안전점검

## 11. 단계별 실행 계획

### 11.1 1단계: 돌출간판 완성

- 돌출간판 법령/조례/심의기준 정리
- 입력 스키마 확장
- 응답 스키마 확장
- 돌출간판 규칙 DB 보강
- 엔진 규격 강제 판정 추가
- fallback 정책 분기 도입
- 테스트 세트 구축

완료 기준:

- 5층 초과 시 `prohibited`
- 돌출폭, 세로, 두께, 이격 기준 위반 시 `prohibited`
- 특례 업종 및 테헤란로 규정 반영
- 안전점검 플래그 반영
- `administrative_action`과 `review_type`이 함께 반환됨
- `missing_fields`와 `fallback_reason`으로 불완전 판정을 구분 가능

### 11.2 2단계: 구조물형 광고물 확장

대상:

- 벽면이용간판(5층 이하 일반)
- 건물 상단간판
- 옥상간판
- 지주이용간판

목표:

- 돌출간판에서 확립한 공통 스키마와 엔진 구조를 재사용
- 광고물별 차이만 규칙 데이터와 보조 규칙으로 표현
- 구조물형 광고물에 적용 가능한 공통 템플릿을 정교화하여 이후 전체 광고물 확장 기반을 만든다.

### 11.3 3단계: 단순/특수 유형 확장

대상:

- 입간판
- 창문이용광고물
- 공연간판
- 현수막
- 애드벌룬
- 선전탑

목표:

- 구조물형에 비해 다른 입력 축을 정리
- 금지 규정 및 신고/허가 분기 중심으로 정리
- 공통 템플릿을 유지하되, 각 광고물 유형의 특수 입력과 행정 절차 차이를 흡수한다.

### 11.4 4단계: 운영 자동화

- 규칙 추출 검토 테이블 도입
- 관리자 검수 워크플로우 구축
- 법령 개정 시 영향 규칙 자동 식별
- 회귀 테스트 자동 실행

## 12. 문서화 및 검증 계획

모든 광고물 유형에 대해 아래 산출물을 유지한다.

- 규칙 분해표
- 필수 입력 정의
- DB 매핑 정의
- 엔진 판정 순서 정의
- 테스트 케이스 목록
- 근거 조문 연결 목록

## 13. 리스크

- 법령 문장이 판정 가능한 규칙으로 바로 떨어지지 않을 수 있다.
- 조례, 시행령, 심의기준의 우선순위와 충돌 정리가 필요하다.
- 예외 조항이 많아 완전 자동 추출은 오판정 위험이 높다.
- 현재 프런트 입력값은 필요한 정보를 충분히 받지 않는다.
- 현재 엔진은 `area` 중심이라 다축 규격 판정을 위해 구조 변경이 필요하다.

## 14. 권고 사항

가장 먼저 해야 할 일은 돌출간판 하나를 완전한 판정 모델로 만드는 것이다. 이 단계가 끝나야 다른 광고물도 동일한 형식으로 확장할 수 있다. 돌출간판을 템플릿으로 삼아 입력, 규칙, 엔진, 테스트를 표준화한 뒤 광고물별 차이를 규칙 데이터로 흡수하는 방식이 가장 안정적이다.

## 15. 다음 산출물

이 문서 다음 단계에서 작성할 구체 산출물은 아래와 같다.

- 돌출간판 규칙 분해표 상세본
- 돌출간판 입력 JSON 스키마 초안
- 돌출간판용 `rule_condition` / `rule_effect` 샘플 정의
- 돌출간판 테스트 케이스 명세서
- 벽면이용간판 확장 초안

## 16. 개발 태스크 백로그

아래 태스크는 현재 코드베이스를 기준으로 바로 착수 가능한 개발 작업으로 재정리한 것이다.
우선순위는 `P0 > P1 > P2`이며, 1차 릴리즈 범위는 `돌출간판 기준 모델 완성`까지로 본다.

운영 규칙:

- 이 백로그를 기준으로 개발을 수행할 때는 작업 진행 또는 완료 시점마다 본 문서를 함께 업데이트한다.
- 최소 반영 항목은 `상태(todo/in_progress/done/blocked)`, 변경 파일, 블로커 또는 범위 변경이다.
- 백로그 업데이트는 후속 수동 작업으로 미루지 않고 해당 개발 흐름 안에서 같이 처리한다.

### 16.1 Epic A. 돌출간판 기준 모델 완성

#### TASK-A1. 판정 요청/응답 스키마 확장

- 상태: `done`
- 변경 파일:
  - `backend/api/judge.py`
  - `backend/engine/rule_engine.py`
  - `frontend/lib/api.ts`
  - `frontend/components/JudgeForm.tsx`
  - `frontend/components/JudgeResult.tsx`
- 구현 메모:
  - 돌출간판 전용 확장 입력 필드를 요청 스키마와 프런트 타입에 추가했다.
  - `sign_type=돌출간판`일 때 필수 확장 필드 누락을 서버 validation으로 차단한다.
  - 응답에 `administrative_action`, `safety_check`, `matched_rule_id`, `missing_fields`, `fallback_reason`를 추가했다.
  - 프런트 폼은 돌출간판 선택 시 확장 입력 UI를 노출하고, 결과 화면은 신규 응답 필드를 표시한다.
- 검증 메모:
  - `backend/api/judge.py`, `backend/engine/rule_engine.py`는 AST 파싱으로 문법 확인 완료
  - `py_compile`는 샌드박스의 `__pycache__` 권한 문제로 사용하지 못했다.
- 우선순위: `P0`
- 목적:
  - 돌출간판 판정에 필요한 신규 입력과 출력 축을 API에 반영한다.
- 대상 파일:
  - `backend/api/judge.py`
  - `backend/engine/rule_engine.py`
  - `frontend/lib/api.ts`
  - `frontend/components/JudgeForm.tsx`
  - `frontend/components/JudgeResult.tsx`
- 작업 내용:
  - `JudgeRequest`에 `business_category`, `height`, `width`, `protrusion`, `thickness`, `bottom_clearance`, `top_height_from_ground`, `face_area`, `building_height`, `floor_height`, `existing_sign_count_for_business`, `existing_sign_types`, `exception_review_approved`를 optional 필드로 추가
  - `sign_type=돌출간판`일 때 필요한 필드를 조건부 validation으로 강제
  - `JudgeResponse`에 `administrative_action`, `safety_check`, `missing_fields`, `fallback_reason`, `matched_rule_id`를 추가
  - 프런트는 `돌출간판` 선택 시 확장 입력 UI를 노출
  - 결과 화면은 신규 응답 필드가 있을 때만 추가 표시
- 완료 기준:
  - 기존 클라이언트 요청은 깨지지 않는다.
  - 돌출간판 요청은 누락 필드 목록을 응답으로 받을 수 있다.
  - 응답에 법적 판정과 행정 절차가 분리되어 나타난다.

#### TASK-A2. RuleEngine 입력 모델과 fallback 정책 개편

- 상태: `done`
- 변경 파일:
  - `backend/engine/rule_engine.py`
- 구현 메모:
  - 엔진 진입 시점에 필수 입력 누락을 먼저 검사해 `fallback_reason=missing_input`으로 반환하도록 변경했다.
  - 규칙 미매칭 fallback은 `fallback_reason=missing_rule`로 유지하고, `decision=report`, `administrative_action=report`를 고정했다.
  - `administrative_action` 매핑을 엔진 내부 함수로 분리해 결과 생성 경로를 일관되게 정리했다.
  - 현재 기준 필수 입력 검사는 `돌출간판`, `지주이용간판`, `공연간판`, `입간판`에 대해 우선 적용했다.
- 검증 메모:
  - `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile backend/engine/rule_engine.py backend/api/judge.py` 성공
- 우선순위: `P0`
- 선행 조건:
  - `TASK-A1`
- 대상 파일:
  - `backend/engine/rule_engine.py`
- 작업 내용:
  - `JudgeInput`를 다축 규격 비교가 가능한 구조로 확장
  - `JudgeResult`에 `administrative_action`, `missing_fields`, `fallback_reason`, `warnings` 표준 필드를 추가
  - fallback을 `missing_input`과 `missing_rule`로 구분
  - 기본 fallback 응답은 `decision=report`, `administrative_action=report`로 고정
- 완료 기준:
  - 입력 부족과 규칙 부재가 서로 다른 응답으로 구분된다.
  - 엔진 결과만으로 프런트가 “확정 판정 불가” 사유를 설명할 수 있다.

#### TASK-A3. 돌출간판 다단계 판정 로직 구현

- 상태: `done`
- 변경 파일:
  - `backend/engine/rule_engine.py`
- 범위 메모:
  - `TASK-A4` 이전 단계이므로, 스키마에 아직 없는 돌출간판 세부 규격은 엔진 상수와 기존 시드 데이터를 함께 사용해 우선 구현한다.
- 구현 메모:
  - 돌출간판은 일반 규칙 조회 경로와 분리해 전용 다단계 판정 흐름으로 처리한다.
  - 판정 순서는 `금지구역 -> 테헤란로 -> 업종 특례 -> 층수/건물높이 -> 규격 -> 이격 -> 수량 -> 심의 특례 -> 안전점검 -> 최종 반환`으로 재구성했다.
  - 이·미용업은 기존 시드의 `돌출간판(이미용)` 규칙을 우선 사용하고, 의료기관/약국은 수량 완화 특례를 우선 적용하도록 분기했다.
  - 심의 특례 승인값이 있을 때는 규격 초과 항목을 경고로 남기고 예외 통과시키도록 임시 구현했다.
  - 안전점검은 `top_height_from_ground >= 5` 이고 `face_area >= 1`일 때 `true`로 계산한다.
- 검증 메모:
  - `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile backend/engine/rule_engine.py backend/api/judge.py` 성공
- 후속 메모:
  - `TASK-A4`에서 DB 스키마가 확장되면 현재 엔진 상수 기반 규칙을 `rule_effect`와 보조 테이블 조회로 치환해야 한다.
- 우선순위: `P0`
- 선행 조건:
  - `TASK-A2`
- 대상 파일:
  - `backend/engine/rule_engine.py`
- 작업 내용:
  - 판정 순서를 `금지구역 -> 테헤란로 -> 업종 특례 -> 층수/건물높이 -> 규격 -> 이격 -> 수량 -> 심의 특례 -> 안전점검 -> 최종 decision`으로 재구성
  - `max_height`, `max_protrusion`, `max_width` 외에 `max_thickness`, `min_bottom_clearance`, `max_top_height_relative_building`, `max_count_per_business` 비교 로직 추가
  - 이·미용업, 의료기관/약국 특례 분기 추가
  - `exception_review_approved`에 따른 완화 판정 분기 추가
  - `top_height_from_ground`와 `face_area`로 안전점검 대상 여부 계산
- 완료 기준:
  - 계획서 5.4 테스트 항목을 모두 코드로 판정할 수 있다.
  - `6층`, `돌출폭 초과`, `두께 초과`, `테헤란로`는 명확한 사유와 함께 `prohibited`가 반환된다.
  - 특례 업종과 심의 특례 승인 케이스는 일반 규칙보다 우선 적용된다.

#### TASK-A4. 돌출간판 규칙 DB 스키마 확장

- 상태: `done`
- 변경 파일:
  - `db/init.sql`
  - `backend/db/models.py`
- 구현 메모:
  - `rule_condition`에 `business_category`, `install_location_type`, `special_zone`, `existing_sign_count_for_business`, `exception_review_approved` 컬럼을 추가했다.
  - `rule_effect`에 `administrative_action`, `max_thickness`, `min_bottom_clearance`, `min_bottom_clearance_no_sidewalk`, `max_top_height_relative_building`, `max_top_height_from_ground`, `max_count_per_business`, `requires_no_existing_wall_sign`, `requires_alignment`, `safety_check_min_height`, `safety_check_min_area` 컬럼을 추가했다.
  - 모든 신규 컬럼은 nullable 또는 안전한 기본값으로 두어 기존 규칙 데이터와의 하위 호환을 유지했다.
- 검증 메모:
  - `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile backend/db/models.py` 성공
  - 개발 DB에는 `db/migrations/20260325_expand_sign_rule_schema.sql`로 실제 반영 완료
- 후속 메모:
  - 실제 DB 반영을 위해서는 초기화 SQL 재적용 또는 별도 마이그레이션이 필요하다.
- 우선순위: `P0`
- 선행 조건:
  - 없음
- 대상 파일:
  - `db/init.sql`
  - `backend/db/models.py`
- 작업 내용:
  - `rule_condition`에 `business_category`, `install_location_type`, `existing_sign_count_for_business`, `special_zone`, `exception_review_approved` 확장 여부 반영
  - `rule_effect`에 `max_thickness`, `min_bottom_clearance`, `min_bottom_clearance_no_sidewalk`, `max_top_height_relative_building`, `max_top_height_from_ground`, `max_count_per_business`, `requires_no_existing_wall_sign`, `safety_check_min_height`, `safety_check_min_area`, `administrative_action`를 추가
  - 필요 시 JSONB 대신 별도 컬럼으로 우선 구현하고, 복잡 규칙은 보조 테이블 후보로 남긴다.
- 완료 기준:
  - 돌출간판 핵심 규칙을 SQL 스키마만으로 저장 가능하다.
  - ORM 모델과 실제 초기화 SQL이 일치한다.

#### TASK-A5. 돌출간판 보조 규칙 테이블 도입

- 상태: `done`
- 변경 파일:
  - `db/init.sql`
  - `backend/db/models.py`
  - `backend/engine/rule_engine.py`
  - `scripts/seed_rules.sql`
  - `backend/tests/test_rule_engine_projecting_sign.py`
- 구현 메모:
  - `industry_exception_rule`, `sign_count_rule`, `special_zone_rule`를 추가하고 돌출간판의 업종 특례, 수량 특례, 테헤란로 금지 규칙을 분리했다.
  - 엔진은 돌출간판 판정 시 `특수구역 -> 업종 특례 -> 수량 규칙 -> 기본 rule_condition/rule_effect` 순으로 조회하도록 고정했다.
  - 기존 `돌출간판(이미용)` 의사 `sign_type`에 의존하던 분기를 제거하고 `business_category` 기반 특례 규칙 조회로 통일했다.
- 검증 메모:
  - `python3 -m unittest backend.tests.test_rule_engine_projecting_sign` 통과
- 우선순위: `P1`
- 선행 조건:
  - `TASK-A4`
- 대상 파일:
  - `db/init.sql`
  - `backend/db/models.py`
  - `backend/engine/rule_engine.py`
- 작업 내용:
  - `industry_exception_rule`, `sign_count_rule`, `special_zone_rule` 중 돌출간판에 필요한 최소 테이블부터 도입
  - 업종 특례, 수량 규칙, 테헤란로 금지 규정을 일반 `rule_effect`와 분리
  - 엔진에서 보조 규칙 조회 순서를 고정
- 완료 기준:
  - 특례 규칙이 일반 max/min 컬럼에 억지로 섞이지 않는다.
  - 돌출간판 특례 변경 시 시드 데이터만 수정해도 동작을 바꿀 수 있다.

#### TASK-A6. 돌출간판 규칙 시드 데이터 재작성

- 상태: `done`
- 변경 파일:
  - `scripts/seed_rules.sql`
  - `backend/engine/rule_engine.py`
- 구현 메모:
  - 돌출간판 시드를 `금지 규칙`, `6층 이상 금지`, `이·미용업 특례`, `일반 자사`, `심의 특례 승인`, `타사광고`로 분리해 재작성했다.
  - 기본 규격은 `rule_effect`에, 업종 특례/수량 특례/테헤란로 금지는 보조 규칙 테이블에 적재하도록 시드를 재구성했다.
  - 엔진은 돌출간판 판정 시 `rule_effect` 세부 컬럼과 보조 규칙 테이블을 함께 읽도록 조정했다.
- 검증 메모:
  - 시드 SQL은 문법 검사 대신 회귀 테스트의 fixture 역할로 검증했다.
- 우선순위: `P0`
- 선행 조건:
  - `TASK-A4`
- 대상 파일:
  - `scripts/seed_rules.sql`
- 작업 내용:
  - 현재 단순 `floor_max=5` 중심 시드를 돌출간판 기준 모델에 맞게 재작성
  - 일반 규칙, 금지 규칙, 특례 규칙, 심의 특례 규칙을 분리해 적재
  - provision 연결을 유지하고 warning 문구를 표준화
- 완료 기준:
  - 시드 데이터만 적재해도 돌출간판 핵심 테스트 케이스가 재현된다.
  - `permit/report/prohibited` 외에 `administrative_action`과 `review_type`이 함께 설정된다.

#### TASK-A7. 돌출간판 테스트 세트 구축

- 상태: `done`
- 변경 파일:
  - `backend/tests/test_rule_engine_projecting_sign.py`
- 구현 메모:
  - `unittest.IsolatedAsyncioTestCase` 기반 엔진 회귀 테스트 18건을 추가했다.
  - 정상 허용, 6층, 돌출폭/세로/두께 초과, 보도 유무별 이격, 수량 초과, 기존 벽면간판 충돌, 테헤란로, 업종 특례, 안전점검, 심의 특례 승인/미승인, `missing_rule`, `missing_input`을 자동 검증한다.
  - DB 없이도 돌출간판 판정 흐름을 고정할 수 있도록 엔진 내부 조회는 `AsyncMock`으로 대체했다.
- 검증 메모:
  - `python3 -m unittest backend.tests.test_rule_engine_projecting_sign` 기준 통과를 목표로 구성했다.
- 우선순위: `P0`
- 선행 조건:
  - `TASK-A3`
  - `TASK-A6`
- 대상 파일:
  - `backend/tests/` 이하 신규 테스트 파일
- 작업 내용:
  - 계획서 5.4의 대표 케이스를 API 또는 엔진 단위 테스트로 추가
  - fallback 정책 테스트를 별도 작성
  - 특례 업종과 심의 특례 승인/미승인 케이스를 고정 회귀 테스트로 관리
- 완료 기준:
  - 최소 15개 이상 대표 케이스가 자동 실행된다.
  - 규칙 시드 변경 후 회귀 검증이 가능하다.

### 16.2 Epic B. 공통 판정 모델 정비

#### TASK-B1. 공통 입력 축/출력 축 타입 정리

- 상태: `done`
- 변경 파일:
  - `backend/api/judge.py`
  - `backend/engine/rule_engine.py`
  - `frontend/lib/api.ts`
  - `frontend/components/JudgeForm.tsx`
- 구현 메모:
  - 백엔드 요청 모델을 `JudgeCommonRequestFields`와 `JudgeProjectingSignRequestFields`로 분리하고, 응답도 `JudgeMaxSpec`, `JudgeFeeSummary` 타입으로 구조화했다.
  - 프런트 타입도 같은 구조로 정리해 공통 필드와 돌출간판 전용 필드를 구분했다.
  - `install_subtype`, `form_type`, `content_type`, `display_orientation`, `special_zone` 이름을 공통 확장 필드로 확정하고 프런트/백엔드 간 네이밍을 맞췄다.
- 검증 메모:
  - `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile backend/api/judge.py backend/engine/rule_engine.py backend/db/models.py backend/tests/test_rule_engine_projecting_sign.py` 성공
- 우선순위: `P1`
- 선행 조건:
  - `TASK-A1`
- 대상 파일:
  - `backend/api/judge.py`
  - `backend/engine/rule_engine.py`
  - `frontend/lib/api.ts`
- 작업 내용:
  - 광고물 공통 필드와 유형별 전용 필드를 구분하는 타입 구조 도입
  - `install_subtype`, `form_type`, `content_type`, `display_orientation` 등 확장 필드 이름을 확정
  - 프런트/백엔드 간 필드 네이밍을 통일
- 완료 기준:
  - 이후 광고물 유형 확장 시 필드 추가 방식이 일관된다.
  - 타입 이름만 보고 공통 필드와 전용 필드를 구분할 수 있다.

#### TASK-B2. 판정 단계별 엔진 함수 분리

- 상태: `done`
- 변경 파일:
  - `backend/engine/rule_engine.py`
- 구현 메모:
  - 돌출간판 전용 판정 흐름을 `금지 검사`, `컨텍스트 구성`, `이격 위반 수집`, `메타데이터 부착`, `성공/실패 결과 생성` 함수로 분리했다.
  - `ProjectingSignContext`를 도입해 기본 규칙, 특례 규칙, 수량 규칙, 누적 warning, review_type을 한 번에 전달하도록 정리했다.
  - 이후 광고물 유형 확장 시에도 `*_context`, `*_prohibition_checks`, `*_success/failure` 패턴으로 동일하게 늘릴 수 있는 구조로 맞췄다.
- 검증 메모:
  - `python3 -m unittest backend.tests.test_rule_engine_projecting_sign` 통과
- 우선순위: `P1`
- 선행 조건:
  - `TASK-A3`
- 대상 파일:
  - `backend/engine/rule_engine.py`
- 작업 내용:
  - 금지 검사, 위치 검사, 규격 검사, 수량 검사, 특례 검사, 안전점검 계산을 별도 함수로 분리
  - 현재 `_fetch_matching_rules` 단일 흐름을 다단계 파이프라인으로 재구성
- 완료 기준:
  - 광고물 유형별 차이를 함수 교체 또는 추가로 확장할 수 있다.
  - 단일 함수 내부에 모든 분기가 몰려 있지 않다.

### 16.3 Epic C. 벽면이용간판 유형 분리

#### TASK-C1. `install_subtype` 도입 및 벽면이용간판 분리

- 상태: `done`
- 변경 파일:
  - `backend/api/judge.py`
  - `backend/db/models.py`
  - `backend/engine/rule_engine.py`
  - `backend/tests/test_rule_engine_wall_sign_subtypes.py`
  - `db/init.sql`
  - `db/migrations/20260325_add_install_subtype_to_rule_condition.sql`
  - `frontend/components/JudgeForm.tsx`
  - `scripts/seed_rules.sql`
- 구현 메모:
  - `rule_condition.install_subtype` 컬럼을 추가하고 벽면이용간판 규칙을 `wall_sign_general_under_5f`, `wall_sign_top_building` 기준으로 재시드하도록 정리했다.
  - API와 엔진에서 `벽면이용간판` 요청은 `install_subtype`를 필수 입력으로 취급한다.
  - 프런트 폼에서 기존 `벽면이용간판(입체형)` 단일 `sign_type`를 제거하고 벽면 하위 유형 선택 UI로 대체했다.
- 우선순위: `P1`
- 선행 조건:
  - `TASK-B1`
- 대상 파일:
  - `backend/api/judge.py`
  - `backend/db/models.py`
  - `db/init.sql`
  - `frontend/components/JudgeForm.tsx`
- 작업 내용:
  - `벽면이용간판` 대분류 아래 `wall_sign_general_under_5f`, `wall_sign_top_building` 하위 유형 추가
  - 기존 `sign_type`만으로 처리하던 벽면 규칙을 하위 유형 기준으로 분리
- 완료 기준:
  - 일반 벽면간판과 상단간판이 서로 다른 규칙셋을 사용한다.

#### TASK-C2. 5층 이하 일반 벽면이용간판 규칙 구현

- 상태: `done`
- 변경 파일:
  - `backend/api/judge.py`
  - `backend/engine/rule_engine.py`
  - `backend/tests/test_rule_engine_wall_sign_subtypes.py`
  - `frontend/components/JudgeForm.tsx`
  - `frontend/lib/api.ts`
  - `scripts/seed_rules.sql`
- 구현 메모:
  - `wall_sign_general_under_5f` 전용 판정 함수를 추가해 형태, 가로폭, 세로 기준, 수량 예외, 무신고 가능 분기를 엔진에서 처리하도록 구현했다.
  - 일반 벽면이용간판 입력으로 `shop_front_width`, `sign_width`, `sign_height`, `sign_area`, `is_corner_lot`, `has_front_and_rear_roads`를 추가하고 서버 validation으로 강제했다.
  - `무신고 가능`은 `decision=permit`, `administrative_action=none`, `review_type=null`로 반환하도록 고정했다.
- 우선순위: `P1`
- 선행 조건:
  - `TASK-C1`
- 작업 내용:
  - `form_type`, `shop_front_width`, `sign_width`, `sign_height`, `sign_area`, `is_corner_lot`, `has_front_and_rear_roads` 입력 추가
  - `1업소 1개`, 예외 시 `2개`, `3층 이하 판류형`, `4층 이상 입체형만` 규칙 구현
  - `무신고 가능`을 `decision=permit`, `administrative_action=none`으로 매핑
- 완료 기준:
  - 일반 벽면이용간판의 형태/수량/절차 분기가 자동 판정된다.

#### TASK-C3. 건물 상단간판 규칙 구현

- 상태: `done`
- 변경 파일:
  - `backend/api/judge.py`
  - `backend/engine/rule_engine.py`
  - `backend/tests/test_rule_engine_wall_sign_subtypes.py`
  - `frontend/components/JudgeForm.tsx`
  - `frontend/lib/api.ts`
- 구현 메모:
  - `wall_sign_top_building` 전용 판정 함수를 추가해 최상단 여부, 4층 이상 건물 조건, 상단 3면 제한, 입체형 전용, 표시 내용 제한, 가로형/세로형 규격 계산을 구현했다.
  - 상단간판 입력으로 `building_floor_count`, `install_at_top_floor`, `display_orientation`, `building_width`, `requested_faces`, `content_type`를 추가하고 서버 validation으로 강제했다.
  - 상단간판은 허용되더라도 항상 `review_type`이 반환되도록 `대심의` 기반 분기로 고정했다.
- 우선순위: `P1`
- 선행 조건:
  - `TASK-C1`
- 작업 내용:
  - `building_floor_count`, `install_at_top_floor`, `display_orientation`, `building_width`, `requested_faces`, `content_type` 입력 추가
  - 상단 3면 제한, 입체형 전용, 가로형/세로형 규격 계산, 심의 필수 로직 구현
- 완료 기준:
  - 상단간판은 허용 시에도 `review_type`이 필수로 반환된다.

### 16.4 Epic D. 규칙 추출 및 운영 기반

#### TASK-D1. 규칙 분해표 템플릿 문서화

- 상태: `done`
- 변경 파일:
  - `docs/rule-breakdown-template.md`
  - `docs/rule-breakdown-projecting-sign.md`
- 구현 메모:
  - 광고물 유형별 검토에 공통 사용 가능한 규칙 분해표 템플릿을 새 문서로 작성했다.
  - 돌출간판에 대해 입력 필드, 규칙 분해, DB 매핑, 엔진 순서, 테스트 케이스를 한 장에서 검토할 수 있는 첫 상세본을 작성했다.
- 우선순위: `P1`
- 대상 파일:
  - `docs/` 이하 신규 문서
- 작업 내용:
  - 광고물 유형별로 `근거 조문 / 입력 필드 / rule_condition / rule_effect / 보조 규칙 / 테스트 케이스`를 한 장에서 보는 템플릿 작성
  - 돌출간판용 첫 번째 분해표 작성
- 완료 기준:
  - 개발자와 정책 검토자가 동일한 문서로 규칙을 검증할 수 있다.

#### TASK-D2. 규칙 추출 검수용 중간 테이블 설계

- 상태: `done`
- 변경 파일:
  - `backend/api/admin.py`
  - `backend/db/models.py`
  - `db/init.sql`
  - `db/migrations/20260325_add_draft_rule_table.sql`
- 구현 메모:
  - 법령/RAG 추출 결과를 운영 규칙과 분리 저장하는 `draft_rule` 테이블을 도입했다.
  - 관리자 API에 `draft_rule` 조회, 생성, 수정, 승인 엔드포인트를 추가해 검토 후 `rule_condition`/`rule_effect`로 승격하는 흐름을 정의했다.
- 우선순위: `P2`
- 대상 파일:
  - `db/init.sql`
  - `backend/db/models.py`
  - `backend/api/admin.py`
- 작업 내용:
  - 법령/RAG 추출 결과를 바로 운영 규칙에 넣지 않고 검수하는 `draft_rule` 성격의 테이블 설계
  - 관리자 검수 후 `rule_condition`/`rule_effect`로 반영하는 흐름 정의
- 완료 기준:
  - 벡터 DB와 판정 DB 사이에 검토 가능한 중간 표현이 생긴다.

#### TASK-D3. `law_chunk` / RAG 초안 적재 경로 연결

- 상태: `done`
- 변경 파일:
  - `backend/api/admin.py`
  - `backend/services/rag_service.py`
  - `backend/services/draft_rule_service.py`
  - `backend/tests/test_draft_rule_service.py`
- 구현 메모:
  - `POST /api/v1/admin/draft-rules/import` 엔드포인트를 추가해 `rag` 검색 결과 또는 지정한 `law_chunk`를 바로 `draft_rule`로 적재할 수 있게 했다.
  - 추출 결과가 이미 있는 경우 `items[]`로 `condition_payload` / `effect_payload` / `auxiliary_payload`를 함께 받아 검수용 초안으로 저장하도록 연결했다.
  - `draft_rule` 조회 응답에 `source_document_id`, `source_provision_id`, `extracted_payload`를 포함시켜 관리자 검토에 필요한 원문 연결 정보를 그대로 확인할 수 있게 했다.
- 우선순위: `P2`
- 대상 파일:
  - `backend/api/admin.py`
  - `backend/services/rag_service.py`
  - `backend/services/draft_rule_service.py`
- 작업 내용:
  - `law_chunk` 또는 RAG 검색 결과를 검수용 `draft_rule` 레코드로 저장하는 실제 적재 경로 구현
  - 소스 청크 메타데이터와 추출 페이로드를 함께 저장해 후속 승인 단계와 연결
- 완료 기준:
  - 법령 검색 결과가 수동 복사 없이 `draft_rule` 검수 큐로 들어간다.

#### TASK-D4. `draft_rule` 승인 시 보조 규칙 자동 승격

- 상태: `done`
- 변경 파일:
  - `backend/api/admin.py`
  - `backend/db/models.py`
  - `db/init.sql`
  - `db/migrations/20260325_add_draft_rule_aux_approval_tracking.sql`
  - `backend/tests/test_admin_draft_rule_approval.py`
- 구현 메모:
  - `approve_draft_rule`가 `auxiliary_payload`의 `industry_exception_rules`, `sign_count_rules`, `special_zone_rules`를 각각 운영 테이블로 승격하도록 확장했다.
  - 메인 `rule_condition` / `rule_effect`가 없는 보조 규칙 전용 초안도 승인 가능하게 처리했다.
  - `draft_rule.approved_auxiliary_rule_ids`에 승인으로 생성된 보조 규칙 ID를 기록해 추적 가능하게 했다.
- 우선순위: `P2`
- 대상 파일:
  - `backend/api/admin.py`
  - `backend/db/models.py`
  - `db/init.sql`
- 작업 내용:
  - `draft_rule` 승인 시 보조 규칙 테이블 자동 적재
  - 승인 결과 ID를 `draft_rule`에 기록해 감사 추적 유지
- 완료 기준:
  - 검수 완료된 특례/수량/특수구역 규칙이 수동 SQL 없이 운영 규칙 테이블로 반영된다.

### 16.5 추천 구현 순서

1. `TASK-A1` ~ `TASK-A4`로 API, 엔진 결과 모델, DB 스키마를 먼저 확장한다.
2. `TASK-A6`, `TASK-A3`를 이어서 진행해 돌출간판 규칙 데이터와 판정 로직을 맞춘다.
3. `TASK-A7`로 돌출간판 회귀 테스트를 고정한다.
4. 이후 `TASK-B1`, `TASK-B2`로 공통 구조를 정리한 뒤 `TASK-C1` ~ `TASK-C3`로 벽면이용간판을 확장한다.
5. 운영 자동화와 규칙 추출 검수 흐름은 `TASK-D1` ~ `TASK-D4`까지 연결했고, 다음으로는 초안 payload 표준화와 영향 규칙 자동 식별을 후속 범위로 잡는다.

### 16.6 1차 릴리즈 체크리스트

- 돌출간판 입력 폼이 규격, 수량, 예외, 안전점검 판정에 필요한 필드를 모두 받는다.
- `/api/v1/judge`가 기존 요청과 신규 확장 요청을 모두 처리한다.
- 엔진이 `missing_input`과 `missing_rule`을 구분한다.
- 돌출간판 대표 테스트 케이스가 자동화되어 있다.
- 결과 화면에서 `decision`, `administrative_action`, `review_type`, `safety_check`, `warnings`를 함께 표시한다.
