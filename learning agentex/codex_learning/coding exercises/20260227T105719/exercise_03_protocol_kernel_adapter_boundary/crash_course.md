# Crash Course: Ground-Up Layering (Both Repos)

## Layer ranking (definitive)
1. **Layer 1 - Contract Kernel (most fundamental)**
   - ACP method contracts and payload schemas
   - stream update lifecycle contracts (`start/delta/full/done`)
   - deterministic state transition invariants
2. **Layer 2 - Port/Adapter Substrate (second most fundamental)**
   - interfaces for streams, persistence, and orchestration
   - Redis/Temporal/HTTP/DB adapters implementing those interfaces
3. **Layer 3 - Orchestration Use Cases**
   - task/message/event flows and aggregation logic
4. **Layer 4 - Delivery Surfaces**
   - FastAPI routes, generated SDK resources, CLI ergonomics

## Why this order is correct
1. Without Layer 1, nothing is interoperable.
2. Without Layer 2, Layer 1 cannot be executed in production.
3. Layer 3 is policy built on top of 1+2.
4. Layer 4 is presentation built on top of 1+2+3.

## What to memorize for interviews
1. Contracts first, adapters second.
2. Kernel logic must be deterministic and testable without I/O.
3. All side effects must go through ports.
4. Concurrency safety belongs at session/entity boundaries.
