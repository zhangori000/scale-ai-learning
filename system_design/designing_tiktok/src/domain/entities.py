from __future__ import annotations
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# --- Patterns from Scale-Agentex: Strict Typing & Pydantic Entities ---

class InteractionType(str, Enum):
    LIKE = "LIKE"
    SAVE = "SAVE"
    SHARE = "SHARE"
    COMMENT = "COMMENT"
    COMMENT_LIKE = "COMMENT_LIKE"
    TIP = "TIP"
    GIFT = "GIFT"

class Interaction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    target_id: str # Can be Video_ID or Comment_ID
    type: InteractionType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None # For Idempotency

class Comment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video_id: str
    user_id: str
    parent_id: Optional[str] = "root" # Level 1 is "root", Level 2 is Top-Level Comment_ID
    text: str
    likes: int = 0
    is_hidden: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class UserProfile(BaseModel):
    user_id: str
    username: str
    bio: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
