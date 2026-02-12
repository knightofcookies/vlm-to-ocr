"""Shared database infrastructure for the data pipeline."""

import os
import sqlite3
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker

load_dotenv()

# --- Configuration ---
DB_PATH = os.environ.get("DB_PATH", "pipeline.db")

# --- SQLAlchemy Setup ---
Base = declarative_base()


class Manifest(Base):
    __tablename__ = "manifest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String, unique=True, nullable=False)
    language = Column(Text)
    doc_type = Column(String)  # 'printed', 'handwritten', or 'scene-text'
    download_date = Column(DateTime)
    sarvam_lang_code = Column(Text)
    query_language = Column(Text)
    status = Column(String, default="queued")
    error_message = Column(Text)
    last_updated = Column(DateTime, default=func.current_timestamp())

    # Relationships
    documents = relationship("Document", back_populates="manifest")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manifest_id = Column(Integer, ForeignKey("manifest.id"), nullable=False)
    original_filename = Column(Text, nullable=False)
    status = Column(
        String, default="pending"
    )  # pending, downloaded, processing, completed, partial_success, failed
    error_message = Column(Text)
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    manifest = relationship("Manifest", back_populates="documents")
    batches = relationship("OcrBatch", back_populates="document")


class OcrBatch(Base):
    __tablename__ = "ocr_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    sarvam_job_id = Column(Text, unique=True, nullable=True)
    status = Column(
        String, default="pending"
    )  # pending, polling, completed, partial_success, failed
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    page_count = Column(Integer, default=0)
    failed_pages = Column(Text)
    output_dir = Column(Text)
    zip_size_bytes = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime)

    # Relationships
    document = relationship("Document", back_populates="batches")


def get_language_code(language_name: str) -> str:
    """Directly maps a language name to its Sarvam BCP-47 code."""
    mapping = {
        "assamese": "as-IN",
        "bengali": "bn-IN",
        "bodo": "bodo-IN",  # API spec uses bodo-IN, overview says brx-IN
        "dogri": "doi-IN",
        "gujarati": "gu-IN",
        "hindi": "hi-IN",
        "kannada": "kn-IN",
        "kashmiri": "ks-IN",
        "konkani": "kok-IN",
        "maithili": "mai-IN",
        "malayalam": "ml-IN",
        "manipuri": "mni-IN",
        "marathi": "mr-IN",
        "nepali": "ne-IN",
        "odia": "or-IN",  # API spec uses or-IN, overview says od-IN
        "punjabi": "pa-IN",
        "sanskrit": "sa-IN",
        "santali": "sat-IN",
        "sindhi": "sd-IN",
        "tamil": "ta-IN",
        "telugu": "te-IN",
        "urdu": "ur-IN",
        "english": "en-IN",
    }
    return mapping.get(language_name.lower().strip(), "hi-IN")


def get_engine():
    """Returns a SQLAlchemy engine for the database."""
    return create_engine(f"sqlite:///{DB_PATH}")


def get_session_factory(engine):
    """Returns a scoped session factory."""
    return scoped_session(sessionmaker(bind=engine))


def ensure_schema_migrated(required_tables):
    """Validate required tables exist; fail with migration guidance if not."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

    missing = sorted(set(required_tables) - existing_tables)
    if missing:
        raise RuntimeError(
            "Database schema is missing required tables: "
            f"{', '.join(missing)}. Run `alembic upgrade head` first."
        )


@contextmanager
def session_scope(session_factory):
    """Provide a transactional scope around a series of operations."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session_factory.remove()  # Return connection to pool
