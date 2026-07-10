from typing import Any, TypedDict, Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.db import get_conn
from app.connectors.youtube import fetch_youtube_rss

# Data Sources
Platform = Literal["youtube", "blog", "custom"]
# Categories
ContentType = Literal["video", "article"]

# (Request Model) Request model for creating a new content source 
class SourceCreate(BaseModel):
    platform: str
    source_type: str
    name: str 
    url: str
    feed_url: str | None = None
    category: str | None = None
    email_notify_mode: str = "never"

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

app = FastAPI(title="Personal Content Portal API")

# API Testing
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/sources")
def list_sources():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sources ORDER BY created_at DESC"
        ).fetchall()
    return {"items": rows}


# API Layer
'''
- Create a new content source in the database
'''
@app.post("/api/sources")
def create_source(source: SourceCreate) -> dict[str, Any]:

    row: dict[str, Any] | None = None

    with get_conn() as conn:
        row = conn.execute(
            """
             INSERT INTO sources
            (platform, source_type, name, url, feed_url, category, email_notify_mode)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                source.platform,
                source.source_type,
                source.name,
                source.url,
                source.feed_url,
                source.category,
                source.email_notify_mode,
            ),
        ).fetchone()
        
        conn.commit()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create source")

    return row

"""
- Sync the latest content from a specificed source and save it to the database
"""
@app.post("/api/sources/{source_id}/sync")
def sync_source(source_id: str) -> dict[str, int | str]:

    source: SourceRow = load_source_or_raise(source_id)
    feed_url: str = get_feed_url_or_raise(source)
    content_type: ContentType = get_content_type(source["platform"]) 

    items: list[FeedItem] = fetch_youtube_rss(feed_url)

    inserted_count: int = insert_content_items(
            source_id = source_id,
            platform = source["platform"],
            content_type = content_type,
            items = items
    )
    print(inserted_count)
    print(type(inserted_count))

    mark_source_synced(source_id)

    return {
        "source_id": source_id,
        "fetched": len(items),
        "inserted": inserted_count,
    } 

"""
- Retrieve all the content items from the database
"""
@app.get("/api/content-items")
def list_content_items():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ci.*, s.name AS source_name
            FROM content_items ci
            JOIN sources s ON ci.source_id = s.id
            ORDER BY ci.published_at DESC NULLS LAST, ci.created_at DESC
            """
        ).fetchall()
    return {"items": rows}

"""
- Load a source by its ID and raise an error if it is not found
"""
def load_source_or_raise(source_id: str) -> SourceRow:
    
    source: dict[str, Any] | None = None

    with get_conn() as conn:
        source = conn.execute(
            """
            SELECT id, platform, feed_url
            FROM sources
            WHERE id = %s
            """,
            (source_id,),
        ).fetchone()

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    return SourceRow(
            id = str(source["id"]),
            platform = source["platform"],
            feed_url = source["feed_url"],
                
    )    

                        
"""
- Get the source's feed URL and raise an error if it is not available
"""
def get_feed_url_or_raise(source: SourceRow) -> str:
    
    feed_url: str | None = source["feed_url"]

    if feed_url is None or feed_url == "":
        raise HTTPException(status_code=400, detail="Source has no feed_url")
    
    return feed_url

"""
- Determine the content type based on the platform
"""
def get_content_type(platform: str) -> ContentType:

    if platform == "youtube":
        return "video"

    if platform == "blog":
        return "article"

    if platform == "custom":
        return "article"

    raise HTTPException(status_code=400, detail="Unsupported platform for sync")

"""
- Insert parsed content items into the database and return the number inserted
"""
def insert_content_items(source_id: str, platform: str, content_type: ContentType, items: list[FeedItem]) -> int:


    inserted_count: int = 0
    
    inserted_row: dict[str, Any] | None = None

    with get_conn() as conn:
        
        for item in items:
            print(item)
            print(type(item))
            inserted_row = conn.execute(
            
                    """
                    INSERT INTO content_items
                    (source_id, platform, content_type, external_id, title, url, thumbnail_url, creator_name, description, published_at)
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    RETURNING id
                    """,
                    (
                        source_id,
                        platform,
                        content_type,
                        item["external_id"],
                        item["title"],
                        item["url"],
                        item["thumbnail_url"],
                        item["creator_name"],
                        item["description"],
                        item["published_at"],
                    ),
            
            ).fetchone()

            if inserted_row is not None:
                inserted_count += 1

        conn.commit()

    return inserted_count

"""
- Update the source's last synchronization time
"""
def mark_source_synced(source_id: str) -> None:

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE sources
            SET last_synced_at = now(),
                sync_status = 'synced',
                updated_at = now()
            WHERE id = %s
            """,
            (source_id,),
        )

        conn.commit()
    














