BEGIN;

ALTER TABLE rule_condition
  ADD COLUMN IF NOT EXISTS business_category VARCHAR(100),
  ADD COLUMN IF NOT EXISTS install_location_type VARCHAR(100),
  ADD COLUMN IF NOT EXISTS special_zone VARCHAR(100),
  ADD COLUMN IF NOT EXISTS existing_sign_count_for_business INT,
  ADD COLUMN IF NOT EXISTS exception_review_approved BOOLEAN;

ALTER TABLE rule_effect
  ADD COLUMN IF NOT EXISTS administrative_action VARCHAR(20),
  ADD COLUMN IF NOT EXISTS max_thickness DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS min_bottom_clearance DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS min_bottom_clearance_no_sidewalk DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS max_top_height_relative_building DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS max_top_height_from_ground DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS max_count_per_business INT,
  ADD COLUMN IF NOT EXISTS requires_no_existing_wall_sign BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS requires_alignment BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS safety_check_min_height DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS safety_check_min_area DECIMAL(10,2);

CREATE TABLE IF NOT EXISTS industry_exception_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  exception_type  VARCHAR(50) NOT NULL,
  max_height      DECIMAL(10,2),
  max_protrusion  DECIMAL(10,2),
  max_thickness   DECIMAL(10,2),
  review_type     VARCHAR(50),
  warnings        JSONB DEFAULT '[]',
  provision_id    UUID REFERENCES provision(id),
  priority        INT DEFAULT 100
);

CREATE TABLE IF NOT EXISTS sign_count_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  exception_type  VARCHAR(50),
  max_count_per_business INT NOT NULL,
  requires_no_existing_wall_sign BOOLEAN DEFAULT FALSE,
  warnings        JSONB DEFAULT '[]',
  provision_id    UUID REFERENCES provision(id),
  priority        INT DEFAULT 100
);

CREATE TABLE IF NOT EXISTS special_zone_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  special_zone    VARCHAR(100) NOT NULL,
  decision        VARCHAR(20) NOT NULL,
  administrative_action VARCHAR(20),
  review_type     VARCHAR(50),
  warnings        JSONB DEFAULT '[]',
  provision_id    UUID REFERENCES provision(id),
  priority        INT DEFAULT 100
);

CREATE INDEX IF NOT EXISTS idx_industry_exception_rule_sign_type
  ON industry_exception_rule(sign_type, exception_type);
CREATE INDEX IF NOT EXISTS idx_sign_count_rule_sign_type
  ON sign_count_rule(sign_type, exception_type);
CREATE INDEX IF NOT EXISTS idx_special_zone_rule_sign_type
  ON special_zone_rule(sign_type, special_zone);

COMMIT;
