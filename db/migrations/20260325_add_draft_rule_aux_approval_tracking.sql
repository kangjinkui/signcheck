BEGIN;

ALTER TABLE draft_rule
  ADD COLUMN IF NOT EXISTS approved_auxiliary_rule_ids JSONB DEFAULT '{}';

COMMIT;
