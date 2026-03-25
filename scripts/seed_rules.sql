-- =============================================================================
-- SignCheck / AdJudge — 규칙 시드 데이터
-- =============================================================================
-- 적용 법령 계층:
--   국가법령 (옥외광고물법 시행령) > 서울시 조례 > 강남구 조례/심의기준
--   상충 시 강남구 기준 우선 적용
--
-- 마지막 업데이트: 2026-03-25
-- 근거 문서:
--   - 옥외광고물법 시행령 제4·5조 (허가/신고 분류)
--   - 서울특별시 옥외광고물 조례 제4~17조
--   - 서울특별시 강남구 옥외광고물 심의기준 (2023-2341호, 2023-09-22)
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 기존 규칙 초기화 (멱등성 보장)
-- rule_effect는 rule_condition ON DELETE CASCADE로 자동 삭제
-- -----------------------------------------------------------------------------
TRUNCATE TABLE special_zone_rule CASCADE;
TRUNCATE TABLE sign_count_rule CASCADE;
TRUNCATE TABLE industry_exception_rule CASCADE;
TRUNCATE TABLE rule_condition CASCADE;

-- =============================================================================
-- 1. 돌출간판
--    근거: 시행령 제4조 (허가), 서울시 조례 제6조, 강남구 심의기준 §3.나.2
--    강남구 특이사항:
--      - 세로 3m 이내 (서울시 조례 3.5m보다 엄격)
--      - 5층 이하 설치 원칙
-- =============================================================================

-- 돌출간판: 테헤란로 금지 특수구역 규칙
INSERT INTO special_zone_rule (
  sign_type,
  special_zone,
  decision,
  administrative_action,
  review_type,
  warnings,
  provision_id,
  priority
)
VALUES (
  '돌출간판',
  'tehranro',
  'prohibited',
  NULL,
  NULL,
  '["테헤란로변 대지는 돌출간판 설치 금지 (지구단위계획 시행지침)"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556',
  10
);

-- 돌출간판: 업종 특례 규칙
INSERT INTO industry_exception_rule (
  sign_type,
  exception_type,
  max_height,
  max_protrusion,
  max_thickness,
  review_type,
  warnings,
  provision_id,
  priority
) VALUES
  (
    '돌출간판',
    'beauty',
    0.80,
    0.50,
    0.30,
    NULL,
    '["이·미용업소 표지등 특례 적용"]'::jsonb,
    'b050815c-97c8-4f66-b8d0-012f0e8d4556',
    50
  ),
  (
    '돌출간판',
    'medical',
    NULL,
    NULL,
    NULL,
    NULL,
    '["의료기관/약국 업종 특례 적용"]'::jsonb,
    'b050815c-97c8-4f66-b8d0-012f0e8d4556',
    60
  );

-- 돌출간판: 수량 규칙
INSERT INTO sign_count_rule (
  sign_type,
  exception_type,
  max_count_per_business,
  requires_no_existing_wall_sign,
  warnings,
  provision_id,
  priority
) VALUES
  (
    '돌출간판',
    NULL,
    1,
    true,
    '["업소당 1개 원칙", "기존 벽면이용간판과 총량 관계 확인 필요"]'::jsonb,
    'b050815c-97c8-4f66-b8d0-012f0e8d4556',
    100
  ),
  (
    '돌출간판',
    'beauty',
    2,
    false,
    '["이·미용업 특례 수량 완화 적용"]'::jsonb,
    'b050815c-97c8-4f66-b8d0-012f0e8d4556',
    50
  ),
  (
    '돌출간판',
    'medical',
    2,
    false,
    '["의료기관/약국 특례 수량 완화 적용"]'::jsonb,
    'b050815c-97c8-4f66-b8d0-012f0e8d4556',
    60
  );

-- 돌출간판: 6층 이상 금지 규칙
WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_min, ad_type, priority)
  VALUES ('돌출간판', 6, 'both', 20)
  RETURNING id
)
INSERT INTO rule_effect (
  rule_id,
  decision,
  administrative_action,
  review_type,
  display_period,
  warnings,
  provision_id
)
SELECT rc.id, 'prohibited', NULL, NULL, '해당없음',
  '["돌출간판은 건물 5층 이하에만 설치 가능"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

