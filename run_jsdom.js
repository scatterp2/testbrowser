const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');
// Read HTML and JS files
const htmlPath = process.argv[2];
const jsPath = process.argv[3];
if (!htmlPath || !jsPath) {
    console.error('Usage: node run_jsdom.js <html_file> <js_file>');
    process.exit(1);
}
const html = fs.readFileSync(htmlPath, 'utf-8');
const jsCode = fs.readFileSync(jsPath, 'utf-8');
// Create JSDOM instance with comprehensive browser API mocks
const dom = new JSDOM(html, {
    url: 'https://accounts.google.com',
    contentType: 'text/html',
    includeNodeLocations: true,
    storageQuota: 10000000,
    pretendToBeVisual: true,
    resources: 'usable',
    runScripts: 'dangerously',
    beforeParse(window) {
        // Mock Performance API
        window.performance = {
            now: () => Date.now(),
            getEntriesByType: (type) => {
                if (type === 'navigation') {
                    return [{
                        type: 'navigate',
                        startTime: 0,
                        duration: 100,
                        name: window.location.href,
                        entryType: 'navigation'
                    }];
                }
                if (type === 'resource') {
                    return [];
                }
                if (type === 'paint') {
                    return [];
                }
                return [];
            },
            getEntriesByName: (name) => [],
            getEntries: () => [],
            mark: (name) => {},
            measure: (name, startMark, endMark) => {},
            clearMarks: (name) => {},
            clearMeasures: (name) => {},
            timing: {
                navigationStart: Date.now(),
                unloadEventStart: 0,
                unloadEventEnd: 0,
                redirectStart: 0,
                redirectEnd: 0,
                fetchStart: Date.now(),
                domainLookupStart: 0,
                domainLookupEnd: 0,
                connectStart: 0,
                connectEnd: 0,
                secureConnectionStart: 0,
                requestStart: 0,
                responseStart: 0,
                responseEnd: 0,
                domLoading: 0,
                domInteractive: 0,
                domContentLoadedEventStart: 0,
                domContentLoadedEventEnd: 0,
                domComplete: 0,
                loadEventStart: 0,
                loadEventEnd: 0
            },
            navigation: {
                type: 0,
                redirectCount: 0
            }
        };
        // Mock ResizeObserver
        window.ResizeObserver = class ResizeObserver {
            constructor(callback) {
                this.callback = callback;
            }
            observe(target) {}
            unobserve(target) {}
            disconnect() {}
        };
        // Mock IntersectionObserver
        window.IntersectionObserver = class IntersectionObserver {
            constructor(callback, options) {
                this.callback = callback;
                this.options = options;
            }
            observe(target) {}
            unobserve(target) {}
            disconnect() {}
        };
        // Mock crypto
        window.crypto = {
            getRandomValues: (array) => {
                for (let i = 0; i < array.length; i++) {
                    array[i] = Math.floor(Math.random() * 256);
                }
                return array;
            },
            subtle: {
                digest: async () => new ArrayBuffer(32),
                encrypt: async () => new ArrayBuffer(32),
                decrypt: async () => new ArrayBuffer(32)
            }
        };
        // Mock Storage APIs
        const storageData = {};
        window.localStorage = {
            getItem: (key) => storageData[key] || null,
            setItem: (key, value) => { storageData[key] = value; },
            removeItem: (key) => { delete storageData[key]; },
            clear: () => { Object.keys(storageData).forEach(k => delete storageData[k]); },
            length: 0,
            key: (index) => Object.keys(storageData)[index] || null
        };
        window.sessionStorage = { ...window.localStorage };
        // Mock requestAnimationFrame
        window.requestAnimationFrame = (callback) => {
            return setTimeout(() => callback(Date.now()), 16);
        };
        window.cancelAnimationFrame = (id) => clearTimeout(id);
        // Mock matchMedia
        window.matchMedia = (query) => ({
            matches: false,
            media: query,
            onchange: null,
            addListener: (fn) => {},
            removeListener: (fn) => {},
            addEventListener: (event, fn) => {},
            removeEventListener: (event, fn) => {},
            dispatchEvent: (event) => true
        });
        // Mock getComputedStyle
        const originalGetComputedStyle = window.getComputedStyle;
        window.getComputedStyle = (elem) => {
            const style = originalGetComputedStyle(elem);
            // Add missing properties
            style.getPropertyValue = (prop) => style[prop] || '';
            return style;
        };
        // Mock scrollTo/scroll
        window.scrollTo = () => {};
        window.scroll = () => {};
        window.scrollBy = () => {};
        // Element scroll methods
        const origElement = window.Element.prototype;
        origElement.scrollTo = function() {};
        origElement.scroll = function() {};
        origElement.scrollBy = function() {};
        origElement.scrollIntoView = function() {};
        // Mock getBoundingClientRect to return reasonable values
        const origGetBoundingClientRect = window.Element.prototype.getBoundingClientRect;
        window.Element.prototype.getBoundingClientRect = function() {
            return {
                top: 0,
                left: 0,
                bottom: 100,
                right: 100,
                width: 100,
                height: 100,
                x: 0,
                y: 0,
                toJSON: function() { return JSON.stringify(this); }
            };
        };
        // Mock clientWidth/clientHeight
        Object.defineProperty(window.HTMLElement.prototype, 'clientWidth', {
            get: function() { return 100; }
        });
        Object.defineProperty(window.HTMLElement.prototype, 'clientHeight', {
            get: function() { return 100; }
        });
        Object.defineProperty(window.HTMLElement.prototype, 'offsetWidth', {
            get: function() { return 100; }
        });
        Object.defineProperty(window.HTMLElement.prototype, 'offsetHeight', {
            get: function() { return 100; }
        });
        Object.defineProperty(window.HTMLElement.prototype, 'scrollWidth', {
            get: function() { return 100; }
        });
        Object.defineProperty(window.HTMLElement.prototype, 'scrollHeight', {
            get: function() { return 100; }
        });
        // Mock innerWidth/innerHeight
        Object.defineProperty(window, 'innerWidth', {
            get: function() { return 1920; }
        });
        Object.defineProperty(window, 'innerHeight', {
            get: function() { return 1080; }
        });
        Object.defineProperty(window, 'outerWidth', {
            get: function() { return 1920; }
        });
        Object.defineProperty(window, 'outerHeight', {
            get: function() { return 1080; }
        });
        // Mock devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', {
            get: function() { return 1; }
        });
        // Mock navigator properties
        const origNavigator = window.navigator;
        window.navigator = {
            ...origNavigator,
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            platform: 'Win32',
            language: 'en-US',
            languages: ['en-US', 'en'],
            cookieEnabled: true,
            onLine: true,
            webdriver: false,
            hardwareConcurrency: 8,
            deviceMemory: 8,
            maxTouchPoints: 0,
            connection: {
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            }
        };
        // Mock document properties
        Object.defineProperty(window.document, 'documentMode', {
            get: function() { return 11; }
        });
        // Mock MutationObserver
        window.MutationObserver = class MutationObserver {
            constructor(callback) {
                this.callback = callback;
            }
            observe(target, options) {}
            disconnect() {}
            takeRecords() { return []; }
        };
        // Mock Promise.resolve/reject for microtasks
        if (!Promise.resolve.toString().includes('[native code]')) {
            // Already native, no need to mock
        }
        // Mock fetch
        window.fetch = (url, options) => {
            return Promise.reject(new Error('Network requests disabled in jsdom'));
        };
        // Mock XMLHttpRequest
        window.XMLHttpRequest = class XMLHttpRequest {
            open() {}
            send() {}
            abort() {}
            setRequestHeader() {}
            getResponseHeader() { return null; }
            getAllResponseHeaders() { return ''; }
            readyState = 0;
            status = 0;
            statusText = '';
            response = '';
            responseText = '';
            responseXML = null;
            onreadystatechange = null;
            timeout = 0;
            withCredentials = false;
        };
        // Mock History API
        window.history = {
            pushState: (state, title, url) => {
                if (url) window.location.href = url;
            },
            replaceState: (state, title, url) => {
                if (url) window.location.href = url;
            },
            go: (delta) => {},
            back: () => {},
            forward: () => {},
            state: null,
            length: 1
        };
        // Mock location reload/replace
        const origLocation = window.location;
        window.location.reload = () => {};
        window.location.replace = (url) => {
            window.location.href = url;
        };
        // Mock setTimeout/setInterval to be synchronous for testing
        // (keeping them async but ensuring they work)
        // Mock CustomEvent
        window.CustomEvent = class CustomEvent extends Event {
            constructor(type, params) {
                params = params || { bubbles: false, cancelable: false, detail: undefined };
                super(type, params);
                this.detail = params.detail;
            }
        };
        // Mock DOMParser
        window.DOMParser = class DOMParser {
            parseFromString(string, type) {
                return new JSDOM(string).window.document;
            }
        };
        // Mock URL.createObjectURL/revokeObjectURL
        window.URL.createObjectURL = (obj) => 'blob:http://example.com/' + Math.random();
        window.URL.revokeObjectURL = (url) => {};
        // Mock getSelection
        window.getSelection = () => ({
            toString: () => '',
            rangeCount: 0,
            getRangeAt: (i) => null,
            addRange: (range) => {},
            removeRange: (range) => {},
            removeAllRanges: () => {},
            empty: () => {},
            collapse: () => {},
            setPosition: () => {},
            extend: () => {},
            isCollapsed: true,
            type: 'None',
            anchorNode: null,
            anchorOffset: 0,
            focusNode: null,
            focusOffset: 0
        });
        // Mock window.name
        window.name = '';
        // Mock window.frames
        window.frames = [];
        window.length = 0;
        window.top = window;
        window.parent = window;
        window.self = window;
        // Mock postMessage
        window.postMessage = (message, targetOrigin, transfer) => {};
        // Mock addEventListener/removeEventListener for window
        // (JSDOM provides these, but ensure they exist)
        // Mock screen
        window.screen = {
            width: 1920,
            height: 1080,
            availWidth: 1920,
            availHeight: 1080,
            colorDepth: 24,
            pixelDepth: 24,
            orientation: {
                type: 'landscape-primary',
                angle: 0,
                onchange: null
            }
        };
        // Mock visualViewport
        window.visualViewport = {
            width: 1920,
            height: 1080,
            offsetLeft: 0,
            offsetTop: 0,
            pageLeft: 0,
            pageTop: 0,
            scale: 1,
            clientWidth: 1920,
            clientHeight: 1080
        };
        // Mock CSS
        window.CSS = {
            escape: (str) => str.replace(/[\\"]/g, '\\$&'),
            supports: (property, value) => true
        };
        // Mock NamedNodeMap for attributes
        // (JSDOM handles this)
        // Mock WindowProperties
        // (JSDOM handles this)
    }
});
const window = dom.window;
const document = window.document;
// Wait for any async initialization
setTimeout(() => {
    try {
        // Execute the user's JavaScript code
        const vm = require('vm');
        const context = vm.createContext({
            window: window,
            document: document,
            console: console,
            require: require,
            process: process,  // Add process object
            __jsdom: true,
            performance: window.performance,
            localStorage: window.localStorage,
            sessionStorage: window.sessionStorage,
            navigator: window.navigator,
            location: window.location,
            history: window.history,
            screen: window.screen,
            crypto: window.crypto,
            CustomEvent: window.CustomEvent,
            Event: window.Event,
            MouseEvent: window.MouseEvent,
            KeyboardEvent: window.KeyboardEvent,
            FocusEvent: window.FocusEvent,
            InputEvent: window.InputEvent,
            DOMParser: window.DOMParser,
            XMLSerializer: window.XMLSerializer,
            Node: window.Node,
            Element: window.Element,
            HTMLElement: window.HTMLElement,
            Document: window.Document,
            Blob: window.Blob,
            File: window.File,
            FileReader: window.FileReader,
            FormData: window.FormData,
            URL: window.URL,
            URLSearchParams: window.URLSearchParams,
            Request: window.Request,
            Response: window.Response,
            Headers: window.Headers,
            AbortController: window.AbortController,
            AbortSignal: window.AbortSignal,
            TextEncoder: window.TextEncoder,
            TextDecoder: window.TextDecoder,
            atob: window.atob,
            btoa: window.btoa,
            setTimeout: setTimeout,
            setInterval: setInterval,
            clearTimeout: clearTimeout,
            clearInterval: clearInterval,
            requestAnimationFrame: window.requestAnimationFrame,
            cancelAnimationFrame: window.cancelAnimationFrame,
            Promise: Promise,
            Map: Map,
            Set: Set,
            WeakMap: WeakMap,
            WeakSet: WeakSet,
            Symbol: Symbol,
            Proxy: Proxy,
            Reflect: Reflect,
            Array: Array,
            Object: Object,
            String: String,
            Number: Number,
            Boolean: Boolean,
            Date: Date,
            RegExp: RegExp,
            Error: Error,
            TypeError: TypeError,
            SyntaxError: SyntaxError,
            ReferenceError: ReferenceError,
            JSON: JSON,
            Math: Math,
            Infinity: Infinity,
            NaN: NaN,
            undefined: undefined,
            null: null
        });
        // Run the JavaScript code
        const result = vm.runInContext(jsCode, context, {
            filename: 'script.js',
            timeout: 10000
        });
        // Output result as JSON if possible
        if (result !== undefined) {
            try {
                console.log(JSON.stringify(result));
            } catch (e) {
                console.log(JSON.stringify({ result: String(result) }));
            }
        } else {
            // If no explicit result, output current state
            console.log(JSON.stringify({
                url: window.location.href,
                title: document.title,
                forms: Array.from(document.forms).map(f => ({
                    action: f.action,
                    method: f.method,
                    inputs: Array.from(f.elements).map(e => ({
                        name: e.name,
                        type: e.type,
                        value: e.value
                    }))
                })),
                links: Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    text: a.textContent.trim(),
                    href: a.href
                }))
            }));
        }
    } catch (error) {
        console.error(JSON.stringify({ error: error.message, stack: error.stack }));
        process.exit(1);
    }
}, 100);
