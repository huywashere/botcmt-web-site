import random
import re
from ai_commenter import AICommenter

NAMES = [
    "Minh Tuấn", "Hoàng Nam", "Khánh Linh", "Bảo Trâm", "Hải Đăng",
    "Ngọc Ánh", "Quốc Bảo", "Thuỳ Dương", "Văn Hậu", "Phương Thảo",
    "Trọng Hiếu", "Thanh Hằng", "Đức Anh", "Mỹ Linh", "Việt Hoàng",
    "Quỳnh Nga", "Tuấn Kiệt", "Mai Phương", "Đăng Khoa", "Lan Anh"
]

SMART_COMMENT_TEMPLATES = [
    "Vừa cày xong bộ {movie_name}, công nhận kịch bản cuốn dã man, đoạn kết bất ngờ ghê!",
    "{movie_name} xem hay thực sự mọi người ơi, diễn xuất của dàn diễn viên nhập tâm dã man.",
    "Đợi mãi {movie_name} bản vietsub nét căng thế này, âm thanh với góc quay đỉnh chóp luôn!",
    "Ai còn đang phân vân thì bật {movie_name} lên xem ngay đi, không phí thời gian tí nào đâu 10/10.",
    "Kịch bản phim {movie_name} chắc tay thật, xem từ đầu đến cuối nghẹt thở không rời mắt được phút nào.",
    "Phim {movie_name} này xem giải trí cuối tuần cùng bạn bè siêu hợp lý luôn, màu phim nghệ thuật ghê.",
    "Mới xem xong {movie_name}, đoạn cao trào làm mình rùng mình luôn, nhạc phim xuất sắc!",
    "Bản vietsub của {movie_name} dịch mượt mà sát nghĩa ghê, cảm ơn subteam nhiều nhé!",
    "Thích nhất thần thái của nhân vật chính trong {movie_name}, coi cuốn từ tập đầu đến giờ.",
    "Cốt truyện {movie_name} lớp lang bất ngờ phết, xem xong vẫn ngồi suy ngẫm mãi, đáng xem nha cả nhà."
]

SMART_REPLY_TEMPLATES = [
    "Chuẩn luôn bạn ơi, mình cũng thấy đoạn đấy xúc động dã man!",
    "Đồng quan điểm với bạn, {movie_name} này xem cuốn thật sự luôn.",
    "Vừa cày xong nghe bạn nói mới để ý, công nhận kịch bản lớp lang ghê.",
    "Cảm ơn review của bạn nhé, nhờ bạn khen mà mình xem thử thấy hay bất ngờ!",
    "Thực sự luôn bạn, đoạn cao trào làm mình rùng mình luôn ấy.",
    "Đúng ý mình luôn, bản vietsub dịch cũng mượt và nét nữa chứ!"
]

class CommentGenerator:
    """Tạo bình luận thông minh (kết hợp AI Gemini và templates thông minh)."""

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

        return title if len(title) >= 3 else "bộ phim này"

    def generate_comment(self, movie_name: str, description: str = "", custom_templates: list = None) -> tuple:
        """
        Tạo bình luận thông minh.
        Ưu tiên dùng Gemini AI nếu có cấu hình.
        Trả về: (câu bình luận, nguồn: 'AI Gemini' hoặc 'Template')
        """
        clean_name = self.clean_movie_title(movie_name)

        # 1. Thử dùng AI Gemini
        if self.ai_commenter.enabled:
            ai_comment = self.ai_commenter.generate_ai_comment(clean_name, description)
            if ai_comment and len(ai_comment) > 10:
                return ai_comment, "AI Gemini"

        # 2. Dùng Template thông minh tự nhiên
        templates = SMART_COMMENT_TEMPLATES
        if custom_templates and len(custom_templates) > 0:
            templates = custom_templates + SMART_COMMENT_TEMPLATES

        template = random.choice(templates)
        comment = template.format(movie_name=clean_name)
        return comment, "Template"

    def generate_reply(self, movie_name: str, target_author: str = "", target_comment: str = "") -> tuple:
        """
        Tạo câu trả lời (Reply) bình luận của người khác.
        Ưu tiên dùng AI Gemini phân tích bình luận gốc để trả lời tự nhiên.
        """
        clean_name = self.clean_movie_title(movie_name)

        # 1. Thử dùng AI Gemini
        if self.ai_commenter.enabled and target_comment:
            ai_reply = self.ai_commenter.generate_ai_reply(clean_name, target_author, target_comment)
            if ai_reply and len(ai_reply) > 5:
                return ai_reply, "AI Gemini Reply"

        # 2. Dùng Template Reply
        tpl = random.choice(SMART_REPLY_TEMPLATES)
        reply_text = tpl.format(movie_name=clean_name)
        if target_author and len(target_author.strip()) > 1 and not target_author.startswith("@"):
            if random.random() < 0.5:
                reply_text = f"@{target_author} {reply_text}"

        return reply_text, "Template Reply"

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
