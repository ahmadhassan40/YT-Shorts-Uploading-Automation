# YT_BOT User Guide

## Table of Contents
1. [Single Video Generation](#single-video-generation)
2. [Batch Processing](#batch-processing)
3. [Scheduler (Automated Daily Uploads)](#scheduler)
4. [Background Music](#background-music)
5. [Tips & Best Practices](#tips--best-practices)

---

## Single Video Generation

### Basic Usage
Generate a single video about any topic:

```powershell
python main.py "Your Topic Here"
```

### Example
```powershell
python main.py "The History of Ancient Rome"
```

**What Happens**:
1. ✅ Ollama generates an informative script with title and description
2. ✅ Piper TTS creates voiceover audio
3. ✅ Whisper generates subtitles
4. ✅ FFmpeg renders video with background video + subtitles + (optional music)
5. ✅ Uploads to YouTube with SEO-optimized metadata

**Output**: YouTube video URL printed to console

---

## Batch Processing

### What Is It?
Process multiple video topics automatically from a text file - hands-free video generation!

### Step-by-Step Guide

#### Step 1: Create Your Topics List
Edit the `topics.txt` file (already exists in your project):

```powershell
notepad topics.txt
```

**Format** (one topic per line):
```txt
# Lines starting with # are comments (ignored)
The Evolution of Smartphones
Amazing Deep Sea Creatures  
How the Internet Changed Everything
The Science Behind Dreams
Ancient Egyptian Mysteries
```

#### Step 2: Run Batch Processor
```powershell
python batch_processor.py
```

**What Happens**:
- Processes each topic sequentially
- Shows progress: "Processing topic 3/10: Amazing Deep Sea Creatures"
- Logs success ✅ or failure ❌ for each topic
- Prints summary at the end:
  ```
  ========================================================
  BATCH PROCESSING SUMMARY
  ========================================================
  Total topics: 10
  ✅ Successful: 6
  ❌ Failed: 4
  ```

#### Step 3: Check Results
- **Success Log**: Check terminal output for uploaded video URLs
- **Error Log**: If any failed, check `batch_errors.log` for details
  ```powershell
  cat batch_errors.log
  ```

### Important Limits

⚠️ **YouTube API Quota**: Free tier allows **~6 uploads per day**
- If processing 10 topics, expect 4 to fail after quota exhausted
- Wait 24 hours and retry failed topics
- OR request quota increase from Google Cloud Console

**Recommendation**: Process 5-6 topics per day maximum

---

## Scheduler (Automated Daily Uploads)

### What Is It?
Automatically run batch processing or single video generation at a specific time every day - set it and forget it!

### Step-by-Step Guide

#### Step 1: Configure Scheduler
Edit `config/settings.yaml`:

```powershell
notepad config\settings.yaml
```

Find the `scheduler` section and update:

```yaml
scheduler:
  enabled: true          # CHANGE TO TRUE
  mode: "batch"          # Options: "batch" or "single"
  run_time: "09:00"      # Change to your preferred time (24-hour format)
  default_topic: "Trending Topic of the Day"  # Used if mode is "single"
```

**Mode Options**:
- **`batch`**: Processes all topics from `topics.txt`
- **`single`**: Generates one video with the default_topic

#### Step 2: Prepare Topics (if using batch mode)
Ensure `topics.txt` has your topics (max 5-6 to respect quota)

#### Step 3: Start the Scheduler
```powershell
python scheduler.py
```

**What Happens**:
```
🕐 Scheduler started!
   Mode: batch
   Daily run time: 09:00
Waiting for scheduled time...
```

The script will:
- ✅ Run continuously (keep the terminal open)
- ✅ Execute at 09:00 every day
- ✅ Process videos automatically
- ✅ Repeat daily until you stop it (Ctrl+C)

#### Step 4: Run in Background (Optional)

**Windows (PowerShell)**:
```powershell
# Start in background
Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden

# Or use Task Scheduler for startup
```

**Alternative: Windows Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 09:00
4. Action: Start a program → `python.exe`
5. Arguments: `d:\AI_YouTube_Shorts_Implementation\scheduler.py`

### Scheduler Examples

**Example 1: Daily Batch Upload at 9 AM**
```yaml
scheduler:
  enabled: true
  mode: "batch"
  run_time: "09:00"
```

**Example 2: Daily Single Video at Midnight**
```yaml
scheduler:
  enabled: true
  mode: "single"
  run_time: "00:00"
  default_topic: "Daily Tech News Summary"
```

---

## Background Music

### What Is It?
Automatically add royalty-free background music to your videos for a more professional feel!

### Step-by-Step Guide

#### Step 1: Download Music Tracks
Get royalty-free music from these sources:

1. **YouTube Audio Library** (Best option)
   - Go to: https://studio.youtube.com/
   - Click: Audio Library
   - Download ambient/cinematic tracks

2. **Pixabay Music**
   - URL: https://pixabay.com/music/
   - Filter by genre (Lo-Fi, Ambient, Electronic)
   - Download as MP3

3. **Free Music Archive**
   - URL: https://freemusicarchive.org/
   - Search for Creative Commons tracks

**Recommended Genres**:
- Ambient (calm, background)
- Lo-Fi (trendy, popular on YouTube)
- Cinematic (epic, engaging)

#### Step 2: Add Music to Your Project
Simply drag and drop MP3 files into:
```
d:\AI_YouTube_Shorts_Implementation\assets\music\
```

**Supported Formats**: MP3, WAV, M4A

**Example**:
```
assets/music/
├── ambient-background-1.mp3
├── lofi-chill-vibes.mp3
└── cinematic-epic.mp3
```

#### Step 3: Configure Volume (Optional)
Edit `config/settings.yaml`:

```yaml
music:
  enabled: true
  tracks_dir: "assets/music"
  volume: -20  # dB reduction (negative value)
```

**Volume Guide**:
- `-30`: Very quiet, barely audible
- `-20`: **Recommended** - subtle background
- `-15`: Noticeable but not overpowering
- `-10`: Loud, may interfere with voice

#### Step 4: Generate Video
Run as normal:
```powershell
python main.py "Amazing Space Facts"
```

**What Happens**:
- ✅ System randomly selects one track from `assets/music/`
- ✅ Music is mixed with voiceover at configured volume
- ✅ Music loops if shorter than video
- ✅ Final video has professional background music!

### Disable Background Music
If you want videos without music:

**Option 1: Remove all music files** from `assets/music/`

**Option 2: Disable in settings**:
```yaml
music:
  enabled: false
```

---

## Tips & Best Practices

### For Batch Processing
✅ **Do**:
- Process 5-6 topics per day (quota limit)
- Use descriptive topic names
- Review `batch_errors.log` if failures occur

❌ **Don't**:
- Process 10+ topics in one run (will hit quota)
- Use offensive or copyrighted topic names
- Run while Ollama is not running

### For Scheduler
✅ **Do**:
- Keep terminal/computer running
- Use Task Scheduler for reliability
- Set realistic run_time (when computer is on)

❌ **Don't**:
- Close the scheduler terminal
- Set run_time when computer is asleep
- Forget to update `topics.txt`

### For Background Music
✅ **Do**:
- Use instrumental tracks (no vocals)
- Choose calm, ambient music
- Test volume levels (-20dB recommended)
- Use 30-60 second loops

❌ **Don't**:
- Use copyrighted mainstream music
- Set volume too high (drowns out voice)
- Use multiple genres (maintain consistency)

---

## Quick Reference

### Common Commands
```powershell
# Single video
python main.py "Topic Name"

# Batch processing
python batch_processor.py

# Scheduler (runs continuously)
python scheduler.py

# Check errors
cat batch_errors.log
```

### File Locations
```
topics.txt                    # Your batch topics
config/settings.yaml          # All configuration
assets/music/*.mp3            # Background music
batch_errors.log              # Error details
output/*.mp4                  # Generated videos
```

### Need Help?
- See [TROUBLESHOOTING.md](file:///d:/AI_YouTube_Shorts_Implementation/TROUBLESHOOTING.md) for upload failures
- Check logs in terminal for real-time errors
- Ensure all external tools are running (Ollama, FFmpeg)
