# 贡献指南

感谢您对AmDb项目的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告问题

如果您发现了Bug或有功能建议，请：

1. 检查[现有Issues](https://github.com/coretrusts/amdb/issues)是否已有相关问题
2. 如果没有，请创建新的Issue，包含：
   - 问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（操作系统、Python版本等）

### 提交代码

1. **Fork仓库**
   ```bash
   git clone https://github.com/coretrusts/amdb.git
   cd amdb
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **编写代码**
   - 遵循项目的代码风格
   - 添加必要的注释和文档
   - 确保代码通过测试

4. **提交更改**
   ```bash
   git add .
   git commit -m "描述您的更改"
   ```

5. **推送并创建Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   然后在GitHub上创建Pull Request

### 代码规范

- 使用Python 3.7+
- 遵循PEP 8代码风格
- 添加类型提示（Type Hints）
- 编写单元测试
- 更新相关文档

### 测试

在提交PR之前，请确保：

```bash
# 运行单元测试
python -m pytest tests/

# 运行性能测试
python tests/performance_benchmark.py

# 检查代码风格
flake8 src/
```

### 文档贡献

文档贡献同样重要！您可以：

- 改进现有文档
- 添加示例代码
- 修复文档错误
- 翻译文档

### 行为准则

- 尊重所有贡献者
- 建设性的反馈
- 包容和友好

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/coretrusts/amdb.git
cd amdb

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

## 问题分类

- `bug`: Bug报告
- `feature`: 新功能请求
- `enhancement`: 功能改进
- `documentation`: 文档相关
- `performance`: 性能优化
- `question`: 问题咨询

## 联系方式

- GitHub Issues: https://github.com/coretrusts/amdb/issues
- GitHub Discussions: https://github.com/coretrusts/amdb/discussions

感谢您的贡献！

