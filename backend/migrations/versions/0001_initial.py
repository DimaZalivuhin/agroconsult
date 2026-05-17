"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-18 09:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- Enums ----------
    user_role = postgresql.ENUM("farmer", "admin", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)

    farm_type = postgresql.ENUM(
        "kfh", "lph", "ip", "ooo", "coop", "other", name="farm_type"
    )
    farm_type.create(op.get_bind(), checkfirst=True)

    farm_direction = postgresql.ENUM(
        "crop", "livestock", "dairy", "meat", "poultry",
        "beekeeping", "aquaculture", "mixed", "other",
        name="farm_direction",
    )
    farm_direction.create(op.get_bind(), checkfirst=True)

    farmer_status = postgresql.ENUM(
        "beginning", "operating", "expanding", name="farmer_status"
    )
    farmer_status.create(op.get_bind(), checkfirst=True)

    document_type = postgresql.ENUM(
        "federal_law", "government_decree", "ministry_order",
        "regional_act", "tax_code", "methodology", "other",
        name="document_type",
    )
    document_type.create(op.get_bind(), checkfirst=True)

    document_status = postgresql.ENUM(
        "pending", "parsing", "chunking", "embedding",
        "indexed", "failed", "archived",
        name="document_status",
    )
    document_status.create(op.get_bind(), checkfirst=True)

    message_role = postgresql.ENUM(
        "user", "assistant", "system", name="message_role"
    )
    message_role.create(op.get_bind(), checkfirst=True)

    feedback_kind = postgresql.ENUM(
        "positive", "negative", "hallucination", "outdated",
        name="feedback_kind",
    )
    feedback_kind.create(op.get_bind(), checkfirst=True)

    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "role",
            postgresql.ENUM(name="user_role", create_type=False),
            nullable=False,
            server_default="farmer",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    # ---------- farmer_profiles ----------
    op.create_table(
        "farmer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region_code", sa.String(8), nullable=True),
        sa.Column("region_name", sa.String(128), nullable=True),
        sa.Column("farm_type", postgresql.ENUM(name="farm_type", create_type=False), nullable=True),
        sa.Column("direction", postgresql.ENUM(name="farm_direction", create_type=False), nullable=True),
        sa.Column("status", postgresql.ENUM(name="farmer_status", create_type=False), nullable=True),
        sa.Column("okved", sa.String(16), nullable=True),
        sa.Column("years_in_business", sa.Integer(), nullable=True),
        sa.Column("inn", sa.String(12), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_farmer_profiles"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_farmer_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", name="uq_farmer_profiles_user_id"),
    )
    op.create_index("ix_farmer_profiles_region_code", "farmer_profiles", ["region_code"])

    # ---------- legal_documents ----------
    op.create_table(
        "legal_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(1024), nullable=False),
        sa.Column("short_title", sa.String(512), nullable=True),
        sa.Column("doc_type", postgresql.ENUM(name="document_type", create_type=False), nullable=False),
        sa.Column("doc_number", sa.String(64), nullable=True),
        sa.Column("doc_date", sa.Date(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("issuing_body", sa.String(255), nullable=True),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("target_regions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("target_farm_types", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("target_directions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="document_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_legal_documents"),
        sa.UniqueConstraint("doc_number", "doc_date", name="uq_doc_number_date"),
    )
    op.create_index("ix_legal_documents_doc_number", "legal_documents", ["doc_number"])
    op.create_index("ix_legal_documents_status", "legal_documents", ["status"])
    op.create_index("ix_legal_documents_is_active", "legal_documents", ["is_active"])

    # ---------- document_chunks ----------
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("section_path", sa.String(512), nullable=True),
        sa.Column("meta", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_document_chunks"),
        sa.ForeignKeyConstraint(
            ["document_id"], ["legal_documents.id"],
            name="fk_document_chunks_document_id_legal_documents",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])

    # ---------- chat_sessions ----------
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False, server_default="Новая консультация"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chat_sessions"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_chat_sessions_user_id_users",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    # ---------- chat_messages ----------
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", postgresql.ENUM(name="message_role", create_type=False), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("retrieval_meta", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("token_usage", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chat_messages"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.id"],
            name="fk_chat_messages_session_id_chat_sessions",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    # ---------- feedbacks ----------
    op.create_table(
        "feedbacks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", postgresql.ENUM(name="feedback_kind", create_type=False), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_feedbacks"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_feedbacks_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"], ["chat_messages.id"],
            name="fk_feedbacks_message_id_chat_messages",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_feedbacks_user_id", "feedbacks", ["user_id"])
    op.create_index("ix_feedbacks_message_id", "feedbacks", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_feedbacks_message_id", table_name="feedbacks")
    op.drop_index("ix_feedbacks_user_id", table_name="feedbacks")
    op.drop_table("feedbacks")

    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_legal_documents_is_active", table_name="legal_documents")
    op.drop_index("ix_legal_documents_status", table_name="legal_documents")
    op.drop_index("ix_legal_documents_doc_number", table_name="legal_documents")
    op.drop_table("legal_documents")

    op.drop_index("ix_farmer_profiles_region_code", table_name="farmer_profiles")
    op.drop_table("farmer_profiles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    for enum_name in (
        "feedback_kind", "message_role", "document_status", "document_type",
        "farmer_status", "farm_direction", "farm_type", "user_role",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
