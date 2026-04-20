import os
import re
from datetime import date
from pathlib import Path
from typing import Annotated, Optional, Dict, Any

import typer
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from rich.console import Console

from local_first_common.providers import PROVIDERS
from local_first_common.cli import (
    provider_option,
    model_option,
    dry_run_option,
    no_llm_option,
    verbose_option,
    debug_option,
    resolve_provider,
    resolve_dry_run,
)
from local_first_common.tracking import register_tool, timed_run

from .schema import VideoSummary
from .prompts import build_system_prompt, build_user_prompt

_TOOL = register_tool("yt-transcription-summarizer")


class YtSummarizerError(Exception):
    """Base typed error for yt-transcription-summarizer."""


class VideoFetchError(YtSummarizerError):
    """Raised when video metadata or transcript fetch fails."""


class ProviderSetupError(YtSummarizerError):
    """Raised when provider resolution fails."""


class LLMRunError(YtSummarizerError):
    """Raised when the LLM summarization call fails."""


console = Console()
app = typer.Typer(
    help="YouTube Transcription Summarizer — fetch a YouTube transcript and create an Obsidian resource note."
)


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
        }


def get_transcript(video_id: str) -> str:
    """Fetch transcript using youtube-transcript-api."""
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id)
        return " ".join([snippet.text for snippet in fetched])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript: {e}")


def format_obsidian_note(summary: VideoSummary, url: str) -> str:
    """Format the summary into an Obsidian markdown note."""
    today = date.today().isoformat()
    concepts = "\n".join(
        [f"- **{c.timestamp}**: {c.concept}" for c in summary.key_concepts]
    )
    quotes = "\n".join([f"> {q}" for q in summary.key_quotes])

    note = f"""---
date: {today}
source_url: {url}
video_title: "{summary.video_title}"
channel: "{summary.channel}"
category: "[[YouTube]]"
---

# {summary.video_title}

## Summary
{summary.summary}

## Key Concepts
{concepts}

## Key Quotes
{quotes}
"""
    return note


@app.command()
def summarize(
    url: str = typer.Argument(..., help="YouTube video URL."),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Target folder for the note."
    ),
    provider: Annotated[str, provider_option(PROVIDERS)] = os.environ.get(
        "MODEL_PROVIDER", "ollama"
    ),
    model: Annotated[Optional[str], model_option()] = None,
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    verbose: Annotated[bool, verbose_option()] = False,
    debug: Annotated[bool, debug_option()] = False,
):
    """Summarize a YouTube video."""
    dry_run = resolve_dry_run(dry_run, no_llm)

    try:
        video_id = extract_video_id(url)
        if verbose:
            console.print(f"Fetching info for video {video_id}...")
        video_info = get_video_info(url)

        if verbose:
            console.print(f"Fetching transcript for {video_info['title']}...")
        transcript = get_transcript(video_id)
    except VideoFetchError as e:
        console.print(f"[red]Error fetching video data: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error fetching video data: {e}[/red]")
        raise typer.Exit(1)

    try:
        llm = resolve_provider(PROVIDERS, provider, model, debug=debug, no_llm=no_llm)
    except ProviderSetupError as e:
        console.print(f"[red]Error initializing provider: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error initializing provider: {e}[/red]")
        raise typer.Exit(1)

    system = build_system_prompt()
    user = build_user_prompt(video_info, transcript)

    if verbose:
        console.print(f"Summarizing using {llm.model}...")

    try:
        with timed_run(
            "yt-transcription-summarizer", llm.model, source_location=url
        ) as run:
            response = llm.complete(system, user, response_model=VideoSummary)
            summary = (
                response
                if isinstance(response, VideoSummary)
                else VideoSummary(**response)
            )
            run.item_count = 1
    except LLMRunError as e:
        console.print(f"[red]Error during LLM processing: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error during LLM processing: {e}[/red]")
        raise typer.Exit(1)

    note_content = format_obsidian_note(summary, url)

    if dry_run:
        console.print("\n[bold yellow][dry-run] Generated Note:[/bold yellow]")
        console.print(note_content)
    else:
        vault_path_str = os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault_path_str:
            console.print(
                "[red]Error: OBSIDIAN_VAULT_PATH not set. Printing to stdout.[/red]"
            )
            console.print(note_content)
            return

        vault_path = Path(vault_path_str)
        target_path = (
            output_dir
            if output_dir and output_dir.is_absolute()
            else (vault_path / (output_dir or "youtube"))
        )
        target_path.mkdir(parents=True, exist_ok=True)

        filename = f"{re.sub(r'[\\/*?:\'\"<>|]', '', summary.video_title)}.md"
        file_path = target_path / filename

        file_path.write_text(note_content)
        console.print(f"[green]Note saved to: {file_path}[/green]")


if __name__ == "__main__":
    app()