-- 돌출간판: 자사광고 (priority 100)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_max, ad_type, priority)
  VALUES ('돌출간판', 5, 'self', 100)
  RETURNING id
)
INSERT INTO rule_effect (
  rule_id,
  decision,
  administrative_action,
  review_type,
  max_height,
  max_protrusion,
  max_thickness,
  min_bottom_clearance,
  min_bottom_clearance_no_sidewalk,
  max_top_height_relative_building,
  safety_check_min_height,
  safety_check_min_area,
  display_period,
  warnings,
  provision_id
)
SELECT rc.id, 'permit', 'permit', '소심의', 3.00, 1.00, 0.30, 3.00, 4.00, 0.00, 5.00, 1.00, '3년',
  '["강남구 기준 세로 3m 이하", "돌출폭 1m 이하", "두께 0.3m 이하", "보도 3m / 비보도 4m 이상 이격"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

-- 돌출간판: 자사광고 심의 특례 승인 규칙
WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_max, ad_type, exception_review_approved, priority)
  VALUES ('돌출간판', 5, 'self', true, 90)
  RETURNING id
)
INSERT INTO rule_effect (
  rule_id,
  decision,
  administrative_action,
  review_type,
  max_height,
  max_protrusion,
  max_thickness,
  min_bottom_clearance,
  min_bottom_clearance_no_sidewalk,
  max_top_height_relative_building,
  safety_check_min_height,
  safety_check_min_area,
  display_period,
  warnings,
  provision_id
)
SELECT rc.id, 'permit', 'permit', '심의특례', 3.00, 1.00, 0.30, 3.00, 4.00, 0.00, 5.00, 1.00, '3년',
  '["심의 특례 승인 시 규격 초과 항목을 별도 검토 후 예외 처리 가능", "기본 구조·안전 기준은 유지"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

-- 돌출간판: 타사광고 (priority 120)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_max, ad_type, priority)
  VALUES ('돌출간판', 5, 'third_party', 120)
  RETURNING id
)
INSERT INTO rule_effect (
  rule_id,
  decision,
  administrative_action,
  review_type,
  max_height,
  max_protrusion,
  max_thickness,
  min_bottom_clearance,
  min_bottom_clearance_no_sidewalk,
  max_top_height_relative_building,
  safety_check_min_height,
  safety_check_min_area,
  display_period,
  warnings,
  provision_id
)
SELECT rc.id, 'permit', 'permit', '대심의', 3.00, 1.00, 0.30, 3.00, 4.00, 0.00, 5.00, 1.00, '3년',
  '["강남구 기준 세로 3m 이하", "돌출폭 1m 이하", "두께 0.3m 이하", "보도 3m / 비보도 4m 이상 이격", "타사광고는 대심의 대상"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

-- =============================================================================
-- 2. 벽면이용간판
--    근거: 시행령 제5조(신고)/제4조(허가), 서울시 조례 제4조
--    강남구 심의기준: 3층 이하 시조례 제4조 적용, 4층 이상 각 면 표시 원칙
-- =============================================================================

-- 벽면이용간판: 1-3층 일반 벽면 기본 (priority 100)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, install_subtype, floor_max, ad_type, priority)
  VALUES ('벽면이용간판', 'wall_sign_general_under_5f', 3, 'self', 100)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 0.80, 10.00, 0.30, '3년',
  '["3층 이하 일반 벽면간판은 판류형/입체형을 모두 검토하되 형태별 세로 기준은 엔진에서 추가 판정한다."]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

-- 벽면이용간판: 4-15층 자사 (permit, priority 150)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, install_subtype, floor_min, floor_max, ad_type, priority)
  VALUES ('벽면이용간판', 'wall_sign_top_building', 4, 15, 'self', 150)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, max_area, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, 225.00, 0.40, '3년',
  '["면적 225㎡ 이하, 돌출폭 40cm 이내, 구조안전확인 필요 (서울시 조례 제4조④)"]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

-- 벽면이용간판: 4-15층 타사 (permit, priority 155)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, install_subtype, floor_min, floor_max, ad_type, priority)
  VALUES ('벽면이용간판', 'wall_sign_top_building', 4, 15, 'third_party', 155)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, max_area, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, 225.00, 0.40, '3년',
  '["면적 225㎡ 이하, 상업지역 건물에 한하여 타사광고 가능 (서울시 조례 제4조④나)"]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

