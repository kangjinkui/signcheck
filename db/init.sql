-- 광고판정 (AdJudge) 데이터베이스 초기화
-- PostgreSQL + pgvector

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────
-- 법령 문서 마스터
-- ─────────────────────────────────────────
CREATE TABLE document_master (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           VARCHAR(200) NOT NULL,
  type           VARCHAR(50),        -- 'law', 'ordinance', 'guideline'
  jurisdiction   VARCHAR(50),        -- 'national', 'seoul', 'gangnam'
  effective_date DATE,
  version        VARCHAR(20),
  source_type    VARCHAR(20),        -- 'api', 'pdf'
  file_url       TEXT,
  created_at     TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- 조문 원문
-- ─────────────────────────────────────────
CREATE TABLE provision (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id    UUID REFERENCES document_master(id) ON DELETE CASCADE,
  article        VARCHAR(50),        -- 제3조
  paragraph      VARCHAR(50),        -- 제1항
  item           VARCHAR(50),        -- 제1호
  content        TEXT NOT NULL,
  effective_date DATE
);

-- ─────────────────────────────────────────
-- 조문 관계 (상위법 → 하위법 우선순위)
-- ─────────────────────────────────────────
CREATE TABLE legal_relation (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_provision UUID REFERENCES provision(id),
  to_provision   UUID REFERENCES provision(id),
  relation_type  VARCHAR(50)         -- 'applies', 'overrides', 'exception'
);

-- ─────────────────────────────────────────
-- 판정 규칙 조건
-- ─────────────────────────────────────────
CREATE TABLE rule_condition (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type        VARCHAR(100) NOT NULL,
  install_subtype  VARCHAR(100),
  business_category VARCHAR(100),
  install_location_type VARCHAR(100),
  floor_min        INT,
  floor_max        INT,
  light_type       VARCHAR(50),       -- 'none', 'internal', 'neon_digital'
  digital          BOOLEAN DEFAULT FALSE,
  area_min         DECIMAL(10,2),
  area_max         DECIMAL(10,2),
  zone             VARCHAR(100),      -- 용도지역
  special_zone     VARCHAR(100),
  ad_type          VARCHAR(20),       -- 'self', 'third_party', 'both'
  tehranro         BOOLEAN,           -- 테헤란로 접면 여부
  vendor_count_min INT,               -- 지주이용간판 최소 업체 수
  existing_sign_count_for_business INT,
  has_sidewalk     BOOLEAN,           -- 보도 유무 (입간판)
  exception_review_approved BOOLEAN,
  priority         INT DEFAULT 100    -- 낮을수록 먼저 체크 (불가 조건 = 1)
);

-- ─────────────────────────────────────────
-- 판정 규칙 결과
-- ─────────────────────────────────────────
CREATE TABLE rule_effect (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_id         UUID REFERENCES rule_condition(id) ON DELETE CASCADE,
  decision        VARCHAR(20) NOT NULL,  -- 'permit', 'report', 'prohibited'
  administrative_action VARCHAR(20),
  review_type     VARCHAR(50),           -- '본심의', '소심의', '서울시심의', NULL
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
  warnings        JSONB DEFAULT '[]',    -- 주의사항 목록
  provision_id    UUID REFERENCES provision(id)
);

-- ─────────────────────────────────────────
-- 업종 특례 규칙
-- ─────────────────────────────────────────
CREATE TABLE industry_exception_rule (
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

-- ─────────────────────────────────────────
-- 수량 특례 규칙
-- ─────────────────────────────────────────
CREATE TABLE sign_count_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  exception_type  VARCHAR(50),
  max_count_per_business INT NOT NULL,
  requires_no_existing_wall_sign BOOLEAN DEFAULT FALSE,
  warnings        JSONB DEFAULT '[]',
  provision_id    UUID REFERENCES provision(id),
  priority        INT DEFAULT 100
);

-- ─────────────────────────────────────────
-- 특수 구역 규칙
-- ─────────────────────────────────────────
CREATE TABLE special_zone_rule (
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

-- ─────────────────────────────────────────
-- 수수료 규칙 (PDF 수수료표 기준)
-- ─────────────────────────────────────────
CREATE TABLE fee_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  ad_type         VARCHAR(20) DEFAULT 'self',  -- 'self', 'third_party'
  area_threshold  DECIMAL(10,2) NOT NULL,      -- 기준 면적
  base_fee        INT NOT NULL,
  extra_fee       INT DEFAULT 0,               -- 초과 1㎡당
  light_weight    DECIMAL(5,2) DEFAULT 1.0,
  digital_weight  DECIMAL(5,2) DEFAULT 2.0,
  provision_id    UUID REFERENCES provision(id)
);

-- ─────────────────────────────────────────
-- 서류 체크리스트 규칙
-- ─────────────────────────────────────────
CREATE TABLE checklist_rule (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  work_type     VARCHAR(50) NOT NULL,  -- 'permit', 'report', 'change', 'extend'
  sign_type     VARCHAR(100),          -- NULL = 공통
  required_docs JSONB NOT NULL,
  optional_docs JSONB DEFAULT '[]',
  condition     TEXT
);

-- ─────────────────────────────────────────
-- 용도지역 규칙
-- ─────────────────────────────────────────
CREATE TABLE zone_rule (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name             VARCHAR(100) NOT NULL UNIQUE,
  sign_count_limit INT DEFAULT 1,              -- 업소당 허용 간판 수
  restriction      TEXT,
  prohibited_types JSONB DEFAULT '[]',
  provision_id     UUID REFERENCES provision(id)
);

-- ─────────────────────────────────────────
-- 판정 이력 로그
-- ─────────────────────────────────────────
CREATE TABLE case_log (
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

-- ─────────────────────────────────────────
-- 규칙 추출 검수용 초안 테이블
-- law_chunk -> draft_rule -> rule_condition/rule_effect
-- ─────────────────────────────────────────
CREATE TABLE draft_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_type       VARCHAR(100) NOT NULL,
  install_subtype VARCHAR(100),
  title           VARCHAR(200) NOT NULL,
  source_type     VARCHAR(50) NOT NULL,      -- 'rag', 'manual', 'import'
  source_document_id UUID REFERENCES document_master(id),
  source_provision_id UUID REFERENCES provision(id),
  source_chunk_ids JSONB DEFAULT '[]',
  summary         TEXT,
  extracted_payload JSONB DEFAULT '{}',
  condition_payload JSONB DEFAULT '{}',
  effect_payload  JSONB DEFAULT '{}',
  auxiliary_payload JSONB DEFAULT '{}',
  status          VARCHAR(30) NOT NULL DEFAULT 'draft', -- 'draft','reviewed','approved','rejected'
  reviewer_note   TEXT,
  reviewer_id     VARCHAR(100),
  approved_rule_condition_id UUID REFERENCES rule_condition(id),
  approved_rule_effect_id UUID REFERENCES rule_effect(id),
  approved_auxiliary_rule_ids JSONB DEFAULT '{}',
  reviewed_at     TIMESTAMP,
  created_at      TIMESTAMP DEFAULT NOW(),
  updated_at      TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- 법령 임베딩 청크 (pgvector RAG용)
-- embed_laws.py --init-db 로 생성됨
-- ─────────────────────────────────────────
CREATE TABLE law_chunk (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id  UUID REFERENCES document_master(id) ON DELETE CASCADE,
  provision_id UUID REFERENCES provision(id) ON DELETE CASCADE,
  content      TEXT NOT NULL,
  embedding    vector(768),   -- nomic-embed-text 차원
  chunk_index  INT DEFAULT 0,
  law_name     VARCHAR(200),  -- 빠른 검색용 비정규화
  article      VARCHAR(50),
  created_at   TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- 인덱스
-- ─────────────────────────────────────────
CREATE INDEX idx_rule_condition_sign_type ON rule_condition(sign_type);
CREATE INDEX idx_rule_condition_priority ON rule_condition(priority);
CREATE INDEX idx_industry_exception_rule_sign_type ON industry_exception_rule(sign_type, exception_type);
CREATE INDEX idx_sign_count_rule_sign_type ON sign_count_rule(sign_type, exception_type);
CREATE INDEX idx_draft_rule_sign_type_status ON draft_rule(sign_type, status, created_at DESC);
CREATE INDEX idx_special_zone_rule_sign_type ON special_zone_rule(sign_type, special_zone);
CREATE INDEX idx_fee_rule_sign_type ON fee_rule(sign_type, ad_type);
CREATE INDEX idx_case_log_created_at ON case_log(created_at DESC);
CREATE INDEX idx_provision_document ON provision(document_id);
CREATE INDEX idx_law_chunk_provision ON law_chunk(provision_id);
CREATE INDEX idx_law_chunk_document  ON law_chunk(document_id);
-- IVFFlat 벡터 인덱스는 데이터 적재 후 별도 생성 (embed_laws.py 참조)

-- ─────────────────────────────────────────
-- 초기 데이터: 용도지역
-- ─────────────────────────────────────────
INSERT INTO zone_rule (name, sign_count_limit, prohibited_types) VALUES
  ('전용주거지역', 1, '["전광류·디지털광고물", "옥상간판", "지주이용간판"]'),
  ('일반주거지역', 1, '["전광류·디지털광고물", "옥상간판"]'),
  ('준주거지역',   2, '["전광류·디지털광고물"]'),
  ('일반상업지역', 2, '[]'),
  ('근린상업지역', 2, '[]'),
  ('준공업지역',   2, '[]');

-- ─────────────────────────────────────────
-- 초기 데이터: 수수료 규칙 (PDF p.13 기준)
-- ─────────────────────────────────────────
INSERT INTO fee_rule (sign_type, ad_type, area_threshold, base_fee, extra_fee, light_weight, digital_weight) VALUES
  -- 벽면이용간판 자사
  ('벽면이용간판',      'self',        5,  4000,  1500, 1.5, 2.0),
  -- 벽면이용간판 타사
  ('벽면이용간판',      'third_party', 5,  40000, 2000, 1.5, 2.0),
  -- 돌출간판
  ('돌출간판',          'self',        5,  20000, 2000, 1.5, 2.0),
  -- 옥상간판
  ('옥상간판',          'self',        10, 40000, 6000, 1.5, 2.0),
  -- 지주이용간판
  ('지주이용간판',      'self',        10, 20000, 2000, 1.5, 2.0),
  -- 공공시설물 이용 광고물
  ('공공시설물 이용 광고물', 'self',   1,  3000,  1000, 1.5, 2.0),
  -- 교통수단 이용 광고물 (대당)
  ('교통수단 이용 광고물',   'self',   0,  2000,  0,    1.0, 2.0),
  -- 입간판 (개당)
  ('입간판',            'self',        0,  4000,  0,    1.0, 1.0);

-- ─────────────────────────────────────────
-- 초기 데이터: 공통 구비서류
-- ─────────────────────────────────────────
INSERT INTO checklist_rule (work_type, sign_type, required_docs, optional_docs) VALUES
  ('report', NULL, '["옥외광고물 표시 신청서 1부", "건물(대지) 사용승낙서 1부", "위치도(약도)", "건물전체 원색사진 및 시뮬레이션", "광고물 원색도안", "광고물 설계도", "광고물 시방서", "옥외광고 사업등록증 사본"]', '[]'),
  ('permit', NULL, '["옥외광고물 허가 신청서 1부", "건물(대지) 사용승낙서 1부", "위치도(약도)", "건물전체 원색사진 및 시뮬레이션", "광고물 원색도안", "광고물 설계도", "광고물 시방서", "옥외광고 사업등록증 사본"]', '[]');
