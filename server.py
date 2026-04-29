import os
import json
import http.server
from datetime import datetime

# Keys to display — prefix filter so students can see exactly what they injected
SHOW_PREFIXES = ("APP_", "DB_", "API_", "FEATURE_")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>envapp</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0 }}
  body {{ font-family: system-ui, sans-serif; background: #f5f5f5; padding: 2rem }}
  header {{ background: {color}; color: #fff; padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1.5rem }}
  header h1 {{ font-size: 1.4rem; font-weight: 600 }}
  header p  {{ font-size: 0.85rem; opacity: 0.85; margin-top: 4px }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin-bottom: 1.5rem }}
  .card {{ background: #fff; border-radius: 8px; padding: 1rem 1.25rem; border: 1px solid #e5e5e5 }}
  .card-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px }}
  .card-value {{ font-size: 1.1rem; font-weight: 600; color: #111; word-break: break-all }}
  table {{ width: 100%; background: #fff; border-radius: 8px; border-collapse: collapse; border: 1px solid #e5e5e5 }}
  th {{ background: #f9f9f9; text-align: left; padding: 10px 14px; font-size: 0.8rem; color: #555; border-bottom: 1px solid #e5e5e5 }}
  td {{ padding: 10px 14px; font-size: 0.9rem; border-bottom: 1px solid #f0f0f0; font-family: monospace }}
  tr:last-child td {{ border-bottom: none }}
  .key {{ color: #2563eb; font-weight: 500 }}
  .val {{ color: #111 }}
  .empty {{ text-align: center; padding: 2rem; color: #aaa; font-size: 0.9rem }}
  footer {{ margin-top: 1.5rem; font-size: 0.8rem; color: #aaa; text-align: center }}
</style>
</head>
<body>
  <header>
    <h1>envapp &mdash; {env}</h1>
    <p>pod: {hostname} &nbsp;|&nbsp; {timestamp}</p>
  </header>

  <div class="grid">
    <div class="card">
      <div class="card-label">Environment</div>
      <div class="card-value">{env}</div>
    </div>
    <div class="card">
      <div class="card-label">App version</div>
      <div class="card-value">{version}</div>
    </div>
    <div class="card">
      <div class="card-label">Database host</div>
      <div class="card-value">{db_host}</div>
    </div>
    <div class="card">
      <div class="card-label">Feature flags</div>
      <div class="card-value">{features}</div>
    </div>
  </div>

  <table>
    <thead><tr><th>Key</th><th>Value</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <footer>Reload the page after kubectl rollout restart to see config changes</footer>
</body>
</html>"""


def env_color():
    e = os.getenv("APP_ENV", "").lower()
    return {"production": "#dc2626", "staging": "#d97706", "dev": "#16a34a"}.get(e, "#3b82f6")


def build_rows():
    items = {k: v for k, v in os.environ.items() if k.startswith(SHOW_PREFIXES)}
    if not items:
        return '<tr><td colspan="2" class="empty">No APP_ / DB_ / API_ / FEATURE_ variables found.<br>Inject a ConfigMap to see values here.</td></tr>'
    return "".join(
        f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
        for k, v in sorted(items.items())
    )


def build_page():
    return HTML.format(
        env=os.getenv("APP_ENV", "unknown"),
        version=os.getenv("APP_VERSION", "1.0"),
        db_host=os.getenv("DB_HOST", "not set"),
        features=os.getenv("FEATURE_FLAGS", "none"),
        hostname=os.uname().nodename,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        color=env_color(),
        rows=build_rows(),
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
