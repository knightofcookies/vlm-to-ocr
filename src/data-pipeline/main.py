"""Data pipeline for downloading and OCR processing of Internet Archive PDFs."""

import json
import logging
import os
import re
import shutil
import signal
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import fitz  # PyMuPDF
import internetarchive as ia
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from db import (
    Document,
    Manifest,
    OcrBatch,
    ensure_schema_migrated,
    get_engine,
    get_session_factory,
    session_scope,
)

load_dotenv()

# --- Configuration ---
DATA_ROOT = os.environ.get("DATA_ROOT", "data")
LOG_FILE = os.environ.get("LOG_FILE", "pipeline.log")
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")

MAX_DOWNLOAD_WORKERS = int(os.environ.get("MAX_DOWNLOAD_WORKERS", 10))
MAX_OCR_SUBMITTERS = int(os.environ.get("MAX_OCR_SUBMITTERS", 10))

# Sarvam API limits
MAX_BATCH_SIZE_MB = 100  # Stay under 100MB limit with buffer
MAX_PAGES_PER_BATCH = 250

# --- Logging Configuration ---
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        logging.FileHandler(LOG_FILE),
        RichHandler(console=console, rich_tracebacks=True, show_path=False),
    ],
)

# Suppress MuPDF chatter to avoid terminal spam
try:
    fitz.TOOLS.mupdf_display_errors(False)
except AttributeError:
    pass

