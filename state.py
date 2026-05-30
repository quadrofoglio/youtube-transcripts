import csv
import os
from datetime import datetime

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.csv")
FIELDNAMES = ["video_id", "title", "playlist", "processed_at"]


def load_processed_ids() -> set:
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, newline="", encoding="utf-8") as f:
        return {row["video_id"] for row in csv.DictReader(f)}


def mark_processed(video_id: str, title: str, playlist: str) -> None:
    file_exists = os.path.exists(STATE_FILE)
    with open(STATE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "video_id": video_id,
            "title": title,
            "playlist": playlist,
            "processed_at": datetime.utcnow().isoformat(),
        })
