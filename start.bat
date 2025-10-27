@echo off
chcp 65001 >nul
title 财务数据分析系统

echo.
echo 💰 财务数据分析系统启动脚本
echo ================================
echo.

:: 检查Python环境
echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python
    echo 💡 建议下载Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查必要文件
echo 📋 检查必要文件...
if not exist "requirements.txt" (
    echo ❌ 未找到requirements.txt文件
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ❌ 未找到app.py文件
    pause
    exit /b 1
)

if not exist "index.html" (
    echo ❌ 未找到index.html文件
    pause
    exit /b 1
)

if not exist "analysis_multi.py" (
    echo ❌ 未找到analysis_multi.py文件
    pause
    exit /b 1
)

:: 检查并创建虚拟环境
echo 🐍 检查虚拟环境...
if not exist "venv" (
    echo 📦 创建虚拟环境...
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

:: 升级pip
echo 📦 升级pip...
python -m pip install --upgrade pip >nul 2>&1

:: 安装依赖
echo 📦 安装项目依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 安装依赖失败
    pause
    exit /b 1
)

echo.
echo ✅ 所有依赖已就绪
echo.
echo 🚀 启动Web服务器...
echo 📊 访问地址: http://localhost:8080
echo 💡 使用 Ctrl+C 停止服务器
echo 🔗 或者在浏览器中打开: http://127.0.0.1:8080
echo.

:: 启动Flask应用
python app.py

:: 如果程序异常退出，暂停以便查看错误信息
if errorlevel 1 (
    echo.
    echo ❌ 应用程序异常退出
    pause
)