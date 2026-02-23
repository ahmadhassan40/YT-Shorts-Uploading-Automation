import os
import subprocess
import logging
import uuid
import random
import math
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from core.engine_interface import VideoEngine
from config.config_loader import config

logger = logging.getLogger(__name__)

CLIP_DURATION = 4.0      # Each clip is at most 4 seconds
FADE_DURATION = 0.5      # Crossfade between clips (seconds)
TARGET_W = 1080
TARGET_H = 1920
TARGET_FPS = 30

class FFmpegVideoEngine(VideoEngine):
    def __init__(self):
        self.output_dir = config.get("paths.output_dir", "output")
        self.assets_dir = config.get("paths.assets_dir", "assets")
        self.stock_videos_dir = os.path.join(self.assets_dir, "stock_videos")

        # Pexels settings
        self.stock_provider = config.get("stock_videos.provider", "local")
        self.pexels_api_key = config.get("stock_videos.api_key", "")
        self.pexels_orientation = config.get("stock_videos.orientation", "portrait")

        # Music settings
        self.music_enabled = config.get("music.enabled", True)
        self.music_dir = config.get("music.tracks_dir", "assets/music")
        self.music_volume = config.get("music.volume", -20)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _get_audio_duration(self, audio_path: str) -> float:
        """Return duration of audio file in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return float(result.stdout.decode().strip())
        except Exception as e:
            logger.warning(f"ffprobe failed ({e}). Falling back to default 60s duration.")
            return 60.0

    def _safe_folder_name(self, topic: str) -> str:
        """Convert topic to a filesystem-safe folder name."""
        safe = re.sub(r'[\\/:*?"<>|]', "", topic)
        safe = re.sub(r'\s+', "_", safe.strip())
        return safe[:80]  # Limit length

    def get_random_music_track(self) -> Optional[str]:
        """Pick a random music track from the music folder."""
        if not self.music_enabled or not os.path.exists(self.music_dir):
            return None
        music_files = [
            f for f in os.listdir(self.music_dir)
            if f.lower().endswith((".mp3", ".wav", ".m4a"))
        ]
        if not music_files:
            logger.warning(f"No music files found in {self.music_dir}")
            return None
        selected = os.path.join(self.music_dir, random.choice(music_files))
        logger.info(f"Selected background music: {os.path.basename(selected)}")
        return selected

    def _clean_query(self, query: str) -> str:
        """Remove common filler prefixes for better Pexels search results."""
        if not query:
            return ""
        q = query.lower()
        for phrase in ["the history of", "history of", "the story of", "story of", "how to", "what is", "about"]:
            if q.startswith(phrase):
                q = q.replace(phrase, "").strip()
        q = "".join(c for c in q if c.isalnum() or c.isspace())
        return q.strip()

    # ──────────────────────────────────────────────
    # Pexels: fetch ONE video file path for a query
    # ──────────────────────────────────────────────

    def _fetch_one_pexels_video(self, query: str) -> Optional[str]:
        """Download a single Pexels video matching the query. Returns local file path or None."""
        if not self.pexels_api_key or "YOUR_PEXELS_API_KEY" in self.pexels_api_key:
            return None

        headers = {"Authorization": self.pexels_api_key}
        params = {
            "query": query,
            "per_page": 10,
            "orientation": self.pexels_orientation,
        }

        try:
            resp = requests.get(
                "https://api.pexels.com/videos/search",
                headers=headers, params=params, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            if not data.get("videos"):
                logger.warning(f"No Pexels results for '{query}'")
                return None

            video_data = random.choice(data["videos"])
            video_files = sorted(
                video_data.get("video_files", []),
                key=lambda x: x.get("width", 0),
                reverse=True,
            )
            if not video_files:
                return None

            best = video_files[0]
            download_url = best["link"]
            
            # CRITICAL DUPLICATION FIX: Name file strictly by Pexels ID, no query keywords.
            # This ensures if two different keywords find the same video, we don't save it twice.
            filename = f"pexels_{video_data['id']}.mp4"
            filepath = os.path.join(self.stock_videos_dir, filename)
            os.makedirs(self.stock_videos_dir, exist_ok=True)

            if os.path.exists(filepath):
                logger.info(f"Cache hit: {filename}")
                return filepath

            logger.info(f"Downloading from Pexels: {filename}")
            with requests.get(download_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)

            return filepath

        except Exception as e:
            logger.error(f"Pexels fetch failed for '{query}': {e}")
            return None

    # ──────────────────────────────────────────────
    # Fetch N stock video clips (parallel)
    # ──────────────────────────────────────────────

    def get_stock_videos(self, num_clips: int, script_data: Dict[str, Any]) -> List[str]:
        """
        Return a list of exactly `num_clips` unique local video file paths.
        Strategy (fast, minimises API calls):
          1. Build a pool of search queries from visual_keywords + topic.
          2. Fire parallel Pexels requests (one per unique query needed).
          3. If Pexels disabled / out of keywords, fill from local folder.
          4. Ensure strict uniqueness. Cycle/repeat only if absolutely necessary.
        """
        clips: List[str] = []
        used_ids = set()

        if self.stock_provider == "pexels" and self.pexels_api_key and "YOUR_PEXELS_API_KEY" not in self.pexels_api_key:
            # Build query list
            keywords = list(script_data.get("visual_keywords") or [])
            topic = script_data.get("topic", "")
            if topic:
                keywords.append(self._clean_query(topic))
            keywords = [self._clean_query(k) for k in keywords if k]
            keywords = list(dict.fromkeys(keywords))  # deduplicate, preserve order

            # We need at most num_clips unique queries; pad by reusing if we run short
            # However, reusing the same keyword likely returns the same video.
            queries = [keywords[i % len(keywords)] for i in range(num_clips * 2)] if keywords else []

            # Parallel download
            with ThreadPoolExecutor(max_workers=min(num_clips, 5)) as pool:
                futures = {pool.submit(self._fetch_one_pexels_video, q): q for q in queries}
                for future in as_completed(futures):
                    if len(clips) >= num_clips:
                        # We have enough, ignore the rest
                        continue
                        
                    result = future.result()
                    if result:
                        # CRITICAL DUPLICATION FIX: Ensure we only add strictly unique files
                        basename = os.path.basename(result)
                        if basename not in used_ids:
                            used_ids.add(basename)
                            clips.append(result)

        # Fill remaining slots from local folder (checking uniqueness)
        if len(clips) < num_clips:
            local_videos = []
            if os.path.exists(self.stock_videos_dir):
                local_videos = [
                    os.path.join(self.stock_videos_dir, f)
                    for f in os.listdir(self.stock_videos_dir)
                    if f.lower().endswith(".mp4")
                ]

            if local_videos:
                needed = num_clips - len(clips)
                # First pass: ONLY add unused locals
                unused_locals = [v for v in local_videos if os.path.basename(v) not in used_ids]
                random.shuffle(unused_locals)
                
                for v in unused_locals[:needed]:
                    clips.append(v)
                    used_ids.add(os.path.basename(v))
                
                # If STILL needed (ran out of unique clips entirely), log warning & recycle
                still_needed = num_clips - len(clips)
                if still_needed > 0:
                    logger.warning(f"Not enough unique videos! Required {num_clips}, only found {len(clips)}. Recycling videos.")
                    for i in range(still_needed):
                        clips.append(local_videos[i % len(local_videos)])
            else:
                logger.warning("No local stock videos available for fallback.")

        if not clips:
            raise FileNotFoundError(
                f"No stock videos found. Check Pexels API key or add .mp4 files to {self.stock_videos_dir}"
            )

        # Shuffle again so fallback videos aren't all clustered at the end
        random.shuffle(clips)
        return clips[:num_clips]

    # ──────────────────────────────────────────────
    # Build FFmpeg filter_complex for N clips w/ xfade
    # ──────────────────────────────────────────────

    def _build_filter_complex(
        self,
        num_clips: int,
        subtitle_filter: str,
        music_volume: int,
        has_music: bool,
    ) -> str:
        """
        Builds the filter_complex string for:
          - Scale + crop + fps-normalise each clip
          - xfade transitions between consecutive clips
          - Subtitle burn-in on the final video
          - (optionally) mix voice + music audio
        Input indices:
          0 .. num_clips-1  → video clips
          num_clips          → voiceover audio
          num_clips+1        → music (only when has_music=True)
        """
        parts = []

        # Step 1: Normalise every clip
        # scale with force_original_aspect_ratio=increase ensures BOTH dimensions
        # are >= target before crop, regardless of source aspect ratio (portrait, landscape, etc.)
        for i in range(num_clips):
            parts.append(
                f"[{i}:v]fps={TARGET_FPS},"
                f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,"
                f"crop={TARGET_W}:{TARGET_H},"
                f"setsar=1[v{i}]"
            )

        # Step 2: Chain xfade transitions
        # Each clip is (CLIP_DURATION) seconds on screen.
        # With a FADE_DURATION overlap, offset of clip i+1 = (i+1)*CLIP_DURATION - (i+1)*FADE_DURATION
        if num_clips == 1:
            parts.append(f"[v0]{subtitle_filter}[vout]")
        else:
            prev_label = "v0"
            for i in range(1, num_clips):
                out_label = f"xf{i}" if i < num_clips - 1 else "prefinal"
                offset = i * CLIP_DURATION - i * FADE_DURATION
                parts.append(
                    f"[{prev_label}][v{i}]xfade=transition=fade:"
                    f"duration={FADE_DURATION}:offset={offset:.3f}[{out_label}]"
                )
                prev_label = out_label
            # Apply subtitles to the stitched stream
            parts.append(f"[prefinal]{subtitle_filter}[vout]")

        # Step 3: Audio mix
        voice_idx = num_clips
        if has_music:
            music_idx = num_clips + 1
            parts.append(
                f"[{voice_idx}:a]volume=0dB[voice];"
                f"[{music_idx}:a]volume={music_volume}dB[music];"
                f"[voice][music]amix=inputs=2:duration=shortest[aout]"
            )
        else:
            parts.append(f"[{voice_idx}:a]anull[aout]")

        return ";".join(parts)

    # ──────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────

    def generate_video(self, script_data: Dict[str, Any], audio_path: str, subtitles_path: str) -> str:
        """
        Generates a YouTube Short by compositing multiple stock video clips,
        voiceover audio, background music, and burned-in subtitles.
        """
        # 1. Calculate how many clips we need.
        # Each xfade overlaps by FADE_DURATION, so total video duration is:
        #   N * CLIP_DURATION - (N-1) * FADE_DURATION
        # We need that to be >= audio_duration + a small safety buffer (0.5s)
        # so the very last word is never cut off.
        # Solving: N >= (audio_duration + buffer - FADE_DURATION) / (CLIP_DURATION - FADE_DURATION)
        SAFETY_BUFFER = 0.5  # extra seconds beyond audio to prevent end cut-off
        effective_clip = CLIP_DURATION - FADE_DURATION  # net seconds each extra clip adds (3.5s)
        audio_duration = self._get_audio_duration(audio_path)
        num_clips = max(1, math.ceil((audio_duration + SAFETY_BUFFER - FADE_DURATION) / effective_clip))
        total_video_s = num_clips * CLIP_DURATION - (num_clips - 1) * FADE_DURATION
        logger.info(
            f"Audio duration: {audio_duration:.1f}s → fetching {num_clips} clip(s) "
            f"(total video ~{total_video_s:.1f}s)"
        )

        # 2. Fetch clips (parallel when using Pexels)
        clips = self.get_stock_videos(num_clips, script_data)
        logger.info(f"Using {len(clips)} clip(s): {[os.path.basename(c) for c in clips]}")

        # 3. Output path: output/<safe_topic>/<uuid>.mp4
        topic = script_data.get("topic", "video")
        safe_topic = self._safe_folder_name(topic)
        topic_dir = os.path.join(self.output_dir, safe_topic)
        os.makedirs(topic_dir, exist_ok=True)
        output_path = os.path.join(topic_dir, f"final_video_{uuid.uuid4().hex[:8]}.mp4")

        # 4. Build subtitle filter string
        subtitles_path_fixed = subtitles_path.replace("\\", "/").replace(":", "\\:")
        is_ass = subtitles_path.endswith(".ass")
        if is_ass:
            subtitle_filter = f"ass='{subtitles_path_fixed}'"
            logger.info("Using ASS subtitle format")
        else:
            subtitle_style = (
                "Fontname=Arial Black,"
                "Fontsize=18,"
                "PrimaryColour=&H00FFFFFF,"
                "OutlineColour=&H00000000,"
                "BorderStyle=3,"
                "Outline=2,"
                "Shadow=1,"
                "MarginV=50,"
                "Alignment=6,"
                "Bold=1"
            )
            subtitle_filter = f"subtitles='{subtitles_path_fixed}':force_style='{subtitle_style}'"
            logger.info("Using SRT subtitle format")

        # 5. Pick music (optional)
        music_track = self.get_random_music_track()

        # 6. Assemble FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Video inputs (each clip, looped to ensure it's long enough)
        for clip in clips:
            cmd += ["-stream_loop", "-1", "-t", str(CLIP_DURATION), "-i", clip]

        # Audio: voiceover
        cmd += ["-i", audio_path]

        # Audio: music (looped)
        if music_track:
            cmd += ["-stream_loop", "-1", "-i", music_track]

        # Build and attach filter_complex
        fc = self._build_filter_complex(
            num_clips=len(clips),
            subtitle_filter=subtitle_filter,
            music_volume=self.music_volume,
            has_music=bool(music_track),
        )
        cmd += ["-filter_complex", fc]

        # Map outputs
        cmd += [
            "-map", "[vout]",
            "-map", "[aout]",
            "-shortest",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]

        logger.info(f"Rendering video → {output_path}")
        logger.debug(f"FFmpeg cmd: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Video saved: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed:\n{e.stderr.decode()}")
            raise
        except FileNotFoundError:
            logger.error("FFmpeg not found in PATH.")
            raise
