@echo off
chcp 65001 >nul
title RoboLearn Shooter - Build EXE

echo ============================================
echo   RoboLearn Shooter - Tao file EXE
echo ============================================
echo.

:: Kiem tra PyInstaller
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller chua duoc cai dat.
    echo     Dang cai dat tu dong...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Cai dat that bai. Kiem tra ket noi mang va thu lai.
        pause
        exit /b 1
    )
)

echo [OK] PyInstaller san sang.
echo.

:: Xoa build cu neu co
if exist "dist\RoboLearnShooter" (
    echo [*] Xoa build cu...
    rmdir /s /q "dist\RoboLearnShooter"
)
if exist "build" (
    rmdir /s /q "build"
)
if exist "RoboLearnShooter.spec" (
    del "RoboLearnShooter.spec"
)

echo [*] Bat dau build EXE...
echo     (Co the mat 1-3 phut, vui long cho)
echo.

:: Build PyInstaller
python -m PyInstaller ^
    --name "RoboLearnShooter" ^
    --onedir ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --add-data "data;data" ^
    --add-data "assets;assets" ^
    --add-data "saves;saves" ^
    --add-data "src;src" ^
    --hidden-import "pygame" ^
    --hidden-import "docx" ^
    --hidden-import "python_docx" ^
    --collect-all "pygame" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build that bai!
    echo Kiem tra log o tren de xem loi.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   BUILD THANH CONG!
echo ============================================
echo.
echo   File EXE nam tai:
echo   dist\RoboLearnShooter\RoboLearnShooter.exe
echo.
echo   De chia se:
echo   Nen toan bo folder dist\RoboLearnShooter\
echo   thanh file ZIP va gui di.
echo.
echo   Nguoi nhan khong can cai Python hay pygame.
echo ============================================
echo.

set /p test="Chay thu EXE ngay bay gio? (y/n): "
if /i "%test%"=="y" (
    start "" "dist\RoboLearnShooter\RoboLearnShooter.exe"
)

pause