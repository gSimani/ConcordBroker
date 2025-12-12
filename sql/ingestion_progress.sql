-- Ingestion telemetry table + helper views
-- Run in Supabase SQL editor (or psql) once.

BEGIN;

CREATE TABLE IF NOT EXISTS public.ingestion_progress (
  id          BIGSERIAL PRIMARY KEY,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  run_id      TEXT,         -- optional logical run identifier
  phase_index INTEGER,
  phase_total INTEGER,
  county      TEXT,
  years       JSONB,        -- e.g. {"start":2023, "end":2023}
  done        INTEGER,      -- files completed in this run scope
  total       INTEGER,      -- files considered in this run scope
  percent     INTEGER,      -- derived percent (0..100)
  current     TEXT          -- e.g. start:NAL 2023, ingested:<filename>
);

-- Helpful indexes for quick lookups
CREATE INDEX IF NOT EXISTS idx_ing_progress_time
  ON public.ingestion_progress(created_at DESC);

-- Add run_id column if table pre-existed without it
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='ingestion_progress' AND column_name='run_id'
  ) THEN
    ALTER TABLE public.ingestion_progress ADD COLUMN run_id TEXT;
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_ing_progress_run_id
  ON public.ingestion_progress(run_id);

-- Year expression index
CREATE INDEX IF NOT EXISTS idx_ing_progress_year
  ON public.ingestion_progress(((years->>'start')));

-- County filter
CREATE INDEX IF NOT EXISTS idx_ing_progress_county
  ON public.ingestion_progress(county);

-- Dataset extractor (start:DS YYY or prefix before colon)
-- Create a view that normalizes dataset + year for latest snapshot queries
CREATE OR REPLACE VIEW public.ingestion_progress_latest AS
WITH norm AS (
  SELECT
    id,
    created_at,
    run_id,
    county,
    (years->>'start')::INT AS year,
    CASE
      WHEN current LIKE 'start:%' THEN split_part(split_part(current, ' ', 1), ':', 2)
      ELSE split_part(current, ':', 1)
    END AS dataset,
    done,
    total,
    percent,
    current
  FROM public.ingestion_progress
)
SELECT DISTINCT ON (dataset, year, run_id)
  dataset,
  year,
  run_id,
  created_at,
  done,
  total,
  percent,
  current
FROM norm
ORDER BY dataset, year, run_id, created_at DESC;

-- Latest per dataset/year/county
CREATE OR REPLACE VIEW public.ingestion_progress_latest_by_county AS
WITH norm AS (
  SELECT
    id,
    created_at,
    run_id,
    county,
    (years->>'start')::INT AS year,
    CASE
      WHEN current LIKE 'start:%' THEN split_part(split_part(current, ' ', 1), ':', 2)
      ELSE split_part(current, ':', 1)
    END AS dataset,
    done,
    total,
    percent,
    current
  FROM public.ingestion_progress
)
SELECT DISTINCT ON (dataset, year, county, run_id)
  dataset,
  year,
  county,
  run_id,
  created_at,
  done,
  total,
  percent,
  current
FROM norm
ORDER BY dataset, year, county, run_id, created_at DESC;

COMMIT;
