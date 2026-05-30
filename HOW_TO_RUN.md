# How to Run

## First-time setup

### Step 1 — Install the missing package
Open **Anaconda Prompt** (search for it in the Start menu) and run:
```
pip install yt-dlp
```

Optionally upgrade Whisper to the latest version while you're here:
```
pip install --upgrade openai-whisper
```

### Step 2 — Create your .env file
In File Explorer, go to:
```
C:\Users\limfy\OneDrive\Documents\bloomberg transcripts\
```
Copy `.env.example` and rename the copy to `.env`. Open it in Notepad and fill in:

```
YOUTUBE_VIDEOS=https://youtube.com/watch?v=AAA|https://youtube.com/watch?v=BBB
YOUTUBE_PLAYLISTS=https://youtube.com/playlist?list=CCC|https://youtube.com/playlist?list=DDD
CUTOFF_DATE=2025-01-01
OUTPUT_DIR=C:\Users\limfy\OneDrive\Documents\bloomberg transcripts\transcripts
WHISPER_MODEL=medium
```

- `YOUTUBE_VIDEOS` — individual video URLs separated by `|`. Leave blank if none.
- `YOUTUBE_PLAYLISTS` — playlist URLs separated by `|`. Leave blank if none.
- `CUTOFF_DATE` — videos published before this date will never be downloaded.
- `OUTPUT_DIR` — where transcripts are saved. Change this if you want a different folder.
- `WHISPER_MODEL` — options: `tiny`, `base`, `small`, `medium`, `large`. `medium` is recommended.

### Step 3 — Set up the daily schedule
Open **PowerShell** (search for it in the Start menu — no need for Administrator) and run:
```powershell
cd "C:\Users\limfy\OneDrive\Documents\bloomberg transcripts"
.\setup_scheduler.ps1
```
This registers a Windows Task Scheduler job that runs automatically at 9:00 PM every day.

---

## Running manually

Open **Anaconda Prompt** and run:
```
cd "C:\Users\limfy\OneDrive\Documents\bloomberg transcripts"
python main.py
```

### Dry run (see what would be downloaded without downloading anything)
```
python main.py --dry-run
```
Use this to verify your playlist URLs are working correctly before the first real run.

---

## Checking results

- **Transcripts** are saved to the folder you set in `OUTPUT_DIR`, organised by playlist name.
- **Run log** — open `run.log` in the project folder to see what happened in each run (videos processed, any errors).
- **State tracking** — `state.csv` lists every video that has been successfully processed. You can open it in Excel. If you want to re-process a video, delete its row from this file.

---

## Updating playlist/video URLs

Just edit the `.env` file and save. The next run (scheduled or manual) will pick up the changes automatically.

---

## Removing the scheduled task

Open **PowerShell** and run:
```powershell
Unregister-ScheduledTask -TaskName "BloombergTranscripts" -Confirm:$false
```
