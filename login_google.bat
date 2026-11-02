@echo off
chcp 65001 >nul
cd /d "%~dp0"
python bot.py --setup-login --email "userwritezeus@gmail.com"
pause
