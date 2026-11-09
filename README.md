# Automated Regression Testing Framework

A reusable UI regression framework built with **Playwright + pytest**, testing a Task Manager web app
across three releases.

| Release | Change | Result |
|---|---|---|
| **v2.0** | Stable | ✅ 31 passed, 2 skipped (sort feature not built yet) |
| **v2.1** | Adds "Sort by priority", but breaks 6 existing UI behaviours | ❌ **9 failed: release blocked** |
| **v2.2** | Sort kept, all 6 regressions fixed | ✅ 33 passed |

Details: [`docs/release_notes.md`](docs/release_notes.md) · Test cases: [`docs/test_cases.csv`](docs/test_cases.csv)

## Framework features
| Feature | Where | Why |
|---|---|---|
| Page objects + component objects | `pages/` (`TasksPage`, `TaskRow`) | Locators live in one place; tests read like user steps |
| `data-testid` locators | every element in the app | Stable: they don't change when the design does |
| **Login once via API**, reuse the session cookie | `auth_cookies` fixture | No repeated UI logins; login itself is still tested through the UI |
| **API-assisted setup** | `seed` fixture, `/api/tasks` | Create test data in milliseconds, then verify it in the UI |
| **Data-driven tests** from JSON | `data/*.json`, `load_data()` | Add a test case by adding a line of data, no code |
| Browser dialogs | `TaskRow.delete(confirm=...)` | Accept or cancel `confirm()` popups |
| Multiple users at once | `test_multi_user.py` | Separate browser contexts = separate sessions |
| **Screenshot in the HTML report on failure** | `pytest_runtest_makereport` hook | See what the page looked like when it failed |
| Playwright trace on failure | `--tracing retain-on-failure` | Replay every step: DOM, network, console |
| Smoke / regression / new-feature suites | markers in `pytest.ini` | Run the right subset at the right time |
| Release-aware tests | `--release`, `@pytest.mark.since("2.1")` | Same suite against any version |
| **Parallel execution** | `pytest -n auto` (pytest-xdist) | Each worker gets its own app server, so tests never collide |
| **Cross-browser CI** | GitHub Actions matrix | Chromium, Firefox and WebKit on every push |

## Run it
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
playwright install chromium

pytest                          # latest release (2.2), Chromium
pytest --release 2.1            # the release with regressions
pytest -n auto                  # in parallel
pytest -m smoke                 # smoke suite only
pytest --headed --slowmo 300    # watch the browser
pytest --browser firefox        # after: playwright install firefox
```
Report: `reports/report.html` (failure screenshots included). Traces: `test-results/`, open one with
`playwright show-trace test-results/<test>/trace.zip`.

To use the app yourself: `python run_server.py` → http://127.0.0.1:5002 (login `demo` / `Demo@123`).

## Project structure
```
app/        # Task Manager web app (system under test), 3 releases
pages/      # Page objects and the TaskRow component object
tests/      # Tests + conftest.py (framework fixtures and hooks)
data/       # JSON test data for data-driven tests
docs/       # Release notes, test cases
```

## CI
For each browser (Chromium, Firefox, WebKit): smoke tests, then the full suite in parallel on v2.2 and v2.0
(must pass), then v2.1 as a regression gate demo (must fail). Reports and traces are uploaded as artifacts.

Verified locally on Chromium. Firefox and WebKit run in the CI matrix.
