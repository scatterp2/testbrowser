#!/usr/bin/env python3
"""
jsbrowser.py - lightweight JS-capable terminal browser
deps: curl, qjs (auto-downloaded), unzip, python3

usage:
  python3 jsbrowser.py [url]
  python3 jsbrowser.py --dump <url>   # non-interactive, just print page
"""

import sys
import os
import re
import json
import html
import subprocess
import shutil
import tempfile
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

# ─── config ───────────────────────────────────────────────────────────────────
HOME       = Path.home()
BASE_DIR   = HOME / ".jsbrowser"
BIN_DIR    = BASE_DIR / "bin"
WORK_DIR   = BASE_DIR / "tmp"
COOKIE_JAR = BASE_DIR / "cookies.txt"
HISTORY    = BASE_DIR / "history.txt"
QJS        = BIN_DIR  / "qjs"
UA         = "Mozilla/5.0 (X11; Linux i686; rv:115.0) Gecko/20100101 Firefox/115.0"
QJS_URL    = "https://bellard.org/quickjs/binary_releases/quickjs-linux-i686-2024-01-13.zip"

for d in (BASE_DIR, BIN_DIR, WORK_DIR):
    d.mkdir(parents=True, exist_ok=True)
COOKIE_JAR.touch()
HISTORY.touch()

# ─── bootstrap qjs ────────────────────────────────────────────────────────────
def bootstrap_qjs():
    if QJS.exists() and os.access(QJS, os.X_OK):
        return
    print("[*] downloading qjs i686...")
    zip_path = WORK_DIR / "qjs.zip"
    subprocess.run(["curl", "-sL", QJS_URL, "-o", str(zip_path)], check=True)
    extract = WORK_DIR / "qjs_extract"
    extract.mkdir(exist_ok=True)
    subprocess.run(["unzip", "-o", str(zip_path), "-d", str(extract)], check=True)
    # find the qjs binary inside the extracted dir
    found = list(extract.rglob("qjs"))
    if not found:
        print("[!] qjs binary not found in zip")
        sys.exit(1)
    shutil.copy(str(found[0]), str(QJS))
    QJS.chmod(0o755)
    print(f"[*] qjs ready: {QJS}")

