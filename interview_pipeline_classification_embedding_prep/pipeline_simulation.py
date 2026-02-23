from __future__ import annotations

import math
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DocumentStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobRecord:
    job_id: str
    user_id: str
    status: JobStatus
    total_files: int
    processed_files: int = 0
    failed_files: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    errors: list[dict[str, str]] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)


@dataclass
class DocumentRecord:
    document_id: str
    job_id: str
    user_id: str
    filename: str
    storage_uri: str
    status: DocumentStatus
    error_message: str | None = None
    attempts: int = 0
    updated_at: float = field(default_factory=time.time)


@dataclass
class DocumentResult:
    document_id: str
    label: str
    embedding: list[float]


@dataclass
class WorkItem:
    document_id: str
    attempt: int = 0


@dataclass
class Metrics:
    jobs_created: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    jobs_partial: int = 0
    documents_processed: int = 0
    documents_failed: int = 0
    classification_calls: int = 0
    embedding_calls: int = 0
    classification_failures: int = 0
    embedding_failures: int = 0
    queue_depth_samples: list[int] = field(default_factory=list)
    classification_latency_ms: list[float] = field(default_factory=list)
    embedding_latency_ms: list[float] = field(default_factory=list)


class ObjectStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._objects: dict[str, bytes] = {}

    def put(self, job_id: str, document_id: str, filename: str, content: bytes) -> str:
        uri = f"obj://jobs/{job_id}/{document_id}/{filename}"
        with self._lock:
            self._objects[uri] = content
        return uri

    def get(self, uri: str) -> bytes:
        with self._lock:
            if uri not in self._objects:
                raise KeyError(f"object not found: {uri}")
            return self._objects[uri]


