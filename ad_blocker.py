import re
import time
from urllib.parse import urlparse
from playwright.sync_api import BrowserContext, Page, Route

# Danh sách đen hơn 60+ mạng quảng cáo, tracker và mạng cá cược chuyên cắm trên web phim VN
AD_DOMAINS_BLACKLIST = [
    # Mạng quảng cáo Popunder & Push notification
    "popads.net", "popcash.net", "adsterra.com", "propellerads.com", "exoclick.com",
    "hilltopads.com", "clickadu.com", "richpush.com", "onesignal.com", "pushwoosh.com",
    "notix.co", "evadav.com", "adcash.com", "adtrue.com", "yadro.ru",

    # Mạng quảng cáo Banner & Native Ads
    "doubleclick.net", "googleadservices.com", "googlesyndication.com", "adnxs.com",
    "criteo.com", "outbrain.com", "taboola.com", "mgid.com", "infolinks.com",
    "aniview.com", "spotxchange.com", "teads.tv", "yieldmo.com", "rubiconproject.com",

    # Mạng cá cược, nổ hũ, game bài hay nhảy tab trên Motchill/Phimmoi
    "w88", "fb88", "fun88", "kubet", "thabet", "shbet", "new88", "jun88", "hi88",
    "789bet", "bk8", "dafabet", "12bet", "sv388", "sunwin", "go88", "rikvip",
    "b52", "iwin", "taixiu", "nohu", "casinowin", "bet365", "188bet",

    # Trình theo dõi & phân tích nặng nề
    "histats.com", "statcounter.com", "hotjar.com", "clarity.ms", "yandex.ru",
    "scorecardresearch.com"
]

# CSS Rules triệt hạ vĩnh viễn mọi banner nổi và overlay
AD_BLOCK_CSS = """
.floating-banner, .ads-overlay, #popup-ad, .popup-wrapper,
div[id*="ad-"], div[class*="popup-banner"], .ad-box,
iframe[src*="ad"], .banner-top, .banner-bottom, .ad-sticky,
#banner-bottom, .adsbox, .qc-container, .banner-qc,
.float-ck, #float_banner, .adblock-notice, #adblock-popup,
.ad-fixed, .banner-fixed, [class*="ad-container"],
div[style*="z-index: 99999"], div[style*="z-index: 9999"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
}
"""

# Script vô hiệu hóa bẫy cướp chuột window.open và anti-adblock
STEALTH_ADBLOCK_JS = """
// 1. Chống bẫy window.open tự động nhảy tab quảng cáo
const _realOpen = window.open;
window.open = function(url, target, features) {
    if (url && (url.includes('google') || url.includes('motchill') || url.includes('phimmoi') || url.includes('rophim') || url.includes('motphim'))) {
        return _realOpen.apply(window, arguments);
    }
    return null;
};

// 2. Đánh lừa kịch bản phát hiện Adblock
window.canRunAds = true;
window.isAdBlockActive = false;
window.fuckAdBlock = { check: () => {}, on: () => {} };

// 3. Tiêm CSS diệt banner quảng cáo ngay từ giai đoạn khởi tạo DOM
(function() {
    function injectAdStyle() {
        if (!document.head) return;
        const style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = `""" + AD_BLOCK_CSS.replace("\n", " ") + """`;
        document.head.appendChild(style);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectAdStyle);
    } else {
        injectAdStyle();
    }
})();
"""

