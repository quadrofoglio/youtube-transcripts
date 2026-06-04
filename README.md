# Bloomberg Transcript Automation

Downloads audio from YouTube playlists/videos and transcribes them using Whisper. Runs daily via Windows Task Scheduler.

## How it works

1. Fetches new videos from configured YouTube playlists and individual video URLs
2. Skips anything already in `state.csv` or older than `CUTOFF_DATE`
3. Downloads audio, transcribes with Whisper, saves `.txt` files to `OUTPUT_DIR`
4. Optionally transcribes local audio files dropped into `AUDIO_INBOX_DIR`

Transcripts are organised as `OUTPUT_DIR/<Playlist Name>/<YYYY-MM-DD> - <Title>.txt`.

## Setup

**Dependencies**

```
pip install yt-dlp openai-whisper python-dotenv
```

FFmpeg must also be on your PATH (required by yt-dlp for audio extraction).

**Configuration**

Copy `.env.example` to `.env` and fill in your values:

| Variable | Description |
|---|---|
| `YOUTUBE_PLAYLISTS` | `Name::URL` pairs separated by `\|` |
| `YOUTUBE_VIDEOS` | `Name::URL` pairs separated by `\|` for individual videos |
| `CUTOFF_DATE` | Skip videos uploaded before this date (ISO format) |
| `OUTPUT_DIR` | Where transcripts are saved |
| `AUDIO_INBOX_DIR` | Folder to watch for local audio files (optional) |
| `WHISPER_MODEL` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |

## Running

```
python main.py            # normal run
python main.py --dry-run  # preview what would be processed without downloading
```

Logs are written to `run.log` in the project directory.

## Audio inbox

Drop `.mp3`, `.m4a`, `.wav`, `.flac`, `.ogg`, or `.opus` files into `AUDIO_INBOX_DIR` to have them transcribed on the next run. Organise by show using subfolders — files in `audio_inbox/Show Name/` will be saved under `OUTPUT_DIR/Show Name/`.

## Scheduled task (Windows)

The task runs daily at 21:00 SGT via Windows Task Scheduler (`BloombergTranscripts`). The script holds a Windows sleep lock for the duration of the run so the PC does not suspend mid-transcription.

## State tracking

`state.csv` records every processed video/file. Delete a row to reprocess that item on the next run.
