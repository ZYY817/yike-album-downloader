# File: tools/yike-album/run.ps1
# 一刻相册迁移一键脚本
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  一刻相册 -> 本地下载 -> 按日期整理" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查 Cookie
$probeFile = Join-Path $scriptDir "probe_result.json"
if (-not (Test-Path $probeFile)) {
    Write-Host "[步骤1] Cookie 不存在，启动登录..." -ForegroundColor Yellow
    python probe.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "登录失败，退出" -ForegroundColor Red
        Pop-Location; exit 1
    }
} else {
    Write-Host "[步骤1] Cookie 已存在，跳过登录" -ForegroundColor Green
}

# 步骤2: 批量下载
Write-Host ""
Write-Host "[步骤2] 开始批量下载..." -ForegroundColor Yellow
python download.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "下载出错" -ForegroundColor Red
    Pop-Location; exit 1
}

# 步骤3: 按日期整理
Write-Host ""
Write-Host "[步骤3] 按日期整理照片..." -ForegroundColor Yellow
python organizer.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "整理出错" -ForegroundColor Red
    Pop-Location; exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  全部完成! 请手动上传到夸克网盘" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Pop-Location
