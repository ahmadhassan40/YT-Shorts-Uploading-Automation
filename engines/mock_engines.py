from typing import Dict, Any
from core.engine_interface import ScriptEngine, AudioEngine, SubtitleEngine, VideoEngine, UploadEngine, VideoMetadata
import time
import logging

logger = logging.getLogger(__name__)

class MockScriptEngine(ScriptEngine):
    def generate_script(self, topic: str) -> Dict[str, Any]:
        logger.info(f"Generating mock script for topic: {topic}")
        return {
            "topic": topic,
            "hook": "This is a hook.",
            "body": "This is the main content.",
            "cta": "Like and subscribe!"
        }

class MockAudioEngine(AudioEngine):
    def generate_audio(self, script_text: str) -> str:
        logger.info("Generating mock audio...")
        return "output/mock_audio.mp3"

class MockSubtitleEngine(SubtitleEngine):
    def generate_subtitles(self, audio_path: str) -> str:
        logger.info(f"Generating mock subtitles for {audio_path}...")
        return "output/mock_subtitles.srt"

class MockVideoEngine(VideoEngine):
    def generate_video(self, script_data: Dict[str, Any], audio_path: str, subtitles_path: str) -> str:
        logger.info("Rendering mock video...")
        time.sleep(1) # Simulate rendering time
        return "output/mock_video.mp4"

class MockUploadEngine(UploadEngine):
    def upload_video(self, video_path: str, metadata: VideoMetadata) -> str:
        logger.info(f"Uploading {video_path} to YouTube (Mock)...")
        return "https://youtube.com/shorts/mock_video_id"
