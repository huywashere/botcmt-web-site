import random
import re
import time
from playwright.sync_api import Page

class CommentPoster:
    """Tự động tìm kiếm khung bình luận, điền Tên, Gmail, Nội dung, giải Captcha và gửi bình luận."""

    def __init__(self, log_fn=None):
        self.log = log_fn if log_fn else print

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

    def solve_math_captcha(self, page: Page) -> bool:
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
                inp = page.locator(sel).first
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
                        self.log(f"      🧮 Đã tự động giải Math Captcha: {n1} {op} {n2} = {ans}", "cyan")
                        time.sleep(0.5)
                        return True
        except Exception:
            pass
        return False

    def post_comment(self, page: Page, comment_text: str, author_name: str, email: str = "") -> dict:
        """
        Tìm khung bình luận trên trang, điền tên và email/gmail, nhập nội dung, sau đó gửi.
        Trả về dict: {"success": bool, "message": str, "verified": bool}
        """
        result = {
            "success": False,
            "message": "",
            "verified": False
        }

        try:
            # 1. Tìm ô nhập bình luận (Textarea)
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
                "textarea"
            ]

            comment_box = None
            for sel in textarea_selectors:
                elements = page.locator(sel).all()
                for el in elements:
                    if el.is_visible():
                        comment_box = el
                        break
                if comment_box:
                    break

            if not comment_box:
                result["message"] = "Không tìm thấy khung bình luận trực tiếp (hoặc trang yêu cầu đăng nhập tài khoản / dùng Facebook iframe)."
                return result

            # Cuộn trang đến khung bình luận mượt mà
            comment_box.scroll_into_view_if_needed()
            time.sleep(1.0)

            # 2. Tìm và điền ô Tên (Name / Author / Nickname) nếu có
            name_selectors = [
                "input[name*='name']",
                "input[name*='author']",
                "input[name*='nickname']",
                "input[id*='author']",
                "input[id*='name']",
                "input[placeholder*='tên' i]",
                "input[placeholder*='name' i]",
                "input[placeholder*='họ tên' i]"
            ]

            name_input = None
            for sel in name_selectors:
                elements = page.locator(sel).all()
                for el in elements:
                    if el.is_visible():
                        name_input = el
                        break
                if name_input:
                    break

            if name_input:
                name_input.click()
                name_input.fill("")
                for ch in author_name:
                    name_input.type(ch, delay=random.randint(40, 80))
                time.sleep(0.5)

            # 3. Tìm và điền ô Gmail / Email nếu có
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
                for sel in email_selectors:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible():
                        el.click()
                        el.fill("")
                        for ch in email:
                            el.type(ch, delay=random.randint(25, 60))
                        time.sleep(0.5)
                        break

            # 4. Nhập nội dung bình luận vào ô Textarea
            comment_box.click()
            comment_box.fill("")
            for ch in comment_text:
                comment_box.type(ch, delay=random.randint(25, 65))
            time.sleep(1.2)

            # 5. Tự động kiểm tra và giải Math Captcha nếu có trước khi bấm gửi
            self.solve_math_captcha(page)

            # 6. Tìm nút Gửi (Submit button)
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Gửi')",
                "button:has-text('Bình luận')",
                "button:has-text('Đăng')",
                "button:has-text('Post')",
                "button:has-text('Comment')",
                "button:has-text('Submit')",
                ".btn-submit-comment",
                ".btn-comment",
                "#submit-comment",
                ".submit-btn"
            ]

            submit_btn = None
            for sel in submit_selectors:
                elements = page.locator(sel).all()
                for el in elements:
                    if el.is_visible():
                        submit_btn = el
                        break
                if submit_btn:
                    break

            if submit_btn:
                submit_btn.click()
            else:
                comment_box.press("Enter")

            time.sleep(2.5)

            # 6. Kiểm tra thông báo phản hồi từ web sau khi gửi
            success_keywords = ["thành công", "cảm ơn", "chờ duyệt", "đã gửi", "success", "submitted"]
            page_text = page.inner_text("body")[:4000].lower() if page.locator("body").count() > 0 else ""
            
            verified = any(kw in page_text for kw in success_keywords) or comment_text.lower() in page_text

            result["success"] = True
            result["verified"] = verified
            if verified:
                result["message"] = "Đã gửi và xác nhận bình luận thành công trên web!"
            else:
                result["message"] = "Đã gửi bình luận (hệ thống web đã nhận request)!"

        except Exception as e:
            result["message"] = f"Lỗi trong quá trình gửi bình luận: {str(e)[:100]}"

        return result
