```python
#!/usr/bin/env python3
"""
jbrowser - A terminal-based browser with JavaScript execution support
Uses Node.js with jsdom for full DOM and V8 JavaScript engine support
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import random
import subprocess
import tempfile
import os
import urllib.parse
from urllib.parse import urljoin, urlparse, parse_qs


class Browser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'X-Same-Origin': 'true',
        })

        self.current_url = None
        self.current_html = None
        self.current_soup = None
        self.wiz_data = {}
        self.cookies = {}

        # Initialize with baseline cookies that Google expects
        self.session.cookies.set(
            'AEC',
            'AQTF6Hy9vZ8XqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJq......',
            domain='.google.com',
            path='/'
        )

        self.session.cookies.set(
            'SOCS',
            'CAESHQgDEikbChIIt9G8qgYQARoMCgxhY2NvdW50c19ob21lGgJlbiACGgQiCigJEAAYgICAgICAgIAKDAgBEAEYACABKAIwADgBQAFIAVAAWABgAGgAcAB4AIABAIgBAJABAJgBAKABAKgBALABALgBwAHIAcgByAHIAdAB0AHQAdgB4AHgAeAB6AHwAfgBAAEQAQ==',
            domain='.google.com',
            path='/'
        )

        self.session.cookies.set(
            '__Secure-BUCKET',
            'true',
            domain='.google.com',
            path='/'
        )

        self.session.cookies.set(
            'CONSENT',
            'YES+CB.de-DE-20240501-00-p0.en-DE-FXPX',
            domain='.google.com',
            path='/'
        )

    def fetch(self, url):
        """Fetch a URL and store the response"""
        print(f"[*] Fetching: {url}")

        try:
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()

            self.current_url = response.url
            self.current_html = response.text
            self.current_soup = BeautifulSoup(
                self.current_html,
                'html.parser'
            )

            # Update cookies
            self.cookies.update(self.session.cookies.get_dict())

            print(f"[+] Successfully fetched: {self.current_url}")
            return True

        except Exception as e:
            print(f"[-] Error fetching {url}: {e}")
            return False

    def execute_js(self, script):
        """Execute JavaScript using Node.js with jsdom for full V8 + DOM support"""

        if not self.current_html:
            print("[-] No HTML content to execute JavaScript on")
            return None

        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.html',
            delete=False
        ) as html_file:
            html_file.write(self.current_html)
            html_path = html_file.name

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.js',
            delete=False
        ) as js_file:
            js_file.write(script)
            js_path = js_file.name

        try:
            # Run Node.js with jsdom
            result = subprocess.run(
                ['node', '/workspace/run_jsdom.js', html_path, js_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(
                    f"[-] JavaScript execution error: {result.stderr}"
                )
                return None

            # Parse JSON output
            try:
                output = json.loads(result.stdout)
                return output

            except json.JSONDecodeError:
                print(
                    f"[-] Failed to parse JavaScript output: "
                    f"{result.stdout}"
                )
                return None

        except subprocess.TimeoutExpired:
            print("[-] JavaScript execution timed out")
            return None

        except Exception as e:
            print(f"[-] Error executing JavaScript: {e}")
            return None

        finally:
            # Cleanup temp files
            try:
                os.unlink(html_path)
                os.unlink(js_path)
            except Exception:
                pass

    def extract_wiz_data(self):
        """Extract Google WIZ global data structures using JavaScript"""

        script = """
const fs = require('fs');
const path = process.argv[2];
const html = fs.readFileSync(path, 'utf-8');

// Extract WIZ_global_data - try multiple patterns
let wizMatch = html.match(/window\\\\.WIZ_global_data\\\\s*=\\\\s*({[\\\\s\\\\S]*?});\\\\s*<\\\\/script>/);

if (!wizMatch) {
    wizMatch = html.match(/window\\\\._WIZ_global_data\\\\s*=\\\\s*({[\\\\s\\\\S]*?});/);
}

if (!wizMatch) {
    console.log(JSON.stringify({
        error: "No WIZ_global_data found",
        htmlSnippet: html.substring(0, 2000)
    }));

    process.exit(0);
}

try {
    let wizData = JSON.parse(wizMatch[1]);

    // Extract tokens
    const tokens = {};
    const tokenNames = [
        'SNlM0e',
        'TSDtV',
        'FdrFJe',
        'Qzxixc',
        'dsh',
        'TL',
        'GxKqAd',
        'k2rUvb',
        'bgfDDd'
    ];

    for (const name of tokenNames) {
        if (wizData[name]) {
            tokens[name] = wizData[name];
        }
    }

    console.log(JSON.stringify({
        tokens: tokens,
        rawKeys: Object.keys(wizData)
    }));

} catch (e) {
    console.log(JSON.stringify({error: e.message}));
}
"""

        result = self.execute_js(script)

        if result:
            self.wiz_data = result
            return result

        return {}

    def get_links(self):
        """Extract all links from the current page"""

        if not self.current_soup:
            return []

        links = []

        for a in self.current_soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a['href']

            links.append({
                'text': text,
                'href': href
            })

        return links

    def get_forms(self):
        """Extract form information including WIZ-driven forms"""

        if not self.current_soup:
            return []

        forms = []

        # Traditional forms
        for form in self.current_soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'GET').upper(),
                'inputs': []
            }

            for input_tag in form.find_all('input'):
                input_data = {
                    'name': input_tag.get('name'),
                    'type': input_tag.get('type', 'text'),
                    'value': input_tag.get('value', '')
                }

                form_data['inputs'].append(input_data)

            forms.append(form_data)

        return forms


def main():
    """Main entry point for testing"""

    browser = Browser()

    print("=== Testing Google Signup Flow ===\n")

    browser.fetch("https://accounts.google.com/signin")
    browser.render_page()


if __name__ == "__main__":
    main()
```
