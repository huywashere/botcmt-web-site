import os
import random
import re
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Page, BrowserContext

from movie_extractor import MovieExtractor
from comment_generator import CommentGenerator
from comment_poster import CommentPoster
from telegram_notifier import TelegramNotifier
from history_manager import CommentHistoryManager

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]

class GoogleTopBot:
    def __init__(self, config: dict, exporter, console=None):
        self.config = config
        self.exporter = exporter
        self.console = console
        self.comment_poster = CommentPoster(log_fn=self.log)

        # Khởi tạo Telegram Notifier
        tg_cfg = self.config.get("telegram", {})
        self.notifier = TelegramNotifier(
            bot_token=tg_cfg.get("bot_token", ""),
            chat_id=tg_cfg.get("chat_id", ""),
            enabled=tg_cfg.get("enabled", False)
        )

        # Khởi tạo Comment Generator (Hỗ trợ AI Gemini)
        cmt_cfg = self.config.get("comment", {})
        self.comment_gen = CommentGenerator(
            ai_api_key=cmt_cfg.get("gemini_api_key", ""),
            use_ai=cmt_cfg.get("use_ai", True)
        )

        # Khởi tạo bộ nhớ chống bình luận trùng phim (Deduplication)
        dedup_cfg = self.config.get("deduplication", {})
        dedup_file = dedup_cfg.get("history_file", "output/commented_history.json")
        self.history_mgr = CommentHistoryManager(history_file=dedup_file)
        self.force_recomment = dedup_cfg.get("force_recomment", False)

        # Tập hợp các domain đã bình luận
        self.commented_domains = set()

    def log(self, message: str, style: str = ""):
        if self.console:
            if style:
                self.console.print(f"[{style}]{message}[/{style}]")
            else:
                self.console.print(message)
        else:
            print(message)

    def _init_browser(self, p):
        browser_cfg = self.config.get("browser", {})
        proxy_cfg = self.config.get("proxy", {})
        headless = browser_cfg.get("headless", False)
        slow_mo = browser_cfg.get("slow_mo_ms", 30)
        width = browser_cfg.get("window_width", 1280)
        height = browser_cfg.get("window_height", 800)
        use_persistent = browser_cfg.get("use_persistent_profile", True)
        profile_dir = browser_cfg.get("profile_dir", "user_profile")

        # Cấu hình Proxy nếu có
        proxy_dict = None
        if proxy_cfg.get("enabled") and proxy_cfg.get("server"):
            proxy_dict = {"server": proxy_cfg.get("server")}
            if proxy_cfg.get("username"):
                proxy_dict["username"] = proxy_cfg.get("username")
            if proxy_cfg.get("password"):
                proxy_dict["password"] = proxy_cfg.get("password")
            self.log(f"🌐 Đang sử dụng Proxy: {proxy_cfg.get('server')}", "cyan")

        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            f"--window-size={width},{height}"
        ]

        user_agent = random.choice(USER_AGENTS)

        stealth_js = """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN', 'vi', 'en-US', 'en'] });
        """

        if use_persistent:
            os.makedirs(profile_dir, exist_ok=True)
            self.log(f"📁 Lưu phiên đăng nhập trình duyệt (Profile): '{profile_dir}'", "dim")
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=headless,
                slow_mo=slow_mo,
                args=browser_args,
                proxy=proxy_dict,
                user_agent=user_agent,
                locale="vi-VN",
                viewport={"width": width, "height": height}
            )
            context.add_init_script(stealth_js)
            browser = None
        else:
            browser = p.chromium.launch(
                headless=headless,
                slow_mo=slow_mo,
                args=browser_args,
                proxy=proxy_dict
            )
            context = browser.new_context(
                user_agent=user_agent,
                locale="vi-VN",
                viewport={"width": width, "height": height}
            )
            context.add_init_script(stealth_js)

        return browser, context

    def _setup_ad_and_popup_protection(self, context: BrowserContext):
        """
        Bảo vệ tự động chống quảng cáo popup nhảy tab và chặn các domain quảng cáo rác.
        Tự động đóng mọi popup ngoài ý muốn để bot không bị chuyển hướng kẹt trang.
        """
        ad_cfg = self.config.get("ad_blocker", {})
        if not ad_cfg.get("enabled", True):
            return

        self.log("🛡️ Đã kích hoạt bộ lọc quảng cáo & chặn popup nhảy tab tự động", "dim")

        # 1. Chặn request tới các mạng quảng cáo rác
        ad_patterns = [
            "*doubleclick.net*",
            "*google-analytics.com*",
            "*popads*",
            "*exoclick*",
            "*adnxs*",
            "*adcash*",
            "*histats*",
            "*propellerads*",
            "*mgid*",
            "*taboola*"
        ]
        for pat in ad_patterns:
            try:
                context.route(f"**/{pat}/**", lambda route: route.abort())
            except Exception:
                pass

        # 2. Tự động đóng các tab popup nhảy trang bất ngờ (Popunder / Popup)
        if ad_cfg.get("block_popups", True):
            def handle_new_page(new_page: Page):
                try:
                    time.sleep(0.5)
                    new_url = new_page.url or ""
                    allowed = self.config.get("movie_filter", {}).get("allowed_domains", ["motchill", "motphim", "phimmoi", "rophim"])
                    is_allowed = any(dom in new_url.lower() for dom in allowed) or "google." in new_url.lower()
                    if not is_allowed or "about:blank" in new_url:
                        self.log(f"      🚫 Đã tự động đóng Popup quảng cáo: {new_url[:55]}...", "dim")
                        new_page.close()
                except Exception:
                    try:
                        new_page.close()
                    except Exception:
                        pass

            context.on("page", handle_new_page)

    def _dismiss_ad_overlays(self, page: Page):
        """
        Bảo vệ siêu cấp: Tìm và bấm nút [X] tắt quảng cáo, nhấn phím ESC
        và xóa bỏ mọi banner quảng cáo nổi che khuất nội dung hoặc nút bình luận.
        """
        try:
            # 1. Nhấn ESC để đóng các modal popup quảng cáo
            page.keyboard.press("Escape")
        except Exception:
            pass

        try:
            # 2. Tìm và click nút tắt [X] nếu có
            close_selectors = [
                ".close-ad", ".btn-close", ".close-popup", ".ad-close",
                "button:has-text('Đóng')", "span:has-text('Đóng')", "a:has-text('Đóng')",
                "button:has-text('Bỏ qua')", "a:has-text('Bỏ qua')", ".skip-ad",
                "[aria-label='Close']", ".modal-close", ".popup-close"
            ]
            for sel in close_selectors:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=1000)
                    time.sleep(0.3)
                    break
        except Exception:
            pass

        try:
            # 3. Chạy script diệt triệt để các banner, iframe quảng cáo và overlay z-index cao
            page.evaluate("""() => {
                const selectors = [
                    '.floating-banner', '.ads-overlay', '#popup-ad', '.popup-wrapper',
                    'div[id*="ad-"]', 'div[class*="popup-banner"]', '.ad-box',
                    'iframe[src*="ad"]', '.banner-top', '.banner-bottom', '.ad-sticky',
                    '#banner-bottom', '.adsbox', '.qc-container', '.banner-qc',
                    '.float-ck', '#float_banner'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        el.style.display = 'none';
                        el.remove();
                    });
                });

                // Diệt các div đè toàn màn hình có z-index cao che nút
                document.querySelectorAll('div, section, aside').forEach(el => {
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
                });
            }""")
        except Exception:
            pass

    def _simulate_video_playback(self, page: Page):
        """
        Giả lập bấm xem video phim (Play video 5-8s) như khán giả thật.
        Tránh thuật toán chống bot của web phim kiểm tra xem người dùng có thực sự xem phim không.
        """
        interaction_cfg = self.config.get("interaction", {})
        if not interaction_cfg.get("simulate_video_playback", True):
            return

        try:
            # 1. Thử click nút Xem Phim nếu đang ở trang giới thiệu
            watch_selectors = [
                "a:has-text('Xem Phim')",
                "a:has-text('Xem ngay')",
                ".btn-watch",
                ".btn-play",
                ".play-icon",
                "#play-film",
                "a[href*='xem-phim']",
                ".btn-see"
            ]
            for sel in watch_selectors:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=3000)
                    self.log("      ▶️ Đã bấm nút 'Xem Phim'...", "dim")
                    time.sleep(1.8)
                    break
        except Exception:
            pass

        try:
            # 2. Thử kích hoạt thẻ <video> chạy 5-8s
            played = page.evaluate("""() => {
                const video = document.querySelector('video');
                if (video) {
                    try {
                        video.muted = true;
                        video.play();
                        return true;
                    } catch(e) { return false; }
                }
                return false;
            }""")
            watch_seconds = random.randint(5, 8)
            if played:
                self.log(f"      🍿 Đang xem phim thật trong {watch_seconds}s...", "bold green")
            else:
                self.log(f"      🍿 Đang ở trình phát phim {watch_seconds}s...", "dim")
            time.sleep(watch_seconds)
        except Exception:
            time.sleep(2.5)

    def run(self, keywords=None):
        if not keywords:
            keywords = self.config.get("search", {}).get("keywords", [])

        if not keywords:
            self.log("[red]Không tìm thấy từ khóa nào để tìm kiếm![/red]")
            return

        with sync_playwright() as p:
            browser, context = self._init_browser(p)
            self._setup_ad_and_popup_protection(context)
            search_page = context.pages[0] if context.pages else context.new_page()

            try:
                for idx, keyword in enumerate(keywords, 1):
                    self.log(f"\n=======================================================", "cyan")
                    self.log(f"🎬 [{idx}/{len(keywords)}] Tìm kiếm phim: '{keyword}'", "bold yellow")
                    self.log(f"=======================================================", "cyan")

                    self._process_keyword(search_page, context, keyword)

                    if idx < len(keywords):
                        pause = random.randint(4, 7)
                        self.log(f"⏳ Tạm nghỉ {pause}s trước khi tìm từ khóa tiếp theo...", "dim")
                        time.sleep(pause)

            except KeyboardInterrupt:
                self.log("\n⚠️ Người dùng đã dừng chương trình bằng Ctrl+C.", "yellow")
            except Exception as e:
                self.log(f"❌ Lỗi ngoài ý muốn: {e}", "red")
            finally:
                self.log("\n🧹 Đang lưu phiên và đóng trình duyệt...", "dim")
                if browser:
                    browser.close()
                else:
                    context.close()
                self.log("✅ Hoàn tất toàn bộ phiên cào & bình luận web phim!", "bold green")

    def _process_keyword(self, page: Page, context: BrowserContext, keyword: str):
        search_cfg = self.config.get("search", {})
        movie_cfg = self.config.get("movie_filter", {})
        top_limit = search_cfg.get("top_limit", 3)
        google_domain = search_cfg.get("google_domain", "https://www.google.com")

        only_movies = movie_cfg.get("only_movie_sites", True)
        movie_kws = movie_cfg.get("keywords_matching", ["motchill", "motphim", "phimmoi", "rophim"])
        allowed_domains = movie_cfg.get("allowed_domains", ["motchill", "motphim", "phimmoi", "rophim"])
        excluded_domains = movie_cfg.get("excluded_domains", ["facebook.com", "youtube.com", "tiktok.com", "wikipedia.org", "shopee.vn", "lazada.vn"])

        # 1. Mở trang Google
        try:
            page.goto(google_domain, wait_until="domcontentloaded", timeout=25000)
        except Exception:
            try:
                page.goto(google_domain, wait_until="networkidle", timeout=25000)
            except Exception as e:
                self.log(f"⚠️ Lỗi kết nối Google: {e}", "red")
                return

        time.sleep(1.0)

        # 2. Xử lý popup cookie nếu có
        for btn_text in ["Đồng ý tất cả", "Tôi đồng ý", "Accept all", "I agree"]:
            try:
                btn = page.locator(f"button:has-text('{btn_text}')")
                if btn.count() > 0 and btn.first.is_visible():
                    btn.first.click()
                    page.wait_for_timeout(1000)
                    break
            except Exception:
                pass

        # 3. Gõ từ khóa tìm kiếm
        search_box = page.locator('textarea[name="q"], input[name="q"]').first
        if not search_box.is_visible():
            self.log("❌ Không tìm thấy ô tìm kiếm Google!", "red")
            return

        search_box.click()
        search_box.fill(keyword)
        time.sleep(0.5)
        search_box.press("Enter")

        # 4. Chờ kết quả hiển thị
        try:
            page.wait_for_selector("a:has(h3)", timeout=15000)
        except Exception:
            self.log("⚠️ Không tải được kết quả tìm kiếm Google hoặc dính CAPTCHA.", "red")
            return

        time.sleep(1.5)

        # 5. Thu thập & Lọc kết quả web phim
        selected_movie_links = []
        seen_hrefs = set()

        max_scroll_attempts = 3
        for scroll_i in range(max_scroll_attempts):
            all_links = page.locator("a:has(h3)").all()

            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if not href or href in seen_hrefs:
                        continue
                    if "/aclk?" in href or "googleadservices" in href:
                        continue
                    if href.startswith("/search?") or href.startswith("https://maps.google.com"):
                        continue

                    title = link.locator("h3").inner_text().strip()
                    if not title:
                        continue

                    cite_text = ""
                    try:
                        parent_container = link.locator("xpath=ancestor::div[contains(@class, 'MjjYud') or contains(@class, 'g')]").first
                        if parent_container.count() > 0:
                            cite_elem = parent_container.locator("cite").first
                            if cite_elem.count() > 0:
                                cite_text = cite_elem.inner_text().strip()
                    except Exception:
                        pass

                    seen_hrefs.add(href)

                    # Kiểm tra bộ lọc web phim mục tiêu
                    if only_movies:
                        is_target = MovieExtractor.is_movie_content(
                            title=title,
                            url=href,
                            movie_keywords=movie_kws,
                            allowed_domains=allowed_domains,
                            excluded_domains=excluded_domains,
                            cite_text=cite_text
                        )
                        if not is_target:
                            continue

                    selected_movie_links.append((link, title, href))

                    detected_brand = "Web phim mục tiêu"
                    for b in allowed_domains:
                        if b.lower() in f"{title} {href} {cite_text}".lower():
                            detected_brand = b.upper()
                            break

                    self.log(f"   🎯 Khớp web [{detected_brand}]: {title[:55]}...", "green")

                    if len(selected_movie_links) >= top_limit:
                        break
                except Exception:
                    continue

            if len(selected_movie_links) >= top_limit:
                break

            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(1.2)

        if not selected_movie_links:
            target_str = ", ".join(allowed_domains)
            self.log(f"⚠️ Không tìm thấy web phim nào thuộc danh sách [{target_str}] cho từ khóa này.", "yellow")
            return

        self.log(f"\n✨ Đã tìm được {len(selected_movie_links)} web phim mục tiêu để cào & bình luận.\n", "bold green")

        # 6. Truy cập & Cào/Bình luận từng trang web phim
        rank = 0
        for link_loc, title, href in selected_movie_links:
            rank += 1
            self.log(f"👉 [Top {rank}] Đang mở web: {title}", "bold cyan")
            self._visit_movie_website(context, link_loc, rank, keyword, title, allowed_domains)
            time.sleep(random.uniform(2.5, 4.0))

    def _get_domain_brand(self, domain_or_url: str, allowed_domains: list) -> str:
        """Lấy tên thương hiệu của website (motchill, motphim, phimmoi, rophim...)."""
        text = domain_or_url.lower()
        for b in allowed_domains:
            if b.lower() in text:
                return b.lower()
        parsed = urlparse(domain_or_url)
        return parsed.netloc or text

    def _extract_hot_movie_links(self, page: Page, limit: int = 3) -> list:
        """Trích xuất danh sách các phim Hot/nổi bật nhất trên trang chủ hoặc trang danh mục."""
        js_code = """
        () => {
            const selectors = [
                "[class*='hot'] a[href]",
                "[class*='featured'] a[href]",
                "[class*='slider'] a[href]",
                "[class*='trending'] a[href]",
                ".tray-item a[href]",
                ".film-item a[href]",
                ".movie-item a[href]",
                ".list-film a[href]",
                "a[href*='/phim/']",
                "a[href*='/phim-']",
                ".item a[href]"
            ];
            const seen = new Set();
            const results = [];
            const ignores = ['the-loai', 'quoc-gia', 'nam-phat-hanh', 'dien-vien', 'dao-dien', 'tin-tuc', 'faq', 'contact', 'login', 'register'];

            for (const sel of selectors) {
                const links = document.querySelectorAll(sel);
                for (const a of links) {
                    const href = a.href;
                    if (!href || seen.has(href)) continue;
                    if (href.startsWith('javascript:') || href.includes('#')) continue;
                    if (ignores.some(ig => href.toLowerCase().includes(ig))) continue;

                    const text = a.innerText ? a.innerText.trim() : (a.title ? a.title.trim() : "");
                    seen.add(href);
                    results.push({ url: href, title: text });
                    if (results.length >= 15) break;
                }
                if (results.length >= 15) break;
            }
            return results;
        }
        """
        try:
            links = page.evaluate(js_code)
            return links[:limit] if links else []
        except Exception:
            return []

    def _visit_movie_website(self, context: BrowserContext, link_loc, rank: int, keyword: str, preview_title: str, allowed_domains: list):
        movie_cfg = self.config.get("movie_filter", {})
        comment_cfg = self.config.get("comment", {})

        auto_comment = comment_cfg.get("auto_comment", True)
        prioritize_hot = comment_cfg.get("prioritize_hot_movies", True)
        comments_per_web = comment_cfg.get("comments_per_website", 3)
        excluded_domains = movie_cfg.get("excluded_domains", ["youtube.com", "facebook.com", "tiktok.com", "wikipedia.org"])

        new_page = None

        try:
            with context.expect_page(timeout=20000) as new_page_info:
                link_loc.click(modifiers=["Control"])
            new_page = new_page_info.value

            try:
                new_page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass

            try:
                new_page.wait_for_function(
                    "() => !window.location.href.includes('google.com/goto') && window.location.href !== 'about:blank'",
                    timeout=10000
                )
            except Exception:
                pass

            time.sleep(1.5)
            landing_url = new_page.url
            landing_title = new_page.title() or preview_title

            # Kiểm tra domain loại trừ
            for exc in excluded_domains:
                if exc.lower() in landing_url.lower():
                    self.log(f"   ⏩ Bỏ qua vì chuyển hướng vào domain loại trừ: {exc}", "yellow")
                    return

            # Kiểm tra xem website thật sự có thuộc danh sách allowed_domains không
            if allowed_domains and len(allowed_domains) > 0:
                is_match = any(d.lower() in landing_url.lower() or d.lower() in landing_title.lower() for d in allowed_domains)
                if not is_match:
                    self.log(f"   ⏩ Bỏ qua: Website {landing_url} không thuộc danh sách mục tiêu ({', '.join(allowed_domains)})", "yellow")
                    return

            domain_brand = self._get_domain_brand(landing_url, allowed_domains)
            self.log(f"   🌐 Đang mở hệ thống web: [bold cyan]{domain_brand.upper()}[/bold cyan] ({landing_url})", "blue")

            # Tìm danh sách phim Hot trên web này để bình luận nhiều lần
            hot_movies = []
            if prioritize_hot and auto_comment:
                candidates = self._extract_hot_movie_links(new_page, limit=comments_per_web * 3)
                if not self.force_recomment:
                    fresh_movies = []
                    for m in candidates:
                        m_url = m.get("url", "")
                        if self.history_mgr.is_commented(m_url):
                            self.log(f"   ⏩ Đã bỏ qua phim đã từng bình luận trước đó: [dim]{m.get('title')}[/dim]", "dim")
                        else:
                            fresh_movies.append(m)
                    hot_movies = fresh_movies[:comments_per_web]
                else:
                    hot_movies = candidates[:comments_per_web]

            if hot_movies and len(hot_movies) > 0:
                self.log(f"   🔥 Tìm thấy {len(hot_movies)} phim Hot/nổi bật trên [{domain_brand.upper()}]. Bắt đầu cào & bình luận từng phim:", "bold yellow")
                for sub_idx, hot_m in enumerate(hot_movies, 1):
                    target_movie_url = hot_m.get("url")
                    target_movie_title = hot_m.get("title") or f"Phim Hot #{sub_idx}"

                    self.log(f"\n   👉 [{domain_brand.upper()} - Phim Hot {sub_idx}/{len(hot_movies)}] {target_movie_title}", "cyan")
                    try:
                        new_page.goto(target_movie_url, wait_until="domcontentloaded", timeout=20000)
                        time.sleep(1.5)
                    except Exception as e:
                        self.log(f"      ⚠️ Không thể tải phim này: {e}", "dim")
                        continue

                    self._process_single_movie_page(
                        page=new_page,
                        movie_url=new_page.url,
                        preview_title=target_movie_title,
                        keyword=keyword,
                        rank=rank,
                        sub_rank=sub_idx,
                        domain_brand=domain_brand
                    )

                    if sub_idx < len(hot_movies):
                        pause = random.randint(3, 6)
                        self.log(f"      ⏳ Nghỉ {pause}s trước khi bình luận phim Hot tiếp theo...", "dim")
                        time.sleep(pause)
            else:
                # Trang hiện tại đã là trang chi tiết 1 bộ phim
                self._process_single_movie_page(
                    page=new_page,
                    movie_url=landing_url,
                    preview_title=landing_title,
                    keyword=keyword,
                    rank=rank,
                    sub_rank=1,
                    domain_brand=domain_brand
                )

        except Exception as e:
            self.log(f"   ❌ Có lỗi khi duyệt web này: {e}", "red")
        finally:
            if new_page:
                try:
                    new_page.close()
                except Exception:
                    pass

    def _process_single_movie_page(self, page: Page, movie_url: str, preview_title: str, keyword: str, rank: int, sub_rank: int, domain_brand: str):
        behavior_cfg = self.config.get("behavior", {})
        movie_cfg = self.config.get("movie_filter", {})
        comment_cfg = self.config.get("comment", {})

        min_stay = behavior_cfg.get("min_stay_seconds", 6)
        max_stay = behavior_cfg.get("max_stay_seconds", 12)
        should_scroll = behavior_cfg.get("scroll_page", True)
        take_screenshot = behavior_cfg.get("take_screenshot", True)
        crawl_details = movie_cfg.get("crawl_details", True)
        auto_comment = comment_cfg.get("auto_comment", True)

        current_url = page.url
        current_title = page.title() or preview_title

        movie_info = {}
        if crawl_details:
            movie_info = MovieExtractor.extract_movie_info(page)
            movie_info["keyword"] = keyword
            movie_info["rank"] = f"{rank}.{sub_rank}"
            movie_info["url"] = current_url
            if not movie_info["movie_name"]:
                movie_info["movie_name"] = current_title

            cmts = movie_info.get("comments", [])
            self.log(f"      🎬 Tên phim: {movie_info['movie_name']}", "bold magenta")
            if movie_info.get("year"):
                self.log(f"      📅 Năm phát hành: {movie_info['year']}", "magenta")
            if cmts:
                self.log(f"      💬 Có {len(cmts)} bình luận cũ (Ví dụ: '{cmts[0][:50]}...')", "dim")

            self.exporter.save_movie_data(movie_info)

        # Mô phỏng cuộn chuột đọc nội dung
        start_time = time.time()

        # Giả lập bấm xem phim 5-8s trước nếu bật
        if self.config.get("interaction", {}).get("simulate_video_playback", True):
            self._simulate_video_playback(page)

        stay_duration = random.uniform(min_stay, max_stay)
        if should_scroll:
            self._simulate_reading(page, stay_duration)
        else:
            time.sleep(stay_duration)

        elapsed = round(time.time() - start_time, 1)
        self.log(f"      ⏱️ Đã xem trang {elapsed}s", "green")

        # Tự động gửi bình luận
        cmt_result = {"success": False, "message": "Chưa bình luận"}
        smart_comment = ""
        author_name = ""

        # Kiểm tra trùng lặp với phim lẻ/trang chi tiết trực tiếp
        if auto_comment and not self.force_recomment and self.history_mgr.is_commented(current_url):
            self.log(f"      ⏩ Phim này đã có trong lịch sử đã bình luận ({current_url}). Bỏ qua bình luận!", "yellow")
            auto_comment = False

        if auto_comment:
            # 1. Tự động đóng banner quảng cáo nổi che nút
            self._dismiss_ad_overlays(page)

            # 2. Tự động đánh giá 5 sao nếu bật
            if self.config.get("interaction", {}).get("auto_vote_5_stars", True):
                self.comment_poster.vote_5_stars(page)

            movie_name = movie_info.get("movie_name", current_title)
            movie_desc = movie_info.get("description", "")
            custom_name = comment_cfg.get("custom_name")
            custom_email = comment_cfg.get("custom_email")
            author_name = custom_name if custom_name else self.comment_gen.generate_nickname()
            author_email = custom_email if custom_email else self.comment_gen.generate_email(author_name)
            custom_templates = comment_cfg.get("custom_templates", [])

            # Kiểm tra xem có nên Trả lời (Reply) bình luận cũ của người khác không
            existing_cmts = movie_info.get("comments", [])
            reply_attempted = False
            is_reply = False

            if existing_cmts and self.config.get("interaction", {}).get("enable_reply_mode", True) and random.random() < 0.5:
                target_cmt = random.choice(existing_cmts[:4])
                smart_comment, cmt_source = self.comment_gen.generate_reply(
                    movie_name=movie_name,
                    target_author="",
                    target_comment=target_cmt
                )
                self.log(f"      💬 [Chế độ trả lời bình luận] Nguồn: [{cmt_source}]", "cyan")
                self.log(f"         • Bình luận gốc: [dim]\"{target_cmt[:45]}...\"[/dim]", "dim")
                self.log(f"         • Người gửi: [bold]{author_name}[/bold] ({author_email})", "white")
                self.log(f"         • Trả lời: [italic yellow]\"{smart_comment}\"[/italic yellow]", "white")

                cmt_result = self.comment_poster.reply_to_comment(
                    page=page,
                    reply_text=smart_comment,
                    author_name=author_name,
                    email=author_email
                )
                if cmt_result.get("success"):
                    reply_attempted = True
                    is_reply = True

            # Nếu không trả lời bình luận cũ hoặc trả lời không thành công thì đăng bình luận mới
            if not reply_attempted or not cmt_result.get("success"):
                smart_comment, cmt_source = self.comment_gen.generate_comment(
                    movie_name=movie_name,
                    description=movie_desc,
                    custom_templates=custom_templates
                )

                self.log(f"      💬 [Gửi bình luận mới] Nguồn: [{cmt_source}]", "cyan")
                self.log(f"         • Người gửi: [bold]{author_name}[/bold] ({author_email})", "white")
                self.log(f"         • Nội dung: [italic yellow]\"{smart_comment}\"[/italic yellow]", "white")

                cmt_result = self.comment_poster.post_comment(
                    page=page,
                    comment_text=smart_comment,
                    author_name=author_name,
                    email=author_email
                )

            if cmt_result.get("success"):
                self.log(f"         ✅ {cmt_result.get('message')}", "bold green")
                # Ghi nhận vào bộ nhớ lịch sử đã bình luận
                self.history_mgr.record_comment(
                    url=current_url,
                    movie_name=movie_name,
                    author=author_name,
                    email=author_email,
                    comment_text=smart_comment
                )
            else:
                self.log(f"         ℹ️ {cmt_result.get('message')}", "dim")

            self.exporter.save_comment_log({
                "keyword": keyword,
                "movie_name": movie_name,
                "url": current_url,
                "author": author_name,
                "email": author_email,
                "comment_text": smart_comment,
                "source": cmt_source,
                "success": cmt_result.get("success"),
                "message": cmt_result.get("message")
            })

        # Chụp ảnh màn hình lưu bằng chứng
        screenshot_path = ""
        if take_screenshot:
            screenshot_path = self._take_screenshot(page, keyword, f"{rank}_{sub_rank}", current_url)

        # Lưu lịch sử truy cập
        self.exporter.save_visit({
            "keyword": keyword,
            "rank": f"{rank}.{sub_rank}",
            "title": current_title,
            "url": current_url,
            "stay_seconds": elapsed,
            "internal_visited": False,
            "screenshot": screenshot_path,
            "status": "SUCCESS"
        })

        # Gửi thông báo Telegram nếu bật
        if self.notifier.enabled:
            movie_name = movie_info.get("movie_name", current_title)
            status_icon = "✅ Đã gửi bình luận" if cmt_result.get("success") else "ℹ️ Đã xem trang"
            cmt_type_label = "💬 *Trả lời bình luận:*" if is_reply else "💬 *Bình luận:*"
            tg_caption = (
                f"🎬 *BOT CÀO PHIM & BÌNH LUẬN*\n\n"
                f"🍿 *Phim:* {movie_name}\n"
                f"🌐 *Trang web:* [{domain_brand.upper()}]\n"
                f"🔗 *Link phim:* {current_url}\n"
                f"👤 *Người gửi:* {author_name or 'Ẩn danh'} ({author_email})\n"
                f"{cmt_type_label} \"{smart_comment}\"\n"
                f"📊 *Trạng thái:* {status_icon}\n"
                f"⏱️ *Thời gian xem:* {elapsed}s"
            )
            if screenshot_path and os.path.exists(screenshot_path):
                self.notifier.send_photo(screenshot_path, tg_caption)
            else:
                self.notifier.send_message(tg_caption)
            self.log("      📱 Đã gửi báo cáo Telegram kèm link trực tiếp!", "cyan")

    def _simulate_reading(self, page: Page, total_duration: float):
        self.log("   📜 Đang cuộn trang xem danh sách phim / bài viết...", "dim")
        start = time.time()

        while time.time() - start < total_duration:
            scroll_step = random.randint(250, 550)
            try:
                page.evaluate(f"window.scrollBy({{top: {scroll_step}, behavior: 'smooth'}})")
            except Exception:
                pass

            if random.random() < 0.25:
                time.sleep(random.uniform(0.6, 1.2))
                try:
                    page.evaluate("window.scrollBy({top: -150, behavior: 'smooth'})")
                except Exception:
                    pass

            pause = random.uniform(1.2, 2.5)
            if time.time() - start + pause > total_duration:
                break
            time.sleep(pause)

    def _visit_internal_page(self, page: Page, base_url: str) -> bool:
        try:
            parsed_base = urlparse(base_url)
            domain = parsed_base.netloc

            internal_links = page.locator("a[href]").all()
            candidate_links = []

            for link in internal_links[:30]:
                href = link.get_attribute("href")
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue

                if href.startswith("/") or domain in href:
                    if link.is_visible():
                        candidate_links.append(link)

            if candidate_links:
                selected_link = random.choice(candidate_links[:10])
                self.log(f"   🔗 Bấm xem thêm trang con/tập phim trong website...", "magenta")
                selected_link.click(timeout=8000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                except Exception:
                    pass
                time.sleep(random.uniform(3, 5))
                page.evaluate("window.scrollBy({top: 400, behavior: 'smooth'}})")
                return True
        except Exception:
            pass
        return False

    def _take_screenshot(self, page: Page, keyword: str, rank: int, url: str) -> str:
        try:
            parsed = urlparse(url)
            clean_domain = re.sub(r'[^a-zA-Z0-9]', '_', parsed.netloc or "movie_web")
            clean_kw = re.sub(r'[^a-zA-Z0-9]', '_', keyword)[:20]
            filename = f"movie_top{rank}_{clean_kw}_{clean_domain}_{int(time.time())}.png"
            filepath = os.path.join(self.exporter.screenshots_dir, filename)

            page.screenshot(path=filepath, full_page=False)
            self.log(f"   📸 Đã chụp ảnh màn hình: {filename}", "dim")
            return filepath
        except Exception:
            return ""
