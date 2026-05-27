@echo off

echo ========================================
echo WindowStatus Build Script
echo ========================================
echo.

if exist C:\BuildEnv rmdir /s /q C:\BuildEnv
if exist C:\TempBuild rmdir /s /q C:\TempBuild

echo [1/5] Creating virtual environment...
"C:\Users\秋月\AppData\Local\Programs\Python\Python311\python.exe" -m venv C:\BuildEnv
if errorlevel 1 (
    echo Failed to create venv!
    pause
    exit /b 1
)

echo [2/5] Installing dependencies...
C:\BuildEnv\Scripts\pip.exe install PyQt5 psutil pywin32 pyinstaller -q

echo [3/5] Copying project files...
mkdir C:\TempBuild
xcopy /E /I /Q "%~dp0*.py" C:\TempBuild\ >nul
xcopy /E /I /Q "%~dp0*.ico" C:\TempBuild\ >nul

echo [4/5] Building...
cd /d C:\TempBuild

C:\BuildEnv\Scripts\pyinstaller.exe --onefile --windowed --icon icon.ico --name WindowStatus window_status.py

if exist C:\TempBuild\dist\WindowStatus.exe (
    echo [5/5] Copying exe...
    copy C:\TempBuild\dist\WindowStatus.exe "%~dp0" >nul
    echo.
    echo ========================================
    echo Build successful!
    echo File: %~dp0WindowStatus.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
)

echo Cleaning up...
cd /d "%~dp0"
rmdir /s /q C:\TempBuild >nul 2>&1
rmdir /s /q C:\BuildEnv >nul 2>&1

pause