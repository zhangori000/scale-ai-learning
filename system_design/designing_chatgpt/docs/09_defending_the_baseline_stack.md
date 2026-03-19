# Unit 9: Defending the Baseline Stack in an Interview

This unit is about turning the component list into an interview-quality
explanation.

Your problem right now is probably not:

- "I do not know the names of the components"

It is more likely:

- "I cannot defend why each component exists"
- "I cannot explain the tradeoff if an interviewer attacks the choice"

That is what this unit fixes.

## The baseline stack we are defending

For a serious early ChatGPT-like product that uses OpenAI, our current baseline
is:

- `Postgres` for relational system-of-record data
- `Object storage` for files and large blobs
- `Redis` for hot ephemeral shared state
- `Queue + workers` for async background jobs
- `CDN` for static assets and public media

This is not "the only possible design."
It is the default design that is easiest to defend.

## The interview answer template

When an interviewer asks "why this component?", use this 5-part template:

1. say the job
2. say why this tool fits that job
3. say what you are explicitly not using it for
4. say the main tradeoff
5. say what scale/change would force a redesign

Example:

- "I use Redis for hot ephemeral state such as rate limiting and request
  coordination because it is fast and in-memory. I am not using it as the
  durable source of truth for chats. The tradeoff is weaker durability than
  Postgres. If that hot state grows into durable multi-consumer event history,
  I would introduce Kafka or move the workload elsewhere."

That is already much stronger than:

- "Redis is fast."

## The one-sentence system story

You should be able to say this cleanly:

- "The canonical chat/account metadata lives in Postgres, large uploads live in
  object storage, Redis keeps only hot ephemeral state, background workers handle
  slow and retryable jobs, and the CDN serves static assets and public media
  close to users."

If you can say that without hesitation, you already sound much more grounded.

## Component-by-component defense

### 1. Postgres

#### Precise job

Postgres is the `system of record` for:

- users
- accounts
- chat threads
- messages
- file metadata
- permissions
- billing/subscription metadata
- deletion and retention metadata

#### Why it fits

PostgreSQL docs emphasize:

- concurrency control for multiple sessions
- `WAL` durability and crash recovery

That matches the core app data model because the system needs:

- transactions
- foreign-key-style relationships
- consistent updates
- indexed lookups

#### What it is not for

Do not use Postgres as the primary home for:

- giant binary file payloads
- extremely hot ephemeral counters if Redis is a better fit
- durable multi-team event replay

#### Tradeoff

Postgres gives you strong transactional structure, but it is not the best
primitive for every workload. Large blobs and ultra-hot cache-like access
patterns can make it more expensive or awkward than specialized systems.

#### Interview attack

"Why not store everything in Postgres?"

Strong answer:

- "Because the jobs are different. Relational truth fits Postgres, but file
  payloads are much larger than metadata and belong in object storage. Also,
  some latency-sensitive ephemeral state is better served from Redis than from
  repeated database reads. I want Postgres to own the canonical relational
  state, not every byte in the system."

### 2. Object storage

#### Precise job

Object storage holds:

- uploaded images
- PDFs
- exports
- media blobs
- archival artifacts

#### Why it fits

Large files scale by bytes, not by row count. From earlier units:

- one large file can outweigh thousands of medium chats

Object storage is built for:

- large blobs
- cheap durable storage
- lifecycle rules
- versioning/delete-marker style semantics

#### What it is not for

Do not use object storage as the main query engine for:

- list my recent chats
- permission checks
- relational joins
- transactional metadata updates

#### Tradeoff

Object storage is cheap and scalable for blobs, but not good for relational
queries or low-latency transactional updates.

#### Interview attack

"Why not just store file bytes in Postgres?"

Strong answer:

- "Because file bytes and relational metadata have very different access
  patterns and scales. Postgres should answer structured queries, while object
  storage should hold heavy blob payloads. That keeps the transactional store
  smaller and easier to operate."

### 3. Redis

#### Precise job

Redis is for hot ephemeral shared state such as:

- rate limiting
- idempotency keys
- short-lived session or request coordination
- presence
- counters
- hot caches

#### Why it fits

Redis is an in-memory data structure store, so it is excellent when:

- latency matters
- the access pattern is simple
- the state is shared across app instances

#### What it is not for

Do not make Redis the only durable source of truth for:

- chat history
- accounts
- billing
- anything where a small durability gap is unacceptable

Redis docs are explicit about persistence tradeoffs:

- `RDB` snapshots can lose recent writes
- `AOF` is more durable but larger/slower
- no persistence is common for cache-like use cases

Redis replication docs also explicitly say Redis uses asynchronous replication by
default and that acknowledged writes can still be lost depending on persistence
configuration.

#### Tradeoff

Redis buys speed by being in-memory and simpler. The cost is weaker durability
and consistency guarantees than your transactional database.

#### Interview attack

"Why not keep chats in Redis if it is faster?"

Strong answer:

- "Because fast is not the only requirement. Chats are durable user data and I
  need canonical truth, not just low latency. I would cache hot chat summaries
  or recent threads in Redis, but the authoritative copy should live in
  Postgres."

