# Task Today

> This file is the project's active memory. Keep it focused on ONE current task only. Overwrite it when the task changes — do not let it accumulate history (history belongs in `audit.md`).

---

## Current Task
Create Supabase Storage bucket `videos` with RLS, and create `reports` table with RLS policies

## Why This Task
Phase 2 (Supabase Setup) requires Storage bucket for video uploads and `reports` table for storing analysis results — both with Row Level Security so users only access their own data.

## Related Requirements
- Phase reference: Phase 2 — Supabase Setup
- Relevant PRD sections: Core Features — "Basic auth via Supabase", "Report history list"
- Implementation plan: Phase 2, bullets 22-26 (DB schema, RLS, Storage bucket)

## Reference Files
- `implementation_plan.md` — Phase 2 section
- `prd.md` — Core Features
- Code files: (Supabase dashboard SQL editor)

## Acceptance Criteria
- [ ] Storage bucket `videos` created with 50MB limit
- [ ] RLS policies on `videos`: INSERT/SELECT/DELETE where `auth.uid() = owner`
- [ ] `reports` table created with columns: id (uuid, pk), user_id (uuid, fk to auth.users), video_url (text), voice_score (int), body_score (int), confidence_score (int), report_json (jsonb), created_at (timestamptz), status (text: pending/processing/complete/failed)
- [ ] RLS policies on `reports`: SELECT/INSERT/UPDATE where `auth.uid() = user_id`
- [ ] No DELETE policy on `reports` (history retained)

## Notes / Blockers
- Must run SQL in Supabase Dashboard → SQL Editor
- Bucket name must match Flutter upload code (`videos`)
- `report_json` uses `jsonb` for efficient querying
- `status` defaults to `'pending'`