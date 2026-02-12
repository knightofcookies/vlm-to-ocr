"""Staging process for adding items to the pipeline manifest."""

import logging
import sys

import internetarchive as ia
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from db import (
    Manifest,
    ensure_schema_migrated,
    get_engine,
    get_language_code,
    get_session_factory,
    session_scope,
)

# Valid document types
VALID_DOC_TYPES = {"printed", "handwritten", "scene-text"}

load_dotenv()

# --- Configuration ---
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(console=console, rich_tracebacks=True, show_path=False),
    ],
)


def stage_by_full_text(query: str, language: str, doc_type: str):
    """Stage items from Internet Archive based on search query."""
    # Validate doc_type
    if doc_type not in VALID_DOC_TYPES:
        raise ValueError(
            f"Invalid doc_type: {doc_type}. Must be one of {', '.join(sorted(VALID_DOC_TYPES))}"
        )

    ensure_schema_migrated({"manifest", "alembic_version"})

    engine = get_engine()
    session_factory = get_session_factory(engine)

    search_query = query
    if "mediatype:texts" not in query:
        search_query = f"{query} mediatype:texts"

    sarvam_code = get_language_code(language)
    logging.info(f"Searching: '{search_query}' (Language: {language} -> {sarvam_code})")

    search = ia.search_items(search_query, fields=["identifier", "language"])

    staged_count = 0
    with session_scope(session_factory) as session:
        for item in search:
            ident = item["identifier"]
            raw_lang = item.get("language")

            existing = session.query(Manifest).filter_by(identifier=ident).first()
            if existing:
                # Update metadata if needed, but don't re-stage if already queued/processing
                if existing.status == "failed":
                    existing.status = "queued"
                continue

            manifest = Manifest(
                identifier=ident,
                language=str(raw_lang),
                doc_type=doc_type,
                sarvam_lang_code=sarvam_code,
                query_language=language,
                status="queued",
            )
            session.add(manifest)
            staged_count += 1

    logging.info(f"Staged {staged_count} items.")


def run_staging():
    """Main entry point for staging script."""
    try:
        # Validate doc_type before processing
        doc_type = sys.argv[3]
        if doc_type not in VALID_DOC_TYPES:
            logging.error(
                f"Invalid doc_type: {doc_type}. Must be one of {', '.join(sorted(VALID_DOC_TYPES))}"
            )
            sys.exit(1)

        stage_by_full_text(
            query=sys.argv[1],
            language=sys.argv[2],
            doc_type=doc_type,
        )
        logging.info("Staging completed.")
    except Exception as e:
        logging.error(f"Staging error: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        logging.error(
            "Usage: python staging.py <archive.org-style query> <language> <doc_type>"
        )
        logging.error(f"Valid doc_types: {', '.join(sorted(VALID_DOC_TYPES))}")
        sys.exit(1)
    run_staging()