### 4. Queue + workers

#### Precise job

Queue-backed workers handle:

- OCR and text extraction
- thumbnail generation
- moderation fan-out
- data exports
- delayed deletion
- analytics shipping
- retry-heavy side effects

#### Why it fits

These jobs are:

- slower than the request path should tolerate
- often retried
- sometimes parallelizable
- often not needed before sending the first response to the user

#### What it is not for

Do not put core synchronous request handling into a worker unless you are
willing to pay the latency and complexity cost.

#### Tradeoff

Workers decouple slow work from user latency, but add eventual consistency and
operational complexity.

#### Interview attack

"Why not do OCR or moderation inline?"

Strong answer:

- "If it blocks the main user path, tail latency gets worse immediately. I keep
  the hot path short and move retryable heavy work into background workers. I
  only keep work inline if the product semantics require it before the response
  can be shown."

### 5. CDN

#### Precise job

The CDN is for:

- JS/CSS bundles
- images
- public media
- repeated static fetches close to users

#### Why it fits

Cloudflare's docs make two important things clear:

- it caches static assets very naturally
- it does **not** cache private chat-style dynamic responses by default

Specifically, Cloudflare documents that it does not cache when:

- the request is not `GET`
- the response is marked `private`, `no-store`, `no-cache`, or `max-age=0`
- `Set-Cookie` is present in important default cases

It also documents that HTML and JSON are not cached by default.

#### What it is not for

Do not describe the CDN as if it is the source of truth for private chat data.

#### Tradeoff

CDNs reduce latency and origin load for shared/static content, but they are not
the primary solution for authenticated per-user chat state.

#### Interview attack

"Why do you need a CDN if chats are dynamic?"

Strong answer:

- "I do not need the CDN mainly for the private chat JSON. I need it for static
  frontend assets and public or semi-public media delivery. Those requests are
  highly cacheable and globally distributed. The private conversation state
  still comes from the application and core stores."

## The hardest follow-up: why not use one tool for everything?

Interviewers often attack here because they want to see if you understand
specialization.

The core answer is:

- different data has different access patterns, durability needs, and cost
  profiles

More precise version:

- relational truth needs transactions and consistency
- large files need cheap durable blob storage
- ephemeral shared state needs low-latency memory access
- slow side effects need asynchronous execution
- static global delivery needs edge caching

That is why multiple components exist.

## What breaks if you remove each component?

If you remove `Postgres`:

- you lose the clean system of record for core relational state

If you remove `Object storage`:

- your main data store gets polluted with heavy blobs

If you remove `Redis`:

- more traffic hits the primary store and rate limiting/hot-state paths get
  slower or harder

If you remove `Workers`:

- slow jobs move into the hot path and latency gets worse

If you remove `CDN`:

- static asset latency and origin load both worsen

That is a useful way to defend necessity.

## What makes the stack evolve later?

The right answer is not "future scale."
The right answer is a more precise trigger.

Examples:

- introduce `Kafka` when many consumers need durable replayable event streams
- introduce `Flink` when you need stateful real-time stream computation
- introduce `Spark` when batch ETL/offline analytics become large and regular
- introduce `ScyllaDB` only when a specialized high-scale key-value or
  wide-column workload outgrows the relational model

That sounds more mature than:

- "we can always add Kafka later"

## A compact interview script

If pressed for a short answer, say:

- "I separate the system by workload. Postgres holds canonical relational truth
  like users, chats, and metadata. Object storage holds heavy uploads. Redis is
  only for hot ephemeral shared state like rate limits and caches. Workers
  handle slow or retryable side effects off the hot path. The CDN serves static
  assets and media near users. I avoid Kafka/Flink/Scylla until the workload
  specifically demands replayable streams, stateful streaming, or distributed
  key-based serving."

That is already a strong interview answer.

## Mini drills

You should be able to answer these in 2 to 4 sentences each:

1. Why not keep chat history only in Redis?
2. Why not store uploads inside Postgres rows?
3. Why do you still need a CDN if the chat responses are dynamic?
4. What work should leave the request path first?
5. What precise workload would justify Kafka?

If you cannot answer these yet, reread this unit and try again out loud.

## Main takeaway

Interview strength comes from being able to say, for each component:

- what job it owns
- why it fits that job
- what it does not own
- what tradeoff it introduces
- what future trigger would replace or complement it

That is the difference between naming tools and actually defending a design.

## Sources

- PostgreSQL concurrency docs: https://www.postgresql.org/docs/current/mvcc.html
- PostgreSQL WAL docs: https://www.postgresql.org/docs/current/wal-intro.html
- Redis persistence docs: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- Redis replication docs: https://redis.io/docs/latest/operate/oss_and_stack/management/replication/
- Amazon S3 delete marker docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeleteMarker.html
- Amazon S3 lifecycle expiration docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html
- Apache Kafka intro: https://kafka.apache.org/intro/
- Cloudflare default cache behavior docs: https://developers.cloudflare.com/cache/concepts/default-cache-behavior/
