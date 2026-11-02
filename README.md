# 🎬 Bot Cào Dữ Liệu & Tự Động Bình Luận Web Phim Top Google (Bản Pro)

Bot tự động hóa tìm kiếm, cào dữ liệu và **bình luận thông minh bằng AI** trên 4 hệ thống web phim lớn:
1. **Motchill** (`motchill.*`)
2. **Motphim** (`motphim.*`)
3. **Phimmoi** (`phimmoi.*`)
4. **Rophim** (`rophim.*`)

---

## 🌟 Các Tính Năng Nâng Cấp Vượt Trội (Bản Pro)

### 1. 🔑 Đăng Nhập Tài Khoản Google / Web Phim (Persistent Profile)
- **Chế độ đăng nhập an toàn (`--setup-login`):** Chạy lệnh `python bot.py --setup-login` để mở trình duyệt, đăng nhập tài khoản Google / Gmail hoặc tài khoản các web phim yêu thích của bạn 1 lần duy nhất bằng tay (tránh hoàn toàn cơ chế chống bot của Google).
- Toàn bộ session, cookies và token được lưu vĩnh viễn vào thư mục `user_profile/`.
- Từ các lần chạy sau, bot mở profile này là đã tự động đăng nhập sẵn, không bao giờ bị hỏi đăng nhập lại!

### 2. 📝 Tự Động Điền Họ Tên & Gmail Khi Bình Luận
- Hỗ trợ điền Tên và Gmail cố định của bạn qua lệnh `--author "Tên Của Bạn" --email "your_email@gmail.com"` hoặc thiết lập trong `config.json`.
- Nếu để trống, bot tự động sinh ngẫu nhiên họ tên người Việt tự nhiên và tự tạo Gmail tương ứng khớp với họ tên (ví dụ: `Huy Hoàng` -> `huyhoang.92@gmail.com`).
- Bot tự động quét và điền chính xác vào các ô `Tên` / `Họ tên` / `Name` và `Email` / `Gmail` trên web phim.

### 3. 📱 Gửi Báo Cáo, Link Phim Trực Tiếp & Ảnh Chụp Về Telegram
- Ngay sau khi gửi bình luận thành công trên phim nào, bot lập tức:
  - Chụp màn hình khoảnh khắc bình luận vừa đăng / form báo thành công.
  - Gửi ảnh về Telegram kèm **Link phim trực tiếp (`🔗 Link phim`)**, tên phim, nội dung comment và tên người gửi.
  - Bạn chỉ cần bấm vào link trên Telegram để mở ngay trang phim và kiểm tra bình luận của mình!

### 4. 🛡️ Chặn Quảng Cáo Toàn Diện & Anti-Adblock Deception (AdBlocker Pro Engine)
- **Chặn từ tầng mạng (Route Interception):** Ngăn chặn hơn 60+ mạng quảng cáo độc hại, cá cược, nổ hũ (W88, Kubet, 789Bet, PopAds, HilltopAds, RichPush...) tải về trình duyệt ngay từ request mạng -> Tăng tốc tải trang 50-70% và tiết kiệm tối đa RAM/CPU.
- **Vô hiệu hóa bẫy cướp chuột & nhảy tab (window.open interceptor):** Chặn đứng các hành vi popunder / click-under khi click bất kỳ đâu trên màn hình.
- **Tiêm CSS & Diệt Overlay:** Tự động ẩn và xóa sổ mọi floating banner, sticky bottom, iframe qc, và overlay z-index cao che nút bình luận.
- **Đánh lừa script chống AdBlock (Anti-Adblock bypass):** Giả lập `canRunAds = true`, `fuckAdBlock` để các web phim không hiện thông báo bắt tắt chặn quảng cáo.
- **Safe Force-Click:** Đảm bảo mọi cú click vào ô nhập liệu hoặc nút gửi luôn xuyên qua các lớp bọc vô hình.

### 5. ⭐ Tự Động Đánh Giá 5 Sao & Giải Math Captcha
- **Vote 5 Sao:** Trước khi gửi bình luận, bot tự động tìm nút đánh giá 5 sao (⭐⭐⭐⭐⭐) trên trang phim để vote -> hành vi giống khán giả thật 100%.
- **Giải Math Captcha:** Tự động phát hiện các câu hỏi bảo vệ dạng toán học (ví dụ: `5 + 3 = ?`), tính toán kết quả và điền tự động vào ô xác nhận.

