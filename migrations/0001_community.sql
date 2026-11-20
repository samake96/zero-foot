CREATE TABLE IF NOT EXISTS community_posts (
 id TEXT PRIMARY KEY,
 match_id TEXT NOT NULL,
 user_id TEXT NOT NULL,
 display_name TEXT NOT NULL,
 parent_id TEXT,
 body TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'visible' CHECK(status IN ('visible','hidden','deleted')),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(parent_id) REFERENCES community_posts(id)
);
CREATE INDEX IF NOT EXISTS idx_community_match_time ON community_posts(match_id,created_at DESC);
CREATE TABLE IF NOT EXISTS community_reports (
 id TEXT PRIMARY KEY,
 post_id TEXT NOT NULL,
 reporter_id TEXT NOT NULL,
 reason TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 UNIQUE(post_id,reporter_id)
);
CREATE TABLE IF NOT EXISTS community_votes (
 match_id TEXT NOT NULL,
 user_id TEXT NOT NULL,
 choice TEXT NOT NULL CHECK(choice IN ('home','draw','away')),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 PRIMARY KEY(match_id,user_id)
);
