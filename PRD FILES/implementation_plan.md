# Implementation Plan — Body Language and Voice Analyzer

Stack: Flutter/Dart (frontend), Python (backend processing), Supabase (auth + storage + DB).

---

## Phase 1: Project Initialization
**Goal:** Get a runnable skeleton for both frontend and backend.

- Initialize Flutter project (`flutter create`), set up folder structure (`lib/screens`, `lib/services`, `lib/models`, `lib/widgets`)
- Add core Dart dependencies: `supabase_flutter`, `file_picker` or `image_picker` (video upload), `http`/`dio`, state management package (e.g. `provider` or `riverpod`)
- Initialize Python backend (FastAPI recommended) with a clean project structure (`app/routes`, `app/services`, `app/models`)
- Add core Python dependencies: `fastapi`, `uvicorn`, `supabase-py`, audio/video processing libs (`opencv-python`, `librosa` or `pydub`, `moviepy`)
- Set up `.env` handling on both ends (Supabase URL/key, backend URL)
- Confirm Flutter app can hit a basic backend `/health` endpoint

## Phase 2: Supabase Setup (Auth + Storage + DB)
**Goal:** Users can sign up, log in, and securely store video uploads and reports.

- Create Supabase project; configure Auth (email/password minimum)
- Build Flutter auth screens: Sign Up, Login, Logout, session persistence
- Create Supabase Storage bucket for video uploads (with row-level security scoped to user ID)
- Design DB schema:
  - `reports` table: id, user_id, video_url, voice_score, body_score, confidence_score, report_json, created_at, status
- Set up Row Level Security (RLS) policies so users only access their own reports
- Wire Flutter upload flow: pick video → upload to Supabase Storage → create `reports` row with status `pending`

## Phase 3: Navigation & Core UI
**Goal:** Clean, professional, glass-style navigation and core screens exist and are wired to real data.

- Build navigation shell (bottom nav or drawer): Home/Upload, History, Report Detail, Profile
- Apply glassmorphism design system: consistent blur/translucency components, spacing, typography scale, color palette
- Build Upload screen: video picker, upload progress, "processing" state
- Build History screen: list of past reports (score badge, date, thumbnail placeholder)
- Build Report Detail screen: score breakdown (Voice / Body / Overall), strengths, weaknesses, tips — reads from `report_json`
- Connect screens to Supabase via a service layer (no logic in widgets)

## Phase 4 (Post-MVP placeholder — not detailed here)
Backend processing pipeline (voice + body analysis), score computation, report generation. Track this phase in `task_today.md` once Phase 3 UI is stable.

---

**Note:** Each phase ends with an entry in `audit.md` before moving to the next phase.
