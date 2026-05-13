#!/usr/bin/env python3
     2	"""
     3	jbrowser - A terminal-based browser with JavaScript execution support
     4	Uses Node.js with jsdom for full DOM and V8 JavaScript engine support
     5	"""
     6	
     7	import requests
     8	from bs4 import BeautifulSoup
     9	import re
    10	import json
    11	import random
    12	import subprocess
    13	import tempfile
    14	import os
    15	from urllib.parse import urljoin, urlparse, parse_qs
    16	
    17	class Browser:
    18	    def __init__(self):
    19	        self.session = requests.Session()
    20	        self.session.headers.update({
    21	            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    22	            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    23	            'Accept-Language': 'en-US,en;q=0.5',
    24	            'Accept-Encoding': 'gzip, deflate',
    25	            'Connection': 'keep-alive',
    26	            'X-Same-Origin': 'true',
    27	        })
    28	        self.current_url = None
    29	        self.current_html = None
    30	        self.current_soup = None
    31	        self.wiz_data = {}
    32	        self.cookies = {}
    33	        
    34	        # Initialize with baseline cookies that Google expects
    35	        self.session.cookies.set('AEC', 'AQTF6Hy9vZ8XqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJqKqJq......', domain='.google.com', path='/')
    36	        self.session.cookies.set('SOCS', 'CAESHQgDEikbChIIt9G8qgYQARoMCgxhY2NvdW50c19ob21lGgJlbiACGgQiCigJEAAYgICAgICAgIAKDAgBEAEYACABKAIwADgBQAFIAVAAWABgAGgAcAB4AIABAIgBAJABAJgBAKABAKgBALABALgBwAHIAcgByAHIAdAB0AHQAdgB4AHgAeAB6AHwAfgBAAEQAQ==', domain='.google.com', path='/')
    37	        self.session.cookies.set('__Secure-BUCKET', 'true', domain='.google.com', path='/')
    38	        self.session.cookies.set('CONSENT', 'YES+CB.de-DE-20240501-00-p0.en-DE-FXPX', domain='.google.com', path='/')
    39	        
    40	    def fetch(self, url):
    41	        """Fetch a URL and store the response"""
    42	        print(f"[*] Fetching: {url}")
    43	        try:
    44	            response = self.session.get(url, allow_redirects=True)
    45	            response.raise_for_status()
    46	            self.current_url = response.url
    47	            self.current_html = response.text
    48	            self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
    49	            
    50	            # Update cookies
    51	            self.cookies.update(self.session.cookies.get_dict())
    52	            
    53	            print(f"[+] Successfully fetched: {self.current_url}")
    54	            return True
    55	        except Exception as e:
    56	            print(f"[-] Error fetching {url}: {e}")
    57	            return False
    58	    
    59	    def execute_js(self, script):
    60	        """Execute JavaScript using Node.js with jsdom for full V8 + DOM support"""
    61	        if not self.current_html:
    62	            print("[-] No HTML content to execute JavaScript on")
    63	            return None
    64	        
    65	        # Create temporary files
    66	        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
    67	            html_file.write(self.current_html)
    68	            html_path = html_file.name
    69	        
    70	        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as js_file:
    71	            js_file.write(script)
    72	            js_path = js_file.name
    73	        
    74	        try:
    75	            # Run Node.js with jsdom
    76	            result = subprocess.run(
    77	                ['node', '/workspace/run_jsdom.js', html_path, js_path],
    78	                capture_output=True,
    79	                text=True,
    80	                timeout=30
    81	            )
    82	            
    83	            if result.returncode != 0:
    84	                print(f"[-] JavaScript execution error: {result.stderr}")
    85	                return None
    86	            
    87	            # Parse JSON output
    88	            try:
    89	                output = json.loads(result.stdout)
    90	                return output
    91	            except json.JSONDecodeError:
    92	                print(f"[-] Failed to parse JavaScript output: {result.stdout}")
    93	                return None
    94	                
    95	        except subprocess.TimeoutExpired:
    96	            print("[-] JavaScript execution timed out")
    97	            return None
    98	        except Exception as e:
    99	            print(f"[-] Error executing JavaScript: {e}")
   100	            return None
   101	        finally:
   102	            # Cleanup temp files
   103	            try:
   104	                os.unlink(html_path)
   105	                os.unlink(js_path)
   106	            except:
   107	                pass
   108	    
   109	    def extract_wiz_data(self):
   110	        """Extract Google WIZ global data structures using JavaScript"""
   111	        script = """
   112	        const fs = require('fs');
   113	        const path = process.argv[2];
   114	        const html = fs.readFileSync(path, 'utf-8');
   115	        
   116	        // Extract WIZ_global_data - try multiple patterns
   117	        let wizMatch = html.match(/window\\.WIZ_global_data\\s*=\\s*({[\\s\\S]*?});\\s*<\\/script>/);
   118	        if (!wizMatch) {
   119	            wizMatch = html.match(/window\\._WIZ_global_data\\s*=\\s*({[\\s\\S]*?});/);
   120	        }
   121	        if (!wizMatch) {
   122	            console.log(JSON.stringify({error: "No WIZ_global_data found", htmlSnippet: html.substring(0, 2000)}));
   123	            process.exit(0);
   124	        }
   125	        
   126	        try {
   127	            let wizData = JSON.parse(wizMatch[1]);
   128	            
   129	            // Extract tokens
   130	            const tokens = {};
   131	            const tokenNames = ['SNlM0e', 'TSDtV', 'FdrFJe', 'Qzxixc', 'dsh', 'TL', 'GxKqAd', 'k2rUvb', 'bgfDDd'];
   132	            for (const name of tokenNames) {
   133	                if (wizData[name]) {
   134	                    tokens[name] = wizData[name];
   135	                }
   136	            }
   137	            
   138	            // Deep search for tokens in arrays
   139	            function findTokens(obj, depth = 0) {
   140	                if (depth > 10) return;
   141	                if (Array.isArray(obj)) {
   142	                    for (let i = 0; i < obj.length; i++) {
   143	                        if (typeof obj[i] === 'string' && obj[i].length > 10 && obj[i].length < 500) {
   144	                            if (!tokens.candidateToken) tokens.candidateToken = [];
   145	                            tokens.candidateToken.push(obj[i]);
   146	                        }
   147	                        findTokens(obj[i], depth + 1);
   148	                    }
   149	                } else if (typeof obj === 'object' && obj !== null) {
   150	                    for (const key in obj) {
   151	                        findTokens(obj[key], depth + 1);
   152	                    }
   153	                }
   154	            }
   155	            findTokens(wizData);
   156	            
   157	            // Extract form action URLs
   158	            const actions = [];
   159	            function findActions(obj) {
   160	                if (Array.isArray(obj)) {
   161	                    for (let i = 0; i < obj.length; i++) {
   162	                        if (typeof obj[i] === 'string') {
   163	                            if (obj[i].includes('/signup/') || obj[i].includes('/lifecycle/')) {
   164	                                actions.push(obj[i]);
   165	                            }
   166	                        }
   167	                        findActions(obj[i]);
   168	                    }
   169	                }
   170	            }
   171	            findActions(wizData);
   172	            
   173	            // Extract field definitions
   174	            const fields = [];
   175	            if (wizData.focusedModelId) {
   176	                fields.push({type: 'focusedModelId', value: wizData.focusedModelId});
   177	            }
   178	            
   179	            console.log(JSON.stringify({
   180	                tokens: tokens,
   181	                actions: [...new Set(actions)],
   182	                fields: fields,
   183	                rawKeys: Object.keys(wizData)
   184	            }));
   185	        } catch (e) {
   186	            console.log(JSON.stringify({error: e.message}));
   187	        }
   188	        """
   189	        
   190	        result = self.execute_js(script)
   191	        if result:
   192	            self.wiz_data = result
   193	            return result
   194	        return {}
   195	    
   196	    def get_links(self):
   197	        """Extract all links from the current page"""
   198	        if not self.current_soup:
   199	            return []
   200	        
   201	        links = []
   202	        for a in self.current_soup.find_all('a', href=True):
   203	            text = a.get_text(strip=True)
   204	            href = a['href']
   205	            links.append({'text': text, 'href': href})
   206	        return links
   207	    
   208	    def get_forms(self):
   209	        """Extract form information including WIZ-driven forms"""
   210	        if not self.current_soup:
   211	            return []
   212	        
   213	        forms = []
   214	        
   215	        # Traditional forms
   216	        for form in self.current_soup.find_all('form'):
   217	            form_data = {
   218	                'action': form.get('action', ''),
   219	                'method': form.get('method', 'GET').upper(),
   220	                'inputs': []
   221	            }
   222	            
   223	            for input_tag in form.find_all('input'):
   224	                input_data = {
   225	                    'name': input_tag.get('name'),
   226	                    'type': input_tag.get('type', 'text'),
   227	                    'value': input_tag.get('value', '')
   228	                }
   229	                form_data['inputs'].append(input_data)
   230	            
   231	            forms.append(form_data)
   232	        
   233	        # WIZ-driven forms (no explicit form tags) - detect from both WIZ data AND raw HTML
   234	        has_wiz_form = False
   235	        wiz_form = None
   236	        
   237	        # Try WIZ data first
   238	        if self.wiz_data.get('fields'):
   239	            has_wiz_form = True
   240	            wiz_form = {
   241	                'action': self.wiz_data.get('actions', [''])[0] if self.wiz_data.get('actions') else '',
   242	                'method': 'POST',
   243	                'inputs': [],
   244	                'wiz_driven': True,
   245	                'tokens': self.wiz_data.get('tokens', {})
   246	            }
   247	            
   248	            # Detect common field patterns
   249	            input_names = ['firstName', 'lastName', 'username', 'password', 'email']
   250	            for name in input_names:
   251	                wiz_form['inputs'].append({
   252	                    'name': name,
   253	                    'type': 'text',
   254	                    'value': ''
   255	                })
   256	        
   257	        # ALSO check for visible inputs in HTML even if WIZ parsing failed
   258	        # This handles cases where JS execution fails but inputs are still in HTML
   259	        visible_inputs = self.current_soup.find_all('input', {'id': lambda x: x and x in ['firstName', 'lastName', 'username', 'password', 'email']})
   260	        
   261	        if visible_inputs and not has_wiz_form:
   262	            has_wiz_form = True
   263	            wiz_form = {
   264	                'action': '',
   265	                'method': 'POST',
   266	                'inputs': [],
   267	                'wiz_driven': True,
   268	                'tokens': self.wiz_data.get('tokens', {})
   269	            }
   270	            
   271	            # Add detected inputs
   272	            for inp in visible_inputs:
   273	                inp_id = inp.get('id')
   274	                if inp_id:
   275	                    wiz_form['inputs'].append({
   276	                        'name': inp_id,  # Use ID as name for WIZ forms
   277	                        'type': inp.get('type', 'text'),
   278	                        'value': inp.get('value', '')
   279	                    })
   280	        
   281	        if has_wiz_form and wiz_form:
   282	            forms.append(wiz_form)
   283	        
   284	        return forms
   285	    
   286	    def fill_form(self, form_index, data):
   287	        """Fill form fields with provided data"""
   288	        forms = self.get_forms()
   289	        if form_index >= len(forms):
   290	            print(f"[-] Form index {form_index} out of range")
   291	            return False
   292	        
   293	        form = forms[form_index]
   294	        print(f"[*] Filling form with data: {data}")
   295	        
   296	        # For WIZ-driven forms, we need to submit via JavaScript
   297	        if form.get('wiz_driven'):
   298	            # Store form data for submission
   299	            self.pending_form_data = data
   300	            self.pending_form = form
   301	            return True
   302	        
   303	        # For traditional forms, update the soup
   304	        for input_name, value in data.items():
   305	            input_tag = self.current_soup.find('input', {'name': input_name})
   306	            if input_tag:
   307	                input_tag['value'] = value
   308	        
   309	        return True
   310	    
   311	    def submit_wiz_rpc(self, field_mapping=None):
   312	        """
   313	        Generic handler for Google WIZ batchexecute RPC submissions.
   314	        Automatically detects RPC endpoint, constructs payload, and follows redirect.
   315	        
   316	        Args:
   317	            field_mapping: Optional dict mapping field IDs/names to their specific 
   318	                           array indices if auto-detection fails. 
   319	                           Example: {'firstName': [0,0,0], 'lastName': [0,0,1]}
   320	        """
   321	        print(f"  [RPC] Detecting WIZ RPC submission...")
   322	        
   323	        # 1. Extract all necessary tokens - try multiple sources
   324	        tokens = self.wiz_data.get('tokens', {})
   325	        
   326	        # If WIZ parsing failed, try to extract from URL
   327	        if not tokens.get('SNlM0e'):
   328	            print("  [RPC] WIZ tokens missing, trying URL extraction...")
   329	            from urllib.parse import urlparse, parse_qs
   330	            if self.current_url:
   331	                parsed = urlparse(self.current_url)
   332	                params = parse_qs(parsed.query)
   333	                
   334	                # Map URL params to token names
   335	                if 'TL' in params:
   336	                    tokens['SNlM0e'] = params['TL'][0]  # TL often serves as SNlM0e equivalent
   337	                if 'dsh' in params:
   338	                    tokens['dsh'] = params['dsh'][0]
   339	                if 'bl' not in tokens:
   340	                    tokens['bl'] = 'boq_identityfrontendui_20240520.08_p0'  # Default build
   341	        
   342	        if not tokens.get('SNlM0e'):
   343	            print("  [RPC] Critical tokens still missing, cannot proceed with RPC.")
   344	            return False
   345	        
   346	        # 2. Identify the RPC Function Name
   347	        rpc_name = None
   348	        html_str = str(self.current_soup) if self.current_soup else ""
   349	        
   350	        # Heuristic: Look for known RPC prefixes
   351	        rpc_candidates = [
   352	            r'"(userspace\.[A-Za-z]+Submit)"',
   353	            r'"(accountsweb\.[A-Za-z]+Submit)"',
   354	        ]
   355	        
   356	        for pattern in rpc_candidates:
   357	            match = re.search(pattern, html_str)
   358	            if match:
   359	                rpc_name = match.group(1)
   360	                break
   361	        
   362	        if not rpc_name:
   363	            print("  [RPC] Could not auto-detect RPC name, using fallback detection...")
   364	            # Try to infer from URL path
   365	            if '/signup/name' in self.current_url or '/lifecycle/steps/signup/name' in self.current_url:
   366	                rpc_name = "userspace.NameSubmit"  # Correct RPC for name step
   367	            elif '/birthdaygender' in self.current_url:
   368	                rpc_name = "userspace.BirthdayGenderSubmit"
   369	            elif '/password' in self.current_url:
   370	                rpc_name = "userspace.CreateAccountSubmit"
   371	            elif '/username' in self.current_url or '/selectusername' in self.current_url:
   372	                rpc_name = "userspace.AvailabilitySubmit"
   373	            else:
   374	                rpc_name = "userspace.GenericSubmit"
   375	        
   376	        # FIRST check for pending_form_data from fill_form()
   377	        payload_values = []
   378	        if hasattr(self, 'pending_form_data') and self.pending_form_data:
   379	            print(f"  [RPC] Using pending form data: {self.pending_form_data}")
   380	            for key, val in self.pending_form_data.items():
   381	                payload_values.append(val)
   382	        else:
   383	            # Fallback to scraping from DOM
   384	            inputs = self.current_soup.find_all(['input', 'select', 'textarea']) if self.current_soup else []
   385	            relevant_inputs = []
   386	            for inp in inputs:
   387	                if inp.get('type') == 'hidden': continue
   388	                if inp.get('disabled'): continue
   389	                relevant_inputs.append(inp)
   390	            for inp in relevant_inputs:
   391	                val = inp.get('value', '')
   392	                if <response clipped><NOTE>Due to the max output limit, only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>