-- 벽면이용간판: 1-5층 자사 판류형 기본 (report, priority 200)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, install_subtype, floor_max, ad_type, priority)
  VALUES ('벽면이용간판', 'wall_sign_general_under_5f', 5, 'self', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 0.80, 10.00, 0.30, '3년',
  '["가로 업소폭 80% 이내 최대 10m, 세로 80cm(판류형)/45cm(입체형), 돌출폭 30cm 이내 (서울시 조례 제4조)"]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

-- =============================================================================
-- 3. 옥상간판
--    근거: 시행령 제4조 (허가), 서울시 조례 제8조
--    볼링핀 모형 등 옥상 고정물: 15층 이하, 최대 3.5m
-- =============================================================================
WITH rc AS (
  INSERT INTO rule_condition (sign_type, ad_type, priority)
  VALUES ('옥상간판', 'self', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, 3.50, '3년',
  '["옥상간판 간 수평거리 50m 이상 유지 필요, 구조안전확인 필요 (서울시 조례 제8조)"]'::jsonb,
  '381ea6f5-f803-4628-bd5b-8e5ef1252b8f'
FROM rc;

-- =============================================================================
-- 4. 지주이용간판
--    근거: 시행령 제5조(신고)/제4조(허가), 서울시 조례 제9조
--    강남구 특이사항: 5개 이상 업체 연립형 원칙, 단독형은 심의위원회 심의
-- =============================================================================

-- 지주이용간판: 1층(지면) → 신고 (priority 200)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_max, priority)
  VALUES ('지주이용간판', 1, 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 3.00, 5.00, '3년',
  '["강남구에서는 동일 장소 5개 이상 업체 연립형 설치 원칙 (강남구 심의기준 §3.나.3)", "단독건물 사용·등록 상표·상징모형 등 단독형은 심의위원회 심의 필요"]'::jsonb,
  'cd099dc5-951f-45fc-9d5c-20adc18c26eb'
FROM rc;

-- 지주이용간판: 4m 이상 (허가) → permit (priority 210)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, priority)
  VALUES ('지주이용간판', 210)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '소심의', 3.00, 5.00, '3년',
  '["강남구에서는 동일 장소 5개 이상 업체 연립형 설치 원칙 (강남구 심의기준 §3.나.3)", "단독건물 사용·등록 상표·상징모형 등 단독형은 심의위원회 심의 필요"]'::jsonb,
  'cd099dc5-951f-45fc-9d5c-20adc18c26eb'
FROM rc;

-- =============================================================================
-- 5. 입간판
--    근거: 시행령 제5조 (신고), 서울시 조례 제9조의2
--    자사광고만 허용, 1층(지상) 설치, 합계면적 1.2㎡ 이하, 조명 불가
-- =============================================================================
WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_min, ad_type, priority)
  VALUES ('입간판', 2, 'both', 20)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, display_period, warnings, provision_id)
SELECT rc.id, 'prohibited', NULL, NULL, '해당없음',
  '["입간판은 건물 부지 내 1층(지상)에만 설치할 수 있습니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

WITH rc AS (
  INSERT INTO rule_condition (sign_type, area_min, ad_type, priority)
  VALUES ('입간판', 1.21, 'both', 30)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, display_period, warnings, provision_id)
SELECT rc.id, 'prohibited', NULL, NULL, '해당없음',
  '["입간판의 합계면적은 1.2㎡ 이하여야 합니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_max, area_max, ad_type, priority)
  VALUES ('입간판', 1, 1.20, 'self', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 1.20, '1년',
  '["자사광고만 표시 가능, 전기·조명 사용 불가 (서울시 조례 제9조의2)", "입간판은 건물 부지 내 1층(지상) 설치, 합계면적 1.2㎡ 이하 기준을 충족해야 합니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

-- =============================================================================
-- 6. 공연간판
--    근거: 시행령 제4조 (허가), 서울시 조례 제7조
--    공연장이 있는 건물 벽면에만 설치, 연립형 원칙
-- =============================================================================

-- 공연간판: 자사 (priority 100)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, ad_type, priority)
  VALUES ('공연간판', 'self', 100)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', 0.30, '3년',
  '["공연장이 있는 건물의 벽면에만 설치 가능", "공연 중 또는 다음 공연 내용을 연립형으로 표시", "가로크기: 해당 벽면 가로폭의 1/3 이내"]'::jsonb,
  '9da63f7d-7d6f-444e-b3aa-e72f71a498e4'
FROM rc;

-- 공연간판: 타사 (priority 110)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, ad_type, priority)
  VALUES ('공연간판', 'third_party', 110)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', 0.30, '3년',
  '["공연장이 있는 건물의 벽면에만 설치 가능", "공연 중 또는 다음 공연 내용을 연립형으로 표시", "타사 광고는 전광류·디지털광고물에 한함 (180cm 이하)"]'::jsonb,
  '9da63f7d-7d6f-444e-b3aa-e72f71a498e4'
FROM rc;

