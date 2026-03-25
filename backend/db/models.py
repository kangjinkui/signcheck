from sqlalchemy import Column, String, Integer, Boolean, Numeric, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
import uuid


class Base(DeclarativeBase):
    pass


class DocumentMaster(Base):
    __tablename__ = "document_master"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name           = Column(String(200), nullable=False)
    type           = Column(String(50))
    jurisdiction   = Column(String(50))
    effective_date = Column(String(20))
    version        = Column(String(20))
    source_type    = Column(String(20))
    file_url       = Column(Text)
    created_at     = Column(DateTime, server_default=func.now())

    provisions     = relationship("Provision", back_populates="document")


class Provision(Base):
    __tablename__ = "provision"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id    = Column(UUID(as_uuid=True), ForeignKey("document_master.id", ondelete="CASCADE"))
    article        = Column(String(50))
    paragraph      = Column(String(50))
    item           = Column(String(50))
    content        = Column(Text, nullable=False)
    effective_date = Column(String(20))

    document       = relationship("DocumentMaster", back_populates="provisions")


class RuleCondition(Base):
    __tablename__ = "rule_condition"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sign_type        = Column(String(100), nullable=False)
    install_subtype  = Column(String(100))
    business_category = Column(String(100))
    install_location_type = Column(String(100))
    floor_min        = Column(Integer)
    floor_max        = Column(Integer)
    light_type       = Column(String(50))
    digital          = Column(Boolean, default=False)
    area_min         = Column(Numeric(10, 2))
    area_max         = Column(Numeric(10, 2))
    zone             = Column(String(100))
    special_zone     = Column(String(100))
    ad_type          = Column(String(20))
    tehranro         = Column(Boolean)
    vendor_count_min = Column(Integer)
    existing_sign_count_for_business = Column(Integer)
    has_sidewalk     = Column(Boolean)
    exception_review_approved = Column(Boolean)
    priority         = Column(Integer, default=100)

    effect           = relationship("RuleEffect", back_populates="condition", uselist=False)


class RuleEffect(Base):
    __tablename__ = "rule_effect"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id        = Column(UUID(as_uuid=True), ForeignKey("rule_condition.id", ondelete="CASCADE"))
    decision       = Column(String(20), nullable=False)
    administrative_action = Column(String(20))
    review_type    = Column(String(50))
    safety_check   = Column(Boolean, default=False)
    max_area       = Column(Numeric(10, 2))
    max_height     = Column(Numeric(10, 2))
    max_protrusion = Column(Numeric(10, 2))
    max_width      = Column(Numeric(10, 2))
    max_thickness  = Column(Numeric(10, 2))
    min_bottom_clearance = Column(Numeric(10, 2))
    min_bottom_clearance_no_sidewalk = Column(Numeric(10, 2))
    max_top_height_relative_building = Column(Numeric(10, 2))
    max_top_height_from_ground = Column(Numeric(10, 2))
    max_count_per_business = Column(Integer)
    requires_no_existing_wall_sign = Column(Boolean, default=False)
    requires_alignment = Column(Boolean, default=False)
    safety_check_min_height = Column(Numeric(10, 2))
    safety_check_min_area = Column(Numeric(10, 2))
    display_period = Column(String(20))
    warnings       = Column(JSON, default=list)
    provision_id   = Column(UUID(as_uuid=True), ForeignKey("provision.id"))

    condition      = relationship("RuleCondition", back_populates="effect")
    provision      = relationship("Provision")


class IndustryExceptionRule(Base):
    __tablename__ = "industry_exception_rule"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sign_type      = Column(String(100), nullable=False)
    exception_type = Column(String(50), nullable=False)
    max_height     = Column(Numeric(10, 2))
    max_protrusion = Column(Numeric(10, 2))
    max_thickness  = Column(Numeric(10, 2))
    review_type    = Column(String(50))
    warnings       = Column(JSON, default=list)
    provision_id   = Column(UUID(as_uuid=True), ForeignKey("provision.id"))
    priority       = Column(Integer, default=100)

    provision      = relationship("Provision")


