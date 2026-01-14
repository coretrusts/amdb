# 手动部署到GitHub指南

如果不想使用自动脚本，可以按照以下步骤手动部署。

## 前提条件

1. 安装Git: `brew install git` 或从 https://git-scm.com/ 下载
2. 安装GitHub CLI: `brew install gh` 或从 https://cli.github.com/ 下载
3. 登录GitHub: `gh auth login`

## 创建仓库

### 1. 源代码仓库 (amdb)

```bash
# 创建仓库
gh repo create coretrusts/amdb --public --description "AmDb - 区块链优化数据库系统（源代码）"

# 初始化并推送
cd "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
git init
git remote add origin https://github.com/coretrusts/amdb.git

# 添加源代码文件
git add src/ tests/ examples/ setup.py setup_cython.py requirements.txt README.md LICENSE .gitignore
git commit -m "Initial commit: AmDb源代码"
git branch -M main
git push -u origin main
```

### 2. 文档仓库 (amdb-docs)

```bash
# 创建仓库
gh repo create coretrusts/amdb-docs --public --description "AmDb - 文档和API参考"

# 初始化并推送
mkdir -p /tmp/amdb-docs
cd /tmp/amdb-docs
git init
git remote add origin https://github.com/coretrusts/amdb-docs.git

# 复制文档
cp -r "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/docs"/* .

# 创建README
cat > README.md << 'EOF'
# AmDb 文档

本仓库包含AmDb数据库系统的完整文档。

## 文档索引

- [网络架构](docs/NETWORK_ARCHITECTURE.md)
- [集成指南](docs/INTEGRATION_GUIDE.md)
- [构建和打包](docs/BUILD_AND_PACKAGE.md)
- [远程操作](docs/REMOTE_OPERATIONS.md)
- [删除功能](docs/DELETE_FEATURES.md)

## 快速开始

查看 [集成指南](docs/INTEGRATION_GUIDE.md) 了解如何在自己的项目中使用AmDb。
EOF

git add .
git commit -m "Initial commit: AmDb文档"
git branch -M main
git push -u origin main
```

### 3. 发行版仓库 (amdb-releases)

```bash
# 创建仓库
gh repo create coretrusts/amdb-releases --public --description "AmDb - 发行版和可执行文件"

# 初始化并推送
mkdir -p /tmp/amdb-releases
cd /tmp/amdb-releases
git init
git remote add origin https://github.com/coretrusts/amdb-releases.git

# 创建目录结构
mkdir -p dist releases

# 复制发行包
cp "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/dist"/*.tar.gz dist/ 2>/dev/null || true
cp "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/dist"/*.dmg dist/ 2>/dev/null || true
cp "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/dist"/*.zip dist/ 2>/dev/null || true

# 创建README
cat > README.md << 'EOF'
# AmDb 发行版

本仓库包含AmDb的编译好的可执行文件和安装包。

## 下载

### macOS
- **DMG安装包**: [AmDb-1.0.0-macOS.dmg](dist/AmDb-1.0.0-macOS.dmg)
- **压缩包**: [amdb-1.0.0-darwin-x86_64.tar.gz](dist/amdb-1.0.0-darwin-x86_64.tar.gz)

### Linux
- **压缩包**: [amdb-1.0.0-linux-x86_64.tar.gz](dist/amdb-1.0.0-linux-x86_64.tar.gz)

### Windows
- **ZIP包**: [amdb-1.0.0-windows-x86_64.zip](dist/amdb-1.0.0-windows-x86_64.zip)

## 使用

### macOS DMG
1. 下载并双击DMG文件
2. 将AmDb拖拽到Applications文件夹
3. 在启动台找到AmDb

### 压缩包
1. 下载对应平台的压缩包
2. 解压: `tar -xzf amdb-*.tar.gz`
3. 运行: `./amdb-cli` 或 `./amdb-server`

## 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。
EOF

# 创建CHANGELOG
cat > CHANGELOG.md << 'EOF'
# 更新日志

## 1.0.0 (2026-01-13)

### 新增功能
- ✅ 完整的数据库系统实现
- ✅ LSM Tree存储引擎
- ✅ Merkle Tree数据完整性验证
- ✅ 版本管理系统
- ✅ 网络服务器和客户端
- ✅ CLI命令行工具
- ✅ GUI图形界面管理器
- ✅ 多数据库支持
- ✅ 远程操作支持（统计信息、配置管理）
- ✅ 跨平台打包（macOS、Linux、Windows）

### 性能
- 顺序写入: ~17,751 记录/秒
- 批量写入: 支持大规模数据

### 文档
- 网络架构文档
- 集成指南
- 构建和打包指南
- API参考
EOF

git add .
git commit -m "Initial release: v1.0.0"
git branch -M main
git push -u origin main
```

## 使用Git LFS（可选）

对于大型二进制文件（如DMG、可执行文件），建议使用Git LFS：

```bash
# 安装Git LFS
brew install git-lfs

# 在发行版仓库中启用
cd /tmp/amdb-releases
git lfs install
git lfs track "*.dmg"
git lfs track "*.tar.gz"
git lfs track "*.zip"
git add .gitattributes
git commit -m "Add Git LFS tracking"
git push
```

## 更新仓库

### 更新源代码
```bash
cd "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
git add src/ tests/ examples/
git commit -m "Update: 描述更改内容"
git push
```

### 更新文档
```bash
cd /tmp/amdb-docs
git pull
cp -r "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/docs"/* .
git add .
git commit -m "Update: 更新文档"
git push
```

### 更新发行版
```bash
cd /tmp/amdb-releases
git pull
cp "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/dist"/*.tar.gz dist/
cp "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/dist"/*.dmg dist/
git add dist/
git commit -m "Release: v1.0.1"
git tag v1.0.1
git push origin main --tags
```

## 创建GitHub Release

```bash
# 创建Release
gh release create v1.0.0 \
  --title "AmDb v1.0.0" \
  --notes "首次发布" \
  dist/AmDb-1.0.0-macOS.dmg \
  dist/amdb-1.0.0-darwin-x86_64.tar.gz
```

