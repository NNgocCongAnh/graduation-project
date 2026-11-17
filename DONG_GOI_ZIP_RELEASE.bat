@echo off
chcp 65001 >nul
echo ========================================================
echo   DONG GOI GAME UNSOLVED CASE FILES (PHUC VU GITHUB RELEASE)
echo ========================================================
echo.

set BUILD_DIR=%~dp0Build
set ZIP_FILE=%~dp0UnsolvedCaseFiles_v1.0.0.zip

if not exist "%BUILD_DIR%\UnsolvedCaseFiles.exe" (
    echo [LOI] Khong tim thay file %BUILD_DIR%\UnsolvedCaseFiles.exe!
    echo Vui long chay build game trong Unity truoc khi dong goi.
    pause
    exit /b 1
)

echo Dang nen toan bo thu muc Build (bao gom .exe, UnityPlayer.dll, cac file du lieu)...
powershell -Command "Compress-Archive -Path '%BUILD_DIR%\*' -DestinationPath '%ZIP_FILE%' -Force"

if exist "%ZIP_FILE%" (
    echo.
    echo ========================================================
    echo   DONG GOI THANH CONG!
    echo   File nen Release: %ZIP_FILE%
    echo ========================================================
    echo.
    echo Huong dan dua len GitHub Release:
    echo 1. Vao GitHub Repo -> Nhan vao muc 'Releases' (ben phai).
    echo 2. Nhan 'Draft a new release' (Tao phien ban moi).
    echo 3. Nhap tag 'v1.0.0' va tieu de phien ban.
    echo 4. Keo tha file UnsolvedCaseFiles_v1.0.0.zip vao o 'Attach binaries'.
    echo 5. Nhan 'Publish release'. Nguoi choi chi can tai file zip nay ve la choi duoc ngay!
) else (
    echo [LOI] Co loi xay ra trong qua trinh nen file zip.
)

echo.
pause
