import random
import re
import time
from playwright.sync_api import Page
from cloudflare_handler import CloudflareHandler

class CommentPoster:
    """Tự động phân tích sâu DOM, xử lý Cloudflare/Turnstile trong form, điền Tên (flexphim.top), Nội dung và gửi bình luận."""

    def __init__(self, log_fn=None):
        self.log = log_fn if log_fn else print

    @staticmethod
    def _safe_click(element, delay=0):
        """Click an toàn: Tự động dùng force=True hoặc dispatch_event nếu bị che khuất."""
        try:
            element.click(timeout=2500, delay=delay)
            return True
        except Exception:
            try:
                element.click(force=True, timeout=1500, delay=delay)
                return True
            except Exception:
                try:
                    element.dispatch_event("click")
                    return True
                except Exception:
                    pass
        return False

    def vote_5_stars(self, page: Page) -> bool:
        """Tự động tìm nút vote 5 sao trên trang phim và bấm đánh giá."""
        star_selectors = [
            ".star-5",
            "[data-rating='5']",
            "[data-score='5']",
            "[data-value='5']",
            ".rating-stars span:nth-child(5)",
            ".stars-rating i:nth-child(5)",
            ".fa-star:nth-child(5)",
            "#star-5",
            ".star-vote:nth-child(5)",
            ".btn-rate[data-val='5']",
            "a[title*='5 sao' i]",
            "span[title*='5 sao' i]",
            "button[title*='5 sao' i]",
            ".rate-star[data-val='5']"
        ]
        try:
            for sel in star_selectors:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    el.scroll_into_view_if_needed()
                    time.sleep(0.4)
                    el.click(delay=random.randint(50, 100))
                    self.log("      ⭐ Đã tự động đánh giá 5 sao cho phim!", "bold yellow")
                    time.sleep(0.6)
                    return True
        except Exception:
            pass
        return False

    def solve_math_captcha(self, page_or_frame) -> bool:
        """Tự động phát hiện và giải câu hỏi bảo vệ / Math Captcha (ví dụ: 3 + 5 = ?)."""
        try:
            captcha_inputs = [
                "input[name*='captcha']",
                "input[name*='math']",
                "input[name*='question']",
                "input[id*='captcha']",
                "input[placeholder*='kết quả' i]",
                "input[placeholder*='tính' i]",
                "input[placeholder*='bảo vệ' i]",
                "input[placeholder*='câu hỏi' i]"
            ]
            for sel in captcha_inputs:
                inp = page_or_frame.locator(sel).first
                if inp.count() > 0 and inp.is_visible():
                    context_text = ""
                    try:
                        parent = inp.locator("xpath=..")
                        context_text = parent.inner_text()
                    except Exception:
                        pass

                    if not context_text:
                        context_text = inp.get_attribute("placeholder") or ""

                    match = re.search(r"(\d{1,2})\s*([\+\-\*])\s*(\d{1,2})", context_text)
                    if match:
                        n1 = int(match.group(1))
                        op = match.group(2)
                        n2 = int(match.group(3))
                        ans = n1 + n2 if op == "+" else (n1 - n2 if op == "-" else n1 * n2)
                        inp.click()
                        inp.fill(str(ans))
                        self.log(f"         • Captcha bảo vệ: [ĐÃ GIẢI MATH CAPTCHA] {n1} {op} {n2} = {ans}", "bold cyan")
                        time.sleep(0.5)
                        return True
        except Exception:
            pass
        return False

    def solve_form_turnstile(self, page_or_frame) -> bool:
        """
        Tự động phát hiện và giải quyết widget Cloudflare Turnstile nhúng trong form bình luận:
        1. Kiểm tra iframe Turnstile (challenges.cloudflare.com) hoặc input token.
        2. Tự động click vào checkbox xác minh nếu chưa hoàn tất.
        3. Đợi trạng thái 'Thành công!' / 'Success!' xuất hiện trước khi cho phép bấm gửi.
        """
        try:
            has_turnstile = page_or_frame.evaluate("""() => {
                return Boolean(
                    document.querySelector('.cf-turnstile') ||
                    document.querySelector('#turnstile-wrapper') ||
                    document.querySelector('iframe[src*="challenges.cloudflare.com"]') ||
                    document.querySelector('input[name="cf-turnstile-response"]')
                );
            }""")

            if not has_turnstile:
                return False

            self.log("         • Cloudflare Turnstile: [PHÁT HIỆN TRONG FORM BÌNH LUẬN]", "cyan")

            # Kiểm tra xem đã giải xong sẵn chưa
            already_solved = page_or_frame.evaluate("""() => {
                const token = document.querySelector('input[name="cf-turnstile-response"]');
                if (token && token.value && token.value.length > 10) return true;
                const txt = document.body ? document.body.innerText : '';
                return txt.includes('Thành công!') || txt.includes('Success!');
            }""")

            if already_solved:
                self.log("         • Cloudflare Turnstile: [ĐÃ XÁC THỰC THÀNH CÔNG! ✓]", "bold green")
                return True

            # Tìm iframe Turnstile
            turnstile_frame = None
            frames_to_check = page_or_frame.frames if hasattr(page_or_frame, 'frames') else (page_or_frame.page.frames if hasattr(page_or_frame, 'page') else [])
            for frame in frames_to_check:
                if "challenges.cloudflare.com" in (frame.url or "").lower():
                    turnstile_frame = frame
                    break

            if turnstile_frame:
                cb_selectors = [
                    "input[type='checkbox']",
                    ".ctp-checkbox-label",
                    "#challenge-stage",
                    "label.ctp-checkbox-label",
                    "span.mark",
                    "div[id*='turnstile']"
                ]
                for c_sel in cb_selectors:
                    cb = turnstile_frame.locator(c_sel).first
                    try:
                        if cb.count() > 0 and cb.is_visible():
                            cb.click(timeout=2500)
                            self.log("         • Cloudflare Turnstile: [ĐÃ CLICK VÀO CHECKBOX XÁC MINH]", "yellow")
                            break
                    except Exception:
                        pass

            # Đợi tối đa 10s để Turnstile xác thực và điền token
            start = time.time()
            while time.time() - start < 10:
                is_done = page_or_frame.evaluate("""() => {
                    const token = document.querySelector('input[name="cf-turnstile-response"]');
                    if (token && token.value && token.value.length > 10) return true;
                    const txt = document.body ? document.body.innerText : '';
                    return txt.includes('Thành công!') || txt.includes('Success!');
                }""")
                if is_done:
                    self.log("         • Cloudflare Turnstile: [XÁC THỰC THÀNH CÔNG - 'Thành công!' ✓]", "bold green")
                    time.sleep(0.5)
                    return True
                time.sleep(1.0)

            return True
        except Exception as e:
            self.log(f"         • Cloudflare Turnstile: {e}", "dim")
            return False

    def reply_to_comment(self, page: Page, reply_text: str, author_name: str, email: str = "") -> dict:
        """
        Tìm bình luận có sẵn của người khác, bấm nút '↳ Trả lời' (Reply) và gửi bình luận.
        Nếu không có nút Trả lời, trả về success=False để chuyển sang bình luận mới thông thường.
        """
        result = {"success": False, "message": "", "replied_to": ""}
        try:
            # 1. Đợi Cloudflare nếu có
            CloudflareHandler.wait_and_bypass(page, log_fn=self.log)

            # Cuộn xuống khu vực bình luận trước
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.75)")
                time.sleep(1.2)
            except Exception:
                pass

            reply_selectors = [
                "button:has-text('Trả lời')",
                "a:has-text('Trả lời')",
                "span:has-text('Trả lời')",
                "div:has-text('Trả lời')",
                "*[class*='reply']:has-text('Trả lời')",
                "*[onclick*='reply' i]",
                "a.reply",
                "button.reply",
                ".comment-reply-link",
                ".btn-reply",
                "a:has-text('Reply')",
                "button:has-text('Reply')"
            ]
            reply_btn = None
            for sel in reply_selectors:
                btns = page.locator(sel).all()
                for b in btns[:8]:
                    try:
                        if b.is_visible():
                            reply_btn = b
                            break
                    except Exception:
                        pass
                if reply_btn:
                    break

            if not reply_btn:
                result["message"] = "Không tìm thấy nút Trả lời bình luận cũ"
                return result

            # Lấy thông tin trích dẫn người được trả lời
            try:
                parent_el = reply_btn.locator("xpath=ancestor::*[contains(@class, 'comment') or contains(@id, 'comment') or contains(@class, 'flex')][1]")
                result["replied_to"] = parent_el.inner_text()[:40].replace("\n", " ").strip()
            except Exception:
                pass

            reply_btn.scroll_into_view_if_needed()
            time.sleep(0.5)
            self._safe_click(reply_btn)
            self.log(f"      ↳ [PHÂN TÍCH] Đã click nút '↳ Trả lời': '{result['replied_to'][:30]}...'", "cyan")
            time.sleep(1.2)

            # Điền vào form bình luận xuất hiện sau khi bấm Trả lời
            cmt_res = self.post_comment(page, reply_text, author_name, email)
            cmt_res["replied_to"] = result["replied_to"]
            return cmt_res
        except Exception as e:
            result["message"] = f"Lỗi khi bấm nút Trả lời: {e}"
            return result

    def post_comment(self, page: Page, comment_text: str, author_name: str = "flexphim.top", email: str = "") -> dict:
        """
        Tìm khung bình luận trên trang:
        1. Đợi Cloudflare bot protection nếu trang đang bị kiểm tra.
        2. Tự động kích hoạt nút mở form nếu form ẩn (như Motchill: 'Viết bình luận' / 'Gửi bình luận').
        3. Nhập nội dung bình luận vào Textarea (VD: 'qua flexphim xem đi mọi người').
        4. Nhập Tên tác giả vào ô text bên dưới (VD: 'flexphim.top').
        5. Xử lý Cloudflare Turnstile trong form (đợi tick xanh 'Thành công!').
        6. Bấm nút 'Gửi bình luận' và xác thực kết quả.
        """
        result = {
            "success": False,
            "message": "",
            "verified": False
        }

        try:
            # 1. Đợi Cloudflare bảo vệ trang nếu có
            CloudflareHandler.wait_and_bypass(page, log_fn=self.log)

            # Cuộn trang xuống khu vực bình luận
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.7)")
                time.sleep(1.0)
            except Exception:
                pass

            textarea_selectors = [
                "textarea[name*='comment']",
                "textarea[name*='content']",
                "textarea[name*='cmt']",
                "textarea[name*='message']",
                "textarea[id*='comment']",
                "textarea[id*='cmt']",
                "textarea[placeholder*='bình luận' i]",
                "textarea[placeholder*='comment' i]",
                "textarea[placeholder*='ý kiến' i]",
                "textarea[placeholder*='nội dung' i]",
                "#comment-form textarea",
                ".box-comment textarea",
                ".comment-box textarea",
                "div[contenteditable='true']",
                "textarea",
                "input[placeholder*='viết bình luận' i]",
                "input[placeholder*='bình luận' i]"
            ]

            target_context = page
            comment_box = None
            found_sel = ""

            # 2. Tìm ô nhập bình luận trực tiếp trước
            for sel in textarea_selectors:
                elements = page.locator(sel).all()
                for el in elements:
                    try:
                        if el.is_visible():
                            comment_box = el
                            found_sel = sel
                            break
                    except Exception:
                        pass
                if comment_box:
                    break

            # 3. Nếu chưa thấy ô nhập (nhiều web ẩn form sau nút 'Viết bình luận' / 'Gửi bình luận')
            if not comment_box:
                trigger_selectors = [
                    "div:has-text('Viết bình luận')",
                    "button:has-text('Viết bình luận')",
                    "h2:has-text('Viết bình luận')",
                    "h3:has-text('Viết bình luận')",
                    "span:has-text('Viết bình luận')",
                    "a:has-text('Viết bình luận')",
                    "button:has-text('Gửi bình luận')",
                    "div:has-text('Gửi bình luận')",
                    "a:has-text('Gửi bình luận')",
                    "span:has-text('Gửi bình luận')",
                    "div[class*='bg-[#FF7E08]']:has-text('bình luận')",
                    "button[class*='bg-[#FF7E08]']",
                    "*[class*='bg-[#FF7E08]']",
                    ".btn-comment",
                    ".btn-write-comment",
                    "#btn-comment",
                    "button:has-text('Bình luận')",
                    "a:has-text('Bình luận')"
                ]

                for trig_sel in trigger_selectors:
                    triggers = page.locator(trig_sel).all()
                    for trig in triggers:
                        try:
                            if trig.is_visible():
                                trig.scroll_into_view_if_needed()
                                time.sleep(0.4)
                                clicked = self._safe_click(trig)
                                if clicked:
                                    tag_name = trig.evaluate("el => el.tagName")
                                    self.log(f"      🔔 [PHÂN TÍCH DOM] Đã phát hiện & click mở khung form ẩn: <{tag_name}> '{trig_sel}'", "cyan")
                                    time.sleep(1.2)
                                    break
                        except Exception:
                            pass

                    # Kiểm tra lại xem textarea đã xuất hiện chưa
                    for sel2 in textarea_selectors:
                        elements = page.locator(sel2).all()
                        for el in elements:
                            try:
                                if el.is_visible():
                                    comment_box = el
                                    found_sel = sel2
                                    break
                            except Exception:
                                pass
                        if comment_box:
                            break
                    if comment_box:
                        break

            # 4. Quét các Frame phụ (iframe ngoài, widget) nếu trang chính không có
            if not comment_box:
                for frame in page.frames:
                    if frame == page.main_frame:
                        continue
                    try:
                        for sel in textarea_selectors:
                            elements = frame.locator(sel).all()
                            for el in elements:
                                try:
                                    if el.is_visible():
                                        comment_box = el
                                        found_sel = sel
                                        target_context = frame
                                        self.log(f"      🖼️ [PHÂN TÍCH DOM] Đã tìm thấy khung bình luận trong iframe con!", "cyan")
                                        break
                                except Exception:
                                    pass
                            if comment_box:
                                break
                        if comment_box:
                            break
                    except Exception:
                        pass

            if not comment_box:
                result["message"] = "Không tìm thấy khung bình luận trực tiếp (hoặc trang web yêu cầu đăng nhập tài khoản / dính Cloudflare chặn)."
                return result

            # Báo cáo kết quả phân tích DOM
            box_tag = comment_box.evaluate("el => el.tagName")
            self.log(f"      🔍 [PHÂN TÍCH DOM BÌNH LUẬN]", "bold cyan")
            self.log(f"         • Ô nhập nội dung: [XÁC ĐỊNH THÀNH CÔNG] <{box_tag}> ({found_sel})", "green")

            # Cuộn mượt mà đến khung bình luận
            try:
                comment_box.scroll_into_view_if_needed()
                time.sleep(0.6)
            except Exception:
                pass

            # 5. Nhập nội dung bình luận vào ô Textarea (VD: 'qua flexphim xem đi mọi người')
            self._safe_click(comment_box)
            try:
                comment_box.fill("")
                comment_box.fill(comment_text)
            except Exception:
                for ch in comment_text:
                    comment_box.type(ch, delay=random.randint(20, 45))
            self.log(f"         • Nội dung Flexphim: [ĐÃ NHẬP XONG] \"{comment_text}\"", "bold yellow")
            time.sleep(0.6)

            # 6. Tìm và điền ô Tên / Tên web bên dưới ô Textarea (VD: 'flexphim.top')
            name_val = author_name if author_name else "flexphim.top"
            name_selectors = [
                "input[name*='name']",
                "input[name*='author']",
                "input[name*='nickname']",
                "input[name*='user']",
                "input[name*='hoten']",
                "input[placeholder*='tên' i]",
                "input[placeholder*='name' i]",
                "input[placeholder*='nickname' i]",
                "input[placeholder*='họ tên' i]",
                "input[placeholder*='người gửi' i]",
                "input[placeholder*='website' i]",
                "input[placeholder*='web' i]",
                "form input[type='text']",
                "input:not([type='hidden']):not([type='submit']):not([type='checkbox']):not([name='q'])"
            ]

            name_input = None
            for sel in name_selectors:
                elements = target_context.locator(sel).all()
                for el in elements:
                    try:
                        if el.is_visible():
                            name_input = el
                            break
                    except Exception:
                        pass
                if name_input:
                    break

            if name_input:
                self._safe_click(name_input)
                name_input.fill("")
                for ch in name_val:
                    name_input.type(ch, delay=random.randint(25, 55))
                self.log(f"         • Ô Tên / Website tác giả: [XÁC ĐỊNH THÀNH CÔNG] -> Đã điền: '{name_val}'", "bold green")
                time.sleep(0.4)
            else:
                self.log(f"         • Ô Tên tác giả: [KHÔNG YÊU CẦU / ĐÃ LƯU TÀI KHOẢN]", "dim")

            # 7. Tìm và điền ô Gmail / Email nếu có (và khác ô Tên)
            if email:
                email_selectors = [
                    "input[type='email']",
                    "input[name*='email']",
                    "input[name*='mail']",
                    "input[id*='email']",
                    "input[placeholder*='email' i]",
                    "input[placeholder*='gmail' i]"
                ]
                for sel in email_selectors:
                    el = target_context.locator(sel).first
                    try:
                        if el.count() > 0 and el.is_visible() and el != name_input:
                            self._safe_click(el)
                            el.fill("")
                            for ch in email:
                                el.type(ch, delay=random.randint(20, 45))
                            self.log(f"         • Ô Gmail: [XÁC ĐỊNH THÀNH CÔNG] -> Đã điền: '{email}'", "green")
                            time.sleep(0.4)
                            break
                    except Exception:
                        pass

            # 8. XỬ LÝ CLOUDFLARE TURNSTILE TRONG FORM (Đợi tick xanh 'Thành công!' như trong ảnh)
            turnstile_solved = self.solve_form_turnstile(target_context)
            if not turnstile_solved:
                # Kiểm tra thêm Math Captcha nếu trang không dùng Turnstile
                self.solve_math_captcha(target_context)

            time.sleep(1.0)

            # 9. Tìm nút Gửi (Submit button: 'Gửi bình luận')
            submit_selectors = [
                "button:has-text('Gửi bình luận')",
                "input[value='Gửi bình luận']",
                "button:has-text('Gửi')",
                "button:has-text('Đăng bình luận')",
                "button:has-text('Đăng')",
                "form button[type='submit']",
                "form input[type='submit']",
                "button[type='submit']",
                "input[type='submit']",
                ".btn-submit-comment",
                ".btn-comment-submit",
                "#submit-comment",
                ".submit-btn"
            ]

            submit_btn = None
            for sel in submit_selectors:
                elements = target_context.locator(sel).all()
                for el in elements:
                    try:
                        if el.is_visible():
                            submit_btn = el
                            break
                    except Exception:
                        pass
                if submit_btn:
                    break

            if submit_btn:
                btn_name = submit_btn.evaluate("el => el.innerText || el.value || el.tagName")
                self.log(f"         • Nút Bấm Gửi: [XÁC ĐỊNH THÀNH CÔNG] <{btn_name.strip()}> -> Đang bấm gửi bình luận!", "bold green")
                self._safe_click(submit_btn)
            else:
                self.log(f"         • Nút Bấm Gửi: [GỬI BẰNG PHÍM ENTER / CTRL+ENTER]", "green")
                try:
                    comment_box.press("Control+Enter")
                except Exception:
                    comment_box.press("Enter")

            time.sleep(2.5)

            # 10. Kiểm tra thông báo phản hồi từ web sau khi gửi
            success_keywords = ["thành công", "cảm ơn", "chờ duyệt", "đã gửi", "success", "submitted"]
            page_text = page.inner_text("body")[:5000].lower() if page.locator("body").count() > 0 else ""
            
            verified = any(kw in page_text for kw in success_keywords) or comment_text.lower() in page_text

            result["success"] = True
            result["verified"] = verified
            if verified:
                result["message"] = f"Đã gửi và xác nhận bình luận: '{comment_text}' (Tác giả: {name_val})"
            else:
                result["message"] = f"Đã gửi bình luận: '{comment_text}' (Tác giả: {name_val})"

        except Exception as e:
            result["message"] = f"Lỗi trong quá trình gửi bình luận: {str(e)[:120]}"

        return result
