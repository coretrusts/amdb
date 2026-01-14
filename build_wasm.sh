#!/bin/bash
# AmDb WebAssembly 编译脚本
# 使用Emscripten将AmDb编译为WebAssembly

set -e

echo "=== AmDb WebAssembly 编译 ==="
echo ""

# 检查Emscripten是否安装
if ! command -v emcc &> /dev/null; then
    echo "错误: 未找到Emscripten"
    echo ""
    echo "请先安装Emscripten:"
    echo "  git clone https://github.com/emscripten-core/emsdk.git"
    echo "  cd emsdk"
    echo "  ./emsdk install latest"
    echo "  ./emsdk activate latest"
    echo "  source ./emsdk_env.sh"
    exit 1
fi

echo "✓ Emscripten已安装"
echo ""

# 创建构建目录
BUILD_DIR="build/wasm"
mkdir -p "$BUILD_DIR"

echo "📦 准备Python环境..."
# 使用Pyodide的Python构建
# 或者使用pyodide-build

echo "📝 创建WebAssembly版本的AmDb核心模块..."

# 创建简化的Python版本（用于WebAssembly）
cat > "$BUILD_DIR/amdb_wasm.py" << 'PYTHON_EOF'
"""
AmDb WebAssembly版本
简化版本，用于浏览器演示
"""
import json
from typing import Dict, List, Tuple, Optional, Any

class DatabaseWASM:
    """AmDb数据库的WebAssembly版本（内存实现）"""
    
    def __init__(self, data_dir: str = None):
        self.data: Dict[bytes, bytes] = {}
        self.versions: Dict[bytes, List[Dict]] = {}
        self.current_version = 0
        
    def put(self, key: bytes, value: bytes) -> Tuple[bool, bytes]:
        """写入键值对"""
        self.data[key] = value
        self.current_version += 1
        
        # 记录版本
        if key not in self.versions:
            self.versions[key] = []
        self.versions[key].append({
            'version': self.current_version,
            'value': value,
            'timestamp': 0  # 简化版本
        })
        
        # 计算简单的哈希
        import hashlib
        root_hash = hashlib.sha256(f"{key}:{value}".encode()).digest()
        return True, root_hash
    
    def get(self, key: bytes, version: Optional[int] = None) -> Optional[bytes]:
        """读取键值"""
        if version is not None:
            if key in self.versions:
                for v in reversed(self.versions[key]):
                    if v['version'] <= version:
                        return v['value']
            return None
        return self.data.get(key)
    
    def batch_put(self, items: List[Tuple[bytes, bytes]]) -> Tuple[bool, bytes]:
        """批量写入"""
        for key, value in items:
            self.put(key, value)
        
        # 计算批量哈希
        import hashlib
        combined = b''.join([k + v for k, v in items])
        root_hash = hashlib.sha256(combined).digest()
        return True, root_hash
    
    def delete(self, key: bytes) -> bool:
        """删除键（标记删除）"""
        if key in self.data:
            self.data[key] = b'__DELETED__'
            return True
        return False
    
    def flush(self, force_sync: bool = False) -> bool:
        """刷新（WebAssembly版本中为无操作）"""
        return True
    
    def get_history(self, key: bytes) -> List[Dict]:
        """获取版本历史"""
        return self.versions.get(key, [])
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_keys': len(self.data),
            'current_version': self.current_version,
            'merkle_root': b'0' * 32  # 简化版本
        }

# 导出供JavaScript使用
__all__ = ['DatabaseWASM']
PYTHON_EOF

echo "✓ 创建了WebAssembly版本的Python模块"
echo ""

echo "🔧 编译为WebAssembly..."
echo "注意: 完整编译需要配置Pyodide环境"
echo ""

# 使用pyodide-build（如果可用）
if command -v pyodide-build &> /dev/null; then
    echo "使用pyodide-build编译..."
    pyodide-build amdb_wasm.py -o "$BUILD_DIR/amdb_wasm.js"
else
    echo "⚠️  pyodide-build未安装"
    echo ""
    echo "安装方法:"
    echo "  pip install pyodide-build"
    echo ""
    echo "或者使用Pyodide的在线构建工具"
fi

echo ""
echo "✅ WebAssembly构建脚本已创建"
echo ""
echo "📋 下一步:"
echo "  1. 安装Pyodide构建工具: pip install pyodide-build"
echo "  2. 运行: ./build_wasm.sh"
echo "  3. 将生成的wasm文件集成到demo.html"

