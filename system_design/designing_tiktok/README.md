# TikTok System Design & Backend Practical

This folder contains a complete breakdown of the TikTok "Watch Path" and a production-grade Python simulation.

## 📂 Folder Structure
- `/docs`: Detailed System Design documentation.
    - `01_architecture.md`: Covers the high-level flow, LSM Trees, and Scaling.
- `/src`: Python implementation showing "Senior-Level" backend patterns.
    - `app.py`: FastAPI server with Middleware and Dependency Injection.
    - `models/schemas.py`: Pydantic validation.
    - `services/recommendation.py`: Async parallel retrieval logic.

## 🚀 Key Practical Lessons (Python)
1.  **Concurrency (`asyncio.gather`):** See `recommendation.py`. Learn how to hit multiple databases in parallel to keep latency under 200ms.
2.  **Dependency Injection (`Depends`):** See `app.py`. Learn how to pass services into endpoints for better testability.
3.  **Fail-Fast Validation (`Pydantic`):** See `schemas.py`. Learn why type-hints alone aren't enough for production data.
4.  **Background Tasks:** See `log_telemetry`. Learn how to offload "expensive" logging to Kafka/Flink without slowing down the user.
5.  **Middleware:** See `app.py`. Learn how to track latency for every request automatically.

## 🛠️ How to run (Optional)
If you have `fastapi` and `uvicorn` installed:
```bash
cd system_design/designing_tiktok
python -m src.app
```
Then send a POST request to `http://localhost:8000/v1/feed` with:
```json
{
    "user_id": "bob_123",
    "count": 10
}
```
