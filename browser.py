#!/usr/bin/env python3
"""
jbrowser - A terminal-based browser with JavaScript execution support
Uses Node.js with jsdom for full DOM and V8 JavaScript engine support
"""

try:
    import requests
except ImportError:  # pragma: no cover - environment dependency check
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - environment dependency check
    BeautifulSoup = None
import re
import json
import random
import subprocess
import tempfile
import os
from urllib.parse import urljoin, urlparse, parse_qs, urlencode


class Browser:
    def __init__(self):
        if requests is None or BeautifulSoup is None:
            raise RuntimeError("Missing dependencies. Install them with: python3 -m pip install -r requirements.txt")
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
        self.session.cookies.set('AEC', 'AQTF6Hy9vZ8XqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJq......', domain='.google.com', path='/')
        self.session.cookies.set('SOCS', 'CAESHQgDEikbChIIt9G8qgYQARoMCgxhY2NvdW50c19ob21lGgJlbiACGgQiCigJEAAYgICAgICAgIAKDAgBEAEYACABKAIwADgBQAFIAVAAWABgAGgAcAB4AIABAIgBAJABAJgBAKABAKgBALABALgBwAHIAcgByAHIAdAB0AHQAdgB4AHgAeAB6AHwAfgBAAEQAQ==', domain='.google.com', path='/')
        self.session.cookies.set('__Secure-BUCKET', 'true', domain='.google.com', path='/')
        self.session.cookies.set('CONSENT', 'YES+CB.de-DE-20240501-00-p0.en-DE-FXPX', domain='.google.com', path='/')

    def fetch(self, url):
        """Fetch a URL and store the response"""
        print(f"[*] Fetching: {url}")
        try:
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()
            self.current_url = response.url
            self.current_html = response.text
            self.current_soup = BeautifulSoup(self.current_html, 'html.parser')

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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
            html_file.write(self.current_html)
            html_path = html_file.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as js_file:
            js_file.write(script)
            js_path = js_file.name

        try:
            # Run Node.js with jsdom
            env = os.environ.copy()
            if self.current_url:
                env['JSDOM_URL'] = self.current_url
            result = subprocess.run(
                ['node', os.path.join(os.path.dirname(__file__), 'run_jsdom.js'), html_path, js_path],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )

            if result.returncode != 0:
                print(f"[-] JavaScript execution error: {result.stderr}")
                return None

            # Parse JSON output
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError:
                print(f"[-] Failed to parse JavaScript output: {result.stdout}")
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
            except:
                pass

    def extract_wiz_data(self):
        """Extract Google WIZ global data and signup tokens from the current HTML."""
        html = self.current_html or ''
        tokens = {}
        actions = []

        def remember_token(name, value):
            if value and name not in tokens:
                tokens[name] = value

        scalar_patterns = {
            'SNlM0e': [r'"SNlM0e"\s*:\s*"([^"]+)"', r'\["SNlM0e","([^"]+)"'],
            'TL': [r'[?&]TL=([^&"\']+)', r'"TL"\s*:\s*"([^"]+)"'],
            'dsh': [r'[?&]dsh=([^&"\']+)', r'"dsh"\s*:\s*"([^"]+)"'],
            'FdrFJe': [r'"FdrFJe"\s*:\s*"?(-?\d+)"?'],
        }
        for name, patterns in scalar_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    remember_token(name, match.group(1))
                    break

        bl_match = re.search(r'boq_identity-account-creation-evolution-ui_[A-Za-z0-9_.-]+', html)
        if bl_match:
            remember_token('bl', bl_match.group(0))
        if tokens.get('FdrFJe'):
            remember_token('f.sid', tokens['FdrFJe'])

        for match in re.finditer(r'"(/(?:lifecycle|signup)[^"\\]*)"', html):
            actions.append(match.group(1))
        for match in re.finditer(r'https://accounts\.google\.com/[^"\'<> ]+', html):
            if '/lifecycle/' in match.group(0) or '/signup' in match.group(0):
                actions.append(match.group(0))

        if self.current_url:
            params = parse_qs(urlparse(self.current_url).query)
            for key in ('TL', 'dsh', 'hl'):
                if key in params:
                    remember_token(key, params[key][0])

        result = {
            'tokens': tokens,
            'actions': sorted(set(actions)),
            'fields': [],
            'rawKeys': [],
        }
        self.wiz_data = result
        return result

    def get_links(self):
        """Extract all links from the current page"""
        if not self.current_soup:
            return []

        links = []
        for a in self.current_soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a['href']
            links.append({'text': text, 'href': href})
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

        # WIZ-driven forms (no explicit form tags) - detect from both WIZ data AND raw HTML
        has_wiz_form = False
        wiz_form = None

        # Try WIZ data first
        if self.wiz_data.get('fields'):
            has_wiz_form = True
            wiz_form = {
                'action': self.wiz_data.get('actions', [''])[0] if self.wiz_data.get('actions') else '',
                'method': 'POST',
                'inputs': [],
                'wiz_driven': True,
                'tokens': self.wiz_data.get('tokens', {})
            }

            # Detect common field patterns
            input_names = ['firstName', 'lastName', 'username', 'password', 'email']
            for name in input_names:
                wiz_form['inputs'].append({
                    'name': name,
                    'type': 'text',
                    'value': ''
                })

        # ALSO check for visible inputs in HTML even if WIZ parsing failed
        # This handles cases where JS execution fails but inputs are still in HTML
        visible_inputs = self.current_soup.find_all('input', {'id': lambda x: x and x in ['firstName', 'lastName', 'username', 'password', 'email']})

        if visible_inputs and not has_wiz_form:
            has_wiz_form = True
            wiz_form = {
                'action': '',
                'method': 'POST',
                'inputs': [],
                'wiz_driven': True,
                'tokens': self.wiz_data.get('tokens', {})
            }

            # Add detected inputs
            for inp in visible_inputs:
                inp_id = inp.get('id')
                if inp_id:
                    wiz_form['inputs'].append({
                        'name': inp_id,  # Use ID as name for WIZ forms
                        'type': inp.get('type', 'text'),
                        'value': inp.get('value', '')
                    })

        if has_wiz_form and wiz_form:
            forms.append(wiz_form)

        return forms

    def fill_form(self, form_index, data):
        """Fill form fields with provided data"""
        forms = self.get_forms()
        if form_index >= len(forms):
            print(f"[-] Form index {form_index} out of range")
            return False

        form = forms[form_index]
        print(f"[*] Filling form with data: {data}")

        # For WIZ-driven forms, we need to submit via JavaScript
        if form.get('wiz_driven'):
            # Store form data for submission
            self.pending_form_data = data
            self.pending_form = form
            return True

        # For traditional forms, update the soup
        for input_name, value in data.items():
            input_tag = self.current_soup.find('input', {'name': input_name})
            if input_tag:
                input_tag['value'] = value

        return True

    def submit_wiz_rpc(self, field_mapping=None):
        """Submit a JavaScript-driven form by letting page code build the request.

        This is intentionally a browser primitive rather than a Google-signup
        protocol table. The current DOM is loaded in jsdom, form controls are
        populated with pending values, and the likely submit/next control is
        clicked. If page JavaScript issues fetch/XHR, the Python session replays
        that captured request with its cookies and headers.
        """
        print("  [RPC] Running DOM-driven JavaScript submission...")
        pending = getattr(self, 'pending_form_data', {}) or {}
        return self.submit_js_interactive_form(pending, submit_text=field_mapping)

    def _build_interaction_script(self, form_data, submit_text=None):
        """Build a jsdom-side script that fills fields and activates submit."""
        payload = json.dumps(form_data)
        desired_text = json.dumps(submit_text or '')
        return f'''
        const data = {payload};
        const desiredText = {desired_text}.toLowerCase();
        const changed = [];
        function labelFor(el) {{
          const labels = [];
          if (el.id) {{
            const explicit = document.querySelector(`label[for="${{CSS.escape(el.id)}}"]`);
            if (explicit) labels.push(explicit.textContent || '');
          }}
          const parent = el.closest('label');
          if (parent) labels.push(parent.textContent || '');
          labels.push(el.getAttribute('aria-label') || '');
          labels.push(el.getAttribute('placeholder') || '');
          labels.push(el.getAttribute('autocomplete') || '');
          labels.push(el.name || el.id || '');
          return labels.join(' ');
        }}
        function semanticValue(el) {{
          const name = (el.name || el.id || '').toLowerCase();
          const text = labelFor(el).toLowerCase();
          const haystack = `${{name}} ${{text}}`.replace(/[-_]/g, '');
          for (const [key, value] of Object.entries(data)) {{
            if (haystack.includes(key.toLowerCase().replace(/[-_]/g, ''))) return value;
          }}
          const aliases = [
            [['first','given'], 'firstName'], [['last','family','surname'], 'lastName'],
            [['user','email'], 'username'], [['pass'], 'password'],
            [['phone','mobile','tel'], 'phoneNumber'], [['day'], 'day'],
            [['month'], 'month'], [['year'], 'year'], [['gender'], 'gender'],
            [['confirm'], 'confirm']
          ];
          for (const [needles, key] of aliases) {{
            if (needles.some((needle) => haystack.includes(needle)) && data[key] !== undefined) return data[key];
          }}
          return undefined;
        }}
        function fire(el) {{
          for (const type of ['input', 'change', 'blur']) {{
            el.dispatchEvent(new window.Event(type, {{ bubbles: true }}));
          }}
        }}
        for (const el of Array.from(document.querySelectorAll('input, textarea, select'))) {{
          if (el.disabled || el.type === 'hidden' || el.type === 'submit' || el.type === 'button') continue;
          const value = semanticValue(el);
          if (value === undefined || value === null) continue;
          if (el.tagName === 'SELECT') {{
            const wanted = String(value).toLowerCase();
            const option = Array.from(el.options).find((opt) =>
              opt.value.toLowerCase() === wanted || opt.textContent.trim().toLowerCase() === wanted);
            if (option) el.value = option.value;
          }} else if (el.type === 'checkbox' || el.type === 'radio') {{
            el.checked = Boolean(value) && (String(value).toLowerCase() !== 'false');
          }} else {{
            el.value = String(value);
          }}
          changed.push(el.name || el.id || labelFor(el));
          fire(el);
        }}
        const controls = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"], [role="button"]'));
        const submit = controls.find((el) => desiredText && (el.textContent || el.value || '').toLowerCase().includes(desiredText)) ||
          controls.find((el) => /^(next|continue|submit|create|i agree|yes|verify)$/i.test((el.textContent || el.value || '').trim())) ||
          controls[controls.length - 1];
        if (submit) submit.click();
        result.changed = changed;
        result.clicked = submit ? (submit.textContent || submit.value || submit.getAttribute('aria-label') || '').trim() : null;
        result.location = window.location.href;
        '''

    def _absolute_request_url(self, url):
        return urljoin(self.current_url or 'https://accounts.google.com/', url)

    def _replay_js_request(self, request_info):
        """Replay a fetch/XHR captured from jsdom using the Python session."""
        method = (request_info.get('method') or 'GET').upper()
        url = self._absolute_request_url(request_info.get('url') or self.current_url or '')
        headers = request_info.get('headers') or {}
        body = request_info.get('body')
        print(f"[*] Replaying JS {method} request to {url}")
        response = self.session.request(method, url, data=body, headers=headers, allow_redirects=True)
        self.last_response = response
        self.current_url = response.url
        self.current_html = response.text
        self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
        return response.status_code < 400

    def submit_js_interactive_form(self, form_data=None, submit_text=None):
        """Fill and submit the current DOM with JavaScript, replaying captured I/O."""
        form_data = form_data or {}
        result = self.execute_js(self._build_interaction_script(form_data, submit_text=submit_text))
        if not result:
            print("[-] JavaScript interaction failed")
            return False
        for request_info in result.get('networkLog', []):
            if request_info.get('url'):
                return self._replay_js_request(request_info)
        html = result.get('html')
        if html and html != self.current_html:
            self.current_html = html
            self.current_soup = BeautifulSoup(html, 'html.parser')
            self.current_url = result.get('result', {}).get('location') or self.current_url
            return True
        print("[-] Page JavaScript did not produce a network request or DOM transition")
        return False

    def submit_form(self, form_index=None):
        """Smart submit: tries WIZ RPC first for Google forms, then standard HTML form."""
        forms = self.get_forms()

        if form_index is None:
            form_index = 0

        if form_index >= len(forms):
            print(f"[-] Form index {form_index} out of range")
            return False

        form = forms[form_index]

        # Check if this looks like a WIZ form
        has_wiz_tokens = bool(self.wiz_data.get('tokens', {}).get('SNlM0e'))
        is_wiz_driven = form.get('wiz_driven', False)

        # Also check for jsaction on buttons
        has_jsaction = False
        if self.current_soup:
            buttons = self.current_soup.find_all('button')
            has_jsaction = any(btn.get('jsaction') for btn in buttons)

        # If we have WIZ tokens OR it's explicitly WIZ-driven, use RPC handler
        if (has_wiz_tokens or is_wiz_driven) and (has_jsaction or is_wiz_driven or not form.get('action')):
            print("[*] Detected WIZ-driven form, using generic RPC handler...")
            return self.submit_wiz_rpc()

        # Traditional form submission
        action = form.get('action', '')
        if not action.startswith('http'):
            action = urljoin(self.current_url, action) if self.current_url else action

        method = form.get('method', 'POST')

        # Collect form data
        form_data = {}
        for input_field in form.get('inputs', []):
            name = input_field.get('name')
            value = input_field.get('value', '')
            if name:
                form_data[name] = value

        # Add any pending form data
        if hasattr(self, 'pending_form_data'):
            form_data.update(self.pending_form_data)

        print(f"[*] Submitting traditional form to {action} with method {method}")
        print(f"[*] Form data: {form_data}")

        try:
            if method.upper() == 'POST':
                response = self.session.post(action, data=form_data, allow_redirects=True)
            else:
                response = self.session.get(action, params=form_data, allow_redirects=True)

            response.raise_for_status()
            self.current_url = response.url
            self.current_html = response.text
            self.current_soup = BeautifulSoup(self.current_html, 'html.parser')

            print(f"[+] Form submitted successfully, now at: {self.current_url}")
            return True

        except Exception as e:
            print(f"[-] Form submission failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[-] Response status: {e.response.status_code}")
            return False

    def click_link(self, text_or_index):
        """Click a link by text or index"""
        links = self.get_links()

        target_link = None
        if isinstance(text_or_index, int):
            if text_or_index < len(links):
                target_link = links[text_or_index]
        else:
            for link in links:
                if text_or_index.lower() in link['text'].lower():
                    target_link = link
                    break

        if not target_link:
            print(f"[-] Link not found: {text_or_index}")
            return False

        href = target_link['href']
        if not href.startswith('http'):
            href = urljoin(self.current_url, href)

        print(f"[*] Clicking link: {target_link['text']} -> {href}")
        return self.fetch(href)

    def click_button(self, text_or_index):
        """Click a button by text or index"""
        if not self.current_soup:
            return False

        buttons = self.current_soup.find_all('button')
        inputs = self.current_soup.find_all('input', {'type': 'submit'})
        all_buttons = buttons + inputs

        target_button = None
        if isinstance(text_or_index, int):
            if text_or_index < len(all_buttons):
                target_button = all_buttons[text_or_index]
        else:
            for button in all_buttons:
                btn_text = button.get_text(strip=True) or button.get('value', '')
                if text_or_index.lower() in btn_text.lower():
                    target_button = button
                    break

        if not target_button:
            print(f"[-] Button not found: {text_or_index}")
            # Try to find by jsaction attribute (Google's way)
            for elem in self.current_soup.find_all(attrs={'jsaction': True}):
                jsaction = elem.get('jsaction', '')
                if 'click' in jsaction.lower():
                    print(f"[*] Found element with jsaction: {jsaction}")
                    # Try to extract URL from onclick or data attributes
                    return self.handle_js_action(elem)

            # Check for span inside button with the text (Google's pattern)
            for button in buttons:
                spans = button.find_all('span')
                for span in spans:
                    span_text = span.get_text(strip=True)
                    if text_or_index.lower() in span_text.lower():
                        target_button = button
                        print(f"[*] Found button via span: {span_text}")
                        break
                if target_button:
                    break

        if not target_button:
            return False

        # Check if button has a form action
        form = target_button.find_parent('form')
        if form:
            action = form.get('action', '')
            if action:
                if not action.startswith('http'):
                    action = urljoin(self.current_url, action)
                return self.fetch(action)

        # Check for jsaction attribute
        jsaction = target_button.get('jsaction', '')
        if jsaction:
            return self.handle_js_action(target_button)

        # For Google signup button, construct the URL manually
        if 'Create account' in target_button.get_text():
            # Extract dsh from current URL
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(self.current_url)
            params = parse_qs(parsed.query)
            dsh = params.get('dsh', [''])[0]

            # Construct signup URL (correct endpoint is /signup not /signup/v2/webname)
            signup_url = f"https://accounts.google.com/signup?dsh={dsh}&flowEntry=SignUp&flowName=GlifWebSignIn"
            print(f"[*] Navigating to signup URL: {signup_url}")
            return self.fetch(signup_url)

        print(f"[-] Button has no actionable URL")
        return False

    def handle_js_action(self, elem):
        """Handle Google's jsaction attribute"""
        jsaction = elem.get('jsaction', '')
        print(f"[*] Processing jsaction: {jsaction}")

        # For Create Account button, construct the signup URL directly
        elem_text = elem.get_text(strip=True)
        if 'Create account' in elem_text:
            # Extract dsh from current URL
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(self.current_url)
            params = parse_qs(parsed.query)
            dsh = params.get('dsh', [''])[0]

            # Construct signup URL (correct endpoint is /signup not /signup/v2/webname)
            signup_url = f"https://accounts.google.com/signup?dsh={dsh}&flowEntry=SignUp&flowName=GlifWebSignIn"
            print(f"[*] Navigating to signup URL: {signup_url}")
            return self.fetch(signup_url)

        # Extract WIZ data to find the action URL for other jsaction elements
        wiz_data = self.extract_wiz_data()

        if wiz_data.get('actions'):
            action_url = wiz_data['actions'][0]
            if not action_url.startswith('http'):
                action_url = 'https://accounts.google.com' + action_url

            # Add required parameters
            tokens = wiz_data.get('tokens', {})
            params = {}
            if 'dsh' in tokens:
                params['dsh'] = tokens['dsh']
            params['flowEntry'] = 'SignUp'
            params['flowName'] = 'GlifWebSignIn'

            full_url = action_url
            if params:
                from urllib.parse import urlencode
                separator = '&' if '?' in action_url else '?'
                full_url += separator + urlencode(params)

            print(f"[*] Navigating to WIZ action URL: {full_url}")
            return self.fetch(full_url)

        print("[-] Could not determine action from jsaction")
        return False

    def classify_signup_step(self):
        """Classify the visible signup step from URL, inputs, labels, and text."""
        html = (self.current_html or '').lower()
        url = (self.current_url or '').lower()
        text = self.current_soup.get_text(' ', strip=True).lower() if self.current_soup else html
        fields = ' '.join(
            ' '.join(filter(None, [inp.get('name'), inp.get('id'), inp.get('type'), inp.get('autocomplete'), inp.get('aria-label'), inp.get('placeholder')]))
            for inp in (self.current_soup.find_all(['input', 'select', 'textarea']) if self.current_soup else [])
        ).lower()
        haystack = f"{url} {text} {fields}"
        if any(token in haystack for token in ('5 gb', '5gb', 'storage', 'add phone later', 'skip')):
            return 'phone_optional'
        if any(token in haystack for token in ('verify your phone', 'phone number', 'mobile number', 'sms', 'text message')):
            return 'phone'
        if any(token in haystack for token in ('birthday', 'birth day', 'gender', 'month', 'year')):
            return 'birthdaygender'
        if any(token in haystack for token in ('choose your gmail', 'username', 'create a gmail', 'email address')):
            return 'username'
        if any(token in haystack for token in ('password', 'confirm')):
            return 'password'
        if any(token in haystack for token in ('first name', 'last name', 'given name', 'family name')):
            return 'name'
        if any(token in haystack for token in ('privacy and terms', 'i agree')):
            return 'terms'
        return 'unknown'

    def default_signup_data(self):
        """Generate non-secret test values for signup automation."""
        suffix = str(random.randrange(100000, 999999))
        return {
            'firstName': 'Test',
            'lastName': f'Browser{suffix}',
            'day': '1',
            'month': 'January',
            'year': '1990',
            'gender': 'Rather not say',
            'username': f'testbrowser{suffix}',
            'password': f'TestBrowser!{suffix}',
            'phoneNumber': f'+1555{random.randrange(1000000, 9999999)}',
        }

    def fill_current_signup_step(self, data=None):
        """Fill fields appropriate for the currently visible signup step."""
        all_data = self.default_signup_data()
        if data:
            all_data.update(data)
        step = self.classify_signup_step()
        if step == 'name':
            fields = {key: all_data[key] for key in ('firstName', 'lastName')}
        elif step == 'birthdaygender':
            fields = {key: all_data[key] for key in ('day', 'month', 'year', 'gender')}
        elif step == 'username':
            fields = {'username': all_data['username']}
        elif step == 'password':
            fields = {'password': all_data['password'], 'confirm': all_data['password']}
        elif step in ('phone', 'phone_optional'):
            fields = {'phoneNumber': all_data['phoneNumber']}
        elif step == 'terms':
            fields = {}
        else:
            return step, False
        self.pending_form_data = fields
        return step, True

    def drive_signup_until_blocked(self, max_steps=12, data=None):
        """Drive completable signup pages until a verification/blocking step remains.

        If a locale or experiment skips phone collection it keeps going; if phone
        is required, it submits one random test number and reports the expected
        verification block instead of pretending that an SMS challenge can be
        completed.
        """
        history = []
        submitted_phone = False
        for _ in range(max_steps):
            step, can_fill = self.fill_current_signup_step(data)
            history.append(step)
            if step == 'unknown' or not can_fill:
                return {'status': 'blocked', 'reason': 'unknown_step', 'history': history, 'url': self.current_url}
            ok = self.submit_js_interactive_form(getattr(self, 'pending_form_data', {}), submit_text='next')
            if not ok:
                reason = 'phone_verification' if step in ('phone', 'phone_optional') else 'submission_failed'
                return {'status': 'blocked', 'reason': reason, 'history': history, 'url': self.current_url}
            new_step = self.classify_signup_step()
            if step in ('phone', 'phone_optional'):
                if submitted_phone or new_step in ('phone', 'phone_optional'):
                    return {'status': 'blocked', 'reason': 'phone_verification', 'history': history + [new_step], 'url': self.current_url}
                submitted_phone = True
        return {'status': 'blocked', 'reason': 'max_steps', 'history': history, 'url': self.current_url}

    def render_page(self):
        """Render the current page content"""
        if not self.current_soup:
            print("[-] No page loaded")
            return

        print("\n" + "=" * 60)
        print(f"Current URL: {self.current_url}")
        print("=" * 60)

        # Show title
        title = self.current_soup.find('title')
        if title:
            print(f"\nTitle: {title.get_text(strip=True)}")

        # Show forms
        forms = self.get_forms()
        if forms:
            print(f"\nForms found: {len(forms)}")
            for i, form in enumerate(forms):
                print(f"\n  Form {i}:")
                print(f"    Action: {form.get('action', 'N/A')}")
                print(f"    Method: {form.get('method', 'N/A')}")
                print(f"    WIZ-driven: {form.get('wiz_driven', False)}")
                if form.get('inputs'):
                    print(f"    Inputs:")
                    for inp in form['inputs']:
                        print(f"      - {inp.get('name')} ({inp.get('type')})")

        # Show links
        links = self.get_links()
        if links:
            print(f"\nLinks found: {len(links)}")
            for i, link in enumerate(links[:10]):  # Show first 10
                print(f"  [{i}] {link['text'][:50]} -> {link['href'][:60]}")
            if len(links) > 10:
                print(f"  ... and {len(links) - 10} more")

        print("=" * 60 + "\n")


def main():
    """Main entry point for exploratory live testing."""
    browser = Browser()

    print("=== Testing Google Signup Browser Flow ===\n")

    if not browser.fetch("https://accounts.google.com/signin"):
        return
    browser.render_page()

    if browser.click_button("Create account"):
        browser.render_page()

    result = browser.drive_signup_until_blocked()
    browser.render_page()
    print("\n=== Signup driver result ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
