CREATE TABLE IF NOT EXISTS match_editorial_revisions (
  id TEXT PRIMARY KEY,
  match_id TEXT NOT NULL,
  content TEXT NOT NULL,
  author TEXT NOT NULL,
  reviewer TEXT,
  decision_note TEXT,
  state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','published','rejected','superseded')),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  reviewed_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS editorial_one_published
  ON match_editorial_revisions(match_id) WHERE state = 'published';
CREATE INDEX IF NOT EXISTS editorial_queue ON match_editorial_revisions(state, created_at);
