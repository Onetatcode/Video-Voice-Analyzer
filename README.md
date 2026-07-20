# Body Language and Voice Analyzer

A Flutter web app + Python FastAPI backend that analyzes uploaded videos for body language and voice patterns, generating confidence scores and actionable feedback reports.

**Try it**: Upload a front-facing video (max 50MB) → backend extracts audio + frames → analyzes voice pace, pitch, filler words, pauses → analyzes posture, gestures, eye contact → generates Voice Score, Body Score, Confidence Score → structured report with strengths, weaknesses, and tips.

---

## Architecture

```
┌─────────────────────┐     ┌─────────────────────────────────────┐
│   Flutter Web App   │────▶│         Python FastAPI Backend       │
│  (body_language_    │     │  (app/)                             │
│   analyzer/)        │     │                                     │
│                     │     │  POST /api/v1/process               │
│  - Auth (Supabase)  │     │  GET  /api/v1/process/{id}/status    │
│  - Upload Video     │     │  POST /api/v1/process/sync           │
│  - History          │     │  GET  /health                       │
│  - Report Detail    │     │                                     │
│  - Profile          │     │  Pipeline:                          │
│                     │     │  1. Download video from Supabase     │
│                     │     │  2. Extract audio (librosa)         │
│                     │     │  3. Extract frames (OpenCV)         │
│                     │     │  4. Analyze voice features          │
│                     │     │  5. Analyze body language           │
│                     │     │  6. Calculate scores                │
│                     │     │  7. Generate report                 │
│                     │     │  8. Save to Supabase               │
└─────────────────────┘     └─────────────────────────────────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
         ┌──────────▼──────────┐
         │      Supabase       │
         │                     │
         │  - Auth (users)     │
         │  - Storage (videos) │
         │  - Database         │
         │    (reports table)  │
         └─────────────────────┘
```

## Features

### Voice Analysis
- **Speech Pace** — words per minute estimate (target: 110–160 WPM)
- **Pitch Variation** — standard deviation of fundamental frequency
- **Filler Word Count** — heuristic detection of "um", "uh", pauses
- **Pause Analysis** — frequency and duration of pauses
- **Voice Score** (0–100) — computed from clarity, consistency, engagement sub-scores

### Body Language Analysis
- **Posture Stability** — head-shoulder-hip alignment score
- **Eye Contact Ratio** — percentage of time facing the camera
- **Gesture Frequency** — purposeful hand gestures per minute
- **Movement Frequency** — body movements per minute
- **Head Nods** — detected head nod count
- **Shoulder Movement** — shoulder stability score
- **Body Score** (0–100) — computed from posture, stability, expressiveness sub-scores

### Scoring
- **Voice Score** — 55% weight in overall confidence
- **Body Score** — 45% weight in overall confidence
- **Confidence Score** — combined 0–100
- Detailed breakdown with sub-scores

### Report Generation
- Top 3 strengths identified from analysis
- Top 3 areas for improvement
- 3 actionable tips (purposeful gestures, power poses, etc.)

### Flutter Web App
- **Auth** — Sign up, login, session persistence via Supabase
- **Upload** — File picker, upload to Supabase Storage, triggers processing
- **History** — List of past reports with score badges, status, timestamps
- **Report Detail** — Score breakdown, strengths, weaknesses, tips
- **Profile** — User info, stats (total/completed/processing/failed), sign out
- **Glassmorphism UI** — Frosted glass design with light/dark theme
- **Bottom Nav** — Home / History / Profile tabs

## Tech Stack

| Layer          | Technology                                                    |
|----------------|---------------------------------------------------------------|
| Frontend       | Flutter 3.44, Dart, Provider, Supabase Flutter SDK            |
| Backend        | Python 3.14, FastAPI, Uvicorn                                 |
| Voice Analysis | Librosa, NumPy                                                |
| Body Analysis  | OpenCV (DNN fallback — no external model required)            |
| Database       | Supabase (PostgreSQL)                                         |
| Storage        | Supabase Storage                                              |
| Auth           | Supabase Auth (GoTrue)                                        |

## Prerequisites

- Python 3.12+
- Flutter SDK 3.44+
- Chrome (for Flutter web)
- Supabase project (free tier works)

## Setup

### 1. Clone and Install Python Dependencies

```powershell
git clone https://github.com/Onetatcode/Video-Voice-Analyzer.git
cd "Body Language and Voice Analyzer"
pip install -r requirements.txt
```

### 2. Configure Supabase

