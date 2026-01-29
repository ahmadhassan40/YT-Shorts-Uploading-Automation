import logging
import sys
import os
from config.config_loader import config
from core.engine_interface import VideoMetadata
from engines.mock_engines import MockScriptEngine, MockAudioEngine, MockSubtitleEngine, MockVideoEngine, MockUploadEngine
from engines.script_engine import OllamaScriptEngine
from engines.audio_engine import PiperAudioEngine
from engines.subtitle_engine import WhisperSubtitleEngine
from engines.video_engine import FFmpegVideoEngine
from engines.upload_engine import YouTubeUploadEngine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("YT_BOT")

def get_engine(api_type: str, engine_class_mock):
    """
    Factory method to get the correct engine instance.
    """
    if api_type == "ollama":
        return OllamaScriptEngine()
    elif api_type == "piper":
        return PiperAudioEngine()
    elif api_type == "whisper":
        return WhisperSubtitleEngine()
    elif api_type == "ffmpeg":
        return FFmpegVideoEngine()
    elif api_type == "youtube":
        return YouTubeUploadEngine()
    elif "mock" in api_type:
        return engine_class_mock()
    else:
        # Fallback to mock for now, or raise NotImplementedError
        logger.warning(f"Engine type '{api_type}' not implemented yet. Using Mock.")
        return engine_class_mock()

class Pipeline:
    def __init__(self):
        self.script_engine = get_engine(config.get('engines.script'), MockScriptEngine)
        self.audio_engine = get_engine(config.get('engines.audio'), MockAudioEngine)
        self.subtitle_engine = get_engine(config.get('engines.subtitle'), MockSubtitleEngine)
        self.video_engine = get_engine(config.get('engines.video'), MockVideoEngine)
        self.upload_engine = get_engine(config.get('engines.upload'), MockUploadEngine)

    def run(self, topic: str):
        logger.info(f"Starting pipeline for topic: {topic}")

        # 1. Generate Script
        logger.info("Step 1: Script Generation")
        try:
            script_data = self.script_engine.generate_script(topic)
            
            # Handle new script array format
            # Handle new script array format
            if "script" in script_data and isinstance(script_data["script"], list):
                # Concatenate all text parts for full voiceover
                # Sanitize text to remove potential labels if model hallucinated them inside the "text" field
                cleaned_parts = []
                for part in script_data["script"]:
                    text = part["text"]
                    # Remove common prefixes like "Hook:", "Context:", "Text:"
                    import re
                    text = re.sub(r'^(Hook|Context|Body|Twist|Reveal|Ending|CTA|Text):\s*', '', text, flags=re.IGNORECASE)
                    cleaned_parts.append(text)
                
                full_script_text = " ".join(cleaned_parts)
            else:
                # Fallback for legacy format
                full_script_text = f"{script_data.get('hook', '')} {script_data.get('body', '')} {script_data.get('cta', '')}"
                
            logger.info(f"Generated Script Length: {len(full_script_text)} chars")
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return

        # Inject topic into script_data for downstream usage (e.g. video search)
        if script_data:
            script_data['topic'] = topic

        # 2. Generate Audio
        logger.info("Step 2: Audio Generation")
        try:
            audio_path = self.audio_engine.generate_audio(full_script_text)
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return

        # 3. Generate Subtitles
        logger.info("Step 3: Subtitle Generation")
        try:
            subtitles_path = self.subtitle_engine.generate_subtitles(audio_path)
        except Exception as e:
            logger.error(f"Subtitle generation failed: {e}")
            return

        # 4. Render Video
        logger.info("Step 4: Video Rendering")
        try:
            video_path = self.video_engine.generate_video(script_data, audio_path, subtitles_path)
        except Exception as e:
            logger.error(f"Video rendering failed: {e}")
            return

        # 5. Upload
        logger.info("Step 5: Upload")
        try:
            # Use AI-generated title and description
            metadata = VideoMetadata(
                title=script_data.get('title', f"Short about {topic}"),
                description=script_data.get('description', full_script_text),
                tags=["shorts", "viral", topic.replace(" ", "").lower()]
            )
            video_url = self.upload_engine.upload_video(video_path, metadata)
            logger.info(f"SUCCESS! Video uploaded at: {video_url}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <topic>")
        # Default topic for testing
        topic = "Artificial Intelligence"
        logger.info(f"No topic provided. Using default: '{topic}'")
    else:
        topic = sys.argv[1]

    pipeline = Pipeline()
    pipeline.run(topic)

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    main()
