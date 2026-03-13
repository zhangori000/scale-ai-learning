from __future__ import annotations

"""
This file mirrors docs' `acp.py` for Base Async ACP.
"""

from mock_fastacp import AsyncACPConfig, FastACP


acp = FastACP.create(
    acp_type="async",
    config=AsyncACPConfig(type="base"),
)
