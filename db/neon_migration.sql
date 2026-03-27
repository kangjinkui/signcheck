-- =============================================================================
-- AdJudge — Neon 마이그레이션 스크립트 (스키마 + 시드 규칙)
-- =============================================================================
-- 실행 순서:
--   1. 익스텐션 + 스키마 생성
--   2. 기준 provision/document 플레이스홀더 삽입 (FK 참조용)
--   3. 기본 시드 데이터 (zone_rule, fee_rule, checklist_rule)
--   4. 판정 규칙 시드 (special_zone_rule, rule_condition, rule_effect, …)
--
-- 주의: pgvector 익스텐션은 Neon에서 기본 지원됩니다.
--       law_chunk (vector(768)) 테이블은 생성되지만 임베딩 데이터는 포함하지 않습니다.
-- =============================================================================

-- ─────────────────────────────────────────
-- 1. 익스텐션
-- ─────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────
-- 2. 스키마 생성
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_master (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           VARCHAR(200) NOT NULL,
  type           VARCHAR(50),
  jurisdiction   VARCHAR(50),
  effective_date DATE,
  version        VARCHAR(20),
  source_type    VARCHAR(20),
  file_url       TEXT,
  created_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS provision (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id    UUID REFERENCES document_master(id) ON DELETE CASCADE,
  article        VARCHAR(50),
  paragraph      VARCHAR(50),
  item           VARCHAR(50),
  content        TEXT NOT NULL,
  effective_date DATE
);

CREATE TABLE IF NOT EXISTS legal_relation (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_provision UUID REFERENCES provision(id),
  to_provision   UUID REFERENCES provision(id),
  relation_type  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS rule_condition (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type        VARCHAR(100) NOT NULL,
  install_subtype  VARCHAR(100),
  business_category VARCHAR(100),
  install_location_type VARCHAR(100),
  floor_min        INT,
  floor_max        INT,
  light_type       VARCHAR(50),
  digital          BOOLEAN DEFAULT FALSE,
  area_min         DECIMAL(10,2),
  area_max         DECIMAL(10,2),
  zone             VARCHAR(100),
  special_zone     VARCHAR(100),
  ad_type          VARCHAR(20),
  tehranro         BOOLEAN,
  vendor_count_min INT,
  existing_sign_count_for_business INT,
  has_sidewalk     BOOLEAN,
  exception_review_approved BOOLEAN,
  priority         INT DEFAULT 100
);

CREATE TABLE IF NOT EXISTS rule_effect (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_id         UUID REFERENCES rule_condition(id) ON DELETE CASCADE,
  decision        VARCHAR(20) NOT NULL,
  administrative_action VARCHAR(20),
  review_type     VARCHAR(50),
  safety_check    BOOLEAN DEFAULT FALSE,
  max_area        DECIMAL(10,2),
  max_height      DECIMAL(10,2),
  max_protrusion  DECIMAL(10,2),
  max_width       DECIMAL(10,2),
  max_thickness   DECIMAL(10,2),
  min_bottom_clearance DECIMAL(10,2),
  min_bottom_clearance_no_sidewalk DECIMAL(10,2),
  max_top_height_relative_building DECIMAL(10,2),
  max_top_height_from_ground DECIMAL(10,2),
  max_count_per_business INT,
  requires_no_existing_wall_sign BOOLEAN DEFAULT FALSE,
  requires_alignment BOOLEAN DEFAULT FALSE,
  safety_check_min_height DECIMAL(10,2),
  safety_check_min_area DECIMAL(10,2),
  display_period  VARCHAR(20),
  warnings        JSONB DEFAULT '[]',
  provision_id    UUID REFERENCES provision(id)
);

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

CREATE TABLE IF NOT EXISTS fee_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  ad_type         VARCHAR(20) DEFAULT 'self',
  area_threshold  DECIMAL(10,2) NOT NULL,
  base_fee        INT NOT NULL,
  extra_fee       INT DEFAULT 0,
  light_weight    DECIMAL(5,2) DEFAULT 1.0,
  digital_weight  DECIMAL(5,2) DEFAULT 2.0,
  provision_id    UUID REFERENCES provision(id)
);

CREATE TABLE IF NOT EXISTS checklist_rule (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  work_type     VARCHAR(50) NOT NULL,
  sign_type     VARCHAR(100),
  required_docs JSONB NOT NULL,
  optional_docs JSONB DEFAULT '[]',
  condition     TEXT
);

CREATE TABLE IF NOT EXISTS zone_rule (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name             VARCHAR(100) NOT NULL UNIQUE,
  sign_count_limit INT DEFAULT 1,
  restriction      TEXT,
  prohibited_types JSONB DEFAULT '[]',
  provision_id     UUID REFERENCES provision(id)
);

CREATE TABLE IF NOT EXISTS case_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  input_data      JSONB NOT NULL,
  output_data     JSONB NOT NULL,
  rule_version    VARCHAR(20),
  decision        VARCHAR(20),
  fee_calculated  INT,
  rag_chunks_used JSONB DEFAULT '[]',
  user_id         VARCHAR(100),
  created_at      TIMESTAMP DEFAULT NOW()
);

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
  approved_auxiliary_rule_ids JSONB DEFAULT '{}',
  reviewed_at     TIMESTAMP,
  created_at      TIMESTAMP DEFAULT NOW(),
  updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS law_chunk (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id  UUID REFERENCES document_master(id) ON DELETE CASCADE,
  provision_id UUID REFERENCES provision(id) ON DELETE CASCADE,
  content      TEXT NOT NULL,
  embedding    vector(768),
  chunk_index  INT DEFAULT 0,
  law_name     VARCHAR(200),
  article      VARCHAR(50),
  created_at   TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- 인덱스
-- ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_rule_condition_sign_type ON rule_condition(sign_type);
CREATE INDEX IF NOT EXISTS idx_rule_condition_priority ON rule_condition(priority);
CREATE INDEX IF NOT EXISTS idx_rule_condition_sign_type_subtype ON rule_condition(sign_type, install_subtype, priority);
CREATE INDEX IF NOT EXISTS idx_industry_exception_rule_sign_type ON industry_exception_rule(sign_type, exception_type);
CREATE INDEX IF NOT EXISTS idx_sign_count_rule_sign_type ON sign_count_rule(sign_type, exception_type);
CREATE INDEX IF NOT EXISTS idx_draft_rule_sign_type_status ON draft_rule(sign_type, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_special_zone_rule_sign_type ON special_zone_rule(sign_type, special_zone);
CREATE INDEX IF NOT EXISTS idx_fee_rule_sign_type ON fee_rule(sign_type, ad_type);
CREATE INDEX IF NOT EXISTS idx_case_log_created_at ON case_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_provision_document ON provision(document_id);
CREATE INDEX IF NOT EXISTS idx_law_chunk_provision ON law_chunk(provision_id);
CREATE INDEX IF NOT EXISTS idx_law_chunk_document  ON law_chunk(document_id);

-- =============================================================================
-- 3. 법령 참조 플레이스홀더 (seed_rules.sql이 참조하는 provision_id FK)
--    실제 법령 원문은 embed_laws.py 또는 관리자 업로드로 별도 적재합니다.
-- =============================================================================
BEGIN;

-- 기준 문서 마스터 (강남구 옥외광고물 심의기준)
INSERT INTO document_master (id, name, type, jurisdiction, effective_date, version, source_type)
VALUES (
  'aaaaaaaa-0000-0000-0000-000000000001',
  '강남구 옥외광고물 심의기준 / 서울특별시 옥외광고물 조례',
  'ordinance',
  'gangnam',
  '2023-09-22',
  '2023-2341',
  'manual'
)
ON CONFLICT (id) DO NOTHING;

-- seed_rules.sql 에서 참조하는 provision 플레이스홀더 10개
INSERT INTO provision (id, document_id, article, content) VALUES
  -- b050815c: 돌출간판 (서울시 조례 제6조 / 강남구 심의기준 §3.나.2)
  ('b050815c-97c8-4f66-b8d0-012f0e8d4556',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제6조',
   '돌출간판 — 서울특별시 옥외광고물 조례 제6조 및 강남구 심의기준 §3.나.2'),

  -- 8c1d1895: 벽면이용간판 (서울시 조례 제4조)
  ('8c1d1895-39a8-4065-b636-b0e0b9d3d5d1',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제4조',
   '벽면이용간판 — 서울특별시 옥외광고물 조례 제4조'),

  -- 381ea6f5: 옥상간판 (서울시 조례 제8조)
  ('381ea6f5-f803-4628-bd5b-8e5ef1252b8f',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제8조',
   '옥상간판 — 서울특별시 옥외광고물 조례 제8조'),

  -- cd099dc5: 지주이용간판 (서울시 조례 제9조)
  ('cd099dc5-951f-45fc-9d5c-20adc18c26eb',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제9조',
   '지주이용간판 — 서울특별시 옥외광고물 조례 제9조 및 강남구 심의기준 §3.나.3'),

  -- 07c2b695: 입간판 (서울시 조례 제9조의2)
  ('07c2b695-9009-46e4-85e7-4cb1cd455a51',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제9조의2',
   '입간판 — 서울특별시 옥외광고물 조례 제9조의2'),

  -- 9da63f7d: 공연간판 (서울시 조례 제7조)
  ('9da63f7d-7d6f-444e-b3aa-e72f71a498e4',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제7조',
   '공연간판 — 서울특별시 옥외광고물 조례 제7조'),

  -- cf184061: 현수막 (서울시 조례 제11조 / 강남구 심의기준 §3.나.4)
  ('cf184061-0afc-43cf-a80f-2f9f89a204c2',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제11조',
   '현수막 — 서울특별시 옥외광고물 조례 제11조 및 강남구 심의기준 §3.나.4'),

  -- 5c3f570b: 애드벌룬 (서울시 조례 제13조)
  ('5c3f570b-4ddd-4cf0-b1f8-b08df86426ed',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제13조',
   '애드벌룬 — 서울특별시 옥외광고물 조례 제13조'),

  -- 4c73e15e: 창문이용광고물 (서울시 조례 제17조)
  ('4c73e15e-9b7c-4b73-a785-aba9ce7ca6e0',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제17조',
   '창문이용광고물 — 서울특별시 옥외광고물 조례 제17조'),

  -- aff7df15: 선전탑 (서울시 조례 제16조)
  ('aff7df15-8c1e-4d54-9e63-df433e0ab86a',
   'aaaaaaaa-0000-0000-0000-000000000001',
   '제16조',
   '선전탑 — 서울특별시 옥외광고물 조례 제16조')

ON CONFLICT (id) DO NOTHING;

COMMIT;

-- =============================================================================
-- 4. 기본 시드 데이터
-- =============================================================================
INSERT INTO zone_rule (name, sign_count_limit, prohibited_types) VALUES
  ('전용주거지역', 1, '["전광류·디지털광고물", "옥상간판", "지주이용간판"]'),
  ('일반주거지역', 1, '["전광류·디지털광고물", "옥상간판"]'),
  ('준주거지역',   2, '["전광류·디지털광고물"]'),
  ('일반상업지역', 2, '[]'),
  ('근린상업지역', 2, '[]'),
  ('준공업지역',   2, '[]')
ON CONFLICT (name) DO NOTHING;

INSERT INTO fee_rule (sign_type, ad_type, area_threshold, base_fee, extra_fee, light_weight, digital_weight) VALUES
  ('벽면이용간판',           'self',        5,  4000,  1500, 1.5, 2.0),
  ('벽면이용간판',           'third_party', 5,  40000, 2000, 1.5, 2.0),
  ('돌출간판',               'self',        5,  20000, 2000, 1.5, 2.0),
  ('옥상간판',               'self',        10, 40000, 6000, 1.5, 2.0),
  ('지주이용간판',           'self',        10, 20000, 2000, 1.5, 2.0),
  ('공공시설물 이용 광고물', 'self',        1,  3000,  1000, 1.5, 2.0),
  ('교통수단 이용 광고물',   'self',        0,  2000,  0,    1.0, 2.0),
  ('입간판',                 'self',        0,  4000,  0,    1.0, 1.0);

INSERT INTO checklist_rule (work_type, sign_type, required_docs, optional_docs) VALUES
  ('report', NULL,
   '["옥외광고물 표시 신청서 1부", "건물(대지) 사용승낙서 1부", "위치도(약도)", "건물전체 원색사진 및 시뮬레이션", "광고물 원색도안", "광고물 설계도", "광고물 시방서", "옥외광고 사업등록증 사본"]',
   '[]'),
  ('permit', NULL,
   '["옥외광고물 허가 신청서 1부", "건물(대지) 사용승낙서 1부", "위치도(약도)", "건물전체 원색사진 및 시뮬레이션", "광고물 원색도안", "광고물 설계도", "광고물 시방서", "옥외광고 사업등록증 사본"]',
   '[]');

-- =============================================================================
-- 5. 판정 규칙 시드
-- =============================================================================
BEGIN;

TRUNCATE TABLE special_zone_rule CASCADE;
TRUNCATE TABLE sign_count_rule CASCADE;
TRUNCATE TABLE industry_exception_rule CASCADE;
TRUNCATE TABLE rule_condition CASCADE;

-- ── 1. 돌출간판 ──────────────────────────────────────────────────────────────
INSERT INTO special_zone_rule (sign_type, special_zone, decision, administrative_action, review_type, warnings, provision_id, priority)
VALUES (
  '돌출간판', 'tehranro', 'prohibited', NULL, NULL,
  '["테헤란로변 대지는 돌출간판 설치 금지 (지구단위계획 시행지침)"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556', 10
);

INSERT INTO industry_exception_rule (sign_type, exception_type, max_height, max_protrusion, max_thickness, review_type, warnings, provision_id, priority)
VALUES
  ('돌출간판', 'beauty',  0.80, 0.50, 0.30, NULL,
   '["이·미용업소 표지등 특례 적용"]'::jsonb,
   'b050815c-97c8-4f66-b8d0-012f0e8d4556', 50),
  ('돌출간판', 'medical', NULL, NULL, NULL, NULL,
   '["의료기관/약국 업종 특례 적용"]'::jsonb,
   'b050815c-97c8-4f66-b8d0-012f0e8d4556', 60);

INSERT INTO sign_count_rule (sign_type, exception_type, max_count_per_business, requires_no_existing_wall_sign, warnings, provision_id, priority)
VALUES
  ('돌출간판', NULL,      1, true,  '["업소당 1개 원칙", "기존 벽면이용간판과 총량 관계 확인 필요"]'::jsonb, 'b050815c-97c8-4f66-b8d0-012f0e8d4556', 100),
  ('돌출간판', 'beauty',  2, false, '["이·미용업 특례 수량 완화 적용"]'::jsonb,                             'b050815c-97c8-4f66-b8d0-012f0e8d4556',  50),
  ('돌출간판', 'medical', 2, false, '["의료기관/약국 특례 수량 완화 적용"]'::jsonb,                         'b050815c-97c8-4f66-b8d0-012f0e8d4556',  60);

WITH rc AS (INSERT INTO rule_condition (sign_type, floor_min, ad_type, priority) VALUES ('돌출간판', 6, 'both', 20) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, display_period, warnings, provision_id)
SELECT rc.id, 'prohibited', NULL, NULL, '해당없음',
  '["돌출간판은 건물 5층 이하에만 설치 가능"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, floor_max, ad_type, priority) VALUES ('돌출간판', 5, 'self', 100) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, max_height, max_protrusion, max_thickness, min_bottom_clearance, min_bottom_clearance_no_sidewalk, max_top_height_relative_building, safety_check_min_height, safety_check_min_area, display_period, warnings, provision_id)
SELECT rc.id, 'permit', 'permit', '소심의', 3.00, 1.00, 0.30, 3.00, 4.00, 0.00, 5.00, 1.00, '3년',
  '["강남구 기준 세로 3m 이하", "돌출폭 1m 이하", "두께 0.3m 이하", "보도 3m / 비보도 4m 이상 이격"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, floor_max, ad_type, exception_review_approved, priority) VALUES ('돌출간판', 5, 'self', true, 90) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, max_height, max_protrusion, max_thickness, min_bottom_clearance, min_bottom_clearance_no_sidewalk, max_top_height_relative_building, safety_check_min_height, safety_check_min_area, display_period, warnings, provision_id)
SELECT rc.id, 'permit', 'permit', '심의특례', 3.00, 1.00, 0.30, 3.00, 4.00, 0.00, 5.00, 1.00, '3년',
  '["심의 특례 승인 시 규격 초과 항목을 별도 검토 후 예외 처리 가능", "기본 구조·안전 기준은 유지"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, floor_max, ad_type, priority) VALUES ('돌출간판', 5, 'third_party', 120) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, max_height, max_protrusion, max_thickness, min_bottom_clearance, min_bottom_clearance_no_sidewalk, max_top_height_relative_building, safety_check_min_height, safety_check_min_area, display_period, warnings, provision_id)
SELECT rc.id, 'permit', 'permit', '대심의', 3.00, 1.00, 0.30, 3.00, 4.00, 0.00, 5.00, 1.00, '3년',
  '["강남구 기준 세로 3m 이하", "돌출폭 1m 이하", "두께 0.3m 이하", "보도 3m / 비보도 4m 이상 이격", "타사광고는 대심의 대상"]'::jsonb,
  'b050815c-97c8-4f66-b8d0-012f0e8d4556'
FROM rc;

-- ── 2. 벽면이용간판 ──────────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, install_subtype, floor_max, ad_type, priority) VALUES ('벽면이용간판', 'wall_sign_general_under_5f', 3, 'self', 100) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 0.80, 10.00, 0.30, '3년',
  '["3층 이하 일반 벽면간판은 판류형/입체형을 모두 검토하되 형태별 세로 기준은 엔진에서 추가 판정한다."]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, install_subtype, floor_min, floor_max, ad_type, priority) VALUES ('벽면이용간판', 'wall_sign_top_building', 4, 15, 'self', 150) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, max_area, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, 225.00, 0.40, '3년',
  '["면적 225㎡ 이하, 돌출폭 40cm 이내, 구조안전확인 필요 (서울시 조례 제4조④)"]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, install_subtype, floor_min, floor_max, ad_type, priority) VALUES ('벽면이용간판', 'wall_sign_top_building', 4, 15, 'third_party', 155) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, max_area, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, 225.00, 0.40, '3년',
  '["면적 225㎡ 이하, 상업지역 건물에 한하여 타사광고 가능 (서울시 조례 제4조④나)"]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, install_subtype, floor_max, ad_type, priority) VALUES ('벽면이용간판', 'wall_sign_general_under_5f', 5, 'self', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 0.80, 10.00, 0.30, '3년',
  '["가로 업소폭 80% 이내 최대 10m, 세로 80cm(판류형)/45cm(입체형), 돌출폭 30cm 이내 (서울시 조례 제4조)"]'::jsonb,
  '8c1d1895-39a8-4065-b636-b0e0b9d3d5d1'
FROM rc;

-- ── 3. 옥상간판 ──────────────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, ad_type, priority) VALUES ('옥상간판', 'self', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, 3.50, '3년',
  '["옥상간판 간 수평거리 50m 이상 유지 필요, 구조안전확인 필요 (서울시 조례 제8조)"]'::jsonb,
  '381ea6f5-f803-4628-bd5b-8e5ef1252b8f'
FROM rc;

-- ── 4. 지주이용간판 ──────────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, floor_max, priority) VALUES ('지주이용간판', 1, 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 3.00, 5.00, '3년',
  '["강남구에서는 동일 장소 5개 이상 업체 연립형 설치 원칙 (강남구 심의기준 §3.나.3)", "단독건물 사용·등록 상표·상징모형 등 단독형은 심의위원회 심의 필요"]'::jsonb,
  'cd099dc5-951f-45fc-9d5c-20adc18c26eb'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, priority) VALUES ('지주이용간판', 210) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '소심의', 3.00, 5.00, '3년',
  '["강남구에서는 동일 장소 5개 이상 업체 연립형 설치 원칙 (강남구 심의기준 §3.나.3)", "단독건물 사용·등록 상표·상징모형 등 단독형은 심의위원회 심의 필요"]'::jsonb,
  'cd099dc5-951f-45fc-9d5c-20adc18c26eb'
