@echo off
chcp 65001 >nul
title Bot Cào Phim & Bình Luận Đa Luồng (Bản Pro)

if not "%~1"=="" (
    python bot.py %*
    goto end
)

:menu
cls
echo ========================================================================
echo       🎬 BOT CÀO PHIM & TỰ ĐỘNG BÌNH LUẬN ĐA LUỒNG (BẢN PRO)
echo ========================================================================
echo.
echo   [1] Chạy ĐA LUỒNG cào & cmt (Hiện cửa sổ Chrome quan sát trực quan)
echo   [2] Chạy NGẦM siêu nhẹ (Headless - 3 luồng song song tốc độ cao)
echo   [3] Chạy chế độ ĐIỀU KHIỂN TỪ XA QUA TELEGRAM bằng điện thoại
echo   [4] Mở Chrome đăng nhập tài khoản Google (userwritezeus@gmail.com)
echo   [5] Chạy test nhanh 1 phim duy nhất (1-2 phút)
echo   [0] Thoát
echo.
echo ========================================================================
set /p choice="👉 Nhập lựa chọn của bạn [1, 2, 3, 4, 5, 0]: "

if "%choice%"=="1" (
    echo.
    echo 🚀 Đang khởi động Bot chế độ Đa Luồng trực quan...
    python bot.py --visible -w 3
    goto end
)
if "%choice%"=="2" (
    echo.
    echo 🚀 Đang khởi động Bot chạy ngầm...
    python bot.py --headless -w 3
    goto end
)
if "%choice%"=="3" (
    echo.
    echo 📱 Đang khởi động Máy chủ điều khiển Telegram...
    echo (Mở Telegram trên điện thoại và gửi lệnh /crawl, /status...)
    python bot.py --remote
    goto end
)
if "%choice%"=="4" (
    echo.
    echo 🔑 Đang mở Google Chrome đăng nhập tài khoản...
    python bot.py --setup-login --email "userwritezeus@gmail.com"
    goto end
)
if "%choice%"=="5" (
    echo.
    echo ⚡ Đang chạy thử nghiệm 1 phim nhanh nhất...
    python bot.py -k "phim mai" -t 1 --cmts-per-web 1 --visible
    goto end
)
if "%choice%"=="0" (
    exit /b 0
)

echo.
echo ⚠️ Lựa chọn không hợp lệ, vui lòng thử lại!
timeout /t 2 >nul
goto menu

:end
echo.
echo ========================================================================
echo   Phiên làm việc đã kết thúc.
echo ========================================================================
pause