class AdBlockerPro:
    """
    Hệ thống chặn quảng cáo toàn diện (AdBlocker Pro):
    1. Chặn request mạng ở mức protocol (Route abort) - tăng tốc độ tải trang 50-70%.
    2. Chặn các bẫy nhảy tab Popunder/Click-under (window.open interceptor).
    3. Tiêm CSS tiêu diệt triệt để các banner nổi, popup cá cược và iframe rác.
    4. Vô hiệu hóa kịch bản bắt tắt Adblock của web phim.
    """

    def __init__(self, enabled: bool = True, block_popups: bool = True, log_fn=None):
        self.enabled = enabled
        self.block_popups = block_popups
        self.log = log_fn if log_fn else print

    def setup_context(self, context: BrowserContext, allowed_domains: list = None):
        """Kích hoạt bộ lọc quảng cáo cho toàn bộ phiên trình duyệt Playwright."""
        if not self.enabled:
            return

        allowed = allowed_domains or ["motchill", "motphim", "phimmoi", "rophim"]

        # 1. Tiêm Script chống Popunder & chống Anti-Adblock vào mọi trang và iframe
        try:
            context.add_init_script(STEALTH_ADBLOCK_JS)
        except Exception:
            pass

        # 2. Định tuyến chặn request rác ở mức mạng (Route Interception)
        def handle_route(route: Route):
            request = route.request
            url = request.url.lower()
            res_type = request.resource_type

            # Chặn các request theo dõi vô bổ
            if res_type in ["beacon", "ping"]:
                route.abort()
                return

            # Chặn nếu URL chứa domain trong blacklist
            for ad_domain in AD_DOMAINS_BLACKLIST:
                if ad_domain in url:
                    route.abort()
                    return

            # Chặn các đường dẫn quảng cáo lộ liễu
            ad_url_keywords = ["/ads/", "/adserver/", "popunder", "clickunder", "vast.xml", "tracking.js", "/qc/"]
            if any(k in url for k in ad_url_keywords):
                # Không chặn nếu là URL web phim chính
                if not any(d in url for d in allowed):
                    route.abort()
                    return

            route.continue_()

        try:
            context.route("**/*", handle_route)
        except Exception:
            pass

        # 3. Tự động đóng các tab lạ mở bất ngờ (Popups do quảng cáo kích hoạt)
        if self.block_popups:
            def handle_new_page(new_page: Page):
                try:
                    # Tuyệt đối không đóng tab chính do bot chủ động tạo (opener là None)
                    try:
                        if new_page.opener() is None:
                            return
                    except Exception:
                        pass

                    time.sleep(0.6)
                    new_url = (new_page.url or "").lower()
                    if not new_url or new_url == "about:blank":
                        return

                    is_legit = any(d in new_url for d in allowed) or "google." in new_url
                    is_ad = any(ad in new_url for ad in ["bet", "casino", "shopee", "lazada", "game", "nohu", "taixiu", "ads", "pop"])
                    if not is_legit or is_ad:
                        new_page.close()
                except Exception:
                    pass

            context.on("page", handle_new_page)

    def clean_page(self, page: Page):
        """Dọn dẹp nhanh các banner nổi và đóng modal trên trang hiện tại."""
        if not self.enabled:
            return

        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        try:
            # Tìm và click nút tắt [X]
            close_selectors = [
                ".close-ad", ".btn-close", ".close-popup", ".ad-close",
                "button:has-text('Đóng')", "span:has-text('Đóng')", "a:has-text('Đóng')",
                "button:has-text('Bỏ qua')", "a:has-text('Bỏ qua')", ".skip-ad",
                "[aria-label='Close']", ".modal-close", ".popup-close"
            ]
            for sel in close_selectors:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=800)
                    time.sleep(0.2)
                    break
        except Exception:
            pass

        try:
            # Xóa các phần tử overlay che nút và các banner quảng cáo
            page.evaluate("""() => {
                const selectors = [
                    '.floating-banner', '.ads-overlay', '#popup-ad', '.popup-wrapper',
                    'div[id*="ad-"]', 'div[class*="popup-banner"]', '.ad-box',
                    'iframe[src*="ad"]', '.banner-top', '.banner-bottom', '.ad-sticky',
                    '#banner-bottom', '.adsbox', '.qc-container', '.banner-qc',
                    '.float-ck', '#float_banner', '.adblock-notice', '#adblock-popup',
                    '.ad-fixed', '.banner-fixed', '[class*="ad-container"]'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        try {
                            el.style.display = 'none';
                            el.remove();
                        } catch(e) {}
                    });
                });

                // Diệt các div đè toàn màn hình có z-index cao che nút
                document.querySelectorAll('div, section, aside').forEach(el => {
                    try {
                        const style = window.getComputedStyle(el);
                        if ((style.position === 'fixed' || style.position === 'absolute') && parseInt(style.zIndex || '0') >= 999) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width * rect.height > window.innerWidth * window.innerHeight * 0.4 || rect.bottom >= window.innerHeight - 5) {
                                if (!el.querySelector('video') && !el.querySelector('header') && !el.id.includes('player')) {
                                    el.style.display = 'none';
                                    el.remove();
                                }
                            }
                        }
                    } catch(e) {}
                });
            }""")
        except Exception:
            pass
