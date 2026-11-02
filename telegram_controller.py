import os
import threading
import time
import requests

class TelegramController:
    """
    Điều khiển bot cào & bình luận 2 chiều qua Telegram (2-Way Remote Controller).
    Cho phép người dùng gửi lệnh từ điện thoại để kích hoạt cào, thêm từ khóa, xem trạng thái.
    """

    def __init__(self, bot_token: str, chat_id: str, run_callback, config: dict, console=None):
        self.bot_token = bot_token.strip()
        self.chat_id = str(chat_id).strip()
        self.run_callback = run_callback
        self.config = config
        self.console = console
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self.is_active = False
        self.is_crawling = False
        self.last_update_id = 0
        self.thread = None

    def log(self, msg: str, style: str = ""):
        if self.console:
            if style:
                self.console.print(f"[{style}]{msg}[/{style}]")
            else:
                self.console.print(msg)
        else:
            print(msg)

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Gửi tin nhắn phản hồi về Telegram."""
        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code != 200:
                payload.pop("parse_mode", None)
                resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def start_polling(self):
        """Khởi động luồng lắng nghe tin nhắn điều khiển từ Telegram."""
        if not self.bot_token or not self.chat_id:
            return

        self.is_active = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        self.log("🤖 [bold green]Đã kích hoạt bộ điều khiển từ xa qua Telegram![/bold green] (Gửi /help trên Telegram để xem lệnh)", "cyan")

    def stop_polling(self):
        """Dừng lắng nghe."""
        self.is_active = False

    def _poll_loop(self):
        """Vòng lặp lấy tin nhắn mới (Long-polling)."""
        while self.is_active:
            try:
                url = f"{self.api_base}/getUpdates"
                params = {
                    "offset": self.last_update_id + 1,
                    "timeout": 15
                }
                resp = requests.get(url, params=params, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    updates = data.get("result", [])
                    for update in updates:
                        self.last_update_id = update["update_id"]
                        self._handle_update(update)
            except Exception:
                time.sleep(3)
            time.sleep(1)

    def _handle_update(self, update: dict):
        """Xử lý từng tin nhắn lệnh từ người dùng."""
        message = update.get("message")
        if not message:
            return

        sender_chat_id = str(message.get("chat", {}).get("id", ""))
        # Bảo mật: Chỉ nhận lệnh từ đúng chat_id được cấu hình
        if sender_chat_id != self.chat_id:
            return

        text = message.get("text", "").strip()
        if not text:
            return

        self.log(f"📱 Nhận lệnh từ Telegram: [bold yellow]{text}[/bold yellow]", "cyan")
        cmd_parts = text.split(maxsplit=1)
        command = cmd_parts[0].lower()
        args = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

        if command in ["/start", "/help", "help"]:
            self._cmd_help()
        elif command in ["/crawl", "/run", "run"]:
            self._cmd_crawl()
        elif command in ["/status", "status"]:
            self._cmd_status()
        elif command in ["/add", "/add_kw"]:
            self._cmd_add_keyword(args)
        elif command in ["/keywords", "/kw"]:
            self._cmd_list_keywords()
        elif command in ["/history"]:
            self._cmd_history()
        elif command in ["/stop"]:
            self._cmd_stop()
        else:
            self.send_message(f"❓ Không nhận diện được lệnh: `{text}`. Gửi `/help` để xem các lệnh có sẵn.")

    def _cmd_help(self):
        msg = (
            "🎬 *BỘ ĐIỀU KHIỂN TỪ XA BOT CÀO PHIM & BÌNH LUẬN (PRO)*\n\n"
            "Các lệnh bạn có thể gửi cho bot:\n"
            "▶️ `/crawl` hoặc `/run` : Bắt đầu cào & bình luận phim ngay lập tức\n"
            "📊 `/status` : Xem thống kê số phim đã cmt & trạng thái bot\n"
            "➕ `/add <từ khóa>` : Thêm từ khóa phim mới vào danh sách\n"
            "📝 `/keywords` : Xem danh sách từ khóa hiện có\n"
            "📜 `/history` : Xem 5 phim vừa cmt gần nhất\n"
            "🛑 `/stop` : Tạm dừng phiên chạy hiện tại"
        )
        self.send_message(msg)

    def _cmd_crawl(self):
        if self.is_crawling:
            self.send_message("⚠️ Bot đang trong quá trình cào & bình luận, xin chờ phiên hiện tại hoàn thành!")
            return

        self.send_message("🚀 *ĐÃ NHẬN LỆNH!* Đang khởi động trình duyệt cào & bình luận trên máy tính...")

        def worker():
            self.is_crawling = True
            try:
                self.run_callback()
                self.send_message("🎉 *HOÀN TẤT PHIÊN CHẠY!* Dữ liệu và lịch sử bình luận đã được cập nhật thành công.")
            except Exception as e:
                self.send_message(f"❌ Có lỗi trong quá trình chạy: {str(e)[:150]}")
            finally:
                self.is_crawling = False

        threading.Thread(target=worker, daemon=True).start()

    def _cmd_status(self):
        from history_manager import CommentHistoryManager
        dedup_file = self.config.get("deduplication", {}).get("history_file", "output/commented_history.json")
        mgr = CommentHistoryManager(history_file=dedup_file)
        
        status_text = "🔄 Đang chạy cào & bình luận..." if self.is_crawling else "🟢 Đang rảnh (Sẵn sàng nhận lệnh)"
        msg = (
            "📊 *BÁO CÁO TRẠNG THÁI BOT*\n\n"
            f"• Trạng thái: {status_text}\n"
            f"• Số phim đã bình luận: *{mgr.count()} phim*\n"
            f"• Số phim Hot / 1 web: *{self.config.get('comment', {}).get('comments_per_website', 3)} phim*\n"
            f"• Chế độ AI: {'Bật (Gemini)' if self.config.get('comment', {}).get('use_ai') else 'Templates'}\n"
            f"• Chặn quảng cáo: {'Bật' if self.config.get('ad_blocker', {}).get('enabled') else 'Tắt'}\n"
            f"• Vote 5 sao: {'Bật' if self.config.get('interaction', {}).get('auto_vote_5_stars') else 'Tắt'}"
        )
        self.send_message(msg)

    def _cmd_add_keyword(self, keyword: str):
        if not keyword:
            self.send_message("⚠️ Vui lòng nhập từ khóa! Ví dụ: `/add xem phim motchill vietsub`")
            return

        kw_file = self.config.get("search", {}).get("keywords_file", "keywords.txt")
        try:
            with open(kw_file, "a", encoding="utf-8") as f:
                f.write(f"\n{keyword.strip()}")
            self.send_message(f"✅ Đã thêm từ khóa mới: *\"{keyword.strip()}\"* vào file `{kw_file}`!")
        except Exception as e:
            self.send_message(f"❌ Không thể ghi file từ khóa: {e}")

    def _cmd_list_keywords(self):
        kw_file = self.config.get("search", {}).get("keywords_file", "keywords.txt")
        kws = []
        if os.path.exists(kw_file):
            with open(kw_file, "r", encoding="utf-8") as f:
                kws = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

        if not kws:
            kws = self.config.get("search", {}).get("keywords", [])

        kw_str = "\n".join([f"{i}. {k}" for i, k in enumerate(kws[:10], 1)])
        self.send_message(f"📝 *DANH SÁCH TỪ KHÓA ĐANG CÀO:*\n\n{kw_str}\n\n_(Hiển thị tối đa 10 từ khóa đầu)_")

    def _cmd_history(self):
        from history_manager import CommentHistoryManager
        dedup_file = self.config.get("deduplication", {}).get("history_file", "output/commented_history.json")
        mgr = CommentHistoryManager(history_file=dedup_file)
        history_items = list(mgr.history.values())[-5:]

        if not history_items:
            self.send_message("📜 Chưa có lịch sử phim nào được bình luận.")
            return

        lines = ["📜 *5 BỘ PHIM GẦN NHẤT ĐÃ BÌNH LUẬN:*\n"]
        for idx, item in enumerate(reversed(history_items), 1):
            lines.append(
                f"{idx}. *{item.get('movie_name', 'Phim')}*\n"
                f"   🔗 [Link phim]({item.get('url', '')})\n"
                f"   👤 Người gửi: {item.get('author', '')}\n"
                f"   💬 \"{item.get('comment_text', '')}\"\n"
                f"   ⏱️ {item.get('timestamp', '')}\n"
            )

        self.send_message("\n".join(lines))

    def _cmd_stop(self):
        if not self.is_crawling:
            self.send_message("ℹ️ Hiện tại không có tiến trình cào nào đang chạy.")
        else:
            self.send_message("🛑 Đã gửi tín hiệu dừng tới bot.")

