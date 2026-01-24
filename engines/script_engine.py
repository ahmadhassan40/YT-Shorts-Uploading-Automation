import requests
import json
import logging
from typing import Dict, Any
from core.engine_interface import ScriptEngine
from config.config_loader import config

logger = logging.getLogger(__name__)

class OllamaScriptEngine(ScriptEngine):
    def __init__(self):
        self.base_url = config.get("ollama.base_url", "http://localhost:11434")
        self.model = config.get("ollama.model", "mistral")
        
    def generate_script(self, topic: str) -> Dict[str, Any]:
        """
        Generates a YouTube Shorts script using Ollama.
        """
        logger.info(f"Generating script for topic '{topic}' using Ollama model '{self.model}'...")
        
        prompt = f"""You are a professional YouTube Shorts scriptwriter. Write a script about: {topic}

CRITICAL RULES:
1. Output ONLY a JSON object, nothing else
2. DO NOT include labels like "Hook:", "Body:", "CTA:" in the script text itself
3. The script content should be natural speech - as if you're talking to a friend
4. Duration: 30-60 seconds when spoken aloud
5. NO website references, external links, or "check our website" lines
6. CTA must naturally include "like, subscribe, and share"

JSON FORMAT (copy this structure exactly):
{{
  "title": "write a catchy 60-character title here",
  "description": "write 2-3 sentences about the video here, followed by #shorts #viral #topic #keyword #trending",
  "hook": "write opening sentence here (no label, just the sentence)",
  "body": "write main content here (no label, just natural speech with facts and examples)",
  "cta": "write closing with like/subscribe/share here (no label, just natural speech)"
}}

EXAMPLE OF CORRECT FORMAT:
{{
  "title": "Coffee's 1000-Year Journey to Your Cup",
  "description": "Discover how coffee went from Ethiopian goats to the world's favorite drink in just 1000 years! #coffee #history #shorts #viral #facts",
  "hook": "A goat herder in 850 AD noticed something strange about his goats",
  "body": "They were dancing after eating red berries! The herder tried them and felt incredibly energized. Monks started using these berries to stay awake during prayers. By the 1600s, coffee houses spread across Europe and became centers of intellect and business. Today, we drink over 2 billion cups of coffee every single day worldwide",
  "cta": "If coffee gets you going too, smash that like button, subscribe for more amazing history, and share this with your coffee-loving friends"
}}

WRONG EXAMPLE (DO NOT DO THIS):
{{
  "hook": "Hook: Did you know?",
  "body": "Body: Here is the information...",
  "cta": "CTA: Like and subscribe"
}}

Now write the script for: {topic}

Return ONLY the JSON object.
"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,  # Enable streaming to avoid timeout
            "options": {
                "temperature": 0.7,
                "num_predict": 800  # Allow longer, more detailed responses
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=300, stream=True)
            response.raise_for_status()
            
            # Collect streamed response
            generated_text = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        generated_text += chunk["response"]
                    if chunk.get("done", False):
                        break
            
            logger.debug(f"Ollama Raw Output: {generated_text}")
            
            # Try to extract JSON from the response (models sometimes add extra text)
            script_data = None
            
            # First, try direct JSON parse
            try:
                script_data = json.loads(generated_text)
            except json.JSONDecodeError:
                # Try to find JSON object in the text
                import re
                json_match = re.search(r'\{[^}]*"title"[^}]*"description"[^}]*"hook"[^}]*"body"[^}]*"cta"[^}]*\}', generated_text, re.DOTALL)
                if json_match:
                    try:
                        script_data = json.loads(json_match.group(0))
                    except:
                        pass
            
            # If still no valid JSON, create a simple fallback
            if not script_data:
                logger.warning("Could not parse JSON, creating fallback script")
                script_data = {
                    "title": f"{topic} - Must See!",
                    "description": f"Discover amazing facts about {topic}! #shorts #viral #{topic.replace(' ', '')}",
                    "hook": "Did you know?",
                    "body": generated_text[:200] if generated_text else f"Here's an interesting fact about {topic}.",
                    "cta": "Like, subscribe, and share for more amazing content!"
                }
            
            # Validate keys
            required_keys = ["title", "description", "hook", "body", "cta"]
            if not all(k in script_data for k in required_keys):
                logger.warning("Missing required keys, adding defaults")
                script_data.setdefault("title", f"{topic} - YouTube Shorts")
                script_data.setdefault("description", f"Watch this amazing video about {topic}! #shorts #viral #{topic.replace(' ', '')}")
                script_data.setdefault("hook", "Check this out!")
                script_data.setdefault("body", f"Interesting facts about {topic}")
                script_data.setdefault("cta", "Like, subscribe, and share for more!")
                
            return script_data
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama at {self.base_url}. Is it running?")
            raise
        except json.JSONDecodeError:
            logger.error("Failed to parse Ollama output as JSON.")
            raise
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
