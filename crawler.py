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
        headless = browser_cfg.get("headless", False)
        slow_mo = browser_cfg.get("slow_mo_ms", 30)
        width = browser_cfg.get("window_width", 1280)
        height = browser_cfg.get("window_height", 800)

        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1280,800"
            ]
        )

        user_agent = random.choice(USER_AGENTS)
        context = browser.new_context(
            user_agent=user_agent,
            locale="vi-VN",
            viewport={"width": width, "height": height}
        )

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['vi-VN', 'vi', 'en-US', 'en']
            });
        """)

        return browser, context

    def run(self, keywords=None):
        if not keywords:
            keywords = self.config.get("search", {}).get("keywords", [])

        if not keywords:
            self.log("[red]Không tìm thấy từ khóa nào để tìm kiếm![/red]")
            return

        with sync_playwright() as p:
            browser, context = self._init_browser(p)
            search_page = context.new_page()

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
                self.log("\n🧹 Đang đóng trình duyệt...", "dim")
                browser.close()
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

        # 5. Thu thập & Lọc kết quả web phim (hỗ trợ cuộn Google để tìm thêm nếu trang 1 chưa đủ)
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

            # 7. TỰ ĐỘNG BÌNH LUẬN THÔNG MINH
            if auto_comment:
                movie_name = movie_info.get("movie_name", final_title)
                custom_name = comment_cfg.get("custom_name")
                author_name = custom_name if custom_name else CommentGenerator.generate_nickname()
                author_email = CommentGenerator.generate_email(author_name)
                custom_templates = comment_cfg.get("custom_templates", [])

                smart_comment = CommentGenerator.generate_comment(movie_name, custom_templates)

                self.log(f"   💬 [Tự động bình luận] Đang soạn bình luận thông minh...", "cyan")
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

                self.exporter.save_comment_log({
                    "keyword": keyword,
                    "movie_name": movie_name,
                    "url": final_url,
                    "author": author_name,
                    "comment_text": smart_comment,
                    "success": cmt_result.get("success"),
                    "message": cmt_result.get("message")
                })

            # Duyệt tập/link nội bộ nếu bật
            if visit_internal:
                internal_clicked = self._visit_internal_page(new_page, final_url)
                visited_data["internal_visited"] = internal_clicked

            # Chụp ảnh màn hình lưu bằng chứng
            if take_screenshot:
                screenshot_filename = self._take_screenshot(new_page, keyword, rank, final_url)
                visited_data["screenshot"] = screenshot_filename

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
