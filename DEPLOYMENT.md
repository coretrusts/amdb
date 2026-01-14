# GitHub部署指南

本指南说明如何将AmDb项目部署到GitHub组织 `coretrusts` 下的不同仓库。

## 仓库结构

项目将分为三个独立的仓库：

1. **amdb** - 源代码仓库
   - 包含所有源代码、测试、示例
   - 地址: https://github.com/coretrusts/amdb

2. **amdb-docs** - 文档仓库
   - 包含所有文档和API参考
   - 地址: https://github.com/coretrusts/amdb-docs

3. **amdb-releases** - 发行版仓库
   - 包含编译好的可执行文件和安装包
   - 地址: https://github.com/coretrusts/amdb-releases

## 快速部署

### 方法1: 使用简化脚本（推荐）

```bash
# 运行部署脚本
./deploy_simple.sh
```

脚本会：
1. 提示您创建每个仓库
2. 自动准备文件
3. 初始化Git并推送

### 方法2: 使用GitHub CLI脚本

```bash
# 安装GitHub CLI
brew install gh

# 登录
gh auth login

# 运行脚本
./deploy_to_github.sh
```

### 方法3: 手动部署

查看 [deploy_manual.md](deploy_manual.md) 了解详细的手动部署步骤。

## 创建仓库

在开始之前，需要在GitHub上创建三个仓库：

1. 访问: https://github.com/organizations/coretrusts/repositories/new
2. 创建以下仓库（都设为Public）：
   - `amdb` - 描述: "AmDb - 区块链优化数据库系统（源代码）"
   - `amdb-docs` - 描述: "AmDb - 文档和API参考"
   - `amdb-releases` - 描述: "AmDb - 发行版和可执行文件"

## 文件组织

### 源代码仓库 (amdb)
```
amdb/
├── src/              # 源代码
├── tests/            # 测试代码
├── examples/         # 示例代码
├── setup.py          # 构建脚本
├── setup_cython.py   # Cython编译脚本
├── requirements.txt  # 依赖
├── README.md         # 项目说明
└── LICENSE           # 许可证
```

### 文档仓库 (amdb-docs)
```
amdb-docs/
├── *.md              # 所有文档文件
└── README.md         # 文档索引
```

### 发行版仓库 (amdb-releases)
```
amdb-releases/
├── dist/             # 发行包
│   ├── *.tar.gz      # 压缩包
│   ├── *.dmg         # macOS安装包
│   └── *.zip         # Windows安装包
├── README.md         # 下载说明
└── CHANGELOG.md      # 更新日志
```

## 更新仓库

### 更新源代码
```bash
cd "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
git add src/ tests/ examples/
git commit -m "Update: 描述更改"
git push
```

### 更新文档
```bash
# 克隆文档仓库
git clone https://github.com/coretrusts/amdb-docs.git
cd amdb-docs

# 更新文档
cp -r "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/docs"/* .

# 提交
git add .
git commit -m "Update: 更新文档"
git push
```

### 更新发行版
```bash
# 克隆发行版仓库
git clone https://github.com/coretrusts/amdb-releases.git
cd amdb-releases

# 更新发行包
cp "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/dist"/*.tar.gz dist/
cp "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb/dist"/*.dmg dist/

# 提交
git add dist/
git commit -m "Release: v1.0.1"
git tag v1.0.1
git push origin main --tags
```

## 使用Git LFS（推荐）

对于大型二进制文件（DMG、可执行文件），建议使用Git LFS：

```bash
# 安装Git LFS
brew install git-lfs

# 在发行版仓库中启用
cd amdb-releases
git lfs install
git lfs track "*.dmg"
git lfs track "*.tar.gz"
git lfs track "*.zip"
git add .gitattributes
git commit -m "Add Git LFS tracking"
git push
```

## 创建GitHub Release

```bash
# 使用GitHub CLI创建Release
gh release create v1.0.0 \
  --title "AmDb v1.0.0" \
  --notes "首次发布" \
  dist/AmDb-1.0.0-macOS.dmg \
  dist/amdb-1.0.0-darwin-x86_64.tar.gz
```

## 故障排除

### 推送失败
1. 检查仓库是否已创建
2. 检查Git认证配置: `git config --list | grep credential`
3. 使用SSH: `git remote set-url origin git@github.com:coretrusts/amdb.git`

### 大文件问题
- 使用Git LFS处理大文件
- 或使用GitHub Releases上传大文件

### 权限问题
- 确认您是 `coretrusts` 组织的成员
- 确认有仓库的写入权限

## 相关文件

- `deploy_simple.sh` - 简化版部署脚本
- `deploy_to_github.sh` - GitHub CLI版本部署脚本
- `deploy_manual.md` - 详细手动部署指南
- `.gitignore` - Git忽略规则

