from __future__ import annotations

import unittest

from pipeline_simulation import (
    BlackBoxClassificationService,
    BlackBoxEmbeddingService,
    JobStatus,
    PipelineSystem,
)


def make_files(n: int, suffix: str = ".txt") -> list[tuple[str, bytes]]:
    out = []
    for i in range(n):
        name = f"doc_{i}{suffix}"
        body = f"payment issue {i}" if i % 2 == 0 else f"general note {i}"
        out.append((name, body.encode("utf-8")))
    return out


class PipelineSimulationTest(unittest.TestCase):
    def test_sync_small_upload_success(self) -> None:
        system = PipelineSystem(
            classifier=BlackBoxClassificationService(latency_ms=1, failure_rate=0.0),
            embedder=BlackBoxEmbeddingService(latency_ms=1, failure_rate=0.0),
        )
        resp = system.post_documents_process("u1", make_files(3))
        self.assertIn(resp["status"], {"completed", "partial", "failed", "processing"})
        # sync path should finish by return time
        self.assertEqual(resp["status"], JobStatus.COMPLETED.value)
        self.assertEqual(resp["processed_count"], 3)
        self.assertEqual(resp["failed_count"], 0)
        self.assertEqual(len(resp["results"]), 3)

    def test_sync_partial_when_unsupported_file(self) -> None:
        system = PipelineSystem(
            classifier=BlackBoxClassificationService(latency_ms=1, failure_rate=0.0),
            embedder=BlackBoxEmbeddingService(latency_ms=1, failure_rate=0.0),
        )
        files = [
            ("good.txt", b"invoice approval"),
            ("bad.pdf", b"%PDF-1.4 fake"),
        ]
        resp = system.post_documents_process("u1", files)
        self.assertEqual(resp["status"], JobStatus.PARTIAL.value)
        self.assertEqual(resp["processed_count"], 1)
        self.assertEqual(resp["failed_count"], 1)

    def test_async_bulk_upload_success(self) -> None:
        system = PipelineSystem(
            classifier=BlackBoxClassificationService(latency_ms=1, failure_rate=0.0),
            embedder=BlackBoxEmbeddingService(latency_ms=1, failure_rate=0.0),
            max_retries=1,
        )
        system.start_workers(num_workers=2, batch_size=8, batch_wait_ms=10)
        try:
            up = system.post_documents_batch_upload("u1", make_files(20))
            job_id = up["job_id"]
            self.assertTrue(system.wait_until_queue_drained(timeout_s=5))
            status = system.get_job(job_id)
            self.assertEqual(status["status"], JobStatus.COMPLETED.value)
            self.assertEqual(status["processed_count"], 20)
            self.assertEqual(status["failed_count"], 0)
        finally:
            system.stop_workers()

    def test_async_retry_exhaustion_failed(self) -> None:
        # Force classification to fail always -> all docs fail after retries.
        system = PipelineSystem(
            classifier=BlackBoxClassificationService(latency_ms=1, failure_rate=1.0, seed=1),
            embedder=BlackBoxEmbeddingService(latency_ms=1, failure_rate=0.0),
            max_retries=1,
        )
        system.start_workers(num_workers=1, batch_size=4, batch_wait_ms=5)
        try:
            up = system.post_documents_batch_upload("u1", make_files(6))
            job_id = up["job_id"]
            self.assertTrue(system.wait_until_queue_drained(timeout_s=8))
            status = system.get_job(job_id)
            self.assertEqual(status["status"], JobStatus.FAILED.value)
            self.assertEqual(status["processed_count"], 0)
            self.assertEqual(status["failed_count"], 6)
        finally:
            system.stop_workers()

    def test_bulk_limit_validation(self) -> None:
        system = PipelineSystem()
        resp = system.post_documents_batch_upload("u1", make_files(1001))
        self.assertEqual(resp["status"], "error")
        self.assertIn("up to 1000", resp["message"])


if __name__ == "__main__":
    unittest.main()
