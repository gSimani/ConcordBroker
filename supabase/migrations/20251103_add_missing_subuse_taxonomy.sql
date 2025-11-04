-- Migration: Add Missing SUBUSE Taxonomy Entries
-- Date: 2025-11-03
-- Purpose: Add CONDOMINIUM subuse category referenced in standardization migration
-- Impact: Enables proper subuse classification for condominiums
-- PDR Reference: FL-USETAX-PDR-001 v1.0.0

-- Safety: Run in transaction
begin;

-- Add CONDOMINIUM as a RESIDENTIAL subuse
-- This is referenced in the standardization migration for DOR code 04
insert into public.use_taxonomy (code, name, level, parent_code)
values ('CONDOMINIUM', 'Condominium', 2, 'RESIDENTIAL')
on conflict (code) do nothing;

-- Verify the insert
select
  'SUBUSE TAXONOMY VERIFICATION' as checkpoint,
  code,
  name,
  level,
  parent_code
from public.use_taxonomy
where code = 'CONDOMINIUM';

commit;

-- === EXPECTED RESULTS ===
/*
New SUBUSE added:
- Code: CONDOMINIUM
- Name: Condominium
- Level: 2 (SUBUSE)
- Parent: RESIDENTIAL

This enables properties with DOR code 04 to be assigned:
- Main Code: RESIDENTIAL
- Subuse Code: CONDOMINIUM
- Confidence: 0.95
*/

-- === POST-MIGRATION NOTES ===
/*
This migration should be run BEFORE 20251103_standardize_null_property_use.sql
to ensure the CONDOMINIUM subuse category exists when assignments are created.

If you've already run the standardization migration, this migration can be run
after, and the CONDOMINIUM subuse will be available for future assignments.
Existing assignments with subuse_code = 'CONDOMINIUM' will automatically
reference this taxonomy entry via foreign key.
*/
