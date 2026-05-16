#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { JSDOM, VirtualConsole } = require('jsdom');

function readStdin() {
  return new Promise((resolve) => {
    let html = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { html += chunk; });
    process.stdin.on('end', () => resolve(html));
  });
}

function installBrowserMocks(window, networkLog) {
  Object.defineProperty(window.navigator, 'webdriver', { get: () => false });
  Object.defineProperty(window.navigator, 'plugins', { get: () => [1, 2, 3] });
  Object.defineProperty(window.navigator, 'languages', { get: () => ['en-US', 'en'] });
  Object.defineProperty(window.navigator, 'hardwareConcurrency', { get: () => 8 });
  Object.defineProperty(window.navigator, 'platform', { get: () => 'Win32' });

  window.chrome = {
    loadTimes: () => ({ connectionType: '4g', firstPaintTime: Date.now() / 1000 }),
    csi: () => ({ startE: Date.now(), onloadT: Date.now() }),
    runtime: {},
  };

  window.performance.getEntriesByType = window.performance.getEntriesByType || (() => []);
  window.performance.mark = window.performance.mark || (() => undefined);
  window.performance.measure = window.performance.measure || (() => undefined);

  window.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  window.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } };
  window.MutationObserver = window.MutationObserver || class { observe() {} disconnect() {} takeRecords() { return []; } };

  const store = new Map();
  const storage = {
    getItem: (key) => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => store.set(String(key), String(value)),
    removeItem: (key) => store.delete(String(key)),
    clear: () => store.clear(),
  };
  Object.defineProperty(window, 'localStorage', { value: storage, configurable: true });
  Object.defineProperty(window, 'sessionStorage', { value: storage, configurable: true });

  window.fetch = (url, options = {}) => {
    networkLog.push({ type: 'fetch', url: String(url), method: options.method || 'GET', body: options.body || null });
    return Promise.resolve({
      ok: true,
      status: 204,
      statusText: 'No Content',
      headers: { get: () => null },
      text: () => Promise.resolve(''),
      json: () => Promise.resolve({}),
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    });
  };

  window.XMLHttpRequest = class {
    constructor() {
      this.headers = {};
      this.readyState = 0;
      this.status = 0;
      this.responseText = '';
    }
    open(method, url) {
      this.method = method;
      this.url = url;
      this.readyState = 1;
    }
    setRequestHeader(name, value) { this.headers[name] = value; }
    getResponseHeader() { return null; }
    send(body = null) {
      networkLog.push({ type: 'xhr', url: String(this.url), method: this.method || 'GET', body });
      this.readyState = 4;
      this.status = 204;
      if (this.onreadystatechange) this.onreadystatechange();
      if (this.onload) this.onload({ target: this });
      if (this.onloadend) this.onloadend({ target: this });
    }
  };

  window.innerWidth = 1280;
  window.innerHeight = 720;
  window.screen = { width: 1280, height: 720, availWidth: 1280, availHeight: 720, colorDepth: 24, pixelDepth: 24 };
  window.requestAnimationFrame = (cb) => window.setTimeout(() => cb(Date.now()), 16);
  window.cancelAnimationFrame = (id) => window.clearTimeout(id);
}

async function main() {
  const htmlPath = process.argv[2];
  const userScriptPath = process.argv[3];
  const html = htmlPath ? fs.readFileSync(htmlPath, 'utf8') : await readStdin();
  const networkLog = [];
  const virtualConsole = new VirtualConsole();
  const consoleLog = [];
  virtualConsole.on('log', (message) => consoleLog.push(String(message)));
  virtualConsole.on('error', (message) => consoleLog.push(String(message)));

  const dom = new JSDOM(html, {
    url: process.env.JSDOM_URL || 'https://accounts.google.com/',
    runScripts: 'dangerously',
    resources: 'usable',
    pretendToBeVisual: true,
    virtualConsole,
    beforeParse(window) { installBrowserMocks(window, networkLog); },
  });

  const userResult = {};
  if (userScriptPath) {
    const code = fs.readFileSync(userScriptPath, 'utf8');
    const sandbox = {
      window: dom.window,
      document: dom.window.document,
      result: userResult,
      console: {
        log: (...args) => consoleLog.push(args.map(String).join(' ')),
        error: (...args) => consoleLog.push(args.map(String).join(' ')),
        warn: (...args) => consoleLog.push(args.map(String).join(' ')),
      },
      require,
      process: { ...process, argv: ['node', userScriptPath, htmlPath], exit: (code = 0) => { throw new Error(`user script called process.exit(${code})`); } },
      Buffer,
      setTimeout,
      clearTimeout,
    };
    sandbox.global = sandbox;
    sandbox.__dirname = path.dirname(userScriptPath);
    sandbox.__filename = userScriptPath;
    vm.runInNewContext(code, sandbox, { filename: userScriptPath, timeout: 5000 });
  }

  await new Promise((resolve) => setTimeout(resolve, Number(process.env.JSDOM_SETTLE_MS || 800)));
  console.log(JSON.stringify({
    html: dom.serialize(),
    title: dom.window.document.title,
    result: userResult,
    networkLog,
    consoleLog,
  }));
}

main().catch((error) => {
  console.log(JSON.stringify({ error: error.message, stack: error.stack }));
  process.exitCode = 1;
});
