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

1. HOOK (first 2-3 seconds)
   - Start with a strong, curiosity-inducing line
   - Must instantly grab attention
   - Can be a shocking fact, question, or surprising statement
   - Do NOT introduce the topic plainly
   - Example style:
     "Did you know...?"
     "This almost changed history forever..."
     "One mistake that cost millions of lives..."

2. MAIN CONTENT
   - Explain the topic clearly and concisely
   - Use short sentences suitable for subtitles
   - Maintain a fast-paced, engaging flow
   - Avoid unnecessary details
   - Focus only on the most interesting and important facts
   - Ensure factual accuracy
   - This section MUST be long enough so the total video is at least 30 seconds

3. ENDING / CALL TO ACTION
   - End with a short CTA encouraging engagement
   - Mention: Like, Share, Comment, and Subscribe
   - Keep it natural and friendly

OUTPUT FORMAT (VERY IMPORTANT):
Return the output in the following JSON format ONLY:

{{
  "title": "<short catchy title for the video>",
  "description": "<short YouTube description with hashtags>",
  "visual_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "script": [
    {{
      "timestamp": "0-3s",
      "text": "<hook line>"
    }},
    {{
      "timestamp": "3-45s",
      "text": "<main content text — must be detailed enough for at least 27 seconds of narration>"
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
- Do NOT include emojis
- Do NOT include markdown
- Do NOT add explanations
- Do NOT add anything outside the JSON
- The script must be optimized for voice-over and subtitles
- Keep sentences short and clear
- Avoid complex words
- VIDEO MUST be at least 30 seconds when narrated aloud at normal pace
- Expand the main content section as much as needed to hit 30-60 seconds
- visual_keywords: 5 terms to search for relevant background footage

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
            
            # ── STEP 1: Ensure script key exists and is a list ─────────────────────
            if "script" not in script_data or not isinstance(script_data["script"], list):
                logger.warning("Script key missing or invalid — checking for legacy format.")
                if isinstance(script_data, dict) and "hook" in script_data:
                    script_data["script"] = [
                        {"timestamp": "0-3s",   "text": script_data.get("hook", "")},
                        {"timestamp": "3-45s",  "text": script_data.get("body", script_data.get("main", ""))},
                        {"timestamp": "45-60s", "text": script_data.get("cta", script_data.get("ending", ""))},
                    ]
                else:
                    script_data["script"] = []

            # ── STEP 2: Normalize each segment to a dict with a "text" key ─────────
            normalized = []
            for i, seg in enumerate(script_data["script"]):
                if isinstance(seg, dict):
                    if "text" not in seg or not seg["text"].strip():
                        continue          # skip empty segments
                    normalized.append(seg)
                elif isinstance(seg, str) and seg.strip():
                    logger.warning(f"Segment {i} is a plain string — wrapping into dict.")
                    normalized.append({"timestamp": f"{i*15}-{(i+1)*15}s", "text": seg.strip()})
                else:
                    logger.warning(f"Segment {i} has unexpected type {type(seg)} — skipping.")
            script_data["script"] = normalized

            # ── STEP 3: ENFORCE 3-SECTION STRUCTURE: hook / main / ending ──────────
            # Defaults used when model failed to produce a section
            DEFAULT_HOOK    = f"Did you know this shocking fact about {topic}?"
            DEFAULT_MAIN    = f"Here are the most fascinating and surprising facts about {topic}. It has a hidden history that most people have never heard of. Experts have studied it for years and the findings are truly remarkable."
            DEFAULT_ENDING  = "If you enjoyed this, please like, comment, share, and subscribe for more amazing content!"

            CTA_KEYWORDS = ["subscribe", "like", "share", "follow", "comment"]

            def _has_cta(text: str) -> bool:
                return any(w in text.lower() for w in CTA_KEYWORDS)

            segs = script_data["script"]
            n = len(segs)

            if n == 0:
                # Model returned absolutely nothing — inject all 3 defaults
                logger.warning("Script is empty — injecting all 3 default sections.")
                script_data["script"] = [
                    {"timestamp": "0-3s",   "text": DEFAULT_HOOK},
                    {"timestamp": "3-45s",  "text": DEFAULT_MAIN},
                    {"timestamp": "45-60s", "text": DEFAULT_ENDING},
                ]

            elif n == 1:
                # Only one segment — treat it as main content, inject hook + ending
                logger.warning("Only 1 segment found — injecting missing hook and ending.")
                main_text = segs[0]["text"]
                script_data["script"] = [
                    {"timestamp": "0-3s",   "text": DEFAULT_HOOK},
                    {"timestamp": "3-45s",  "text": main_text},
                    {"timestamp": "45-60s", "text": DEFAULT_ENDING},
                ]

            elif n == 2:
                # Two segments found. Check if ending is missing.
                last_text = segs[-1]["text"]
                if not _has_cta(last_text):
                    logger.warning("2 segments found, last has no CTA — appending ending.")
                    script_data["script"].append({"timestamp": "45-60s", "text": DEFAULT_ENDING})
                else:
                    # Last segment IS the CTA, so inject a hook at the front if very short
                    current_hook = segs[0]["text"]
                    if len(current_hook.split()) < 20:
                        logger.info("2-segment script: treating first as hook, second as ending — inserting main.")
                        script_data["script"] = [
                            segs[0],
                            {"timestamp": "3-45s", "text": DEFAULT_MAIN},
                            segs[1],
                        ]

            else:
                # 3+ segments. Find and validate the ending/CTA specifically.
                last_seg = script_data["script"][-1]
                if not _has_cta(last_seg.get("text", "")):
                    # Last segment is not a CTA — see if any other segment is
                    cta_indices = [
                        i for i, s in enumerate(script_data["script"])
                        if _has_cta(s.get("text", ""))
                    ]
                    if cta_indices:
                        # Move the CTA segment to the very end
                        cta_seg = script_data["script"].pop(cta_indices[-1])
                        script_data["script"].append(cta_seg)
                        logger.info("Moved CTA segment to end of script.")
                    else:
                        # No CTA anywhere — append one
                        logger.warning("No CTA found in any segment — appending ending.")
                        script_data["script"].append({"timestamp": "55-60s", "text": DEFAULT_ENDING})

            # ── STEP 4: Ensure metadata fields exist ───────────────────────────────
            if "title" not in script_data or not script_data["title"].strip():
                script_data["title"] = f"{topic} - Shocking Facts"

            if "description" not in script_data or not script_data["description"].strip():
                script_data["description"] = f"Amazing facts about {topic}! #shorts #viral #facts"

            if "visual_keywords" not in script_data or not isinstance(script_data["visual_keywords"], list) or len(script_data["visual_keywords"]) == 0:
                cleanup = topic.lower().replace("history of", "").replace("facts", "").strip()
                script_data["visual_keywords"] = [cleanup, "technology", "abstract", "background", "nature"]

            # Log final structure for debugging
            logger.info(f"Final script: {len(script_data['script'])} sections — "
                        + " | ".join(f"[{s.get('timestamp','?')}] {s['text'][:30]}..." for s in script_data["script"]))

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
