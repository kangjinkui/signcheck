-- Fix provision reference notation for wall_sign_top_building rules
--
-- 문제: wall_sign_top_building 규칙의 warnings에 "서울시 조례 제4조④"로
--       표기되어 제4조제1항제4호(가로형 대형 벽면광고)를 잘못 참조하고 있었음.
--
-- 수정:
--   · 가로형(면적형): 서울시 조례 제4조제1항제4호  (기존 ④ 표기 정정)
--   · 세로형(건물명 표시): 서울시 조례 제4조제1항제3호
--     → Python rule_engine._judge_wall_sign_top_building에서
--       display_orientation == "vertical"일 때 런타임 치환으로 처리.

UPDATE rule_effect re
SET warnings = (
    SELECT jsonb_agg(
        to_jsonb(
            replace(
                replace(
                    elem #>> '{}',
                    '서울시 조례 제4조④나',
                    '서울시 조례 제4조제1항제4호나목'
                ),
                '서울시 조례 제4조④',
                '서울시 조례 제4조제1항제4호'
            )
        )
    )
    FROM jsonb_array_elements(re.warnings) AS elem
)
FROM rule_condition rc
WHERE re.rule_id = rc.id
  AND rc.install_subtype = 'wall_sign_top_building'
  AND re.warnings::text LIKE '%제4조④%';
