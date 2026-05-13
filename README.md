# testbrowser

bellard.org/quickjs/binary_releases/quickjs-linux-i686-2024-01-13.zip 

steps visit https://accounts.google.com/signin
click create an account
click personal
click next
enter first and last name (steven boils) 
click next..
return the data on the next page

Project Context: Lightweight Text-Based Browser with V8/jsdom
Goal: Create a pure Python/Node.js terminal browser that can execute complex JavaScript (specifically Google's WIZ framework) to automate the Google Account signup flow up to Page 3 (Username Selection), without using heavy tools like Selenium or Playwright.
Current State:
Core Architecture:
Backend: Python requests + BeautifulSoup4 for HTTP and static parsing.
JS Engine: Node.js running a custom script (run_jsdom.js) using jsdom to simulate a DOM.
Execution Flow: Python sends HTML to Node -> Node injects mocks, runs JS, serializes modified DOM -> Python parses result.
Key Achievements:
✅ Navigation: Successfully navigates from Google Home -> Sign In -> "Create Account" click.
✅ JS Execution: Successfully executes document.write, dynamic DOM creation, and Google's initial WIZ data parsing.
✅ Anti-Detection Spoofing: Implemented mocks for navigator.webdriver=false, window.chrome, performance.getEntriesByType(), ResizeObserver, and realistic user-agent strings.
✅ Text Rendering: Can render the final DOM state (including JS-generated content) as a text tree in the terminal.
⚠️ The Blocker: The flow stops at Page 2 (Name Input). Clicking "Next" fails (400/405 errors) because Google requires specific RPC-style form submission with obfuscated field names and dynamic tokens that standard HTML form parsing misses.
The Specific Problem to Solve:
Google's Page 2 form does not use standard <form action="...">.
The "Next" button triggers a JavaScript function that:
Reads obfuscated field IDs (e.g., rZHESd instead of firstName) from window.WIZ_global_data.
Constructs a specific payload with tokens (SNlM0e, dsh, et).
Sends an XHR/Fetch request to a dynamic endpoint (e.g., /signup/v1/webname).
Current Failure: The browser attempts a standard POST to the current URL, which Google rejects.
Required Implementation Details (The "Secret Sauce"):
File: run_jsdom.js
Must use jsdom with { runScripts: "dangerously", resources: "usable" }.
Critical Mocks:
navigator.webdriver = false
window.chrome = { loadTimes: ..., csi: ... }
performance.getEntriesByType() must return a valid array (not undefined).
XMLHttpRequest and fetch must be mocked to log requests or route them through Python if needed (though for now, just preventing crashes is key).
ResizeObserver, IntersectionObserver, MutationObserver must be no-op classes.
Output: Must return the serialized HTML after all async tasks (setTimeout/Promises) settle.
File: browser.py
Method fill_and_submit_wiz_form(page_html, field_values):
Instead of looking for <form>, it must execute a JS snippet via Node to parse window.WIZ_global_data.
Parsing Logic: Look for the nested array structure in WIZ_global_data that contains the RPC endpoint URL and the mapping of logical names (firstName) to obfuscated keys (rZHESd).
Token Extraction: Extract SNlM0e (auth token), dsh (data session hash), and et (execution token) from the global data or hidden inputs.
Submission: Construct a POST request to the extracted RPC endpoint with Content-Type: application/x-www-form-urlencoded (or sometimes JSON depending on the specific WIZ version), including the obfuscated keys and tokens.
File: test_flow.py
Sequence:
GET Sign-in URL.
Find "Create account" link/button (handle jsaction clicks).
GET Signup Page 1 (Name).
Call fill_and_submit_wiz_form with {"firstName": "steve", "lastName": "boils"}.
Check response: If successful, it redirects/returns HTML for Page 2 (Username).
Render Page 2.
Dependencies:
Python: requests, beautifulsoup4, lxml.
Node.js: jsdom (installed via npm install jsdom).
System: node and python3 must be in PATH.
Instruction to New AI:
"Recreate the files browser.py, run_jsdom.js, and test_flow.py based on the architecture above. Focus heavily on the fill_and_submit_wiz_form logic in browser.py to parse WIZ_global_data for obfuscated keys and tokens, ensuring run_jsdom.js has all necessary anti-detection mocks so Google's JS doesn't crash or refuse to run. The goal is to successfully POST the name data and receive the Username Selection page HTML.
