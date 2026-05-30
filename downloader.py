import os
import re
import yt_dlp
from datetime import date


def _sanitize(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def fetch_playlist_videos(playlist_url: str, cutoff_date: date, processed_ids: set) -> list[dict]:
    """Return list of unprocessed video metadata from a playlist."""
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

    playlist_name = _sanitize(info.get("title", "Unknown Playlist"))
    videos = []
    for entry in info.get("entries", []):
        video_id = entry.get("id")
        if not video_id or video_id in processed_ids:
            continue
        upload_str = entry.get("upload_date")  # YYYYMMDD string or None
        if upload_str:
            upload_date = date(int(upload_str[:4]), int(upload_str[4:6]), int(upload_str[6:8]))
            if upload_date < cutoff_date:
                continue
        videos.append({
            "id": video_id,
            "title": _sanitize(entry.get("title", video_id)),
            "upload_date": upload_str,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "playlist": playlist_name,
        })
    return videos


def fetch_single_video(url: str, processed_ids: set) -> dict | None:
    """Return metadata for a single video if not already processed."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    video_id = info.get("id")
    if not video_id or video_id in processed_ids:
        return None
    return {
        "id": video_id,
        "title": _sanitize(info.get("title", video_id)),
        "upload_date": info.get("upload_date"),
        "url": url,
        "playlist": "Individual Videos",
    }


def download_audio(video: dict, tmp_dir: str) -> str:
    """Download best audio to tmp_dir, return path to downloaded file."""
    out_template = os.path.join(tmp_dir, f"{video['id']}.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video["url"]])

    return os.path.join(tmp_dir, f"{video['id']}.mp3")
