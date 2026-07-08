from fastapi import FastAPI
from pydantic import BaseModel
from app.db import get_conn

app = FastAPI(title="Personal Content Portal API")

class SourceCreate(BaseModel):
    platform: str
    source_type: str
    name: str 
    url: str
    feed_url: str | None = None
    category: str | None = None
    email_notify_mode: str = "never"

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

@app.post("/api/sources")
def create_source(source: SourceCreate):
    with get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO sources
            (platform, source_type, name, url, feed_url, category, email_notify_mode)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
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
    return row

@app.get("/api/content-items")
def list_content_items():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ci.*, s.name AS source_name
            FROM content_items ci
            JOIN source s ON ci.source_id = s.id
            ORDER BY ci.published_at DESC NULLS LAST, ci.created_at DESC
            """
        ).fetchall()

    return {"items": rows}