-- =============================================================================
-- 7. 현수막
--    근거: 시행령 제5조 (신고), 서울시 조례 제11조
--    강남구 특이사항: 현수막 및 게시시설 설치 금지 (강남구 심의기준 §3.나.4)
--    예외: 대규모점포, 전시관, 연면적 1만㎡ 이상 상업/공업지역 건물 등 → 심의 후 가능
-- =============================================================================
WITH rc AS (
  INSERT INTO rule_condition (sign_type, priority)
  VALUES ('현수막', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, display_period, warnings, provision_id)
SELECT rc.id, 'prohibited', '소심의', 2.00, 0.70, '해당없음',
  '["강남구에서는 현수막 및 게시시설 설치 금지 (강남구 심의기준 §3.나.4)", "예외: 대규모점포·전시관·연면적 1만㎡ 이상 상업/공업지역 건물·관광숙박업 등록 건물은 심의위원회 심의 후 가능"]'::jsonb,
  'cf184061-0afc-43cf-a80f-2f9f89a204c2'
FROM rc;

-- =============================================================================
-- 8. 애드벌룬 (옥상 고정)
--    근거: 시행령 제5조 (신고), 서울시 조례 제13조②
--    상업·공업지역 건물만 가능, 높이 10m·면적 100㎡ 이하
-- =============================================================================

-- 애드벌룬 옥상: 일반상업지역 (priority 200)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, zone, priority)
  VALUES ('애드벌룬', '일반상업지역', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 100.00, 10.00, '1년',
  '["상업·공업지역만 가능, 높이 10m·건물높이 1/2 이하, 면적 합계 100㎡ 이하 (서울시 조례 제13조②)"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

-- 애드벌룬 옥상: 준공업지역 (priority 201)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, zone, priority)
  VALUES ('애드벌룬', '준공업지역', 201)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 100.00, 10.00, '1년',
  '["상업·공업지역만 가능, 높이 10m·건물높이 1/2 이하, 면적 합계 100㎡ 이하 (서울시 조례 제13조②)"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

-- =============================================================================
-- 9. 애드벌룬 (지면 고정)
--    근거: 시행령 제5조 (신고), 서울시 조례 제13조③
--    지주이용간판이 없는 건물 부지 내, 지주이용간판 기준 준용
-- =============================================================================

-- 애드벌룬(지면): 일반상업지역 (priority 200)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, zone, priority)
  VALUES ('애드벌룬(지면)', '일반상업지역', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 3.00, 5.00, '1년',
  '["지주이용간판이 표시되지 않은 건물 부지 안에서만 설치 가능", "지면 설치: 지주이용간판 기준(서울시 조례 제9조·시행령 제16조) 준용"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

-- 애드벌룬(지면): 준공업지역 (priority 201)
WITH rc AS (
  INSERT INTO rule_condition (sign_type, zone, priority)
  VALUES ('애드벌룬(지면)', '준공업지역', 201)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 3.00, 5.00, '1년',
  '["지주이용간판이 표시되지 않은 건물 부지 안에서만 설치 가능", "지면 설치: 지주이용간판 기준(서울시 조례 제9조·시행령 제16조) 준용"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

-- =============================================================================
-- 10. 창문이용광고물
--     근거: 시행령 제5조 (신고), 서울시 조례 제17조
--     3층 이하, 가로·세로 각 30cm 이하, 조명 불가
-- =============================================================================
WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_max, ad_type, priority)
  VALUES ('창문이용광고물', 3, 'self', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 0.30, 0.30, '1년',
  '["건물 3층 이하, 가로·세로 각 30cm 이하, 조명 불가 (서울시 조례 제17조)"]'::jsonb,
  '4c73e15e-9b7c-4b73-a785-aba9ce7ca6e0'
FROM rc;

-- =============================================================================
-- 11. 선전탑
--     근거: 시행령 제4조 (허가), 서울시 조례 제16조
--     상업·공업지역, 구청장이 지정한 장소만 가능
-- =============================================================================
WITH rc AS (
  INSERT INTO rule_condition (sign_type, zone, priority)
  VALUES ('선전탑', '일반상업지역', 200)
  RETURNING id
)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, '3년',
  '["상업·공업지역 내 구청장 지정 장소만 가능, 20m 이상 도로변 설치 가능 (서울시 조례 제16조)"]'::jsonb,
  'aff7df15-8c1e-4d54-9e63-df433e0ab86a'
FROM rc;

COMMIT;

-- =============================================================================
-- 검증 쿼리 (실행 후 확인용)
-- =============================================================================
-- SELECT rc.sign_type, rc.floor_min, rc.floor_max, rc.zone, rc.ad_type, rc.priority,
--        re.decision, re.review_type, re.max_area, re.max_height, re.max_width,
--        re.max_protrusion, re.display_period
-- FROM rule_condition rc
-- JOIN rule_effect re ON rc.id = re.rule_id
-- ORDER BY rc.sign_type, rc.priority;
