@echo off
chcp 65001 >nul
title Unsolved Case Files AI - Autonomous Detective Playtester
color 0A

cd /d "%~dp0detective-backend"
python playtest_case.py %*

echo.
pause
