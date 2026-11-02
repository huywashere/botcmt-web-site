import argparse
import json
import os
import sys
import time

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
        "[bold cyan]🎬 BOT TỰ ĐỘNG CÀO DỮ LIỆU & BÌNH LUẬN THÔNG MINH WEB PHIM TOP GOOGLE (PRO)[/bold cyan]\n"
        "[italic green]• Hỗ trợ 4 web phim lớn: Motchill, Motphim, Phimmoi, Rophim[/italic green]\n"
        "[italic green]• Tích hợp AI Gemini & Templates tạo bình luận phim độc nhất, tự nhiên[/italic green]\n"
        "[italic green]• Lưu phiên đăng nhập trình duyệt (Profile/Session) - Không lo bị đăng xuất[/italic green]\n"
        "[italic green]• Hỗ trợ Proxy xoay IP chống chặn & Gửi báo cáo tức thì về Telegram[/italic green]\n"
        "[italic green]• Chế độ hẹn giờ chạy lặp tự động (Scheduler / Loop Mode)[/italic green]"
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
            "use_ai": True,
            "gemini_api_key": "",
            "custom_name": "",
            "custom_templates": []
        },
        "browser": {
            "use_persistent_profile": True,
            "profile_dir": "user_profile",
            "headless": False,
            "slow_mo_ms": 30,
            "window_width": 1280,
            "window_height": 800
        },
        "proxy": {
            "enabled": False,
            "server": "",
            "username": "",
            "password": ""
        },
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": "",
            "send_screenshot": True
        },
        "scheduler": {
            "loop_mode": False,
            "interval_minutes": 60
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

def run_once(config, target_keywords):
    exporter = DataExporter(output_dir=config["output"]["output_dir"])
    bot = GoogleTopBot(config=config, exporter=exporter, console=console)
    bot.run(keywords=target_keywords)

    console.print(f"\n[bold green]🎉 Hoàn tất phiên chạy! Báo cáo đã lưu tại:[/bold green] [bold cyan]{config['output']['output_dir']}[/bold cyan]")
    console.print(f"   • Lịch sử gửi bình luận: [cyan]{exporter.comments_csv_path}[/cyan]")
    console.print(f"   • Dữ liệu phim chi tiết: [cyan]{exporter.movies_csv_path}[/cyan]")
    console.print(f"   • Lịch sử truy cập web: [cyan]{exporter.csv_path}[/cyan]")
    console.print(f"   • Ảnh chụp màn hình: [cyan]{exporter.screenshots_dir}[/cyan]\n")

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Bot cào web phim và tự động bình luận thông minh (Bản Nâng Cấp Pro)")
    parser.add_argument("-k", "--keyword", type=str, help="Từ khóa phim cần tìm kiếm")
    parser.add_argument("-f", "--file", type=str, help="File danh sách từ khóa")
    parser.add_argument("-t", "--top", type=int, help="Số lượng top web phim cần cào/bình luận")
    parser.add_argument("--author", type=str, help="Tên người bình luận")
    parser.add_argument("--cmts-per-web", type=int, help="Số lượng phim Hot muốn bình luận trên mỗi website (mặc định: 3)")
    parser.add_argument("--comment", action="store_true", help="Bật tính năng tự động bình luận")
    parser.add_argument("--no-comment", action="store_true", help="Tắt tính năng tự động bình luận")
    parser.add_argument("--headless", action="store_true", help="Chạy ngầm không hiện trình duyệt")
    parser.add_argument("--visible", action="store_true", help="Hiện cửa sổ trình duyệt theo dõi trực quan")
    parser.add_argument("--stay", type=int, help="Thời gian ở lại xem mỗi website (giây)")
    parser.add_argument("-i", "--interval", type=int, help="Chế độ lặp lại sau mỗi X phút (ví dụ: -i 60)")
    parser.add_argument("--proxy", type=str, help="Địa chỉ Proxy HTTP (ví dụ: http://127.0.0.1:8080)")
    parser.add_argument("--ai-key", type=str, help="API Key Google Gemini để bình luận AI")
    parser.add_argument("--no-ai", action="store_true", help="Tắt tính năng bình luận AI (chỉ dùng templates)")
    parser.add_argument("--tg-token", type=str, help="Bot Token Telegram để nhận thông báo")
    parser.add_argument("--tg-chat", type=str, help="Chat ID Telegram để nhận thông báo")

    args = parser.parse_args()

    # Tải cấu hình
    config = load_config()

    # Áp dụng tham số dòng lệnh
    if args.top:
        config["search"]["top_limit"] = args.top

    if args.author:
        config["comment"]["custom_name"] = args.author

    if args.cmts_per_web:
        config["comment"]["comments_per_website"] = args.cmts_per_web

    if args.comment:
        config["comment"]["auto_comment"] = True
    elif args.no_comment:
        config["comment"]["auto_comment"] = False

    if args.ai_key:
        config["comment"]["gemini_api_key"] = args.ai_key
        config["comment"]["use_ai"] = True
    if args.no_ai:
        config["comment"]["use_ai"] = False

    if args.proxy:
        config["proxy"]["enabled"] = True
        config["proxy"]["server"] = args.proxy

    if args.tg_token:
        config["telegram"]["bot_token"] = args.tg_token
        config["telegram"]["enabled"] = True
    if args.tg_chat:
        config["telegram"]["chat_id"] = args.tg_chat
        config["telegram"]["enabled"] = True

    if args.interval:
        config["scheduler"]["loop_mode"] = True
        config["scheduler"]["interval_minutes"] = args.interval

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
    table = Table(title="📋 Cấu Hình Bot Cào & Bình Luận Web Phim (Bản Pro)", border_style="cyan")
    table.add_column("Thuộc tính", style="bold green")
    table.add_column("Giá trị", style="white")

    table.add_row("Số từ khóa cần chạy", f"{len(target_keywords)} từ khóa")
    table.add_row("Từ khóa mẫu", ", ".join(target_keywords[:3]) + ("..." if len(target_keywords) > 3 else ""))
    table.add_row("Số lượng Top web phim", f"Top {config['search']['top_limit']}")
    table.add_row("Web phim mục tiêu", "motchill, motphim, phimmoi, rophim")
    
    # Persistent Session
    p_status = f"Bật (Lưu tại: {config['browser'].get('profile_dir')})" if config["browser"].get("use_persistent_profile") else "Tắt (Mở trình duyệt mới)"
    table.add_row("Lưu phiên đăng nhập (Profile)", p_status)

    # Bình luận tự động & AI
    cmt_status = "Đang BẬT" if config["comment"]["auto_comment"] else "Đang TẮT"
    table.add_row("Tự động bình luận thông minh", cmt_status)
    if config["comment"]["auto_comment"]:
        ai_status = "Bật (Ưu tiên Gemini AI khi có key)" if config["comment"].get("use_ai") else "Chỉ dùng Template thông minh"
        table.add_row("Chế độ soạn bình luận", ai_status)
        cmts_count = config["comment"].get("comments_per_website", 3)
        table.add_row("Số phim Hot cmt mỗi web", f"{cmts_count} phim Hot / 1 website")

    # Proxy
    proxy_status = f"Đang BẬT ({config['proxy'].get('server')})" if config["proxy"].get("enabled") and config["proxy"].get("server") else "Không dùng Proxy (IP trực tiếp)"
    table.add_row("Trạng thái Proxy", proxy_status)

    # Telegram
    tg_status = "Đang BẬT (Gửi tin nhắn & ảnh về Telegram)" if config["telegram"].get("enabled") and config["telegram"].get("bot_token") else "Tắt"
    table.add_row("Thông báo Telegram", tg_status)

    # Chế độ chạy lặp
    sched_status = f"BẬT (Lặp lại sau mỗi {config['scheduler'].get('interval_minutes')} phút)" if config["scheduler"].get("loop_mode") else "Chạy 1 lần duy nhất"
    table.add_row("Chế độ chạy hẹn giờ", sched_status)

    table.add_row("Chế độ hiển thị", "Chạy ngầm (Headless)" if config["browser"]["headless"] else "Mở trình duyệt (Visible)")
    table.add_row("Thời gian ở lại web", f"{config['behavior']['min_stay_seconds']}s - {config['behavior']['max_stay_seconds']}s")

    console.print(table)
    console.print()

    # Vòng lặp hẹn giờ nếu bật loop_mode
    if config["scheduler"].get("loop_mode"):
        interval_min = config["scheduler"].get("interval_minutes", 60)
        console.print(f"[bold yellow]🔄 Đã kích hoạt chế độ lặp lại sau mỗi {interval_min} phút. Nhấn Ctrl+C để dừng.[/bold yellow]\n")
        cycle = 1
        while True:
            console.print(f"[bold magenta]▶️ BẮT ĐẦU CHU KỲ #{cycle}[/bold magenta]")
            run_once(config, target_keywords)
            cycle += 1
            console.print(f"[yellow]⏳ Đang ngủ {interval_min} phút trước khi bắt đầu chu kỳ tiếp theo...[/yellow]")
            try:
                for remaining in range(interval_min * 60, 0, -10):
                    time.sleep(10)
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ Người dùng đã dừng chế độ lặp bằng Ctrl+C.[/yellow]")
                break
    else:
        run_once(config, target_keywords)

if __name__ == "__main__":
    main()
