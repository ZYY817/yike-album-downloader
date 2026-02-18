# 一刻相册批量下载工具

一键下载百度一刻相册的所有照片和视频到本地，支持原画质、断点续传、并发下载。

## ✨ 特性

- 🚀 **高速下载**：15线程并发，充分利用带宽
- 📦 **原画质**：VIP用户可下载原始高清文件
- 💾 **断点续传**：支持中断后继续下载
- 🔍 **完整性校验**：自动验证文件大小，确保下载完整
- 📊 **进度保存**：实时保存下载进度，随时可恢复
- 📁 **智能整理**：按拍摄日期自动归类到文件夹
- 🛡️ **错误处理**：网络异常自动重试，失败记录可单独重下

## 📋 系统要求

- Windows 10/11 或 macOS 或 Linux
- Python 3.8+
- Chrome 浏览器（用于登录获取Cookie）
- 百度一刻相册账号（建议VIP，可下载大视频）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置下载路径（可选）

编辑 `config.py`，修改下载目录：

```python
DOWNLOAD_DIR = Path(r"E:\照片")  # 改成你的路径
```

### 3. 运行下载

**Windows用户**：
```powershell
.\run.ps1
```

**Linux/Mac用户**：
```bash
python main.py
```

### 4. 扫码登录

首次运行会自动打开浏览器，扫码登录一刻相册即可。

## 📖 详细说明

### 工作流程

1. **登录获取Cookie** (`probe.py`)
2. **下载照片** (`download.py`)
3. **下载视频** (`download_video_final.py`)
4. **验证完整性** (`verify_download.py`)
5. **按日期整理** (`organizer.py`)

### 配置说明

`config.py` 中可配置的参数：

```python
DOWNLOAD_DIR = Path(r"E:\照片")           # 下载目录
ORGANIZED_DIR = Path(r"E:\照片_整理")     # 整理后目录
CONCURRENT_DOWNLOADS = 15                  # 并发线程数
DOWNLOAD_TIMEOUT = 180                     # 下载超时(秒)
REQUEST_DELAY = 0.2                        # 请求间隔(秒)
```

### 单独运行模块

```bash
python probe.py              # 只登录
python download.py           # 只下载照片
python download_video_final.py  # 只下载视频
python verify_download.py    # 验证完整性
python organizer.py          # 整理照片
python stats.py              # 查看统计
```

## 🔧 故障排查

### Cookie过期
重新运行：`python probe.py`

### 视频下载失败（errno=50007）
需要开通百度网盘VIP会员

### 下载速度慢
增加并发数（修改`config.py`中的`CONCURRENT_DOWNLOADS`）

### Chrome未找到
修改 `config.py` 中的 `CHROME_CANDIDATES`

## 📊 项目结构

```
yike-album/
├── config.py              # 配置文件
├── utils.py               # 公共工具
├── probe.py               # 登录获取Cookie
├── download.py            # 照片下载
├── download_video_final.py # 视频下载
├── verify_download.py     # 完整性验证
├── organizer.py           # 按日期整理
├── stats.py               # 统计信息
├── main.py                # 统一入口
├── run.ps1                # Windows一键脚本
├── requirements.txt       # Python依赖
└── README.md              # 本文档
```

## ⚠️ 注意事项

1. **隐私安全**：`probe_result.json`包含登录Cookie，请勿分享
2. **VIP限制**：大视频（>30MB）需要VIP会员才能下载原画质
3. **存储空间**：确保有足够磁盘空间（建议预留100GB+）
4. **网络稳定**：建议在稳定网络环境下运行
5. **合法使用**：仅用于备份个人照片，请勿用于其他用途

## 📝 更新日志

### v1.0.0 (2026-02-18)
- ✅ 支持照片和视频批量下载
- ✅ 原画质下载（VIP）
- ✅ 断点续传
- ✅ 并发下载
- ✅ 完整性校验
- ✅ 按日期整理

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
