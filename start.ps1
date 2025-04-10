# 行政服务平台PowerShell启动脚本
$Host.UI.RawUI.WindowTitle = "行政服务平台启动工具"

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "    行政服务平台一键启动工具 (PowerShell)" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否已安装
try {
    $pythonVersion = python --version
    Write-Host "[信息] 检测到Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Python，请先安装Python 3.8或更高版本" -ForegroundColor Red
    Write-Host "可以从 https://www.python.org/downloads/ 下载安装" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按任意键退出"
    exit 1
}

# 检查虚拟环境是否存在
if (-not (Test-Path "venv")) {
    Write-Host "[信息] 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
    if (-not $?) {
        Write-Host "[错误] 创建虚拟环境失败，请检查Python版本" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
    Write-Host "[成功] 虚拟环境创建完成" -ForegroundColor Green
}

# 激活虚拟环境
Write-Host "[信息] 激活虚拟环境..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# 检查是否存在requirements.txt文件
if (-not (Test-Path "requirements.txt")) {
    Write-Host "[错误] 未找到requirements.txt文件，请确保文件存在" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 安装依赖
Write-Host "[信息] 检查并安装依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
if (-not $?) {
    Write-Host "[警告] 依赖安装出现问题，尝试使用国内镜像源..." -ForegroundColor Yellow
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if (-not $?) {
        Write-Host "[错误] 依赖安装失败，请检查网络连接或手动安装" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
}
Write-Host "[成功] 依赖安装完成" -ForegroundColor Green

# 启动应用
Write-Host ""
Write-Host "[信息] 正在启动行政服务平台..." -ForegroundColor Cyan
Write-Host "[提示] 请使用浏览器访问 http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "[提示] 默认管理员账号: admin  密码: 123456" -ForegroundColor Green
Write-Host "[提示] 按 Ctrl+C 可以停止服务器" -ForegroundColor Yellow
Write-Host ""

try {
    python app.py
} catch {
    Write-Host ""
    Write-Host "[错误] 程序异常退出，错误信息: $_" -ForegroundColor Red
    Read-Host "按任意键退出"
} 