class MetadataDB:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.jobs: dict[str, JobRecord] = {}
        self.documents: dict[str, DocumentRecord] = {}
        self.results: dict[str, DocumentResult] = {}

    def create_job(self, user_id: str, total_files: int) -> JobRecord:
        with self._lock:
            job_id = f"job-{uuid.uuid4()}"
            job = JobRecord(
                job_id=job_id,
                user_id=user_id,
                status=JobStatus.QUEUED,
                total_files=total_files,
            )
            self.jobs[job_id] = job
            return job

    def create_document(
        self,
        job_id: str,
        user_id: str,
        filename: str,
        storage_uri: str,
    ) -> DocumentRecord:
        with self._lock:
            document_id = f"doc-{uuid.uuid4()}"
            doc = DocumentRecord(
                document_id=document_id,
                job_id=job_id,
                user_id=user_id,
                filename=filename,
                storage_uri=storage_uri,
                status=DocumentStatus.QUEUED,
            )
            self.documents[document_id] = doc
            self.jobs[job_id].document_ids.append(document_id)
            self.jobs[job_id].updated_at = time.time()
            return doc

    def set_job_status(self, job_id: str, status: JobStatus) -> None:
        with self._lock:
            job = self.jobs[job_id]
            job.status = status
            job.updated_at = time.time()

    def set_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> None:
        with self._lock:
            doc = self.documents[document_id]
            doc.status = status
            doc.error_message = error_message
            doc.updated_at = time.time() if hasattr(doc, "updated_at") else None

    def increment_attempt(self, document_id: str) -> None:
        with self._lock:
            self.documents[document_id].attempts += 1

    def write_result(self, result: DocumentResult) -> None:
        with self._lock:
            self.results[result.document_id] = result

    def mark_document_completed(self, document_id: str) -> None:
        with self._lock:
            doc = self.documents[document_id]
            if doc.status == DocumentStatus.COMPLETED:
                return
            if doc.status == DocumentStatus.FAILED:
                return
            doc.status = DocumentStatus.COMPLETED
            job = self.jobs[doc.job_id]
            job.processed_files += 1
            job.updated_at = time.time()
            self._refresh_job_terminal_status_locked(job)

    def mark_document_failed(self, document_id: str, reason: str) -> None:
        with self._lock:
            doc = self.documents[document_id]
            if doc.status == DocumentStatus.FAILED:
                return
            if doc.status == DocumentStatus.COMPLETED:
                return
            doc.status = DocumentStatus.FAILED
            doc.error_message = reason
            job = self.jobs[doc.job_id]
            job.failed_files += 1
            job.errors.append({"document_id": doc.document_id, "error": reason})
            job.updated_at = time.time()
            self._refresh_job_terminal_status_locked(job)

    def _refresh_job_terminal_status_locked(self, job: JobRecord) -> None:
        done = job.processed_files + job.failed_files
        if done < job.total_files:
            job.status = JobStatus.PROCESSING
            return
        if job.failed_files == 0:
            job.status = JobStatus.COMPLETED
        elif job.processed_files == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.PARTIAL

    def get_job(self, job_id: str) -> JobRecord:
        with self._lock:
            return self.jobs[job_id]

    def get_job_documents(self, job_id: str) -> list[DocumentRecord]:
        with self._lock:
            ids = list(self.jobs[job_id].document_ids)
            return [self.documents[i] for i in ids]

    def get_job_results(self, job_id: str) -> list[dict[str, Any]]:
        with self._lock:
            out: list[dict[str, Any]] = []
            for doc in self.get_job_documents(job_id):
                row: dict[str, Any] = {
                    "document_id": doc.document_id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "error_message": doc.error_message,
                }
                if doc.document_id in self.results:
                    r = self.results[doc.document_id]
                    row["label"] = r.label
                    row["embedding_dim"] = len(r.embedding)
                out.append(row)
            return out


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._vectors: dict[str, list[float]] = {}
        self._meta: dict[str, dict[str, Any]] = {}

    def upsert(self, document_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        with self._lock:
            self._vectors[document_id] = embedding
            self._meta[document_id] = dict(metadata)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            scored: list[tuple[float, str]] = []
            for doc_id, vec in self._vectors.items():
                score = cosine_similarity(query_vector, vec)
                scored.append((score, doc_id))
            scored.sort(key=lambda x: x[0], reverse=True)
            out: list[dict[str, Any]] = []
            for score, doc_id in scored[:top_k]:
                out.append({"document_id": doc_id, "score": score, "metadata": self._meta[doc_id]})
            return out


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vector lengths mismatch")
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


class BlackBoxClassificationService:
    def __init__(self, latency_ms: float = 25.0, failure_rate: float = 0.0, seed: int = 7) -> None:
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self._rng = __import__("random").Random(seed)
        self._lock = threading.RLock()

    def classify(self, texts: list[str]) -> list[str]:
        self._sleep_latency()
        self._maybe_fail("classification service failure")
        labels = []
        for t in texts:
            s = t.lower()
            if any(k in s for k in ["invoice", "payment", "billing"]):
                labels.append("finance")
            elif any(k in s for k in ["error", "bug", "incident", "failure"]):
                labels.append("support")
            elif any(k in s for k in ["contract", "policy", "legal"]):
                labels.append("legal")
            else:
                labels.append("general")
        return labels

    def _sleep_latency(self) -> None:
        time.sleep(self.latency_ms / 1000.0)

    def _maybe_fail(self, message: str) -> None:
        with self._lock:
            if self.failure_rate > 0 and self._rng.random() < self.failure_rate:
                raise RuntimeError(message)


class BlackBoxEmbeddingService:
    def __init__(
        self,
        embedding_dim: int = 16,
        latency_ms: float = 30.0,
        failure_rate: float = 0.0,
        seed: int = 17,
    ) -> None:
        self.embedding_dim = embedding_dim
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self._rng = __import__("random").Random(seed)
        self._lock = threading.RLock()

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._sleep_latency()
        self._maybe_fail("embedding service failure")
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        # Deterministic hash-based pseudo embedding for simulation.
        vec = [0.0 for _ in range(self.embedding_dim)]
        if not text:
            return vec
        for i, ch in enumerate(text.encode("utf-8")):
            idx = i % self.embedding_dim
            vec[idx] += (ch % 31) / 31.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def _sleep_latency(self) -> None:
        time.sleep(self.latency_ms / 1000.0)

    def _maybe_fail(self, message: str) -> None:
        with self._lock:
            if self.failure_rate > 0 and self._rng.random() < self.failure_rate:
                raise RuntimeError(message)


class TextExtractor:
    @staticmethod
    def extract(filename: str, content: bytes) -> str:
        lower = filename.lower()
        if not (lower.endswith(".txt") or lower.endswith(".md") or lower.endswith(".csv")):
            raise ValueError("unsupported file type; only .txt/.md/.csv in this simulation")
        try:
            return content.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError("file is not valid utf-8 text") from exc


class PipelineSystem:
    """
    End-to-end simulation:
    - sync API for small uploads
    - async API for bulk uploads
    - queue + worker pool with batching
    - black-box classification/embedding services
    - object store + metadata db + vector store
    """

    def __init__(
        self,
        classifier: BlackBoxClassificationService | None = None,
        embedder: BlackBoxEmbeddingService | None = None,
        max_sync_files: int = 10,
        max_bulk_files: int = 1000,
        max_retries: int = 2,
    ) -> None:
        self.object_store = ObjectStore()
        self.db = MetadataDB()
        self.vector_store = InMemoryVectorStore()
        self.metrics = Metrics()

        self.classifier = classifier or BlackBoxClassificationService()
        self.embedder = embedder or BlackBoxEmbeddingService()
        self.max_sync_files = max_sync_files
        self.max_bulk_files = max_bulk_files
        self.max_retries = max_retries

        self._queue: queue.Queue[WorkItem] = queue.Queue()
        self._stop_event = threading.Event()
        self._workers: list[threading.Thread] = []
        self._workers_started = False
        self._lock = threading.RLock()
        self._counted_terminal_jobs: set[str] = set()

    # ------------------------------------------------------------------
    # API-like methods
    # ------------------------------------------------------------------
    def post_documents_process(
        self,
        user_id: str,
        files: list[tuple[str, bytes]],
    ) -> dict[str, Any]:
        if not files:
            return {"status": "error", "message": "no files uploaded"}
        if len(files) > self.max_sync_files:
            return {
                "status": "error",
                "message": f"sync endpoint supports up to {self.max_sync_files} files",
            }

        job = self.db.create_job(user_id=user_id, total_files=len(files))
        self.metrics.jobs_created += 1
        self.db.set_job_status(job.job_id, JobStatus.PROCESSING)

        docs: list[DocumentRecord] = []
        extracted: list[str] = []
        for filename, content in files:
            uri = self.object_store.put(job.job_id, f"seed-{uuid.uuid4()}", filename, content)
            doc = self.db.create_document(job.job_id, user_id, filename, uri)
            docs.append(doc)
            self.db.set_document_status(doc.document_id, DocumentStatus.PROCESSING)
            try:
                text = TextExtractor.extract(filename, content)
            except Exception as exc:
                self.db.mark_document_failed(doc.document_id, f"text extraction failed: {exc}")
                self.metrics.documents_failed += 1
                continue
            extracted.append(text)

        # Process valid documents in one synchronous batch path.
        valid_docs = [
            d for d in docs if self.db.documents[d.document_id].status != DocumentStatus.FAILED
        ]
        if valid_docs:
            batch_errors = self._classify_and_embed(valid_docs, extracted)
            failed_doc_ids = {e["document_id"] for e in batch_errors}
            for err in batch_errors:
                job.errors.append({"document_id": err["document_id"], "error": err["error"]})
                self.db.mark_document_failed(err["document_id"], err["error"])
                self.metrics.documents_failed += 1

            for doc in valid_docs:
                if doc.document_id not in failed_doc_ids:
                    self.db.mark_document_completed(doc.document_id)
                    self.metrics.documents_processed += 1

        # Job status finalization handled by mark_document_*.
        final_job = self.db.get_job(job.job_id)
        self._update_job_metrics_from_status(final_job.job_id, final_job.status)
        return self._job_response(final_job, include_results=True)

    def post_documents_batch_upload(
        self,
        user_id: str,
        files: list[tuple[str, bytes]],
    ) -> dict[str, Any]:
        if not files:
            return {"status": "error", "message": "no files uploaded"}
        if len(files) > self.max_bulk_files:
            return {
                "status": "error",
                "message": f"bulk endpoint supports up to {self.max_bulk_files} files",
            }

        job = self.db.create_job(user_id=user_id, total_files=len(files))
        self.metrics.jobs_created += 1

        for filename, content in files:
            uri = self.object_store.put(job.job_id, f"seed-{uuid.uuid4()}", filename, content)
            doc = self.db.create_document(job.job_id, user_id, filename, uri)
            self._queue.put(WorkItem(document_id=doc.document_id, attempt=0))

        self.db.set_job_status(job.job_id, JobStatus.QUEUED)
        return {"job_id": job.job_id, "status": "queued", "total_files": len(files)}

    def get_job(self, job_id: str) -> dict[str, Any]:
        job = self.db.get_job(job_id)
        return self._job_response(job, include_results=False)

    def get_job_results(self, job_id: str) -> dict[str, Any]:
        job = self.db.get_job(job_id)
        return {
            **self._job_response(job, include_results=False),
            "results": self.db.get_job_results(job_id),
        }

    def semantic_search(self, query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_vec = self.embedder.embed([query_text])[0]
        return self.vector_store.search(query_vec, top_k=top_k)

    # ------------------------------------------------------------------
    # Worker pool
    # ------------------------------------------------------------------
    def start_workers(
        self,
        num_workers: int = 4,
        batch_size: int = 32,
        batch_wait_ms: int = 50,
    ) -> None:
        with self._lock:
            if self._workers_started:
                return
            self._workers_started = True
            self._stop_event.clear()
            for i in range(num_workers):
                t = threading.Thread(
                    target=self._worker_loop,
                    args=(batch_size, batch_wait_ms),
                    name=f"pipeline-worker-{i}",
                    daemon=True,
                )
                t.start()
                self._workers.append(t)

    def stop_workers(self) -> None:
        with self._lock:
            if not self._workers_started:
                return
            self._stop_event.set()
            for t in self._workers:
                t.join(timeout=1.0)
            self._workers.clear()
            self._workers_started = False

    def wait_until_queue_drained(self, timeout_s: float = 30.0) -> bool:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self._queue.unfinished_tasks == 0:
                return True
            time.sleep(0.02)
        return False

    def _worker_loop(self, batch_size: int, batch_wait_ms: int) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            batch = [item]
            batch_deadline = time.time() + (batch_wait_ms / 1000.0)
            while len(batch) < batch_size and time.time() < batch_deadline:
                try:
                    batch.append(self._queue.get_nowait())
                except queue.Empty:
                    time.sleep(0.001)
                    continue

            self.metrics.queue_depth_samples.append(self._queue.qsize())
            self._process_batch(batch)
            for _ in batch:
                self._queue.task_done()

    def _process_batch(self, batch: list[WorkItem]) -> None:
        valid_docs: list[DocumentRecord] = []
        texts: list[str] = []

        for item in batch:
            doc = self.db.documents[item.document_id]
            if doc.status in (DocumentStatus.COMPLETED, DocumentStatus.FAILED):
                continue
            self.db.increment_attempt(doc.document_id)
            self.db.set_document_status(doc.document_id, DocumentStatus.PROCESSING)
            self.db.set_job_status(doc.job_id, JobStatus.PROCESSING)

            try:
                content = self.object_store.get(doc.storage_uri)
                text = TextExtractor.extract(doc.filename, content)
            except Exception as exc:
                self._handle_document_failure(doc, f"text extraction failed: {exc}", doc.attempts)
                continue

            valid_docs.append(doc)
            texts.append(text)

        if not valid_docs:
            return

        errors = self._classify_and_embed(valid_docs, texts)
        for err in errors:
            doc = self.db.documents[err["document_id"]]
            self._handle_document_failure(doc, err["error"], doc.attempts)

        for doc in valid_docs:
            # If this doc was not marked failed by above errors, mark completed.
            if self.db.documents[doc.document_id].status == DocumentStatus.PROCESSING:
                self.db.mark_document_completed(doc.document_id)
                self.metrics.documents_processed += 1
                self._update_job_metrics_from_status(doc.job_id, self.db.jobs[doc.job_id].status)

    def _handle_document_failure(self, doc: DocumentRecord, reason: str, attempt: int) -> None:
        if attempt <= self.max_retries:
            # Retry with small exponential backoff.
            time.sleep(0.01 * (2 ** max(0, attempt - 1)))
            self.db.set_document_status(doc.document_id, DocumentStatus.QUEUED, error_message=reason)
            self._queue.put(WorkItem(document_id=doc.document_id, attempt=attempt))
            return
        self.db.mark_document_failed(doc.document_id, reason)
        self.metrics.documents_failed += 1
        self._update_job_metrics_from_status(doc.job_id, self.db.jobs[doc.job_id].status)

    # ------------------------------------------------------------------
    # ML orchestration helpers
    # ------------------------------------------------------------------
    def _classify_and_embed(
        self,
        docs: list[DocumentRecord],
        texts: list[str],
    ) -> list[dict[str, str]]:
        errors: list[dict[str, str]] = []
        if len(docs) != len(texts):
            raise ValueError("docs/texts length mismatch")
        if not docs:
            return errors

        with ThreadPoolExecutor(max_workers=2) as pool:
            t0 = time.time()
            f_cls = pool.submit(self.classifier.classify, texts)
            f_emb = pool.submit(self.embedder.embed, texts)

            labels: list[str] | None = None
            vectors: list[list[float]] | None = None

            try:
                labels = f_cls.result()
                self.metrics.classification_calls += 1
                self.metrics.classification_latency_ms.append((time.time() - t0) * 1000.0)
            except Exception as exc:
                self.metrics.classification_failures += 1
                for doc in docs:
                    errors.append({"document_id": doc.document_id, "error": f"classification failed: {exc}"})

            t1 = time.time()
            try:
                vectors = f_emb.result()
                self.metrics.embedding_calls += 1
                self.metrics.embedding_latency_ms.append((time.time() - t1) * 1000.0)
            except Exception as exc:
                self.metrics.embedding_failures += 1
                for doc in docs:
                    errors.append({"document_id": doc.document_id, "error": f"embedding failed: {exc}"})

        if labels is None or vectors is None:
            return dedupe_doc_errors(errors)

        if len(labels) != len(docs):
            for doc in docs:
                errors.append({"document_id": doc.document_id, "error": "classification output length mismatch"})
            return dedupe_doc_errors(errors)
        if len(vectors) != len(docs):
            for doc in docs:
                errors.append({"document_id": doc.document_id, "error": "embedding output length mismatch"})
            return dedupe_doc_errors(errors)

        for doc, label, vec in zip(docs, labels, vectors):
            self.db.write_result(DocumentResult(document_id=doc.document_id, label=label, embedding=vec))
            self.vector_store.upsert(
                doc.document_id,
                vec,
                {"job_id": doc.job_id, "user_id": doc.user_id, "filename": doc.filename, "label": label},
            )
        return []

    # ------------------------------------------------------------------
    # Response + metrics helpers
    # ------------------------------------------------------------------
    def _job_response(self, job: JobRecord, include_results: bool) -> dict[str, Any]:
        payload = {
            "job_id": job.job_id,
            "status": job.status.value,
            "processed_count": job.processed_files,
            "failed_count": job.failed_files,
            "total_count": job.total_files,
            "errors": list(job.errors),
        }
        if include_results:
            payload["results"] = self.db.get_job_results(job.job_id)
        return payload

    def _update_job_metrics_from_status(self, job_id: str, status: JobStatus) -> None:
        # best-effort counters (may be called more than once but only terminal states matter)
        if status not in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.PARTIAL):
            return
        if job_id in self._counted_terminal_jobs:
            return
        self._counted_terminal_jobs.add(job_id)
        if status == JobStatus.COMPLETED:
            self.metrics.jobs_completed += 1
        elif status == JobStatus.FAILED:
            self.metrics.jobs_failed += 1
        elif status == JobStatus.PARTIAL:
            self.metrics.jobs_partial += 1

    def metrics_snapshot(self) -> dict[str, Any]:
        return {
            "jobs_created": self.metrics.jobs_created,
            "jobs_completed": self.metrics.jobs_completed,
            "jobs_failed": self.metrics.jobs_failed,
            "jobs_partial": self.metrics.jobs_partial,
            "documents_processed": self.metrics.documents_processed,
            "documents_failed": self.metrics.documents_failed,
            "classification_calls": self.metrics.classification_calls,
            "embedding_calls": self.metrics.embedding_calls,
            "classification_failures": self.metrics.classification_failures,
            "embedding_failures": self.metrics.embedding_failures,
            "avg_classification_latency_ms": avg(self.metrics.classification_latency_ms),
            "avg_embedding_latency_ms": avg(self.metrics.embedding_latency_ms),
            "latest_queue_depth": self.metrics.queue_depth_samples[-1]
            if self.metrics.queue_depth_samples
            else 0,
        }


def dedupe_doc_errors(errors: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for e in errors:
        doc_id = e["document_id"]
        if doc_id in seen:
            continue
        seen.add(doc_id)
        out.append(e)
    return out


def avg(xs: list[float]) -> float:
    if not xs:
        return 0.0
    return sum(xs) / len(xs)


__all__ = [
    "PipelineSystem",
    "BlackBoxClassificationService",
    "BlackBoxEmbeddingService",
    "JobStatus",
    "DocumentStatus",
]
