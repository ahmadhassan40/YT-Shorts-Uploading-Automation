import os
import subprocess
import logging
import uuid
import random
import requests
from typing import Dict, Any
from core.engine_interface import VideoEngine
from config.config_loader import config

logger = logging.getLogger(__name__)

class FFmpegVideoEngine(VideoEngine):
    def __init__(self):
        self.output_dir = config.get("paths.output_dir", "output")
        self.assets_dir = config.get("paths.assets_dir", "assets")
        self.stock_videos_dir = os.path.join(self.assets_dir, "stock_videos")
        
        # Pexels Settings
        self.stock_provider = config.get("stock_videos.provider", "local")
        self.pexels_api_key = config.get("stock_videos.api_key", "")
        self.pexels_orientation = config.get("stock_videos.orientation", "portrait")
        
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

    def download_from_pexels(self, query: str) -> str:
        """Downloads a video from Pexels based on the query."""
        if not self.pexels_api_key or "YOUR_PEXELS_API_KEY" in self.pexels_api_key:
            logger.warning("Pexels API Key not set. Falling back to local videos.")
            return None
            
        logger.info(f"Searching Pexels for video with query: '{query}'...")
        headers = {"Authorization": self.pexels_api_key}
        params = {
            "query": query,
            "per_page": 5, # Get top 5 to pick random
            "orientation": self.pexels_orientation,
            # "size": "medium" # REMOVED: Caused 0 results for many queries
        }
        
        try:
            response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("videos"):
                logger.warning(f"No videos found on Pexels for query: {query}")
                return None
                
            # Pick a random video from results
            video_data = random.choice(data["videos"])
            
            # Find the best video file (closest to 1080p or 720p)
            video_files = video_data.get("video_files", [])
            # Sort by width to get decent quality (descending)
            video_files.sort(key=lambda x: x.get("width", 0), reverse=True)
            
            # Use the first one (highest quality) or a middle one to save bandwidth?
            # Let's go with the highest quality to ensure it looks good
            best_video = video_files[0]
            download_url = best_video["link"]
            
            # Create filename
            filename = f"pexels_{video_data['id']}_{query.replace(' ', '_')}.mp4"
            filepath = os.path.join(self.stock_videos_dir, filename)
            
            # Ensure folder exists
            os.makedirs(self.stock_videos_dir, exist_ok=True)
            
            # Check if we already downloaded it
            if os.path.exists(filepath):
                logger.info(f"Video already exists in cache: {filepath}")
                return filepath
                
            logger.info(f"Downloading video from Pexels: {download_url}...")
            # Stream download
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
                        
            logger.info(f"Video downloaded to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to download from Pexels: {e}")
            return None

    def _clean_query(self, query: str) -> str:
        """Removes common prefixes to get better search results."""
        if not query: return ""
        q = query.lower()
        remove_phrases = ["the history of", "history of", "the story of", "story of", "how to", "what is", "about"]
        for phrase in remove_phrases:
            if q.startswith(phrase):
                q = q.replace(phrase, "").strip()
        
        # Remove punctuation/extra chars
        q = "".join([c for c in q if c.isalnum() or c.isspace()])
        return q.strip()

    def get_stock_video(self, query: str = None) -> str:
        """Picks a stock video based on provider settings."""
        
        # Default behavior: check if we should use Pexels
        if self.stock_provider == "pexels" and query:
            # 1. Try cleaned query
            cleaned = self._clean_query(query)
            logger.info(f"Targeting Pexels with query: '{cleaned}' (Original: '{query}')")
            
            video_path = self.download_from_pexels(cleaned)
            if video_path:
                return video_path
            
            # 2. Try single keyword (longest word) if phrase failed
            words = cleaned.split()
            if len(words) > 1:
                 longest_word = max(words, key=len)
                 if len(longest_word) > 3: # Ignore short words
                     logger.info(f"Retrying Pexels with keyword: '{longest_word}'")
                     video_path = self.download_from_pexels(longest_word)
                     if video_path: return video_path

        # Fallback to local
        logger.info("Using local stock videos fallback.")
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
        """
        background_video = None
        
        # 1. Try 'visual_keywords' from AI script (Best chance of match)
        keywords = script_data.get("visual_keywords", [])
        if isinstance(keywords, list):
            for keyword in keywords:
                if not keyword: continue
                logger.info(f"Trying Pexels search with AI keyword: '{keyword}'")
                background_video = self.get_stock_video(query=keyword)
                if background_video:
                    break
        
        # 2. If no keywords worked, try the topic itself
        if not background_video:
            topic = script_data.get("topic", "")
            if topic:
                logger.info(f"Keywords failed. Retrying Pexels with topic: '{topic}'")
                background_video = self.get_stock_video(query=topic)
        
        # 3. Last Resort Fallback - Use a generic term if everything else fails
        if not background_video:
             logger.warning("All specific searches failed. Trying generic 'technology' fallback.")
             background_video = self.get_stock_video(query="technology")

        if not background_video:
            raise FileNotFoundError(f"No stock videos found even after fallbacks. Please check Pexels API key or add files to {self.stock_videos_dir}")

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
            "Alignment=6,"  # Top center alignment
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
