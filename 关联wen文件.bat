@echo off
:: ======================================================
::  关联 .wen 文件到 wen.exe
::
::  以管理员身份运行此脚本。
::  运行后，双击任何 .wen 文件自动编译并显示结果。
:: ======================================================

cd /d "%~dp0"

echo  文语言文件关联工具
echo.
echo  运行后，双击 .wen 文件将自动用 wen.exe 执行。
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo  [错误] 请以管理员身份运行此脚本。
    echo  右键此文件 → 以管理员身份运行。
    pause
    exit /b
)

set "WEN_EXE=%~dp0wen.exe"

if not exist "%WEN_EXE%" (
    echo  [错误] 未找到 wen.exe
    pause
    exit /b
)

echo  注册 .wen 文件类型...
ftype WenFile="%WEN_EXE%" "%%1" >nul 2>&1
assoc .wen=WenFile >nul 2>&1

echo.
echo  [OK] 完成！现在双击任何 .wen 文件即可运行。
echo.
pause
