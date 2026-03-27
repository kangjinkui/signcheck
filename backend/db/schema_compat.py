from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from db.models import Base


COMPATIBILITY_SQL = (
    'CREATE EXTENSION IF NOT EXISTS vector',
    'CREATE EXTENSION IF NOT EXISTS "pgcrypto"',
    """
    ALTER TABLE rule_condition
      ADD COLUMN IF NOT EXISTS install_subtype VARCHAR(100),
      ADD COLUMN IF NOT EXISTS business_category VARCHAR(100),
      ADD COLUMN IF NOT EXISTS install_location_type VARCHAR(100),
      ADD COLUMN IF NOT EXISTS special_zone VARCHAR(100),
      ADD COLUMN IF NOT EXISTS existing_sign_count_for_business INT,
      ADD COLUMN IF NOT EXISTS has_sidewalk BOOLEAN,
      ADD COLUMN IF NOT EXISTS exception_review_approved BOOLEAN,
      ADD COLUMN IF NOT EXISTS priority INT DEFAULT 100;
    """,
    """
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
      ADD COLUMN IF NOT EXISTS safety_check_min_area DECIMAL(10,2),
      ADD COLUMN IF NOT EXISTS warnings JSONB DEFAULT '[]';
    """,
    """
    CREATE TABLE IF NOT EXISTS industry_exception_rule (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      sign_type VARCHAR(100) NOT NULL,
      exception_type VARCHAR(50) NOT NULL,
      max_height DECIMAL(10,2),
      max_protrusion DECIMAL(10,2),
      max_thickness DECIMAL(10,2),
      review_type VARCHAR(50),
      warnings JSONB DEFAULT '[]',
      provision_id UUID REFERENCES provision(id),
      priority INT DEFAULT 100
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sign_count_rule (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      sign_type VARCHAR(100) NOT NULL,
      exception_type VARCHAR(50),
      max_count_per_business INT NOT NULL,
      requires_no_existing_wall_sign BOOLEAN DEFAULT FALSE,
      warnings JSONB DEFAULT '[]',
      provision_id UUID REFERENCES provision(id),
      priority INT DEFAULT 100
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS special_zone_rule (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      sign_type VARCHAR(100) NOT NULL,
      special_zone VARCHAR(100) NOT NULL,
      decision VARCHAR(20) NOT NULL,
      administrative_action VARCHAR(20),
      review_type VARCHAR(50),
      warnings JSONB DEFAULT '[]',
      provision_id UUID REFERENCES provision(id),
      priority INT DEFAULT 100
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS draft_rule (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      sign_type VARCHAR(100) NOT NULL,
      install_subtype VARCHAR(100),
      title VARCHAR(200) NOT NULL,
      source_type VARCHAR(50) NOT NULL,
      source_document_id UUID REFERENCES document_master(id),
      source_provision_id UUID REFERENCES provision(id),
      source_chunk_ids JSONB DEFAULT '[]',
      summary TEXT,
      extracted_payload JSONB DEFAULT '{}',
      condition_payload JSONB DEFAULT '{}',
      effect_payload JSONB DEFAULT '{}',
      auxiliary_payload JSONB DEFAULT '{}',
      status VARCHAR(30) NOT NULL DEFAULT 'draft',
      reviewer_note TEXT,
      reviewer_id VARCHAR(100),
      approved_rule_condition_id UUID REFERENCES rule_condition(id),
      approved_rule_effect_id UUID REFERENCES rule_effect(id),
      approved_auxiliary_rule_ids JSONB DEFAULT '{}',
      reviewed_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    ALTER TABLE draft_rule
      ADD COLUMN IF NOT EXISTS auxiliary_payload JSONB DEFAULT '{}',
      ADD COLUMN IF NOT EXISTS approved_auxiliary_rule_ids JSONB DEFAULT '{}';
    """,
)


async def ensure_schema_compatibility(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for statement in COMPATIBILITY_SQL:
            await conn.execute(text(statement))
