@echo off
setlocal
cd /d "%~dp0"
cd /d "%~dp0\.."

set RELEASE_DIR=STEM_Study_Generator_Portable
set BUILD_PY=.venv\Scripts\python.exe
set PYINSTALLER=.venv\Scripts\pyinstaller.exe

if not exist "%BUILD_PY%" (
    echo Creating local build environment...
    python -m venv .venv
)

echo Installing build requirements...
"%BUILD_PY%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1

echo Cleaning previous build output...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"

echo Building executable with PyInstaller...
"%PYINSTALLER%" ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --name STEM_Study_Generator ^
  --add-data "src\stem_study_generator\app.py;stem_study_generator" ^
  --collect-all streamlit ^
  --collect-all altair ^
  --collect-all pydeck ^
  src\stem_study_generator\launcher.py
if errorlevel 1 exit /b 1

echo Creating portable release folder...
mkdir "%RELEASE_DIR%"
xcopy /e /i /y "dist\STEM_Study_Generator\*" "%RELEASE_DIR%\" >nul
mkdir "%RELEASE_DIR%\data"
mkdir "%RELEASE_DIR%\exports"
mkdir "%RELEASE_DIR%\reports"

(
echo @echo off
echo cd /d "%%~dp0"
echo start "" "STEM_Study_Generator.exe"
) > "%RELEASE_DIR%\Start.bat"

(
echo STEM Study Generator Portable
echo =============================
echo.
echo HOW TO RUN
echo 1. Open this folder.
echo 2. Double-click Start.bat.
echo 3. The app opens in your browser at http://localhost:8501.
echo.
echo Python is not required on the computer running this portable release.
echo.
echo HOW TO BUILD
echo 1. On a build computer with Python installed, open this project folder.
echo 2. Double-click build_release.bat.
echo 3. The portable release is created in STEM_Study_Generator_Portable.
echo.
echo HOW TO TRANSFER TO ANOTHER COMPUTER
echo 1. Copy the entire STEM_Study_Generator_Portable folder.
echo 2. Move it with a USB drive, zip file, or normal file copy.
echo 3. Keep all files and folders together, including the internal dependency folder.
echo 4. On the other Windows computer, unzip if needed and double-click Start.bat.
echo.
echo STUDENT PROGRESS AND BACKUPS
echo Student progress is stored in data\stem_study.db.
echo To back up progress, copy the data folder.
echo To move progress to another copy, replace that copy's data folder with your backup.
echo.
echo DATA STORAGE
echo The app creates data\stem_study.db automatically if it does not exist.
echo Generated attempts, answers, confidence ratings, and dashboard stats stay inside this portable folder.
) > "%RELEASE_DIR%\README.txt"

echo.
echo Release created: %RELEASE_DIR%
echo Double-click %RELEASE_DIR%\Start.bat to run it.
endlocal
