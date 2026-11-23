"""URL 단축 웹 서버 (표준 모듈 http.server만 사용).

    python3 src/server.py --port 8000 --table chaining
    python3 src/server.py --port 8000 --table linear

GET  /          URL 입력 폼
POST /shorten   단축 결과 페이지 (잘못된 URL이면 400)
GET  /table     코드 -> URL 테이블 내부 (버킷·슬롯과 Horner 해시 계산 과정)
GET  /<code>    원래 URL로 302, 없으면 404
"""

import argparse
import html
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hash_table import TABLES, horner_steps  # noqa: E402
from shortener import Shortener  # noqa: E402

STYLE = """
body{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#222}
input[type=text]{width:70%;padding:.5rem;font-size:1rem}
button{padding:.5rem 1rem;font-size:1rem}
code{background:#f3f3f3;padding:0 .25rem;border-radius:3px}
table{border-collapse:collapse;margin:.5rem 0}
td,th{border:1px solid #ddd;padding:.25rem .5rem;font-size:.9rem;vertical-align:top}
.empty{color:#aaa}.err{color:#c0392b}.chain span{display:inline-block;border:1px solid #2a6fdb;
border-radius:4px;padding:0 .4rem;margin:.1rem}.home{color:#1a9e5c}.moved{color:#d9534f}
"""


def page(title, body):
    return (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{STYLE}</style></head>"
            f"<body><h1>{html.escape(title)}</h1>{body}"
            f"<p><a href='/'>처음으로</a> · <a href='/table'>/table</a></p></body></html>")


FORM = ("<form method='post' action='/shorten'>"
        "<input type='text' name='url' placeholder='https://example.com/아주/긴/주소' autofocus> "
        "<button>줄이기</button></form>")


def horner_html(key, m):
    rows = "".join(f"<tr><td><code>{html.escape(ch)}</code></td><td>{o}</td>"
                   f"<td>(31×{h} + {o}) mod {m} = <b>{nh}</b></td></tr>"
                   for ch, o, h, nh in horner_steps(key, m))
    return f"<table><tr><th>글자</th><th>ord</th><th>h</th></tr>{rows}</table>"


def table_html(t):
    head = (f"<p>방식: <b>{t.kind}</b> · 크기 M = {t.capacity} · 원소 {len(t)} · "
            f"적재율 {t.load_factor():.2f}</p>")
    if t.kind == "chaining":
        rows = []
        for i, chain in enumerate(t.buckets()):
            if chain:
                cells = "".join(f"<span><code>{html.escape(k)}</code> → {html.escape(v)}</span>"
                                for k, v in chain)
            else:
                cells = "<span class='empty' style='border:0'>비어 있음</span>"
            rows.append(f"<tr><td>{i}</td><td class='chain'>{cells}</td></tr>")
        body = f"<table><tr><th>버킷</th><th>체인</th></tr>{''.join(rows)}</table>"
    else:
        rows = []
        for i, slot in enumerate(t.slots()):
            if slot is None:
                rows.append(f"<tr><td>{i}</td><td colspan='3' class='empty'>비어 있음</td></tr>")
            else:
                k, v, home = slot
                cls = "home" if home == i else "moved"
                note = "제자리" if home == i else f"원래 {home}번 → {(i - home) % t.capacity}칸 밀림"
                rows.append(f"<tr><td>{i}</td><td><code>{html.escape(k)}</code></td>"
                            f"<td>{html.escape(v)}</td><td class='{cls}'>{note}</td></tr>")
        body = (f"<table><tr><th>슬롯</th><th>코드</th><th>URL</th><th>해시 위치</th></tr>"
                f"{''.join(rows)}</table>")
    calc = "".join(f"<h3><code>{html.escape(k)}</code></h3>{horner_html(k, t.capacity)}"
                   for k, _ in t.items())
    return head + body + "<h2>Horner 해시 계산</h2>" + (calc or "<p class='empty'>아직 없음</p>")


def make_handler(shortener):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, body, headers=()):
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            for k, v in headers:
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _base(self):
            host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "localhost"
            proto = self.headers.get("X-Forwarded-Proto") or "http"
            return f"{proto}://{host}"

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                return self._send(200, page("URL 단축기", FORM))
            if path == "/table":
                return self._send(200, page("테이블 들여다보기", table_html(shortener.by_code)))
            if path == "/favicon.ico":
                return self._send(404, "")
            code = path[1:]
            url = shortener.expand(code)
            if url is None:
                return self._send(404, page("찾을 수 없음",
                                            f"<p class='err'>없는 코드입니다: <code>{html.escape(code)}</code></p>"))
            self._send(302, "", [("Location", url)])

        def do_POST(self):
            if self.path != "/shorten":
                return self._send(404, page("찾을 수 없음", ""))
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8", "replace")
            url = ""
            for k, v in parse_qsl(raw, keep_blank_values=True):
                if k == "url":
                    url = v
            try:
                code = shortener.shorten(url)
            except ValueError as e:
                return self._send(400, page("URL 단축기",
                                            f"<p class='err'>{html.escape(str(e))}</p>{FORM}"))
            link = f"{self._base()}/{code}"
            body = (f"<p>단축 링크: <a href='{html.escape(link)}'><b>{html.escape(link)}</b></a></p>"
                    f"<p>원래 주소: <code>{html.escape(shortener.expand(code))}</code></p>{FORM}")
            self._send(200, page("URL 단축기", body))

        def log_message(self, fmt, *args):
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    return Handler


def main(argv=None):
    p = argparse.ArgumentParser(description="URL 단축 서버")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--table", default="chaining", choices=[name for name, _ in TABLES])
    a = p.parse_args(argv)
    table_class = [cls for name, cls in TABLES if name == a.table][0]
    server = ThreadingHTTPServer(("0.0.0.0", a.port), make_handler(Shortener(table_class)))
    print(f"http://localhost:{a.port}  (테이블: {a.table})  Ctrl+C로 멈춤")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
