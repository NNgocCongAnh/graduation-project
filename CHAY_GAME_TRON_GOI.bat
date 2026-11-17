@echo off
chcp 65001 >nul
title Khởi chạy Trọn gói Game Unsolved Case Files AI (Backend + Unity Client)
color 0A

echo ===========================================================================
echo       KHỞI CHẠY TRỌN GÓI: DETECTIVE BACKEND + UNITY 6 CLIENT
echo ===========================================================================
echo.

set "EXE_PATH=%~dp0Build\UnsolvedCaseFiles.exe"

echo [1/3] Đang kiểm tra và khởi động Backend FastAPI (Port 8000)...
start "Detective Backend Server" cmd /k "cd /d %~dp0detective-backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/3] Đang đợi Backend sẵn sàng (khoảng 3-5 giây)...
timeout /t 4 /nobreak >nul

echo.
echo [3/3] Đang khởi chạy Game Client: %EXE_PATH%
if exist "%EXE_PATH%" (
    start "" "%EXE_PATH%"
) else (
    echo [LỖI] Chưa tìm thấy file: %EXE_PATH%
    echo Hãy chạy DONG_GOI_GAME_EXE.bat trước để xuất bản game!
)

echo.
echo ===========================================================================
echo  Hệ thống đã hoạt động:
echo  - Backend API: http://localhost:8000/docs
echo  - Cửa sổ Game Unity đã được mở.
echo  - Phím tắt trong Game:
echo      + Phím O: Mở Cài đặt Model AI (chọn Llama 3.3, GPT-4o-mini, Gemini,...)
echo      + Phím L: Mở phòng chơi LAN
echo      + Phím T: Bật Chat
echo      + Phím Esc: Đóng các bảng
echo ===========================================================================
echo.
pause
