import os
import logging
import time
import zipfile
import shutil
import math
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import internetarchive as ia
from pypdf import PdfReader, PdfWriter
from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship
from sqlalchemy.sql import func

load_dotenv()

# --- CONFIGURATION ---
DB_PATH = os.getenv("DB_PATH", "manifest.sqlite")
DATA_ROOT = os.getenv("DATA_ROOT", "./data")
LOG_FILE = os.getenv("LOG_FILE", "pipeline.log")

# Concurrency & Limits
MAX_DOWNLOAD_WORKERS = 4
MAX_OCR_SUBMITTERS = 5
SARVAM_PAGE_LIMIT = (
    250  # Conservative safety buffer (API limit is 500, but 480 causes failures)
)
SARVAM_SIZE_LIMIT_BYTES = 100 * 1024 * 1024  # 100MB Safety buffer (Limit is 200MB)
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# ---------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)

# Suppress verbose logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("pypdf").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# --- SQLAlchemy Models ---
Base = declarative_base()


class Manifest(Base):
    __tablename__ = "manifest"

    identifier = Column(String, primary_key=True)
    language = Column(Text)
    sarvam_lang_code = Column(Text)
    status = Column(String, default="queued")
    local_path = Column(Text)
    error_message = Column(Text)
    last_updated = Column(DateTime, default=func.current_timestamp())

    # Relationship
    ocr_queue_items = relationship("OcrQueue", back_populates="manifest")


class OcrQueue(Base):
    __tablename__ = "ocr_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String, ForeignKey("manifest.identifier"), nullable=False)
    file_name = Column(Text, nullable=False)
    original_filename = Column(Text)  # Original PDF name before splitting
    page_start = Column(Integer)  # First page in this split (1-indexed)
    page_end = Column(Integer)  # Last page in this split (inclusive)
    status = Column(String, default="pending")  # pending, polling, completed, failed
    sarvam_job_id = Column(Text)
    page_count = Column(Integer)
    ocr_output_path = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime)

    # Relationship
    manifest = relationship("Manifest", back_populates="ocr_queue_items")


def get_language_code(ia_lang, preferred_lang=None):
    """Maps IA language metadata to Sarvam BCP-47 codes.

    If preferred_lang is provided, it returns the code only if it's among the IA metadata languages.
    Otherwise, returns None.
    """
    mapping = {
        "assamese": "as-IN",
        "asm": "as-IN",
        "bengali": "bn-IN",
        "ben": "bn-IN",
        "gujarati": "gu-IN",
        "guj": "gu-IN",
        "hindi": "hi-IN",
        "hin": "hi-IN",
        "kannada": "kn-IN",
        "kan": "kn-IN",
        "malayalam": "ml-IN",
        "mal": "ml-IN",
        "marathi": "mr-IN",
        "mar": "mr-IN",
        "odia": "or-IN",
        "ori": "or-IN",
        "punjabi": "pa-IN",
        "pan": "pa-IN",
        "tamil": "ta-IN",
        "tam": "ta-IN",
        "telugu": "te-IN",
        "tel": "te-IN",
        "urdu": "ur-IN",
        "urd": "ur-IN",
        "sanskrit": "sa-IN",
        "san": "sa-IN",
        "nepali": "ne-IN",
        "nep": "ne-IN",
        "konkani": "kok-IN",
        "kok": "kok-IN",
        "maithili": "mai-IN",
        "mai": "mai-IN",
        "sindhi": "sd-IN",
        "snd": "sd-IN",
        "kashmiri": "ks-IN",
        "kas": "ks-IN",
        "dogri": "doi-IN",
        "doi": "doi-IN",
        "manipuri": "mni-IN",
        "mni": "mni-IN",
        "bodo": "bodo-IN",
        "bod": "bodo-IN",
        "santali": "sat-IN",
        "sat": "sat-IN",
        "english": "en-IN",
        "eng": "en-IN",
    }

    if not ia_lang or not preferred_lang:
        return None

    # Clean up the string: remove brackets, quotes, and convert to lowercase
    cleaned = (
        str(ia_lang)
        .lower()
        .replace("[", "")
        .replace("]", "")
        .replace("'", "")
        .replace('"', "")
    )
    langs = [l.strip() for l in cleaned.replace(";", ",").split(",")]

    preferred_lang = preferred_lang.lower().strip()

    # If preferred_lang isn't in our mapping at all, we can't do anything
    if preferred_lang not in mapping:
        return None

    target_sarvam_code = mapping[preferred_lang]

    # Check if ANY of the languages in the metadata map to the same Sarvam code
    for l in langs:
        if l in mapping and mapping[l] == target_sarvam_code:
            return target_sarvam_code

    return None


