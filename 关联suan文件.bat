@echo off
:: ======================================================
::  关联 .suan 文件到 suan.exe
::  
::  以管理员身份运行此脚本。
::  运行后，双击任何 .suan 文件会自动编译并执行。
:: ======================================================

cd /d "%~dp0"

echo  算筭字谱文件关联工具
echo.
echo  运行后，双击 .suan 文件将自动用 suan.exe 打开并运行。
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo  [错误] 请以管理员身份运行此脚本。
    echo  右键此文件 → 以管理员身份运行。
    pause
    exit /b
)

set "SUAN_EXE=%~dp0suan.exe"

if not exist "%SUAN_EXE%" (
    echo  [错误] 未找到 suan.exe
    pause
    exit /b
)

echo  注册 .suan 文件类型...
ftype SuanFile="%SUAN_EXE%" "%%1" >nul 2>&1
assoc .suan=SuanFile >nul 2>&1

echo.
echo  [OK] 完成！现在双击任何 .suan 文件即可运行。
echo.
pause
