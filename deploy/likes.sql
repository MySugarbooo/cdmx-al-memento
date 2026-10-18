-- Execute once in the D1 database connected as LIKES_DB.
CREATE TABLE IF NOT EXISTS site_likes (
  visitor_hash TEXT PRIMARY KEY NOT NULL,
  created_at INTEGER NOT NULL
);
