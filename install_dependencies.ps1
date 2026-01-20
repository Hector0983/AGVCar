# BTC 交易策略系统 - 依赖安装脚本
# 自动检测并安装所需的 Python 包

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  BTC 交易策略系统 - 依赖包安装" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 是否安装
Write-Host "[1/3] 检查 Python 环境..." -ForegroundColor Yellow
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue

if (-not $pythonCommand) {
    Write-Host "❌ 未检测到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}

# 获取 Python 版本
$pythonVersion = python --version 2>&1
Write-Host "✅ 已检测到: $pythonVersion" -ForegroundColor Green
Write-Host ""

# 安装依赖包
Write-Host "[2/3] 安装依赖包..." -ForegroundColor Yellow
Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Gray
Write-Host ""

$packages = @("ccxt", "pandas", "ta", "numpy", "requests")

foreach ($package in $packages) {
    Write-Host "正在安装 $package..." -ForegroundColor Cyan
    python -m pip install $package --quiet --disable-pip-version-check
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $package 安装成功" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $package 安装失败，请检查网络连接" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[3/3] 验证安装..." -ForegroundColor Yellow

# 验证包是否正确安装
python -c "import ccxt, pandas, ta, numpy, requests; print('✅ 所有依赖包验证通过')" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "  🎉 安装完成！" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "现在你可以运行策略脚本了：" -ForegroundColor White
    Write-Host "  python btc_trading_strategy.py" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠️  部分包安装可能失败，请检查错误信息" -ForegroundColor Yellow
    Write-Host ""
}

pause
