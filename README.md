# testbrowser

A lightweight text-based browser prototype with Python HTTP state, terminal rendering, and a Node/jsdom JavaScript/DOM execution layer. The goal is closer to `w3m-js` than a full graphical browser or Browsh: keep the runtime small, but support enough DOM and JavaScript behavior to drive modern WIZ-style pages.

## Google signup test case

The current proving flow is Google account signup:

1. Visit `https://accounts.google.com/signin`.
2. Click **Create account**.
3. Open the signup name step.
4. Submit first/last name.
5. Verify the next WIZ lifecycle step is returned.

The checked-in HAR (`accounts.google.com_Archive [26-05-13 19-01-55].har`) is used as protocol documentation. The key finding is that the name page is **not** a normal HTML form submit. It uses Google `batchexecute`:

```text
POST /lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute
rpcids=E815hb
source-path=/lifecycle/steps/signup/name
f.req=[[['E815hb','["steve","boils",null,null,null,[],null,1]',null,'generic']]]
```

The successful response contains the next lifecycle path inside the `wrb.fr` payload:

```text
steps/signup/birthdaygender
```

## Important files

- `browser.py` — Python session/state, DOM parsing, text rendering, WIZ token extraction, and HAR-backed Google signup RPC submission.
- `run_jsdom.js` — jsdom runner with browser API mocks (`navigator.webdriver=false`, `window.chrome`, observers, storage, `fetch`, and `XMLHttpRequest` logging).
- `test_flow.py` — exploratory live-flow script.
- `test_browser.py` — offline tests that validate the checked-in HAR shape and batchexecute response parsing.

## Setup

Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Node dependency:

```bash
wget -O jsdom-29.1.1.tgz https://github.com/scatterp2/testbrowser/raw/8eb8f60db2d61b5b35108bbbd063162df93a9953/jsdom-29.1.1.tgz
npm install ./jsdom-29.1.1.tgz
npm install
```

The `package.json` dependency is pinned to the same jsdom 29.1.1 tarball so a plain `npm install` also installs the project against that browser runtime.

## Checks

```bash
python3 -m unittest test_browser.py
python3 -m py_compile browser.py test_flow.py test_browser.py
node --check run_jsdom.js
```

## Notes

- `run_jsdom.js` intentionally mocks network APIs by default. It records attempted `fetch`/XHR calls in `networkLog` instead of leaking browser-side requests.
- The live Google flow is inherently unstable because tokens and RPC shapes can change. Prefer adding HAR-backed offline tests for every newly supported WIZ step before relying on a live run.
