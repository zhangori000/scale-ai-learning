from __future__ import annotations

# --- Patterns from Scale-Agentex: Custom Domain Exceptions ---

class TikTokError(Exception):
    """Base exception for all TikTok related errors"""
    pass

class InteractionError(TikTokError):
    """Base exception for interaction related errors"""
    pass

class IdempotencyError(InteractionError):
    """Raised when a request with the same request_id is processed twice"""
    pass

class TargetNotFoundError(InteractionError):
    """Raised when the video or comment being interacted with does not exist"""
    pass
