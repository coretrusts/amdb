# AmDb Makefile
# 支持跨平台构建和打包

.PHONY: help install build cli gui native test benchmark clean all

# 默认目标
help:
	@echo "AmDb 构建系统"
	@echo ""
	@echo "可用目标:"
	@echo "  make install      - 安装依赖"
	@echo "  make build        - 编译原生扩展"
	@echo "  make cli          - 打包CLI工具"
	@echo "  make gui           - 打包GUI管理器"
	@echo "  make native       - 编译Cython扩展"
	@echo "  make test          - 运行测试"
	@echo "  make benchmark     - 运行性能测试"
	@echo "  make clean         - 清理构建文件"
	@echo "  make all           - 执行全部构建步骤"

# 安装依赖
install:
	pip install -r requirements.txt
	pip install pyinstaller cython

# 编译原生扩展
build: native

# 编译Cython扩展
native:
	python3 setup_cython.py build_ext --inplace

# 打包CLI
cli:
	@echo "打包CLI工具..."
	@if [ "$(shell uname -s)" = "Linux" ] || [ "$(shell uname -s)" = "Darwin" ]; then \
		./build_all_platforms.sh; \
	else \
		build_all_platforms.bat; \
	fi

# 打包GUI
gui:
	@echo "打包GUI管理器..."
	@if [ "$(shell uname -s)" = "Linux" ] || [ "$(shell uname -s)" = "Darwin" ]; then \
		./build_all_platforms.sh; \
	else \
		build_all_platforms.bat; \
	fi

# 运行测试
test:
	python3 -m pytest tests/ -v

# 运行性能测试
benchmark:
	python3 tests/performance_benchmark.py

# 清理
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.spec
	rm -rf __pycache__/
	rm -rf src/**/__pycache__/
	rm -rf src/**/*.pyc
	rm -rf src/**/*.so
	rm -rf src/**/*.pyd
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 全部构建
all: install build cli gui
	@echo "构建完成！"

