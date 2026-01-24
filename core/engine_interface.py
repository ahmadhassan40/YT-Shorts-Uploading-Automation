from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class VideoMetadata:
    title: str
    description: str
    tags: List[str]
    privacy_status: str = "private"

class ScriptEngine(ABC):
    @abstractmethod
    def generate_script(self, topic: str) -> Dict[str, Any]:
        """
        Generates a script for the given topic.
        Returns a dictionary containing script sections (hook, body, cta).
        """
        pass

class AudioEngine(ABC):
    @abstractmethod
    def generate_audio(self, script_text: str) -> str:
        """
        Generates audio from the given script text.
        Returns the path to the generated audio file.
        """
        pass

class SubtitleEngine(ABC):
    @abstractmethod
    def generate_subtitles(self, audio_path: str) -> str:
        """
        Generates subtitles for the given audio file.
        Returns the path to the generated subtitle file (e.g., .srt).
        """
        pass

class VideoEngine(ABC):
    @abstractmethod
    def generate_video(self, script_data: Dict[str, Any], audio_path: str, subtitles_path: str) -> str:
        """
        Generates the final video.
        Returns the path to the generated video file.
        """
        pass

class UploadEngine(ABC):
    @abstractmethod
    def upload_video(self, video_path: str, metadata: VideoMetadata) -> str:
        """
        Uploads the video to YouTube.
        Returns the URL of the uploaded video.
        """
        pass
