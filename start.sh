#!/bin/bash

echo "💰 财务数据分析系统启动脚本"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python，请先安装Python"
    exit 1
fi

# 检查依赖文件
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到requirements.txt文件"
    exit 1
fi

# 安装依赖
echo "📦 检查并安装依赖..."
pip3 install -r requirements.txt

# 检查必要文件
required_files=("app.py" "analysis_multi.py" "index.html")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done

echo "✅ 所有依赖已就绪"
echo ""

# 安全检查
echo "� 执行安全检查..."
if [ "${FLASK_DEBUG:-false}" = "true" ]; then
    echo "⚠️  警告: 调试模式已启用，请确保这是开发环境！"
fi

if [ "${FLASK_HOST:-127.0.0.1}" = "0.0.0.0" ]; then
    echo "⚠️  警告: 服务器绑定到所有网络接口，请确保网络安全！"
fi

# 显示当前配置
echo "📋 当前配置:"
python3 config.py
echo ""

echo "�🚀 启动Web服务器..."
host=${FLASK_HOST:-127.0.0.1}
port=${FLASK_PORT:-8080}
echo "📊 访问地址: http://$host:$port"
echo "💡 使用 Ctrl+C 停止服务器"
echo ""

# 启动Flask应用
python3 app.py 