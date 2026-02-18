# 贡献指南

感谢你考虑为一刻相册批量下载工具做出贡献！

## 如何贡献

### 报告Bug

如果你发现了Bug，请创建一个Issue并包含以下信息：

1. **问题描述**：清晰描述遇到的问题
2. **复现步骤**：详细的操作步骤
3. **预期行为**：你期望发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：
   - 操作系统版本
   - Python版本
   - 是否有VIP会员
6. **错误日志**：如果有的话，请附上完整的错误信息

### 提交功能建议

如果你有新功能的想法：

1. 先检查是否已有类似的Issue
2. 创建新Issue，描述功能需求和使用场景
3. 等待维护者反馈

### 提交代码

1. Fork本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8代码风格
- 添加必要的注释
- 确保代码可以正常运行
- 更新相关文档

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/ZYY817/yike-album-downloader.git
cd yike-album-downloader

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 运行测试
python main.py
```

## 问题讨论

如果你有任何问题，欢迎在Issues中讨论！

## 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性的批评
- 关注对项目最有利的事情

感谢你的贡献！🎉
