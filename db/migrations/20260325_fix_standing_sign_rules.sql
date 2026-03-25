BEGIN;

DELETE FROM rule_effect
WHERE rule_id IN (
  SELECT id
  FROM rule_condition
  WHERE sign_type = '입간판'
);

DELETE FROM rule_condition
WHERE sign_type = '입간판';

WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_min, ad_type, priority)
  VALUES ('입간판', 2, 'both', 20)
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
SELECT
  rc.id,
  'prohibited',
  NULL,
  NULL,
  '해당없음',
  '["입간판은 건물 부지 내 1층(지상)에만 설치할 수 있습니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

WITH rc AS (
  INSERT INTO rule_condition (sign_type, area_min, ad_type, priority)
  VALUES ('입간판', 1.21, 'both', 30)
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
SELECT
  rc.id,
  'prohibited',
  NULL,
  NULL,
  '해당없음',
  '["입간판의 합계면적은 1.2㎡ 이하여야 합니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

WITH rc AS (
  INSERT INTO rule_condition (sign_type, floor_max, area_max, ad_type, priority)
  VALUES ('입간판', 1, 1.20, 'self', 200)
  RETURNING id
)
INSERT INTO rule_effect (
  rule_id,
  decision,
  administrative_action,
  review_type,
  max_height,
  display_period,
  warnings,
  provision_id
)
SELECT
  rc.id,
  'report',
  'report',
  '소심의',
  1.20,
  '1년',
  '["자사광고만 표시 가능, 전기·조명 사용 불가 (서울시 조례 제9조의2)", "입간판은 건물 부지 내 1층(지상) 설치, 합계면적 1.2㎡ 이하 기준을 충족해야 합니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

COMMIT;
