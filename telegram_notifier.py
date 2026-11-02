import os
import requests

class TelegramNotifier:
    """Gửi thông báo & ảnh chụp màn hình về Telegram qua Bot Token và Chat ID."""

    def __init__(self, bot_token: str = "", chat_id: str = "", enabled: bool = False):
        self.bot_token = bot_token.strip()
        self.chat_id = str(chat_id).strip()
        self.enabled = enabled and bool(self.bot_token and self.chat_id)
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text: str) -> bool:
        if not self.enabled:
            return False

        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        if not self.enabled or not photo_path or not os.path.exists(photo_path):
            return False

        try:
            url = f"{self.api_base}/sendPhoto"
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {
                    "chat_id": self.chat_id,
                    "caption": caption[:1024],
                    "parse_mode": "Markdown"
                }
                resp = requests.post(url, data=data, files=files, timeout=20)
                return resp.status_code == 200
        except Exception:
            # Fallback nếu gửi ảnh lỗi: gửi tin nhắn text
            return self.send_message(caption)

