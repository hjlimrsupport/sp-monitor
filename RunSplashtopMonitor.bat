@echo off
setlocal
cd /d %~dp0

title Splashtop JP Monitor

echo ================================================
echo    Splashtop JP Monitor (Windows)
echo ================================================
echo.

:: 1. Python Check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo [!] https://www.python.org 에서 설치 후 다시 실행해 주세요.
    pause
    exit /b
)

:: 2. Requirements Check
echo [*] 필수 라이브러리 상태를 확인하고 설치합니다...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [!] 라이브러리 설치 중 오류가 발생했습니다. 인터넷 연결을 확인해 주세요.
    pause
    exit /b
)

:: 3. Run Server
echo [*] 모니터링 센터를 가동합니다...
echo [*] 잠시 후 브라우저가 자동으로 열립니다.
python monitor_server.py

pause