# Global shutdown event
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logging.info("Received shutdown signal, stopping pipeline...")
    shutdown_event.set()


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class ArchivePipeline:
    def __init__(self):
        self.engine = get_engine()
        self.session_factory = get_session_factory(self.engine)
        self._backoff_until = 0.0

    def ensure_db_ready(self):
        """Fail fast when required tables are missing and instruct migration usage."""
        try:
            ensure_schema_migrated(
                {"manifest", "documents", "ocr_batches", "alembic_version"}
            )
        except Exception as e:
            logging.error(f"Failed database schema validation: {e}")
            exit(1)

    def reset_stalled_jobs(self):
        """Resets jobs stuck in 'downloading' or 'processing' state from previous crashes."""
        with session_scope(self.session_factory) as session:
            session.query(Manifest).filter(Manifest.status == "processing").update(
                {"status": "queued"}
            )
            session.query(Document).filter(Document.status == "processing").update(
                {"status": "pending"}
            )
            logging.info("Pipeline state synchronized.")

    @staticmethod
    def _normalize_to_utc(download_dt):
        """Normalizes datetime to UTC, defaulting to now when absent."""
        if download_dt is None:
            return datetime.now(timezone.utc)
        if download_dt.tzinfo is None:
            return download_dt.replace(tzinfo=timezone.utc)
        return download_dt.astimezone(timezone.utc)

    def _to_storage_date(self, download_dt):
        """Formats the UTC date partition used for item storage."""
        return self._normalize_to_utc(download_dt).strftime("%Y-%m-%d")

    def _get_item_path(self, manifest_id, download_dt):
        """Returns the base directory for a manifest item."""
        return os.path.join(
            DATA_ROOT,
            "items",
            self._to_storage_date(download_dt),
            str(manifest_id),
        )

    def _get_doc_path(self, manifest_id, doc_id, download_dt):
        """Returns the base directory for a specific document."""
        return os.path.join(
            self._get_item_path(manifest_id, download_dt), f"doc_{doc_id}"
        )

    @staticmethod
    def _parse_failed_pages(failed_pages):
        if not failed_pages:
            return set()
        try:
            parsed = json.loads(failed_pages)
            if isinstance(parsed, list):
                return {int(p) for p in parsed}
        except Exception:
            return set()
        return set()

    @staticmethod
    def _local_to_global_page(page_start, local_page_num):
        """Convert a batch-local page index (1-based) to the document-global page."""
        return page_start + local_page_num - 1

    @staticmethod
    def _count_json_separators(json_path):
        """Count raw '---' occurrences in a page metadata JSON file."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return f.read().count("---")
        except Exception:
            return 0

    def _split_markdown_by_page_budgets(
        self, chunks, ordered_local_pages, metadata_json_by_local_page
    ):
        """
        Split markdown chunks to local pages using per-page separator budgets.

        Returns (local_page_to_markdown_dict, mode_string).
        """
        page_text_by_local = {}
        cursor = 0
        for local_page in ordered_local_pages:
            json_path = metadata_json_by_local_page.get(local_page)
            budget = self._count_json_separators(json_path) if json_path else 0
            take = budget + 1
            if cursor + take > len(chunks):
                break
            page_text_by_local[local_page] = "\n---\n".join(
                chunks[cursor : cursor + take]
            )
            cursor += take

        if len(page_text_by_local) == len(ordered_local_pages) and cursor == len(
            chunks
        ):
            return page_text_by_local, "budgeted"

        if len(chunks) == len(ordered_local_pages):
            return {
                local_page: chunk
                for local_page, chunk in zip(ordered_local_pages, chunks)
            }, "simple-fallback"

        # Best effort fallback for malformed combined markdown:
        # preserve ordering; if extra chunks exist, append them to the last page.
        page_text_by_local = {}
        n_pages = len(ordered_local_pages)
        n_chunks = len(chunks)

        if n_pages == 0 or n_chunks == 0:
            return page_text_by_local, "empty"

        if n_chunks >= n_pages:
            for i, local_page in enumerate(ordered_local_pages):
                if i < n_pages - 1:
                    page_text_by_local[local_page] = chunks[i]
                else:
                    page_text_by_local[local_page] = "\n---\n".join(chunks[i:])
        else:
            for i, local_page in enumerate(ordered_local_pages[:n_chunks]):
                page_text_by_local[local_page] = chunks[i]

        return page_text_by_local, "sequential-fallback"

    def _get_pending_pages_for_document(self, session, doc_id, page_count):
        if page_count <= 0:
            return []

        excluded_pages = set()
        batches = session.query(OcrBatch).filter(OcrBatch.document_id == doc_id).all()

        for batch in batches:
            batch_range = set(range(batch.page_start, batch.page_end + 1))
            if batch.status in {"pending", "polling", "completed", "partial_success"}:
                # No retry for failed_pages yet; partial_success pages are intentionally
                # considered terminal for now.
                excluded_pages.update(batch_range)

        return [p for p in range(1, page_count + 1) if p not in excluded_pages]

    def _refresh_document_and_manifest_status(self, session, doc_id, manifest_id):
        doc = session.get(Document, doc_id)
        if not doc or doc.page_count <= 0:
            return

        all_pages = set(range(1, doc.page_count + 1))
        completed_batches = (
            session.query(OcrBatch)
            .filter(
                OcrBatch.document_id == doc_id,
                OcrBatch.status.in_(["completed", "partial_success"]),
            )
            .all()
        )
        active_batch_count = (
            session.query(OcrBatch)
            .filter(
                OcrBatch.document_id == doc_id,
                OcrBatch.status.in_(["pending", "polling"]),
            )
            .count()
        )

        covered_pages = set()
        failed_pages = set()
        for batch in completed_batches:
            batch_range = set(range(batch.page_start, batch.page_end + 1))
            covered_pages.update(batch_range)
            failed_pages.update(self._parse_failed_pages(batch.failed_pages))

        if covered_pages >= all_pages:
            if failed_pages:
                doc.status = "partial_success"
            else:
                doc.status = "completed"
        elif active_batch_count > 0:
            doc.status = "processing"
        else:
            doc.status = "downloaded"

        doc_states = [
            row[0]
            for row in session.query(Document.status)
            .filter(Document.manifest_id == manifest_id)
            .all()
        ]
        if not doc_states:
            return

        if all(state == "completed" for state in doc_states):
            manifest_status = "completed"
        elif any(
            state in {"processing", "pending", "downloaded"} for state in doc_states
        ):
            manifest_status = "processing"
        elif any(state == "partial_success" for state in doc_states):
            manifest_status = "partial_success"
        elif all(state == "failed" for state in doc_states):
            manifest_status = "failed"
        else:
            manifest_status = "processing"

        manifest = session.get(Manifest, manifest_id)
        if manifest:
            manifest.status = manifest_status

    # --- PHASE 2: DOWNLOAD & PRE-PROCESS (ASYNC) ---
    def run_downloader(self, limit=10):
        """Runs the downloader for queued items."""
        with session_scope(self.session_factory) as session:
            queued_items = (
                session.query(Manifest.identifier)
                .filter(Manifest.status == "queued")
                .limit(limit)
                .all()
            )

        if not queued_items:
            return

        logging.info(f"Downloading {len(queued_items)} archive items...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("Downloading...", total=len(queued_items))

            with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as executor:
                futures = [
                    executor.submit(self._download_task, item.identifier)
                    for item in queued_items
                ]
                for future in futures:
                    future.result()  # Wait for each to finish
                    progress.advance(task_id)

    def _convert_pdf_to_images(self, document_id, pdf_path, output_dir):
        """Converts a PDF to a series of images."""
        os.makedirs(output_dir, exist_ok=True)
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)

            for page_num in range(1, page_count + 1):
                page = doc.load_page(page_num - 1)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Better quality
                image_filename = f"{page_num}.png"
                image_path = os.path.join(output_dir, image_filename)
                pix.save(image_path)

            doc.close()
            return page_count
        except Exception as e:
            logging.error(f"Failed to convert PDF {pdf_path}: {e}")
            return 0

    def _download_task(self, identifier):
        with session_scope(self.session_factory) as session:
            manifest = session.query(Manifest).filter_by(identifier=identifier).first()
            if not manifest:
                return
            manifest_id = manifest.id
            manifest.status = "processing"
            if manifest.download_date is None:
                manifest.download_date = datetime.now(timezone.utc)
                logging.info(
                    f"Assigned download_date for manifest {manifest_id}: {manifest.download_date}"
                )
            session.commit()
            download_dt = manifest.download_date

        item_dir = self._get_item_path(manifest_id, download_dt)
        temp_download_dir = os.path.join(item_dir, "temp_downloads")
        os.makedirs(temp_download_dir, exist_ok=True)

        try:
            # 1. Check for PDFs before downloading to avoid IA library retry loop
            item = ia.get_item(identifier)
            files = [
                f["name"] for f in item.files if f["name"].lower().endswith(".pdf")
            ]

            if not files:
                raise FileNotFoundError(f"No PDFs found for {identifier}")

            # 2. Download to temp directory
            abs_temp_dir = os.path.abspath(temp_download_dir)
            os.makedirs(abs_temp_dir, exist_ok=True)

            logging.info(f"Downloading {identifier} to {abs_temp_dir}...")
            item.download(
                glob_pattern="*.pdf",
                destdir=abs_temp_dir,
                no_directory=True,
                verbose=False,
                ignore_existing=True,
            )

            # 3. Find all PDFs
            pdf_files = []
            for root, _, filenames in os.walk(abs_temp_dir):
                for filename in filenames:
                    if filename.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, filename))

            if not pdf_files:
                raise FileNotFoundError(f"No PDFs downloaded for {identifier}")

            # 4. Create Document records and move files
            for pdf_path in pdf_files:
                original_name = os.path.basename(pdf_path)

                with session_scope(self.session_factory) as session:
                    # Check if already tracked
                    existing_doc = (
                        session.query(Document)
                        .filter_by(
                            manifest_id=manifest_id, original_filename=original_name
                        )
                        .first()
                    )

                    if existing_doc:
                        doc_id = existing_doc.id
                    else:
                        doc_record = Document(
                            manifest_id=manifest_id,
                            original_filename=original_name,
                            status="processing",
                        )
                        session.add(doc_record)
                        session.flush()  # Get ID
                        doc_id = doc_record.id

                doc_dir = self._get_doc_path(manifest_id, doc_id, download_dt)
                os.makedirs(doc_dir, exist_ok=True)
                final_pdf_path = os.path.join(doc_dir, f"doc_{doc_id}.pdf")

                if not os.path.exists(final_pdf_path):
                    shutil.move(pdf_path, final_pdf_path)

                # 5. Convert to images and create OCR queue
                pages_dir = os.path.join(doc_dir, "pages")
                page_count = self._convert_pdf_to_images(
                    doc_id, final_pdf_path, pages_dir
                )

                with session_scope(self.session_factory) as session:
                    doc_record = session.get(Document, doc_id)
                    doc_record.page_count = page_count
                    if page_count > 0:
                        doc_record.status = "downloaded"
                    else:
                        doc_record.status = "failed"
                        doc_record.error_message = "PDF to Image conversion failed."

            with session_scope(self.session_factory) as session:
                manifest = session.get(Manifest, manifest_id)
                manifest.status = "downloaded"

        except Exception as e:
            logging.error(f"Download task failed for {identifier}: {e}")
            with session_scope(self.session_factory) as session:
                manifest = (
                    session.query(Manifest).filter_by(identifier=identifier).first()
                )
                if manifest:
                    manifest.status = "failed"
                    manifest.error_message = str(e)
        finally:
            if os.path.exists(temp_download_dir):
                # Retry rmtree for Windows
                for _ in range(3):
                    try:
                        shutil.rmtree(temp_download_dir, ignore_errors=True)
                        break
                    except Exception:
                        time.sleep(1)

    # --- PHASE 3: OCR SUBMISSION (ASYNC) ---
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(ApiError),
        reraise=True,
    )
    def _create_sarvam_job(self, client, lang_code):
        """Create a Sarvam job with retries."""
        return client.document_intelligence.create_job(
            language=lang_code, output_format="md"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(ApiError),
        reraise=True,
    )
    def _upload_and_start_job(self, job, zip_path):
        """Upload file and start job with retries."""
        job.upload_file(zip_path)
        job.start()

    def run_ocr_submitter(self, limit=500):
        if not SARVAM_API_KEY:
            logging.error("SARVAM_API_KEY is not set in environment.")
            return

        if time.time() < self._backoff_until:
            logging.info("OCR Submitter is in backoff mode. Skipping.")
            return

        client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

        with session_scope(self.session_factory) as session:
            eligible_docs = (
                session.query(
                    Document.id.label("doc_id"),
                    Document.page_count,
                    Manifest.id.label("manifest_id"),
                    Manifest.sarvam_lang_code,
                    Manifest.download_date.label("download_date"),
                )
                .join(Manifest, Document.manifest_id == Manifest.id)
                .filter(Document.status.in_(["downloaded", "partial_success"]))
                .limit(limit)
                .all()
            )

        docs_to_process = {}
        total_pending_pages = 0
        with session_scope(self.session_factory) as session:
            for doc in eligible_docs:
                pending_pages = self._get_pending_pages_for_document(
                    session, doc.doc_id, doc.page_count or 0
                )
                if not pending_pages:
                    continue
                docs_to_process[doc.doc_id] = {
                    "manifest_id": doc.manifest_id,
                    "download_date": doc.download_date,
                    "lang_code": doc.sarvam_lang_code,
                    "pages": pending_pages,
                }
                total_pending_pages += len(pending_pages)

        if not docs_to_process:
            return

        logging.info(
            f"Submitting {total_pending_pages} pages across {len(docs_to_process)} documents..."
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(
                "Submitting Docs...", total=len(docs_to_process)
            )

            with ThreadPoolExecutor(max_workers=MAX_OCR_SUBMITTERS) as executor:
                futures = []
                for doc_id, data in docs_to_process.items():
                    futures.append(
                        executor.submit(
                            self._submit_document_batches,
                            client,
                            doc_id,
                            data["manifest_id"],
                            data["download_date"],
                            data["lang_code"],
                            data["pages"],
                        )
                    )
                for future in futures:
                    future.result()
                    progress.advance(task_id)

    def _submit_document_batches(
        self, client, doc_id, manifest_id, download_dt, lang_code, pages
    ):
        """Submit a document's pages as one or more batches based on size limits."""
        doc_dir = self._get_doc_path(manifest_id, doc_id, download_dt)
        zip_dir = os.path.join(doc_dir, "temp_zips")
        os.makedirs(zip_dir, exist_ok=True)

        # Split pages into size-aware batches
        batches = self._create_size_aware_batches(pages, doc_dir)

        for batch_idx, batch_pages in enumerate(batches, 1):
            zip_path = os.path.join(
                zip_dir, f"batch_{doc_id}_{batch_idx}_{int(time.time())}.zip"
            )
            batch_id = None

            try:
                # Create ZIP
                submitted_pages = []
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for local_index, page_number in enumerate(batch_pages, start=1):
                        image_path = os.path.join(
                            doc_dir, "pages", f"{page_number}.png"
                        )
                        if os.path.exists(image_path):
                            # Use zero-padded sequential names so lexical and numeric
                            # ordering match for downstream OCR page indexing.
                            archive_name = f"page_{local_index:06d}.png"
                            zf.write(image_path, archive_name)
                            submitted_pages.append(page_number)

                if not submitted_pages:
                    logging.warning(
                        f"Skipping empty batch candidate for doc_{doc_id} (no images found)."
                    )
                    continue

                with session_scope(self.session_factory) as session:
                    batch_record = OcrBatch(
                        document_id=doc_id,
                        status="pending",
                        page_start=min(submitted_pages),
                        page_end=max(submitted_pages),
                        page_count=len(submitted_pages),
                    )
                    session.add(batch_record)
                    session.flush()
                    batch_id = batch_record.id

                zip_size = os.path.getsize(zip_path)

                # Submit to Sarvam
                job = self._create_sarvam_job(client, lang_code)
                self._upload_and_start_job(job, zip_path)

                with session_scope(self.session_factory) as session:
                    batch = session.get(OcrBatch, batch_id)
                    if batch:
                        batch.sarvam_job_id = job.job_id
                        batch.status = "polling"
                        batch.zip_size_bytes = zip_size
                        batch.updated_at = datetime.now(timezone.utc)

                logging.info(
                    f"Submitted batch_{batch_id} (doc_{doc_id}, {len(submitted_pages)} pages, {zip_size / 1024 / 1024:.1f}MB) -> Job {job.job_id}"
                )

            except ApiError as e:
                if e.status_code == 429:
                    logging.warning(
                        "Rate Limit (429) during batch submission. Backing off."
                    )
                    self._backoff_until = time.time() + 60
                    if batch_id is not None:
                        self._mark_batch_failed(
                            batch_id, "Rate limited during submission"
                        )
                else:
                    logging.error(f"Batch {batch_id or 'unknown'} failed: {e}")
                    if batch_id is not None:
                        self._mark_batch_failed(batch_id, str(e))
            except Exception as e:
                logging.error(f"Batch {batch_id or 'unknown'} failed: {e}")
                if batch_id is not None:
                    self._mark_batch_failed(batch_id, str(e))
            finally:
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except Exception:
                        pass

    def _create_size_aware_batches(self, pages, doc_dir):
        """Split pages into batches that respect size and page count limits."""
        batches = []
        current_batch = []
        current_size = 0

        for page_number in sorted(set(pages)):
            image_path = os.path.join(doc_dir, "pages", f"{page_number}.png")
            if not os.path.exists(image_path):
                continue

            image_size = os.path.getsize(image_path)

            # Check if adding this page would exceed limits
            would_exceed_size = (current_size + image_size) > (
                MAX_BATCH_SIZE_MB * 1024 * 1024
            )
            would_exceed_count = len(current_batch) >= MAX_PAGES_PER_BATCH

            would_break_range = current_batch and page_number != (current_batch[-1] + 1)

            if current_batch and (
                would_exceed_size or would_exceed_count or would_break_range
            ):
                # Start new batch
                batches.append(current_batch)
                current_batch = []
                current_size = 0

            current_batch.append(page_number)
            current_size += image_size

        # Add final batch
        if current_batch:
            batches.append(current_batch)

        return batches

    def _mark_batch_failed(self, batch_id, error_msg):
        with session_scope(self.session_factory) as session:
            session.query(OcrBatch).filter(OcrBatch.id == batch_id).update(
                {
                    "status": "failed",
                    "error_message": error_msg,
                    "updated_at": datetime.now(timezone.utc),
                }
            )

    # --- PHASE 4: OCR POLLING (ASYNC) ---
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(ApiError),
        reraise=True,
    )
    def _get_job_status(self, client, job_id):
        """Get job status with retries."""
        return client.document_intelligence.get_status(job_id=job_id)

    def run_ocr_poller(self, limit=20):
        """Checks status of batches that are already running."""
        client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

        with session_scope(self.session_factory) as session:
            batch_data = (
                session.query(
                    OcrBatch.id,
                    OcrBatch.sarvam_job_id,
                    OcrBatch.document_id,
                    Document.manifest_id,
                    Manifest.download_date,
                )
                .join(Document, OcrBatch.document_id == Document.id)
                .join(Manifest, Document.manifest_id == Manifest.id)
                .filter(OcrBatch.status == "polling")
                .limit(limit)
                .all()
            )

        if not batch_data:
            return

        for batch_id, sarvam_job_id, doc_id, manifest_id, download_dt in batch_data:
            try:
                status = self._get_job_status(client, sarvam_job_id)
                state = status.job_state

                if state == "Completed" or state == "PartiallyCompleted":
                    self._finalize_batch(
                        client,
                        batch_id,
                        sarvam_job_id,
                        manifest_id,
                        doc_id,
                        download_dt,
                    )
                elif state == "Failed":
                    error_msg = getattr(status, "error_message", "Job failed")
                    self._mark_batch_failed(batch_id, f"Sarvam Job Failed: {error_msg}")
            except Exception as e:
                logging.error(
                    f"Failed to poll batch {batch_id} (Job {sarvam_job_id}): {e}"
                )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(ApiError),
        reraise=True,
    )
    def _download_job_output(self, client, job_id, zip_path):
        """Download job output with retries."""
        response = client.document_intelligence.get_download_links(job_id=job_id)
        if not response.download_urls:
            raise RuntimeError(f"No download URLs returned for job {job_id}")

        # Get the first file's download URL
        first_file = next(iter(response.download_urls.values()))
        file_url = first_file.file_url

        r = requests.get(file_url, timeout=300)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(r.content)

    def _finalize_batch(
        self, client, batch_id, sarvam_job_id, manifest_id, doc_id, download_dt
    ):
        """Downloads the output, extracts it, and updates DB for all pages in batch."""
        doc_path = self._get_doc_path(manifest_id, doc_id, download_dt)
        output_dir = os.path.join(doc_path, "ocr_output", f"batch_{batch_id}")
        os.makedirs(output_dir, exist_ok=True)
        zip_path = os.path.join(output_dir, f"{sarvam_job_id}.zip")

        try:
            self._download_job_output(client, sarvam_job_id, zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(output_dir)

            # Reclaim disk space once extraction succeeds.
            try:
                os.remove(zip_path)
            except OSError as e:
                logging.warning(f"Could not remove ZIP for batch {batch_id}: {e}")

            with session_scope(self.session_factory) as session:
                batch = session.get(OcrBatch, batch_id)
                if not batch:
                    raise RuntimeError(
                        f"Batch {batch_id} not found during finalization."
                    )
                expected_global_pages = set(range(batch.page_start, batch.page_end + 1))
                expected_local_pages = set(range(1, len(expected_global_pages) + 1))

                md_files = []
                metadata_json_by_local_page = {}
                for root, _, files in os.walk(output_dir):
                    for name in files:
                        file_path = os.path.join(root, name)
                        _, ext = os.path.splitext(name)
                        ext = ext.lower()
                        if ext == ".md":
                            md_files.append(file_path)
                        elif ext == ".json":
                            match = re.match(r"^page_(\d+)\.json$", name)
                            if match:
                                local_page_num = int(match.group(1))
                                if local_page_num in expected_local_pages:
                                    metadata_json_by_local_page[local_page_num] = (
                                        file_path
                                    )

                local_pages_present = set(metadata_json_by_local_page.keys())
                processed_page_numbers = {
                    self._local_to_global_page(batch.page_start, local_page_num)
                    for local_page_num in local_pages_present
                }
                missing_local_pages = sorted(expected_local_pages - local_pages_present)
                failed_page_numbers = sorted(
                    self._local_to_global_page(batch.page_start, local_page_num)
                    for local_page_num in missing_local_pages
                )
                if failed_page_numbers:
                    logging.warning(
                        f"Batch {batch_id} missing JSON metadata for local pages: {missing_local_pages}; global pages: {failed_page_numbers}"
                    )
                logging.info(
                    f"Batch {batch_id} metadata summary: expected_local={len(expected_local_pages)} found_local={len(local_pages_present)} failed_global={len(failed_page_numbers)}"
                )

                combined_md_path = (
                    max(md_files, key=os.path.getsize) if md_files else None
                )
                if combined_md_path is None:
                    logging.warning(
                        f"Batch {batch_id} has no markdown output files in {output_dir}"
                    )

                split_md_by_page_number = {}
                if combined_md_path and processed_page_numbers:
                    with open(combined_md_path, "r", encoding="utf-8") as f:
                        combined_markdown = f.read()

                    chunks = re.split(r"\r?\n[ \t]*---[ \t]*\r?\n", combined_markdown)
                    ordered_local_pages = sorted(local_pages_present)
                    page_text_by_local, split_mode = (
                        self._split_markdown_by_page_budgets(
                            chunks, ordered_local_pages, metadata_json_by_local_page
                        )
                    )

                    for local_page_num, page_text in page_text_by_local.items():
                        page_number = self._local_to_global_page(
                            batch.page_start, local_page_num
                        )
                        page_md_path = os.path.join(output_dir, f"{page_number}.md")
                        with open(page_md_path, "w", encoding="utf-8") as f:
                            f.write(page_text.rstrip() + "\n")
                        split_md_by_page_number[page_number] = page_md_path

                    if len(page_text_by_local) < len(ordered_local_pages):
                        logging.warning(
                            f"Batch {batch_id} markdown split incomplete ({split_mode}): mapped {len(page_text_by_local)} pages from {len(chunks)} chunks with {len(ordered_local_pages)} metadata pages."
                        )
                    elif split_mode != "budgeted":
                        logging.warning(
                            f"Batch {batch_id} markdown split used {split_mode}: chunks={len(chunks)} metadata_pages={len(ordered_local_pages)}."
                        )

                now = datetime.now(timezone.utc)
                batch.status = (
                    "completed" if not failed_page_numbers else "partial_success"
                )
                batch.failed_pages = json.dumps(failed_page_numbers)
                batch.output_dir = output_dir
                batch.updated_at = now

                # TODO: Implement retry workflow for failed_page_numbers in a future pass.
                self._refresh_document_and_manifest_status(session, doc_id, manifest_id)

            logging.info(f"Batch {batch_id} (Job {sarvam_job_id}) finalized.")
        except Exception as e:
            self._mark_batch_failed(batch_id, f"Finalization failed: {e}")

    def print_status(self):
        with session_scope(self.session_factory) as session:
            pending_docs = (
                session.query(Document.id, Document.page_count)
                .filter(Document.status.in_(["downloaded", "partial_success"]))
                .all()
            )
            ocr_pending_docs = 0
            for doc_id, page_count in pending_docs:
                if self._get_pending_pages_for_document(
                    session, doc_id, page_count or 0
                ):
                    ocr_pending_docs += 1

            ocr_polling = (
                session.query(OcrBatch).filter(OcrBatch.status == "polling").count()
            )
            active_manifests = (
                session.query(Manifest)
                .filter(Manifest.status.in_(["queued", "downloading", "processing"]))
                .count()
            )

            status_text = (
                f"[bold blue]OCR Pending Docs:[/bold blue] {ocr_pending_docs} "
                f"[bold yellow]OCR Polling:[/bold yellow] {ocr_polling} "
                f"[bold cyan]Active Manifests:[/bold cyan] {active_manifests}"
            )
            console.print(
                Panel(
                    status_text,
                    title="[bold white]Pipeline Status[/bold white]",
                    expand=False,
                )
            )


def download_loop(pipeline):
    """Continuously run the download phase"""
    while not shutdown_event.is_set():
        try:
            pipeline.run_downloader(limit=50)
            time.sleep(10)  # Check for downloads every 10 seconds
        except Exception as e:
            logging.error(f"Download loop error: {e}")
            time.sleep(30)


def ocr_submit_loop(pipeline):
    """Continuously run the OCR submission phase"""
    while not shutdown_event.is_set():
        try:
            pipeline.run_ocr_submitter(limit=500)
            time.sleep(15)  # Check for OCR submissions every 15 seconds
        except Exception as e:
            logging.error(f"OCR submitter loop error: {e}")
            time.sleep(30)


def ocr_poll_loop(pipeline):
    """Continuously run the OCR polling phase"""
    while not shutdown_event.is_set():
        try:
            pipeline.run_ocr_poller(limit=50)
            pipeline.print_status()
            time.sleep(20)  # Check for OCR polling every 20 seconds and print status
        except Exception as e:
            logging.error(f"OCR poller loop error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    console.print(
        Panel.fit(
            "[bold magenta]ARC-HIVE[/bold magenta] - [italic]Document Intelligence Pipeline[/italic]",
            border_style="magenta",
        )
    )

    if not SARVAM_API_KEY:
        logging.error(
            "[bold red]ERROR:[/bold red] SARVAM_API_KEY is not set. Please check your .env file."
        )
        exit(1)

    pipeline = ArchivePipeline()
    pipeline.ensure_db_ready()
    pipeline.reset_stalled_jobs()

    logging.info(
        "Starting pipeline with all stages running in parallel (Excluding Staging)..."
    )

    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all stages as separate tasks to run in parallel
        download_future = executor.submit(download_loop, pipeline)
        ocr_submit_future = executor.submit(ocr_submit_loop, pipeline)
        ocr_poll_future = executor.submit(ocr_poll_loop, pipeline)

        try:
            # Wait for shutdown event
            while not shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Received interrupt signal, shutting down...")
            shutdown_event.set()

        # Wait for threads to finish
        logging.info("Waiting for threads to complete...")
        download_future.result(timeout=30)
        ocr_submit_future.result(timeout=30)
        ocr_poll_future.result(timeout=30)

    logging.info("Pipeline shutdown complete.")
