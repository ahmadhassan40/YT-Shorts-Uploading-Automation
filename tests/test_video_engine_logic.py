from engines.video_engine import FFmpegVideoEngine

e = FFmpegVideoEngine()

# Test filter_complex for 3 clips, no music
fc = e._build_filter_complex(3, "ass='subs.ass'", -20, False)
print("== 3 clips, no music ==")
print(fc)
print()

# Test filter_complex for 1 clip, with music
fc1 = e._build_filter_complex(1, "ass='subs.ass'", -20, True)
print("== 1 clip, with music ==")
print(fc1)
print()

# Test safe folder name
print("Folder:", e._safe_folder_name("History of: Rome / Italy?"))
print("Folder:", e._safe_folder_name("What is AI?"))
print("Folder:", e._safe_folder_name("The Rise of the Roman Empire"))
