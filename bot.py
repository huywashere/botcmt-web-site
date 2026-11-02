import argparse
import json
import os
import sys

# Đảm bảo mã hóa UTF-8 cho console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from crawler import GoogleTopBot
from data_exporter import DataExporter

console = Console()

def print_banner():
    banner_text = (
        "[bold cyan]🎬 BOT TỰ ĐỘNG CÀO DỮ LIỆU & BÌNH LUẬN THÔNG MINH WEB PHIM TOP GOOGLE[/bold cyan]\n"
        "[italic green]• Chỉ cào đúng 4 web phim: Motchill, Motphim, Phimmoi, Rophim[/italic green]\n"
        "[italic green]• Tự động tạo bình luận thông minh sát với tên phim & cốt truyện[/italic green]\n"
        "[italic green]• Giả lập điền tên, nội dung và gửi bình luận (Human Typing)[/italic green]\n"
        "[italic green]• Tự động ghi nhận lịch sử bình luận và dữ liệu ra file CSV & JSON[/italic green]"
    )
    console.print(Panel(banner_text, border_style="bold blue", expand=False))

def load_config(config_path="config.json") -> dict:
    default_config = {
        "search": {
            "keywords": ["xem phim motchill vietsub"],
            "keywords_file": "keywords.txt",
            "top_limit": 3,
            "google_domain": "https://www.google.com"
        },
        "movie_filter": {
            "only_movie_sites": True,
            "keywords_matching": ["motchill", "motphim", "phimmoi", "rophim"],
            "allowed_domains": ["motchill", "motphim", "phimmoi", "rophim"],
            "excluded_domains": ["facebook.com", "youtube.com", "tiktok.com", "wikipedia.org"],
            "crawl_details": True,
            "crawl_comments": True
        },
        "comment": {
            "auto_comment": True,
            "custom_name": "",
            "custom_templates": []
        },
        "browser": {
            "headless": False,
            "slow_mo_ms": 30,
            "window_width": 1280,
            "window_height": 800
        },
        "behavior": {
            "min_stay_seconds": 6,
            "max_stay_seconds": 12,
            "scroll_page": True,
            "visit_internal_link": True,
            "take_screenshot": True
        },
        "output": {
            "save_json": True,
            "save_csv": True,
            "output_dir": "output"
        }
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    if isinstance(v, dict) and k in default_config:
                        default_config[k].update(v)
                    else:
                        default_config[k] = v
        except Exception as e:
            console.print(f"[yellow]⚠️ Lỗi đọc file {config_path}: {e}. Dùng cấu hình mặc định.[/yellow]")

    return default_config

def load_keywords_from_file(filepath: str) -> list:
    keywords = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                kw = line.strip()
                if kw and not kw.startswith("#"):
                    keywords.append(kw)
    return keywords

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Bot cào web phim và tự động bình luận thông minh")
    parser.add_argument("-k", "--keyword", type=str, help="Từ khóa phim cần tìm kiếm")
    parser.add_argument("-f", "--file", type=str, help="File danh sách từ khóa")
    parser.add_argument("-t", "--top", type=int, help="Số lượng top web phim cần cào/bình luận")
    parser.add_argument("--author", type=str, help="Tên người bình luận (mặc định sẽ tự tạo tên ngẫu nhiên)")
    parser.add_argument("--comment", action="store_true", help="Bật tính năng tự động bình luận")
    parser.add_argument("--no-comment", action="store_true", help="Tắt tính năng tự động bình luận")
    parser.add_argument("--headless", action="store_true", help="Chạy ngầm không hiện trình duyệt")
    parser.add_argument("--visible", action="store_true", help="Hiện cửa sổ trình duyệt theo dõi trực quan")
    parser.add_argument("--stay", type=int, help="Thời gian ở lại xem mỗi website (giây)")

    args = parser.parse_args()

    # Tải cấu hình
    config = load_config()

    # Áp dụng tham số
    if args.top:
        config["search"]["top_limit"] = args.top

    if args.author:
        config["comment"]["custom_name"] = args.author

    if args.comment:
        config["comment"]["auto_comment"] = True
    elif args.no_comment:
        config["comment"]["auto_comment"] = False

    if args.headless:
        config["browser"]["headless"] = True
    elif args.visible:
        config["browser"]["headless"] = False

    if args.stay:
        config["behavior"]["min_stay_seconds"] = max(2, args.stay - 2)
        config["behavior"]["max_stay_seconds"] = args.stay + 2

    # Lấy danh sách từ khóa
    target_keywords = []
    if args.keyword:
        target_keywords = [args.keyword]
    elif args.file:
        target_keywords = load_keywords_from_file(args.file)
    else:
        kw_file = config.get("search", {}).get("keywords_file", "keywords.txt")
        if os.path.exists(kw_file):
            target_keywords = load_keywords_from_file(kw_file)
        if not target_keywords:
            target_keywords = config.get("search", {}).get("keywords", ["xem phim motchill vietsub"])

    # Bảng tóm tắt cấu hình
    table = Table(title="📋 Cấu Hình Bot Cào & Bình Luận Web Phim", border_style="cyan")
    table.add_column("Thuộc tính", style="bold green")
    table.add_column("Giá trị", style="white")

    table.add_row("Số từ khóa cần chạy", f"{len(target_keywords)} từ khóa")
    table.add_row("Từ khóa mẫu", ", ".join(target_keywords[:3]) + ("..." if len(target_keywords) > 3 else ""))
    table.add_row("Số lượng Top web phim", f"Top {config['search']['top_limit']}")
    table.add_row("Web phim mục tiêu", "motchill, motphim, phimmoi, rophim")
    
    # Trạng thái bình luận tự động
    cmt_status = "Đang BẬT (Tự động soạn & gửi bình luận)" if config["comment"]["auto_comment"] else "Đang TẮT"
    table.add_row("Tự động bình luận thông minh", cmt_status)
    if config["comment"]["auto_comment"]:
        author_display = config["comment"]["custom_name"] if config["comment"]["custom_name"] else "Ngẫu nhiên tên Việt Nam tự nhiên"
        table.add_row("Tên người bình luận", author_display)

    table.add_row("Chế độ hiển thị", "Chạy ngầm (Headless)" if config["browser"]["headless"] else "Mở trình duyệt (Visible)")
    table.add_row("Thời gian ở lại web", f"{config['behavior']['min_stay_seconds']}s - {config['behavior']['max_stay_seconds']}s")
    table.add_row("Cuộn trang đọc nội dung", "Bật" if config["behavior"]["scroll_page"] else "Tắt")
    table.add_row("Thư mục xuất kết quả", config["output"]["output_dir"])

    console.print(table)
    console.print()

    exporter = DataExporter(output_dir=config["output"]["output_dir"])
    bot = GoogleTopBot(config=config, exporter=exporter, console=console)

    bot.run(keywords=target_keywords)

    console.print(f"\n[bold green]🎉 Hoàn tất! Báo cáo phiên chạy đã được lưu tại thư mục:[/bold green] [bold cyan]{config['output']['output_dir']}[/bold cyan]")
    console.print(f"   • Lịch sử gửi bình luận: [cyan]{exporter.comments_csv_path}[/cyan]")
    console.print(f"   • Dữ liệu phim chi tiết: [cyan]{exporter.movies_csv_path}[/cyan]")
    console.print(f"   • Lịch sử truy cập web: [cyan]{exporter.csv_path}[/cyan]")
    console.print(f"   • Ảnh chụp màn hình: [cyan]{exporter.screenshots_dir}[/cyan]\n")

if __name__ == "__main__":
    main()
