# YT_BOT - AI YouTube Shorts Automation

🤖 **Fully automated YouTube Shorts generation and upload system** powered by local AI models.

Generate informative, engaging YouTube Shorts videos automatically with AI-generated scripts, voiceovers, subtitles, and background music - all from a single command!

---

## ✨ Features

- 🎬 **AI Script Generation** with Ollama (Mistral/Llama3)
- 🎤 **Text-to-Speech** using Piper TTS
- 📝 **Auto Subtitles** with Whisper AI
- 🎵 **Background Music** mixing
- 🎨 **Professional Styling** (top-positioned subtitles, 9:16 vertical format)
- 📤 **YouTube Upload** with OAuth 2.0
- 🔄 **Batch Processing** for multiple videos
- ⏰ **Scheduler** for automated daily uploads
- 💯 **100% Free** - uses local AI models

---

## 🎥 Sample Output

Videos include:
- ✅ SEO-optimized titles (max 60 chars)
- ✅ Hashtag-rich descriptions
- ✅ Informative scripts with facts and storytelling
- ✅ Professional voiceover
- ✅ Styled subtitles
- ✅ Background music (optional)

---

## 📋 Prerequisites

### Required Software
1. **Python 3.8+** - [Download](https://www.python.org/downloads/)
2. **FFmpeg** - [Download](https://www.gyan.dev/ffmpeg/builds/)
3. **Ollama** - [Download](https://ollama.com/)
4. **Git** - [Download](https://git-scm.com/)

### External Downloads (Not in Repo)
Due to GitHub file size limits, you must download these manually:

1. **Piper TTS Binary** (~10MB)
   - Download: [Piper Releases](https://github.com/rhasspy/piper/releases)
   - Extract to: `assets/piper/`

2. **Piper Voice Model** (~60MB)
   - Download: [en_US-ryan-medium.onnx](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ryan/medium)
   - Place in: `assets/voices/`

3. **Stock Videos** (Optional, for backgrounds)
   - Download from: [Pexels](https://www.pexels.com/videos/) or [Pixabay](https://pixabay.com/videos/)
   - Place in: `assets/stock_videos/`

4. **Background Music** (Optional)
   - Download from: [YouTube Audio Library](https://studio.youtube.com/) or [Pixabay Music](https://pixabay.com/music/)
   - Place in: `assets/music/`

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/yt-shorts-automation.git
cd yt-shorts-automation
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download External Files
See [Prerequisites](#external-downloads-not-in-repo) above.

### 4. Setup Ollama
```bash
# Install and pull model
ollama pull mistral

# Start Ollama server (keep running)
ollama serve
```

### 5. Setup YouTube API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project and enable "YouTube Data API v3"
3. Create OAuth 2.0 credentials (Desktop App)
4. Download `client_secrets.json` to `config/`

### 6. Generate Your First Video!
```bash
python main.py "The History of the Internet"
```

---

## 📖 Usage

### Single Video
```bash
python main.py "Your Topic Here"
```

### Batch Processing (Interactive)
```bash
python batch_processor.py
# Enter topics one by one when prompted
```

### Automated Daily Uploads
```bash
# 1. Edit config/settings.yaml
scheduler:
  enabled: true
  run_time: "09:00"

# 2. Run scheduler
python scheduler.py
```

---

## ⚙️ Configuration

All settings in `config/settings.yaml`:

```yaml
# Ollama Model
ollama:
  model: "mistral"  # or "llama3.2:1b"

# Background Music
music:
  enabled: true
  volume: -20  # dB

# Scheduler
scheduler:
  enabled: true
  mode: "batch"
  run_time: "09:00"
  auto_generate_topics: false  # AI auto-generates topics
```

---

## 📁 Project Structure

```
yt-shorts-automation/
├── config/
│   ├── settings.yaml          # Configuration
│   └── client_secrets.json    # YouTube OAuth (you create)
├── engines/
│   ├── script_engine.py       # Ollama script generation
│   ├── audio_engine.py        # Piper TTS
│   ├── subtitle_engine.py     # Whisper
│   ├── video_engine.py        # FFmpeg rendering
│   └── upload_engine.py       # YouTube upload
├── assets/
│   ├── piper/                 # Piper binary (you download)
│   ├── voices/                # Voice models (you download)
│   ├── music/                 # Background music (optional)
│   └── stock_videos/          # Background videos (optional)
├── main.py                    # Single video generator
├── batch_processor.py         # Batch processing
├── scheduler.py               # Automated scheduler
└── requirements.txt           # Python dependencies
```

---

## 🔧 Troubleshooting

### YouTube Upload Fails
- **Quota Exceeded**: Free tier allows ~6 uploads/day. Wait 24 hours or request increase.
- **Authentication Error**: Delete `config/token.json` and re-authenticate.

### Ollama Timeout
- Increase timeout in `script_engine.py` or use smaller model (`llama3.2:1b`)

### FFmpeg Not Found
- Add FFmpeg to system PATH

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

---

## 📚 Documentation

- [USER_GUIDE.md](USER_GUIDE.md) - Detailed usage instructions
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [SPECIFICATION.md](SPECIFICATION.md) - Technical specifications

---

## ⚠️ Important Notes

### YouTube API Quotas
- Free tier: **10,000 quota units/day**
- Each upload: **~1,600 units**
- **Practical limit: 5-6 videos/day**

### Large Files (Not in Git)
This repository does NOT include:
- Piper TTS binary and voice models (60MB+)
- Stock videos
- Background music
- Generated outputs

See [Setup Guide](#external-downloads-not-in-repo) for download links.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) - Local AI models
- [Piper TTS](https://github.com/rhasspy/piper) - Text-to-speech
- [Whisper](https://github.com/openai/whisper) - Speech recognition
- [FFmpeg](https://ffmpeg.org/) - Video processing

---

## 📞 Support

For issues and questions:
- Open an [Issue](https://github.com/yourusername/yt-shorts-automation/issues)
- Check [Discussions](https://github.com/yourusername/yt-shorts-automation/discussions)

---

**Made with ❤️ for content creators**
