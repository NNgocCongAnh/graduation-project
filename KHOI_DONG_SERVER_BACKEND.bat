@echo off
chcp 65001 >nul
title Khởi động Server Backend FastAPI (Port 8000)
color 0E

echo ===========================================================================
echo            KHỞI ĐỘNG HỆ THỐNG DETECTIVE BACKEND (FASTAPI)
echo ===========================================================================
echo.
cd /d "%~dp0detective-backend"

echo Đang khởi chạy máy chủ FastAPI tại http://localhost:8000 ...
echo Nhấn Ctrl+C để dừng server khi không dùng nữa.
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo.
pause
