# Unit 8: Mapping Back-of-the-Envelope Numbers to System Components

This unit answers the first practical architecture question:

- given the numbers from the storage units, what components do we actually need?

The main rule is:

- do not start from tools
- start from jobs the system must perform

Then choose the smallest set of components that covers those jobs.

## New words

`system of record`

- the place where the canonical truth lives

`hot path`

- the request path that directly affects user latency

`replay`

- the ability to read old events again later

`event-time`

- processing events based on when they happened, not when they arrived

## The first component map

For a ChatGPT-like app that uses OpenAI, the first major jobs are:

1. store users, chats, messages, settings, and permissions
2. store large uploaded files and images
3. keep a few things hot in memory for low latency
4. run background work outside the request path
5. deliver static assets globally

That already suggests a baseline stack:

- `Postgres` for relational system-of-record data
- `Object storage` for large blobs/files
- `Redis` for hot ephemeral state and caching
- `Background workers + queue` for async tasks
- `CDN` for static/public asset delivery

This is the "start here" stack.

For most early designs, do **not** begin with:

- Kafka
- Flink
- Spark
- ScyllaDB

Those can become justified later, but not just because they are popular.

## What Postgres is for

PostgreSQL's docs explain two properties that matter immediately:

- `MVCC`: read and write concurrency without readers blocking writers
- `WAL`: durable commit and crash recovery through write-ahead logging

That makes Postgres a strong first choice for:

- users
- accounts
- chat threads
- messages
- saved memories metadata
- file metadata
- billing/subscription metadata
- delete jobs and retention metadata

Back-of-the-envelope check:

Suppose you store:

- `10^8` messages
- `10^3 bytes/message`

That is:

- `10^8 * 10^3 = 10^11 bytes = 100 GB`

That is large, but still a very normal database scale for a serious production
system, especially before attachments dominate.

### When Postgres is a good fit

- you need transactions
- you need relational queries
- you need consistency for core product state
- your request pattern is mostly CRUD plus indexes

### When Postgres is not enough by itself

- the blob payloads become huge
- you need ultra-hot ephemeral counters or rate limits at very high request rates
- you need durable replayable event streams for many consumers

## What object storage is for

Use object storage from day 1 for:

- uploads
- images
- PDFs
- exports
- logs/checkpoints/archives

From prior units, a single file can be larger than thousands of medium chats.
That is why blob bytes should not live in the main relational store.

Official S3 docs also matter here because they show production-friendly storage
behaviors:

- buckets
- versioning
- lifecycle rules
- delete markers

These map cleanly to retention and deletion workflows.

### Simple size intuition

Suppose:

- `10^6` uploaded files
- average size `10^7 bytes = 10 MB`

Then blob storage is:

- `10^6 * 10^7 = 10^13 bytes = 10 TB`

That is exactly the kind of storage that belongs in object storage, not in
Postgres rows.

## What Redis is for

Redis is useful because it gives very fast access to in-memory data structures.
Its own docs explicitly frame Redis as a data structure store, and it supports
strings, hashes, sets, sorted sets, streams, and more.

Good first uses:

- session and auth-adjacent state
- request rate limiting
- idempotency keys
- hot chat/thread caches
- presence / "user is online"
- short-lived job coordination
- counters and rolling windows

Bad first use:

- the only durable source of truth for chats or accounts

Why not? Redis docs are very explicit that persistence is a tradeoff. RDB is
snapshot-based, AOF is more durable but larger/slower, and disabling
persistence entirely is sometimes used for caching.

That means the right beginner mental model is:

- Redis is for `speed`
- Postgres is for `truth`

### A simple heuristic

If losing a few seconds or minutes of this data would be unacceptable, Redis
alone is probably the wrong home for it.

## What a CDN is for

A CDN is for data that many users can fetch repeatedly from edge locations:

- JS/CSS bundles
- images
- static media
- maybe downloadable public assets

Cloudflare's cache docs are useful here because they also show what a CDN does
**not** cache by default:

- non-GET requests
- `private`, `no-store`, `no-cache`, `max-age=0`
- responses with `Set-Cookie` in key default cases
- HTML/JSON are not cached by default

That leads to an important design lesson:

- your private chat API responses are usually **not** a CDN caching problem
- your static assets and media delivery **are**

So when someone says "put ChatGPT behind a CDN", the precise answer is:

- yes for assets
- not as the primary storage or truth layer for private chat data

## What edge workers are for

Cloudflare Workers are useful close to the edge for:

- request normalization
- light auth checks
- bot filtering
- geo routing
- signed URL generation
- API gateway-style logic

They are not the main home for:

- long-lived relational state
- huge file storage
- heavy transactional coordination

This is another frequent beginner confusion:

- edge compute helps the edges of the system
- it does not replace the core databases

## What background queues are for

Some work should leave the hot path:

- virus scanning uploads
- OCR / text extraction
- thumbnail generation
- moderation fan-out
- export generation
- delayed deletes
- analytics event shipping