class SignCountRule(Base):
    __tablename__ = "sign_count_rule"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sign_type      = Column(String(100), nullable=False)
    exception_type = Column(String(50))
    max_count_per_business = Column(Integer, nullable=False)
    requires_no_existing_wall_sign = Column(Boolean, default=False)
    warnings       = Column(JSON, default=list)
    provision_id   = Column(UUID(as_uuid=True), ForeignKey("provision.id"))
    priority       = Column(Integer, default=100)

    provision      = relationship("Provision")


class SpecialZoneRule(Base):
    __tablename__ = "special_zone_rule"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sign_type      = Column(String(100), nullable=False)
    special_zone   = Column(String(100), nullable=False)
    decision       = Column(String(20), nullable=False)
    administrative_action = Column(String(20))
    review_type    = Column(String(50))
    warnings       = Column(JSON, default=list)
    provision_id   = Column(UUID(as_uuid=True), ForeignKey("provision.id"))
    priority       = Column(Integer, default=100)

    provision      = relationship("Provision")


class FeeRule(Base):
    __tablename__ = "fee_rule"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sign_type       = Column(String(100), nullable=False)
    ad_type         = Column(String(20), default="self")
    area_threshold  = Column(Numeric(10, 2), nullable=False)
    base_fee        = Column(Integer, nullable=False)
    extra_fee       = Column(Integer, default=0)
    light_weight    = Column(Numeric(5, 2), default=1.0)
    digital_weight  = Column(Numeric(5, 2), default=2.0)
    provision_id    = Column(UUID(as_uuid=True), ForeignKey("provision.id"))


class ChecklistRule(Base):
    __tablename__ = "checklist_rule"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_type     = Column(String(50), nullable=False)
    sign_type     = Column(String(100))
    required_docs = Column(JSON, nullable=False)
    optional_docs = Column(JSON, default=list)
    condition     = Column(Text)


class ZoneRule(Base):
    __tablename__ = "zone_rule"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name             = Column(String(100), nullable=False, unique=True)
    sign_count_limit = Column(Integer, default=1)
    restriction      = Column(Text)
    prohibited_types = Column(JSON, default=list)
    provision_id     = Column(UUID(as_uuid=True), ForeignKey("provision.id"))


class CaseLog(Base):
    __tablename__ = "case_log"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    input_data      = Column(JSON, nullable=False)
    output_data     = Column(JSON, nullable=False)
    rule_version    = Column(String(20))
    decision        = Column(String(20))
    fee_calculated  = Column(Integer)
    rag_chunks_used = Column(JSON, default=list)
    user_id         = Column(String(100))
    created_at      = Column(DateTime, server_default=func.now())


class DraftRule(Base):
    __tablename__ = "draft_rule"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sign_type       = Column(String(100), nullable=False)
    install_subtype = Column(String(100))
    title           = Column(String(200), nullable=False)
    source_type     = Column(String(50), nullable=False)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("document_master.id"))
    source_provision_id = Column(UUID(as_uuid=True), ForeignKey("provision.id"))
    source_chunk_ids = Column(JSON, default=list)
    summary         = Column(Text)
    extracted_payload = Column(JSON, default=dict)
    condition_payload = Column(JSON, default=dict)
    effect_payload  = Column(JSON, default=dict)
    auxiliary_payload = Column(JSON, default=dict)
    status          = Column(String(30), nullable=False, default="draft")
    reviewer_note   = Column(Text)
    reviewer_id     = Column(String(100))
    approved_rule_condition_id = Column(UUID(as_uuid=True), ForeignKey("rule_condition.id"))
    approved_rule_effect_id = Column(UUID(as_uuid=True), ForeignKey("rule_effect.id"))
    approved_auxiliary_rule_ids = Column(JSON, default=dict)
    reviewed_at     = Column(DateTime)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    source_document = relationship("DocumentMaster")
    source_provision = relationship("Provision", foreign_keys=[source_provision_id])
    approved_condition = relationship("RuleCondition", foreign_keys=[approved_rule_condition_id])
    approved_effect = relationship("RuleEffect", foreign_keys=[approved_rule_effect_id])
