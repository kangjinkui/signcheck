BEGIN;

ALTER TABLE rule_condition
  ADD COLUMN IF NOT EXISTS install_subtype VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_rule_condition_sign_type_subtype
  ON rule_condition(sign_type, install_subtype, priority);

COMMIT;
