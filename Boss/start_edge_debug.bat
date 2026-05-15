@echo off
setlocal

set "USER_DATA_DIR=D:\aiSpider\Boss\state\edge_profile"
set "DEBUG_PORT=9222"
set "START_URL=https://login.zhipin.com/?ka=header-login"
set "EDGE_EXE="

if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE_EXE if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

if not defined EDGE_EXE goto edge_missing

if not exist "%USER_DATA_DIR%" (
  mkdir "%USER_DATA_DIR%"
)

echo Starting Edge debug window...
start "" "%EDGE_EXE%" --new-window --remote-debugging-port=%DEBUG_PORT% --user-data-dir="%USER_DATA_DIR%" "%START_URL%"
echo.
echo Edge should now be listening on port %DEBUG_PORT%.
echo If the login page opens, finish login there first.
echo Then run:
echo python -m Boss --attach-edge --force-login
echo.
pause
exit /b 0

:edge_missing
echo Edge executable not found.
echo Checked:
echo   %ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe
echo   %ProgramFiles%\Microsoft\Edge\Application\msedge.exe
echo.
pause
exit /b 1
