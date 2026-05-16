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
            result = subprocess.run(
                ['node', os.path.join(os.path.dirname(__file__), 'run_jsdom.js'), html_path, js_path],
                capture_output=True,
                text=True,
                timeout=30
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
        """Submit the current Google WIZ step via HAR-derived batchexecute RPCs.

        Older versions of this prototype tried to invent ``userspace.*`` RPC
        names from DOM text. The signup HAR checked into this repo shows that
        the name step uses the compact RPC id ``E815hb`` and the exact inner
        payload ``[firstName,lastName,null,null,null,[],null,1]``. Route known
        signup steps through the dedicated helpers and leave unknown steps as a
        clear failure instead of posting malformed data.
        """
        print("  [RPC] Detecting WIZ RPC submission...")
        pending = getattr(self, 'pending_form_data', {}) or {}
        current_url = self.current_url or ''
        requested = field_mapping if isinstance(field_mapping, str) else ''

        if '/lifecycle/steps/signup/name' in current_url or 'NameSubmit' in requested:
            first_name = pending.get('firstName') or pending.get('first_name') or pending.get('givenName') or ''
            last_name = pending.get('lastName') or pending.get('last_name') or pending.get('familyName') or ''
            if not first_name and self.current_soup:
                first = self.current_soup.find('input', attrs={'name': re.compile('first|given', re.I)})
                first_name = first.get('value', '') if first else ''
            if not last_name and self.current_soup:
                last = self.current_soup.find('input', attrs={'name': re.compile('last|family', re.I)})
                last_name = last.get('value', '') if last else ''
            if not first_name:
                print("  [RPC] Cannot submit name step without a first name.")
                return False
            return self.submit_name_form(first_name, last_name)

        print(f"  [RPC] No HAR-backed submitter for current URL: {current_url}")
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

    def _extract_signup_tokens(self):
        """Collect Google signup RPC tokens from WIZ data, URL params, and HTML."""
        tokens = dict(self.wiz_data.get('tokens', {}) if isinstance(self.wiz_data, dict) else {})
        parsed_url = urlparse(self.current_url or '')
        url_params = parse_qs(parsed_url.query)

        for key in ('TL', 'dsh', 'hl'):
            if key in url_params and not tokens.get(key):
                tokens[key] = url_params[key][0]

        html = self.current_html or ''
        patterns = {
            'SNlM0e': [r'"SNlM0e"\s*:\s*"([^"]+)"', r'\["SNlM0e","([^"]+)"\]', r'\bat=([^&"\']+)'],
            'f.sid': [r'"FdrFJe"\s*:\s*"?(-?\d+)"?', r'"f\.sid"\s*:\s*"?(-?\d+)"?'],
            'bl': [r'boq_identity-account-creation-evolution-ui_[A-Za-z0-9_.-]+'],
        }
        for key, candidates in patterns.items():
            if tokens.get(key):
                continue
            for pattern in candidates:
                match = re.search(pattern, html)
                if match:
                    tokens[key] = match.group(1) if match.groups() else match.group(0)
                    break

        if not tokens.get('f.sid'):
            tokens['f.sid'] = str(random.randint(1000000000000000000, 9999999999999999999))
        if not tokens.get('bl'):
            tokens['bl'] = 'boq_identity-account-creation-evolution-ui_20260512.06_p0'
        if not tokens.get('hl'):
            tokens['hl'] = 'en-US'
        return tokens, parsed_url, url_params

    def _parse_batchexecute_response(self, text):
        """Parse Google's )]}' length-prefixed batchexecute response."""
        if text.startswith(")]}'"):
            text = text[4:]
        lines = text.strip().split('\n')
        parsed_items = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.isdigit():
                length = int(line)
                i += 1
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    try:
                        parsed_items.extend(json.loads(lines[i]))
                        i += 1
                        continue
                    except json.JSONDecodeError:
                        pass
                json_str = ''
                while i < len(lines) and len(json_str) < length:
                    if json_str:
                        json_str += '\n'
                    json_str += lines[i]
                    i += 1
                try:
                    parsed_items.extend(json.loads(json_str))
                except json.JSONDecodeError:
                    pass
                continue
            try:
                parsed = json.loads(line)
                if isinstance(parsed, list):
                    parsed_items.extend(parsed if parsed and isinstance(parsed[0], list) else [parsed])
            except json.JSONDecodeError:
                pass
            i += 1
        return parsed_items

    def _find_lifecycle_step(self, value):
        """Return the first steps/signup/... path found in nested JSON-ish data."""
        if isinstance(value, str):
            if value.startswith('steps/signup/'):
                return value
            try:
                return self._find_lifecycle_step(json.loads(value))
            except (json.JSONDecodeError, TypeError):
                match = re.search(r'steps/signup/[A-Za-z0-9_-]+', value)
                return match.group(0) if match else None
        if isinstance(value, list):
            for item in value:
                found = self._find_lifecycle_step(item)
                if found:
                    return found
        if isinstance(value, dict):
            for item in value.values():
                found = self._find_lifecycle_step(item)
                if found:
                    return found
        return None

    def submit_wiz_batchexecute(self, rpcid, inner_data_array, source_path):
        """Submit a Google WIZ batchexecute RPC using the HAR-observed format."""
        tokens, parsed_url, url_params = self._extract_signup_tokens()
        tl = tokens.get('TL')
        at = tokens.get('SNlM0e')
        dsh = tokens.get('dsh') or url_params.get('dsh', [None])[0]

        if not tl:
            print("ERROR: Missing TL token; fetch the signup step before submitting.")
            return None
        if not at:
            print("ERROR: Missing SNlM0e/at token; Google will reject batchexecute without it.")
            return None

        inner_json_str = json.dumps(inner_data_array, separators=(',', ':'))
        f_req_data = [[[rpcid, inner_json_str, None, "generic"]]]
        post_data = {
            'f.req': json.dumps(f_req_data, separators=(',', ':')),
            'at': at,
            '': '',
        }

        query = {
            'rpcids': rpcid,
            'source-path': source_path,
            'f.sid': tokens['f.sid'],
            'bl': tokens['bl'],
            'hl': tokens['hl'],
            'TL': tl,
            '_reqid': str(random.randrange(100000, 999999)),
            'rt': 'c',
        }
        endpoint = 'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute'
        full_url = f"{endpoint}?{urlencode(query)}"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Origin': 'https://accounts.google.com',
            'Referer': self.current_url or f'https://accounts.google.com{source_path}',
            'X-Same-Domain': '1',
            'X-Same-Origin': '1',
        }

        print("\n=== SUBMITTING BATCHEXECUTE RPC ===")
        print(f"RPC: {rpcid}")
        print(f"URL: {full_url}")
        print(f"f.req: {post_data['f.req'][:200]}...")

        try:
            response = self.session.post(full_url, data=post_data, headers=headers)
        except Exception as e:
            print(f"Request failed: {e}")
            return None

        self.last_response = response
        parsed_items = self._parse_batchexecute_response(response.text)
        print(f"Status: {response.status_code}; parsed {len(parsed_items)} batchexecute item(s)")

        next_step = self._find_lifecycle_step(parsed_items) or self._find_lifecycle_step(response.text)
        if next_step:
            next_url = f"https://accounts.google.com/lifecycle/{next_step}"
            preserved = {key: values[0] for key, values in url_params.items() if values}
            if dsh and 'dsh' not in preserved:
                preserved['dsh'] = dsh
            if tl and 'TL' not in preserved:
                preserved['TL'] = tl
            if preserved:
                next_url += '?' + urlencode(preserved)
            print(f"✓ SUCCESS: Next page detected: {next_url}")
            self.pending_form_data = {}
            return self.fetch(next_url)

        self.current_html = response.text
        self.current_soup = BeautifulSoup(response.text, 'html.parser')
        return response

    def submit_name_form(self, first_name, last_name):
        """
        Submit the name form using the batchexecute protocol.
        Based on HAR analysis, use RPC ID 'E815hb' with flat array format:
        [firstName, lastName, null, null, null, [], null, 1]
        """
        # Construct the inner data array - FLAT structure as per HAR
        inner_data = [
            first_name,   # Index 0: firstName
            last_name,    # Index 1: lastName
            None,         # Index 2: middleName
            None,         # Index 3: fullName
            None,         # Index 4: prefix
            [],           # Index 5: empty array (NOT null!)
            None,         # Index 6: unknown
            1             # Index 7: flag
        ]

        return self.submit_wiz_batchexecute(
            rpcid='E815hb',
            inner_data_array=inner_data,
            source_path='/lifecycle/steps/signup/name'
        )

    def submit_wiz_form(self, form):
        """Submit a WIZ-driven form using JavaScript"""
        print("[*] Submitting WIZ-driven form...")

        # Get form data
        form_data = getattr(self, 'pending_form_data', {})
        tokens = form.get('tokens', {})

        # Build JavaScript for form submission
        script = '''
        const fs = require('fs');
        const path = process.argv[2];
        const html = fs.readFileSync(path, 'utf-8');

        // Extract the actual submission endpoint from WIZ data
        const wizMatch = html.match(/window\\._WIZ_global_data\\s*=\\s*({[\\s\\S]*?});/);

        let submitUrl = "''' + self.current_url + '''";
        let additionalParams = {};

        if (wizMatch) {
            try {
                const wizData = JSON.parse(wizMatch[1]);

                // Look for nextPageUrl or action URLs
                if (wizData.nextPageUrl) {
                    submitUrl = wizData.nextPageUrl;
                }

                // Search for RPC endpoints
                function findRpcEndpoints(obj) {
                    if (Array.isArray(obj)) {
                        for (let item of obj) {
                            if (typeof item === 'string' && item.includes('/signup/') && item.includes('/webname')) {
                                submitUrl = 'https://accounts.google.com' + item;
                            }
                            findRpcEndpoints(item);
                        }
                    }
                }
                findRpcEndpoints(wizData);

                // Extract additional required parameters
                if (wizData.TL) additionalParams.TL = wizData.TL;
                if (wizData.dsh) additionalParams.dsh = wizData.dsh;
            } catch (e) {
                console.error("Error parsing WIZ data:", e);
            }
        }

        // Prepare the payload
        const payload = {
            url: submitUrl,
            params: additionalParams,
            formData: ''' + json.dumps(form_data) + ''',
            tokens: ''' + json.dumps(tokens) + '''
        };

        console.log(JSON.stringify(payload));
        '''

        result = self.execute_js(script)
        if not result:
            print("[-] Failed to prepare WIZ form submission")
            return False

        submit_url = result.get('url', self.current_url)
        additional_params = result.get('params', {})
        form_payload = result.get('formData', {})
        tokens = result.get('tokens', {})

        # Merge all parameters
        form_payload.update(additional_params)
        form_payload.update(tokens)

        print(f"[*] Submitting to: {submit_url}")
        print(f"[*] Payload: {form_payload}")

        try:
            # Try different content types that Google might expect
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Same-Origin': '1',
            }

            response = self.session.post(
                submit_url,
                data=form_payload,
                headers=headers,
                allow_redirects=True
            )

            # Check if we got redirected to the next page
            if response.status_code in [200, 302, 303]:
                self.current_url = response.url
                self.current_html = response.text
                self.current_soup = BeautifulSoup(self.current_html, 'html.parser')

                print(f"[+] Submission successful, now at: {self.current_url}")

                # Check if we reached the username page (page 3)
                if 'username' in self.current_html.lower() or 'choose your username' in self.current_html.lower():
                    print("[+] SUCCESS: Reached username selection page (Page 3)!")

                return True
            else:
                print(f"[-] Unexpected status code: {response.status_code}")
                print(f"[-] Response: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"[-] WIZ form submission failed: {e}")
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
    """Main entry point for testing"""
    browser = Browser()

    # Test Google signup flow
    print("=== Testing Google Signup Flow ===\n")

    # Step 1: Go to sign-in page
    browser.fetch("https://accounts.google.com/signin")
    browser.render_page()

    # Step 2: Click "Create account"
    if browser.click_button("Create account"):
        browser.render_page()

    # Step 3: Fill in name and submit using HAR-matched RPC
    if browser.fill_form(0, {'firstName': 'steve', 'lastName': 'boils'}):
        print("[*] Submitting name form via HAR-matched RPC...")
        response = browser.submit_name_form('steve', 'boils')
        if response:
            browser.render_page()
            if 'username' in browser.current_url.lower() or 'name' not in browser.current_url.lower():
                print("\n✓ SUCCESS: Moved past name page!")
                print(f"Current URL: {browser.current_url}")
            else:
                print("\n✗ Still on name page")
                print(f"Current URL: {browser.current_url}")
        else:
            print("[!] submit_name_form returned None/False")
            if browser.fill_form(0, {'firstName': 'steve', 'lastName': 'boils'}):
                if browser.submit_form(0):
                    browser.render_page()

    # Check if we reached page 3 (username selection)
    if 'username' in browser.current_html.lower():
        print("\n✓ SUCCESS: Reached username selection page!")
    else:
        print("\n✗ Did not reach username page yet")


if __name__ == "__main__":
    main()
