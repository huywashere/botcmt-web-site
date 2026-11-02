import csv
import json
import os
from datetime import datetime

class DataExporter:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.screenshots_dir = os.path.join(output_dir, "screenshots")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)

        self.csv_path = os.path.join(self.output_dir, "visit_history.csv")
        self.json_path = os.path.join(self.output_dir, "visit_history.json")

        self.movies_csv_path = os.path.join(self.output_dir, "movies_crawled.csv")
        self.movies_json_path = os.path.join(self.output_dir, "movies_crawled.json")

        self.comments_csv_path = os.path.join(self.output_dir, "comments_posted.csv")
        self.comments_json_path = os.path.join(self.output_dir, "comments_posted.json")

        self._init_csv()

    def _init_csv(self):
        """Khởi tạo tiêu đề cột cho CSV nếu file chưa tồn tại."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Thời gian",
                    "Từ khóa",
                    "Thứ hạng Top",
                    "Tiêu đề website",
                    "URL",
                    "Thời gian lưu lại (giây)",
                    "Duyệt link nội bộ",
                    "Trạng thái",
                    "Ảnh chụp màn hình"
                ])

        if not os.path.exists(self.movies_csv_path):
            with open(self.movies_csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Thời gian",
                    "Từ khóa",
                    "Thứ hạng Top",
                    "Tên phim",
                    "Năm phát hành",
                    "Mô tả phim",
                    "URL",
                    "Số bình luận cào được",
                    "Bình luận mẫu",
                    "Ảnh thumbnail"
                ])

        if not os.path.exists(self.comments_csv_path):
            with open(self.comments_csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Thời gian",
                    "Từ khóa",
                    "Tên phim",
                    "URL website",
                    "Người gửi (Nickname)",
                    "Nội dung bình luận",
                    "Trạng thái gửi",
                    "Chi tiết"
                ])

    def save_visit(self, data: dict):
        """Lưu một bản ghi truy cập vào CSV và JSON."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.csv_path, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                data.get("keyword", ""),
                data.get("rank", ""),
                data.get("title", ""),
                data.get("url", ""),
                data.get("stay_seconds", 0),
                data.get("internal_visited", False),
                data.get("status", "SUCCESS"),
                data.get("screenshot", "")
            ])

        all_data = []
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except Exception:
                all_data = []

        data_entry = {
            "timestamp": timestamp,
            **data
        }
        all_data.append(data_entry)

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

    def save_movie_data(self, data: dict):
        """Lưu dữ liệu cào phim chi tiết."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comments = data.get("comments", [])
        sample_cmt = " | ".join(comments[:3]) if comments else ""

        with open(self.movies_csv_path, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                data.get("keyword", ""),
                data.get("rank", ""),
                data.get("movie_name", ""),
                data.get("year", ""),
                data.get("description", ""),
                data.get("url", ""),
                len(comments),
                sample_cmt,
                data.get("thumbnail", "")
            ])

        all_movies = []
        if os.path.exists(self.movies_json_path):
            try:
                with open(self.movies_json_path, "r", encoding="utf-8") as f:
                    all_movies = json.load(f)
            except Exception:
                all_movies = []

        movie_entry = {
            "timestamp": timestamp,
            **data
        }
        all_movies.append(movie_entry)

        with open(self.movies_json_path, "w", encoding="utf-8") as f:
            json.dump(all_movies, f, ensure_ascii=False, indent=2)

    def save_comment_log(self, data: dict):
        """Lưu lịch sử đã tự động gửi bình luận trên web phim."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.comments_csv_path, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                data.get("keyword", ""),
                data.get("movie_name", ""),
                data.get("url", ""),
                data.get("author", ""),
                data.get("comment_text", ""),
                "THÀNH CÔNG" if data.get("success") else "THẤT BẠI",
                data.get("message", "")
            ])

        all_cmts = []
        if os.path.exists(self.comments_json_path):
            try:
                with open(self.comments_json_path, "r", encoding="utf-8") as f:
                    all_cmts = json.load(f)
            except Exception:
                all_cmts = []

        cmt_entry = {
            "timestamp": timestamp,
            **data
        }
        all_cmts.append(cmt_entry)

        with open(self.comments_json_path, "w", encoding="utf-8") as f:
            json.dump(all_cmts, f, ensure_ascii=False, indent=2)
