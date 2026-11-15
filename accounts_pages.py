"""Self-contained Jinja pages; no new HTML/static files are needed."""

from __future__ import annotations

from flask import render_template_string


BASE_START = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} · GameTrend</title>
<style>
:root{color-scheme:dark;--bg:#0b1021;--panel:#151c34;--line:#323d5b;--text:#f1f4ff;--muted:#a9b6d1;--accent:#9f88ff;--danger:#ff9a9a}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#202b4c 0%,var(--bg) 56%);color:var(--text);font:16px/1.5 system-ui,-apple-system,Segoe UI,Arial,sans-serif;min-height:100vh}
a{color:#c5b8ff;text-decoration:none}a:hover{text-decoration:underline}
.sitebar{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:19px max(22px,calc((100vw - 930px)/2));border-bottom:1px solid var(--line);background:#0b1021dd}
.brand{font-size:1.25rem;font-weight:800;letter-spacing:.2px;color:white}.sitebar nav{display:flex;flex-wrap:wrap;gap:18px}
main{width:min(92%,760px);margin:54px auto 80px}.panel{background:var(--panel);border:1px solid var(--line);padding:30px;border-radius:18px;box-shadow:0 20px 60px #05081850}
h1{margin:0 0 6px;font-size:1.8rem}h2{font-size:1.17rem;margin:0 0 14px}.sub{color:var(--muted);margin:0 0 25px}.notice{padding:13px 16px;border-radius:9px;margin:14px 0;background:#234338;color:#c2f9dc}.error{padding:13px 16px;border-radius:9px;margin:14px 0;background:#57252c;color:#ffdddd}
label{display:block;font-weight:600;margin:15px 0 7px}input{width:100%;padding:12px 13px;background:#090f21;border:1px solid #526080;border-radius:9px;color:white;font:inherit}input:focus{outline:2px solid var(--accent);outline-offset:1px}
button,.button{display:inline-block;border:0;background:var(--accent);color:#101326;border-radius:9px;padding:11px 18px;font:inherit;font-weight:750;cursor:pointer;margin-top:19px}.button{text-decoration:none}button:hover,.button:hover{filter:brightness(1.13);text-decoration:none}.danger-btn{background:#ff8d97}.secondary{background:#354369;color:white}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.hint{font-size:.88rem;color:var(--muted)}.split{border-top:1px solid var(--line);margin-top:26px;padding-top:25px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}.stat{border:1px solid var(--line);padding:16px;border-radius:10px}.stat b{display:block;overflow-wrap:anywhere}
.history{display:grid;gap:15px;margin-top:22px}.submission{border:1px solid var(--line);border-radius:12px;padding:18px}.submission h3{margin:0 0 6px}.submission p{margin:7px 0}.muted{color:var(--muted)}
@media(max-width:500px){.panel{padding:20px}.sitebar{padding:16px 20px}main{margin-top:25px}}
</style></head><body>
<header class="sitebar"><a class="brand" href="/">🎮 GameTrend</a>
<nav><a href="/">Survey</a><a href="/results">Results</a>
{% if user %}<a href="{{ url_for('account_pages.dashboard') }}">My account</a><a href="{{ url_for('account_pages.history') }}">My votes</a>
{% else %}<a href="{{ url_for('account_pages.login') }}">Log in</a><a href="{{ url_for('account_pages.register') }}">Sign up</a>{% endif %}
</nav></header><main><div class="panel">
{% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}
{% if notice %}<div class="notice" role="status">{{ notice }}</div>{% endif %}
"""
BASE_END = "</div></main></body></html>"

LOGIN = r"""
<h1>Log in</h1><p class="sub">See your own survey history and manage your GameTrend profile.</p>
<form method="post" action="{{ url_for('account_pages.login') }}">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<input type="hidden" name="next" value="{{ next_path }}">
<label for="login">Username or email</label><input id="login" name="login" required maxlength="254" autocomplete="username" value="{{ login_value }}">
<label for="password">Password</label><input id="password" name="password" type="password" required autocomplete="current-password">
<button type="submit">Log in</button></form>
<p class="hint">No account? <a href="{{ url_for('account_pages.register') }}">Create one</a>.</p>
"""

REGISTER = r"""
<h1>Create an account</h1><p class="sub">Track your own gaming choices while contributing to the community rankings.</p>
<form method="post" action="{{ url_for('account_pages.register') }}">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<label for="username">Username</label><input id="username" name="username" required minlength="3" maxlength="32" pattern="[A-Za-z0-9_]+" autocomplete="username" value="{{ username_value }}">
<label for="email">Email</label><input id="email" name="email" type="email" required maxlength="254" autocomplete="email" value="{{ email_value }}">
<label for="password">Password</label><input id="password" name="password" type="password" required minlength="12" maxlength="128" autocomplete="new-password">
<p class="hint">Use at least 12 characters. Do not reuse another account's password.</p>
<label for="confirm">Confirm password</label><input id="confirm" name="confirm" type="password" required minlength="12" autocomplete="new-password">
<button type="submit">Sign up</button></form>
<p class="hint">Already registered? <a href="{{ url_for('account_pages.login') }}">Log in</a>.</p>
"""

DASHBOARD = r"""
<h1>Your GameTrend account</h1><p class="sub">Welcome back, {{ user.username }}.</p>
<div class="stats"><div class="stat"><span class="muted">Username</span><b>{{ user.username }}</b></div>
<div class="stat"><span class="muted">Email</span><b>{{ user.email }}</b></div></div>
<div class="row"><a class="button" href="{{ url_for('account_pages.history') }}">View my votes</a>
<a class="button secondary" href="/#survey">Submit a survey</a></div>
<div class="split"><h2>Edit profile</h2><p class="hint">Enter your current password to change your account details.</p>
<form method="post" action="{{ url_for('account_pages.profile') }}">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<label for="username">Username</label><input id="username" name="username" required maxlength="32" value="{{ user.username }}">
<label for="email">Email</label><input id="email" name="email" type="email" required maxlength="254" value="{{ user.email }}">
<label for="current_password">Current password</label><input id="current_password" name="current_password" type="password" required autocomplete="current-password">
<button type="submit">Save profile</button></form></div>
<div class="split"><h2>Change password</h2>
<form method="post" action="{{ url_for('account_pages.password') }}">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<label for="old_password">Current password</label><input id="old_password" name="current_password" type="password" required autocomplete="current-password">
<label for="new_password">New password</label><input id="new_password" name="new_password" type="password" required minlength="12" maxlength="128" autocomplete="new-password">
<label for="confirm_password">Confirm new password</label><input id="confirm_password" name="confirm" type="password" required autocomplete="new-password">
<button type="submit">Update password</button></form></div>
<div class="split"><h2>Sign out</h2>
<form method="post" action="{{ url_for('account_pages.logout') }}">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}"><button class="secondary" type="submit">Log out</button>
</form></div>
<div class="split"><h2>Delete account</h2><p class="hint">Deleting your account removes its profile and personal submission history links. Your past votes remain anonymously in the public totals.</p>
<form method="post" action="{{ url_for('account_pages.delete') }}">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<label for="delete_password">Current password</label><input id="delete_password" name="current_password" type="password" required autocomplete="current-password">
<label for="confirm_delete">Type DELETE to confirm</label><input id="confirm_delete" name="confirmation" required autocomplete="off">
<button type="submit" class="danger-btn">Permanently delete account</button></form></div>
"""

HISTORY = r"""
<h1>My survey history</h1><p class="sub">Your latest 100 surveys. Only submissions made while signed in are associated with your account.</p>
{% if submissions %}<div class="history">
{% for s in submissions %}<article class="submission">
<h3>{{ s.platform }} <span class="muted">#{{ s.submission_id }}</span></h3>
<p class="hint">{{ s.created_at }}</p>
<p><strong>Favorite:</strong> {{ s.favorite or '—' }}</p>
<p><strong>Most played:</strong> {{ s.most_played or '—' }}</p>
<p><strong>Currently playing:</strong> {{ s.currently_playing or '—' }}</p>
</article>{% endfor %}</div>
{% else %}<p>No saved surveys yet. <a href="/#survey">Submit your first survey</a> while signed in.</p>{% endif %}
"""


def render_page(title: str, contents: str, **context):
    return render_template_string(BASE_START + contents + BASE_END, title=title, **context)
