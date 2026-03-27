def build_system_prompt() -> str:
    return """You are an expert technical content summarizer. Your goal is to process a YouTube transcript and generate a structured Obsidian resource note.

INSTRUCTIONS:
1. EXTRACT:
   - Summary: A concise 2-3 sentence overview of the video's core message.
   - Key Concepts: A list of the most important technical concepts discussed, each tied to its approximate timestamp in the video.
   - Key Quotes: Exactly 3 high-impact or particularly insightful quotes from the speaker.
2. FORMAT:
   - Use the provided JSON schema for your response.
   - Timestamps must be in HH:MM:SS or MM:SS format.
"""

def build_user_prompt(video_info: dict, transcript: str) -> str:
    return f"""VIDEO TITLE: {video_info.get('title')}
CHANNEL: {video_info.get('channel')}
URL: {video_info.get('url')}

TRANSCRIPT:
{transcript}

Please summarize this video based on the transcript.
"""