### 6. 🔄 Bộ Nhớ Chống Bình Luận Trùng Phim (Deduplication Memory)
- Tự động ghi nhớ toàn bộ link các phim đã bình luận vào file `output/commented_history.json`.
- Khi bot chạy lặp lại định kỳ, bot sẽ **tự động bỏ qua các phim đã bình luận** và tìm phim mới tiếp theo, tránh tuyệt đối việc bình luận 2 lần trên cùng 1 bộ phim.

### 7. 🔥 Dò Tìm Phim Tương Tác Cao (High-Engagement Hunter)
- **Thuật toán quét tương tác thông minh:** Khi mở một trang web phim, bot không chọn phim ngẫu nhiên mà tự động phân tích và tính toán **Điểm Tương Tác (Engagement Score)**:
  - 🥇 **Hero Slider / Banner đầu trang:** Ưu tiên các phim được web ghim ở vị trí nổi bật nhất.
  - 🥈 **Bảng Xếp Hạng (BXH) & Top Xem Nhiều:** Ưu tiên các phim nằm trong mục *Top Ngày, Top Tuần, Top Tháng, Phim Thịnh Hành*.
  - 🥉 **Chỉ số Lượt xem & Bình luận:** Tự động bóc tách số lượt xem (*150K views, 50 bình luận, điểm IMDb*) để xếp hạng các phim được quan tâm nhất lên đầu.
- Giúp bình luận của bạn luôn nằm ở các phim "nóng" nhất, tiếp cận lượng người xem tối đa!

### 8. 🤖 Điều Khiển Từ Xa 2 Chiều Qua Telegram (2-Way Remote Controller)
- **Cầm điện thoại điều khiển máy tính:** Chỉ cần mở Telegram trên điện thoại, bạn có thể nhắn tin ra lệnh cho bot:
  - `/crawl` hoặc `/run` : Bắt đầu chu trình cào và bình luận ngay lập tức.
  - `/status` : Xem thống kê số phim đã cmt, trạng thái bot.
  - `/add <tên phim>` : Thêm nhanh từ khóa phim mới vào danh sách cào.
  - `/keywords` : Xem danh sách từ khóa hiện tại.
  - `/history` : Xem 5 phim vừa bình luận gần nhất kèm link trực tiếp.
  - `/stop` : Tạm dừng bot.
- Kích hoạt chế độ máy chủ chờ lệnh: `python bot.py --remote`

### 8. ▶️ Giả Lập Xem Phim Thật (Fake Watch Video 5–8s)
- Tự động tìm và bấm nút **"Xem Phim"** hoặc kích hoạt trình phát `<video>` chạy ngẫu nhiên từ 5 – 8 giây trước khi cuộn xuống viết bình luận.
- Vượt qua các cơ chế kiểm tra ngầm của web phim (kiểm tra xem người dùng có thực sự xem video hay chỉ là bot vào cào dữ liệu).

### 9. 💬 Chế Độ Thảo Luận & Trả Lời Bình Luận (Reply To Comments)
- Khi phim đã có bình luận của người khác, bot có tỷ lệ tự động bấm **"Trả lời" (Reply)** bình luận của bạn đó và thảo luận cùng họ *(kết hợp AI Gemini phân tích bình luận cũ để trả lời tự nhiên nhất)*.
- Tạo cảm giác thảo luận sôi nổi, tăng độ tin cậy và không bao giờ bị coi là tài khoản spam rác.

### 10. 🧠 Bình Luận Thông Minh Bằng AI & Bình Luận Hàng Loạt Phim HOT
- **Bình luận nhiều phim HOT trên mỗi website:** Khi mở một trang web phim (*Motchill, Motphim, Phimmoi, Rophim*), bot tự động quét và cào lần lượt **Top 3 (hoặc 5) phim HOT nhất** trên trang chủ của web đó, vào chi tiết từng phim và để lại bình luận.
- **Tự động đổi danh tính (Anti-Spam):** Mỗi phim được bình luận bằng một Nickname khác nhau và một nội dung nhận xét độc nhất (hoặc sinh bởi Gemini AI theo đúng tóm tắt phim).
- **Tự động chuyển đổi thông minh:** Nếu không điền API key, bot tự động dùng kho mẫu câu cảm nghĩ tiếng Việt tự nhiên đã được làm sạch tên phim.

