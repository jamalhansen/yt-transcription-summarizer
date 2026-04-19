from yt_transcription_summarizer.logic import (
    extract_video_id,
    YtSummarizerError,
    VideoFetchError,
    ProviderSetupError,
    LLMRunError,
)


def test_extract_video_id():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


class TestTypedErrors:
    def test_error_hierarchy(self):
        assert issubclass(VideoFetchError, YtSummarizerError)
        assert issubclass(ProviderSetupError, YtSummarizerError)
        assert issubclass(LLMRunError, YtSummarizerError)

    def test_video_fetch_error_message(self):
        err = VideoFetchError("no transcript")
        assert "no transcript" in str(err)

    def test_provider_setup_error_message(self):
        err = ProviderSetupError("bad provider")
        assert "bad provider" in str(err)
