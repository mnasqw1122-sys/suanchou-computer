@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ============================================================
::  算筭字谱双击运行器
::  
::  用法：
::    1. 双击 .suan 文件 → 用这个 bat 打开 → 自动编译运行
::    2. 命令行：suan_run.bat 石破天惊.suan
::
::  文件关联方式（在 PowerShell 管理员模式下运行一次）：
::    cmd /c assoc .suan=SuanFile
::    cmd /c ftype SuanFile="D:\....\suan_run.bat" "%%1"
:: ============================================================

cd /d "%~dp0"

set "SUAN_FILE=%~1"
set "PY=py"

if "%SUAN_FILE%"=="" (
    echo.
    echo   算筭字谱运行器
    echo   SuanChou Zupu Runner
    echo.
    echo   拖一个 .suan 文件到本脚本上即可运行。
    echo   也可以在命令行输入: suan_run.bat 文件.suan
    echo.
    echo   可用的 .suan 文件：
    for %%f in (*.suan) do echo     %%f
    echo.
    pause
    exit /b
)

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║  算筭字谱运行器                          ║
echo   ║  %~nx1
echo   ╚══════════════════════════════════════════╝
echo.

%PY% suan_run.py "%SUAN_FILE%"
echo.
pause
