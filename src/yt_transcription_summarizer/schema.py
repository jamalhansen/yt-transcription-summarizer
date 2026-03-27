from typing import List
from pydantic import BaseModel, Field

class TimestampedConcept(BaseModel):
    timestamp: str = Field(..., description="Timestamp in format HH:MM:SS or MM:SS")
    concept: str

class VideoSummary(BaseModel):
    video_title: str
    channel: str
    summary: str
    key_concepts: List[TimestampedConcept]
    key_quotes: List[str] = Field(..., min_length=3, max_length=3)
