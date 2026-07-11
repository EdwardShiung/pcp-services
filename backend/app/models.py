from typing import Literal, TypedDict


# Data Sources
Platform = Literal["youtube", "blog", "custom", "bilibili"]
# Categories
ContentType = Literal["video", "article"]

# (Database Record) Represents a content source record stored in the database 
class SourceRow(TypedDict):
    id: str
    platform: str
    feed_url: str | None

# (Normalized Content Model) Represents a normalized content item from different platforms 
class FeedItem(TypedDict):
    external_id: str | None
    title: str
    url: str
    thumbnail_url: str | None
    creator_name: str | None
    description: str | None
    published_at: str | None
