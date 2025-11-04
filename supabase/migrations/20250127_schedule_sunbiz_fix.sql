-- Schedule automated Sunbiz batch processing with self-terminating wrapper

-- Create wrapper function that auto-stops when complete
CREATE OR REPLACE FUNCTION public.run_fix_sunbiz_and_maybe_stop(
  jobname text DEFAULT 'fix-sunbiz-batches',
  batch_size int DEFAULT 2000
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  updated int := 0;
BEGIN
  -- Run one batch
  SELECT public.fix_sunbiz_entity_batches(batch_size) INTO updated;

  -- Log progress to server logs
  RAISE LOG 'fix_sunbiz batch_size=% rows_updated=%', batch_size, updated;

  -- If nothing left to fix, unschedule the job
  IF updated = 0 THEN
    PERFORM cron.unschedule(jobname);
    RAISE LOG 'fix_sunbiz complete; cron job "%" unscheduled', jobname;
  END IF;
END;
$$;

-- Schedule the wrapper to run every minute
SELECT cron.schedule(
  'fix-sunbiz-batches',
  '* * * * *',
  $$SELECT public.run_fix_sunbiz_and_maybe_stop('fix-sunbiz-batches', 2000);$$
);
