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


def _parse_env_list(key: str) -> list[str]:
    raw = os.getenv(key, "").strip()
    return [u.strip() for u in raw.split("|") if u.strip()]


def _output_path(output_dir: str, video: dict) -> str:
    upload_str = video.get("upload_date") or datetime.utcnow().strftime("%Y%m%d")
    d = date(int(upload_str[:4]), int(upload_str[4:6]), int(upload_str[6:8]))
    filename = f"{d.isoformat()} - {video['title']}.txt"
    return os.path.join(output_dir, video["playlist"], filename)


def run(dry_run: bool = False) -> None:
    output_dir = os.getenv("OUTPUT_DIR", "transcripts")
    whisper_model = os.getenv("WHISPER_MODEL", "medium")
    cutoff_str = os.getenv("CUTOFF_DATE", "2020-01-01")
    cutoff_date = date.fromisoformat(cutoff_str)

    playlist_urls = _parse_env_list("YOUTUBE_PLAYLISTS")
    video_urls = _parse_env_list("YOUTUBE_VIDEOS")

    log.info("=== Run started (dry_run=%s) ===", dry_run)
    log.info("Cutoff date: %s | Whisper model: %s", cutoff_date, whisper_model)

    processed_ids = load_processed_ids()
    videos_to_process: list[dict] = []

    for url in playlist_urls:
        log.info("Fetching playlist: %s", url)
        try:
            videos = fetch_playlist_videos(url, cutoff_date, processed_ids)
            log.info("  Found %d new video(s)", len(videos))
            videos_to_process.extend(videos)
        except Exception as e:
            log.error("  Failed to fetch playlist %s: %s", url, e)

    for url in video_urls:
        log.info("Fetching video: %s", url)
        try:
            video = fetch_single_video(url, processed_ids)
            if video:
                log.info("  New: %s", video["title"])
                videos_to_process.append(video)
            else:
                log.info("  Already processed or unavailable")
        except Exception as e:
            log.error("  Failed to fetch video %s: %s", url, e)

    if not videos_to_process:
        log.info("No new videos to process. Done.")
        return

    log.info("Total new videos: %d", len(videos_to_process))

    if dry_run:
        log.info("--- DRY RUN: would process ---")
        for v in videos_to_process:
            log.info("  [%s] %s / %s", v["id"], v["playlist"], v["title"])
        return

    success, failed = 0, 0

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

    log.info("=== Run complete: %d succeeded, %d failed ===", success, failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bloomberg transcript downloader")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without downloading")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
