from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner
from yt_transcription_summarizer.logic import app, extract_video_id, format_obsidian_note
from yt_transcription_summarizer.schema import VideoSummary, TimestampedConcept

runner = CliRunner()

def test_extract_video_id():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    with pytest.raises(ValueError):
        extract_video_id("invalid-url")

def test_format_obsidian_note():
    summary = VideoSummary(
        video_title="Never Gonna Give You Up",
        channel="Rick Astley",
        summary="A classic song.",
        key_concepts=[TimestampedConcept(timestamp="0:00", concept="Introduction")],
        key_quotes=["Never gonna give you up", "Never gonna let you down", "Never gonna run around"]
    )
    note = format_obsidian_note(summary, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert "Never Gonna Give You Up" in note
    assert "Rick Astley" in note
    assert "0:00" in note

@patch("yt_transcription_summarizer.logic.get_transcript")
@patch("yt_transcription_summarizer.logic.get_video_info")
@patch("yt_transcription_summarizer.logic.resolve_provider")
@patch("yt_transcription_summarizer.logic.timed_run")
def test_summarize_command(mock_timed_run, mock_resolve_provider, mock_get_info, mock_get_transcript):
    mock_get_info.return_value = {
        "title": "Test Video",
        "channel": "Test Channel",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "id": "dQw4w9WgXcQ"
    }
    mock_get_transcript.return_value = "This is a test transcript."

    mock_llm = MagicMock()
    mock_llm.model = "mock-model"
    mock_llm.complete.return_value = VideoSummary(
        video_title="Test Video",
        channel="Test Channel",
        summary="Test summary.",
        key_concepts=[],
        key_quotes=["Quote 1", "Quote 2", "Quote 3"]
    )
    mock_resolve_provider.return_value = mock_llm
    mock_timed_run.return_value.__enter__.return_value = MagicMock()

    result = runner.invoke(app, ["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "--no-llm", "--dry-run"])
    
    assert result.exit_code == 0
    assert "Test Video" in result.stdout
    assert "Generated Note:" in result.stdout
