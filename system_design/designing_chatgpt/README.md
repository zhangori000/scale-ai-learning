# Designing ChatGPT

This folder is a staged system design study track for designing a ChatGPT-like
product that uses OpenAI models.

The current path starts with storage because that is where we began the design
discussion. Later units can branch into request flow, streaming, APIs, caches,
queues, databases, sharding, edge delivery, and compute fleets.

## How this track is organized

- One unit per markdown file.
- Each unit uses simple `10^x` style estimation where possible.
- Each unit separates `official` statements from `inference`.
- The goal is not to guess OpenAI's private internals with false precision.
- The goal is to build a defensible mental model from public sources and rough
  systems reasoning.

## Current units

- [01 Storage Mental Model](./docs/01_storage_mental_model.md)
- [02 Estimating Text Conversations](./docs/02_estimating_text_conversations.md)
- [03 Why Files Dominate Storage](./docs/03_why_files_dominate_storage.md)
- [04 Database vs Object Storage](./docs/04_database_vs_object_storage.md)
- [05 Deletion Pipeline](./docs/05_deletion_pipeline.md)
- [06 Other Storage Buckets](./docs/06_other_storage_buckets.md)
- [07 GPUs, VRAM, and Weights](./docs/07_gpus_vram_and_weights.md)
- [08 Mapping Numbers to Components](./docs/08_mapping_numbers_to_components.md)
- [09 Defending the Baseline Stack](./docs/09_defending_the_baseline_stack.md)

## Near-term roadmap

These are the next likely directions for the study track:

- Connect back-of-the-envelope numbers to concrete system components.
- Decide when you need Postgres, Redis, object storage, queues, and caches.
- Decide when Kafka, Flink, Spark, or ScyllaDB are actually justified.
- Map streaming responses to edge, CDN, API gateway, and websocket/SSE choices.
- Introduce shards, replicas, buckets, fleets, and regional deployment.

## Working rules for future units

- Start from one bottleneck or requirement at a time.
- Tie every component choice back to a number or an operational need.
- Prefer "why this component exists" before "how to deploy it."
- Keep units small enough that each one teaches one architectural jump.
