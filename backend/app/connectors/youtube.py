from typing import Any
from app.models import FeedItem
import feedparser

def get_youtube_feed_url(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def fetch_youtube_rss(feed_url: str) -> list[FeedItem]:
    feed: Any = feedparser.parse(feed_url)

    items: list[FeedItem] = []

    for entry in feed.entries:
        
        thumbnail_url: str | None = None

        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                   thumbnail_url = entry.media_thumbnail[0]["url"]

        
        item: FeedItem = {
            "external_id": entry.get("yt_videoid") or entry.get("id"),
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "thumbnail_url": thumbnail_url,
            "creator_name": entry.get("author"),
            "published_at": entry.get("published"),
            "description": entry.get("summary", ""),
        }

        items.append(item)

    return items

