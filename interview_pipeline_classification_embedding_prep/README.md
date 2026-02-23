# Classification + Embedding Pipeline Prep Pack

This folder contains a complete interview-prep package:

1. Conceptual system design notes
2. Mock interview response scripts
3. Runnable Python simulation code

## Files

- `CONCEPTS.md` - architecture, scaling, reliability, observability
- `INTERVIEW_MOCK_RESPONSES.md` - spoken answer templates
- `pipeline_simulation.py` - end-to-end simulation
- `test_pipeline_simulation.py` - unit tests
- `demo.py` - quick demo run

## What the simulation includes

- Sync endpoint simulation for small uploads
- Async bulk endpoint simulation for up to 1,000 files
- Object store + metadata DB + vector store abstractions
- Queue + worker pool for async processing
- Batched classification/embedding calls
- Retry and per-document failure handling
- Job status tracking (`queued/processing/completed/failed/partial`)
- Basic semantic search over stored embeddings
- Metrics snapshot

## Run tests

```bash
python -m unittest test_pipeline_simulation.py -v
```

## Run demo

```bash
python demo.py
```

## Interview usage tip

When asked "design this system", first state:

1. split sync vs async API strategy
2. storage model (object + metadata + vector)
3. queue/worker orchestration
4. failure model and observability
