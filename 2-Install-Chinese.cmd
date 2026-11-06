@echo off
setlocal
chcp 65001 >nul
if not exist "%~dp0Install.ps1" goto missing_files
if not exist "%~dp0PatchData.zip" goto missing_files
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1" -Mode Chinese
set "patchExit=%errorlevel%"
echo.
if not "%patchExit%"=="0" echo 操作未完成，请查看上面的错误信息。
pause
exit /b %patchExit%

:missing_files
echo 缺少配套的 Install.ps1 或 PatchData.zip，安装尚未开始。
echo 请勿在压缩包预览窗口中直接双击 CMD。
echo 请右键最外层 NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip，选择“全部解压”。
echo 解压完成后，进入普通文件夹 NITW-Xbox-CN，再运行本 CMD。
echo 请保持 CMD、Install.ps1 和 PatchData.zip 位于同一个文件夹。
echo.
pause
exit /b 2
