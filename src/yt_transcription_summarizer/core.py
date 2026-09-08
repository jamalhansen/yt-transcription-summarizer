import re
from datetime import date, datetime
from typing import Any, Dict

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

from .schema import VideoSummary


class YtSummarizerError(Exception):
    """Base typed error for yt-transcription-summarizer."""


class VideoFetchError(YtSummarizerError):
    """Raised when video metadata or transcript fetch fails."""


class ProviderSetupError(YtSummarizerError):
    """Raised when provider resolution fails."""


class LLMRunError(YtSummarizerError):
    """Raised when the LLM summarization call fails."""


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_video_info(url: str) -> Dict[str, Any]:
    """Get video metadata using yt-dlp."""
    ydl_opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "channel": info.get("uploader"),
            "url": url,
            "id": info.get("id"),
            "upload_date": info.get("upload_date"),  # YYYYMMDD
        }


def get_transcript(video_id: str) -> str:
    """Fetch transcript using youtube-transcript-api."""
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id)
        return " ".join([snippet.text for snippet in fetched])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript: {e}")


def _format_apa_citation(
    channel: str, upload_date: str | None, title: str, url: str
) -> str:
    """Build an APA 7 citation for a YouTube video."""
    if upload_date:
        d = datetime.strptime(upload_date, "%Y%m%d")
        date_str = d.strftime("%Y, %B ") + str(d.day)
    else:
        date_str = "n.d."
    return f"{channel}. ({date_str}). *{title}* [Video]. YouTube. {url}"


def format_obsidian_note(
    summary: VideoSummary, url: str, upload_date: str | None = None
) -> str:
    """Format the summary into an Obsidian markdown note."""
    today = date.today().isoformat()
    concepts = "\n".join(
        [f"- **{c.timestamp}**: {c.concept}" for c in summary.key_concepts]
    )
    quotes = "\n".join([f"> {q}" for q in summary.key_quotes])
    citation = _format_apa_citation(
        summary.channel, upload_date, summary.video_title, url
    )

    note = f"""---
date: {today}
source_url: {url}
video_title: "{summary.video_title}"
channel: "{summary.channel}"
category: "[[YouTube]]"
---

## Citation
{citation}

# {summary.video_title}

## Summary
{summary.summary}

## Key Concepts
{concepts}

## Key Quotes
{quotes}
"""
    return note
