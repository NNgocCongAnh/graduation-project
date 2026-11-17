@echo off
chcp 65001 >nul
title Đóng gói và Khởi chạy Docker - Detective Game Backend
color 0B

echo ===========================================================================
echo       ĐÓNG GÓI VÀ KHỞI CHẠY HỆ THỐNG BẰNG DOCKER COMPOSE
echo ===========================================================================
echo.

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [LỖI] Chưa tìm thấy Docker Desktop trên máy tính.
    echo Vui lòng cài đặt và bật Docker Desktop trước khi chạy script này.
    pause
    exit /b 1
)

echo [1/2] Đang xây dựng (Build) container cho Backend và CSDL...
docker compose build backend

echo.
echo [2/2] Đang khởi chạy hệ thống (FastAPI Backend + PostgreSQL)...
docker compose up -d backend db

echo.
echo ===========================================================================
echo   Hệ thống Backend đã chạy trong Docker tại:
echo   - Swagger API Docs: http://localhost:8000/docs
echo   - Health Check:    http://localhost:8000/api/health
echo ===========================================================================
echo.
pause
