import os
import json
import http.server
from datetime import datetime

# Keys to display — prefix filter so students can see exactly what they injected
SHOW_PREFIXES = ("APP_", "DB_", "API_", "FEATURE_")

# Treat these substrings as secret-ish → mask value behind a reveal toggle
SECRET_HINTS = ("PASSWORD", "SECRET", "TOKEN", "KEY")

# Per-key icon (inline SVG via emoji to keep zero-dep). Falls back to ▦.
KEY_ICONS = {
    "APP_ENV": "🌍",
    "APP_VERSION": "🏷️",
    "APP_COLOR": "🎨",
    "APP_NAME": "📦",
    "DB_HOST": "🗄️",
    "DB_PORT": "🔌",
    "DB_NAME": "📚",
    "DB_USER": "👤",
    "DB_PASSWORD": "🔐",
    "API_KEY": "🔑",
    "API_URL": "🔗",
    "FEATURE_FLAGS": "🚩",
}

# CSS named colors that we accept directly as APP_COLOR / *_COLOR values.
NAMED_COLORS = {
    "red": "#dc2626", "orange": "#d97706", "amber": "#f59e0b",
    "yellow": "#eab308", "green": "#16a34a", "lime": "#65a30d",
    "teal": "#0d9488", "cyan": "#06b6d4", "blue": "#2563eb",
    "indigo": "#4f46e5", "violet": "#7c3aed", "purple": "#9333ea",
    "pink": "#db2777", "rose": "#e11d48", "gray": "#6b7280",
    "grey": "#6b7280", "black": "#111111", "white": "#ffffff",
}


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>envapp — {env}</title>
<style>
  :root {{
    --accent: {color};
    --bg: #0f172a;
    --panel: #ffffff;
    --muted: #64748b;
    --line: #e2e8f0;
    --ink: #0f172a;
    --chip: #f1f5f9;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0 }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
    color: var(--ink);
    padding: 2rem;
    min-height: 100vh;
  }}
  .wrap {{ max-width: 1100px; margin: 0 auto }}

  header {{
    background: linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 70%, #000) 100%);
    color: #fff;
    padding: 1.5rem 1.75rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 30px -10px color-mix(in srgb, var(--accent) 50%, transparent);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
  }}
  header .left h1 {{ font-size: 1.5rem; font-weight: 700; letter-spacing: -0.01em }}
  header .left p {{ font-size: 0.85rem; opacity: 0.9; margin-top: 6px; font-family: ui-monospace, monospace }}
  header .badges {{ display: flex; gap: 8px; flex-wrap: wrap }}
  .badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(255,255,255,0.18);
    backdrop-filter: blur(6px);
    padding: 6px 12px; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600;
    border: 1px solid rgba(255,255,255,0.25);
  }}
  .badge .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 0 3px rgba(74,222,128,0.25) }}

  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }}
  .card {{
    background: var(--panel);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    border: 1px solid var(--line);
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
    transition: transform 0.15s, box-shadow 0.15s;
  }}
  .card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px -8px rgba(15,23,42,0.15) }}
  .card-head {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px }}
  .card-icon {{ font-size: 1.1rem }}
  .card-label {{ font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600 }}
  .card-value {{ font-size: 1.15rem; font-weight: 700; color: var(--ink); word-break: break-all }}

  .section-title {{
    display: flex; align-items: center; gap: 8px;
    font-size: 0.85rem; font-weight: 700; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 1.5rem 0 0.75rem;
  }}

  .chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px }}
  .chip {{
    display: inline-flex; align-items: center; gap: 5px;
    background: var(--chip); color: #334155;
    padding: 4px 10px; border-radius: 999px;
    font-size: 0.78rem; font-weight: 500;
    border: 1px solid var(--line);
  }}
  .chip.on {{ background: #dcfce7; color: #166534; border-color: #bbf7d0 }}
  .chip.off {{ background: #fee2e2; color: #991b1b; border-color: #fecaca }}

  table {{
    width: 100%;
    background: var(--panel);
    border-radius: 12px;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid var(--line);
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  }}
  thead th {{
    background: #f8fafc; text-align: left;
    padding: 12px 16px; font-size: 0.72rem; font-weight: 700;
    color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em;
    border-bottom: 1px solid var(--line);
  }}
  tbody td {{
    padding: 12px 16px; font-size: 0.88rem;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: middle;
  }}
  tbody tr:last-child td {{ border-bottom: none }}
  tbody tr:hover {{ background: #fafbfc }}

  .key-cell {{ display: flex; align-items: center; gap: 10px; font-family: ui-monospace, monospace; font-weight: 600; color: #1e293b }}
  .key-icon {{ font-size: 1.1rem }}
  .prefix-tag {{
    font-size: 0.65rem; font-weight: 700;
    padding: 2px 7px; border-radius: 4px;
    margin-left: auto;
    text-transform: uppercase; letter-spacing: 0.05em;
  }}
  .prefix-APP_ {{ background: #dbeafe; color: #1e40af }}
  .prefix-DB_ {{ background: #f3e8ff; color: #6b21a8 }}
  .prefix-API_ {{ background: #fef3c7; color: #92400e }}
  .prefix-FEATURE_ {{ background: #d1fae5; color: #065f46 }}

  .val-cell {{ font-family: ui-monospace, monospace; color: #0f172a; word-break: break-all }}

  .color-swatch {{
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--swatch-bg, #888); color: #fff;
    padding: 4px 12px; border-radius: 6px;
    font-weight: 600; font-size: 0.85rem;
    border: 1px solid rgba(0,0,0,0.1);
    text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    cursor: default;
  }}
  .color-swatch::before {{
    content: ""; width: 10px; height: 10px; border-radius: 50%;
    background: rgba(255,255,255,0.85); display: inline-block;
  }}

  .secret-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #fef2f2; color: #991b1b;
    padding: 4px 10px; border-radius: 6px;
    font-family: ui-monospace, monospace; font-size: 0.82rem;
    border: 1px dashed #fca5a5;
    cursor: pointer; user-select: none;
  }}
  .secret-pill:hover {{ background: #fee2e2 }}
  .secret-pill .reveal {{ font-weight: 600 }}

  .empty {{
    text-align: center; padding: 3rem 1rem;
    color: var(--muted); font-size: 0.95rem;
  }}
  .empty .big {{ font-size: 2.5rem; margin-bottom: 0.5rem }}
  .empty code {{ background: #f1f5f9; padding: 2px 8px; border-radius: 4px; font-size: 0.85em }}

  footer {{
    margin-top: 2rem; padding: 1rem;
    font-size: 0.8rem; color: var(--muted); text-align: center;
    border-top: 1px solid var(--line);
  }}
  footer code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: ui-monospace, monospace }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="left">
      <h1>⚙️ envapp &mdash; {env_label}</h1>
      <p>🐳 pod: {hostname} &nbsp;|&nbsp; 🕒 {timestamp}</p>
    </div>
    <div class="badges">
      <span class="badge"><span class="dot"></span> healthy</span>
      <span class="badge">v{version}</span>
      <span class="badge">{env_emoji} {env}</span>
    </div>
  </header>

  <div class="section-title">📌 Quick view</div>
  <div class="grid">
    <div class="card">
      <div class="card-head"><span class="card-icon">🌍</span><span class="card-label">Environment</span></div>
      <div class="card-value">{env}</div>
    </div>
    <div class="card">
      <div class="card-head"><span class="card-icon">🏷️</span><span class="card-label">App version</span></div>
      <div class="card-value">{version}</div>
    </div>
    <div class="card">
      <div class="card-head"><span class="card-icon">🗄️</span><span class="card-label">Database host</span></div>
      <div class="card-value">{db_host}</div>
    </div>
    <div class="card">
      <div class="card-head"><span class="card-icon">🚩</span><span class="card-label">Feature flags</span></div>
      <div class="chips">{feature_chips}</div>
    </div>
  </div>

  <div class="section-title">🔧 All injected variables ({count})</div>
  <table>
    <thead><tr><th style="width:42%">Key</th><th>Value</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <footer>
    Reload after <code>kubectl rollout restart deployment/envapp</code> to see config changes.
  </footer>
</div>

<script>
  document.querySelectorAll('.secret-pill').forEach(el => {{
    const real = el.dataset.value;
    const masked = '•'.repeat(Math.min(12, real.length));
    el.querySelector('.reveal').textContent = masked;
    el.addEventListener('click', () => {{
      const span = el.querySelector('.reveal');
      span.textContent = (span.textContent === masked) ? real : masked;
    }});
  }});
</script>
</body>
</html>"""


def env_color():
    e = os.getenv("APP_ENV", "").lower()
    return {"production": "#dc2626", "staging": "#d97706", "dev": "#16a34a"}.get(e, "#3b82f6")


def env_emoji():
    e = os.getenv("APP_ENV", "").lower()
    return {"production": "🔥", "staging": "🧪", "dev": "🌱"}.get(e, "❔")


def env_label():
    return os.getenv("APP_ENV", "unknown").upper()


def html_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def is_secret(key):
    return any(h in key for h in SECRET_HINTS)


def is_color_key(key):
    return key.endswith("_COLOR") or key == "APP_COLOR"


def resolve_color(val):
    v = val.strip().lower()
    if v in NAMED_COLORS:
        return NAMED_COLORS[v]
    if v.startswith("#") and len(v) in (4, 7):
        return v
    return None


def render_value(key, val):
    if not val:
        return '<span class="val-cell" style="color:#94a3b8;font-style:italic">not set</span>'
    safe = html_escape(val)

    # color → swatch button
    if is_color_key(key):
        hex_ = resolve_color(val)
        if hex_:
            return f'<span class="color-swatch" style="--swatch-bg: {hex_}">{safe} &nbsp;<span style="opacity:0.85;font-size:0.75rem">{hex_}</span></span>'

    # secret → masked pill
    if is_secret(key):
        return f'<span class="secret-pill" data-value="{safe}" title="click to reveal">🔒 <span class="reveal"></span></span>'

    # feature flags → chips
    if key == "FEATURE_FLAGS" and val:
        chips = "".join(f'<span class="chip on">✓ {html_escape(f.strip())}</span>'
                        for f in val.split(",") if f.strip())
        return f'<div class="chips">{chips}</div>'

    # port → numeric chip
    if key.endswith("_PORT"):
        return f'<span class="chip">🔌 {safe}</span>'

    # url/host → link-styled mono
    if key.endswith(("_HOST", "_URL")):
        return f'<span class="val-cell">🔗 {safe}</span>'

    return f'<span class="val-cell">{safe}</span>'


def render_key_cell(key):
    icon = KEY_ICONS.get(key, "▦")
    prefix = next((p for p in SHOW_PREFIXES if key.startswith(p)), "")
    tag = f'<span class="prefix-tag prefix-{prefix}">{prefix.rstrip("_")}</span>' if prefix else ""
    return f'<div class="key-cell"><span class="key-icon">{icon}</span><span>{html_escape(key)}</span>{tag}</div>'


def feature_chips():
    val = os.getenv("FEATURE_FLAGS", "")
    if not val:
        return '<span class="chip off">none</span>'
    return "".join(f'<span class="chip on">✓ {html_escape(f.strip())}</span>'
                   for f in val.split(",") if f.strip())


ALWAYS_SHOW = ("DB_PASSWORD", "API_KEY")


def build_rows():
    items = {k: v for k, v in os.environ.items() if k.startswith(SHOW_PREFIXES)}
    for k in ALWAYS_SHOW:
        items.setdefault(k, "")
    if not items:
        return ('<tr><td colspan="2"><div class="empty">'
                '<div class="big">📭</div>'
                'No <code>APP_</code> / <code>DB_</code> / <code>API_</code> / <code>FEATURE_</code> variables found.<br>'
                'Apply a ConfigMap to see values here.'
                '</div></td></tr>')
    return "".join(
        f'<tr><td>{render_key_cell(k)}</td><td>{render_value(k, v)}</td></tr>'
        for k, v in sorted(items.items())
    )


def count_vars():
    return sum(1 for k in os.environ if k.startswith(SHOW_PREFIXES))


def build_page():
    return HTML.format(
        env=html_escape(os.getenv("APP_ENV", "unknown")),
        env_label=html_escape(env_label()),
        env_emoji=env_emoji(),
        version=html_escape(os.getenv("APP_VERSION", "1.0")),
        db_host=html_escape(os.getenv("DB_HOST", "not set")),
        feature_chips=feature_chips(),
        hostname=html_escape(os.uname().nodename),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        color=env_color(),
        rows=build_rows(),
        count=count_vars(),
    )


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "env": os.getenv("APP_ENV", "unknown")}).encode())
            return

        body = build_page().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"envapp listening on :{port}")
    print(f"APP_ENV = {os.getenv('APP_ENV', 'not set')}")
    http.server.HTTPServer(("", port), Handler).serve_forever()
