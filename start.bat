@echo off
REM 行政服务平台一键启动脚本
echo ===================================
echo    行政服务平台一键启动工具
echo ===================================

REM 检查Python是否已安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 可以从 https://www.python.org/downloads/ 下载安装
    echo.
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "venv\" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败，请检查Python版本
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
)

REM 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate

REM 安装依赖
echo [信息] 检查并安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [警告] 依赖安装出现问题，尝试使用国内镜像源...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请检查网络连接或手动安装
        pause
        exit /b 1
    )
)
echo [成功] 依赖安装完成

REM 启动应用
echo.
echo [信息] 正在启动行政服务平台...
echo [提示] 本地访问地址: http://127.0.0.1:5000
echo [提示] 外网访问地址: http://本机IP:5000 (将"本机IP"替换为您的计算机IP地址)
echo [提示] 默认管理员账号: admin  密码: 123456
echo [提示] 按 Ctrl+C 可以停止服务器
echo.
python app.py

REM 如果程序异常退出，暂停以查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序异常退出，错误代码: %errorlevel%
    pause
) 