FROM rc;

-- ── 5. 입간판 ────────────────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, floor_min, ad_type, priority) VALUES ('입간판', 2, 'both', 20) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, display_period, warnings, provision_id)
SELECT rc.id, 'prohibited', NULL, NULL, '해당없음',
  '["입간판은 건물 부지 내 1층(지상)에만 설치할 수 있습니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, area_min, ad_type, priority) VALUES ('입간판', 1.21, 'both', 30) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, administrative_action, review_type, display_period, warnings, provision_id)
SELECT rc.id, 'prohibited', NULL, NULL, '해당없음',
  '["입간판의 합계면적은 1.2㎡ 이하여야 합니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, floor_max, area_max, ad_type, priority) VALUES ('입간판', 1, 1.20, 'self', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 1.20, '1년',
  '["자사광고만 표시 가능, 전기·조명 사용 불가 (서울시 조례 제9조의2)", "입간판은 건물 부지 내 1층(지상) 설치, 합계면적 1.2㎡ 이하 기준을 충족해야 합니다."]'::jsonb,
  '07c2b695-9009-46e4-85e7-4cb1cd455a51'
FROM rc;

-- ── 6. 공연간판 ──────────────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, ad_type, priority) VALUES ('공연간판', 'self', 100) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', 0.30, '3년',
  '["공연장이 있는 건물의 벽면에만 설치 가능", "공연 중 또는 다음 공연 내용을 연립형으로 표시", "가로크기: 해당 벽면 가로폭의 1/3 이내"]'::jsonb,
  '9da63f7d-7d6f-444e-b3aa-e72f71a498e4'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, ad_type, priority) VALUES ('공연간판', 'third_party', 110) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_protrusion, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', 0.30, '3년',
  '["공연장이 있는 건물의 벽면에만 설치 가능", "공연 중 또는 다음 공연 내용을 연립형으로 표시", "타사 광고는 전광류·디지털광고물에 한함 (180cm 이하)"]'::jsonb,
  '9da63f7d-7d6f-444e-b3aa-e72f71a498e4'
