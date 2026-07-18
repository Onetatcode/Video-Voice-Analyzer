# App Name
Body Language and Voice Analyzer

# Core Problem
Speakers (public speakers, interview candidates, presenters, students) have no easy way to objectively measure how confident they appear and sound during a talk. Self-review by watching a raw recording is slow, subjective, and rarely highlights specific vocal or physical habits (monotone delivery, fidgeting, poor posture, filler words) that undermine perceived confidence. There is no simple tool that ingests a video and returns an objective, structured confidence report covering both voice and body language.

# Target Audience
- Cybersecurity/CS students and professionals preparing presentations or interviews
- Public speaking learners (Toastmasters-style self-improvement)
- Job seekers rehearsing interview answers on video
- Content creators wanting quick feedback before publishing

# Core Features (MVP Scope Only)
- User uploads a single video file (front-facing, one speaker) via the Flutter app
- Backend extracts audio and processes it for: speech pace, pitch variation, filler word count, pause frequency
- Backend extracts video frames and processes them for: posture stability, eye contact estimate (facing camera %), gesture/movement frequency
- Backend generates a single combined "Confidence Score" (0–100) plus separate Voice Score and Body Language Score
- Backend generates a structured report (JSON + rendered UI) summarizing strengths, weaknesses, and 2-3 actionable tips
- User can view the report in-app after processing completes
- Basic auth (sign up / login) via Supabase so reports are tied to a user account
- Report history list (past uploads with score + date)

# Out of Scope (Do Not Build These)
- Multi-speaker detection/diarization
- Real-time/live analysis during recording
- Video editing or trimming tools
- Social sharing / public report links
- Payment, subscriptions, or usage limits
- Advanced emotion detection (facial expression sentiment)
- Cross-platform desktop app (Flutter mobile/web only)
- Custom ML model training — use existing libraries/APIs only, used sparingly
- Team/organization accounts or multi-user collaboration
