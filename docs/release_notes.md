# Release notes and regression results

## v2.0: stable release
Login, add tasks (title, priority, due date), complete/reopen, delete with confirmation,
All/Open/Done filters, live search, per-user task lists.

**Result:** 31 passed, 2 skipped (sort feature not built yet). ✅ Released.

## v2.1: release candidate
**New:** "Sort by priority" link (high, then medium, then low).

**Result:** 24 passed, **9 failed**. ❌ **Release blocked.**

| Regression | What broke in the UI | Caught by |
|---|---|---|
| U1 | Search became case-sensitive ("REPORT" no longer finds "Write FYP report") | TC_SRC_01, TC_SRC_02 |
| U2 | The summary counts every task as open ("5 open · 3 done" for 5 tasks) | TC_ACT_01, TC_SUM_01 |
| U3 | Empty or spaces-only titles are saved as blank tasks | TC_CRT_02a, TC_CRT_02b |
| U4 | Due dates in the past are accepted | TC_CRT_02d |
| U5 | Clicking **Cancel** on "Delete this task?" still deletes the task | TC_ACT_04 |
| U6 | The Done tab shows open tasks too | TC_FLT_02 |

Both new-feature tests (TC_SORT_01, 02) **passed** on v2.1. The new feature worked; the change broke six
other things, and only the regression suite noticed.

## v2.2: fix release (latest)
Sort feature kept, U1 to U6 fixed.

**Result:** 33 passed. ✅ Released.
