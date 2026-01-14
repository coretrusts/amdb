# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- 性能优化：目标达到LevelDB的550,000 ops/s顺序写入性能
- Cython扩展：编译关键路径以提升性能
- 更多语言绑定支持

## [1.0.0] - 2024-01-XX

### 新增
- 混合存储引擎：LSM树、B+树、Merkle树的组合设计
- 版本管理系统：完整的版本历史和时间点查询
- 数据持久化：支持WAL日志、SSTable、版本文件等多种格式
- 多语言绑定：支持Python、Go、C、C++、Node.js、PHP、Rust、Java、Swift、Ruby、Kotlin等10+种语言
- CLI工具：命令行界面管理数据库
- GUI管理器：桌面版数据库管理工具
- 网络服务：支持远程数据库访问
- 分布式架构：支持多节点集群部署
- 性能优化：顺序写入100,000+ ops/s，随机读取280,000+ ops/s

### 优化
- 批量写入性能优化
- 内存管理优化
- 锁竞争减少
- 版本管理开销降低

### 修复
- 数据持久化问题修复
- Merkle树加载错误修复
- 内存泄漏问题修复

### 文档
- 完整的API文档
- 快速开始指南
- 集成指南
- 性能优化指南
- 官网部署（getamdb.com）

## [0.9.0] - 2024-01-XX

### 新增
- 初始版本发布
- 基础存储引擎实现
- 版本管理功能
- CLI工具

---

## 版本说明

- **主版本号**：不兼容的API修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

## 链接

- [GitHub Releases](https://github.com/coretrusts/amdb/releases)
- [完整变更历史](https://github.com/coretrusts/amdb/commits/main)
