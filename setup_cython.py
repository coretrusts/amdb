"""
Cython扩展构建脚本
用于构建高性能的C扩展模块
目标：超越PolarDB的20.55亿tpmC性能
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import sys

# 检测平台，优化编译参数
compile_args = ['-O3']
link_args = ['-O3']

if sys.platform == 'darwin':  # macOS
    compile_args.extend(['-march=native', '-mtune=native'])
elif sys.platform.startswith('linux'):  # Linux
    compile_args.extend(['-march=native', '-mtune=native', '-mavx2'])
elif sys.platform.startswith('win'):  # Windows
    compile_args.extend(['/O2', '/arch:AVX2'])

extensions = [
    Extension(
        "amdb.storage.skip_list_cython",
        ["src/amdb/storage/skip_list_cython.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=compile_args,
        extra_link_args=link_args,
        language="c"
    ),
    Extension(
        "amdb.version_cython",
        ["src/amdb/version_cython.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=compile_args,
        extra_link_args=link_args,
        language="c"
    ),
]

# 确保编译后的文件在正确的位置
import os
package_dir = os.path.join(os.path.dirname(__file__), 'src')

setup(
    name="amdb-cython",
    version="1.0.0",
    description="AmDb Cython优化扩展 - 目标超越PolarDB性能",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
            'initializedcheck': False,
            'nonecheck': False,
            'infer_types': True,
        },
        annotate=True  # 生成HTML注解文件，用于性能分析
    ),
    zip_safe=False,
)