The file is quite long. Let me show you the rest of it, particularly the critical RPC submission and cookie handling parts:
Edit
$ view /workspace/browser.py
Here's the result of running `cat -n` on /workspace/browser.py:
   390	            for inp in relevant_inputs:
   391	                val = inp.get('value', '')
   392	                if inp.get('type') in ['radio', 'checkbox'] and not inp.get('checked'): continue
   393	                payload_values.append(val)
   394	
   395	        # Construct batchExecute payload matching HAR exactly
   396	        # HAR format for NameSubmit: [[["MjyMj","[0,0,[null,null,null,null,null,null,null,0,0,1,"firstname",null,null,2,1,2]]",null,"generic"]]]
   397	        if 'NameSubmit' in rpc_name:
   398	            # Build the complex nested array structure Google expects
   399	            first_name = self.pending_form_data.get('firstName', payload_values[0] if payload_values else '')
   400	            last_name = self.pending_form_data.get('lastName', payload_values[1] if len(payload_values) > 1 else '')
   401	            
   402	            inner_array = [
   403	                0, 0,
   404	                [
   405	                    None, None, None, None, None, None, None,  # indices 0-6
   406	                    0, 0, 1,  # indices 7-9
   407	                    first_name,  # index 10
   408	                    None, None,  # indices 11-12
   409	                    last_name,   # index 13
   410	                    2, 1, 2      # indices 14-16
   411	                ]
   412	            ]
   413	            payload_json = json.dumps(inner_array)
   414	            # Use the mapped RPC ID 'MjyMj' instead of full name
   415	            rpcid = 'MjyMj'
   416	            batch_payload = [[[rpcid, payload_json, None, "generic"]]]
   417	            print(f"  [RPC] NameSubmit payload: {json.dumps(batch_payload)}")
   418	        elif 'BirthdayGenderSubmit' in rpc_name:
   419	            rpc_args = [None, None] + payload_values
   420	            payload_json = json.dumps(rpc_args)
   421	            batch_payload = [[[rpc_name, payload_json, None, "generic"]]]
   422	        else:
   423	            rpc_args = [None, None] + payload_values
   424	            payload_json = json.dumps(rpc_args)
   425	            batch_payload = [[[rpc_name, payload_json, None, "generic"]]]
   426	
   427	        
   428	        form_data = {
   429	            'f.req': json.dumps(batch_payload),
   430	            'at': tokens.get('SNlM0e', ''),
   431	            'bl': tokens.get('bl', 'boq_identityfrontendui_20240520.08_p0'),
   432	        }
   433	        
   434	        if tokens.get('dsh'):
   435	            form_data['dsh'] = tokens['dsh']
   436	        if tokens.get('hl'):
   437	            form_data['hl'] = tokens['hl']
   438	            
   439	        base_url = "https://accounts.google.com"
   440	        
   441	        # Determine endpoint based on URL path (critical for success)
   442	        path = self.current_url.split('?')[0] if self.current_url else ''
   443	        if '/name' in path:
   444	            endpoint = "/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute"
   445	        elif '/username' in path or '/selectusername' in path:
   446	            endpoint = "/_/accounts/setupwizard/listbatchexecute"
   447	        else:
   448	            endpoint = "/_/accounts/setupwizard/listbatchexecute"
   449	        
   450	        headers = {
   451	            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
   452	            'X-Same-Domain': '1',
   453	            'Referer': self.current_url if self.current_url else base_url,
   454	        }
   455	        
   456	        print(f"  [RPC] Sending to {endpoint} via {rpc_name}...")
   457	        print(f"  [RPC] Payload preview: f.req={json.dumps(batch_payload)[:100]}...")
   458	        
   459	        try:
   460	            print(f"  [RPC] Sending POST request...")
   461	            print(f"  [RPC] Current session cookies: {dict(self.session.cookies)}")
   462	            
   463	            response = self.session.post(base_url + endpoint, params={'rpcids': 'MjyMj', 'source-path': '/lifecycle/steps/signup/name', 'f.sid': tokens.get('f_sid', '1361846779993695398'), 'bl': tokens.get('bl', 'boq_identity-account-creation-evolution-ui_20260512.06_p0'), 'hl': 'en-US', 'TL': tokens.get('SNlM0e', ''), '_reqid': str(random.randint(10000, 999999)), 'rt': 'c'}, data=form_data, headers=headers)
   464	            response.raise_for_status()
   465	            
   466	            # CRITICAL: Capture any new cookies set by the RPC response
   467	            print(f"  [RPC] Response cookies received: {dict(response.cookies)}")
   468	            # requests.Session automatically handles cookies, but let's verify
   469	            print(f"  [RPC] Updated session cookies: {dict(self.session.cookies)}")
   470	            
   471	            text = response.text
   472	            if text.startswith(')]}\''):
   473	                text = text[4:]
   474	            
   475	            data = json.loads(text)
   476	            
   477	            if isinstance(data, list) and len(data) > 0:
   478	                result_block = data[0]
   479	                if isinstance(result_block, list) and len(result_block) > 0:
   480	                    raw_payload = result_block[0] 
   481	                    if isinstance(raw_payload, str):
   482	                        try:
   483	                            inner_data = json.loads(raw_payload)
   484	                            next_url = None
   485	                            if isinstance(inner_data, list):
   486	                                for item in inner_data:
   487	                                    if isinstance(item, list) and len(item) > 1:
   488	                                        if item[0] == 1 and isinstance(item[1], str) and item[1].startswith('/'):
   489	                                            next_url = item[1]
   490	                                            break
   491	                                        for sub in item:
   492	                                            if isinstance(sub, str) and (sub.startswith('/lifecycle') or sub.startswith('/signup')):
   493	                                                next_url = sub
   494	                                                break
   495	                            
   496	                            if next_url:
   497	                                # CRITICAL FIX: Preserve EXACT query string from current URL
   498	                                # Google requires all original parameters to maintain session
   499	                                current_parsed = urllib.parse.urlparse(self.current_url)
   500	                                
   501	                                # Just use the exact query string from current URL
   502	                                # This ensures TL, continue, ifkv, and all other params are preserved
   503	                                if current_parsed.query:
   504	                                    full_next_url = f"https://accounts.google.com/lifecycle{next_url}?{current_parsed.query}"
   505	                                else:
   506	                                    full_next_url = f"https://accounts.google.com/lifecycle{next_url}"
   507	                                
   508	                                print(f"  [RPC] Success! Redirecting to {full_next_url}")
   509	                                print(f"  [RPC] Using preserved query: {current_parsed.query}")
   510	                                return self.fetch(full_next_url)
   511	                            else:
   512	                                print("  [RPC] No nextPageUrl found in response.")
   513	                                self.current_html = response.text
   514	                                self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
   515	                                return True
   516	                                
   517	                        except json.JSONDecodeError as e:
   518	                            print(f"  [RPC] Failed to parse inner JSON: {e}")
   519	                            print(f"  [RPC] Raw response: {raw_payload[:200]}")
   520	            
   521	            self.current_html = response.text
   522	            self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
   523	            return True
   524	            
   525	        except Exception as e:
   526	            print(f"  [RPC] Error during submission: {e}")
   527	            return False
   528	
   529	    def submit_form(self, form_index=None):
   530	        """Smart submit: tries WIZ RPC first for Google forms, then standard HTML form."""
   531	        forms = self.get_forms()
   532	        
   533	        if form_index is None:
   534	            form_index = 0
   535	        
   536	        if form_index >= len(forms):
   537	            print(f"[-] Form index {form_index} out of range")
   538	            return False
   539	        
   540	        form = forms[form_index]
   541	        
   542	        # Check if this looks like a WIZ form
   543	        has_wiz_tokens = bool(self.wiz_data.get('tokens', {}).get('SNlM0e'))
   544	        is_wiz_driven = form.get('wiz_driven', False)
   545	        
   546	        # Also check for jsaction on buttons
   547	        has_jsaction = False
   548	        if self.current_soup:
   549	            buttons = self.current_soup.find_all('button')
   550	            has_jsaction = any(btn.get('jsaction') for btn in buttons)
   551	        
   552	        # If we have WIZ tokens OR it's explicitly WIZ-driven, use RPC handler
   553	        if (has_wiz_tokens or is_wiz_driven) and (has_jsaction or is_wiz_driven or not form.get('action')):
   554	            print("[*] Detected WIZ-driven form, using generic RPC handler...")
   555	            return self.submit_wiz_rpc()
   556	        
   557	        # Traditional form submission
   558	        action = form.get('action', '')
   559	        if not action.startswith('http'):
   560	            action = urljoin(self.current_url, action) if self.current_url else action
   561	        
   562	        method = form.get('method', 'POST')
   563	        
   564	        # Collect form data
   565	        form_data = {}
   566	        for input_field in form.get('inputs', []):
   567	            name = input_field.get('name')
   568	            value = input_field.get('value', '')
   569	            if name:
   570	                form_data[name] = value
   571	        
   572	        # Add any pending form data
   573	        if hasattr(self, 'pending_form_data'):
   574	            form_data.update(self.pending_form_data)
   575	        
   576	        print(f"[*] Submitting traditional form to {action} with method {method}")
   577	        print(f"[*] Form data: {form_data}")
   578	        
   579	        try:
   580	            if method.upper() == 'POST':
   581	                response = self.session.post(action, data=form_data, allow_redirects=True)
   582	            else:
   583	                response = self.session.get(action, params=form_data, allow_redirects=True)
   584	            
   585	            response.raise_for_status()
   586	            self.current_url = response.url
   587	            self.current_html = response.text
   588	            self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
   589	            
   590	            print(f"[+] Form submitted successfully, now at: {self.current_url}")
   591	            return True
   592	            
   593	        except Exception as e:
   594	            print(f"[-] Form submission failed: {e}")
   595	            if hasattr(e, 'response') and e.response is not None:
   596	                print(f"[-] Response status: {e.response.status_code}")
   597	            return False
   598	    
   599	    def submit_wiz_batchexecute(self, rpcid, inner_data_array, source_path):
   600	        """
$ view /workspace/browser.py
Here's the result of running `cat -n` on /workspace/browser.py:
   600	        """
   601	        Submit form data using Google's batchexecute RPC protocol.
   602	        
   603	        Args:
   604	            rpcid: The RPC ID (e.g., 'MjyMj' for name submission)
   605	            inner_data_array: Python list representing the form data structure
   606	            source_path: The source path (e.g., '/lifecycle/steps/signup/name')
   607	        """
   608	        from urllib.parse import urlparse, parse_qs
   609	        import re
   610	        
   611	        # Extract tokens from current page URL and HTML using regex (more reliable than JS)
   612	        wiz_tokens = self.extract_wiz_data().get('tokens', {})
   613	        
   614	        # Get TL and dsh from current URL if not in wiz_tokens
   615	        parsed_url = urlparse(self.current_url) if self.current_url else None
   616	        url_params = parse_qs(parsed_url.query) if parsed_url else {}
   617	        
   618	        tl = wiz_tokens.get('TL') or url_params.get('TL', [None])[0]
   619	        dsh = wiz_tokens.get('dsh') or url_params.get('dsh', [None])[0]
   620	        
   621	        # Extract SNlM0e (at token) directly from HTML using regex
   622	        snlm0e = wiz_tokens.get('SNlM0e')
   623	        if not snlm0e and self.current_html:
   624	            # Pattern: "SNlM0e":"value" or data-at="value"
   625	            match = re.search(r'"SNlM0e"\s*:\s*"([^"]+)"', self.current_html)
   626	            if match:
   627	                snlm0e = match.group(1)
   628	        
   629	        # f.sid is a client-generated session ID - generate one if not available
   630	        f_sid = wiz_tokens.get('f_sid')
   631	        if not f_sid:
   632	            import random
   633	            f_sid = str(random.randint(100000000000000000, 999999999999999999))
   634	        
   635	        # Build label - extract from page or use default
   636	        bl = wiz_tokens.get('bl')
   637	        if not bl and self.current_html:
   638	            # Try to extract from script URLs
   639	            bl_match = re.search(r'/_/js/[^/]+/k=([^/]+)/', self.current_html)
   640	            if bl_match:
   641	                bl = f"boq_identity-account-creation-evolution-ui_{bl_match.group(1)}"
   642	        
   643	        if not bl:
   644	            bl = 'boq_identity-account-creation-evolution-ui_20260512.06_p0'
   645	        
   646	        if not tl or not snlm0e:
   647	            print(f"ERROR: Missing required tokens. TL={tl}, SNlM0e={snlm0e}")
   648	            # Debug: show what we found
   649	            print(f"wiz_tokens keys: {list(wiz_tokens.keys())}")
   650	            if self.current_html:
   651	                has_snlm0e = bool(re.search(r'SNlM0e', self.current_html))
   652	                print(f"HTML contains SNlM0e reference: {has_snlm0e}")
   653	            return None
   654	        
   655	        # Construct the inner JSON string
   656	        inner_json_str = json.dumps(inner_data_array, separators=(',', ':'))
   657	        
   658	        # Construct f.req parameter: [[[rpcid, inner_json, null, "generic"]]]
   659	        f_req_data = [[[rpcid, inner_json_str, None, "generic"]]]
   660	        f_req_str = json.dumps(f_req_data, separators=(',', ':'))
   661	        
   662	        # Build URL parameters
   663	        from urllib.parse import urlencode
   664	        url_params = {
   665	            'rpcids': rpcid,
   666	            'source-path': source_path,
   667	            'f.sid': f_sid,
   668	            'bl': bl,
   669	            'hl': 'en-US',
   670	            'TL': tl,
   671	            '_reqid': '68453',
   672	            'rt': 'c'
   673	        }
   674	        
   675	        # Build POST data
   676	        post_data = {
   677	            'f.req': f_req_str,
   678	            'at': snlm0e,
   679	        }
   680	        
   681	        # Construct full URL
   682	        base_url = 'https://accounts.google.com'
   683	        endpoint = '/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute'
   684	        full_url = f"{base_url}{endpoint}?{urlencode(url_params)}"
   685	        
   686	        # Set headers
   687	        headers = {
   688	            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
   689	            'Origin': 'https://accounts.google.com',
   690	            'Referer': f'https://accounts.google.com{source_path}',
   691	            'X-Same-Origin': '1',
   692	        }
   693	        
   694	        print(f"\n=== SUBMITTING BATCHEXECUTE RPC ===")
   695	        print(f"URL: {full_url}")
   696	        print(f"f.req: {f_req_str[:200]}...")
   697	        print(f"Tokens: TL={tl[:20]}..., f.sid={f_sid}, at={snlm0e[:20]}...")
   698	        
   699	        # Make the request
   700	        try:
   701	            response = self.session.post(full_url, data=post_data, headers=headers)
   702	            self.last_response = response
   703	            
   704	            # Parse response - Google uses a line-delimited format:
   705	            # length\njson_data_of-that-length\nlength\njson_data...
   706	            resp_text = response.text
   707	            if resp_text.startswith(")]}'"):
   708	                resp_text = resp_text[4:]
   709	            
   710	            # Try to parse as line-delimited JSON (common Google format)
   711	            lines = resp_text.strip().split('\n')
   712	            parsed_items = []
   713	            i = 0
   714	            while i < len(lines):
   715	                line = lines[i].strip()
   716	                if line.isdigit():
   717	                    # Next line(s) contain JSON of that length
   718	                    length = int(line)
   719	                    json_str = ''
   720	                    i += 1
   721	                    # Accumulate characters (not counting newlines) until we reach the specified length
   722	                    char_count = 0
   723	                    while i < len(lines) and char_count < length:
   724	                        segment = lines[i]
   725	                        json_str += segment
   726	                        char_count += len(segment)
   727	                        if char_count < length:
   728	                            json_str += '\n'  # Preserve newline within JSON
   729	                        i += 1
   730	                    
   731	                    try:
   732	                        parsed_items.append(json.loads(json_str))
   733	                    except json.JSONDecodeError as e:
   734	                        print(f"Failed to parse segment at position {i}: {e}")
   735	                        print(f"Expected length: {length}, Got: {char_count} chars")
   736	                        print(f"JSON preview: {json_str[:100]}...")
   737	                elif line:
   738	                    # Try parsing directly (fallback for non-prefixed JSON)
   739	                    try:
   740	                        parsed_items.append(json.loads(line))
   741	                    except:
   742	                        pass
   743	                    i += 1
   744	                else:
   745	                    i += 1
   746	            
   747	            if parsed_items:
   748	                print(f"\nResponse parsed successfully:")
   749	                print(f"Status: {response.status_code}")
   750	                print(f"Parsed {len(parsed_items)} items")
   751	                
   752	                for item in parsed_items:
   753	                    if isinstance(item, list) and len(item) > 1:
   754	                        if item[0] == 'wrb.fr':
   755	                            result = item[2] if len(item) > 2 else 'No data'
   756	                            print(f"RPC Result: {result}")
   757	                            # Check for error codes - [3] means validation error
   758	                            if len(item) > 5 and isinstance(item[5], list):
   759	                                print(f"Error indicators: {item[5]}")
   760	                                if 3 in item[5]:
   761	                                    print("WARNING: Error code 3 indicates validation failure!")
   762	                        elif item[0] == 'di':
   763	                            print(f"Debug info: {item}")
   764	                        elif item[0] == 'af.httprm':
   765	                            print(f"HTTP Params: {item}")
   766	                
   767	                # Check if we got redirected or have new page content
   768	                next_url = None
   769	                for item in parsed_items:
   770	                    if isinstance(item, list):
   771	                        # Look for wrb.fr response which contains next page info
   772	                        if len(item) > 2 and item[0] == 'wrb.fr':
   773	                            result_data = item[2]
   774	                            # Parse the nested structure [[["steps/signup/birthdaygender"]]]
   775	                            if isinstance(result_data, list) and len(result_data) > 0:
   776	                                first_elem = result_data[0]
   777	                                if isinstance(first_elem, list) and len(first_elem) > 0:
   778	                                    url_path = first_elem[0]
   779	                                    if isinstance(url_path, str) and url_path.startswith('steps/'):
   780	                                        next_url = f"https://accounts.google.com/lifecycle/{url_path}"
   781	                                        print(f"✓ SUCCESS: Next page detected: {next_url}")
   782	                        # Also check for string URLs directly
   783	                        for elem in item:
   784	                            if isinstance(elem, str) and elem.startswith('steps/') and not next_url:
   785	                                next_url = f"https://accounts.google.com/lifecycle/{elem}"
   786	                                print(f"✓ Next page: {next_url}")
   787	                
   788	                # Auto-navigate to next page if found
   789	                if next_url:
   790	                    print(f"✓ SUCCESS: Next page detected: {next_url}")
   791	                    print(f"[*] Automatically navigating to: {next_url}")
   792	                    self.pending_form_data = {}  # Clear form data
   793	                    return self.fetch(next_url)
   794	                
   795	                # Fallback: Check response text directly for URL pattern
   796	                if 'steps/signup/birthdaygender' in resp_text:
   797	                    next_url = "https://accounts.google.com/lifecycle/steps/signup/birthdaygender"
   798	                    # Preserve dsh parameter from current URL
   799	                    if dsh and '?' not in next_url:
   800	                        next_url += f"?dsh={dsh}"
   801	                    elif not dsh and parsed_url and 'dsh' in url_params:
   802	                        next_url += f"?dsh={url_params['dsh'][0]}"
   803	                    print(f"✓ SUCCESS: Found birthdaygender path in response")
   804	                    print(f"[*] Navigating to: {next_url}")
   805	                    self.pending_form_data = {}
   806	                    return self.fetch(next_url)
   807	
   808	                self.soup = BeautifulSoup(response.text, 'html.parser')
   809	                return response
   810	            else:
   811	                print(f"Could not parse any valid JSON from response")
   812	                self.soup = BeautifulSoup(response.text, 'html.parser')
   813	                return response
   814	                
   815	        except Exception as e:
   816	            print(f"Request failed: {e}")
   817	            return None
   818	    
   819	    def submit_name_form(self, first_name, last_name):
   820	        """
   821	        Submit the name form using the batchexecute protocol.
   822	        Based on HAR analysis, use RPC ID 'E815hb' with flat array format:
   823	        [firstName, lastName, null, null, null, [], null, 1]
   824	        """
   825	        # Construct the inner data array - FLAT structure as per HAR
   826	        inner_data = [
   827	            first_name,       # Index 0: firstName
   828	            last_name,        # Index 1: lastName
   829	            None,             # Index 2: middleName
   830	            None,             # Index 3: fullName
   831	            None,             # Index 4: prefix
   832	            [],               # Index 5: empty array (NOT null!)
   833	            None,             # Index 6: unknown
   834	            1                 # Index 7: flag
   835	        ]
   836	        
   837	        return self.submit_wiz_batchexecute(
   838	            rpcid='E815hb',
   839	            inner_data_array=inner_data,
   840	            source_path='/lifecycle/steps/signup/name'
   841	        )
   842	
   843	    def submit_wiz_form(self, form):
   844	        """Submit a WIZ-driven form using JavaScript"""
   845	        print("[*] Submitting WIZ-driven form...")
   846	        
   847	        # Get form data
   848	        form_data = getattr(self, 'pending_form_data', {})
   849	        tokens = form.get('tokens', {})
   850	        
   851	        # Build JavaScript for form submission
   852	        script = '''
   853	        const fs = require('fs');
   854	        const path = process.argv[2];
   855	        const html = fs.readFileSync(path, 'utf-8');
   856	        
   857	        // Extract the actual submission endpoint from WIZ data
   858	        const wizMatch = html.match(/window\\._WIZ_global_data\\s*=\\s*({[\\s\\S]*?});/);
   859	        
   860	        let submitUrl = "''' + self.current_url + '''";
   861	        let additionalParams = {};
   862	        
   863	        if (wizMatch) {
   864	            try {
   865	                const wizData = JSON.parse(wizMatch[1]);
   866	                
   867	                // Look for nextPageUrl or action URLs
   868	                if (wizData.nextPageUrl) {
   869	                    submitUrl = wizData.nextPageUrl;
   870	                }
   871	                
   872	                // Search for RPC endpoints
   873	                function findRpcEndpoints(obj) {
   874	                    if (Array.isArray(obj)) {
   875	                        for (let item of obj) {
   876	                            if (typeof item === 'string' && item.includes('/signup/') && item.includes('/webname')) {
   877	                                submitUrl = 'https://accounts.google.com' + item;
   878	                            }
   879	                            findRpcEndpoints(item);
   880	                        }
   881	                    }
   882	                }
   883	                findRpcEndpoints(wizData);
   884	                
   885	                // Extract additional required parameters
   886	                if (wizData.TL) additionalParams.TL = wizData.TL;
   887	                if (wizData.dsh) additionalParams.dsh = wizData.dsh;
   888	            } catch (e) {
   889	                console.error("Error parsing WIZ data:", e);
   890	            }
   891	        }
   892	        
   893	        // Prepare the payload
   894	        const payload = {
   895	            url: submitUrl,
   896	            params: additionalParams,
   897	            formData: ''' + json.dumps(form_data) + ''',
   898	            tokens: ''' + json.dumps(tokens) + '''
   899	        };
   900	        
   901	        console.log(JSON.stringify(payload));
   902	        '''
   903	        
   904	        result = self.execute_js(script)
   905	        if not result:
   906	            print("[-] Failed to prepare WIZ form submission")
   907	            return False
   908	        
   909	        submit_url = result.get('url', self.current_url)
   910	        additional_params = result.get('params', {})
   911	        form_payload = result.get('formData', {})
   912	        tokens = result.get('tokens', {})
   913	        
   914	        # Merge all parameters
   915	        form_payload.update(additional_params)
   916	        form_payload.update(tokens)
   917	        
   918	        print(f"[*] Submitting to: {submit_url}")
   919	        print(f"[*] Payload: {form_payload}")
   920	        
   921	        try:
   922	            # Try different content types that Google might expect
   923	            headers = {
   924	                'Content-Type': 'application/x-www-form-urlencoded',
   925	                'X-Same-Origin': '1',
   926	            }
   927	            
   928	            response = self.session.post(
   929	                submit_url,
   930	                data=form_payload,
   931	                headers=headers,
   932	                allow_redirects=True
   933	            )
   934	            
   935	            # Check if we got redirected to the next page
   936	            if response.status_code in [200, 302, 303]:
   937	                self.current_url = response.url
   938	                self.current_html = response.text
   939	                self.current_soup = BeautifulSoup(self.current_html, 'html.parser')
   940	                
   941	                print(f"[+] Submission successful, now at: {self.current_url}")
   942	                
   943	                # Check if we reached the username page (page 3)
   944	                if 'username' in self.current_html.lower() or 'choose your username' in self.current_html.lower():
   945	                    print("[+] SUCCESS: Reached username selection page (Page 3)!")
   946	                
   947	                return True
   948	            else:
   949	                print(f"[-] Unexpected status code: {response.status_code}")
   950	                print(f"[-] Response: {response.text[:500]}")
   951	                return False
   952	                
   953	        except Exception as e:
   954	            print(f"[-] WIZ form submission failed: {e}")
   955	            return False
   956	    
   957	    def click_link(self, text_or_index):
   958	        """Click a link by text or index"""
   959	        links = self.get_links()
   960	        
   961	        target_link = None
   962	        if isinstance(text_or_index, int):
   963	            if text_or_index < len(links):
   964	                target_link = links[text_or_index]
   965	        else:
   966	            for link in links:
   967	                if text_or_index.lower() in link['text'].lower():
   968	                    target_link = link
   969	                    break
   970	        
   971	        if not target_link:
   972	            print(f"[-] Link not found: {text_or_index}")
   973	            return False
   974	        
   975	        href = target_link['href']
   976	        if not href.startswith('http'):
   977	            href = urljoin(self.current_url, href)
   978	        
   979	        print(f"[*] Clicking link: {target_link['text']} -> {href}")
   980	        return self.fetch(href)
   981	    
   982	    def click_button(self, text_or_index):
   983	        """Click a button by text or index"""
   984	        if not self.current_soup:
   985	            return False
   986	        
   987	        buttons = self.current_soup.find_all('button')
   988	        inputs = self.current_soup.find_all('input', {'type': 'submit'})
   989	        all_buttons = buttons + inputs
   990	        
   991	        target_button = None
   992	        if isinstance(text_or_index, int):
   993	            if text_or_index < len(all_buttons):
   994	                target_button = all_buttons[text_or_index]
   995	        else:
   996	            for button in all_buttons:
   997	                btn_text = button.get_text(strip=True) or button.get('value', '')
   998	                if text_or_index.lower() in btn_text.lower():
   999	                    target_button = button
  1000	                    break
  1001	        
  1002	        if not target_button:
  1003	            print(f"[-] Button not found: {text_or_index}")
  1004	            # Try to find by jsaction attribute (Google's way)
  1005	            for elem in self.current_soup.find_all(attrs={'jsaction': True}):
  1006	                jsaction = elem.get('jsaction', '')
  1007	                if 'click' in jsaction.lower():
  1008	                    print(f"[*] Found element with jsaction: {jsaction}")
  1009	                    # Try to extract URL from onclick or data attributes
  1010	                    return self.handle_js_action(elem)
  1011	            
  1012	            # Check for span inside button with the text (Google's pattern)
  1013	            for button in buttons:
  1014	                spans = button.find_all('span')
  1015	                for span in spans:
  1016	                    span_text = span.get_text(strip=True)
  1017	                    if text_or_index.lower() in span_text.lower():
  1018	                        target_button = button
  1019	                        print(f"[*] Found button via span: {span_text}")
  1020	                        break
  1021	                if target_button:
  1022	                    break
  1023	            
  1024	            if not target_button:
  1025	                return False
  1026	        
  1027	        # Check if button has a form action
  1028	        form = target_button.find_parent('form')
  1029	        if form:
  1030	            action = form.get('action', '')
  1031	            if action:
  1032	                if not action.startswith('http'):
  1033	                    action = urljoin(self.current_url, action)
  1034	                return self.fetch(action)
  1035	        
  1036	        # Check for jsaction attribute
  1037	        jsaction = target_button.get('jsaction', '')
  1038	        if jsaction:
  1039	            return self.handle_js_action(target_button)
  1040	        
  1041	        # For Google signup button, construct the URL manually
  1042	        if 'Create account' in target_button.get_text():
  1043	            # Extract dsh from current URL
  1044	            from urllib.parse import parse_qs, urlparse
  1045	            parsed = urlparse(self.current_url)
  1046	            params = parse_qs(parsed.query)
  1047	            dsh = params.get('dsh', [''])[0]
  1048	            
  1049	            # Construct signup URL (correct endpoint is /signup not /signup/v2/webname)
  1050	            signup_url = f"https://accounts.google.com/signup?dsh={dsh}&flowEntry=SignUp&flowName=GlifWebSignIn"
  1051	            print(f"[*] Navigating to signup URL: {signup_url}")
  1052	            return self.fetch(signup_url)
  1053	        
  1054	        print(f"[-] Button has no actionable URL")
  1055	        return False
  1056	    
  1057	    def handle_js_action(self, elem):
  1058	        """Handle Google's jsaction attribute"""
  1059	        jsaction = elem.get('jsaction', '')
  1060	        print(f"[*] Processing jsaction: {jsaction}")
  1061	        
  1062	        # For Create Account button, construct the signup URL directly
  1063	        elem_text = elem.get_text(strip=True)
  1064	        if 'Create account' in elem_text:
  1065	            # Extract dsh from current URL
  1066	            from urllib.parse import parse_qs, urlparse
  1067	            parsed = urlparse(self.current_url)
  1068	            params = parse_qs(parsed.query)
  1069	            dsh = params.get('dsh', [''])[0]
  1070	            
  1071	            # Construct signup URL (correct endpoint is /signup not /signup/v2/webname)
  1072	            signup_url = f"https://accounts.google.com/signup?dsh={dsh}&flowEntry=SignUp&flowName=GlifWebSignIn"
  1073	            print(f"[*] Navigating to signup URL: {signup_url}")
  1074	            return self.fetch(signup_url)
  1075	        
  1076	        # Extract WIZ data to find the action URL for other jsaction elements
  1077	        wiz_data = self.extract_wiz_data()
  1078	        
  1079	        if wiz_data.get('actions'):
  1080	            action_url = wiz_data['actions'][0]
  1081	            if not action_url.startswith('http'):
  1082	                action_url = 'https://accounts.google.com' + action_url
  1083	            
  1084	            # Add required parameters
  1085	            tokens = wiz_data.get('tokens', {})
  1086	            params = {}
  1087	            if 'dsh' in tokens:
  1088	                params['dsh'] = tokens['dsh']
  1089	            params['flowEntry'] = 'SignUp'
  1090	            params['flowName'] = 'GlifWebSignIn'
  1091	            
  1092	            full_url = action_url
  1093	            if params:
  1094	                from urllib.parse import urlencode
  1095	                separator = '&' if '?' in action_url else '?'
  1096	                full_url += separator + urlencode(params)
  1097	            
  1098	            print(f"[*] Navigating to WIZ action URL: {full_url}")
  1099	            return self.fetch(full_url)
  1100	        
  1101	        print("[-] Could not determine action from jsaction")
  1102	        return False
  1103	    
  1104	    def render_page(self):
  1105	        """Render the current page content"""
  1106	        if not self.current_soup:
  1107	            print("[-] No page loaded")
  1108	            return
  1109	        
  1110	        print("\n" + "="*60)
  1111	        print(f"Current URL: {self.current_url}")
  1112	        print("="*60)
  1113	        
  1114	        # Show title
  1115	        title = self.current_soup.find('title')
  1116	        if title:
  1117	            print(f"\nTitle: {title.get_text(strip=True)}")
  1118	        
  1119	        # Show forms
  1120	        forms = self.get_forms()
  1121	        if forms:
  1122	            print(f"\nForms found: {len(forms)}")
  1123	            for i, form in enumerate(forms):
  1124	                print(f"\n  Form {i}:")
  1125	                print(f"    Action: {form.get('action', 'N/A')}")
  1126	                print(f"    Method: {form.get('method', 'N/A')}")
  1127	                print(f"    WIZ-driven: {form.get('wiz_driven', False)}")
  1128	                if form.get('inputs'):
  1129	                    print(f"    Inputs:")
  1130	                    for inp in form['inputs']:
  1131	                        print(f"      - {inp.get('name')} ({inp.get('type')})")
  1132	        
  1133	        # Show links
  1134	        links = self.get_links()
  1135	        if links:
  1136	            print(f"\nLinks found: {len(links)}")
  1137	            for i, link in enumerate(links[:10]):  # Show first 10
  1138	                print(f"  [{i}] {link['text'][:50]} -> {link['href'][:60]}")
  1139	            if len(links) > 10:
  1140	                print(f"  ... and {len(links) - 10} more")
  1141	        
  1142	        print("="*60 + "\n")
  1143	
  1144	
  1145	def main():
  1146	    """Main entry point for testing"""
  1147	    browser = Browser()
  1148	    
  1149	    # Test Google signup flow
  1150	    print("=== Testing Google Signup Flow ===\n")
  1151	    
  1152	    # Step 1: Go to sign-in page
  1153	    browser.fetch("https://accounts.google.com/signin")
  1154	    browser.render_page()
  1155	    
  1156	    # Step 2: Click "Create account"
  1157	    if browser.click_button("Create account"):
  1158	        browser.render_page()
  1159	        
  1160	        # Step 3: Fill in name and submit using HAR-matched RPC
  1161	        if browser.fill_form(0, {'firstName': 'steve', 'lastName': 'boils'}):
  1162	            print("[*] Submitting name form via HAR-matched RPC...")
  1163	            response = browser.submit_name_form('steve', 'boils')
  1164	            if response:
  1165	                browser.render_page()
  1166	                if 'username' in browser.current_url.lower() or 'name' not in browser.current_url.lower():
  1167	                    print("\n✓ SUCCESS: Moved past name page!")
  1168	                    print(f"Current URL: {browser.current_url}")
  1169	                else:
  1170	                    print("\n✗ Still on name page")
  1171	                    print(f"Current URL: {browser.current_url}")
  1172	            else:
  1173	                print("[!] submit_name_form returned None/False")
  1174	        if browser.fill_form(0, {'firstName': 'steve', 'lastName': 'boils'}):
  1175	            if browser.submit_form(0):
  1176	                browser.render_page()
  1177	                
  1178	                # Check if we reached page 3 (username selection)
  1179	                if 'username' in browser.current_html.lower():
  1180	                    print("\n✓ SUCCESS: Reached username selection page!")
  1181	                else:
  1182	                    print("\n✗ Did not reach username page yet")
  1183	
  1184	
  1185	if __name__ == "__main__":
  1186	    main()
