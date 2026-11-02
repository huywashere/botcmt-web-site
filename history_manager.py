import json
import os
import time
from urllib.parse import urlparse

class CommentHistoryManager:
    """
    Quản lý bộ nhớ lịch sử các phim đã được bình luận (Deduplication Memory).
    Giúp bot không bình luận trùng lặp 2 lần trên cùng 1 bộ phim khi chạy lặp lại định kỳ.
    """

    def __init__(self, history_file: str = "output/commented_history.json"):
        self.history_file = history_file
        self.history = self._load()

    def _normalize_url(self, url: str) -> str:
        """Chuẩn hóa URL để so sánh chính xác."""
        try:
            parsed = urlparse(url.strip())
            netloc = parsed.netloc.lower()
            path = parsed.path.rstrip("/")
            return f"{parsed.scheme}://{netloc}{path}"
        except Exception:
            return url.strip().rstrip("/")

    def _load(self) -> dict:
        """Tải lịch sử đã lưu từ file JSON."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    def _save(self):
        """Lưu lịch sử ra file JSON."""
        try:
            os.makedirs(os.path.dirname(self.history_file) or ".", exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def is_commented(self, url: str) -> bool:
        """Kiểm tra URL phim này đã từng được bình luận thành công chưa."""
        norm = self._normalize_url(url)
        return norm in self.history

    def record_comment(self, url: str, movie_name: str, author: str, email: str, comment_text: str):
        """Ghi nhận phim đã được bình luận thành công."""
        norm = self._normalize_url(url)
        self.history[norm] = {
            "movie_name": movie_name,
            "url": url,
            "author": author,
            "email": email,
            "comment_text": comment_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save()

    def count(self) -> int:
        """Tổng số lượng phim duy nhất đã được bình luận."""
        return len(self.history)
