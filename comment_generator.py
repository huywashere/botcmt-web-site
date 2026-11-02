import random
import re

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

class CommentGenerator:
    """Tạo bình luận thông minh, tự nhiên theo ngữ cảnh phim và người bình luận."""

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
            # Chọn phần chứa tên phim (thường là phần đầu tiên có ý nghĩa)
            title = meaningful_parts[0]

        # Bỏ các tag chất lượng & loại phim
        patterns_to_remove = [
            r'\(?Vietsub\)?', r'\(?Thuyết\s*Minh\)?', r'\(?Lồng\s*Tiếng\)?',
            r'\(?Full\s*HD\)?', r'\(?HD\)?', r'\(?4K\)?',
            r'Xem\s+phim\s+online', r'Xem\s+phim', r'Phim\s+mới',
            r'Tập\s+\d+(\s*-\s*\d+)?', r'Trọn\s+bộ', r'Bản\s+chuẩn',
            r'Online'
        ]
        for p in patterns_to_remove:
            title = re.sub(p, '', title, flags=re.IGNORECASE)

        # Dọn dẹp ký tự thừa còn sót lại như dấu phẩy, gạch chéo, dấu chấm
        title = re.sub(r'[,|/–\-]+', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()

        return title if len(title) >= 3 else "bộ phim này"

    @staticmethod
    def generate_comment(movie_name: str, custom_templates: list = None) -> str:
        """Tạo 1 bình luận thông minh mang phong cách người xem phim chân thật."""
        clean_name = CommentGenerator.clean_movie_title(movie_name)

        templates = SMART_COMMENT_TEMPLATES
        if custom_templates and len(custom_templates) > 0:
            templates = custom_templates + SMART_COMMENT_TEMPLATES

        template = random.choice(templates)
        comment = template.format(movie_name=clean_name)
        return comment

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
