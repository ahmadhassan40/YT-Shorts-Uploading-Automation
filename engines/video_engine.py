import os
import subprocess
import logging
import uuid
import random
from typing import Dict, Any
from core.engine_interface import VideoEngine
from config.config_loader import config

logger = logging.getLogger(__name__)

class FFmpegVideoEngine(VideoEngine):
    def __init__(self):
        self.output_dir = config.get("paths.output_dir", "output")
        self.assets_dir = config.get("paths.assets_dir", "assets")
        self.stock_videos_dir = os.path.join(self.assets_dir, "stock_videos")
        
        # Music settings
        self.music_enabled = config.get("music.enabled", True)
        self.music_dir = config.get("music.tracks_dir", "assets/music")
        self.music_volume = config.get("music.volume", -20)

    def get_random_music_track(self) -> str:
        """Picks a random music track from the music folder."""
        if not self.music_enabled or not os.path.exists(self.music_dir):
            return None
        
        music_files = [f for f in os.listdir(self.music_dir) 
                      if f.lower().endswith((".mp3", ".wav", ".m4a"))]
        if not music_files:
            logger.warning(f"No music files found in {self.music_dir}")
            return None
        
        selected = os.path.join(self.music_dir, random.choice(music_files))
        logger.info(f"Selected background music: {os.path.basename(selected)}")
        return selected

    def get_random_stock_video(self) -> str:
        """Picks a random video from the stock folder."""
        if not os.path.exists(self.stock_videos_dir):
            os.makedirs(self.stock_videos_dir, exist_ok=True)
            logger.warning(f"Stock video directory created at {self.stock_videos_dir}. Please add mp4 files.")
            return None
        
        videos = [f for f in os.listdir(self.stock_videos_dir) if f.endswith(".mp4")]
        if not videos:
            return None
        return os.path.join(self.stock_videos_dir, random.choice(videos))

    def generate_video(self, script_data: Dict[str, Any], audio_path: str, subtitles_path: str) -> str:
        """
        Generates a video by compositing a stock video, audio, and subtitles.
        Note: This is a basic implementation.
        """
        background_video = self.get_random_stock_video()
        if not background_video:
            raise FileNotFoundError(f"No stock videos found in {self.stock_videos_dir}")

        output_filename = f"final_video_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        logger.info(f"Rendering video to {output_path}...")
        
        # FFmpeg command to:
        # 1. Take background video input
        # 2. Take audio input
        # 3. Loop background video if shorter than audio
        # 4. Crop background to 9:16 (vertical)
        # 5. Burn in subtitles
        # 6. Map video and audio to output
        # 7. Shortest output determined by audio
        
        # Note: Subtitles burning often requires full path with forward slashes on Windows
        subtitles_path_fixed = subtitles_path.replace("\\", "/").replace(":", "\\:")

        # Modern subtitle styling for YouTube Shorts
        subtitle_style = (
            "Fontname=Arial Black,"  # Bold, readable font
            "Fontsize=18,"  # Smaller, less intrusive
            "PrimaryColour=&H00FFFFFF,"  # White text
            "OutlineColour=&H00000000,"  # Black outline
            "BorderStyle=3,"  # Outline + shadow
            "Outline=2,"  # Thick outline for readability
            "Shadow=1,"  # Subtle shadow
            "MarginV=50,"  # Position from top (50 pixels from top)
            "Alignment=2,"  # Top center alignment
            "Bold=1"  # Bold text
        )

        # Get background music if enabled
        music_track = self.get_random_music_track()
        
        if music_track:
            # Complex FFmpeg command with background music
            # 1. Loop background video
            # 2. Mix voice (audio_path) with music (music_track)
            # 3. Music is lowered to configured volume (default -20dB)
            # 4. Apply subtitles
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite
                "-stream_loop", "-1",  # Loop video
                "-i", background_video,  # Input 0: video
                "-i", audio_path,  # Input 1: voice
                "-stream_loop", "-1",  # Loop music
                "-i", music_track,  # Input 2: music
                "-filter_complex",
                f"[1:a]volume=0dB[voice];"  # Voice at normal volume
                f"[2:a]volume={self.music_volume}dB[music];"  # Music ducked
                f"[voice][music]amix=inputs=2:duration=shortest[audio];"  # Mix both
                f"[0:v]crop=ih*(9/16):ih,subtitles='{subtitles_path_fixed}':force_style='{subtitle_style}'[video]",
                "-map", "[video]",
                "-map", "[audio]",
                "-shortest",  # Stop when shortest input ends
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "192k",  # Good audio quality
                output_path
            ]
        else:
            # No music - simple command
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite
                "-stream_loop", "-1",  # Loop video
                "-i", background_video,
                "-i", audio_path,
                "-shortest",
                "-map", "0:v",
                "-map", "1:a",
                "-vf", f"crop=ih*(9/16):ih,subtitles='{subtitles_path_fixed}':force_style='{subtitle_style}'",
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                output_path
            ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr.decode()}")
            raise
        except FileNotFoundError:
             logger.error("FFmpeg not found in PATH.")
             raise
