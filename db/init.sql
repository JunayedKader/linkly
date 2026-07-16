-- init.sql runs automatically on first PostgreSQL container startup.
-- The official postgres image looks for .sql files in
-- /docker-entrypoint-initdb.d/ and executes them in alphabetical order.
-- This only runs when the data directory is empty — i.e. first ever start
-- or after docker compose down -v. It never runs on normal restarts.

-- links table — stores every shortened URL
CREATE TABLE IF NOT EXISTS links (
    -- SERIAL is PostgreSQL's auto-incrementing integer type.
    -- PRIMARY KEY means this column uniquely identifies each row.
    id SERIAL PRIMARY KEY,

    -- short_code — the random string that appears in the short URL.
    -- e.g. "aB3kP" in "localhost/aB3kP"
    -- VARCHAR(10) — maximum 10 characters.
    -- UNIQUE — no two rows can have the same short_code.
    -- NOT NULL — every row must have one.
    short_code VARCHAR(10) UNIQUE NOT NULL,

    -- original_url — the full URL the user wants to shorten.
    -- TEXT — unlimited length, URLs can be very long.
    original_url TEXT NOT NULL,

    -- created_at — when the short URL was created.
    -- TIMESTAMP WITH TIME ZONE — stores timezone-aware timestamps.
    -- DEFAULT NOW() — automatically set to current time on insert,
    -- you never need to pass this value manually.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- click_count — how many times this short URL has been visited.
    -- INTEGER DEFAULT 0 — starts at zero, incremented on each redirect.
    click_count INTEGER DEFAULT 0
);

-- Index on short_code — every redirect lookup searches by short_code.
-- Without an index PostgreSQL scans every row to find a match (slow).
-- With an index it jumps directly to the matching row (fast).
-- The PRIMARY KEY on id already has an index — this adds one for short_code.
CREATE INDEX IF NOT EXISTS idx_links_short_code ON links(short_code);
