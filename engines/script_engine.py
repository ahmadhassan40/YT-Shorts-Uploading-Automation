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
        
        prompt = f"""Write a YouTube Shorts script about: {topic}

SCRIPT STRUCTURE (STRICTLY FOLLOW THIS ORDER):

1. HOOK (first 2–3 seconds)
   - Start with a strong, curiosity-inducing line
   - Must instantly grab attention
   - Can be a shocking fact, question, or surprising statement
   - Do NOT introduce the topic plainly
   - Example style: "Did you know...?", "This almost changed history forever..."

2. MAIN CONTENT
   - Explain the topic clearly and concisely
   - Use short sentences suitable for subtitles
   - Maintain a fast-paced, engaging flow
   - Avoid unnecessary details
   - Ensure factual accuracy

3. ENDING / CALL TO ACTION
   - End with a short CTA encouraging engagement
   - Mention: Like, Share, and Subscribe
   - Keep it natural and friendly

OUTPUT FORMAT (VERY IMPORTANT):
Return the output in the following JSON format ONLY:

{{
  "title": "<short catchy title for the video>",
  "description": "<video description with hashtags>",
  "visual_keywords": ["keyword1", "keyword2", "keyword3"],
  "script": [
    {{
      "timestamp": "0-3s",
      "text": "<hook line>"
    }},
    {{
      "timestamp": "3-45s",
      "text": "<main content text>"
    }},
    {{
      "timestamp": "45-60s",
      "text": "<call to action text>"
    }}
  ],
  "tone": "informative, engaging, dramatic",
  "target_duration_seconds": 60
}}

RULES:
- "visual_keywords": Provide 3-5 single-word search terms for finding background videos (e.g. for 'Rome' use ['colosseum', 'roman', 'ancient']).
- Do NOT include emojis in the script text
- Do NOT include markdown
- The script must be optimized for voice-over
- Keep sentences short and clear
- Assume background visuals will be added later

Now write for: {topic}
Return ONLY the JSON object.
"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "num_predict": 1000  # Increased token limit for structured output
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
                json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
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
                    "description": f"Amazing facts about {topic} #shorts",
                    "script": [
                        {"timestamp": "0-5s", "text": "Did you know?"},
                        {"timestamp": "5-50s", "text": generated_text[:200] if generated_text else f"Here is an interesting fact about {topic}."},
                        {"timestamp": "50-60s", "text": "Like and subscribe for more!"}
                    ],
                    "tone": "informative"
                }
            
            # Validate keys
            if "script" not in script_data or not isinstance(script_data["script"], list):
                logger.warning("Invalid script format, normalizing...")
                # Try to rescue legacy format if model ignored instructions
                if "hook" in script_data and "body" in script_data:
                     script_data["script"] = [
                        {"timestamp": "0-5s", "text": script_data.get("hook", "")},
                        {"timestamp": "5-50s", "text": script_data.get("body", "")},
                        {"timestamp": "50-60s", "text": script_data.get("cta", "")}
                     ]
            
            if "title" not in script_data:
                script_data["title"] = f"{topic} Shorts"
            
            # Ensure visual keywords exist
            if "visual_keywords" not in script_data or not isinstance(script_data["visual_keywords"], list):
                # Fallback: simple keyword extraction from topic
                cleanup = topic.lower().replace("history of", "").replace("facts", "").strip()
                # Add generic fallback terms to ensure Pexels finds something
                script_data["visual_keywords"] = [cleanup, "technology", "abstract", "background", "nature"]

            # Ensure description exists
            if "description" not in script_data:
                script_data["description"] = f"Watch this amazing video about {topic}! #shorts #viral"
            
            # CRITICAL: Force a CTA if missing or too short
            if "script" in script_data and isinstance(script_data["script"], list):
                has_cta = False
                if len(script_data["script"]) > 0:
                    last_segment = script_data["script"][-1]["text"].lower()
                    if any(word in last_segment for word in ["subscribe", "like", "share", "follow"]):
                        has_cta = True
                
                if not has_cta:
                    logger.warning("Script missing CTA, appending mandatory ending.")
                    script_data["script"].append({
                        "timestamp": "55-60s",
                        "text": "If you enjoyed this, please like and subscribe for more amazing facts!"
                    })

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