class ArchivePipeline:
    def __init__(self):
        # Set up SQLAlchemy engine and session
        self.engine = create_engine(
            f"sqlite:///{DB_PATH}",
            connect_args={"timeout": 30.0},
            pool_pre_ping=True,
        )

        # Enable WAL mode
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        # Create scoped session for thread-safety
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)

        self.init_db()
        self.reset_stalled_jobs()
        os.makedirs(DATA_ROOT, exist_ok=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Disposes the engine and removes the session."""
        try:
            self.Session.remove()
            self.engine.dispose()
            logging.info("Pipeline resources released.")
        except Exception as e:
            logging.error(f"Error during resource cleanup: {e}")

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            self.Session.remove()  # Crucial: return connection to pool

    def init_db(self):
        """Create all tables using SQLAlchemy models."""
        Base.metadata.create_all(self.engine)
        logging.info("Database initialized.")

    def reset_stalled_jobs(self):
        """Resets jobs stuck in 'downloading' or 'processing' state from previous crashes."""
        with self.session_scope() as session:
            session.query(Manifest).filter(Manifest.status == "processing").update(
                {"status": "queued"}
            )
            # Optional: Reset stalled OCR jobs if needed, but safer to leave them for manual review
            logging.info("Pipeline state synchronized.")

    def _get_shard_path(self, identifier):
        """Returns the data directory for an identifier."""
        return os.path.join(DATA_ROOT, identifier)

    # --- PHASE 1: STAGING ---
    def stage_by_keywords(self, target_lang, keywords, limit=1000):
        logging.info(f"Staging items for {target_lang}...")
        queries = [f"language:({target_lang}) AND mediatype:(texts)"] + [
            f"title:({w}) AND mediatype:(texts)" for w in keywords
        ]

        count = 0
        with self.session_scope() as session:
            for query in queries:
                try:
                    search = ia.search_items(query, fields=["identifier", "language"])
                    for result in search:
                        if count >= limit:
                            break

                        ident = result["identifier"]
                        raw_lang = result.get("language", "")

                        # Check if exists
                        existing = (
                            session.query(Manifest).filter_by(identifier=ident).first()
                        )
                        if existing:
                            existing.language = str(raw_lang)
                            if existing.status == "failed":
                                existing.status = "queued"
                        else:
                            new_item = Manifest(
                                identifier=ident,
                                language=str(raw_lang),
                                sarvam_lang_code=get_language_code(
                                    raw_lang, target_lang
                                ),
                                status="queued",
                            )
                            session.add(new_item)

                        count += 1
                        if count % 100 == 0:
                            session.commit()
                except Exception as e:
                    logging.error(f"Search error: {e}")
            session.commit()
        logging.info(f"Staged {count} items.")

    # --- PHASE 2: DOWNLOADING & SPLITTING ---
    def run_downloader(self, limit=100):
        with self.session_scope() as session:
            tasks = (
                session.query(Manifest.identifier)
                .filter(Manifest.status == "queued")
                .limit(limit)
                .all()
            )

        if not tasks:
            return

        logging.info(f"Downloading {len(tasks)} items...")
        with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as executor:
            for task in tasks:
                executor.submit(self._download_task, task.identifier)

    def _split_pdf(self, file_path, splits_dir):
        """Splits PDF into chunks satisfying Sarvam API limits (Pages & Size).

        Returns list of tuples: (split_path, page_start, page_end)
        """
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            parts = []

            # If small enough, no split needed
            file_size = os.path.getsize(file_path)
            if total_pages <= SARVAM_PAGE_LIMIT and file_size < SARVAM_SIZE_LIMIT_BYTES:
                return [(file_path, 1, total_pages)]

            # Create splits directory
            os.makedirs(splits_dir, exist_ok=True)

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            start = 0
            part_num = 1

            while start < total_pages:
                # 1. Try max allowed pages
                end = min(start + SARVAM_PAGE_LIMIT, total_pages)

                # 2. Check size constraints
                while end > start:
                    writer = PdfWriter()
                    for page in reader.pages[start:end]:
                        writer.add_page(page)

                    temp_filename = os.path.join(splits_dir, f"{base_name}.temp")
                    with open(temp_filename, "wb") as f:
                        writer.write(f)

                    file_size = os.path.getsize(temp_filename)

                    if file_size < SARVAM_SIZE_LIMIT_BYTES:
                        # Success: Rename and save
                        final_name = os.path.join(
                            splits_dir, f"{base_name}_{part_num:03d}.pdf"
                        )
                        os.rename(temp_filename, final_name)
                        parts.append((final_name, start + 1, end))  # 1-indexed pages

                        part_num += 1
                        start = end
                        break
                    else:
                        # Fail: File too big, reduce page count by half and retry
                        os.remove(temp_filename)
                        step = end - start
                        if step <= 1:
                            logging.error(
                                f"Single page {start + 1} exceeds size limit! Skipping."
                            )
                            start += 1
                            break

                        end = start + (step // 2)

            return parts

        except Exception as e:
            logging.error(f"Failed to split PDF {file_path}: {e}")
            return []

    def _download_task(self, identifier):
        dest_dir = self._get_shard_path(identifier)

        try:
            with self.session_scope() as session:
                manifest = (
                    session.query(Manifest).filter_by(identifier=identifier).first()
                )
                if manifest:
                    manifest.status = "processing"
                session.commit()

            # Download to identifier directory
            ia.get_item(identifier).download(
                glob_pattern="*.pdf",
                destdir=dest_dir,
                no_directory=True,  # Don't create nested identifier folder
                verbose=False,
                ignore_existing=True,
            )

            if not os.path.exists(dest_dir):
                raise FileNotFoundError("No directory created")

            files = [f for f in os.listdir(dest_dir) if f.lower().endswith(".pdf")]
            if not files:
                raise FileNotFoundError("No PDFs found in item")

            # Process each downloaded PDF
            with self.session_scope() as session:
                manifest = (
                    session.query(Manifest).filter_by(identifier=identifier).first()
                )
                if manifest:
                    manifest.status = "downloaded"
                    manifest.local_path = dest_dir

                for original_file in files:
                    original_path = os.path.join(dest_dir, original_file)
                    splits_dir = os.path.join(dest_dir, ".splits")

                    # Check if already processed (OCR queue entries exist)
                    existing = (
                        session.query(OcrQueue)
                        .filter_by(
                            identifier=identifier, original_filename=original_file
                        )
                        .first()
                    )

                    if existing:
                        logging.info(
                            f"Skipping already processed file: {original_file}"
                        )
                        continue

                    # Split the PDF (or return original if small enough)
                    split_results = self._split_pdf(original_path, splits_dir)

                    if not split_results:
                        logging.error(f"Failed to split {original_file}")
                        continue

                    # Add OCR queue entries for each split
                    for split_path, page_start, page_end in split_results:
                        split_filename = os.path.basename(split_path)

                        ocr_item = OcrQueue(
                            identifier=identifier,
                            file_name=split_filename,
                            original_filename=original_file,
                            page_start=page_start,
                            page_end=page_end,
                            status="pending",
                        )
                        session.add(ocr_item)

                    logging.info(
                        f"Processed {original_file}: {len(split_results)} split(s)"
                    )

        except Exception as e:
            logging.error(f"Download failed for {identifier}: {e}")
            with self.session_scope() as session:
                manifest = (
                    session.query(Manifest).filter_by(identifier=identifier).first()
                )
                if manifest:
                    manifest.status = "failed"
                    manifest.error_message = str(e)

    # --- PHASE 3: OCR SUBMISSION (ASYNC) ---
    def run_ocr_submitter(self, limit=50):
        if not SARVAM_API_KEY:
            logging.error("No API Key.")
            return

        client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

        with self.session_scope() as session:
            tasks = (
                session.query(
                    OcrQueue.id,
                    OcrQueue.identifier,
                    OcrQueue.file_name,
                    Manifest.local_path,
                    Manifest.sarvam_lang_code,
                )
                .join(Manifest, OcrQueue.identifier == Manifest.identifier)
                .filter(OcrQueue.status == "pending")
                .limit(limit)
                .all()
            )

        if not tasks:
            return
        logging.info(f"Submitting {len(tasks)} files to Sarvam...")

        with ThreadPoolExecutor(max_workers=MAX_OCR_SUBMITTERS) as executor:
            for task in tasks:
                executor.submit(self._submit_task, client, task)

    def _submit_task(self, client, task):
        queue_id, identifier, fname, local_path, lang_code = task
        fpath = os.path.join(local_path, fname)

        # Check if file is in .splits/ subdirectory
        if not os.path.exists(fpath):
            fpath = os.path.join(local_path, ".splits", fname)

        try:
            if not os.path.exists(fpath):
                raise FileNotFoundError(f"File missing: {fpath}")

            job = client.document_intelligence.create_job(
                language=lang_code, output_format="md"
            )
            job.upload_file(fpath)
            job.start()

            with self.session_scope() as session:
                ocr_item = session.query(OcrQueue).filter_by(id=queue_id).first()
                if ocr_item:
                    ocr_item.status = "polling"
                    ocr_item.sarvam_job_id = job.job_id
                    ocr_item.updated_at = datetime.now()

            logging.info(f"Submitted {identifier}/{fname} -> Job {job.job_id}")

        except ApiError as e:
            self._handle_api_error(queue_id, e)
        except Exception as e:
            self._mark_failed(queue_id, str(e))

    # --- PHASE 4: OCR POLLING (ASYNC) ---
    def run_ocr_poller(self):
        """Checks status of jobs that are already running."""
        client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

        with self.session_scope() as session:
            jobs = (
                session.query(
                    OcrQueue.id,
                    OcrQueue.identifier,
                    OcrQueue.file_name,
                    OcrQueue.sarvam_job_id,
                    Manifest.local_path,
                )
                .join(Manifest, OcrQueue.identifier == Manifest.identifier)
                .filter(OcrQueue.status == "polling")
                .limit(20)
                .all()
            )

        if not jobs:
            return

        for job_row in jobs:
            try:
                status = client.document_intelligence.get_status(
                    job_id=job_row.sarvam_job_id
                )
                state = status.job_state

                # Handle both Completed and PartiallyCompleted
                if state == "Completed" or state == "PartiallyCompleted":
                    if state == "PartiallyCompleted":
                        logging.warning(
                            f"Job {job_row.id} finished with partial errors."
                        )
                    self._finalize_job(client, job_row)

                elif state == "Failed":
                    self._mark_failed(
                        job_row.id, f"Sarvam Job Failed: {status.error_message}"
                    )

                # Else: Still Running/Pending - do nothing

            except Exception as e:
                logging.error(f"Polling error for {job_row.identifier}: {e}")

    def _finalize_job(self, client, job_row):
        """Downloads, unzips, merges, and organizes completed OCR job."""
        queue_id = job_row.id
        local_path = job_row.local_path
        sarvam_job_id = job_row.sarvam_job_id

        # Temporary directory for this specific job
        temp_dir = os.path.join(local_path, ".ocr_temp", f"job_{queue_id}")
        os.makedirs(temp_dir, exist_ok=True)
        zip_path = os.path.join(temp_dir, "output.zip")

        try:
            # 1. Get Download Links
            links = client.document_intelligence.get_download_links(
                job_id=sarvam_job_id
            )

            # Check for API-level errors (e.g., NO_OUTPUT_AVAILABLE)
            if hasattr(links, "error_code") and links.error_code:
                # Handle NO_OUTPUT_AVAILABLE gracefully - some PDFs can't be processed
                if links.error_code == "NO_OUTPUT_AVAILABLE":
                    logging.warning(
                        f"Job {queue_id} completed but produced no output. "
                        f"PDF may be unprocessable by Sarvam API."
                    )
                    # Mark as completed with no output
                    with self.session_scope() as session:
                        ocr_item = (
                            session.query(OcrQueue).filter_by(id=queue_id).first()
                        )
                        if ocr_item:
                            ocr_item.status = "completed"
                            ocr_item.ocr_output_path = None
                            ocr_item.error_message = "NO_OUTPUT_AVAILABLE"
                    return
                else:
                    # Other errors are still fatal
                    error_msg = f"Sarvam API Error: {links.error_code}"
                    if hasattr(links, "error_message") and links.error_message:
                        error_msg += f" - {links.error_message}"
                    raise ValueError(error_msg)

            download_url = None
            # Robustly find URL by checking extensions, not just keys
            if hasattr(links, "download_urls") and links.download_urls:
                for key, details in links.download_urls.items():
                    if details.file_url.split("?")[0].endswith(".zip"):
                        download_url = details.file_url
                        break

                # Fallback: if only 1 item, take it
                if not download_url and len(links.download_urls) == 1:
                    download_url = list(links.download_urls.values())[0].file_url

            if not download_url:
                raise ValueError("No ZIP download URL found in response")

            # 2. Download
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # 3. Extract
            with zipfile.ZipFile(zip_path, "r") as z:
                # Basic security check
                for member in z.namelist():
                    if ".." in member or member.startswith("/"):
                        logging.warning(f"Skipping suspicious file: {member}")
                        continue
                    z.extract(member, temp_dir)

            os.remove(zip_path)  # Cleanup zip

            # 4. Get OCR queue item details for merging
            with self.session_scope() as session:
                ocr_item = session.query(OcrQueue).filter_by(id=queue_id).first()
                if not ocr_item:
                    raise ValueError(f"OCR queue item {queue_id} not found")

                identifier = ocr_item.identifier
                original_filename = ocr_item.original_filename

                # Mark this split as completed
                ocr_item.status = "completed"
                ocr_item.ocr_output_path = temp_dir

            # 5. Check if all splits for this original file are complete
            with self.session_scope() as session:
                all_splits = (
                    session.query(OcrQueue)
                    .filter_by(
                        identifier=identifier, original_filename=original_filename
                    )
                    .order_by(OcrQueue.page_start)
                    .all()
                )

                all_complete = all(split.status == "completed" for split in all_splits)

                if all_complete:
                    # Merge all OCR outputs for this original file
                    self._merge_ocr_outputs(identifier, original_filename, all_splits)
                    logging.info(
                        f"Merged OCR outputs for {identifier}/{original_filename}"
                    )
                else:
                    logging.info(
                        f"Split {queue_id} completed, waiting for other splits of {original_filename}"
                    )

        except Exception as e:
            self._mark_failed(queue_id, f"Finalization failed: {e}")

    def _merge_ocr_outputs(self, identifier, original_filename, splits):
        """Merges OCR outputs from all splits into a clean user-facing structure."""
        import json
        import glob

        # Get the base directory
        if not splits:
            return

        base_dir = os.path.dirname(splits[0].ocr_output_path.replace(".ocr_temp", ""))

        # Create clean OCR output directory
        ocr_base = os.path.join(base_dir, "ocr")
        original_base = os.path.splitext(original_filename)[0]
        ocr_dir = os.path.join(ocr_base, original_base)
        metadata_dir = os.path.join(ocr_dir, "metadata")
        os.makedirs(metadata_dir, exist_ok=True)

        # Collect all markdown and JSON files
        all_md_content = []
        all_json_files = []
        manifest_data = {
            "original_file": original_filename,
            "identifier": identifier,
            "splits": [],
            "total_pages": 0,
        }

        for split in splits:
            temp_path = split.ocr_output_path

            # Skip splits that have no output (NO_OUTPUT_AVAILABLE)
            if not temp_path or not os.path.exists(temp_path):
                logging.warning(
                    f"Skipping split {split.id} - no output available (temp_path: {temp_path})"
                )
                continue

            # Find markdown files
            md_files = glob.glob(os.path.join(temp_path, "**", "*.md"), recursive=True)
            for md_file in md_files:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        all_md_content.append(content)

            # Find JSON files
            json_files = glob.glob(
                os.path.join(temp_path, "**", "*.json"), recursive=True
            )
            for json_file in json_files:
                # Copy to metadata directory with unique name
                base_name = os.path.basename(json_file)
                dest_name = f"split{split.id}_{base_name}"
                shutil.copy2(json_file, os.path.join(metadata_dir, dest_name))
                all_json_files.append(dest_name)

            # Add to manifest
            manifest_data["splits"].append(
                {
                    "split_id": split.id,
                    "file_name": split.file_name,
                    "page_start": split.page_start,
                    "page_end": split.page_end,
                    "sarvam_job_id": split.sarvam_job_id,
                }
            )

            if split.page_end:
                manifest_data["total_pages"] = max(
                    manifest_data["total_pages"], split.page_end
                )

        # Write merged markdown
        content_path = os.path.join(ocr_dir, "content.md")
        with open(content_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(all_md_content))

        # Write manifest
        manifest_path = os.path.join(ocr_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        logging.info(
            f"Created merged OCR output: {len(all_md_content)} markdown sections, "
            f"{len(all_json_files)} JSON files"
        )

    # --- HELPERS ---
    def _handle_api_error(self, queue_id, error):
        if error.status_code == 429:
            logging.warning(f"Rate Limit (429) for job {queue_id}. Backing off.")
            # Move back to pending to retry later, but sleep now to clear congestion
            time.sleep(30)
            with self.session_scope() as session:
                ocr_item = session.query(OcrQueue).filter_by(id=queue_id).first()
                if ocr_item:
                    ocr_item.status = "pending"
        elif error.status_code == 422:
            self._mark_failed(queue_id, "File Unprocessable (422) - likely corrupt")
        else:
            self._mark_failed(queue_id, str(error))

    def _mark_failed(self, queue_id, msg):
        logging.error(f"Job {queue_id} failed: {msg}")
        with self.session_scope() as session:
            ocr_item = session.query(OcrQueue).filter_by(id=queue_id).first()
            if ocr_item:
                ocr_item.status = "failed"
                ocr_item.error_message = msg

    def run_full_cycle(self):
        """Runs one full cycle of the pipeline and returns True if work was done."""
        # Check if we have pending jobs to avoid unnecessary submissions
        with self.session_scope() as session:
            pending_count = (
                session.query(OcrQueue)
                .filter(OcrQueue.status.in_(["pending", "polling"]))
                .count()
            )
            queued_count = (
                session.query(Manifest).filter(Manifest.status == "queued").count()
            )

            logging.info(
                f"Status: {pending_count} OCR items in flight, {queued_count} items queued for download."
            )

        # 1. Run Downloader (if we have capacity/need)
        self.run_downloader(limit=5)

        # 2. Run Submitter
        self.run_ocr_submitter(limit=10)

        # 3. Run Poller
        self.run_ocr_poller()

        # Determine if we should continue
        return pending_count > 0 or queued_count > 0


if __name__ == "__main__":
    with ArchivePipeline() as pipeline:
        # 1. Stage (Example: Bodo books)
        pipeline.stage_by_keywords("Bodo", [])

        # 2. Controlled Loop
        print("--- Pipeline Started (Ctrl+C to stop) ---")
        try:
            while True:
                has_work = pipeline.run_full_cycle()

                if not has_work:
                    logging.info("No more work found. Exiting.")
                    break

                # Sleep to prevent tight loops
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nStopping...")
