CREATE TABLE IF NOT EXISTS unique_visitors (visitor_hash TEXT PRIMARY KEY, first_seen INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS article_likes (article_id TEXT NOT NULL, visitor_hash TEXT NOT NULL, created_at INTEGER NOT NULL, PRIMARY KEY(article_id, visitor_hash));
CREATE INDEX IF NOT EXISTS idx_article_likes_article ON article_likes(article_id);
CREATE TABLE IF NOT EXISTS site_likes (visitor_hash TEXT PRIMARY KEY, created_at INTEGER NOT NULL);
