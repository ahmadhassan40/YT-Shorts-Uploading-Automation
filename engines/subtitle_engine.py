import os
import logging
import math
import re
from typing import List, Dict, Tuple
from core.engine_interface import SubtitleEngine
from config.config_loader import config

logger = logging.getLogger(__name__)

class WhisperSubtitleEngine(SubtitleEngine):
    def __init__(self):
        self.model_size = config.get("whisper.model_size", "base")
        self.device = config.get("whisper.device", "cpu")
        self.compute_type = config.get("whisper.compute_type", "int8")
        self._model = None
        
        # Important words for highlighting (dark/shocking keywords)
        self.important_keywords = {
            'death', 'killed', 'murder', 'betrayal', 'secret', 'hidden', 'truth', 
            'dark', 'shocking', 'horror', 'tragedy', 'disaster', 'sin', 'evil',
            'forbidden', 'cursed', 'haunted', 'bloody', 'war', 'slaughter',
            'conspiracy', 'cover-up', 'lie', 'deception', 'poison', 'assassin',
            'torture', 'suffering', 'pain', 'doom', 'fate', 'revenge', 'wrath'
        }

    def _load_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading Whisper model '{self.model_size}' on {self.device}...")
                self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            except ImportError:
                logger.error("faster-whisper not installed. Please pip install faster-whisper")
                raise

    def format_ass_time(self, seconds: float) -> str:
        """Converts seconds to ASS time format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds %= 60
        centiseconds = int((seconds - int(seconds)) * 100)
        seconds = int(seconds)
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def detect_important_word(self, words: List[str]) -> int:
        """
        Detects the most important word in a chunk for highlighting.
        Returns the index of the word to highlight.
        """
        # Check for important keywords first
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in self.important_keywords:
                return i
        
        # Fallback: highlight nouns/verbs (simple heuristic - longer words, capitalized words)
        # Priority: capitalized words (likely proper nouns or emphasized)
        for i, word in enumerate(words):
            if len(word) > 0 and word[0].isupper() and i > 0:  # Skip first word (sentence start)
                return i
        
        # Fallback: longest word
        if words:
            longest_idx = max(range(len(words)), key=lambda i: len(words[i]))
            return longest_idx
        
        return 0

    def should_capitalize(self, word: str) -> bool:
        """Determine if a word should be in ALL CAPS for emphasis"""
        clean_word = re.sub(r'[^\w]', '', word.lower())
        return clean_word in self.important_keywords

    def chunk_words(self, words_with_times: List[Dict], min_words: int = 2, max_words: int = 4) -> List[List[Dict]]:
        """
        Chunks words into 2-4 word segments with appropriate timing.
        Each chunk should last 0.6-1.2 seconds ideally.
        """
        chunks = []
        current_chunk = []
        
        for word_data in words_with_times:
            current_chunk.append(word_data)
            
            # Check if we should finalize this chunk
            if len(current_chunk) >= min_words:
                chunk_duration = current_chunk[-1]['end'] - current_chunk[0]['start']
                
                # Finalize if we hit max words OR if duration is good (0.6-1.2s)
                if len(current_chunk) >= max_words or (0.6 <= chunk_duration <= 1.2):
                    chunks.append(current_chunk)
                    current_chunk = []
        
        # Add remaining words
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def apply_highlighting(self, words: List[str], highlight_idx: int) -> str:
        """
        Applies blood red highlighting to the important word.
        Format: {\c&H0000FF&}WORD{\c&HFFFFFF&}
        (BGR format: 0000FF = red, FFFFFF = white)
        """
        result_words = []
        for i, word in enumerate(words):
            # Apply ALL CAPS if it's an important keyword
            display_word = word.upper() if self.should_capitalize(word) else word
            
            if i == highlight_idx:
                # Blood red highlight
                result_words.append(f"{{\\c&H0000FF&}}{display_word}{{\\c&HFFFFFF&}}")
            else:
                result_words.append(display_word)
        
        return " ".join(result_words)

    def generate_subtitles(self, audio_path: str) -> str:
        """
        Generates ASS subtitles with advanced styling and word highlighting.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()
        
        logger.info(f"Transcribing {audio_path} with word-level timestamps...")
        segments, info = self._model.transcribe(audio_path, beam_size=5, word_timestamps=True)
        
        # Collect all words with timestamps
        all_words_with_times = []
        for segment in segments:
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    all_words_with_times.append({
                        'word': word.word.strip(),
                        'start': word.start,
                        'end': word.end
                    })
        
        # Chunk into 2-4 word segments
        chunks = self.chunk_words(all_words_with_times, min_words=2, max_words=4)
        
        logger.info(f"Created {len(chunks)} subtitle chunks from {len(all_words_with_times)} words")
        
        # Generate ASS content
        ass_content = self._generate_ass_header()
        
        # Determine hook duration (first 2-3 seconds)
        hook_duration = 3.0
        
        for i, chunk in enumerate(chunks):
            start_time = chunk[0]['start']
            end_time = chunk[-1]['end']
            words = [w['word'] for w in chunk]
            
            # Detect important word for highlighting
            highlight_idx = self.detect_important_word(words)
            
            # Apply highlighting
            styled_text = self.apply_highlighting(words, highlight_idx)
            
            # Determine style (Hook vs Default)
            style = "Hook" if start_time < hook_duration else "Default"
            
            # Create dialogue line
            start_ass = self.format_ass_time(start_time)
            end_ass = self.format_ass_time(end_time)
            
            ass_content += f"Dialogue: 0,{start_ass},{end_ass},{style},,0,0,0,,{styled_text}\n"
        
        # Save ASS file
        output_path = audio_path.replace(os.path.splitext(audio_path)[1], ".ass")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        
        logger.info(f"ASS subtitles saved to {output_path}")
        return output_path

    def _generate_ass_header(self) -> str:
        """Generates the ASS file header with dual styles"""
        return """[Script Info]
Title: YT Shorts Subtitle
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Arial Black,130,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,8,10,10,400,1
Style: Default,Arial Black,120,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,10,10,550,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
