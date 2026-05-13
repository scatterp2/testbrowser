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
   """
   Generic handler for Google WIZ batchexecute RPC submissions.
   Automatically detects RPC endpoint, constructs payload, and follows redirect.
   
   Args:
   field_mapping: Optional dict mapping field IDs/names to their specific 
   array indices if auto-detection fails. 
   Example: {'firstName': [0,0,0], 'lastName': [0,0,1]}
   """
   print(f"  [RPC] Detecting WIZ RPC submission...")
   
   # 1. Extract all necessary tokens - try multiple sources
   tokens = self.wiz_data.get('tokens', {})
   
   # If WIZ parsing failed, try to extract from URL
   if not tokens.get('SNlM0e'):
   print("  [RPC] WIZ tokens missing, trying URL extraction...")
   from urllib.parse import urlparse, parse_qs
   if self.current_url:
   parsed = urlparse(self.current_url)
   params = parse_qs(parsed.query)
   
   # Map URL params to token names
   if 'TL' in params:
   tokens['SNlM0e'] = params['TL'][0]  # TL often serves as SNlM0e equivalent
   if 'dsh' in params:
   tokens['dsh'] = params['dsh'][0]
   if 'bl' not in tokens:
   tokens['bl'] = 'boq_identityfrontendui_20240520.08_p0'  # Default build
   
   if not tokens.get('SNlM0e'):
   print("  [RPC] Critical tokens still missing, cannot proceed with RPC.")
   return False
   
   # 2. Identify the RPC Function Name
   rpc_name = None
   html_str = str(self.current_soup) if self.current_soup else ""
   
   # Heuristic: Look for known RPC prefixes
   rpc_candidates = [
   r'"(userspace\.[A-Za-z]+Submit)"',
   r'"(accountsweb\.[A-Za-z]+Submit)"',
   ]
   
   for pattern in rpc_candidates:
   match = re.search(pattern, html_str)
   if match:
   rpc_name = match.group(1)
   break
   
   if not rpc_name:
   print("  [RPC] Could not auto-detect RPC name, using fallback detection...")
   # Try to infer from URL path
   if '/signup/name' in self.current_url or '/lifecycle/steps/signup/name' in self.current_url:
   rpc_name = "userspace.NameSubmit"  # Correct RPC for name step
   elif '/birthdaygender' in self.current_url:
   rpc_name = "userspace.BirthdayGenderSubmit"
   elif '/password' in self.current_url:
   rpc_name = "userspace.CreateAccountSubmit"
   elif '/username' in self.current_url or '/selectusername' in self.current_url:
   rpc_name = "userspace.AvailabilitySubmit"
   else:
   rpc_name = "userspace.GenericSubmit"
   
   # FIRST check for pending_form_data from fill_form()
   payload_values = []
   if hasattr(self, 'pending_form_data') and self.pending_form_data:
   print(f"  [RPC] Using pending form data: {self.pending_form_data}")
   for key, val in self.pending_form_data.items():
   payload_values.append(val)
   else:
   # Fallback to scraping from DOM
   inputs = self.current_soup.find_all(['input', 'select', 'textarea']) if self.current_soup else []
   relevant_inputs = []
   for inp in inputs:
   if inp.get('type') == 'hidden': continue
   if inp.get('disabled'): continue
   relevant_inputs.append(inp)
   for inp in relevant_inputs:
   val = inp.get('value', '')
   if <response clipped><NOTE>Due to the max output limit, only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>
