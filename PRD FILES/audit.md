# Project Audit Framework

Run this audit after completing each phase in `implementation_plan.md`, before starting the next phase. Log the date and phase number at the top of each audit entry.

---

## Audit Template

### Audit: Phase [N] — [Phase Name]
**Date:**
**Auditor:**

#### 1. Codebase Analysis
- List all files/modules touched or created during this phase
- Note any TODOs, hardcoded values, or placeholder logic left in code
- Check that naming conventions and folder structure match the established pattern (`lib/`, `app/`)

#### 2. Plan Comparison
- Go through each bullet point for this phase in `implementation_plan.md`
- Mark each as: ✅ Done / ⚠️ Partial / ❌ Not Done
- For ⚠️ or ❌ items, note what's missing and why

#### 3. Missing Elements / Errors / Incorrect Implementations
- List any features that were implemented differently than planned (and whether that's acceptable)
- List any known bugs (cross-reference `error_bug.md` entries)
- List any security gaps (e.g., missing RLS policy, missing input validation, exposed keys)

#### 4. Orphaned / Unused Files
- Run a search for files not imported/referenced anywhere (dead widgets, unused Python modules, leftover test/demo files)
- Confirm no unused dependencies remain in `pubspec.yaml` / `requirements.txt`
- Flag any duplicate logic that should be consolidated

#### 5. Verdict
- Overall status: **Ready to proceed** / **Needs fixes before proceeding**
- List blocking items (if any) that must be resolved before starting the next phase
- Update `task_today.md` with the next task based on this audit's findings

---

## Audit Log
(Append one filled-out template entry per phase below this line.)
