# 创建 amdb-scripts 仓库指南

## 问题

`https://github.com/coretrusts/amdb-scripts` 返回404，说明仓库尚未创建。

## 解决方案

### 方法1: 使用GitHub CLI（推荐）

如果您已安装GitHub CLI (`gh`)，运行：

```bash
gh repo create coretrusts/amdb-scripts \
  --public \
  --description "AmDb - 构建、部署和维护脚本" \
  --source=. \
  --remote=origin-scripts \
  --push
```

### 方法2: 使用提供的脚本

运行：

```bash
./push_scripts.sh
```

脚本会提示您：
1. 在GitHub上手动创建仓库
2. 然后自动推送内容

### 方法3: 手动创建和推送

#### 步骤1: 在GitHub上创建仓库

1. 访问: https://github.com/organizations/coretrusts/repositories/new
2. 仓库名称: `amdb-scripts`
3. 描述: `AmDb - 构建、部署和维护脚本`
4. 可见性: Public
5. 不要初始化README、.gitignore或license
6. 点击"Create repository"

#### 步骤2: 推送本地内容

```bash
cd "/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"

# 运行推送脚本
./push_scripts.sh
```

## 包含的脚本文件

### 构建脚本
- `build_all_platforms.sh` - 跨平台构建脚本（Linux/macOS）
- `build_all_platforms.bat` - Windows构建脚本
- `build_distribution.sh` - 创建分发包
- `build_dmg.sh` - 创建macOS DMG安装包
- `build_windows.bat` - Windows构建脚本
- `build_complete_package.sh` - 完整打包脚本
- `rebuild_all.sh` - 完整重建脚本
- `Makefile` - Make构建文件

### 部署脚本
- `deploy_direct.sh` - 直接SSH推送
- `deploy_simple.sh` - 简化部署脚本
- `deploy_ssh.sh` - SSH方式部署
- `final_deploy.sh` - 最终部署脚本
- `create_and_deploy.sh` - 创建并部署
- `quick_push.sh` - 快速推送脚本
- `create_bindings_repo.sh` - 创建bindings仓库脚本
- `quick_push_bindings.sh` - 快速推送bindings脚本

### 安装脚本
- `install.sh` - Linux/macOS安装脚本
- `install.bat` - Windows安装脚本

### 构建配置
- `setup.py` - Python包配置
- `setup_cython.py` - Cython编译配置

## 验证

推送完成后，访问 https://github.com/coretrusts/amdb-scripts 确认内容已正确上传。

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases
- **多语言绑定**: https://github.com/coretrusts/amdb-bindings