The file is quite long. Let me show you the rest of it, particularly the critical RPC submission and cookie handling parts:
Edit
$ view /workspace/browser.py
Here's the result of running `cat -n` on /workspace/browser.py:
   for inp in relevant_inputs:
   val = inp.get('value', '')
   if inp.get('type') in ['radio', 'checkbox'] and not inp.get('checked'): continue
   payload_values.append(val)
   
   # Construct batchExecute payload matching HAR exactly
   # HAR format for NameSubmit: [[["MjyMj","[0,0,[null,null,null,null,null,null,null,0,0,1,"firstname",null,null,2,1,2]]",null,"generic"]]]
   if 'NameSubmit' in rpc_name:
   # Build the complex nested array structure Google expects
   first_name = self.pending_form_data.get('firstName', payload_values[0] if payload_values else '')
   last_name = self.pending_form_data.get('lastName', payload_values[1] if len(payload_values) > 1 else '')
   
   inner_array = [
   0, 0,
   [
   None, None, None, None, None, None, None,  # indices 0-6
   0, 0, 1,  # indices 7-9
   first_name,  # index 10
   None, None,  # indices 11-12
   last_name,   # index 13
   2, 1, 2      # indices 14-16
   ]
   ]
   payload_json = json.dumps(inner_array)
   # Use the mapped RPC ID 'MjyMj' instead of full name
   rpcid = 'MjyMj'
   batch_payload = [[[rpcid, payload_json, None, "generic"]]]
   print(f"  [RPC] NameSubmit payload: {json.dumps(batch_payload)}")
   elif 'BirthdayGenderSubmit' in rpc_name:
   rpc_args = [None, None] + payload_values
   payload_json = json.dumps(rpc_args)
   batch_payload = [[[rpc_name, payload_json, None, "generic"]]]
   else:
   rpc_args = [None, None] + payload_values
   payload_json = json.dumps(rpc_args)
   batch_payload = [[[rpc_name, payload_json, None, "generic"]]]
   
   
   form_data = {
   'f.req': json.dumps(batch_payload),
   'at': tokens.get('SNlM0e', ''),
   'bl': tokens.get('bl', 'boq_identityfrontendui_20240520.08_p0'),
   }
   
   if tokens.get('dsh'):
   form_data['dsh'] = tokens['dsh']
   if tokens.get('hl'):
   form_data['hl'] = tokens['hl']
   
   base_url = "https://accounts.google.com"
   
   # Determine endpoint based on URL path (critical for success)
   path = self.current_url.split('?')[0] if self.current_url else ''
   if '/name' in path:
   endpoint = "/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute"
   elif '/username' in path or '/selectusername' in path:
   endpoint = "/_/accounts/setupwizard/listbatchexecute"
   else:
   endpoint = "/_/accounts/setupwizard/listbatchexecute"
   
   headers = {
   'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
   'X-Same-Domain': '1',
   'Referer': self.current_url if self.current_url else base_url,
   }
   
   print(f"  [RPC] Sending to {endpoint} via {rpc_name}...")
   print(f"  [RPC] Payload preview: f.req={json.dumps(batch_payload)[:100]}...")
   
   try:
   print(f"  [RPC] Sending POST request...")
   print(f"  [RPC] Current session cookies: {dict(self.session.cookies)}")
   
   response = self.session.post(base_url + endpoint, params={'rpcids': 'MjyMj', 'source-path': '/lifecycle/steps/signup/name', 'f.sid': tokens.get('f_sid', '1361846779993695398'), 'bl': tokens.get('bl', 'boq_identity-account-creation-evolution-ui_20260512.06_p0'), 'hl': 'en-US', 'TL': tokens.get('SNlM0e', ''), '_reqid': str(random.randint(10000, 999999)), 'rt': 'c'}, data=form_data, headers=headers)
   response.raise_for_status()
   
   # CRITICAL: Capture any new cookies set by the RPC response
   print(f"  [RPC] Response cookies received: {dict(response.cookies)}")
   # requests.Session automatically handles cookies, but let's verify
   print(f"  [RPC] Updated session cookies: {dict(self.session.cookies)}")
   
   text = response.text
   if text.startswith(')]}\''):
   text = text[4:]
   
   data = json.loads(text)
   
   if isinstance(data, list) and len(data) > 0:
   result_block = data[0]
   if isinstance(result_block, list) and len(result_block) > 0:
   raw_payload = result_block[0] 
   if isinstance(raw_payload, str):
   try:
   inner_data = json.loads(raw_payload)
   next_url = None
   if isinstance(inner_data, list):
   for item in inner_data:
   if isinstance(item, list) and len(item) > 1:
   if item[0] == 1 and isinstance(item[1], str) and item[1].startswith('/'):
   next_url = item[1]
   break
   for sub in item:
   if isinstance(sub, str) and (sub.startswith('/lifecycle') or sub.startswith('/signup')):
   next_url = sub
   break
   
   if next_url:
   # CRITICAL FIX: Preserve EXACT query string from current URL
   # Google requires all original parameters to maintain session
   current_parsed = urllib.parse.urlparse(self.current_url)
   
   # Just use the exact query string from current URL
   # This ensures TL, continue, ifkv, and all other params are preserved
   if current_parsed.query:
   full_next_url = f"https://accounts.google.com/lifecycle{next_url}?{current_parsed.query}"
   else:
   full_next_url = f"https://accounts.google.com/lifecycle{next_url}"
   
   print(f"  [RPC] Success! Redirecting to {full_next_url}")
   print(f"  [RPC] Using preserved query: {current_parsed.query}")
   return self.fetch(full_next_url)
   else:
   print("  [RPC] No nextPageUrl found in response.")
   self.current_html = response.text
   self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
   return True
   
   except json.JSONDecodeError as e:
   print(f"  [RPC] Failed to parse inner JSON: {e}")
   print(f"  [RPC] Raw response: {raw_payload[:200]}")
   
   self.current_html = response.text
   self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
   return True
   
   except Exception as e:
   print(f"  [RPC] Error during submission: {e}")
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
   
   def submit_wiz_batchexecute(self, rpcid, inner_data_array, source_path):
   """
$ view /workspace/browser.py
Here's the result of running `cat -n` on /workspace/browser.py:
   """
   Submit form data using Google's batchexecute RPC protocol.
   
   Args:
   rpcid: The RPC ID (e.g., 'MjyMj' for name submission)
   inner_data_array: Python list representing the form data structure
   source_path: The source path (e.g., '/lifecycle/steps/signup/name')
   """
   from urllib.parse import urlparse, parse_qs
   import re
   
   # Extract tokens from current page URL and HTML using regex (more reliable than JS)
   wiz_tokens = self.extract_wiz_data().get('tokens', {})
   
   # Get TL and dsh from current URL if not in wiz_tokens
   parsed_url = urlparse(self.current_url) if self.current_url else None
   url_params = parse_qs(parsed_url.query) if parsed_url else {}
   
   tl = wiz_tokens.get('TL') or url_params.get('TL', [None])[0]
   dsh = wiz_tokens.get('dsh') or url_params.get('dsh', [None])[0]
   
   # Extract SNlM0e (at token) directly from HTML using regex
   snlm0e = wiz_tokens.get('SNlM0e')
   if not snlm0e and self.current_html:
   # Pattern: "SNlM0e":"value" or data-at="value"
   match = re.search(r'"SNlM0e"\s*:\s*"([^"]+)"', self.current_html)
   if match:
   snlm0e = match.group(1)
   
   # f.sid is a client-generated session ID - generate one if not available
   f_sid = wiz_tokens.get('f_sid')
   if not f_sid:
   import random
   f_sid = str(random.randint(100000000000000000, 999999999999999999))
   
   # Build label - extract from page or use default
   bl = wiz_tokens.get('bl')
   if not bl and self.current_html:
   # Try to extract from script URLs
   bl_match = re.search(r'/_/js/[^/]+/k=([^/]+)/', self.current_html)
   if bl_match:
   bl = f"boq_identity-account-creation-evolution-ui_{bl_match.group(1)}"
   
   if not bl:
   bl = 'boq_identity-account-creation-evolution-ui_20260512.06_p0'
   
   if not tl or not snlm0e:
   print(f"ERROR: Missing required tokens. TL={tl}, SNlM0e={snlm0e}")
   # Debug: show what we found
   print(f"wiz_tokens keys: {list(wiz_tokens.keys())}")
   if self.current_html:
   has_snlm0e = bool(re.search(r'SNlM0e', self.current_html))
   print(f"HTML contains SNlM0e reference: {has_snlm0e}")
   return None
   
   # Construct the inner JSON string
   inner_json_str = json.dumps(inner_data_array, separators=(',', ':'))
   
   # Construct f.req parameter: [[[rpcid, inner_json, null, "generic"]]]
   f_req_data = [[[rpcid, inner_json_str, None, "generic"]]]
   f_req_str = json.dumps(f_req_data, separators=(',', ':'))
   
   # Build URL parameters
   from urllib.parse import urlencode
   url_params = {
   'rpcids': rpcid,
   'source-path': source_path,
   'f.sid': f_sid,
   'bl': bl,
   'hl': 'en-US',
   'TL': tl,
   '_reqid': '68453',
   'rt': 'c'
   }
   
   # Build POST data
   post_data = {
   'f.req': f_req_str,
   'at': snlm0e,
   }
   
   # Construct full URL
   base_url = 'https://accounts.google.com'
   endpoint = '/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute'
   full_url = f"{base_url}{endpoint}?{urlencode(url_params)}"
   
   # Set headers
   headers = {
   'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
   'Origin': 'https://accounts.google.com',
   'Referer': f'https://accounts.google.com{source_path}',
   'X-Same-Origin': '1',
   }
   
   print(f"\n=== SUBMITTING BATCHEXECUTE RPC ===")
   print(f"URL: {full_url}")
   print(f"f.req: {f_req_str[:200]}...")
   print(f"Tokens: TL={tl[:20]}..., f.sid={f_sid}, at={snlm0e[:20]}...")
   
   # Make the request
   try:
   response = self.session.post(full_url, data=post_data, headers=headers)
   self.last_response = response
   
   # Parse response - Google uses a line-delimited format:
   # length\njson_data_of-that-length\nlength\njson_data...
   resp_text = response.text
   if resp_text.startswith(")]}'"):
   resp_text = resp_text[4:]
   
   # Try to parse as line-delimited JSON (common Google format)
   lines = resp_text.strip().split('\n')
   parsed_items = []
   i = 0
   while i < len(lines):
   line = lines[i].strip()
   if line.isdigit():
   # Next line(s) contain JSON of that length
   length = int(line)
   json_str = ''
   i += 1
   # Accumulate characters (not counting newlines) until we reach the specified length
   char_count = 0
   while i < len(lines) and char_count < length:
   segment = lines[i]
   json_str += segment
   char_count += len(segment)
   if char_count < length:
   json_str += '\n'  # Preserve newline within JSON
   i += 1
   
   try:
   parsed_items.append(json.loads(json_str))
   except json.JSONDecodeError as e:
   print(f"Failed to parse segment at position {i}: {e}")
   print(f"Expected length: {length}, Got: {char_count} chars")
   print(f"JSON preview: {json_str[:100]}...")
   elif line:
   # Try parsing directly (fallback for non-prefixed JSON)
   try:
   parsed_items.append(json.loads(line))
   except:
   pass
   i += 1
   else:
   i += 1
   
   if parsed_items:
   print(f"\nResponse parsed successfully:")
   print(f"Status: {response.status_code}")
   print(f"Parsed {len(parsed_items)} items")
   
   for item in parsed_items:
   if isinstance(item, list) and len(item) > 1:
   if item[0] == 'wrb.fr':
   result = item[2] if len(item) > 2 else 'No data'
   print(f"RPC Result: {result}")
   # Check for error codes - [3] means validation error
   if len(item) > 5 and isinstance(item[5], list):
   print(f"Error indicators: {item[5]}")
   if 3 in item[5]:
   print("WARNING: Error code 3 indicates validation failure!")
   elif item[0] == 'di':
   print(f"Debug info: {item}")
   elif item[0] == 'af.httprm':
   print(f"HTTP Params: {item}")
   
   # Check if we got redirected or have new page content
   next_url = None
   for item in parsed_items:
   if isinstance(item, list):
   # Look for wrb.fr response which contains next page info
   if len(item) > 2 and item[0] == 'wrb.fr':
   result_data = item[2]
   # Parse the nested structure [[["steps/signup/birthdaygender"]]]
   if isinstance(result_data, list) and len(result_data) > 0:
   first_elem = result_data[0]
   if isinstance(first_elem, list) and len(first_elem) > 0:
   url_path = first_elem[0]
   if isinstance(url_path, str) and url_path.startswith('steps/'):
   next_url = f"https://accounts.google.com/lifecycle/{url_path}"
   print(f"✓ SUCCESS: Next page detected: {next_url}")
   # Also check for string URLs directly
   for elem in item:
   if isinstance(elem, str) and elem.startswith('steps/') and not next_url:
   next_url = f"https://accounts.google.com/lifecycle/{elem}"
   print(f"✓ Next page: {next_url}")
   
   # Auto-navigate to next page if found
   if next_url:
   print(f"✓ SUCCESS: Next page detected: {next_url}")
   print(f"[*] Automatically navigating to: {next_url}")
   self.pending_form_data = {}  # Clear form data
   return self.fetch(next_url)
   
   # Fallback: Check response text directly for URL pattern
   if 'steps/signup/birthdaygender' in resp_text:
   next_url = "https://accounts.google.com/lifecycle/steps/signup/birthdaygender"
   # Preserve dsh parameter from current URL
   if dsh and '?' not in next_url:
   next_url += f"?dsh={dsh}"
   elif not dsh and parsed_url and 'dsh' in url_params:
   next_url += f"?dsh={url_params['dsh'][0]}"
   print(f"✓ SUCCESS: Found birthdaygender path in response")
   print(f"[*] Navigating to: {next_url}")
   self.pending_form_data = {}
   return self.fetch(next_url)
   
   self.soup = BeautifulSoup(response.text, 'html.parser')
   return response
   else:
   print(f"Could not parse any valid JSON from response")
   self.soup = BeautifulSoup(response.text, 'html.parser')
   return response
   
   except Exception as e:
   print(f"Request failed: {e}")
   return None
   
   def submit_name_form(self, first_name, last_name):
   """
   Submit the name form using the batchexecute protocol.
   Based on HAR analysis, use RPC ID 'E815hb' with flat array format:
   [firstName, lastName, null, null, null, [], null, 1]
   """
   # Construct the inner data array - FLAT structure as per HAR
   inner_data = [
   first_name,       # Index 0: firstName
   last_name,        # Index 1: lastName
   None,             # Index 2: middleName
   None,             # Index 3: fullName
   None,             # Index 4: prefix
   [],               # Index 5: empty array (NOT null!)
   None,             # Index 6: unknown
   1                 # Index 7: flag
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
