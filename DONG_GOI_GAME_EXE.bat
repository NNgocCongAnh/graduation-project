@echo off
chcp 65001 >nul
title Đóng gói Game Unity 6 URP - Standalone Windows Player
color 0B

echo ===========================================================================
echo       BẮT ĐẦU ĐÓNG GÓI GAME UNSOLVED CASE FILES AI (UNITY 6 URP)
echo ===========================================================================
echo.
echo [1/3] Kiểm tra đường dẫn cài đặt Unity 6 (6000.5.8f1)...
set "UNITY_PATH=C:\Program Files\Unity\Hub\Editor\6000.5.8f1\Editor\Unity.exe"
if not exist "%UNITY_PATH%" (
    echo [LỖI] Không tìm thấy Unity.exe tại: %UNITY_PATH%
    pause
    exit /b 1
)
echo       -> Đã tìm thấy Unity Editor tại: %UNITY_PATH%

echo.
echo [2/3] Thiết lập thư mục xuất xưởng Build...
set "PROJECT_PATH=%~dp0Unity\My project"
set "BUILD_DIR=%~dp0Build"
set "EXE_PATH=%BUILD_DIR%\UnsolvedCaseFiles.exe"
set "LOG_PATH=%~dp0unity_build.log"

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

echo.
echo [3/3] Đang biên dịch và đóng gói Standalone Player (Windows 64-bit)...
echo       Quá trình này mất khoảng 1-2 phút, vui lòng đợi...
echo.

"%UNITY_PATH%" -batchmode -quit -projectPath "%PROJECT_PATH%" -buildWindows64Player "%EXE_PATH%" -logFile "%LOG_PATH%"

if exist "%EXE_PATH%" (
    echo ===========================================================================
    echo   [THÀNH CÔNG] Game đã được đóng gói thành công tại:
    echo   %EXE_PATH%
    echo ===========================================================================
) else (
    echo ===========================================================================
    echo   [CẢNH BÁO / LỖI] Quá trình đóng gói chưa tạo được file .exe.
    echo   Vui lòng kiểm tra file nhật ký: %LOG_PATH%
    echo ===========================================================================
)

echo.
pause
