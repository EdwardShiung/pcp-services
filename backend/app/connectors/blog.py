from typing import Any
from app.models import FeedItem
import feedparser

def fetch_blog_rss(feed_url: str) -> list[FeedItem]:
    feed: Any = feedparser.parse(feed_url) 
    items: list[FeedItem] = []

    for entry in feed.entries:
        external_id: str | None = entry.get("id")
        title: str = entry.get("title", "")
        url: str = entry.get("link", "")
        creator_name: str | None = entry.get("author")
        description: str | None = get_description(entry) 
        published_at: str | None = get_published_at(entry)
        thumbnail_url: str | None = get_thumbnail_url(entry)

        if title == "" or url == "":
            continue

        item: FeedItem = {

                "external_id":external_id,
                "title": title,
                "url": url,
                "creator_name": creator_name,
                "description": description,
                "published_at": published_at,
                "thumbnail_url": thumbnail_url
        }

        items.append(item)

    return items


def get_description(entry: Any) -> str | None:
    
    summary: str | None = entry.get("summary")

    if summary is not None:
        return summary

    content: list[dict[str, Any]] | None = entry.get("content")

    if content is not None and len(content) > 0:
        value: Any = content[0].get("value")

        if isinstance(value, str):
            return value

    return None

def get_published_at(entry: Any) -> str | None:
    
    published: str | None = entry.get("published")

    if published is not None:
        return published

    updated: str | None = entry.get("updated")

    return updated


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
            url = content.get("url")

            if isinstance(url, str):
                return url

    return None
