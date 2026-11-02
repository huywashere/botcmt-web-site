import random
import re
from ai_commenter import AICommenter

NAMES = [
    "flexphim.top", "flexphim", "FlexPhim.top", "Minh Tuấn", "Hoàng Nam", "Khánh Linh", "Bảo Trâm", "Hải Đăng",
    "Ngọc Ánh", "Quốc Bảo", "Thuỳ Dương", "Văn Hậu", "Phương Thảo",
    "Trọng Hiếu", "Thanh Hằng", "Đức Anh", "Mỹ Linh", "Việt Hoàng",
    "Quỳnh Nga", "Tuấn Kiệt", "Mai Phương", "Đăng Khoa", "Lan Anh"
]

DEFAULT_FLEXPHIM_TEMPLATES = [
    "qua flexphim xem đi mọi người",
    "qua flexphim xem đi mn ơi, full hd không quảng cáo",
    "qua flexphim xem đi mn ơi",
    "bên flexphim xem mượt hơn nè mọi người ơi",
    "qua flexphim xem đi cả nhà ơi",
    "phim này qua flexphim xem nét hơn nè mn",
    "qua flexphim xem mượt mà không quảng cáo mn ơi",
    "qua flexphim xem đi mọi người ơi, load nhanh lắm",
    "phim này bên flexphim có bản đẹp rồi qua xem đi mọi người",
    "mọi người qua flexphim xem cho mượt nè"
]

DEFAULT_FLEXPHIM_REPLY_TEMPLATES = [
    "qua flexphim xem đi bạn ơi mượt lắm",
    "qua flexphim xem đi mn ơi",
    "chuẩn luôn bạn, mà qua flexphim xem nét hơn nè",
    "bên flexphim có bản full hd không quảng cáo đó bạn qua xem thử đi",
    "qua flexphim xem đi mọi người",
    "mình xem bên flexphim thấy load nhanh hơn hẳn nè bạn",
    "qua flexphim xem mượt lắm bạn ơi, không lo bị gián đoạn",
    "qua flexphim xem đi mn ơi, full hd nét căng"
]

class CommentGenerator:
    """Tạo bình luận thông minh quảng bá Flexphim tự nhiên, mượt mà."""

    def __init__(self, ai_api_key: str = "", use_ai: bool = True):
        self.ai_commenter = AICommenter(api_key=ai_api_key, enabled=use_ai)

    @staticmethod
    def clean_movie_title(raw_title: str) -> str:
        """Lọc bỏ các từ thừa như Full HD, Vietsub, Tập 1, Thuyết Minh, tên web để lấy tên phim chuẩn."""
        if not raw_title:
            return "phim này"

        title = raw_title.strip()

        # Tách theo dấu gạch đứng (|) hoặc gạch ngang (-) nếu có tên web
        parts = re.split(r'[-–|:]', title)
        meaningful_parts = []
        for part in parts:
            p_strip = part.strip()
            # Bỏ qua các phần chỉ là tên web hoặc khẩu hiệu web
            if re.search(r'^(Motchill|Motphim|PhimMoi|RoPhim|VieON|Galaxy\s*Play|Xem\s*Phim|Phim\s*Mới)$', p_strip, re.IGNORECASE):
                continue
            if len(p_strip) > 0:
                meaningful_parts.append(p_strip)

        if meaningful_parts:
            title = meaningful_parts[0]

        patterns_to_remove = [
            r'\(?Vietsub\)?', r'\(?Thuyết\s*Minh\)?', r'\(?Lồng\s*Tiếng\)?',
            r'\(?Full\s*HD\)?', r'\(?HD\)?', r'\(?4K\)?',
            r'Xem\s+phim\s+online', r'Xem\s+phim', r'Phim\s+mới',
            r'Tập\s+\d+(\s*-\s*\d+)?', r'Trọn\s+bộ', r'Bản\s+chuẩn',
            r'Online'
        ]
        for p in patterns_to_remove:
            title = re.sub(p, '', title, flags=re.IGNORECASE)

        title = re.sub(r'[,|/–\-]+', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()

        return title if len(title) >= 3 else "phim này"

    def generate_comment(self, movie_name: str, description: str = "", custom_templates: list = None) -> tuple:
        """
        Tạo câu bình luận quảng bá Flexphim tự nhiên.
        Ưu tiên custom_templates nếu người dùng thiết lập trong cấu hình.
        """
        clean_name = self.clean_movie_title(movie_name)

        # 1. Dùng custom_templates nếu có
        if custom_templates and len(custom_templates) > 0:
            template = random.choice(custom_templates)
            comment = template.format(movie_name=clean_name)
            return comment, "Custom Flexphim Template"

        # 2. Thử dùng AI Gemini (nếu bật và có key)
        if self.ai_commenter.enabled and self.ai_commenter.api_key:
            ai_comment = self.ai_commenter.generate_ai_comment(clean_name, description)
            if ai_comment and len(ai_comment) > 10:
                return ai_comment, "AI Gemini"

        # 3. Dùng Template Flexphim chuẩn
        template = random.choice(DEFAULT_FLEXPHIM_TEMPLATES)
        comment = template.format(movie_name=clean_name)
        return comment, "Flexphim Template"

    def generate_reply(self, movie_name: str, target_author: str = "", target_comment: str = "") -> tuple:
        """
        Tạo câu trả lời (Reply) bình luận của người khác quảng bá Flexphim.
        """
        clean_name = self.clean_movie_title(movie_name)

        tpl = random.choice(DEFAULT_FLEXPHIM_REPLY_TEMPLATES)
        reply_text = tpl.format(movie_name=clean_name)
        if target_author and len(target_author.strip()) > 1 and not target_author.startswith("@"):
            if random.random() < 0.4:
                reply_text = f"@{target_author} {reply_text}"

        return reply_text, "Flexphim Reply"

    @staticmethod
    def generate_nickname() -> str:
        """Tạo tên hiển thị người bình luận tự nhiên."""
        return random.choice(NAMES)

    @staticmethod
    def generate_email(nickname: str) -> str:
        """Tạo email ngẫu nhiên phù hợp với tên."""
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', nickname).lower()
        num = random.randint(10, 999)
        return f"{clean_name}{num}@gmail.com"
