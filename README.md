# YouTube Transcription Summarizer

Fetches a YouTube transcript, extracts key concepts with timestamps, and generates a structured Obsidian resource note.

## Features
- **Transcript Fetching**: Automatically retrieves transcripts using `youtube-transcript-api`.
- **Metadata Extraction**: Uses `yt-dlp` for video titles and channel names.
- **Timestamped Concepts**: Correlates key concepts with specific parts of the video.
- **Obsidian Integration**: Saves notes with YAML frontmatter directly to your vault.

## Installation
```bash
uv sync
```

## Usage
```bash
export OBSIDIAN_VAULT_PATH="/path/to/your/vault"
uv run yt-summarize "https://www.youtube.com/watch?v=..."
```

Standard flags supported: `--dry-run`, `--no-llm`, `--provider`, `--model`.