Create a Supabase project at [supabase.com](https://supabase.com) and set up:

**Database — `reports` table:**

```sql
CREATE TABLE reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  video_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  voice_score INTEGER,
  body_score INTEGER,
  confidence_score INTEGER,
  report_json JSONB,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Allow users to CRUD their own reports
CREATE POLICY "Users can CRUD own reports"
  ON reports FOR ALL
  USING (auth.uid() = user_id);
```

**Storage — `videos` bucket:**

```sql
INSERT INTO storage.buckets (id, name, public) VALUES ('videos', 'videos', false);
```

### 3. Environment Variables

**`app/.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
BACKEND_URL=http://localhost:8000
```

**`body_language_analyzer/.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
BACKEND_URL=http://localhost:8000
```

### 4. Run

**Terminal 1 — Backend:**
```powershell
cd "Body Language and Voice Analyzer"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Flutter Web (dev mode):**
```powershell
cd body_language_analyzer
flutter run -d chrome
```

**Or serve the pre-built app:**
```powershell
cd body_language_analyzer\build\web
python -m http.server 3000
# Open http://localhost:3000
```

## API Endpoints

| Method | Path                                | Description                        |
|--------|-------------------------------------|------------------------------------|
| GET    | `/health`                           | Health check                       |
| POST   | `/api/v1/process`                   | Start async video processing       |
| GET    | `/api/v1/process/{report_id}/status`| Check processing status            |
| POST   | `/api/v1/process/sync`              | Process video synchronously        |

### Process Request

```json
{
  "report_id": "uuid-from-database",
  "video_url": "https://supabase.co/storage/...",
  "user_id": "uuid-of-user"
}
```

### Process Response (Sync)

```json
{
  "report_id": "uuid",
  "status": "complete",
  "voice_features": { "speech_pace": 91.8, "pitch_variation": 32.71, ... },
  "body_features": { "posture_stability": 0.5, "eye_contact_ratio": 0.5, ... },
  "scores": { "confidence_score": 68, "voice_score": 82, "body_score": 50 },
  "analysis_report": {
    "strengths": ["Your speech was clear and well-articulated..."],
    "weaknesses": ["Focus on keeping shoulders back..."],
    "tips": ["Map one purposeful gesture to each of your 3 main points..."]
  }
}
```

## Project Structure

```
├── app/                          # Python FastAPI Backend
│   ├── main.py                   # FastAPI app, CORS, route includes
│   ├── .env                      # Supabase credentials
│   ├── models/
│   │   └── processing.py         # Pydantic models (request/response)
│   ├── routes/
│   │   └── processing.py         # API endpoints + background task
│   └── services/
│       ├── video_processor.py    # Download, frame extraction, audio
│       ├── voice_analyzer.py     # Speech pace, pitch, filler words
│       ├── body_analyzer.py      # Posture, gestures, eye contact
│       ├── score_calculator.py   # Voice/Body/Confidence scores
│       ├── processing_pipeline.py# Orchestrates full pipeline
│       └── report_generator.py   # Strengths, weaknesses, tips
│
├── body_language_analyzer/       # Flutter Web App
│   ├── lib/
│   │   ├── main.dart             # App entry, providers, routes
│   │   ├── models/report.dart    # Report data model
│   │   ├── screens/
│   │   │   ├── auth_gate.dart    # Auth state routing
│   │   │   ├── main_shell.dart   # Bottom nav shell (Home/History/Profile)
│   │   │   ├── home_screen.dart  # Welcome + upload button
│   │   │   ├── upload_screen.dart# File picker + upload
│   │   │   ├── history_screen.dart# Past reports list
│   │   │   ├── report_detail_screen.dart# Score breakdown + tips
│   │   │   ├── profile_screen.dart# User info + stats
│   │   │   └── auth/
│   │   │       ├── login_screen.dart
│   │   │       └── sign_up_screen.dart
│   │   ├── services/
│   │   │   ├── api_service.dart   # Backend API calls
│   │   │   ├── auth_service.dart  # Supabase auth
│   │   │   ├── report_service.dart# Supabase reports CRUD
│   │   │   ├── storage_service.dart# Supabase file upload
│   │   │   └── supabase_service.dart# Supabase init
│   │   ├── theme/app_theme.dart   # Light/dark theme
│   │   └── widgets/glass_widgets.dart# Glassmorphism UI kit
│   └── .env                      # Flutter env vars
│
└── PRD FILES/
    ├── prd.md                    # Product requirements
    ├── implementation_plan.md    # Implementation plan
    └── task_today.md             # Active task tracking
```

## Current Limitations

- **Body analysis uses fallback** — OpenPose model files not included. Analysis returns default values (Body Score: 50). Download the OpenPose model (`pose_iter_440000.caffemodel` + `pose_deploy_linevec.prototxt`) to `app/models/` for real analysis.
- **In-memory job tracking** — `processing_jobs` dict resets on server restart. Replace with Redis or Supabase-based job tracking for production.
- **Single-user testing** — Auth works but no admin panel or multi-tenant isolation beyond Supabase RLS.
- **Web-only** — Flutter app targets web. Mobile builds untested.

## License

MIT
