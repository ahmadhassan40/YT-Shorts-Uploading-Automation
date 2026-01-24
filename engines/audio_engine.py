import subprocess
import os
import uuid
import logging
from core.engine_interface import AudioEngine
from config.config_loader import config

logger = logging.getLogger(__name__)

class PiperAudioEngine(AudioEngine):
    def __init__(self):
        self.binary_path = config.get("piper.binary_path", "assets/piper/piper.exe")
        self.model_path = config.get("piper.model_path", "assets/voices/en_US-ryans-medium.onnx")
        self.output_dir = config.get("paths.output_dir", "output")

    def generate_audio(self, script_text: str) -> str:
        """
        Generates audio using Piper TTS.
        """
        if not os.path.exists(self.binary_path):
            raise FileNotFoundError(f"Piper binary not found at {self.binary_path}. Please download it.")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Piper model not found at {self.model_path}. Please download a model.")

        output_filename = f"audio_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(self.output_dir, output_filename)
        
        logger.info(f"Generating audio to {output_path}...")

        try:
            # Set espeak-ng data path for Windows
            env = os.environ.copy()
            espeak_data_path = os.path.join(os.path.dirname(self.binary_path), "espeak-ng-data")
            if os.path.exists(espeak_data_path):
                env["ESPEAK_DATA_PATH"] = espeak_data_path
            
            # Piper takes input from stdin and outputs to a file
            command = [
                self.binary_path,
                "--model", self.model_path,
                "--output_file", output_path
            ]
            
            process = subprocess.Popen(
                command, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env
            )
            
            stdout, stderr = process.communicate(input=script_text)
            
            if process.returncode != 0:
                logger.error(f"Piper TTS failed: {stderr}")
                raise RuntimeError(f"Piper TTS failed with exit code {process.returncode}")
                
            return output_path

        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            raise
