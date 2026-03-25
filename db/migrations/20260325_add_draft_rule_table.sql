BEGIN;

CREATE TABLE IF NOT EXISTS draft_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  install_subtype VARCHAR(100),
  title           VARCHAR(200) NOT NULL,
  source_type     VARCHAR(50) NOT NULL,
  source_document_id UUID REFERENCES document_master(id),
  source_provision_id UUID REFERENCES provision(id),
  source_chunk_ids JSONB DEFAULT '[]',
  summary         TEXT,
  extracted_payload JSONB DEFAULT '{}',
  condition_payload JSONB DEFAULT '{}',
  effect_payload  JSONB DEFAULT '{}',
  auxiliary_payload JSONB DEFAULT '{}',
  status          VARCHAR(30) NOT NULL DEFAULT 'draft',
  reviewer_note   TEXT,
  reviewer_id     VARCHAR(100),
  approved_rule_condition_id UUID REFERENCES rule_condition(id),
  approved_rule_effect_id UUID REFERENCES rule_effect(id),
  reviewed_at     TIMESTAMP,
  created_at      TIMESTAMP DEFAULT NOW(),
  updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_draft_rule_sign_type_status
  ON draft_rule(sign_type, status, created_at DESC);

COMMIT;
