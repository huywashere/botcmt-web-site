# 🎬 Bot Cào Dữ Liệu & Tự Động Bình Luận Web Phim Top Google

Bot chuyên biệt tìm kiếm, cào dữ liệu và **tự động bình luận thông minh** trên 4 hệ thống web phim lớn:
1. **Motchill** (`motchill.*`)
2. **Motphim** (`motphim.*`)
3. **Phimmoi** (`phimmoi.*`)
4. **Rophim** (`rophim.*`)

---

## 🌟 Tính Năng Tự Động Bình Luận Thông Minh

* **Soạn bình luận ngữ cảnh tự nhiên:**
  - Tự động bóc tách tên phim gốc (lọc bỏ các từ thừa như *Full HD, Vietsub, Tập 1, Motchill, Phimmoi*...).
  - Ghép tên phim vào các mẫu câu cảm nghĩ của người xem phim chân thật (nhận xét diễn xuất, âm thanh, kịch bản, lời khen subteam...).
* **Giả lập người dùng thật gửi bình luận:**
  - Tự động tạo tên hiển thị (Nickname) ngẫu nhiên tự nhiên của người Việt (hoặc cho phép bạn tự đặt tên).
  - Tự động cuộn trang xuống phần bình luận.
  - Gõ phím từng ký tự với độ trễ ngẫu nhiên (Human Typing) để tránh bị chặn spam.
  - Tự động bấm gửi hoặc Enter.
* **Ghi nhận lịch sử bình luận:**
  - Lưu toàn bộ bình luận đã gửi vào `output/comments_posted.csv` và `output/comments_posted.json`.

---

## 🚀 Cách Sử Dụng

### 1. Bấm đúp chuột chạy nhanh
Click đúp vào file **[`run.bat`](file:///c:/auto-crawl-bot-cmt-web/run.bat)** trên máy tính.

---

### 2. Các câu lệnh chạy tùy biến

* **Chạy tự động bình luận mặc định:**
  ```powershell
  python bot.py
  ```

* **Chỉ định tên người bình luận của bạn:**
  ```powershell
  python bot.py --author "Hoàng Nam"
  ```

* **Mở trình duyệt để quan sát bot tự điền & gửi bình luận:**
  ```powershell
  python bot.py --visible
  ```

* **Tắt tính năng bình luận (chỉ cào dữ liệu):**
  ```powershell
  python bot.py --no-comment
  ```

* **Chạy với 1 từ khóa phim cụ thể:**
  ```powershell
  python bot.py -k "xem phim motchill vietsub" -t 1 --visible
  ```

---

## ⚙️ Cấu Hình (`config.json`)

Mở file [`config.json`](file:///c:/auto-crawl-bot-cmt-web/config.json) để tùy biến nội dung bình luận:

```json
{
  "comment": {
    "auto_comment": true,
    "custom_name": "",
    "custom_templates": [
      "Phim {movie_name} xem cuốn quá, diễn xuất đỉnh thực sự!",
      "Vừa xem xong {movie_name}, kịch bản bất ngờ phút cuối ghê.",
      "Bản vietsub của {movie_name} nét căng, cảm ơn web đã cập nhật nhanh nhé!"
    ]
  }
}
```

* **`auto_comment`**: `true` để bật tự động bình luận, `false` để tắt.
* **`custom_name`**: Để trống `""` bot sẽ tự xoay vòng tên ngẫu nhiên (Minh Tuấn, Hoàng Nam, Khánh Linh...), hoặc điền tên bạn muốn.
* **`custom_templates`**: Các mẫu câu bạn muốn bot sử dụng (dùng `{movie_name}` ở vị trí muốn chèn tên phim).

---

## 📁 Kết Quả Xuất Ra (`output/`)

* [`output/comments_posted.csv`](file:///c:/auto-crawl-bot-cmt-web/output/comments_posted.csv): Danh sách lịch sử các bình luận đã gửi kèm trạng thái.
* [`output/movies_crawled.csv`](file:///c:/auto-crawl-bot-cmt-web/output/movies_crawled.csv): Bảng thông tin phim đã cào (Tên, Năm, Mô tả, Ảnh bìa, Bình luận cũ).
* [`output/visit_history.csv`](file:///c:/auto-crawl-bot-cmt-web/output/visit_history.csv): Lịch sử phiên truy cập Google và thời gian ở lại trang.
* [`output/screenshots/`](file:///c:/auto-crawl-bot-cmt-web/output/screenshots/): Ảnh chụp màn hình website thực tế.
