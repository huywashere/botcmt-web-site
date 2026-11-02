import re
from urllib.parse import urlparse
from playwright.sync_api import Page

class MovieExtractor:
    """Bộ bóc tách thông tin phim & bình luận từ các website phim."""

    @staticmethod
    def is_movie_content(title: str, url: str, movie_keywords: list, allowed_domains: list, excluded_domains: list, cite_text: str = "") -> bool:
        combined = f"{title} {url} {cite_text}".lower()

        # Kiểm tra nếu domain nằm trong danh sách loại trừ
        for exc in excluded_domains:
            if exc.lower() in combined:
                return False

        # Nếu người dùng có danh sách domain cụ thể (allowed_domains)
        if allowed_domains and len(allowed_domains) > 0:
            for domain in allowed_domains:
                if domain.lower() in combined:
                    return True
            return False

        # Kiểm tra từ khóa liên quan đến phim trong URL, Tiêu đề hoặc Cite
        for kw in movie_keywords:
            kw_clean = kw.lower().strip()
            if kw_clean and kw_clean in combined:
                return True

        return False

    @staticmethod
    def extract_movie_info(page: Page) -> dict:
        """Trích xuất thông tin chi tiết phim qua JavaScript siêu nhanh: tiêu đề, mô tả, ảnh, năm, bình luận."""
        js_code = """
        () => {
            let data = {
                movie_name: "",
                description: "",
                thumbnail: "",
                year: "",
                comments: []
            };

            // 1. Tên phim
            const h1 = document.querySelector('h1');
            if (h1 && h1.innerText.trim()) {
                data.movie_name = h1.innerText.trim();
            } else {
                const ogTitle = document.querySelector('meta[property="og:title"]');
                if (ogTitle && ogTitle.content) {
                    data.movie_name = ogTitle.content.trim();
                }
            }

            // 2. Mô tả
            const ogDesc = document.querySelector('meta[property="og:description"]');
            if (ogDesc && ogDesc.content) {
                data.description = ogDesc.content.trim();
            } else {
                const descMeta = document.querySelector('meta[name="description"]');
                if (descMeta && descMeta.content) {
                    data.description = descMeta.content.trim();
                }
            }

            // 3. Ảnh Thumbnail
            const ogImg = document.querySelector('meta[property="og:image"]');
            if (ogImg && ogImg.content) {
                data.thumbnail = ogImg.content.trim();
            }

            // 4. Bình luận (Comments)
            const selectors = [
                '.cmt-content', '.comment-content', '.comment-item p',
                '.comment_item', "[class*='comment-text']", "[class*='cmt-text']",
                '.box-comment p', '#list-comments li', '.comment-body'
            ];

            for (let sel of selectors) {
                let els = document.querySelectorAll(sel);
                if (els && els.length > 0) {
                    for (let i = 0; i < Math.min(els.length, 10); i++) {
                        let t = els[i].innerText ? els[i].innerText.trim() : "";
                        if (t.length > 5 && !data.comments.includes(t)) {
                            data.comments.push(t);
                        }
                    }
                    if (data.comments.length > 0) break;
                }
            }

            return data;
        }
        """
        try:
            res = page.evaluate(js_code)
            # Trích xuất năm phát hành bằng regex
            full_text = page.inner_text("body")[:3000] if page.locator("body").count() > 0 else ""
            year_match = re.search(r'\b(20[0-2][0-9]|19[89][0-9])\b', full_text)
            if year_match:
                res["year"] = year_match.group(1)
            return res
        except Exception:
            return {
                "movie_name": "",
                "description": "",
                "thumbnail": "",
                "year": "",
                "comments": []
            }