### 11. 🌐 Hỗ Trợ Proxy Xoay IP (Rotating Proxy)
- Hỗ trợ cấu hình Proxy HTTP/SOCKS5 trong `config.json` hoặc tham số dòng lệnh `--proxy`. Giúp bạn cào dữ liệu liên tục mà không lo bị chặn IP mạng nhà.

### 12. ⏰ Chế Độ Hẹn Giờ Chạy Lặp Tự Động (Scheduler / Loop Mode)
- Tự động chạy định kỳ (ví dụ mỗi 60 phút thức dậy 1 lần) để quét các phim mới phát hành trên Motchill/Phimmoi/Rophim, tương tác để lại bình luận rồi tự động nghỉ ngơi.

---

## 📁 Cấu Trúc Dự Án

```
auto-crawl-bot-cmt-web/
├── bot.py                  # File khởi chạy chính (CLI & Bảng điều khiển Rich)
├── crawler.py              # Động cơ cào dữ liệu & điều khiển trình duyệt Playwright
├── telegram_controller.py  # Máy chủ điều khiển từ xa 2 chiều qua Telegram
├── history_manager.py      # Bộ nhớ quản lý phim đã cmt (chống trùng lặp)
├── movie_extractor.py      # Bộ lọc độc quyền 4 web phim & bóc tách dữ liệu
├── comment_generator.py    # Bộ tạo bình luận thông minh (kết hợp AI & Templates)
├── comment_poster.py       # Giả lập gõ phím người thật, Vote 5 sao & giải Captcha
├── ai_commenter.py         # Module tích hợp Gemini AI phân tích tóm tắt phim
├── telegram_notifier.py    # Module gửi thông báo & ảnh chụp về Telegram
├── data_exporter.py        # Xuất dữ liệu ra CSV & JSON
├── config.json             # File cấu hình toàn diện
├── keywords.txt            # Danh sách từ khóa phim mẫu
├── run.bat                 # File click đúp chuột chạy nhanh trên Windows
├── requirements.txt        # Thư viện yêu cầu
└── output/                 # Thư mục lưu trữ kết quả
    ├── commented_history.json
    ├── comments_posted.csv
    ├── movies_crawled.csv
    ├── visit_history.csv
    └── screenshots/
```

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Thiết lập đăng nhập tài khoản lần đầu (Tùy chọn)
Nếu bạn muốn đăng nhập Google/Gmail hoặc tài khoản web phim để lưu cookie:
```powershell
python bot.py --setup-login
```
*(Trình duyệt sẽ mở ra -> Bạn đăng nhập tài khoản -> Quay lại cửa sổ gõ ENTER để lưu lại vĩnh viễn).*

---

### 2. Chạy cơ bản với trình duyệt hiển thị
```powershell
python bot.py --visible
```

---

### 3. Đặt Tên & Gmail cố định khi bình luận
```powershell
python bot.py --author "Huy Hoàng" --email "huyhoang@gmail.com" --visible
```

---

### 4. Bình luận nhiều phim HOT trên mỗi web (Ví dụ: 3 phim / 1 web):
```powershell
python bot.py --cmts-per-web 3 --visible
```

---

### 5. Gửi báo cáo & link kiểm tra về Telegram:
```powershell
python bot.py --tg-token "BOT_TOKEN" --tg-chat "CHAT_ID"
```

---

### 6. Chạy hẹn giờ lặp lại (Ví dụ: Cứ 60 phút chạy 1 lần):
```powershell
python bot.py -i 60 --visible
```

---

### 7. Chạy bình luận với Gemini AI:
```powershell
python bot.py --ai-key "AIzaSy..." --visible
```
*(Hoặc điền key trực tiếp vào mục `gemini_api_key` trong `config.json`)*

---

### 8. Chạy qua Proxy:
```powershell
python bot.py --proxy "http://username:password@ip:port"
```

---

### 9. Chỉ cào dữ liệu (Tắt bình luận):
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
