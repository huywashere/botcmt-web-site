import os
import random
import re

class AICommenter:
    """Tạo bình luận phim bằng Google Gemini AI dựa trên cốt truyện thực tế."""

    def __init__(self, api_key: str = "", enabled: bool = True):
        self.api_key = api_key.strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        self.enabled = enabled and bool(self.api_key)
        self.client = None

        if self.enabled:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.enabled = False

    def generate_ai_comment(self, movie_name: str, description: str = "") -> str:
        """Sử dụng Gemini AI để viết một câu bình luận nhận xét tự nhiên, sâu sắc về phim."""
        if not self.enabled or not self.client:
            return ""

        prompt = (
            f"Bạn là một khán giả xem phim người Việt Nam vừa xem xong bộ phim '{movie_name}'.\n"
            f"Tóm tắt nội dung phim: '{description[:500]}'.\n\n"
            "Hãy viết duy nhất 1 câu bình luận ngắn (khoảng 15 đến 30 từ) bằng tiếng Việt tự nhiên, chân thật.\n"
            "Yêu cầu:\n"
            "1. Thể hiện cảm xúc chân thật của người xem (khen kịch bản, diễn xuất, đoạn kết bất ngờ, góc quay hoặc nhạc phim).\n"
            "2. Dùng từ ngữ tự nhiên của giới trẻ xem phim (ví dụ: cuốn dã man, đỉnh chóp, nghẹt thở, cảm động, đáng xem...).\n"
            "3. Không thêm giải thích, không dùng ngoặc kép, chỉ trả về đúng câu bình luận."
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response and response.text:
                comment = response.text.strip().replace('"', '').replace("'", "")
                return comment
        except Exception:
            pass

        return ""

