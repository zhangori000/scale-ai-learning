from __future__ import annotations

from pprint import pprint

from pipeline_simulation import (
    BlackBoxClassificationService,
    BlackBoxEmbeddingService,
    PipelineSystem,
)


def section(title: str) -> None:
    print("\n" + "=" * 14 + f" {title} " + "=" * 14)


def main() -> None:
    system = PipelineSystem(
        classifier=BlackBoxClassificationService(latency_ms=10, failure_rate=0.0),
        embedder=BlackBoxEmbeddingService(latency_ms=12, failure_rate=0.0),
        max_retries=1,
    )

    section("Synchronous Small Upload")
    small_files = [
        ("invoice.txt", b"Customer invoice payment issue."),
        ("policy.md", b"Please review updated contract policy."),
    ]
    sync_resp = system.post_documents_process(user_id="user-1", files=small_files)
    pprint(sync_resp)

    section("Async Bulk Upload")
    bulk_files = []
    for i in range(12):
        text = f"incident report {i}" if i % 3 == 0 else f"general memo {i}"
        bulk_files.append((f"doc_{i}.txt", text.encode("utf-8")))

    system.start_workers(num_workers=3, batch_size=6, batch_wait_ms=20)
    upload_resp = system.post_documents_batch_upload("user-1", bulk_files)
    pprint(upload_resp)
    system.wait_until_queue_drained(timeout_s=5)
    job_resp = system.get_job(upload_resp["job_id"])
    pprint(job_resp)

    section("Async Job Results")
    pprint(system.get_job_results(upload_resp["job_id"]))

    section("Semantic Search")
    hits = system.semantic_search("payment issue on invoice", top_k=3)
    pprint(hits)

    section("Metrics Snapshot")
    pprint(system.metrics_snapshot())

    system.stop_workers()


if __name__ == "__main__":
    main()
