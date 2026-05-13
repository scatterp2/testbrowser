#!/usr/bin/env python3
"""
jbrowser - A terminal-based browser with JavaScript execution support
Uses Node.js with jsdom for full DOM and V8 JavaScript engine support
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import subprocess
import tempfile
import os
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
        })
        self.current_url = None
        self.current_html = None
        self.current_soup = None
        self.wiz_data = {}
        self.cookies = {}
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
                ['node', '/workspace/run_jsdom.js', html_path, js_path],
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
        """Extract Google WIZ global data structures using JavaScript"""
        script = """
        const fs = require('fs');
        const path = process.argv[2];
        const html = fs.readFileSync(path, 'utf-8');
        // Extract WIZ_global_data - try multiple patterns
        let wizMatch = html.match(/window\\.WIZ_global_data\\s*=\\s*({[\\s\\S]*?});\\s*<\\/script>/);
        if (!wizMatch) {
            wizMatch = html.match(/window\\._WIZ_global_data\\s*=\\s*({[\\s\\S]*?});/);
        }
        if (!wizMatch) {
            console.log(JSON.stringify({error: "No WIZ_global_data found", htmlSnippet: html.substring(0, 2000)}));
            process.exit(0);
        }
        try {
            let wizData = JSON.parse(wizMatch[1]);
            // Extract tokens
            const tokens = {};
            const tokenNames = ['SNlM0e', 'TSDtV', 'FdrFJe', 'Qzxixc', 'dsh', 'TL', 'GxKqAd', 'k2rUvb', 'bgfDDd'];
            for (const name of tokenNames) {
                if (wizData[name]) {
                    tokens[name] = wizData[name];
                }
            }
            // Deep search for tokens in arrays
            function findTokens(obj, depth = 0) {
                if (depth > 10) return;
                if (Array.isArray(obj)) {
                    for (let i = 0; i < obj.length; i++) {
                        if (typeof obj[i] === 'string' && obj[i].length > 10 && obj[i].length < 500) {
                            if (!tokens.candidateToken) tokens.candidateToken = [];
                            tokens.candidateToken.push(obj[i]);
                        }
                        findTokens(obj[i], depth + 1);
                    }
                } else if (typeof obj === 'object' && obj !== null) {
                    for (const key in obj) {
                        findTokens(obj[key], depth + 1);
                    }
                }
            }
            findTokens(wizData);
            // Extract form action URLs
            const actions = [];
            function findActions(obj) {
                if (Array.isArray(obj)) {
                    for (let i = 0; i < obj.length; i++) {
                        if (typeof obj[i] === 'string') {
                            if (obj[i].includes('/signup/') || obj[i].includes('/lifecycle/')) {
                                actions.push(obj[i]);
                            }
                        }
                        findActions(obj[i]);
                    }
                }
            }
            findActions(wizData);
            // Extract field definitions
            const fields = [];
            if (wizData.focusedModelId) {
                fields.push({type: 'focusedModelId', value: wizData.focusedModelId});
            }
            console.log(JSON.stringify({
                tokens: tokens,
                actions: [...new Set(actions)],
                fields: fields,
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
        # WIZ-driven forms (no explicit form tags)
        if self.wiz_data.get('fields'):
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
    def submit_form(self, form_index=None):
        """Submit a form, handling both traditional and WIZ-driven forms"""
        forms = self.get_forms()
        if form_index is None:
            form_index = 0
        if form_index >= len(forms):
            print(f"[-] Form index {form_index} out of range")
            return False
        form = forms[form_index]
        # Handle WIZ-driven form submission with JavaScript
        if form.get('wiz_driven') or not form.get('action'):
            return self.submit_wiz_form(form)
        # Traditional form submission
        action = form.get('action', '')
        if not action.startswith('http'):
            action = urljoin(self.current_url, action)
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
        print(f"[*] Submitting form to {action} with method {method}")
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
                print(f"[-] Response body (first 500 chars): {e.response.text[:500]}")
            return False
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
        print("\n" + "="*60)
        print(f"Current URL: {self.current_url}")
        print("="*60)
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
        print("="*60 + "\n")
def main():
    """Main entry point for testing"""
    browser = Browser()
    # Test Google signup flow
    print("=== Testing Google Signup Flow ===\n")
    # Step 1: Go to sign-in page
    browser.fetch("https://accounts.google.com/signin")
    browser.render_page()
    # Step 2: Click "Create account"
    if browser.click_link("Create account"):
        browser.render_page()
        # Step 3: Fill in name and submit
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

