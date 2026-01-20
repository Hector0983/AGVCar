@echo off
setlocal

REM Build Windows EXE for btc_trading_strategy.py using PyInstaller

where python >nul 2>nul
if errorlevel 1 (
  echo Python not found. Please install Python 3.8+ and ensure it is in PATH.
  exit /b 1
)

REM Install PyInstaller if missing
python -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
  echo Installing PyInstaller...
  python -m pip install pyinstaller --quiet --disable-pip-version-check
)

REM Build single-file executable
pyinstaller --onefile --name BTCStrategy btc_trading_strategy.py

if errorlevel 1 (
  echo Build failed. Check the logs above.
  exit /b 1
)

echo.
echo Build succeeded. EXE location: dist\BTCStrategy.exe
echo.
pause
endlocal
