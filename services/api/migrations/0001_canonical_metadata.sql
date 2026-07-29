BEGIN;

CREATE TABLE paper (
    id BIGSERIAL PRIMARY KEY,
    arxiv_id TEXT NOT NULL UNIQUE,
    canonical_title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    primary_category TEXT NOT NULL,
    doi TEXT UNIQUE,
    journal_reference TEXT,
    citation_count INTEGER NOT NULL DEFAULT 0 CHECK (citation_count >= 0),
    first_published_at TIMESTAMPTZ NOT NULL,
    latest_updated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX paper_category_published_idx
    ON paper (primary_category, first_published_at DESC);
CREATE INDEX paper_normalized_title_idx ON paper (normalized_title);

CREATE TABLE paper_version (
    paper_id BIGINT NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    version INTEGER NOT NULL CHECK (version >= 1),
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    source_url TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    source_payload_sha256 TEXT NOT NULL,
    PRIMARY KEY (paper_id, version)
);

CREATE TABLE author (
    id BIGSERIAL PRIMARY KEY,
    display_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    orcid TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX author_normalized_name_idx ON author (normalized_name);

CREATE TABLE paper_author (
    paper_id BIGINT NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES author(id) ON DELETE RESTRICT,
    author_position INTEGER NOT NULL CHECK (author_position >= 1),
    PRIMARY KEY (paper_id, author_position),
    UNIQUE (paper_id, author_id)
);

CREATE TABLE paper_category (
    paper_id BIGINT NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (paper_id, category)
);

CREATE INDEX paper_category_lookup_idx ON paper_category (category, paper_id);

CREATE TABLE citation_edge (
    citing_paper_id BIGINT NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    cited_paper_id BIGINT NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (citing_paper_id, cited_paper_id, source),
    CHECK (citing_paper_id <> cited_paper_id)
);

CREATE INDEX citation_edge_cited_idx ON citation_edge (cited_paper_id);

CREATE TABLE ingestion_cursor (
    source TEXT PRIMARY KEY,
    cursor TEXT,
    last_success_at TIMESTAMPTZ,
    last_attempt_at TIMESTAMPTZ,
    consecutive_failures INTEGER NOT NULL DEFAULT 0 CHECK (consecutive_failures >= 0),
    state JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE data_manifest (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL,
    source_window_start TIMESTAMPTZ,
    source_window_end TIMESTAMPTZ,
    record_count BIGINT NOT NULL CHECK (record_count >= 0),
    rejected_count BIGINT NOT NULL DEFAULT 0 CHECK (rejected_count >= 0),
    payload_sha256 TEXT NOT NULL,
    code_revision TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX data_manifest_source_created_idx
    ON data_manifest (source, created_at DESC);

CREATE TABLE dedup_candidate (
    left_paper_id BIGINT NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    right_paper_id BIGINT NOT NULL REFERENCES paper(id) ON DELETE CASCADE,
    detector_version TEXT NOT NULL,
    reason TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    title_similarity DOUBLE PRECISION NOT NULL CHECK (title_similarity BETWEEN 0 AND 1),
    author_overlap DOUBLE PRECISION NOT NULL CHECK (author_overlap BETWEEN 0 AND 1),
    decision TEXT NOT NULL CHECK (decision IN ('pending', 'duplicate', 'distinct')),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (left_paper_id, right_paper_id, detector_version),
    CHECK (left_paper_id < right_paper_id)
);

COMMIT;
