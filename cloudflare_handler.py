import time
from playwright.sync_api import Page

class CloudflareHandler:
    """
    Tự động phát hiện và chờ đợi/vượt qua lớp bảo vệ Cloudflare Bot Protection & Cloudflare Turnstile.
    Hỗ trợ phát hiện 'Just a moment...', 'Verify you are human', và tự động click checkbox Turnstile trong iframe.
    """

    @staticmethod
    def is_cloudflare_active(page: Page) -> bool:
        """Kiểm tra xem trang hiện tại có đang bị chặn bởi màn hình Cloudflare không."""
        try:
            # 1. Kiểm tra tiêu đề trang
            title = (page.title() or "").strip().lower()
            cf_titles = [
                "just a moment",
                "please wait",
                "attention required",
                "cloudflare",
                "đang kiểm tra trình duyệt",
                "checking your browser",
                "moment..."
            ]
            if any(t in title for t in cf_titles):
                return True

            # 2. Kiểm tra URL
            url = (page.url or "").lower()
            if "challenges.cloudflare.com" in url or "__cf_chl" in url:
                return True

            # 3. Kiểm tra các phần tử đặc trưng của Cloudflare trong DOM
            has_cf_element = page.evaluate("""() => {
                const selectors = [
                    '#challenge-stage',
                    '#challenge-running',
                    '#cf-please-wait',
                    '#challenge-form',
                    '.cf-turnstile',
                    '.cf-turnstile-wrapper',
                    '#turnstile-wrapper',
                    'iframe[src*="challenges.cloudflare.com"]',
                    'input[name="cf-turnstile-response"]'
                ];
                for (const s of selectors) {
                    if (document.querySelector(s)) return true;
                }
                const bodyText = (document.body ? document.body.innerText : '').toLowerCase();
                if (bodyText.includes('checking your browser before accessing') || 
                    bodyText.includes('verify you are human') || 
                    bodyText.includes('đang kiểm tra trình duyệt')) {
                    return true;
                }
                return false;
            }""")
            return bool(has_cf_element)
        except Exception:
            return False

    @classmethod
    def wait_and_bypass(cls, page: Page, timeout: int = 25, log_fn=None) -> bool:
        """
        Đợi và tự động giải quyết thử thách Cloudflare Turnstile / Bot Protection.
        """
        log = log_fn if log_fn else print

        if not cls.is_cloudflare_active(page):
            return True

        log("🛡️ [CLOUDFLARE] Phát hiện hệ thống kiểm tra bot Cloudflare / Turnstile!", "bold yellow")
        log("⏳ Đang đợi Cloudflare xác minh trình duyệt sạch (tự động xử lý)...", "cyan")

        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout:
            attempt += 1

            # 1. Kiểm tra xem Cloudflare đã biến mất chưa
            if not cls.is_cloudflare_active(page):
                log("✅ [CLOUDFLARE] Đã vượt qua bảo vệ Cloudflare thành công!", "bold green")
                time.sleep(1.2)
                return True

            # 2. Quét tìm và click checkbox Turnstile trong tất cả các iframe con
            clicked = False
            for frame in page.frames:
                f_url = (frame.url or "").lower()
                if "cloudflare" in f_url or "challenge" in f_url or "turnstile" in f_url:
                    try:
                        checkbox_selectors = [
                            "input[type='checkbox']",
                            ".ctp-checkbox-label",
                            "#challenge-stage",
                            ".mark",
                            "label.ctp-checkbox-label",
                            "span.mark"
                        ]
                        for c_sel in checkbox_selectors:
                            cb = frame.locator(c_sel).first
                            if cb.count() > 0 and cb.is_visible():
                                cb.click(timeout=2000)
                                log("   👉 [CLOUDFLARE] Đã click nút 'Verify you are human' / 'Xác minh bạn là con người'...", "yellow")
                                clicked = True
                                time.sleep(2.0)
                                break
                    except Exception:
                        pass
                if clicked:
                    break

            # 3. Nếu chưa click được trong iframe, thử tìm checkbox ở main page
            if not clicked:
                try:
                    main_selectors = [
                        "#challenge-stage input[type='checkbox']",
                        ".cf-turnstile input[type='checkbox']",
                        "label:has-text('Verify you are human')",
                        "label:has-text('Xác minh bạn là con người')",
                        "input[type='checkbox']"
                    ]
                    for m_sel in main_selectors:
                        m_cb = page.locator(m_sel).first
                        if m_cb.count() > 0 and m_cb.is_visible():
                            m_cb.click(timeout=1500)
                            log("   👉 [CLOUDFLARE] Đã bấm xác minh trên trang chính...", "yellow")
                            time.sleep(1.5)
                            break
                except Exception:
                    pass

            time.sleep(1.5)

        # Kiểm tra lần cuối sau khi hết timeout
        if not cls.is_cloudflare_active(page):
            log("✅ [CLOUDFLARE] Đã vào được web chính sau khi đợi Cloudflare!", "bold green")
            return True

        log("⚠️ [CLOUDFLARE] Hết thời gian chờ Cloudflare (hoặc yêu cầu Captcha hình ảnh thủ công). Tiếp tục thử cào web...", "yellow")
        return False
