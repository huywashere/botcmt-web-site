import os
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        
        menu_text = (
            "[bold yellow]1.[/bold yellow] [bold green]Chạy ĐA LUỒNG cào & cmt[/bold green] (Hiện Chrome quan sát trực quan 3 web cùng lúc)\n"
            "[bold yellow]2.[/bold yellow] [bold cyan]Chạy NGẦM siêu nhẹ (Headless)[/bold cyan] (Chạy ngầm tốc độ cao, không mở cửa sổ)\n"
            "[bold yellow]3.[/bold yellow] [bold magenta]Chế độ ĐIỀU KHIỂN TỪ XA qua TELEGRAM[/bold magenta] (Dùng điện thoại gửi /crawl, /status...)\n"
            "[bold yellow]4.[/bold yellow] [bold blue]Mở Chrome đăng nhập tài khoản Google[/bold blue] (userwritezeus@gmail.com)\n"
            "[bold yellow]5.[/bold yellow] [bold yellow]Chạy TEST NHANH 1 phim duy nhất[/bold yellow] (Test thử nghiệm trong 1 phút)\n"
            "[bold yellow]6.[/bold yellow] [dim]Xem danh sách các phim đã bình luận[/dim]\n"
            "[bold yellow]0.[/bold yellow] [red]Thoát[/red]"
        )
        
        console.print(Panel(
            menu_text,
            title="[bold cyan]🎬 BOT CÀO PHIM & TỰ ĐỘNG BÌNH LUẬN ĐA LUỒNG (BẢN PRO)[/bold cyan]",
            subtitle="[dim]Nhập số lựa chọn rồi bấm ENTER[/dim]",
            border_style="cyan"
        ))
        
        try:
            choice = input("\n👉 Nhập lựa chọn của bạn [1, 2, 3, 4, 5, 6, 0]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát.")
            break
            
        if choice == "1":
            console.print("\n[bold green]🚀 Đang khởi động chế độ Đa Luồng trực quan (3 web song song)...[/bold green]\n")
            subprocess.run([sys.executable, "bot.py", "--visible", "-w", "3"])
            input("\n👉 Nhấn ENTER để quay lại menu chính...")
        elif choice == "2":
            console.print("\n[bold cyan]🚀 Đang khởi động chế độ Chạy Ngầm (Headless)...[/bold cyan]\n")
            subprocess.run([sys.executable, "bot.py", "--headless", "-w", "3"])
            input("\n👉 Nhấn ENTER để quay lại menu chính...")
        elif choice == "3":
            console.print("\n[bold magenta]📱 Đang khởi động Máy chủ Telegram... Mở Telegram trên điện thoại để điều khiển bot![/bold magenta]\n")
            subprocess.run([sys.executable, "bot.py", "--remote"])
            input("\n👉 Nhấn ENTER để quay lại menu chính...")
        elif choice == "4":
            console.print("\n[bold blue]🔑 Đang mở Google Chrome đăng nhập tài khoản...[/bold blue]\n")
            subprocess.run([sys.executable, "bot.py", "--setup-login", "--email", "userwritezeus@gmail.com"])
            input("\n👉 Nhấn ENTER để quay lại menu chính...")
        elif choice == "5":
            console.print("\n[bold yellow]⚡ Đang chạy thử nghiệm 1 phim nhanh nhất...[/bold yellow]\n")
            subprocess.run([sys.executable, "bot.py", "-k", "phim mai", "-t", "1", "--cmts-per-web", "1", "--visible"])
            input("\n👉 Nhấn ENTER để quay lại menu chính...")
        elif choice == "6":
            from history_manager import CommentHistoryManager
            mgr = CommentHistoryManager()
            console.print(f"\n[bold green]📊 Tổng số phim đã bình luận: {mgr.count()} phim[/bold green]")
            for idx, (url, item) in enumerate(list(mgr.history.items())[-10:], 1):
                console.print(f"  {idx}. [bold]{item.get('movie_name')}[/bold] - [dim]{url}[/dim]")
            input("\n👉 Nhấn ENTER để quay lại menu chính...")
        elif choice == "0":
            console.print("[dim]Tạm biệt![/dim]")
            break
        else:
            console.print("[red]⚠️ Lựa chọn không hợp lệ, vui lòng thử lại![/red]")
            input("\n👉 Nhấn ENTER để tiếp tục...")

if __name__ == "__main__":
    main()
