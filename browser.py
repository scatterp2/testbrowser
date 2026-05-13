import requests
from bs4 import BeautifulSoup
import subprocess
import json
import re
import hashlib
import random
import urllib.parse

class Browser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.last_response = None
        self.soup = None
        self.pending_form_data = {}
        self.current_url = ""
        
    def fetch(self, url):
        """Fetch URL and update internal state"""
        if not url.startswith('http'):
            base = self.last_response.url if self.last_response else 'https://accounts.google.com'
            if url.startswith('/'):
                url = base.split('/')[2]
                url = f"https://{url}{url}"
            else:
                # Relative path
                base_path = '/'.join(self.last_response.url.rsplit('/', 1)[:-1])
                url = f"{base_path}/{url}"
        
        self.current_url = url
        response = self.session.get(url)
        self.last_response = response
        self.soup = BeautifulSoup(response.text, 'html.parser')
        
        # Execute JS to render dynamic content (though we rely mostly on RPC parsing)
        if response.headers.get('content-type', '').startswith('text/html'):
            self.execute_js_scripts()
            
        return response
    
    def execute_js_scripts(self):
        """Execute scripts using jsdom to render dynamic DOM elements"""
        if not self.soup:
            return
            
        html = str(self.soup)
        try:
            result = subprocess.run(
                ['node', 'run_jsdom.js'],
                input=html,
                text=True,
                capture_output=True,
                check=True,
                timeout=10
            )
            dom_state = json.loads(result.stdout)
            if 'html' in dom_state:
                self.soup = BeautifulSoup(dom_state['html'], 'html.parser')
        except Exception as e:
            # JS execution failed, continue with original soup
            pass
    
    def extract_all_wiz_tokens(self):
        """Extract all necessary tokens from WIZ_global_data"""
        if not self.soup:
            return {}
        
        tokens = {}
        script_tags = self.soup.find_all('script')
        
        for script in script_tags:
            if script.string and 'WIZ_global_data' in script.string:
                # Find the JSON object
                match = re.search(r'WIZ_global_data\s*=\s*(\{.*?\});', script.string, re.DOTALL)
                if match:
                    try:
                        wiz_json = json.loads(match.group(1))
                        tokens['raw'] = wiz_json
                        
                        # Extract specific known tokens
                        tokens['SNlM0e'] = wiz_json.get('SNlM0e')
                        tokens['TSDtV'] = wiz_json.get('TSDtV')
                        tokens['FdrFJe'] = wiz_json.get('FdrFJe')
                        tokens['TL'] = wiz_json.get('TL')
                        tokens['dsh'] = wiz_json.get('dsh')
                        tokens['bl'] = wiz_json.get('bl', 'boq_identityfrontendui_20240520.09_p0')
                        
                        # Try to find f.sid
                        if 'f.sid' in wiz_json:
                            tokens['f_sid'] = wiz_json['f.sid']
                        elif 'GxU1Ic' in wiz_json: # Sometimes stored here
                            tokens['f_sid'] = wiz_json['GxU1Ic']
                            
                        break
                    except json.JSONDecodeError:
                        continue
        
        # Fallback: Check URL for dsh
        if 'dsh' not in tokens and self.last_response and self.last_response.url:
            parsed = urllib.parse.urlparse(self.last_response.url)
            params = urllib.parse.parse_qs(parsed.query)
            if 'dsh' in params:
                tokens['dsh'] = params['dsh'][0]
                
        return tokens
    
    def fill_form(self, form_index, data):
        """Store form data for later RPC submission"""
        self.pending_form_data = data
        
        # Also try to update the DOM for rendering purposes
        if self.soup:
            forms = self.soup.find_all('form')
            if form_index < len(forms):
                form = forms[form_index]
                for field_name, value in data.items():
                    # Try by ID first (Google often uses IDs for dynamic fields)
                    inp = form.find('input', id=field_name)
                    if not inp:
                        inp = form.find('input', {'name': field_name})
                    if not inp:
                        # Try placeholder matching
                        inp = form.find('input', placeholder=lambda x: x and field_name.lower() in x.lower())
                    
                    if inp:
                        inp['value'] = value
    
    def submit_wiz_rpc(self, rpc_name_override=None):
        """Generic RPC Handler: Detects endpoint, constructs payload, submits, and follows redirect"""
        tokens = self.extract_all_wiz_tokens()
        if not tokens.get('SNlM0e'):
            print("⚠️ Warning: SNlM0e token not found. Attempting fallback.")
        
        # 1. Determine RPC Name based on URL path
        path = self.current_url.split('?')[0]
        rpc_name = rpc_name_override
        
        if not rpc_name:
            if '/name' in path:
                rpc_name = 'userspace.NameSubmit'
            elif '/birthdaygender' in path:
                rpc_name = 'userspace.BirthdayGenderSubmit'
            elif '/password' in path:
                rpc_name = 'userspace.CreateAccountSubmit'
            elif '/phone' in path:
                rpc_name = 'userspace.PhoneVerificationSubmit'
            elif '/username' in path:
                rpc_name = 'userspace.AvailabilitySubmit'
            else:
                # Default guess
                rpc_name = 'userspace.GenericSubmit'
        
        print(f"🚀 Submitting via RPC: {rpc_name}")
        
        # 2. Collect Values
        # Priority: pending_form_data > HTML inputs
        values = []
        if self.pending_form_data:
            # Maintain order based on expected fields for this RPC
            # This is a simplification; ideally we map field names to indices
            for key, val in self.pending_form_data.items():
                values.append(val)
        else:
            # Fallback to scraping inputs
            inputs = self.soup.find_all('input')
            for inp in inputs:
                if inp.get('type') not in ['hidden', 'submit', 'button']:
                    val = inp.get('value', '')
                    if val:
                        values.append(val)
        
        # Ensure we have at least empty strings if no values found
        if not values:
            values = [""] * 2 
            
        # 3. Construct Payload Structure
        # Most Google RPCs expect: [[[rpcId, "json_string", null, "generic"]]]
        # The inner json_string structure varies by RPC. 
        # Common pattern for simple forms: [null, null, val1, val2, ...]
        
        # Special handling for Birthday/Gender which has specific indices
        if 'BirthdayGender' in rpc_name:
            # Expected: [null, null, month, day, year, gender]
            # Assuming values passed are {'month': '1', 'day': '15', 'year': '1990', 'gender': '1'}
            # We need to map them correctly. If pending_form_data is used, it should be ordered or mapped.
            # For now, assume the user passed a list or we map known keys
            if isinstance(self.pending_form_data, dict):
                m = self.pending_form_data.get('month', '1')
                d = self.pending_form_data.get('day', '1')
                y = self.pending_form_data.get('year', '1990')
                g = self.pending_form_data.get('gender', '1')
                inner_data = [None, None, m, d, y, g]
            else:
                inner_data = [None, None] + values
        elif 'NameSubmit' in rpc_name:
            # [firstName, lastName]
            inner_data = values
        elif 'CreateAccountSubmit' in rpc_name:
            # [password, password_confirm] (usually)
            inner_data = values
        else:
            # Generic fallback
            inner_data = values

        inner_json = json.dumps(inner_data)
        
        batch_payload = [
            [
                [rpc_name, inner_json, None, "generic"]
            ]
        ]
        
        # Serialize the outer list to string format expected by form data
        # Note: Google often expects the value to be a string representation of the list
        payload_str = json.dumps(batch_payload)
        
        # 4. Prepare Request
        base_url = "https://accounts.google.com"
        # Construct endpoint URL
        # Usually: /_/accounts/setupwizard/listbatchexecute
        endpoint = "/_/accounts/setupwizard/listbatchexecute"
        
        # Add query parameters
        params = {
            'bl': tokens.get('bl', 'boq_identityfrontendui_20240520.09_p0'),
            'hl': 'en',
            '_reqid': str(random.randint(100000, 999999)),
            'rt': 'j'
        }
        if tokens.get('dsh'):
            params['dsh'] = tokens['dsh']
            
        req_url = f"{base_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'X-Same-Origin': 'true',
            'Referer': self.current_url
        }
        
        # Form data needs specific keys
        form_data = {
            'f.req': payload_str,
            'at': tokens.get('SNlM0e', '')
        }
        
        print(f"📡 Sending to: {req_url}")
        # print(f"📦 Payload: {payload_str[:100]}...") # Debug
        
        try:
            response = self.session.post(req_url, params=params, data=form_data, headers=headers)
            response.raise_for_status()
            
            # 5. Parse Response
            # Response is often line-delimited JSON or wrapped in ]}'
            text = response.text
            # Clean up Google's weird response wrapper if present
            if text.startswith(")]}'"):
                text = text[4:]
            
            # Try to parse JSON
            try:
                data = json.loads(text)
                # Look for nextPageUrl in the response structure
                # Structure is usually: [ [[response_data]], [[next_page_info]] ]
                # Next page info often contains [9, null, null, null, "URL"]
                
                next_url = None
                
                # Deep search for URL
                def find_url(obj):
                    if isinstance(obj, list):
                        for item in obj:
                            res = find_url(item)
                            if res: return res
                    elif isinstance(obj, dict):
                        if 'nextPageUrl' in obj:
                            return obj['nextPageUrl']
                        # Sometimes it's just a URL string in a specific position
                        for v in obj.values():
                            res = find_url(v)
                            if res: return res
                    elif isinstance(obj, str) and obj.startswith('/'):
                        # Heuristic: if it looks like a path
                        if 'signup' in obj or 'setup' in obj:
                            return obj
                    return None
                
                next_url = find_url(data)
                
                if next_url:
                    print(f"✅ Success! Redirecting to: {next_url}")
                    self.pending_form_data = {} # Clear form data
                    return self.fetch(next_url)
                else:
                    print("⚠️ No redirect URL found in response. Checking for errors...")
                    # Check for error codes
                    if isinstance(data, list) and len(data) > 0:
                         # Often error is in the second part of the tuple
                         pass
                    self.last_response = response
                    self.soup = BeautifulSoup(response.text, 'html.parser')
                    return response
                    
            except json.JSONDecodeError:
                print("⚠️ Could not parse JSON response. Raw content:")
                print(text[:200])
                self.last_response = response
                self.soup = BeautifulSoup(response.text, 'html.parser')
                return response
                
        except Exception as e:
            print(f"❌ RPC Submission failed: {e}")
            return None

    def click_button(self, text):
        """Click button by text. If it's a WIZ form, trigger RPC."""
        if not self.soup:
            return None
            
        buttons = self.soup.find_all('button')
        target_btn = None
        for btn in buttons:
            if text.lower() in btn.get_text().lower():
                target_btn = btn
                break
        
        if not target_btn:
            inputs = self.soup.find_all('input', type='submit')
            for inp in inputs:
                if text.lower() in inp.get('value', '').lower():
                    target_btn = inp
                    break
        
        if target_btn:
            # Check if this button is inside a form that requires RPC
            parent_form = target_btn.find_parent('form')
            if parent_form and parent_form.get('jsaction'):
                print(f"🖱️ Detected WIZ button click: {text}")
                return self.submit_wiz_rpc()
            
            # Fallback: Standard link or form submit
            onclick = target_btn.get('onclick')
            if onclick:
                # Try to extract URL from onclick
                match = re.search(r"window\.location\.href='([^']+)'", onclick)
                if match:
                    return self.fetch(match.group(1))
            
            # If it's a standard form submit
            if parent_form:
                forms = self.soup.find_all('form')
                idx = forms.index(parent_form)
                # Try standard submit first, if fails, try RPC
                # For this demo, we assume if we are on a signup page, it's RPC
                if 'accounts.google.com' in self.current_url:
                    return self.submit_wiz_rpc()
        
        return None

    def render_page(self):
        """Render page as text"""
        if not self.soup:
            return "No page loaded"
        
        for tag in self.soup(['script', 'style']):
            tag.decompose()
        
        text = self.soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
