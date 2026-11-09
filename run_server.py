"""
Run the Task Manager on http://127.0.0.1:5002 to look at it in your browser.

    python run_server.py           # latest release (2.2)
    python run_server.py 2.1       # the release with UI regressions

Log in as demo / Demo@123 (or alex / Alex@123). The automated tests do NOT need this.
"""
import sys

from app.task_app import RELEASES, create_app

if __name__ == "__main__":
    release = sys.argv[1] if len(sys.argv) > 1 else "2.2"
    if release not in RELEASES:
        sys.exit(f"Unknown release {release}. Choose from: {', '.join(RELEASES)}")
    print(f"Task Manager v{release} on http://127.0.0.1:5002  (login: demo / Demo@123)")
    create_app(release).run(host="127.0.0.1", port=5002)
