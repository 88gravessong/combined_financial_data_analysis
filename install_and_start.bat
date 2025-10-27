@echo off
chcp 65001 >nul
title 财务数据分析系统 - 一键安装启动

echo.
echo 🎯 财务数据分析系统 - 一键安装启动
echo ==================================
echo.

:: 检查管理员权限（可选）
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 💡 建议以管理员身份运行以获得最佳体验
    echo.
)

:: 检查Python环境
echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python环境
    echo.
    echo 🔗 正在尝试打开Python官网下载页面...
    start https://www.python.org/downloads/
    echo.
    echo 请安装Python 3.8或更高版本后重新运行此脚本
    pause
    exit /b 1
)

:: 显示Python版本
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ 找到 %PYTHON_VERSION%

:: 检查pip
echo 🔍 检查pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip未正确安装
    pause
    exit /b 1
)

:: 创建项目目录结构
echo 📁 检查项目结构...
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
if not exist "uploads" mkdir uploads

:: 检查必要文件
set "missing_files="
if not exist "app.py" set "missing_files=%missing_files% app.py"
if not exist "index.html" set "missing_files=%missing_files% index.html"
if not exist "requirements.txt" set "missing_files=%missing_files% requirements.txt"

if not "%missing_files%"=="" (
    echo ❌ 缺少必要文件:%missing_files%
    echo 请确保所有项目文件都在当前目录中
    pause
    exit /b 1
)

:: 创建或检查虚拟环境
echo 🐍 配置Python虚拟环境...
if not exist "venv" (
    echo    创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

:: 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 激活虚拟环境失败
    pause
    exit /b 1
)

:: 升级pip到最新版本
echo 📦 升级pip到最新版本...
python -m pip install --upgrade pip --quiet

:: 安装项目依赖
echo 📦 安装项目依赖...
echo    正在安装: flask pandas openpyxl werkzeug
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ 安装依赖失败，尝试重新安装...
    pip install flask==3.1.1 pandas>=2.0.0 openpyxl>=3.1.0 werkzeug>=3.1.0
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

:: 检查安装结果
echo 🔍 验证安装...
python -c "import flask, pandas, openpyxl; print('✅ 所有依赖安装成功')" 2>nul
if errorlevel 1 (
    echo ❌ 依赖验证失败
    pause
    exit /b 1
)

:: 创建桌面快捷方式（可选）
echo 🔗 是否创建桌面快捷方式？ (y/n)
set /p create_shortcut="请选择: "
if /i "%create_shortcut%"=="y" (
    echo 正在创建快捷方式...
    echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
    echo sLinkFile = "%USERPROFILE%\Desktop\财务数据分析系统.lnk" >> CreateShortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
    echo oLink.TargetPath = "%cd%\quick_start.bat" >> CreateShortcut.vbs
    echo oLink.WorkingDirectory = "%cd%" >> CreateShortcut.vbs
    echo oLink.Description = "财务数据分析系统" >> CreateShortcut.vbs
    echo oLink.Save >> CreateShortcut.vbs
    cscript CreateShortcut.vbs >nul 2>&1
    del CreateShortcut.vbs >nul 2>&1
    echo ✅ 桌面快捷方式已创建
)

echo.
echo 🎉 安装完成！
echo.
echo 📋 系统信息:
echo    Python版本: %PYTHON_VERSION%
echo    工作目录: %cd%
echo    虚拟环境: venv\
echo.
echo 🚀 正在启动财务数据分析系统...
echo 📊 访问地址: http://localhost:8080
echo 🌐 浏览器地址: http://127.0.0.1:8080
echo 💡 使用 Ctrl+C 停止服务器
echo.

:: 尝试自动打开浏览器
timeout /t 3 /nobreak >nul
start http://localhost:8080 >nul 2>&1

:: 启动应用
python app.py

:: 程序退出处理
echo.
echo 📋 财务数据分析系统已停止运行
echo 💡 如需重新启动，请运行 quick_start.bat
pause