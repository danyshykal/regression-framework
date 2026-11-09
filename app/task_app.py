"""
Task Manager web app: the system under test.

    create_app(release="2.0")  stable release
    create_app(release="2.1")  adds "sort by priority", but accidentally introduces UI regressions [U1]..[U6]
    create_app(release="2.2")  sort kept, regressions fixed (latest)

Server-rendered HTML + a little JavaScript. Every element tests need has a data-testid.
/api/* is a small JSON API the test framework uses to log in and set up data quickly.
"""
import itertools
from datetime import date

from flask import Flask, jsonify, redirect, render_template_string, request, session, url_for

RELEASES = {
    "2.0": {"sort_feature": False, "regressions": False},
    "2.1": {"sort_feature": True, "regressions": True},
    "2.2": {"sort_feature": True, "regressions": False},
}
USERS = {"demo": "Demo@123", "alex": "Alex@123"}     # demo accounts only
PRIORITIES = ("high", "medium", "low")
MAX_TITLE = 100

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{{ title }} - Task Manager</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 760px; margin: 24px auto; padding: 0 16px; }
  [hidden] { display: none !important; }
  header, nav, .row { display: flex; gap: 12px; align-items: center; }
  header { justify-content: space-between; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
  nav a[aria-current] { font-weight: bold; }
  ul { list-style: none; padding: 0; }
  li { display: flex; gap: 12px; align-items: center; padding: 8px 0; border-bottom: 1px solid #eee; }
  li.done [data-testid=task-title] { text-decoration: line-through; color: #888; }
  .error { color: #b00020; }
  .p-high { color: #b00020; } .p-medium { color: #a15c00; } .p-low { color: #2e7d32; }
  form.inline { display: inline; margin: 0; }
</style></head>
<body>
{% if page == 'login' %}
  <h1>Task Manager</h1>
  <form method="post" action="/login" data-testid="login-form">
    <p><label>Username <input name="username" data-testid="username" value="{{ username or '' }}"></label></p>
    <p><label>Password <input name="password" type="password" data-testid="password"></label></p>
    {% if error %}<p class="error" role="alert" data-testid="login-error">{{ error }}</p>{% endif %}
    <button data-testid="login-button">Log in</button>
  </form>
{% else %}
  <header>
    <h1>My tasks</h1>
    <div><span data-testid="user-name">{{ user }}</span> · <a href="/logout" data-testid="logout">Log out</a></div>
  </header>
  <p data-testid="summary">{{ open_count }} open · {{ done_count }} done</p>
  <nav>
    <a href="/tasks?filter=all" data-testid="filter-all" {% if filter == 'all' %}aria-current="page"{% endif %}>All</a>
    <a href="/tasks?filter=open" data-testid="filter-open" {% if filter == 'open' %}aria-current="page"{% endif %}>Open</a>
    <a href="/tasks?filter=done" data-testid="filter-done" {% if filter == 'done' %}aria-current="page"{% endif %}>Done</a>
    {% if sort_feature %}<a href="/tasks?filter={{ filter }}&sort=priority" data-testid="sort-priority">Sort by priority</a>{% endif %}
  </nav>
  <form method="post" action="/tasks" class="row" data-testid="new-task-form">
    <input name="title" placeholder="New task" data-testid="title-input" value="{{ form.title or '' }}">
    <select name="priority" data-testid="priority-select">
      {% for p in priorities %}<option value="{{ p }}" {% if form.priority == p %}selected{% endif %}>{{ p }}</option>{% endfor %}
    </select>
    <input name="due" type="date" data-testid="due-input" value="{{ form.due or '' }}">
    <button data-testid="add-task">Add task</button>
  </form>
  {% if error %}<p class="error" role="alert" data-testid="form-error">{{ error }}</p>{% endif %}
  <p><input type="search" placeholder="Search tasks" data-testid="search"></p>
  <ul data-testid="task-list">
    {% for t in tasks %}
    <li data-testid="task-row" data-task-id="{{ t.id }}" class="{{ 'done' if t.done else '' }}">
      <form method="post" action="/tasks/{{ t.id }}/toggle" class="inline">
        <input type="checkbox" data-testid="task-toggle" aria-label="Done" {% if t.done %}checked{% endif %} onchange="this.form.submit()">
      </form>
      <span data-testid="task-title">{{ t.title }}</span>
      <span data-testid="task-priority" class="p-{{ t.priority }}">{{ t.priority }}</span>
      <span data-testid="task-due">{{ t.due or '' }}</span>
      <form method="post" action="/tasks/{{ t.id }}/delete" class="inline"
            onsubmit="{{ 'confirm(\\'Delete this task?\\'); return true;' if buggy else 'return confirm(\\'Delete this task?\\')' }}">
        <button data-testid="task-delete">Delete</button>
      </form>
    </li>
    {% endfor %}
  </ul>
  {% if not tasks %}<p data-testid="empty-state">No tasks here yet.</p>{% endif %}
  <p data-testid="no-matches" hidden>No matching tasks.</p>
  <script>
    const search = document.querySelector('[data-testid=search]');
    search.addEventListener('input', () => {
      const q = search.value.trim();
      let shown = 0;
      document.querySelectorAll('[data-testid=task-row]').forEach(row => {
        const title = row.querySelector('[data-testid=task-title]').textContent;
        const match = {{ 'title.includes(q)' if buggy else 'title.toLowerCase().includes(q.toLowerCase())' }};
        row.hidden = !match;
        if (match) shown++;
      });
      document.querySelector('[data-testid=no-matches]').hidden = shown > 0 || !document.querySelector('[data-testid=task-row]');
    });
  </script>
{% endif %}
<footer><small data-testid="release">Task Manager v{{ release }}</small></footer>
</body></html>"""
# [U1] search is case-sensitive in 2.1 (see the script above)
# [U5] Delete ignores "Cancel" on the confirm dialog in 2.1 (see the delete form above)


def create_app(release: str = "2.2") -> Flask:
    if release not in RELEASES:
        raise ValueError(f"Unknown release {release}")
    sort_feature = RELEASES[release]["sort_feature"]
    buggy = RELEASES[release]["regressions"]

    app = Flask(__name__)
    app.secret_key = "local-demo-secret"           # demo only
    tasks = {user: [] for user in USERS}            # username -> list of task dicts
    next_id = itertools.count(1)

    def current_user():
        return session.get("user")

    def validate(title, priority, due):
        """Return (clean_values, error_message)."""
        title = (title or "").strip()
        if not buggy and not title:                 # [U3] empty title accepted in 2.1
            return None, "Title is required"
        if len(title) > MAX_TITLE:
            return None, f"Title must be {MAX_TITLE} characters or fewer"
        if priority not in PRIORITIES:
            return None, "Priority must be high, medium or low"
        if due:
            try:
                due_date = date.fromisoformat(due)
            except ValueError:
                return None, "Due date must be a valid date"
            if not buggy and due_date < date.today():   # [U4] past due dates accepted in 2.1
                return None, "Due date cannot be in the past"
        return {"title": title, "priority": priority, "due": due or ""}, None

    def add_task(user, values, done=False):
        task = {"id": next(next_id), "done": done, **values}
        tasks[user].append(task)
        return task

    def render_tasks(error=None, form=None, status=200):
        user = current_user()
        mine = tasks[user]
        view = request.args.get("filter", "all")
        if view == "open":
            shown = [t for t in mine if not t["done"]]
        elif view == "done":
            shown = mine if buggy else [t for t in mine if t["done"]]   # [U6] Done filter shows everything in 2.1
        else:
            view, shown = "all", list(mine)
        if sort_feature and request.args.get("sort") == "priority":
            shown = sorted(shown, key=lambda t: PRIORITIES.index(t["priority"]))
        done_count = sum(t["done"] for t in mine)
        open_count = len(mine) if buggy else len(mine) - done_count     # [U2] wrong open count in 2.1
        html = render_template_string(
            PAGE, page="tasks", title="My tasks", user=user, tasks=shown, filter=view,
            open_count=open_count, done_count=done_count, priorities=PRIORITIES,
            form=form or {"priority": "medium"}, error=error, sort_feature=sort_feature,
            buggy=buggy, release=release)
        return html, status

    @app.before_request
    def require_login():
        public = request.path in ("/login", "/api/login") or request.path.startswith("/static")
        if not public and not current_user():
            if request.path.startswith("/api/"):
                return jsonify(error="Login required"), 401
            return redirect(url_for("login"))

    # ---------- pages ----------

    @app.get("/")
    def home():
        return redirect(url_for("task_list"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template_string(PAGE, page="login", title="Log in", release=release)
        username = request.form.get("username", "").strip()
        if USERS.get(username) and USERS[username] == request.form.get("password", ""):
            session["user"] = username
            return redirect(url_for("task_list"))
        return render_template_string(PAGE, page="login", title="Log in", username=username,
                                      error="Invalid username or password", release=release), 401

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/tasks")
    def task_list():
        return render_tasks()

    @app.post("/tasks")
    def create_task():
        form = {k: request.form.get(k, "") for k in ("title", "priority", "due")}
        values, error = validate(**form)
        if error:
            return render_tasks(error=error, form=form, status=400)
        add_task(current_user(), values)
        return redirect(url_for("task_list"))

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle(task_id):
        for t in tasks[current_user()]:
            if t["id"] == task_id:
                t["done"] = not t["done"]
        return redirect(request.referrer or url_for("task_list"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete(task_id):
        tasks[current_user()][:] = [t for t in tasks[current_user()] if t["id"] != task_id]
        return redirect(request.referrer or url_for("task_list"))

    # ---------- JSON API used by the test framework for fast login and setup ----------

    @app.post("/api/login")
    def api_login():
        data = request.get_json(silent=True) or {}
        if USERS.get(data.get("username")) and USERS[data["username"]] == data.get("password"):
            session["user"] = data["username"]
            return jsonify(user=data["username"])
        return jsonify(error="Invalid username or password"), 401

    @app.post("/api/tasks")
    def api_create_task():
        data = request.get_json(silent=True) or {}
        values, error = validate(data.get("title"), data.get("priority", "medium"), data.get("due", ""))
        if error:
            return jsonify(error=error), 400
        return jsonify(add_task(current_user(), values, done=bool(data.get("done")))), 201

    @app.post("/api/reset")
    def api_reset():
        tasks[current_user()].clear()
        return jsonify(ok=True)

    return app
