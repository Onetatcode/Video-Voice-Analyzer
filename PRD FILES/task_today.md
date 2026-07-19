# Task Today

> This file is the project's active memory. Keep it focused on ONE current task only. Overwrite it when the task changes — do not let it accumulate history (history belongs in `audit.md`).

---

## Current Task
Build Flutter video upload screen with Supabase Storage integration

## Why This Task
Phase 2 (Supabase Setup) requires wiring the upload flow: pick video → upload to Supabase Storage → create `reports` row with status `pending`. This is the final piece of Phase 2 before moving to Phase 3 UI.

## Related Requirements
- Phase reference: Phase 2 — Supabase Setup
- Relevant PRD sections: Core Features — "User uploads a single video file", "Report history list"
- Implementation plan: Phase 2, bullet 26 ("Wire Flutter upload flow: pick video → upload to Supabase Storage → create `reports` row with status `pending`")

## Reference Files
- `implementation_plan.md` — Phase 2 section
- `prd.md` — Core Features
- Code files: `lib/services/storage_service.dart` (new), `lib/screens/upload_screen.dart` (new), `lib/models/report.dart` (new), `lib/main.dart` (add route)

## Acceptance Criteria
- [ ] `StorageService` class with `uploadVideo(File)` returning video URL
- [ ] `Report` model with fromJson/toJson
- [ ] `UploadScreen` with video picker, upload progress, success/error states
- [ ] On success: create `reports` row with `status: 'pending'`, `video_url`, `user_id`
- [ ] Navigate from HomeScreen "Upload Video" button to UploadScreen
- [ ] Upload button in HomeScreen wired to navigation

## Notes / Blockers
- Supabase Storage bucket `videos` and `reports` table with RLS already created (manual step)
- Uses `file_picker` for video selection
- Glassmorphism styling deferred to Phase 3 — basic Material 3 for now