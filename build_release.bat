@echo off
REM SoundVault Release Builder
REM Builds the app .exe and the setup installer .exe

echo ========================================
echo  SoundVault Release Builder
echo ========================================
echo.

REM Step 1: Clean previous builds
echo [1/4] Cleaning previous builds...
if exist dist rmdir /S /Q dist
if exist build rmdir /S /Q build
if exist installer\build rmdir /S /Q installer\build
echo OK
echo.

REM Step 2: Build SoundVault.exe
echo [2/4] Building SoundVault.exe with PyInstaller...
python -m PyInstaller SoundVault.spec --distpath dist --noconfirm
if %ERRORLEVEL% neq 0 (
    echo ERROR: SoundVault build failed!
    exit /b 1
)
echo OK - dist\SoundVault.exe
echo.

REM Step 3: Build SoundVault_Setup.exe
echo [3/4] Building SoundVault_Setup.exe (installer)...
python -m PyInstaller installer\installer.spec --workpath installer\build --distpath dist --noconfirm
if %ERRORLEVEL% neq 0 (
    echo ERROR: Installer build failed!
    exit /b 1
)
echo OK - dist\SoundVault_Setup.exe
echo.

REM Step 4: Clean up build artifacts
echo [4/4] Cleaning build artifacts...
if exist build rmdir /S /Q build
if exist installer\build rmdir /S /Q installer\build
echo OK
echo.

echo ========================================
echo  Build complete!
echo ========================================
echo.
echo  Output:
echo    dist\SoundVault.exe        - The app
echo    dist\SoundVault_Setup.exe  - Setup installer
echo.
pause
