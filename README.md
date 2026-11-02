# 🎬 Bot Cào Dữ Liệu & Tự Động Bình Luận Web Phim Top Google (Bản Pro)

Bot tự động hóa tìm kiếm, cào dữ liệu và **bình luận thông minh bằng AI** trên 4 hệ thống web phim lớn:
1. **Motchill** (`motchill.*`)
2. **Motphim** (`motphim.*`)
3. **Phimmoi** (`phimmoi.*`)
4. **Rophim** (`rophim.*`)

---

## 🌟 5 Tính Năng Nâng Cấp Vượt Trội (Bản Pro)

### 1. 🔑 Lưu Phiên Trình Duyệt (Persistent Profile / Session)
- Tự động lưu cookie, lịch sử và trạng thái đăng nhập vào thư mục `user_profile/`.
- Bạn chỉ cần đăng nhập tài khoản web phim hoặc Facebook **1 lần duy nhất**, các lần chạy sau bot sẽ tự động giữ phiên đăng nhập và bình luận được mọi khung chat.

### 2. 🧠 Bình Luận Thông Minh Bằng AI (Google Gemini AI)
- Tích hợp Gemini AI: Bot tự đọc đoạn tóm tắt nội dung phim (synopsis) và tự động tạo 1 câu nhận xét độc nhất, bàn luận đúng tình tiết/nhân vật trong phim.
- **Tự động chuyển đổi thông minh:** Nếu không điền API key, bot tự động dùng kho mẫu câu cảm nghĩ tiếng Việt tự nhiên đã được làm sạch tên phim.

### 3. 📱 Gửi Báo Cáo & Ảnh Chụp Tức Thì Về Telegram
- Tự động gửi tin nhắn báo cáo kèm ảnh chụp màn hình về điện thoại của bạn qua Telegram ngay khi cào xong hoặc bình luận thành công một bộ phim.

### 4. 🌐 Hỗ Trợ Proxy Xoay IP (Rotating Proxy)
- Hỗ trợ cấu hình Proxy HTTP/SOCKS5 trong `config.json` hoặc tham số dòng lệnh `--proxy`. Giúp bạn cào dữ liệu liên tục mà không lo bị chặn IP mạng nhà.

### 5. ⏰ Chế Độ Hẹn Giờ Chạy Lặp Tự Động (Scheduler / Loop Mode)
- Tự động chạy định kỳ (ví dụ mỗi 60 phút thức dậy 1 lần) để quét các phim mới phát hành trên Motchill/Phimmoi/Rophim, tương tác để lại bình luận rồi tự động nghỉ ngơi.

---

## 📁 Cấu Trúc Dự Án

```
auto-crawl-bot-cmt-web/
├── bot.py                # File khởi chạy chính (CLI & Bảng điều khiển Rich)
├── crawler.py            # Động cơ cào dữ liệu & điều khiển trình duyệt Playwright
├── movie_extractor.py    # Bộ lọc độc quyền 4 web phim & bóc tách dữ liệu
├── comment_generator.py  # Bộ tạo bình luận thông minh (kết hợp AI & Templates)
├── comment_poster.py     # Giả lập gõ phím người thật & gửi bình luận vào form
├── ai_commenter.py       # Module tích hợp Gemini AI phân tích tóm tắt phim
├── telegram_notifier.py  # Module gửi thông báo & ảnh chụp về Telegram
├── data_exporter.py      # Xuất dữ liệu ra CSV & JSON
├── config.json           # File cấu hình toàn diện
├── keywords.txt          # Danh sách từ khóa phim mẫu
├── run.bat               # File click đúp chuột chạy nhanh trên Windows
├── requirements.txt      # Thư viện yêu cầu
└── output/               # Thư mục lưu trữ kết quả
    ├── comments_posted.csv
    ├── movies_crawled.csv
    ├── visit_history.csv
    └── screenshots/
```

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Bấm đúp chuột chạy nhanh
Bấm đúp chuột vào file **[`run.bat`](file:///c:/auto-crawl-bot-cmt-web/run.bat)** trên máy tính.

---

### 2. Các câu lệnh chạy tùy biến

#### A. Chạy chế độ hiển thị trình duyệt (Khuyên dùng để theo dõi bot lướt web):
```powershell
python bot.py --visible
```

#### B. Chạy hẹn giờ lặp lại (Ví dụ: Cứ 60 phút chạy 1 lần):
```powershell
python bot.py -i 60 --visible
```

#### C. Chạy bình luận với Gemini AI:
```powershell
python bot.py --ai-key "AIzaSy..." --visible
```
*(Hoặc điền key trực tiếp vào mục `gemini_api_key` trong `config.json`)*

#### D. Chạy qua Proxy:
```powershell
python bot.py --proxy "http://username:password@ip:port"
```

#### E. Chạy gửi thông báo về Telegram:
```powershell
python bot.py --tg-token "BOT_TOKEN" --tg-chat "CHAT_ID"
```

#### F. Chỉ cào dữ liệu (Tắt bình luận):
```powershell
python bot.py --no-comment
```

---

## ⚙️ Cấu Hình Nâng Cao (`config.json`)

```json
{
  "comment": {
    "auto_comment": true,
    "use_ai": true,
    "gemini_api_key": "ĐIỀN_API_KEY_NẾU_MUỐN_DÙNG_AI",
    "custom_name": ""
  },
  "browser": {
    "use_persistent_profile": true,
    "profile_dir": "user_profile",
    "headless": false
  },
  "proxy": {
    "enabled": false,
    "server": "http://ip:port",
    "username": "",
    "password": ""
  },
  "telegram": {
    "enabled": false,
    "bot_token": "BOT_TOKEN_CỦA_BẠN",
    "chat_id": "CHAT_ID_CỦA_BẠN",
    "send_screenshot": true
  },
  "scheduler": {
    "loop_mode": false,
    "interval_minutes": 60
  }
}
```
