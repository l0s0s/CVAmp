import logging

logger = logging.getLogger(__name__)

# Comprehensive JavaScript to mask browser automation across CDP and Playwright
STEALTH_JS = r"""
(() => {
    // 1. Pass the Webdriver Test
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    delete navigator.__proto__.webdriver;

    // 2. Mock window.chrome
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            PlatformOs: {
                MAC: 'mac',
                WIN: 'win',
                ANDROID: 'android',
                CROS: 'cros',
                LINUX: 'linux',
                OPENBSD: 'openbsd'
            },
            PlatformArch: {
                ARM: 'arm',
                X86_32: 'x86-32',
                X86_64: 'x86-64'
            },
            PlatformNaclArch: {
                ARM: 'arm',
                X86_32: 'x86-32',
                X86_64: 'x86-64'
            },
            connect: function() {},
            sendMessage: function() {}
        };
    }
    if (!window.chrome.loadTimes) {
        window.chrome.loadTimes = function() {
            return {
                requestTime: performance.timing.navigationStart / 1000,
                startLoadTime: performance.timing.navigationStart / 1000,
                commitLoadTime: performance.timing.responseStart / 1000,
                finishDocumentLoadTime: performance.timing.domContentLoadedEventEnd / 1000,
                finishLoadTime: performance.timing.loadEventEnd / 1000,
                firstPaintTime: (performance.timing.domInteractive || performance.timing.navigationStart) / 1000,
                firstPaintAfterLoadTime: 0,
                navigationType: 'Other',
                wasFetchedViaSpdy: true,
                wasNpnNegotiated: true,
                npnNegotiatedProtocol: 'h2',
                wasAlternateProtocolAvailable: false,
                connectionInfo: 'h2'
            };
        };
    }
    if (!window.chrome.csi) {
        window.chrome.csi = function() {
            return {
                startE: performance.timing.navigationStart,
                onloadT: performance.timing.domContentLoadedEventEnd,
                pageT: performance.timing.loadEventEnd - performance.timing.navigationStart,
                tran: 15
            };
        };
    }
    if (!window.chrome.app) {
        window.chrome.app = {
            isInstalled: false,
            InstallState: {
                DISABLED: 'disabled',
                INSTALLED: 'installed',
                NOT_INSTALLED: 'not_installed'
            },
            RunningState: {
                CANNOT_RUN: 'cannot_run',
                READY_TO_RUN: 'ready_to_run',
                RUNNING: 'running'
            }
        };
    }

    // 3. Mock navigator.plugins & navigator.mimeTypes
    const fakePlugins = [
        {
            name: 'PDF Viewer',
            filename: 'internal-pdf-viewer',
            description: 'Portable Document Format',
            mimeTypes: [{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }]
        },
        {
            name: 'Chrome PDF Viewer',
            filename: 'internal-pdf-viewer',
            description: 'Portable Document Format',
            mimeTypes: [{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }]
        },
        {
            name: 'Chromium PDF Viewer',
            filename: 'internal-pdf-viewer',
            description: 'Portable Document Format',
            mimeTypes: [{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }]
        }
    ];

    try {
        const pluginArray = Object.create(PluginArray.prototype);
        const mimeTypeArray = Object.create(MimeTypeArray.prototype);

        fakePlugins.forEach((p, pIdx) => {
            const plugin = Object.create(Plugin.prototype);
            Object.defineProperties(plugin, {
                name: { get: () => p.name },
                filename: { get: () => p.filename },
                description: { get: () => p.description },
                length: { get: () => p.mimeTypes.length }
            });

            p.mimeTypes.forEach((m, mIdx) => {
                const mimeType = Object.create(MimeType.prototype);
                Object.defineProperties(mimeType, {
                    type: { get: () => m.type },
                    suffixes: { get: () => m.suffixes },
                    description: { get: () => m.description },
                    enabledPlugin: { get: () => plugin }
                });
                plugin[mIdx] = mimeType;
                mimeTypeArray[mIdx] = mimeType;
            });

            pluginArray[pIdx] = plugin;
        });

        Object.defineProperty(pluginArray, 'length', { get: () => fakePlugins.length });
        Object.defineProperty(mimeTypeArray, 'length', { get: () => fakePlugins.length });

        Object.defineProperty(navigator, 'plugins', { get: () => pluginArray });
        Object.defineProperty(navigator, 'mimeTypes', { get: () => mimeTypeArray });
    } catch(e) {}

    // 4. Mock navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'ru'],
        configurable: true
    });

    // 5. Mock permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission === 'denied' ? 'denied' : 'prompt' }) :
            originalQuery(parameters)
    );

    // 6. Mock WebGL Vendor & Renderer
    try {
        const getParameterProto = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // UNMASKED_VENDOR_WEBGL
            if (parameter === 37445) {
                return 'Google Inc. (NVIDIA)';
            }
            // UNMASKED_RENDERER_WEBGL
            if (parameter === 37446) {
                return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            }
            return getParameterProto.apply(this, [parameter]);
        };

        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameter2Proto = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Google Inc. (NVIDIA)';
                }
                if (parameter === 37446) {
                    return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                }
                return getParameter2Proto.apply(this, [parameter]);
            };
        }
    } catch(e) {}

    // 7. Cleanup automation flags & globals
    const cleanGlobals = () => {
        ['__playwright', '__pw_manual', 'cdc_adoQpoasnfa76pfcZLmcfl_Array', 'cdc_adoQpoasnfa76pfcZLmcfl_Promise', 'cdc_adoQpoasnfa76pfcZLmcfl_Symbol'].forEach(prop => {
            try {
                delete window[prop];
            } catch(e) {}
        });
    };
    cleanGlobals();
    window.addEventListener('DOMContentLoaded', cleanGlobals);
})();
"""


def get_stealth_chromium_args(location_x=0, location_y=0, headless=False, low_cpu=False):
    """
    Returns robust Chromium launch arguments configured for stealth and low resource footprint.
    """
    args = [
        f"--window-position={location_x},{location_y}",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-features=IsolateOrigins,site-per-process,UserAgentClientHint",
        "--disable-dev-shm-usage",
        "--password-store=basic",
        "--use-mock-keychain",
        "--mute-audio",
        "--webrtc-ip-handling-policy=disable_non_proxied_udp",
        "--force-webrtc-ip-handling-policy",
    ]

    if headless:
        args.append("--headless=new")

    if low_cpu:
        args.extend([
            "--disable-accelerated-2d-canvas",
            "--disable-gpu-rasterization",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--blink-settings=imagesEnabled=false",
        ])

    return args


def apply_stealth_to_page(page):
    """
    Applies stealth scripts and libraries to a Playwright page.
    """
    try:
        page.add_init_script(STEALTH_JS)
    except Exception as e:
        logger.warning(f"Error injecting custom stealth JS: {e}")

    try:
        from playwright_stealth import stealth_sync
        stealth_sync(page)
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"playwright_stealth helper info: {e}")


def apply_stealth_to_context(context):
    """
    Applies stealth init scripts to a Playwright BrowserContext.
    """
    try:
        context.add_init_script(STEALTH_JS)
    except Exception as e:
        logger.warning(f"Error adding stealth script to context: {e}")
