const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// Read HTML from stdin
let html = '';
process.stdin.setEncoding('utf8');
process.stdin.on('readable', () => {
    let chunk;
    while ((chunk = process.stdin.read()) !== null) {
        html += chunk;
    }
});

process.stdin.on('end', () => {
    if (!html.trim()) {
        console.log(JSON.stringify({ error: "No input provided" }));
        return;
    }

    const dom = new JSDOM(html, {
        url: 'https://accounts.google.com',
        runScripts: "dangerously",
        resources: "usable",
        pretendToBeVisual: true,
        hasFocus: true,
        beforeParse(window) {
            // --- Anti-Detection & API Mocks ---
            
            // Navigator
            Object.defineProperty(window.navigator, 'webdriver', { get: () => false });
            Object.defineProperty(window.navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(window.navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(window.navigator, 'hardwareConcurrency', { get: () => 8 });
            
            // Chrome object (Critical for Google)
            window.chrome = {
                loadTimes: () => ({ connectionType: '4g' }),
                csi: () => ({ startE: Date.now() }),
                runtime: {}
            };

            // Performance API
            window.performance = window.performance || {};
            window.performance.getEntriesByType = window.performance.getEntriesByType || (() => []);
            window.performance.now = window.performance.now || (() => Date.now());
            
            // Observers
            window.ResizeObserver = class { constructor(){} observe(){} unobserve(){} disconnect(){} };
            window.IntersectionObserver = class { constructor(){} observe(){} unobserve(){} disconnect(){} };
            window.MutationObserver = class { constructor(){} observe(){} disconnect(){} takeRecords(){ return []; } };
            
            // Crypto
            window.crypto = window.crypto || {
                getRandomValues: (arr) => {
                    for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256);
                    return arr;
                }
            };
            
            // Storage
            const store = {};
            window.localStorage = {
                getItem: (k) => store[k] || null,
                setItem: (k, v) => { store[k] = v; },
                removeItem: (k) => { delete store[k]; }
            };
            window.sessionStorage = { ...window.localStorage };
            
            // Network Mocks (Prevent external leaks, return empty)
            window.fetch = () => Promise.resolve({
                text: () => Promise.resolve(""),
                json: () => Promise.resolve({}),
                ok: true,
                status: 200
            });
            
            window.XMLHttpRequest = class {
                open() {}
                send() { 
                    if (this.onload) this.onload({ target: { responseText: "", status: 200 } });
                }
                setRequestHeader() {}
                getResponseHeader() { return null; }
            };

            // Dimensions
            window.innerWidth = 1920;
            window.innerHeight = 1080;
            window.screen = { width: 1920, height: 1080, availWidth: 1920, availHeight: 1080 };
            
            // Timing
            window.requestAnimationFrame = (cb) => setTimeout(cb, 16);
        }
    });

    const window = dom.window;
    const document = window.document;

    // Allow scripts to run
    // Wait a bit for async operations
    setTimeout(() => {
        try {
            const result = {
                html: dom.serialize(),
                title: document.title
            };
            console.log(JSON.stringify(result));
        } catch (e) {
            console.log(JSON.stringify({ error: e.message, html: dom.serialize() }));
        }
        process.exit(0);
    }, 500);
});