This is where a queue + workers help, even before Kafka enters the picture.

`Inference`: the exact first queue technology is a product choice. The design
principle is more important than the specific tool:

- request path should stay short
- slow or retry-heavy work moves to background jobs

## When Kafka becomes justified

Kafka's docs describe a durable event stream with:

- topics
- partitions
- retention independent of consumption
- replay
- multiple producers and multiple consumers

Kafka becomes justified when you need something like:

- many independent downstream consumers
- durable retained event history
- replay
- ordered partitions by key
- very large event throughput

Examples:

- analytics pipeline
- moderation pipeline
- billing/audit event stream
- model feedback stream
- many teams consuming the same event history

### When Kafka is probably overkill

If your architecture is:

- web app
- one worker pool
- one analytics sink

then a simpler queue is often enough.

The presence of "events" does **not** automatically imply Kafka.

## When Flink becomes justified

Flink's docs are about stateful stream processing, checkpoints, and exact or
near-exact recovery behavior. Flink becomes useful when the problem is not just
"move events", but:

- keep large keyed state
- do windowed aggregations
- use event-time
- recover from checkpoints
- continuously update live aggregates

Typical examples:

- rolling abuse/risk scores
- real-time per-model or per-tenant usage windows
- stream joins
- complex event detection

In most early ChatGPT-like designs:

- Kafka may come before Flink
- Flink comes only if the streaming computation becomes stateful and important

## When Spark becomes justified

Spark's Structured Streaming docs explicitly describe a scalable and
fault-tolerant engine, but Spark is still most naturally thought of as:

- batch analytics
- ETL
- large historical processing
- data science / offline pipelines

Good uses:

- training-data preparation
- large usage reports
- offline analytics
- periodic backfills

Spark is usually not your core online request path.

## When ScyllaDB becomes justified

ScyllaDB's docs describe it as a distributed wide-column database for
data-intensive applications, and its docs also describe a shared-nothing, one
shard-per-core model.

That points to the kind of problems where ScyllaDB can make sense:

- very high write throughput
- key-based access patterns
- predictable low-latency at large scale
- wide-column/time-series-ish or feed/event data

It is usually **not** the first choice when the core data looks like:

- users
- accounts
- permissions
- transactional relational metadata

So for a ChatGPT-like app, ScyllaDB is more likely to appear in a specialized
high-scale subsystem than as the first database.

## A concrete "start here" architecture

For an early serious product, a strong baseline is:

- `Postgres` as system of record
- `Object storage` for files and large blobs
- `Redis` for hot ephemeral state
- `Workers + queue` for background jobs
- `CDN` for static assets and public media

This covers the main needs introduced in Units 1 through 7.

## What not to add yet

Do not add Kafka just because events exist.
Do not add Flink just because analytics exist.
Do not add Spark just because data exists.
Do not add ScyllaDB just because scale might grow later.

Add them only when the problem statement changes.

## Decision cheat sheet

Use `Postgres` when:

- you need transactions and relational truth

Use `Object storage` when:

- you are storing large blobs/files

Use `Redis` when:

- you need very fast ephemeral shared state

Use `CDN` when:

- many users fetch the same static or public content

Use `Kafka` when:

- you need durable replayable event streams for many consumers

Use `Flink` when:

- you need stateful real-time stream processing

Use `Spark` when:

- you need large batch analytics or ETL

Use `ScyllaDB` when:

- you need very high-scale distributed key-based serving and the relational
  model is the bottleneck

## Main takeaway

For the first serious version of a ChatGPT-like system that uses OpenAI, the
default answer is usually:

- Postgres
- object storage
- Redis
- queue/workers
- CDN

Everything else has to earn its way in.

## Sources

- PostgreSQL concurrency docs: https://www.postgresql.org/docs/current/mvcc.html
- PostgreSQL WAL docs: https://www.postgresql.org/docs/current/wal-intro.html
- Redis data types docs: https://redis.io/docs/latest/develop/data-types/
- Redis persistence docs: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- Redis replication docs: https://redis.io/docs/latest/operate/oss_and_stack/management/replication/
- Amazon S3 versioning docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
- Amazon S3 lifecycle docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-configuration-bucket-no-versioning.html
- Apache Kafka intro: https://kafka.apache.org/intro/
- Apache Flink stateful stream processing docs: https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/concepts/stateful-stream-processing/
- Apache Spark Structured Streaming docs: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- Cloudflare Cache docs: https://developers.cloudflare.com/cache/
- Cloudflare default cache behavior docs: https://developers.cloudflare.com/cache/concepts/default-cache-behavior/
- Cloudflare Workers overview: https://developers.cloudflare.com/workers/
- ScyllaDB docs root: https://docs.scylladb.com/manual/stable/
- ScyllaDB gossip internals: https://docs.scylladb.com/manual/master/kb/gossip.html
