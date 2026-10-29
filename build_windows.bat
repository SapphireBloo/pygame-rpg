@echo off
rem ===================================================================
rem  Builds the Windows playtest version of Chin Check Charlie.
rem  Double-click this file. It takes a few minutes the first time.
rem
rem  Everything it makes goes in %USERPROFILE%\ChinCheckCharlie-build
rem  (outside OneDrive and outside the project), and it opens that
rem  folder when it's done. Send your testers:
rem    ChinCheckCharlie-windows.zip      (Windows: unzip, run the .exe)
rem    ChinCheckCharlie-linux-source.zip (Linux: unzip, bash run_linux.sh)
rem ===================================================================
setlocal
cd /d "%~dp0"
set "OUT=%USERPROFILE%\ChinCheckCharlie-build"
set "VENV=%OUT%\venv"

echo.
echo  Building Chin Check Charlie for Windows...
echo  (output: %OUT%)
echo.

set "PY=python"
where py >nul 2>nul && set "PY=py -3"

if not exist "%VENV%\Scripts\python.exe" (
    echo  Setting up a build environment...
    %PY% -m venv "%VENV%" || goto :fail
)
"%VENV%\Scripts\python.exe" -m pip install --quiet --upgrade pip
"%VENV%\Scripts\python.exe" -m pip install --quiet -r requirements.txt pyinstaller || goto :fail

echo  Bundling the game (Python, pygame, art, and sound)...
"%VENV%\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --log-level WARN ^
    --name ChinCheckCharlie ^
    --add-data "%~dp0assets;assets" ^
    --distpath "%OUT%\dist" --workpath "%OUT%\work" --specpath "%OUT%" ^
    main.py || goto :fail

copy /y "PLAYTEST.md" "%OUT%\dist\ChinCheckCharlie\PLAYTEST.txt" >nul

echo  Zipping it up...
powershell -NoProfile -Command "Compress-Archive -Path '%OUT%\dist\ChinCheckCharlie' -DestinationPath '%OUT%\ChinCheckCharlie-windows.zip' -Force" || goto :fail

rem The Linux friend gets the source plus run_linux.sh (needs everything committed first)
where git >nul 2>nul && git archive --format=zip --prefix=ChinCheckCharlie/ -o "%OUT%\ChinCheckCharlie-linux-source.zip" HEAD

echo.
echo  Done!
echo    Windows testers: %OUT%\ChinCheckCharlie-windows.zip
if exist "%OUT%\ChinCheckCharlie-linux-source.zip" echo    Linux tester:    %OUT%\ChinCheckCharlie-linux-source.zip  (built from your last commit)
echo.
explorer "%OUT%"
pause
exit /b 0

:fail
echo.
echo  Build failed. Scroll up for the error message.
pause
exit /b 1
