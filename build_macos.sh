#!/bin/bash

echo "========================================"
echo "加权平均分规划助手 - macOS 构建脚本"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.8 或更高版本"
    exit 1
fi

echo "[1/4] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "[2/4] 激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install -r requirements.txt

echo "[3/4] 使用 PyInstaller 构建 APP..."
pyinstaller --clean build.spec

echo "[4/4] 构建完成！"
echo ""
echo "应用程序位置: dist/加权平均分规划助手.app"
echo ""
echo "提示: 如需分发，可以将 .app 文件压缩为 .dmg 或 .zip"
echo ""
