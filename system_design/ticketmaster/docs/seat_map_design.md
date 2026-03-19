# The "Ghost Map" Architecture: Scaling Real-time Seat Status

To show 60,000 seats to 50,000 active shoppers, we use a layered approach that separates static assets from dynamic state.

## 1. Layered Data Model

| Layer | Type | Data | Size | TTL | Delivery |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Layer 1: Static** | Asset | SVG/JSON coordinates, section shapes. | 2-5 MB | 24 Hours | CDN Edge (Immutable) |
| **Layer 2: Status** | State | 2-bit state per seat (0=Free, 1=Lock, 2=Sold). | ~15 KB | 1-2 Sec | CDN Edge (Mutable) |

## 2. Real-time Synchronization Strategy

### Phase A: The CDN Polling Baseline (Efficiency)
- **Problem:** 50,000 users = 25,000 RPS. Origin servers cannot handle this.
- **Solution:** `StatusGenerator` writes the 15KB bitmask to the CDN every 1 second.
- **Polling:** Browsers fetch `latest.json` every 2 seconds. The CDN handles the 25,000 RPS, protecting our backend.

### Phase B: Server-Sent Events (SSE) Deltas (Freshness)
- **Refinement:** To reduce the 2-second "Ghost" effect, we use **one-way SSE**.
- **Scope:** Users only subscribe to the **Section** they are viewing (e.g., `sse/section/101`).
- **Fan-out:** Instead of 50,000 users, we only push updates to the ~500 users looking at Section 101. 
- **Delta Format:** We only send the *changes* (e.g., `{"seat": "A15", "status": "LOCKED"}`).

### Phase C: Optimistic UI (UX)
- When a user clicks a seat, the UI shows a "Holding..." spinner immediately (**Prediction**).
- The `SeatSelectionService` returns the **Truth** (Success/Failure) in the direct HTTP response.
- The UI updates the local seat color instantly based on this response, **not** the next CDN poll.

## 3. Gaming vs. Ticketing: Why no UDP?

| Feature | League of Legends (UDP) | Ticketmaster (HTTP/TCP) |
| :--- | :--- | :--- |
| **Consistency** | Eventual (Latest frame wins) | **Strict** (Cannot double-sell) |
| **Audience** | 10 Players per match | 50,000+ per event |
| **Infrastructure** | Regional Edge Servers | Global CDNs |
| **Cost** | High Per-User Cost | Low Per-User Cost (Scale) |

**Conclusion:** We use **TCP/HTTP** because we need the reliability and the CDN caching layer. We borrow the **Delta Compression** and **Optimistic UI** patterns from games to make the web feel "live."