FROM rc;

-- ── 7. 현수막 ────────────────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, priority) VALUES ('현수막', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, display_period, warnings, provision_id)
SELECT rc.id, 'prohibited', '소심의', 2.00, 0.70, '해당없음',
  '["강남구에서는 현수막 및 게시시설 설치 금지 (강남구 심의기준 §3.나.4)", "예외: 대규모점포·전시관·연면적 1만㎡ 이상 상업/공업지역 건물·관광숙박업 등록 건물은 심의위원회 심의 후 가능"]'::jsonb,
  'cf184061-0afc-43cf-a80f-2f9f89a204c2'
FROM rc;

-- ── 8. 애드벌룬 (옥상) ───────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, zone, priority) VALUES ('애드벌룬', '일반상업지역', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 100.00, 10.00, '1년',
  '["상업·공업지역만 가능, 높이 10m·건물높이 1/2 이하, 면적 합계 100㎡ 이하 (서울시 조례 제13조②)"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, zone, priority) VALUES ('애드벌룬', '준공업지역', 201) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 100.00, 10.00, '1년',
  '["상업·공업지역만 가능, 높이 10m·건물높이 1/2 이하, 면적 합계 100㎡ 이하 (서울시 조례 제13조②)"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

-- ── 9. 애드벌룬 (지면) ───────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, zone, priority) VALUES ('애드벌룬(지면)', '일반상업지역', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 3.00, 5.00, '1년',
  '["지주이용간판이 표시되지 않은 건물 부지 안에서만 설치 가능", "지면 설치: 지주이용간판 기준(서울시 조례 제9조·시행령 제16조) 준용"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

WITH rc AS (INSERT INTO rule_condition (sign_type, zone, priority) VALUES ('애드벌룬(지면)', '준공업지역', 201) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_area, max_height, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 3.00, 5.00, '1년',
  '["지주이용간판이 표시되지 않은 건물 부지 안에서만 설치 가능", "지면 설치: 지주이용간판 기준(서울시 조례 제9조·시행령 제16조) 준용"]'::jsonb,
  '5c3f570b-4ddd-4cf0-b1f8-b08df86426ed'
FROM rc;

-- ── 10. 창문이용광고물 ───────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, floor_max, ad_type, priority) VALUES ('창문이용광고물', 3, 'self', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, max_height, max_width, display_period, warnings, provision_id)
SELECT rc.id, 'report', '소심의', 0.30, 0.30, '1년',
  '["건물 3층 이하, 가로·세로 각 30cm 이하, 조명 불가 (서울시 조례 제17조)"]'::jsonb,
  '4c73e15e-9b7c-4b73-a785-aba9ce7ca6e0'
FROM rc;

-- ── 11. 선전탑 ───────────────────────────────────────────────────────────────
WITH rc AS (INSERT INTO rule_condition (sign_type, zone, priority) VALUES ('선전탑', '일반상업지역', 200) RETURNING id)
INSERT INTO rule_effect (rule_id, decision, review_type, safety_check, display_period, warnings, provision_id)
SELECT rc.id, 'permit', '대심의', true, '3년',
  '["상업·공업지역 내 구청장 지정 장소만 가능, 20m 이상 도로변 설치 가능 (서울시 조례 제16조)"]'::jsonb,
  'aff7df15-8c1e-4d54-9e63-df433e0ab86a'
FROM rc;

COMMIT;
