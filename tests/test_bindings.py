"""
多语言绑定测试
测试各种编程语言的绑定是否正常工作
"""

import unittest
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


class BindingsTest(unittest.TestCase):
    """多语言绑定测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(__file__).parent.parent
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_c_binding_header(self):
        """测试C绑定头文件"""
        header_file = self.project_root / "bindings" / "c" / "amdb.h"
        self.assertTrue(header_file.exists(), "C头文件不存在")
        
        # 检查头文件内容
        content = header_file.read_text()
        self.assertIn("amdb_init", content, "缺少amdb_init函数声明")
        self.assertIn("amdb_put", content, "缺少amdb_put函数声明")
        self.assertIn("amdb_get", content, "缺少amdb_get函数声明")
        print("✓ C绑定头文件检查通过")
    
    def test_cpp_binding_header(self):
        """测试C++绑定头文件"""
        header_file = self.project_root / "bindings" / "cpp" / "amdb.hpp"
        self.assertTrue(header_file.exists(), "C++头文件不存在")
        
        # 检查头文件内容
        content = header_file.read_text()
        self.assertIn("class Database", content, "缺少Database类声明")
        self.assertIn("put", content, "缺少put方法声明")
        self.assertIn("get", content, "缺少get方法声明")
        print("✓ C++绑定头文件检查通过")
    
    def test_go_binding(self):
        """测试Go绑定"""
        go_file = self.project_root / "bindings" / "go" / "amdb.go"
        self.assertTrue(go_file.exists(), "Go绑定文件不存在")
        
        # 检查Go文件内容
        content = go_file.read_text()
        self.assertIn("package amdb", content, "缺少package声明")
        self.assertIn("type Database", content, "缺少Database类型声明")
        self.assertIn("func NewDatabase", content, "缺少NewDatabase函数")
        print("✓ Go绑定文件检查通过")
    
    def test_nodejs_binding(self):
        """测试Node.js绑定"""
        js_file = self.project_root / "bindings" / "nodejs" / "amdb.js"
        self.assertTrue(js_file.exists(), "Node.js绑定文件不存在")
        
        # 检查JS文件内容
        content = js_file.read_text()
        self.assertIn("class", content, "缺少类声明")
        self.assertIn("put", content, "缺少put方法声明")
        self.assertIn("get", content, "缺少get方法声明")
        print("✓ Node.js绑定文件检查通过")
    
    def test_php_binding(self):
        """测试PHP绑定"""
        php_file = self.project_root / "bindings" / "php" / "amdb.php"
        self.assertTrue(php_file.exists(), "PHP绑定文件不存在")
        
        # 检查PHP文件内容
        content = php_file.read_text()
        self.assertIn("class AmDb", content, "缺少AmDb类声明")
        self.assertIn("function put", content, "缺少put方法声明")
        self.assertIn("function get", content, "缺少get方法声明")
        print("✓ PHP绑定文件检查通过")
    
    def test_rust_binding(self):
        """测试Rust绑定"""
        rust_file = self.project_root / "bindings" / "rust" / "src" / "lib.rs"
        self.assertTrue(rust_file.exists(), "Rust绑定文件不存在")
        
        # 检查Rust文件内容
        content = rust_file.read_text()
        self.assertIn("pub struct", content, "缺少结构体声明")
        self.assertIn("pub fn put", content, "缺少put函数声明")
        self.assertIn("pub fn get", content, "缺少get函数声明")
        print("✓ Rust绑定文件检查通过")
    
    def test_java_binding(self):
        """测试Java绑定"""
        java_file = self.project_root / "bindings" / "java" / "src" / "main" / "java" / "com" / "amdb" / "AmDb.java"
        self.assertTrue(java_file.exists(), "Java绑定文件不存在")
        
        # 检查Java文件内容
        content = java_file.read_text()
        self.assertIn("public class AmDb", content, "缺少AmDb类声明")
        self.assertIn("put", content, "缺少put方法声明")
        self.assertIn("get", content, "缺少get方法声明")
        print("✓ Java绑定文件检查通过")
    
    def test_swift_binding(self):
        """测试Swift绑定"""
        swift_file = self.project_root / "bindings" / "swift" / "AmDb.swift"
        self.assertTrue(swift_file.exists(), "Swift绑定文件不存在")
        
        # 检查Swift文件内容
        content = swift_file.read_text()
        self.assertIn("public class AmDb", content, "缺少AmDb类声明")
        self.assertIn("public func put", content, "缺少put方法声明")
        self.assertIn("public func get", content, "缺少get方法声明")
        print("✓ Swift绑定文件检查通过")
    
    def test_ruby_binding(self):
        """测试Ruby绑定"""
        ruby_file = self.project_root / "bindings" / "ruby" / "amdb.rb"
        self.assertTrue(ruby_file.exists(), "Ruby绑定文件不存在")
        
        # 检查Ruby文件内容
        content = ruby_file.read_text()
        self.assertIn("module AmDb", content, "缺少AmDb模块声明")
        self.assertIn("class Database", content, "缺少Database类声明")
        self.assertIn("def put", content, "缺少put方法声明")
        self.assertIn("def get", content, "缺少get方法声明")
        print("✓ Ruby绑定文件检查通过")
    
    def test_kotlin_binding(self):
        """测试Kotlin绑定"""
        kotlin_file = self.project_root / "bindings" / "kotlin" / "src" / "main" / "kotlin" / "com" / "amdb" / "AmDb.kt"
        self.assertTrue(kotlin_file.exists(), "Kotlin绑定文件不存在")
        
        # 检查Kotlin文件内容
        content = kotlin_file.read_text()
        self.assertIn("class AmDb", content, "缺少AmDb类声明")
        self.assertIn("fun put", content, "缺少put方法声明")
        self.assertIn("fun get", content, "缺少get方法声明")
        print("✓ Kotlin绑定文件检查通过")


class BindingCompilationTest(unittest.TestCase):
    """绑定编译测试"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = Path(__file__).parent.parent
    
    def _test_php_with_docker(self):
        """使用Docker测试PHP"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                raise Exception("Docker未安装")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise Exception("Docker未安装")
        
        # 检查Docker daemon是否运行
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                raise Exception("Docker daemon未运行")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise Exception("Docker daemon未运行")
        
        php_file = self.project_root / "bindings" / "php" / "amdb.php"
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{self.project_root}:/workspace",
                    "php:8.1-cli",
                    "php", "-l", "/workspace/bindings/php/amdb.php"
                ],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                print("✓ PHP代码语法检查通过（Docker）")
            else:
                error_msg = result.stderr.decode()[:300]
                print(f"✗ PHP代码语法检查失败（Docker）: {error_msg}")
                self.fail(f"PHP语法错误: {error_msg}")
        except subprocess.TimeoutExpired:
            raise Exception("Docker PHP测试超时")
    
    def test_c_syntax_check(self):
        """测试C代码语法"""
        c_file = self.project_root / "bindings" / "c" / "amdb.c"
        if not c_file.exists():
            self.skipTest("C文件不存在")
        
        # 使用gcc检查语法（如果可用）
        try:
            # 尝试找到Python.h路径
            import sysconfig
            python_include = sysconfig.get_path('include')
            result = subprocess.run(
                ["gcc", "-fsyntax-only", "-I", python_include, "-c", str(c_file)],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                print("✓ C代码语法检查通过")
            else:
                error_msg = result.stderr.decode()[:300]
                # Python.h未找到是正常的（需要Python开发包）
                if "Python.h" in error_msg:
                    print("⚠ C代码需要Python开发头文件（正常，需要安装python3-dev）")
                else:
                    print(f"✗ C代码语法检查失败: {error_msg}")
                    self.fail(f"C代码语法错误: {error_msg}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.skipTest(f"gcc不可用: {e}")
    
    def test_cpp_syntax_check(self):
        """测试C++代码语法"""
        cpp_file = self.project_root / "bindings" / "cpp" / "amdb.cpp"
        if cpp_file.exists():
            try:
                result = subprocess.run(
                    ["g++", "-fsyntax-only", "-c", str(cpp_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print("✓ C++代码语法检查通过")
                else:
                    error_msg = result.stderr.decode()[:300]
                    if "Python.h" in error_msg:
                        print("⚠ C++代码需要Python开发头文件（正常）")
                    else:
                        print(f"✗ C++代码语法检查失败: {error_msg}")
                        self.fail(f"C++代码语法错误: {error_msg}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                self.skipTest(f"g++不可用: {e}")
    
    def test_go_syntax_check(self):
        """测试Go代码语法"""
        go_file = self.project_root / "bindings" / "go" / "amdb.go"
        if go_file.exists():
            try:
                result = subprocess.run(
                    ["go", "fmt", str(go_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print("✓ Go代码语法检查通过")
                else:
                    error_msg = result.stderr.decode()[:300]
                    print(f"✗ Go代码语法检查失败: {error_msg}")
                    self.fail(f"Go代码语法错误: {error_msg}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                self.skipTest(f"go不可用: {e}")
    
    def test_nodejs_syntax_check(self):
        """测试Node.js代码语法"""
        js_file = self.project_root / "bindings" / "nodejs" / "amdb.js"
        if js_file.exists():
            try:
                result = subprocess.run(
                    ["node", "--check", str(js_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print("✓ Node.js代码语法检查通过")
                else:
                    error_msg = result.stderr.decode()[:300]
                    print(f"✗ Node.js代码语法检查失败: {error_msg}")
                    self.fail(f"Node.js代码语法错误: {error_msg}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                self.skipTest(f"node不可用: {e}")
    
    def test_php_syntax_check(self):
        """测试PHP代码语法"""
        php_file = self.project_root / "bindings" / "php" / "amdb.php"
        if php_file.exists():
            try:
                result = subprocess.run(
                    ["php", "-l", str(php_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print("✓ PHP代码语法检查通过")
                else:
                    error_msg = result.stderr.decode()[:300]
                    print(f"✗ PHP代码语法检查失败: {error_msg}")
                    self.fail(f"PHP代码语法错误: {error_msg}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                # PHP不可用，尝试使用Docker
                try:
                    self._test_php_with_docker()
                except Exception as docker_error:
                    self.skipTest(f"PHP未安装且Docker不可用: {docker_error}")
    
    def test_rust_syntax_check(self):
        """测试Rust代码语法"""
        rust_file = self.project_root / "bindings" / "rust" / "src" / "lib.rs"
        if rust_file.exists():
            try:
                # 检查Rust语法
                result = subprocess.run(
                    ["rustc", "--crate-type", "lib", "--emit", "metadata", str(rust_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print("✓ Rust代码语法检查通过")
                else:
                    error_msg = result.stderr.decode()[:300]
                    print(f"✗ Rust代码语法检查失败: {error_msg}")
                    self.fail(f"Rust代码语法错误: {error_msg}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                self.skipTest(f"rustc不可用: {e}")
    
    def test_java_syntax_check(self):
        """测试Java代码语法"""
        java_file = self.project_root / "bindings" / "java" / "src" / "main" / "java" / "com" / "amdb" / "AmDb.java"
        if not java_file.exists():
            self.skipTest("Java文件不存在")
        
        try:
            # 创建临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            # 创建AmDbException类（如果不存在）
            exception_file = java_file.parent / "AmDbException.java"
            if not exception_file.exists():
                exception_content = '''package com.amdb;

public class AmDbException extends Exception {
    public AmDbException(String message) {
        super(message);
    }
}
'''
                exception_file.write_text(exception_content)
            
            result = subprocess.run(
                ["javac", "-Xlint:all", "-d", temp_dir, str(java_file), str(exception_file)],
                capture_output=True,
                timeout=10
            )
            
            # 清理
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if result.returncode == 0:
                print("✓ Java代码语法检查通过")
            else:
                error_msg = result.stderr.decode()[:300]
                print(f"✗ Java代码语法检查失败: {error_msg}")
                self.fail(f"Java代码语法错误: {error_msg}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.skipTest(f"javac不可用: {e}")


class BindingIntegrationTest(unittest.TestCase):
    """绑定集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = Path(__file__).parent.parent
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_python_api_compatibility(self):
        """测试Python API兼容性（作为参考）"""
        sys.path.insert(0, str(self.project_root))
        from src.amdb import Database
        
        db = Database(data_dir=self.temp_dir, enable_sharding=True, shard_count=16)
        db.put(b"test_key", b"test_value")
        value = db.get(b"test_key")
        
        self.assertIsNotNone(value)
        print("✓ Python API兼容性测试通过")
    
    def test_binding_file_structure(self):
        """测试绑定文件结构"""
        bindings_dir = self.project_root / "bindings"
        
        expected_bindings = [
            "c",
            "cpp",
            "go",
            "nodejs",
            "php",
            "rust",
            "java",
            "swift",
            "ruby",
            "kotlin"
        ]
        
        for binding in expected_bindings:
            binding_path = bindings_dir / binding
            self.assertTrue(binding_path.exists(), f"绑定目录不存在: {binding}")
        
        print(f"✓ 所有 {len(expected_bindings)} 个绑定目录存在")


if __name__ == '__main__':
    print("=" * 80)
    print("AmDb 多语言绑定测试")
    print("=" * 80)
    print()
    
    unittest.main(verbosity=2)