# ─── html renderer ────────────────────────────────────────────────────────────
class PageParser(HTMLParser):
    """parse HTML into text, links, forms, and script blocks"""

    SKIP   = {"script", "style", "noscript", "svg", "iframe"}
    BLOCK  = {"p","div","h1","h2","h3","h4","h5","h6","li","tr",
               "br","section","article","header","footer","nav",
               "main","aside","blockquote","pre","form","table",
               "thead","tbody","tfoot","fieldset","legend","title"}
    SPACER = {"td","th"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text    = []        # rendered text chunks
        self.links   = []        # [(num, text, href)]
        self.forms   = []        # [{action,method,fields:[{name,type,value,id}]}]
        self.scripts = []        # [src_string]
        self.title   = ""

        self._skip_depth   = 0
        self._script_buf   = []
        self._in_script    = False
        self._link         = None   # (num, href)
        self._link_buf     = []
        self._form         = None
        self._link_counter = 0
        self._last_block   = True

    def _attrs(self, attrs):
        return dict(attrs)

    def handle_starttag(self, tag, attrs):
        a = self._attrs(attrs)

        if self._skip_depth > 0:
            self._skip_depth += 1
            return

        if tag in self.SKIP:
            self._skip_depth += 1
            if tag == "script" and not a.get("src"):
                self._in_script = True
                self._script_buf = []
            return

        if tag == "title":
            self._in_script = True
            self._script_buf = []
            return

        # meta refresh
        if tag == "meta":
            he = a.get("http-equiv","").lower()
            if he == "refresh":
                m = re.search(r"url=([^\s;]+)", a.get("content",""), re.I)
                if m:
                    self._meta_refresh = m.group(1).strip("\"'")

        # links
        if tag == "a":
            href = a.get("href","")
            if href and not href.startswith("#") and not href.startswith("javascript:"):
                self._link_counter += 1
                self._link = (self._link_counter, href)
                self._link_buf = []

        # forms
        if tag == "form":
            self._form = {
                "action": a.get("action",""),
                "method": a.get("method","GET").upper(),
                "id":     a.get("id",""),
                "fields": []
            }

        # form fields
        if tag in ("input","textarea","select") and self._form is not None:
            self._form["fields"].append({
                "name":  a.get("name",""),
                "type":  a.get("type","text"),
                "value": a.get("value",""),
                "id":    a.get("id",""),
            })

        # block spacing
        if tag in self.BLOCK:
            if not self._last_block:
                self.text.append("\n")
            self._last_block = True

        if tag == "br":
            self.text.append("\n")
            self._last_block = True

        if tag in self.SPACER:
            self.text.append("  ")

        # headings
        if tag in ("h1","h2","h3"):
            self.text.append("\n")

    def handle_endtag(self, tag):
        if self._skip_depth > 0:
            self._skip_depth -= 1
            if self._skip_depth == 0 and self._in_script:
                src = "".join(self._script_buf).strip()
                if src:
                    self.scripts.append(src)
                self._in_script = False
                self._script_buf = []
            return

        if tag == "title":
            self.title = "".join(self._script_buf).strip()
            self._in_script = False
            self._script_buf = []
            return

        if tag == "a" and self._link:
            text = "".join(self._link_buf).strip()
            num, href = self._link
            if text:
                self.links.append((num, text, href))
                self.text.append(f" [{num}]")
            self._link = None
            self._link_buf = []

        if tag == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None

        if tag in self.BLOCK:
            self.text.append("\n")
            self._last_block = True

    def handle_data(self, data):
        if self._skip_depth > 0:
            if self._in_script:
                self._script_buf.append(data)
            return
        if self._in_script:
            self._script_buf.append(data)
            return
        if self._link is not None:
            self._link_buf.append(data)
        text = data
        if text.strip():
            self.text.append(text)
            self._last_block = False

    def render(self):
        out = "".join(self.text)
        # collapse 3+ newlines to 2
        out = re.sub(r"\n{3,}", "\n\n", out)
        return out.strip()


def parse_page(html_src):
    p = PageParser()
    p._meta_refresh = None
    try:
        p.feed(html_src)
    except Exception:
        pass
    return p


# ─── url helpers ──────────────────────────────────────────────────────────────
def resolve_url(base, url):
    """resolve url relative to base"""
    if not url:
        return base
    if url.startswith("http"):
        return url
    return urllib.parse.urljoin(base, url)


def url_origin(url):
    p = urllib.parse.urlparse(url)
    return f"{p.scheme}://{p.netloc}"


# ─── curl wrapper ─────────────────────────────────────────────────────────────
class Browser:
    def __init__(self):
        self.current_url  = ""
        self.current_html = ""
        self.current_page = None   # PageParser
        self.js_ctx       = {}
        self.history_list = []
        self._forms_filled = {}    # field overrides for next submit

    def fetch(self, url, method="GET", data=None, extra_headers=None):
        """fetch url with curl, return html string"""
        cmd = [
            "curl", "-sL",
            "-A", UA,
            "-b", str(COOKIE_JAR),
            "-c", str(COOKIE_JAR),
            "-D", str(WORK_DIR / "last_headers.txt"),
            "--compressed",
            "-o", str(WORK_DIR / "last_page.html"),
        ]
        if method == "POST" and data:
            cmd += ["-X", "POST", "--data", data]
        if extra_headers:
            for h in extra_headers:
                cmd += ["-H", h]
        cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[!] curl error: {result.stderr.strip()}")
            return ""

        html_src = (WORK_DIR / "last_page.html").read_text(errors="replace")

        # log history
        with open(HISTORY, "a") as f:
            f.write(url + "\n")
        self.history_list.append(url)
        self.current_url  = url
        self.current_html = html_src
        return html_src

    def run_js(self, html_src, url):
        """run inline scripts from page through qjs with fake DOM, return context dict"""
        if not QJS.exists():
            return {}

        # write page and url for dom.js to pick up
        (WORK_DIR / "last_page.html").write_text(html_src)

        dom_js = Path(__file__).parent / "dom.js"
        if not dom_js.exists():
            return {}

        env = os.environ.copy()
        env["JSBROWSER_WORK_DIR"]    = str(WORK_DIR)
        env["JSBROWSER_CURRENT_URL"] = url

        result = subprocess.run(
            [str(QJS), "--std", str(dom_js)],
            capture_output=True, text=True, env=env, timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}

    def load(self, url):
        """fetch, run JS, handle redirects, render"""
        url = resolve_url(self.current_url, url)
        print(f"[*] → {url}")
        html_src = self.fetch(url)
        if not html_src:
            return

        page = parse_page(html_src)

        # run inline JS
        ctx = {}
        try:
            ctx = self.run_js(html_src, url)
        except Exception as e:
            pass
        self.js_ctx = ctx

        # follow JS/meta redirect if any
        redirects = (ctx.get("js_redirects") or [])
        if page._meta_refresh:
            redirects.insert(0, page._meta_refresh)
        if redirects:
            rurl = resolve_url(url, redirects[0])
            if rurl != url:
                print(f"[*] redirect → {rurl}")
                self.load(rurl)
                return

        self.current_page = page
        self.current_url  = url
        self._forms_filled = {}
        self._render(page, url, ctx)

    def _render(self, page, url, ctx):
        """print the page to terminal"""
        title = ctx.get("title") or page.title or "(no title)"
        print()
        print("━" * 60)
        print(f"  {title}")
        print(f"  {url}")
        print("━" * 60)
        print(page.render())

        if page.links:
            print()
            print("── links " + "─" * 52)
            for num, text, href in page.links[:40]:
                resolved = resolve_url(url, href)
                # truncate long text/urls
                display = text[:50].replace("\n"," ").strip()
                short   = resolved[:70]
                print(f"  [{num:>3}] {display}")
                print(f"         {short}")

        if page.forms:
            print()
            print("── forms " + "─" * 52)
            for i, form in enumerate(page.forms):
                print(f"  form[{i}]: {form['method']} {form['action'] or '(current)'}")
                visible = [f for f in form["fields"]
                           if f["type"] not in ("hidden","submit")]
                for field in visible:
                    print(f"    {field['name'] or field['id']} ({field['type']})")

        if ctx.get("js_errors"):
            print()
            print("── js errors " + "─" * 47)
            for e in ctx["js_errors"][:5]:
                print(f"  {e}")

        print()

    def submit(self, form_index=0, extra=None):
        """submit a form, merging filled fields and hidden tokens"""
        page = self.current_page
        if not page or not page.forms:
            print("[!] no forms on current page")
            return

        if form_index >= len(page.forms):
            print(f"[!] no form[{form_index}]")
            return

        form   = page.forms[form_index]
        action = resolve_url(self.current_url, form["action"] or self.current_url)
        method = form["method"]

        # build field dict: hidden tokens + user fills + extra
        fields = {}
        for f in form["fields"]:
            if f["name"]:
                fields[f["name"]] = f["value"]
        # overlay JS-updated tokens
        for k, v in (self.js_ctx.get("form_tokens") or {}).items():
            fields[k] = v
        # overlay user fills
        fields.update(self._forms_filled)
        if extra:
            fields.update(extra)

        data = urllib.parse.urlencode(fields)
        print(f"[*] {method} {action}")

        if method == "POST":
            html_src = self.fetch(action, method="POST", data=data)
        else:
            sep = "&" if "?" in action else "?"
            html_src = self.fetch(action + sep + data)

        if html_src:
            page = parse_page(html_src)
            ctx  = {}
            try:
                ctx = self.run_js(html_src, self.current_url)
            except Exception:
                pass
            self.js_ctx      = ctx
            self.current_page = page
            self._forms_filled = {}
            self._render(page, self.current_url, ctx)

    def fill(self, name, value):
        """fill a form field by name or id"""
        self._forms_filled[name] = value
        print(f"[*] filled {name} = {value!r}")

    def back(self):
        if len(self.history_list) >= 2:
            self.history_list.pop()  # current
            prev = self.history_list.pop()
            self.load(prev)
        else:
            print("[!] no history")

    def show_cookies(self):
        print(COOKIE_JAR.read_text() or "(no cookies)")

    def show_source(self):
        print(self.current_html[:5000])

    def show_headers(self):
        h = WORK_DIR / "last_headers.txt"
        print(h.read_text() if h.exists() else "(none)")

    def show_js_ctx(self):
        print(json.dumps(self.js_ctx, indent=2))

    def show_forms(self):
        if not self.current_page or not self.current_page.forms:
            print("[!] no forms")
            return
        for i, form in enumerate(self.current_page.forms):
            print(f"\nform[{i}]: {form['method']} {form['action']}")
            for f in form["fields"]:
                filled = self._forms_filled.get(f["name"], f["value"])
                print(f"  {f['type']:10} {f['name'] or f['id']:30} = {filled!r}")


# ─── repl ─────────────────────────────────────────────────────────────────────
HELP = """
commands:
  <url>                  navigate to url
  <number>               follow link by number
  back / b               go back
  fill <name> <value>    fill a form field
  submit [n]             submit form (default form 0)
  forms                  show all form fields
  cookies                show cookie jar
  source                 show page source (first 5k)
  headers                show last response headers
  js                     show JS execution context
  reload                 reload current page
  help                   this message
  quit / q               exit
"""

def repl(browser, start_url):
    browser.load(start_url)

    while True:
        try:
            line = input(f"\n[{browser.current_url[:60]}]\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        if not line:
            browser._render(browser.current_page, browser.current_url, browser.js_ctx)
            continue

        parts = line.split(None, 2)
        cmd   = parts[0].lower()

        if cmd in ("quit","exit","q"):
            print("bye")
            break
        elif cmd in ("back","b"):
            browser.back()
        elif cmd == "reload":
            browser.load(browser.current_url)
        elif cmd == "cookies":
            browser.show_cookies()
        elif cmd == "source":
            browser.show_source()
        elif cmd == "headers":
            browser.show_headers()
        elif cmd == "js":
            browser.show_js_ctx()
        elif cmd == "forms":
            browser.show_forms()
        elif cmd == "help":
            print(HELP)
        elif cmd == "fill":
            if len(parts) >= 3:
                browser.fill(parts[1], parts[2])
            elif len(parts) == 2:
                val = input(f"  value for {parts[1]}: ")
                browser.fill(parts[1], val)
            else:
                print("usage: fill <name> <value>")
        elif cmd == "submit":
            idx = int(parts[1]) if len(parts) > 1 else 0
            browser.submit(idx)
        elif re.match(r"^\d+$", cmd):
            # follow numbered link
            num = int(cmd)
            if browser.current_page:
                found = [(t,h) for n,t,h in browser.current_page.links if n == num]
                if found:
                    browser.load(found[0][1])
                else:
                    print(f"[!] link {num} not found")
        elif cmd.startswith("http"):
            browser.load(line)
        else:
            print(f"[?] unknown command: {cmd}")
            print("type 'help' for commands")


# ─── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bootstrap_qjs()

    args = sys.argv[1:]
    dump_mode = "--dump" in args
    if dump_mode:
        args.remove("--dump")

    start = args[0] if args else "https://example.com"

    browser = Browser()

    if dump_mode:
        html_src = browser.fetch(start)
        page     = parse_page(html_src)
        ctx      = {}
        try:
            ctx = browser.run_js(html_src, start)
        except Exception:
            pass
        browser._render(page, start, ctx)
    else:
        print("jsbrowser — curl + python + qjs terminal browser")
        print("type 'help' for commands")
        repl(browser, start)
