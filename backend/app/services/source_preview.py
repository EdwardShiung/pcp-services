import re
from urllib.parse import urljoin, urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.models import Platform, SourcePreview


REQUEST_TIMEOUT_SECONDS: float = 15.0

HTTP_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 PersonalContentPortal/1.0"
    )
}


def preview_source(source_url: str) -> SourcePreview:
    normalized_url: str = normalize_url(source_url)
    hostname: str = get_hostname(normalized_url)

    if is_youtube_hostname(hostname):
        return preview_youtube_source(normalized_url)

    if is_bilibili_hostname(hostname):
        raise ValueError(
            "Bilibili source requires an RSSHub feed URL in the current version"
        )

    return preview_blog_or_rss_source(normalized_url)


def normalize_url(source_url: str) -> str:
    normalized_url: str = source_url.strip()

    if normalized_url == "":
        raise ValueError("Source URL cannot be empty")

    if not normalized_url.startswith(("http://", "https://")):
        normalized_url = f"https://{normalized_url}"

    return normalized_url


def get_hostname(source_url: str) -> str:
    parsed_url = urlparse(source_url)
    hostname: str | None = parsed_url.hostname

    if hostname is None:
        raise ValueError("Invalid source URL")

    return hostname.lower()


def is_youtube_hostname(hostname: str) -> bool:
    return hostname in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    }


def is_bilibili_hostname(hostname: str) -> bool:
    return hostname in {
        "bilibili.com",
        "www.bilibili.com",
        "space.bilibili.com",
    }


def preview_youtube_source(source_url: str) -> SourcePreview:
    channel_id: str = extract_youtube_channel_id(source_url)

    feed_url: str = (
        "https://www.youtube.com/feeds/videos.xml"
        f"?channel_id={channel_id}"
    )

    feed = feedparser.parse(feed_url)

    if feed.bozo and len(feed.entries) == 0:
        raise ValueError("Unable to read the YouTube channel RSS feed")

    source_name: str = get_feed_title(feed)

    return {
        "platform": "youtube",
        "source_type": "channel",
        "name": source_name,
        "url": source_url,
        "feed_url": feed_url,
        "external_id": channel_id,
    }


def extract_youtube_channel_id(source_url: str) -> str:
    parsed_url = urlparse(source_url)
    path_parts: list[str] = [
        part
        for part in parsed_url.path.split("/")
        if part != ""
    ]

    if len(path_parts) >= 2 and path_parts[0] == "channel":
        channel_id: str = path_parts[1]

        if channel_id.startswith("UC"):
            return channel_id

    response: httpx.Response = httpx.get(
        source_url,
        headers=HTTP_HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    )

    response.raise_for_status()

    channel_id_patterns: list[str] = [
        r'"channelId":"(UC[^"]+)"',
        r'<meta itemprop="channelId" content="(UC[^"]+)"',
        r'"externalId":"(UC[^"]+)"',
    ]

    for pattern in channel_id_patterns:
        match: re.Match[str] | None = re.search(
            pattern,
            response.text,
        )

        if match is not None:
            return match.group(1)

    raise ValueError(
        "Unable to determine the YouTube channel ID"
    )


def preview_blog_or_rss_source(
    source_url: str,
) -> SourcePreview:
    response: httpx.Response = httpx.get(
        source_url,
        headers=HTTP_HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    )

    response.raise_for_status()

    final_url: str = str(response.url)
    content_type: str = response.headers.get(
        "content-type",
        "",
    ).lower()

    if is_feed_document(response.text, content_type):
        return build_rss_preview(
            source_url=final_url,
            feed_url=final_url,
            platform="custom",
        )

    feed_url: str = discover_feed_url(
        page_url=final_url,
        html=response.text,
    )

    return build_rss_preview(
        source_url=final_url,
        feed_url=feed_url,
        platform="blog",
    )


def is_feed_document(
    body: str,
    content_type: str,
) -> bool:
    beginning: str = body.lstrip()[:200].lower()

    if "application/rss+xml" in content_type:
        return True

    if "application/atom+xml" in content_type:
        return True

    if beginning.startswith("<?xml"):
        return True

    if beginning.startswith("<rss"):
        return True

    if beginning.startswith("<feed"):
        return True

    return False


def discover_feed_url(
    page_url: str,
    html: str,
) -> str:
    soup = BeautifulSoup(html, "html.parser")

    supported_types: set[str] = {
        "application/rss+xml",
        "application/atom+xml",
        "application/feed+json",
    }

    alternate_links = soup.find_all(
        "link",
        rel=lambda value: (
            value is not None
            and "alternate" in value
        ),
    )

    for link in alternate_links:
        link_type = link.get("type")
        href = link.get("href")

        if not isinstance(link_type, str):
            continue

        if not isinstance(href, str):
            continue

        if link_type.lower() not in supported_types:
            continue

        return urljoin(page_url, href)

    raise ValueError(
        "No RSS or Atom feed was found on this website"
    )


def build_rss_preview(
    source_url: str,
    feed_url: str,
    platform: Platform,
) -> SourcePreview:
    feed = feedparser.parse(feed_url)

    if feed.bozo and len(feed.entries) == 0:
        raise ValueError("The discovered RSS feed is invalid")

    source_name: str = get_feed_title(feed)

    external_id: str | None = None
    feed_id = feed.feed.get("id")

    if isinstance(feed_id, str):
        external_id = feed_id

    return {
        "platform": platform,
        "source_type": "rss",
        "name": source_name,
        "url": source_url,
        "feed_url": feed_url,
        "external_id": external_id,
    }


def get_feed_title(feed: object) -> str:
    feed_metadata = getattr(feed, "feed", None)

    if feed_metadata is None:
        return "Unknown Source"

    title = feed_metadata.get("title")

    if isinstance(title, str) and title.strip() != "":
        return title.strip()

    return "Unknown Source"
