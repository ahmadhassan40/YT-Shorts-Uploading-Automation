# Actions Required to Run YT_BOT

You have a fully implemented AI YouTube Shorts automation system! However, since it relies on local AI models and protected APIs, you must perform the following setup steps before running it.

## 1. Setup Ollama (Script Engine)
- [x] **Install Ollama**: Download from [ollama.com](https://ollama.com/).
- [ ] **Pull Model**: Run `ollama pull mistral` in your terminal.
- [ ] **Run Server**: Ensure `ollama serve` is running in a background terminal.

## 2. Setup Piper TTS (Audio Engine)
- [x] **Download Binary**: Get the latest release from [rhasspy/piper](https://github.com/rhasspy/piper/releases).
- [ ] **Extract**: Place the `piper.exe` (and DLLs) in: `d:\AI_YouTube_Shorts_Implementation\assets\piper\`
- [ ] **Download Voice**: Get an ONNX model (e.g., `en_US-ryans-medium.onnx`) and its `.json` config.
- [ ] **Place Voice**: Put the `.onnx` and `.json` files in: `d:\AI_YouTube_Shorts_Implementation\assets\voices\`

## 3. Setup Stock Videos (Video Engine)
- [x] **Create Folder**: Ensure `d:\AI_YouTube_Shorts_Implementation\assets\stock_videos\` exists. (Created automatically)
- [ ] **Add Videos**: Download some royalty-free vertical (9:16) videos (e.g., from Pexels/Pixabay) and place them in this folder. The system picks a random one for the background.

## 4. Setup YouTube API (Upload Engine)
- [ ] **Google Cloud Console**: Go to [console.cloud.google.com](https://console.cloud.google.com/).
- [ ] **New Project**: Create a project and enable "YouTube Data API v3".
- [ ] **Credentials**: Create an "OAuth 2.0 Client ID" (Desktop App).
- [ ] **Download JSON**: Download the client secrets JSON file.
- [ ] **Save**: Rename it to `client_secrets.json` and place it in: `d:\AI_YouTube_Shorts_Implementation\config\`
- [ ] **First Run**: The first time you run the bot, a browser window will open asking you to log in to your Google account.

## 5. First Run
Once the above are done, run:
```bash
python main.py "The History of Coffee"
```
