# Manual Testing Guide — Body Language and Voice Analyzer

Follow these steps in order after any build to confirm core functionality works end-to-end. Each test lists Preconditions, Steps, and Expected Result. Mark Pass/Fail and log failures in `error_bug.md`.

---

## 1. Authentication

### 1.1 Sign Up
- **Preconditions:** App installed, not logged in, valid Supabase connection
- **Steps:**
  1. Open app → tap "Sign Up"
  2. Enter a new email and password (8+ chars)
  3. Submit
- **Expected Result:** Account created, user redirected to Home/Upload screen, session persists on app restart

### 1.2 Login
- **Steps:**
  1. Log out if logged in
  2. Enter valid credentials on Login screen
  3. Submit
- **Expected Result:** User lands on Home/Upload screen with their existing report history visible

### 1.3 Invalid Login
- **Steps:** Enter incorrect password
- **Expected Result:** Clear error message shown, no crash, no navigation

### 1.4 Logout
- **Steps:** Tap Logout from Profile/Nav
- **Expected Result:** Session cleared, user returned to Login screen, protected screens no longer accessible

---

## 2. Video Upload

### 2.1 Upload Valid Video
- **Preconditions:** Logged in, have a short (10–30s) front-facing test video
- **Steps:**
  1. Tap Upload
  2. Select the test video
  3. Confirm upload
- **Expected Result:** Upload progress shown, video appears in Supabase Storage bucket, new row created in `reports` table with status `pending`

### 2.2 Upload Invalid File Type
- **Steps:** Attempt to select a non-video file (if file picker allows it)
- **Expected Result:** App rejects file with clear error, no crash, no partial upload

### 2.3 Upload Oversized File
- **Steps:** Attempt to upload a video exceeding the defined size limit
- **Expected Result:** App blocks upload before sending, shows size-limit error message

### 2.4 Cancel Upload Mid-Progress
- **Steps:** Start upload, cancel before completion
- **Expected Result:** Upload stops cleanly, no orphaned partial file in storage, no orphaned DB row left in `pending` indefinitely

---

## 3. Backend Processing

### 3.1 Successful Processing
- **Preconditions:** A video has completed upload (status `pending`)
- **Steps:**
  1. Trigger/await backend processing (manual trigger or automatic, per current implementation)
  2. Poll or refresh report status in app
- **Expected Result:** Status transitions `pending` → `processing` → `complete`; `report_json`, `voice_score`, `body_score`, `confidence_score` populated in DB

### 3.2 Processing Failure Handling
- **Steps:** Submit a video expected to fail processing (e.g., no audio track, corrupted file)
- **Expected Result:** Status transitions to `failed` with a stored error reason; app shows a user-friendly failure message, not a raw stack trace

---

## 4. Report Viewing

### 4.1 View Completed Report
- **Steps:**
  1. From History, tap a report with status `complete`
- **Expected Result:** Report Detail screen shows Overall Confidence Score, Voice Score, Body Language Score, strengths, weaknesses, and tips — all rendered from `report_json`, no placeholder/lorem ipsum text

### 4.2 View Report Still Processing
- **Steps:** Tap a report with status `processing` or `pending`
- **Expected Result:** Screen shows a clear "still processing" state, not an empty/broken report screen

### 4.3 History List Accuracy
- **Steps:** Compare History list against actual rows in `reports` table for the logged-in user
- **Expected Result:** List shows only the current user's reports (RLS working), correct scores and dates, most recent first

---

## 5. UI / Design QA

### 5.1 Glass UI Consistency
- **Steps:** Navigate through every screen
- **Expected Result:** Glassmorphism styling (blur, translucency, spacing, typography) is consistent across Upload, History, Report Detail, and Auth screens — no mismatched components

### 5.2 Responsive Layout
- **Steps:** Test on at least one small phone screen and one tablet/larger screen size
- **Expected Result:** No overflow, clipped text, or broken layouts

### 5.3 Navigation Integrity
- **Steps:** Tap through every nav item; use back button/gesture repeatedly
- **Expected Result:** No dead-end screens, no crashes, correct screen always loads

---

## 6. Regression Pass (Run Before Each Release)
- [ ] Sign up
- [ ] Login / Logout
- [ ] Upload valid video
- [ ] Processing completes and report is viewable
- [ ] History list correct and scoped to user
- [ ] No console errors during full flow above
