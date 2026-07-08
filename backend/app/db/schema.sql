CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  platform TEXT NOT NULL,
  source_type TEXT NOT NULL,
  name TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  feed_url TEXT,
  external_id TEXT,
  avatar_url TEXT,
  description TEXT,
  category TEXT,
  enabled BOOLEAN DEFAULT TRUE,
  show_on_home BOOLEAN DEFAULT TRUE,
  sync_interval_minutes INT DEFAULT 60,
  last_synced_at TIMESTAMPTZ,
  sync_status TEXT DEFAULT 'pending',
  email_notify_mode TEXT DEFAULT 'never',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  content_type TEXT NOT NULL,
  external_id TEXT,
  title TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  thumbnail_url TEXT,
  creator_name TEXT,
  description TEXT,
  published_at TIMESTAMPTZ,
  fetched_at TIMESTAMPTZ DEFAULT now(),
  status TEXT DEFAULT FALSE,
  saved BOOLEAN DEFAULT FALSE,
  watch_later BOOLEAN DEFAULT FALSE,
  raw_metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
