# testbrowser

A lightweight text-based browser prototype with Python HTTP state, terminal rendering, and a Node/jsdom JavaScript/DOM execution layer. The goal is closer to `w3m-js` than a graphical browser or Browsh: keep the runtime small, but support enough DOM, events, cookies, and JavaScript-driven network behavior to drive modern pages.

## Browser approach

The browser should not be a Google-signup protocol script. Google signup is only the current stress test for DOM + JavaScript behavior. The submit path now prefers a browser-like interaction loop:

1. Load the current HTML into jsdom using the real current URL.
2. Fill controls by semantic labels, names, placeholders, autocomplete, and ARIA text.
3. Click the likely **Next**, **Continue**, **Submit**, **Verify**, or requested button.
4. Capture any `fetch`/`XMLHttpRequest` the page JavaScript emits.
5. Replay that captured request through the Python `requests.Session` so cookies and redirects remain browser-owned.

This keeps WIZ RPC IDs and payload shapes data-driven by the live page JavaScript instead of hard-coded from a HAR.

## Google signup test case

The proving flow is Google account signup, but it is treated as an end-to-end browser scenario:

1. Visit `https://accounts.google.com/signin`.
2. Click **Create account**.
3. Progress through all recognized, completable steps (name, birthday/gender, username, password, terms, etc.).
4. If a phone step appears, submit one random test phone number and then stop at the expected phone/SMS verification block.
5. If a locale or experiment skips phone collection, continue until the next unknown or non-automatable challenge.

The checked-in HAR may be useful while developing, but it is not part of the browser contract and tests should not require it. New coverage should prefer compact synthetic fixtures that verify generic browser behavior and dynamic branches.

## Important files

- `browser.py` — Python session/state, DOM parsing, text rendering, semantic signup-step classification, JS-driven form interaction, and replay of captured JS network requests.
- `run_jsdom.js` — jsdom runner with browser API mocks (`navigator.webdriver=false`, `window.chrome`, observers, storage, `fetch`, and `XMLHttpRequest` logging).
- `test_flow.py` — exploratory live-flow script.
- `test_browser.py` — offline unit tests for dynamic signup-step classification and generic, non-HAR-driven interaction script generation.

## Setup

Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Node dependency from the supplied tarball, when available:

```bash
wget -O jsdom-29.1.1.tgz https://github.com/scatterp2/testbrowser/raw/8eb8f60db2d61b5b35108bbbd063162df93a9953/jsdom-29.1.1.tgz
npm install ./jsdom-29.1.1.tgz
```

If the tarball is unavailable in your environment, use the normal npm dependency path:

```bash
npm install
```

## Checks

```bash
python3 -m unittest test_browser.py
python3 -m py_compile browser.py test_flow.py test_browser.py
node --check run_jsdom.js
git diff --check
```

## Notes

- `run_jsdom.js` intentionally mocks browser-side network APIs. It records attempted `fetch`/XHR calls in `networkLog`; Python decides whether to replay those requests through the browser session.
- PyV8 is worth tracking as a future embedded-V8 backend, but this code path stays on Node/jsdom for now because jsdom supplies the DOM/event surface needed by the current browser tests.
