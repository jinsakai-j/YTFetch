@echo off
chcp 65001 >nul 2>&1
title YTFetch Installer
color 0F
cls

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                                                      ║
echo  ║           ⚡  YTFetch v1.0 — Installer               ║
echo  ║     YouTube Media Downloader ^& Trimmer               ║
echo  ║                                                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: ─────────────────────────────────────────────
:: STEP 1: Cek Python
:: ─────────────────────────────────────────────
echo  [1/5] Mengecek instalasi Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ╔══════════════════════════════════════════════════════╗
    echo  ║  ❌ Python TIDAK ditemukan di sistem Anda!           ║
    echo  ║                                                      ║
    echo  ║  Silakan download dan install Python terlebih dahulu:║
    echo  ║  https://www.python.org/downloads/                   ║
    echo  ║                                                      ║
    echo  ║  PENTING: Saat install, CENTANG opsi:                ║
    echo  ║  [✓] Add Python to PATH                              ║
    echo  ║                                                      ║
    echo  ║  Setelah install Python, jalankan installer ini lagi. ║
    echo  ╚══════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo         ✅ %PYVER% ditemukan.
echo.

:: ─────────────────────────────────────────────
:: STEP 2: Cek & Upgrade pip
:: ─────────────────────────────────────────────
echo  [2/5] Mengecek pip...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo         ⏳ pip belum ada, menginstall pip...
    python -m ensurepip --upgrade >nul 2>&1
    python -m pip --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo         ❌ Gagal menginstall pip!
        echo         Silakan install pip secara manual.
        pause
        exit /b 1
    )
)
echo         ✅ pip tersedia.
echo         ⏳ Mengupgrade pip ke versi terbaru...
python -m pip install --upgrade pip >nul 2>&1
echo         ✅ pip sudah versi terbaru.
echo.

:: ─────────────────────────────────────────────
:: STEP 3: Cek Dependencies
:: ─────────────────────────────────────────────
echo  [3/5] Mengecek library yang dibutuhkan...
echo.

set "NEED_INSTALL=0"

call :check_pkg customtkinter "CustomTkinter (GUI Framework)"
call :check_pkg yt_dlp "yt-dlp (YouTube Downloader Engine)"
call :check_pkg PIL "Pillow (Image Processing)"
call :check_pkg requests "requests (HTTP Client)"
call :check_pkg imageio_ffmpeg "imageio-ffmpeg (FFmpeg Binary)"
call :check_pkg win32com "pywin32 (Windows API)"
call :check_pkg sounddevice "sounddevice (Audio Recording)"
call :check_pkg numpy "NumPy (Numerical Processing)"

echo.

:: ─────────────────────────────────────────────
:: STEP 4: Install Dependencies (jika ada yang kurang)
:: ─────────────────────────────────────────────
if %NEED_INSTALL% EQU 0 (
    echo  [4/5] Semua library sudah terinstall, skip instalasi.
    echo.
    goto :step5
)

echo  [4/5] Menginstall library yang belum ada...
echo         Ini mungkin memakan waktu beberapa menit.
echo.

pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo         ⚠️  Ada masalah saat install, mencoba ulang satu per satu...
    echo.
    pip install customtkinter >nul 2>&1
    pip install yt-dlp >nul 2>&1
    pip install Pillow >nul 2>&1
    pip install requests >nul 2>&1
    pip install imageio-ffmpeg >nul 2>&1
    pip install pywin32 >nul 2>&1
    pip install sounddevice >nul 2>&1
    pip install numpy >nul 2>&1
)

echo.
echo         Memverifikasi hasil instalasi...
echo.

set "FAIL=0"
call :verify_pkg customtkinter "CustomTkinter (GUI Framework)"
call :verify_pkg yt_dlp "yt-dlp (YouTube Downloader Engine)"
call :verify_pkg PIL "Pillow (Image Processing)"
call :verify_pkg requests "requests (HTTP Client)"
call :verify_pkg imageio_ffmpeg "imageio-ffmpeg (FFmpeg Binary)"
call :verify_pkg win32com "pywin32 (Windows API)"
call :verify_pkg sounddevice "sounddevice (Audio Recording)"
call :verify_pkg numpy "NumPy (Numerical Processing)"

echo.

if %FAIL% NEQ 0 (
    echo         ⚠️  Beberapa library gagal diinstall.
    echo         Coba jalankan manual: pip install -r requirements.txt
    echo.
) else (
    echo         ✅ Semua library berhasil diinstall!
    echo.
)

:: ─────────────────────────────────────────────
:: STEP 5: Buat Desktop Shortcut
:: ─────────────────────────────────────────────
:step5
echo  [5/5] Membuat shortcut YTFetch di Desktop...
python create_shortcut.py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo         ✅ Shortcut YTFetch berhasil dibuat di Desktop!
) else (
    echo         ⚠️  Gagal membuat shortcut. Anda bisa menjalankan YTFetch
    echo             secara manual dengan: python YTFetch.py
)
echo.

:: ─────────────────────────────────────────────
:: SELESAI
:: ─────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                                                      ║
echo  ║        ✅  Instalasi YTFetch Selesai!                 ║
echo  ║                                                      ║
echo  ║  Cara membuka YTFetch:                                ║
echo  ║   • Klik ikon "YTFetch" di Desktop                    ║
echo  ║   • Atau klik dua kali "Run_YTFetch.bat"              ║
echo  ║   • Atau ketik: python YTFetch.py                     ║
echo  ║                                                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
pause
exit /b 0

:: ─────────────────────────────────────────────
:: FUNCTION: check_pkg <import_name> <display_name>
:: Cek apakah library sudah terinstall (tanpa install)
:: ─────────────────────────────────────────────
:check_pkg
set "PKG_IMPORT=%~1"
set "PKG_NAME=%~2"

python -c "import %PKG_IMPORT%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo         ✅ %PKG_NAME% — sudah terinstall
) else (
    echo         ⬜ %PKG_NAME% — belum ada, perlu diinstall
    set "NEED_INSTALL=1"
)
exit /b 0

:: ─────────────────────────────────────────────
:: FUNCTION: verify_pkg <import_name> <display_name>
:: Verifikasi library setelah install
:: ─────────────────────────────────────────────
:verify_pkg
set "PKG_IMPORT=%~1"
set "PKG_NAME=%~2"

python -c "import %PKG_IMPORT%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo         ✅ %PKG_NAME% — OK
) else (
    echo         ❌ %PKG_NAME% — gagal diinstall!
    set "FAIL=1"
)
exit /b 0
