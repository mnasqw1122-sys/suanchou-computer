@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  ============================================================
echo    SuanChou Computer / 算筭计算机
echo    — = ON (1)    | = OFF (0)
echo  ============================================================
echo.
echo    [核心系统]
echo    1. 交互模式 (Interactive mode)
echo    2. 完整演示 (Full pipeline demo)
echo    3. 算筭虚拟机演示 (VM execution demo)
echo    4. 搜索引擎交互 (Interactive search engine)
echo    5. 效率分析报告 (Efficiency report)
echo.
echo    [新增探索]
echo    6. 字族演化树 (Character family tree)
echo    7. 逐笔识别动画 (Stroke-by-stroke animation)
echo    8. 算筭码染色 (Rod code color visualization)
echo.
echo    q. 退出 (Quit)
echo.
set /p choice="  请选择 (1-8/q): "

if "%choice%"=="1" py main.py --interactive
if "%choice%"=="2" py suanchou_search.py --all
if "%choice%"=="3" py suanchou_vm.py
if "%choice%"=="4" py suanchou_search.py -i
if "%choice%"=="5" py efficiency_analysis.py
if "%choice%"=="6" py suanchou_tree.py
if "%choice%"=="7" py suanchou_animation.py
if "%choice%"=="8" py suanchou_color.py
if "%choice%"=="q" goto end
if "%choice%"=="Q" goto end

:end
echo.
