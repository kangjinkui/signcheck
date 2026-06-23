-- 건물 상단간판은 4층 이상 건물에 적용되므로 15층 상한을 제거한다.
-- 16층 이상 건물도 동일한 규격 검사를 타야 하며, 규칙 미정의 fallback으로 빠지면 안 된다.

UPDATE rule_condition
SET floor_max = NULL
WHERE sign_type = '벽면이용간판'
  AND install_subtype = 'wall_sign_top_building'
  AND floor_min = 4
  AND floor_max = 15;
