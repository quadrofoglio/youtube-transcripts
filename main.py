import argparse
import logging
import os
import sys
import tempfile
from datetime import date, datetime

from dotenv import load_dotenv

from downloader import download_audio, fetch_playlist_videos, fetch_single_video
from state import load_processed_ids, mark_processed
from transcriber import transcribe

load_dotenv()

LOG_FILE = os.path.join(os.path.dirname(__file__), "run.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def _parse_env_entries(key: str) -> list[tuple[str, str]]:
    """Parse 'Name::URL|Name::URL' into list of (name, url) tuples."""
    raw = os.getenv(key, "").strip()
    entries = []
    for part in raw.split("|"):
        part = part.strip()
        if not part:
            continue
        if "::" in part:
            name, url = part.split("::", 1)
            entries.append((name.strip(), url.strip()))
        else:
            entries.append(("Unknown", part))
    return entries


AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus"}


def _output_path(output_dir: str, video: dict) -> str:
    upload_str = video.get("upload_date") or datetime.utcnow().strftime("%Y%m%d")
    d = date(int(upload_str[:4]), int(upload_str[4:6]), int(upload_str[6:8]))
    filename = f"{d.isoformat()} - {video['title']}.txt"
    return os.path.join(output_dir, video["playlist"], filename)


def _collect_inbox_files(inbox_dir: str, processed_ids: set) -> list[tuple[str, str, str]]:
    """Return list of (audio_path, stem, show_name) for all unprocessed audio files.

    Files in the root inbox_dir use 'Local Audio' as the show name.
    Files in a subfolder use the subfolder name as the show name.
    """
    items = []
    for entry in os.scandir(inbox_dir):
        if entry.is_file() and os.path.splitext(entry.name)[1].lower() in AUDIO_EXTENSIONS:
            stem = os.path.splitext(entry.name)[0]
            if stem not in processed_ids:
                items.append((entry.path, stem, "Local Audio"))
        elif entry.is_dir():
            show_name = entry.name
            for sub in os.scandir(entry.path):
                if sub.is_file() and os.path.splitext(sub.name)[1].lower() in AUDIO_EXTENSIONS:
                    stem = os.path.splitext(sub.name)[0]
                    unique_id = f"{show_name}/{stem}"
                    if unique_id not in processed_ids:
                        items.append((sub.path, unique_id, show_name))
    return items


def _process_audio_inbox(inbox_dir: str, output_dir: str, whisper_model: str, processed_ids: set, dry_run: bool) -> tuple[int, int]:
    if not os.path.isdir(inbox_dir):
        return 0, 0

    items = _collect_inbox_files(inbox_dir, processed_ids)

    if not items:
        return 0, 0

    log.info("Audio inbox: %d file(s) to transcribe", len(items))

    if dry_run:
        for _, stem, show in items:
            log.info("  [DRY RUN] Would transcribe: %s / %s", show, stem)
        return 0, 0

    success, failed = 0, 0
    for audio_path, unique_id, show_name in items:
        filename = os.path.basename(audio_path)
        stem = os.path.splitext(filename)[0]
        out_path = os.path.join(output_dir, show_name, f"{stem}.txt")
        log.info("Transcribing: %s / %s", show_name, filename)
        try:
            transcribe(audio_path, whisper_model, out_path)
            mark_processed(unique_id, stem, show_name)
            os.remove(audio_path)
            log.info("  Saved: %s", out_path)
            success += 1
        except Exception as e:
            log.error("  FAILED %s: %s", filename, e)
            failed += 1

    return success, failed


def run(dry_run: bool = False) -> None:
    output_dir = os.getenv("OUTPUT_DIR", "transcripts")
    whisper_model = os.getenv("WHISPER_MODEL", "medium")
    cutoff_str = os.getenv("CUTOFF_DATE", "2020-01-01")
    cutoff_date = date.fromisoformat(cutoff_str)
    inbox_dir = os.getenv("AUDIO_INBOX_DIR", os.path.join(os.path.dirname(__file__), "audio_inbox"))

    playlist_entries = _parse_env_entries("YOUTUBE_PLAYLISTS")
    video_entries = _parse_env_entries("YOUTUBE_VIDEOS")

    log.info("=== Run started (dry_run=%s) ===", dry_run)
    log.info("Cutoff date: %s | Whisper model: %s", cutoff_date, whisper_model)

    processed_ids = load_processed_ids()
    videos_to_process: list[dict] = []

    for name, url in playlist_entries:
        log.info("Fetching playlist: %s", name)
        try:
            videos = fetch_playlist_videos(url, name, cutoff_date, processed_ids)
            log.info("  Found %d new video(s)", len(videos))
            videos_to_process.extend(videos)
        except Exception as e:
            log.error("  Failed to fetch playlist %s: %s", name, e)

    for name, url in video_entries:
        log.info("Fetching video: %s", name)
        try:
            video = fetch_single_video(url, name, processed_ids)
            if video:
                log.info("  New: %s", video["title"])
                videos_to_process.append(video)
            else:
                log.info("  Already processed or unavailable")
        except Exception as e:
            log.error("  Failed to fetch video %s: %s", name, e)

    success, failed = 0, 0

    if videos_to_process:
        log.info("Total new videos: %d", len(videos_to_process))

        if dry_run:
            log.info("--- DRY RUN: would process ---")
            for v in videos_to_process:
                log.info("  [%s] %s / %s", v["id"], v["playlist"], v["title"])
        else:
            with tempfile.TemporaryDirectory() as tmp_dir:
                for video in videos_to_process:
                    log.info("Processing: %s - %s", video["playlist"], video["title"])
                    audio_path = None
                    try:
                        audio_path = download_audio(video, tmp_dir)
                        out_path = _output_path(output_dir, video)
                        transcribe(audio_path, whisper_model, out_path)
                        mark_processed(video["id"], video["title"], video["playlist"])
                        log.info("  Saved: %s", out_path)
                        success += 1
                    except Exception as e:
                        log.error("  FAILED %s: %s", video["id"], e)
                        failed += 1
                    finally:
                        if audio_path and os.path.exists(audio_path):
                            os.remove(audio_path)
    else:
        log.info("No new YouTube videos to process.")

    inbox_success, inbox_failed = _process_audio_inbox(inbox_dir, output_dir, whisper_model, processed_ids, dry_run)
    success += inbox_success
    failed += inbox_failed

    log.info("=== Run complete: %d succeeded, %d failed ===", success, failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bloomberg transcript downloader")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without downloading")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
