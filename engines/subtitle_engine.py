import os
import logging
import math
from core.engine_interface import SubtitleEngine
from config.config_loader import config

logger = logging.getLogger(__name__)

class WhisperSubtitleEngine(SubtitleEngine):
    def __init__(self):
        self.model_size = config.get("whisper.model_size", "base")
        self.device = config.get("whisper.device", "cpu")
        self.compute_type = config.get("whisper.compute_type", "int8")
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading Whisper model '{self.model_size}' on {self.device}...")
                self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            except ImportError:
                logger.error("faster-whisper not installed. Please pip install faster-whisper")
                raise

    def format_time(self, seconds: float) -> str:
        """Converts seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = math.floor(seconds / 3600)
        seconds %= 3600
        minutes = math.floor(seconds / 60)
        seconds %= 60
        milliseconds = round((seconds - math.floor(seconds)) * 1000)
        seconds = math.floor(seconds)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def generate_subtitles(self, audio_path: str) -> str:
        """
        Generates SRT subtitles using Whisper.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()
        
        logger.info(f"Transcribing {audio_path}...")
        segments, info = self._model.transcribe(audio_path, beam_size=5)
        
        srt_content = ""
        for i, segment in enumerate(segments, start=1):
            start = self.format_time(segment.start)
            end = self.format_time(segment.end)
            text = segment.text.strip()
            srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
        
        output_path = audio_path.replace(os.path.splitext(audio_path)[1], ".srt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
            
        logger.info(f"Subtitles saved to {output_path}")
        return output_path
