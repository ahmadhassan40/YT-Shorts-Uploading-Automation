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

CHANNEL NICHE: History + Dark Facts + Shocking Truths
TARGET AUDIENCE: People who love discovering hidden historical events, dark secrets, and shocking revelations

SCRIPT STRUCTURE (STRICTLY FOLLOW THIS ORDER):

1. HOOK (0–3 seconds) - CRITICAL FOR SUCCESS
   Choose ONE of these proven hook patterns based on the topic:
   
   A. Hidden Knowledge Pattern:
      - "This historical fact was hidden for centuries..."
      - "They don't teach this dark truth in school..."
      - "What they never told you about [topic]..."
   
   B. Shocking Scale Pattern:
      - "This decision killed millions—and no one talks about it..."
      - "One choice changed history forever—and it was kept secret..."
      - "This mistake cost thousands of lives..."
   
   C. Question Pattern:
      - "Do you know the dark truth behind [topic]?"
      - "Ever wondered why they hide this from history books?"
   
   D. Immediate Shock Pattern:
      - "The truth about [topic] will shock you..."
      - "[Topic] was hiding something sinister..."
   
   REQUIREMENTS:
   - Create immediate curiosity
   - Use dramatic, suspenseful tone
   - NO generic introductions
   - Maximum 10-15 words

2. CONTEXT (3–15 seconds)
   - Who / When / Where - establish the setting
   - Provide just enough background for the story to make sense
   - Use short, punchy sentences (ideal for 2-4 word subtitles)
   - Build anticipation for the dark reveal

3. DARK REVEAL (15–52 seconds) - MAIN CONTENT
   - This is the core shocking content: secret, betrayal, death, cover-up, etc.
   - Include the twist/revelation that justifies the hook
   - Examples of transitions:
     * "But here's what they covered up..."
     * "The truth? Far more sinister..."
     * "What happened next is horrifying..."
   - Layer multiple shocking details if the topic warrants it
   - Maintain suspenseful, dramatic pacing throughout
   - This section can be longer for complex topics (up to ~37 seconds)

4. ENDING (Last 3-5 seconds)
   - Soft, natural CTA - don't be pushy
   - Examples:
     * "More dark truths coming soon. Subscribe."
     * "Want more shocking history? Hit subscribe."
   - Keep it brief and authentic

VIDEO DURATION: 30-60 seconds (flexible based on topic complexity)
- Simple topics: aim for 30-40s
- Complex/layered topics: can extend to 50-60s
- The AI should determine optimal length based on how much shocking content exists

OUTPUT FORMAT:
Return strictly valid JSON with this structure:
{{
  "title": "Video Title",
  "description": "Video Description",
  "visual_keywords": ["keyword1", "keyword2", "keyword3"],
  "script": [
    {{"timestamp": "0-3s", "section": "hook", "text": "Hook text here"}},
    {{"timestamp": "3-15s", "section": "context", "text": "Context text here"}},
    {{"timestamp": "15-52s", "section": "dark_reveal", "text": "Main shocking content here"}},
    {{"timestamp": "52-60s", "section": "ending", "text": "CTA text here"}}
  ],
  "tone": "dark",
  "target_duration_seconds": 60
}}

CRITICAL RULES:
- Output valid JSON only.
- visual_keywords: 5 terms for Pexels search.
- Script text must be narratable (no labels like 'Hook:').
- VIDEO MUST BE AT LEAST 40 SECONDS LONG. This is a "Story Time" video.
- Expand the 'dark_reveal' section to ensure sufficient length.

Now write for: {topic}
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "format": "json",  # Enable native structured output for reliability
            "options": {
                "temperature": 0.7,
                "num_predict": 1200  # Increased token limit for longer scripts
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
                # Ensure it's a dictionary, not a string or list
                if not isinstance(script_data, dict):
                    logger.warning(f"Parsed JSON is {type(script_data)}, expected dict. Trying to recover...")
                    if isinstance(script_data, str):
                        try:
                            # Handle double-encoded JSON
                            script_data = json.loads(script_data)
                        except:
                            script_data = None
                    else:
                        script_data = None
                        
                if not isinstance(script_data, dict):
                     script_data = None

            except json.JSONDecodeError:
                # Try to find JSON object in the text (handling markdown blocks)
                import re
                
                # Check for markdown code blocks first
                code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', generated_text, re.DOTALL)
                if code_block_match:
                    try:
                        potential_data = json.loads(code_block_match.group(1))
                        if isinstance(potential_data, dict):
                            script_data = potential_data
                    except:
                        pass
                
                # If no code block, look for any curly brace block
                if not script_data:
                    json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
                    if json_match:
                        try:
                            potential_data = json.loads(json_match.group(0))
                            if isinstance(potential_data, dict):
                                script_data = potential_data
                        except:
                            pass
            
            # If still no valid JSON, create a simple fallback
            if not script_data:
                logger.warning("Could not parse JSON, creating fallback script")
                # Fallback: Don't use raw text as it contains labels. Use a safe default.
                # Or try to clean the raw text by removing known labels?
                # Better to use a safe default to avoid "Hook statement" being read aloud.
                script_data = {
                    "title": f"{topic} - Must See!",
                    "description": f"Amazing facts about {topic} #shorts",
                    "script": [
                        {"timestamp": "0-5s", "text": f"Here is a shocking fact about {topic}."}, 
                        {"timestamp": "5-50s", "text": "This historical event has secrets that few people know about. It changed everything."},
                        {"timestamp": "50-60s", "text": "Subscribe to find out more!"}
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
