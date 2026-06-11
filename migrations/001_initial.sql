CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('article', 'paper', 'repo_release')),
  published_at TEXT,
  discovered_at TEXT NOT NULL,
  hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'queued', 'deep_done', 'skimmed', 'skipped')),
  score REAL,
  score_reasons TEXT,
  UNIQUE(source_id, url),
  UNIQUE(hash)
);

CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL UNIQUE,
  deep_item_id TEXT,
  spend_usd REAL NOT NULL DEFAULT 0,
  duration_s REAL NOT NULL DEFAULT 0,
  pdf_path TEXT,
  errata TEXT,
  FOREIGN KEY(deep_item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS ratings (
  item_id TEXT NOT NULL,
  value TEXT NOT NULL CHECK (value IN ('up', 'down')),
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,
  raw_text TEXT NOT NULL,
  signals_json TEXT NOT NULL,
  processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concepts (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  summary TEXT NOT NULL,
  created_run_id INTEGER NOT NULL,
  FOREIGN KEY(created_run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS concept_edges (
  a INTEGER NOT NULL,
  b INTEGER NOT NULL,
  relation TEXT NOT NULL CHECK (relation IN ('builds_on', 'related', 'prereq')),
  PRIMARY KEY(a, b, relation),
  FOREIGN KEY(a) REFERENCES concepts(id),
  FOREIGN KEY(b) REFERENCES concepts(id)
);

CREATE TABLE IF NOT EXISTS item_concepts (
  item_id TEXT NOT NULL,
  concept_id INTEGER NOT NULL,
  PRIMARY KEY(item_id, concept_id),
  FOREIGN KEY(item_id) REFERENCES items(id),
  FOREIGN KEY(concept_id) REFERENCES concepts(id)
);

CREATE TABLE IF NOT EXISTS prompt_versions (
  id INTEGER PRIMARY KEY,
  stage TEXT NOT NULL,
  version INTEGER NOT NULL,
  parent_version INTEGER,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'candidate', 'retired')),
  rationale TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(stage, version)
);

CREATE TABLE IF NOT EXISTS experiments (
  id INTEGER PRIMARY KEY,
  stage TEXT NOT NULL,
  version_a INTEGER NOT NULL,
  version_b INTEGER NOT NULL,
  fixtures_json TEXT NOT NULL,
  judge_scores_json TEXT,
  user_verdict TEXT,
  status TEXT NOT NULL CHECK (status IN ('proposed', 'replayed', 'reported', 'verdict', 'promoted', 'rejected')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS preference_revisions (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,
  content TEXT NOT NULL,
  diff_summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS spend_log (
  run_id INTEGER NOT NULL,
  stage TEXT NOT NULL,
  model TEXT NOT NULL,
  cost_usd REAL NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(run_id) REFERENCES runs(id)
);
