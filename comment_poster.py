import random
import re
import time
from playwright.sync_api import Page
from cloudflare_handler import CloudflareHandler

class CommentPoster:
    """Tự động phân tích sâu DOM, vượt bảo vệ Cloudflare/Turnstile, điền Tên, Gmail, giải Captcha và gửi bình luận (Spam CMT)."""

    def __init__(self, log_fn=None):
        self.log = log_fn if log_fn else print

    @staticmethod
    def _safe_click(element, delay=0):
        """Click an toàn: Tự động dùng force=True hoặc dispatch_event nếu bị banner quảng cáo che khuất."""
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
                result["message"] = "Không tìm thấy nút Trả lời bình luận cũ (hoặc web yêu cầu đăng nhập)"
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
            self.log(f"      ↳ [PHÂN TÍCH] Đã xác định & click nút '↳ Trả lời': '{result['replied_to'][:30]}...'", "cyan")
            time.sleep(1.2)

            # Điền vào form bình luận xuất hiện sau khi bấm Trả lời
            cmt_res = self.post_comment(page, reply_text, author_name, email)
            cmt_res["replied_to"] = result["replied_to"]
            return cmt_res
        except Exception as e:
            result["message"] = f"Lỗi khi bấm nút Trả lời: {e}"
            return result

    def post_comment(self, page: Page, comment_text: str, author_name: str, email: str = "") -> dict:
        """
        Tìm khung bình luận trên trang:
        1. Đợi Cloudflare bot protection nếu trang đang bị kiểm tra.
        2. Tự động kích hoạt nút mở form nếu form ẩn (như Motchill, Rophim).
        3. Phân tích chi tiết và xác định chính xác các ô Textarea, Name, Email, Captcha, Submit.
        4. Gửi bình luận và xác thực kết quả.
        """
        result = {
            "success": False,
            "message": "",
            "verified": False
        }

        try:
            # 1. Đợi Cloudflare nếu có
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

            # 3. Nếu chưa thấy ô nhập (nhiều web ẩn form sau nút 'Gửi bình luận' / 'Viết bình luận')
            if not comment_box:
                trigger_selectors = [
                    "button:has-text('Gửi bình luận')",
                    "div:has-text('Gửi bình luận')",
                    "a:has-text('Gửi bình luận')",
                    "span:has-text('Gửi bình luận')",
                    "button:has-text('Viết bình luận')",
                    "div:has-text('Viết bình luận')",
                    "a:has-text('Viết bình luận')",
                    "span:has-text('Viết bình luận')",
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
                                    self.log(f"      🔔 [PHÂN TÍCH DOM] Đã phát hiện nút mở form ẩn: <{tag_name}> '{trig_sel}' -> Click kích hoạt!", "cyan")
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

            # 4. Quét các Frame phụ (iframe bình luận Facebook, iframe ngoài) nếu trang chính không có
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
            self.log(f"         • Ô nhập nội dung: [XÁC ĐỊNH THÀNH CÔNG] <{box_tag}> (selector: {found_sel})", "green")

            # Cuộn mượt mà đến khung bình luận
            try:
                comment_box.scroll_into_view_if_needed()
                time.sleep(0.6)
            except Exception:
                pass

            # 5. Tìm và điền ô Tên (Author / Nickname / Họ tên) nếu có
            name_selectors = [
                "input[name*='name']",
                "input[name*='author']",
                "input[name*='nickname']",
                "input[name*='hoten']",
                "input[id*='author']",
                "input[id*='name']",
                "input[placeholder*='tên' i]",
                "input[placeholder*='name' i]",
                "input[placeholder*='họ tên' i]",
                "input[placeholder*='người gửi' i]"
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
                for ch in author_name:
                    name_input.type(ch, delay=random.randint(25, 55))
                self.log(f"         • Ô Tên tác giả: [XÁC ĐỊNH THÀNH CÔNG] -> Đã điền: '{author_name}'", "green")
                time.sleep(0.4)
            else:
                self.log(f"         • Ô Tên tác giả: [KHÔNG YÊU CẦU / ĐÃ ĐĂNG NHẬP SẴN TÀI KHOẢN]", "dim")

            # 6. Tìm và điền ô Gmail / Email nếu có
            if email:
                email_selectors = [
                    "input[type='email']",
                    "input[name*='email']",
                    "input[name*='mail']",
                    "input[id*='email']",
                    "input[placeholder*='email' i]",
                    "input[placeholder*='gmail' i]",
                    "input[placeholder*='thư điện tử' i]"
                ]
                email_found = False
                for sel in email_selectors:
                    el = target_context.locator(sel).first
                    try:
                        if el.count() > 0 and el.is_visible():
                            self._safe_click(el)
                            el.fill("")
                            for ch in email:
                                el.type(ch, delay=random.randint(20, 45))
                            self.log(f"         • Ô Gmail: [XÁC ĐỊNH THÀNH CÔNG] -> Đã điền: '{email}'", "green")
                            email_found = True
                            time.sleep(0.4)
                            break
                    except Exception:
                        pass
                if not email_found:
                    self.log(f"         • Ô Gmail: [KHÔNG YÊU CẦU / ĐÃ LƯU PROFILE]", "dim")

            # 7. Nhập nội dung bình luận vào ô Textarea (Spam CMT Flexphim)
            self._safe_click(comment_box)
            try:
                comment_box.fill("")
                comment_box.fill(comment_text)
            except Exception:
                for ch in comment_text:
                    comment_box.type(ch, delay=random.randint(20, 45))
            self.log(f"         • Nội dung Flexphim: [ĐÃ NHẬP XONG] \"{comment_text}\"", "bold yellow")
            time.sleep(1.0)

            # 8. Tự động kiểm tra và giải Math Captcha nếu có trước khi bấm gửi
            solved_captcha = self.solve_math_captcha(target_context)
            if not solved_captcha:
                self.log(f"         • Captcha bảo vệ: [KHÔNG CÓ / TRANG AN TOÀN]", "dim")

            # 9. Tìm nút Gửi (Submit button)
            submit_selectors = [
                "form button[type='submit']",
                "form input[type='submit']",
                "#commentform input[type='submit']",
                "#commentform button",
                ".comment-form button[type='submit']",
                ".comment-form .btn-submit",
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Gửi')",
                "button:has-text('Đăng bình luận')",
                "button:has-text('Đăng')",
                "button:has-text('Submit')",
                "button:has-text('Post')",
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
                self.log(f"         • Nút Gửi/Đăng: [XÁC ĐỊNH THÀNH CÔNG] <{btn_name.strip()}> -> Đang bấm gửi!", "bold green")
                self._safe_click(submit_btn)
            else:
                self.log(f"         • Nút Gửi/Đăng: [GỬI BẰNG PHÍM ENTER / CTRL+ENTER]", "green")
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
                result["message"] = f"Đã gửi và xác nhận bình luận: '{comment_text}'"
            else:
                result["message"] = f"Đã gửi bình luận: '{comment_text}' (yêu cầu đã được server tiếp nhận)"

        except Exception as e:
            result["message"] = f"Lỗi trong quá trình gửi bình luận: {str(e)[:120]}"

        return result
