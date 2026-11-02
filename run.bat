@echo off
chcp 65001 >nul
cd /d "%~dp0"
python launcher.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Co loi xay ra. Nhan phim bat ky de thoat...
    pause >nul
)
