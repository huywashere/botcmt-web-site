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

        # Tập hợp các domain đã bình luận (Đảm bảo: chỉ cmt 1 lần / 1 website)
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

    def run(self, keywords=None):
        if not keywords:
            keywords = self.config.get("search", {}).get("keywords", [])

        if not keywords:
            self.log("[red]Không tìm thấy từ khóa nào để tìm kiếm![/red]")
            return

        with sync_playwright() as p:
            browser, context = self._init_browser(p)
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

    def _navigate_to_hot_movie(self, page: Page) -> bool:
        """Tìm và bấm vào phim Hot/đang nổi bật trên trang chủ để bình luận đúng phim."""
        hot_selectors = [
            "[class*='hot'] a[href]",
            "[class*='featured'] a[href]",
            "[class*='slider'] a[href]",
            "[class*='trending'] a[href]",
            ".tray-item a[href]",
            ".film-item a[href]",
            ".movie-item a[href]",
            ".list-film a[href]",
            ".item a[href*='phim']",
            "a[href*='/phim/']",
            "a[href*='/phim-']",
            "article a[href]"
        ]

        try:
            for sel in hot_selectors:
                links = page.locator(sel).all()
                for l in links[:15]:
                    try:
                        href = l.get_attribute("href")
                        if not href or href.startswith("#") or href.startswith("javascript:"):
                            continue
                        if any(x in href.lower() for x in ["/the-loai/", "/quoc-gia/", "/nam-phat-hanh/", "/dien-vien/", "/dao-dien/"]):
                            continue

                        if l.is_visible():
                            movie_title_hint = l.inner_text().strip() or l.get_attribute("title") or "Phim nổi bật"
                            self.log(f"   🔥 Tự động mở phim Hot/đầu trang chủ: {movie_title_hint[:50]}...", "bold yellow")
                            l.click(timeout=10000)
                            try:
                                page.wait_for_load_state("domcontentloaded", timeout=12000)
                            except Exception:
                                pass
                            time.sleep(2)
                            return True
                    except Exception:
                        continue
        except Exception:
            pass
        return False

    def _visit_movie_website(self, context: BrowserContext, link_loc, rank: int, keyword: str, preview_title: str, allowed_domains: list):
        behavior_cfg = self.config.get("behavior", {})
        movie_cfg = self.config.get("movie_filter", {})
        comment_cfg = self.config.get("comment", {})

        min_stay = behavior_cfg.get("min_stay_seconds", 6)
        max_stay = behavior_cfg.get("max_stay_seconds", 12)
        should_scroll = behavior_cfg.get("scroll_page", True)
        visit_internal = behavior_cfg.get("visit_internal_link", False)
        take_screenshot = behavior_cfg.get("take_screenshot", True)
        crawl_details = movie_cfg.get("crawl_details", True)
        auto_comment = comment_cfg.get("auto_comment", True)
        prioritize_hot = comment_cfg.get("prioritize_hot_movies", True)
        excluded_domains = movie_cfg.get("excluded_domains", ["youtube.com", "facebook.com", "tiktok.com", "wikipedia.org"])

        new_page = None
        visited_data = {
            "keyword": keyword,
            "rank": rank,
            "title": preview_title,
            "url": "",
            "stay_seconds": 0,
            "internal_visited": False,
            "screenshot": "",
            "status": "SUCCESS"
        }

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
            final_url = new_page.url
            final_title = new_page.title() or preview_title

            # Kiểm tra domain loại trừ
            for exc in excluded_domains:
                if exc.lower() in final_url.lower():
                    self.log(f"   ⏩ Bỏ qua vì chuyển hướng vào domain loại trừ: {exc}", "yellow")
                    return

            # Kiểm tra xem website thật sự có thuộc danh sách allowed_domains không
            if allowed_domains and len(allowed_domains) > 0:
                is_match = any(d.lower() in final_url.lower() or d.lower() in final_title.lower() for d in allowed_domains)
                if not is_match:
                    self.log(f"   ⏩ Bỏ qua: Website {final_url} không thuộc danh sách mục tiêu ({', '.join(allowed_domains)})", "yellow")
                    return

            # Xác định thương hiệu web (motchill, motphim, phimmoi, rophim...)
            domain_brand = self._get_domain_brand(final_url, allowed_domains)
            already_commented = domain_brand in self.commented_domains

            # Ưu tiên mở phim Hot/đầu trang nếu đang ở trang chủ hoặc danh mục
            parsed_path = urlparse(final_url).path.strip("/")
            is_homepage = parsed_path in ["", "home", "trang-chu", "index.html"]
            if prioritize_hot and is_homepage and not already_commented:
                navigated = self._navigate_to_hot_movie(new_page)
                if navigated:
                    final_url = new_page.url
                    final_title = new_page.title()
                    self.log(f"   🎬 Đã chuyển vào phim Hot: {final_title}", "white")

            visited_data["url"] = final_url
            visited_data["title"] = final_title

            self.log(f"   🌐 Website: {final_url}", "blue")
            self.log(f"   📄 Tiêu đề: {final_title}", "white")

            movie_info = {}
            if crawl_details:
                movie_info = MovieExtractor.extract_movie_info(new_page)
                movie_info["keyword"] = keyword
                movie_info["rank"] = rank
                movie_info["url"] = final_url
                if not movie_info["movie_name"]:
                    movie_info["movie_name"] = final_title

                cmts = movie_info.get("comments", [])
                self.log(f"   🎬 Tên phim cào được: {movie_info['movie_name']}", "bold magenta")
                if movie_info.get("year"):
                    self.log(f"   📅 Năm phát hành: {movie_info['year']}", "magenta")
                if cmts:
                    self.log(f"   💬 Cào được {len(cmts)} bình luận cũ (Ví dụ: '{cmts[0][:60]}...')", "green")

                self.exporter.save_movie_data(movie_info)

            # Mô phỏng cuộn chuột và đọc nội dung
            start_time = time.time()
            stay_duration = random.uniform(min_stay, max_stay)

            if should_scroll:
                self._simulate_reading(new_page, stay_duration)
            else:
                time.sleep(stay_duration)

            elapsed = round(time.time() - start_time, 1)
            visited_data["stay_seconds"] = elapsed
            self.log(f"   ⏱️ Đã ở lại web phim {elapsed}s", "green")

            # 7. TỰ ĐỘNG BÌNH LUẬN THÔNG MINH (QUY TẮC: CHỈ CMT 1 LẦN / 1 WEBSITE)
            cmt_result = {"success": False, "message": "Chưa bình luận"}
            smart_comment = ""
            author_name = ""

            if auto_comment:
                if already_commented:
                    self.log(f"   🔒 Website [{domain_brand.upper()}] đã được bình luận trong phiên này (quy tắc: 1 cmt / 1 web). Bỏ qua bình luận!", "yellow")
                else:
                    movie_name = movie_info.get("movie_name", final_title)
                    movie_desc = movie_info.get("description", "")
                    custom_name = comment_cfg.get("custom_name")
                    author_name = custom_name if custom_name else self.comment_gen.generate_nickname()
                    author_email = self.comment_gen.generate_email(author_name)
                    custom_templates = comment_cfg.get("custom_templates", [])

                    # Tạo bình luận (AI hoặc Template)
                    smart_comment, cmt_source = self.comment_gen.generate_comment(
                        movie_name=movie_name,
                        description=movie_desc,
                        custom_templates=custom_templates
                    )

                    self.log(f"   💬 [Tự động bình luận] Nguồn: [{cmt_source}]", "cyan")
                    self.log(f"      • Người gửi: [bold]{author_name}[/bold]", "white")
                    self.log(f"      • Nội dung: [italic yellow]\"{smart_comment}\"[/italic yellow]", "white")

                    cmt_result = self.comment_poster.post_comment(
                        page=new_page,
                        comment_text=smart_comment,
                        author_name=author_name,
                        email=author_email
                    )

                    if cmt_result.get("success"):
                        self.log(f"      ✅ {cmt_result.get('message')}", "bold green")
                    else:
                        self.log(f"      ℹ️ {cmt_result.get('message')}", "dim")

                    # Ghi nhận domain này đã được bình luận (Không bình luận trùng)
                    self.commented_domains.add(domain_brand)
                    self.log(f"   🔒 Đã hoàn thành bình luận trên [{domain_brand.upper()}]. Sẽ không bình luận trùng!", "bold green")

                    self.exporter.save_comment_log({
                        "keyword": keyword,
                        "movie_name": movie_name,
                        "url": final_url,
                        "author": author_name,
                        "comment_text": smart_comment,
                        "source": cmt_source,
                        "success": cmt_result.get("success"),
                        "message": cmt_result.get("message")
                    })

            # Chụp ảnh màn hình lưu bằng chứng
            screenshot_path = ""
            if take_screenshot:
                screenshot_path = self._take_screenshot(new_page, keyword, rank, final_url)
                visited_data["screenshot"] = screenshot_path

            # Gửi thông báo về Telegram nếu có bật
            if self.notifier.enabled:
                movie_name = movie_info.get("movie_name", final_title)
                status_icon = "✅ Thành công" if cmt_result.get("success") else "ℹ️ Đã xem"
                tg_caption = (
                    f"🎬 *BOT CÀO PHIM & BÌNH LUẬN*\n"
                    f"🍿 *Phim:* {movie_name}\n"
                    f"🌐 *Website:* {final_url[:70]}\n"
                    f"👤 *Tác giả:* {author_name or 'Ẩn danh'}\n"
                    f"💬 *Bình luận:* \"{smart_comment}\"\n"
                    f"📊 *Trạng thái:* {status_icon}\n"
                    f"⏱️ *Thời gian xem:* {elapsed}s"
                )
                if screenshot_path and os.path.exists(screenshot_path):
                    self.notifier.send_photo(screenshot_path, tg_caption)
                else:
                    self.notifier.send_message(tg_caption)
                self.log("   📱 Đã gửi báo cáo tiến độ về Telegram!", "cyan")

            # Duyệt tập/link nội bộ nếu bật
            if visit_internal:
                internal_clicked = self._visit_internal_page(new_page, final_url)
                visited_data["internal_visited"] = internal_clicked

        except Exception as e:
            visited_data["status"] = f"ERROR: {str(e)[:100]}"
            self.log(f"   ❌ Có lỗi khi cào trang này: {e}", "red")
        finally:
            if new_page:
                try:
                    new_page.close()
                except Exception:
                    pass

            self.exporter.save_visit(visited_data)
            self.log(f"   💾 Đã lưu dữ liệu cào Top {rank} vào CSV & JSON\n", "dim")

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
