from app.models import FeedItem
from typing import Any
import feedparser


def fetch_bilibili_rss(feed_url: str) -> list[FeedItem]:
    feed: Any = feedparser.parse(feed_url)
    items: list[FeedItem] = []

    for entry in feed.entries:
        external_id: str | None = entry.get("id")
        title: str = entry.get("title", "")
        url: str = entry.get("link", "")
        creator_name: str | None = entry.get("author")
        description: str | None = entry.get("summary")
        published_at: str | None = get_published_at(entry)
        thumbnail_url: str | None = get_thumbnail_url(entry)

        if title == "" or url == "":
            continue

        item: FeedItem = {
            "external_id": external_id,
            "title": title,
            "url": url,
            "thumbnail_url": thumbnail_url,
            "creator_name": creator_name,
            "description": description,
            "published_at": published_at,
        }

        items.append(item)

    return items


def get_published_at(entry: Any) -> str | None:
    published: Any = entry.get("published")

    if isinstance(published, str):
        return published

    updated: Any = entry.get("updated")

    if isinstance(updated, str):
        return updated

    return None


def get_thumbnail_url(entry: Any) -> str | None:
    media_thumbnail: Any = entry.get("media_thumbnail")

    if isinstance(media_thumbnail, list) and len(media_thumbnail) > 0:
        thumbnail: Any = media_thumbnail[0]

        if isinstance(thumbnail, dict):
            url: Any = thumbnail.get("url")

            if isinstance(url, str):
                return url

    media_content: Any = entry.get("media_content")

    if isinstance(media_content, list) and len(media_content) > 0:
        content: Any = media_content[0]

        if isinstance(content, dict):
            url: Any = content.get("url")

            if isinstance(url, str):
                return url

    return None

