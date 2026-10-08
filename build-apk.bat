@echo off
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "TOOLS=%ROOT%.tools"

echo ===============================================
echo  PlantMind APK build - one command
echo ===============================================

REM ---------- 0. Node (bundled in .tools\node) ----------
set "PATH=%TOOLS%\node;%PATH%"
set "npm_config_cache=%TOOLS%\npm-cache"

REM ---------- Scratch dirs (this PC cannot create files under the user
REM profile, so all Java/Android scratch locations are redirected here) ------
for %%D in (tmp android-home gradle-home) do (
  if not exist "%TOOLS%\%%D" mkdir "%TOOLS%\%%D" 2>nul
)
set "JAVA_TOOL_OPTIONS=-Djava.io.tmpdir=%TOOLS%\tmp"
set "ANDROID_USER_HOME=%TOOLS%\android-home"
set "GRADLE_USER_HOME=%TOOLS%\gradle-home"

REM ---------- 1. Java 17 ----------
set "JDK_DIR=%TOOLS%\jdk-17"
if not exist "%JDK_DIR%\bin\java.exe" if exist "%TOOLS%\jdk-extract" for /d %%D in ("%TOOLS%\jdk-extract\jdk-17*") do set "JDK_DIR=%%D"
if exist "%JDK_DIR%\bin\java.exe" (
  echo [1/5] Java 17 found
  goto have_java
)
echo [1/5] Downloading Java 17 - Temurin JDK...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse' -OutFile '%TOOLS%\jdk.zip'"
if errorlevel 1 goto fail_java_dl
echo Extracting Java...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Expand-Archive -Path '%TOOLS%\jdk.zip' -DestinationPath '%TOOLS%\jdk-extract' -Force"
for /d %%D in ("%TOOLS%\jdk-extract\*") do (
  if exist "%%D\bin\java.exe" set "JDK_DIR=%%D"
)
del "%TOOLS%\jdk.zip" 2>nul
if not exist "%JDK_DIR%\bin\java.exe" goto fail_java_dl
echo [1/5] Java 17 ready
:have_java
set "JAVA_HOME=%JDK_DIR%"
set "PATH=%JAVA_HOME%\bin;%PATH%"

REM ---------- 2+3. Android SDK (direct download, no sdkmanager) ----------
set "SDK=%TOOLS%\android-sdk"
if exist "%SDK%\platforms\android-34\android.jar" (
  echo [2/5] Android SDK found
  goto have_sdk
)
echo [2/5] Installing Android SDK packages directly...
powershell -NoProfile -ExecutionPolicy Bypass -File "%TOOLS%\install-sdk.ps1"
if not exist "%SDK%\platforms\android-34\android.jar" (
  echo SDK install failed - see message above.
  pause
  exit /b 1
)
:have_sdk
set "ANDROID_HOME=%SDK%"
set "ANDROID_SDK_ROOT=%SDK%"
echo [3/5] SDK ready

REM ---------- 4. Web build + Capacitor sync ----------
cd /d "%ROOT%frontend"
if exist node_modules goto have_deps
echo [4/5] Installing frontend npm dependencies...
call "%TOOLS%\node\npm.cmd" install
if errorlevel 1 goto fail_npm
:have_deps
echo [4/5] Building web assets and syncing to Android...
call "%TOOLS%\node\npm.cmd" run build
if errorlevel 1 goto fail
call "%TOOLS%\node\npx.cmd" cap sync android
if errorlevel 1 goto fail

REM ---------- 5. Compile APK with Gradle ----------
echo [5/5] Compiling debug APK - first run downloads Gradle dependencies...
cd /d "%ROOT%frontend\android"
if exist "%TOOLS%\gradle-8.2.1\bin\gradle.bat" (
  call "%TOOLS%\gradle-8.2.1\bin\gradle.bat" assembleDebug --no-daemon
) else (
  call gradlew.bat assembleDebug
)
if errorlevel 1 goto fail

echo.
echo ===============================================
echo  DONE! Single APK file:
echo  %ROOT%PlantMind.apk
echo  also at frontend\android\app\build\outputs\apk\debug\app-debug.apk
echo  Send it to your phone and install it.
echo ===============================================
copy /y "app\build\outputs\apk\debug\app-debug.apk" "%ROOT%PlantMind.apk" >nul
pause
exit /b 0

:fail_java_dl
echo FAILED to download or extract Java - check internet connection.
pause
exit /b 1
:fail_npm
echo npm install failed.
pause
exit /b 1
:fail
echo BUILD FAILED - see messages above.
pause
exit /b 1
