@echo off
chcp 65001 >nul
title 财务数据分析系统 - 快速启动

echo.
echo 🚀 财务数据分析系统 - 快速启动
echo ===============================
echo.

:: 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    echo 🔧 激活虚拟环境...
    call venv\Scripts\activate.bat
)

:: 直接启动应用
echo 🌟 启动应用服务器...
echo 📊 访问地址: http://localhost:8080
echo.

python app.py

:: 程序退出后暂停
echo.
echo 📋 应用程序已停止
pause