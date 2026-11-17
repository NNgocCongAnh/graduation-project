@echo off
chcp 65001 >nul
title Unsolved Case Files AI - Pipeline Demo (Hai Phong)
color 0B

cd /d "%~dp0detective-backend"
python demo_haiphong_case.py

echo.
pause
