@echo off
echo ========================================
echo 加权平均分规划助手 - Windows 构建脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo [1/4] 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
)

echo [2/4] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo [3/4] 使用 PyInstaller 构建 EXE...
pyinstaller --clean build.spec

echo [4/4] 构建完成！
echo.
echo 可执行文件位置: dist\加权平均分规划助手.exe
echo.
pause
