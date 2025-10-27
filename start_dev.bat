@echo off
chcp 65001 >nul
title 财务数据分析系统 - 开发模式

echo.
echo 🛠️  财务数据分析系统 - 开发模式
echo ================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python环境
    pause
    exit /b 1
)

:: 检查并创建虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

:: 安装开发依赖
echo 📦 安装依赖（包含开发工具）...
pip install -r requirements.txt
pip install flask-cors python-dotenv

:: 设置开发环境变量
set FLASK_ENV=development
set FLASK_DEBUG=1

:: 显示环境信息
echo.
echo 📋 环境信息:
echo    Python版本: 
python --version
echo    Flask版本: 
python -c "import flask; print('Flask', flask.__version__)"
echo    工作目录: %cd%
echo.

echo 🚀 启动开发服务器...
echo 📊 访问地址: http://localhost:8080
echo 🔧 开发模式已启用（自动重载）
echo 💡 使用 Ctrl+C 停止服务器
echo.

:: 启动Flask应用
python app.py

:: 程序退出后显示信息
echo.
echo 📋 开发服务器已停止
pause