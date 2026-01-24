# Setup Guide - Download Required Files

This project requires some large binary files that are NOT included in the Git repository due to GitHub's 50MB file size limit.

## Required Downloads

### 1. Piper TTS (Required)

**Piper Binary** (~10MB)
- **Download**: https://github.com/rhasspy/piper/releases
- **File**: `piper_windows_amd64.zip` (or your OS version)
- **Extract to**: `assets/piper/`
- **Expected files**:
  ```
  assets/piper/
  ├── piper.exe
  ├── espeak-ng.dll
  ├── onnxruntime.dll
  └── other DLLs
  ```

**Voice Model** (~60MB) - This is what caused your GitHub error!
- **Download**: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ryan/medium
- **Files needed**:
  - `en_US-ryan-medium.onnx` (60MB)
  - `en_US-ryan-medium.onnx.json` (5KB)
- **Place in**: `assets/voices/`

### 2. Stock Videos (Optional)

For background visuals:
- **Sources**: 
  - https://www.pexels.com/videos/
  - https://pixabay.com/videos/
- **Format**: MP4, vertical (9:16) preferred
- **Place in**: `assets/stock_videos/`
- **Recommendation**: Download 5-10 generic videos (nature, space, abstract)

### 3. Background Music (Optional)

For professional touch:
- **Sources**:
  - YouTube Audio Library: https://studio.youtube.com/ (Audio Library section)
  - Pixabay Music: https://pixabay.com/music/
- **Format**: MP3 or WAV
- **Place in**: `assets/music/`
- **Recommendation**: 3-5 ambient/lo-fi tracks

---

## Quick Setup Checklist

```bash
# 1. Clone repo
git clone <your-repo-url>
cd yt-shorts-automation

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Download Piper (REQUIRED)
# - Visit: https://github.com/rhasspy/piper/releases
# - Download for your OS
# - Extract to assets/piper/

# 4. Download Voice Model (REQUIRED)
# - Visit: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ryan/medium
# - Download .onnx and .json files
# - Place in assets/voices/

# 5. Setup Ollama
ollama pull mistral
ollama serve  # Keep running

# 6. Setup YouTube API
# - Create OAuth credentials at console.cloud.google.com
# - Download client_secrets.json to config/

# 7. Test it!
python main.py "Test Topic"
```

---

## Verification

Run this to check if all files are in place:

```bash
# Check Piper
dir assets\piper\piper.exe

# Check Voice Model
dir assets\voices\en_US-ryan-medium.onnx

# Check config
dir config\settings.yaml
```

---

## Why These Files Aren't in Git

- **File Size**: Voice model is 60MB (GitHub limit: 50MB)
- **Binary Files**: Not suitable for version control
- **License**: Some files have specific distribution requirements
- **Flexibility**: Users can choose their own voices/music

---

## Alternative: Git LFS (Advanced)

If you want to include large files in your own fork:

```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.onnx"
git lfs track "*.exe"
git lfs track "*.dll"

# Commit
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

Note: Git LFS has storage limits on free tier.
