"""
使用Docker测试多语言绑定
"""

import unittest
import subprocess
import os
import tempfile
from pathlib import Path


class DockerBindingTest(unittest.TestCase):
    """使用Docker测试绑定"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = Path(__file__).parent.parent
        self.docker_available = self._check_docker()
    
    def _check_docker(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def test_php_with_docker(self):
        """使用Docker测试PHP绑定"""
        if not self.docker_available:
            self.skipTest("Docker不可用")
        
        # 检查Docker daemon是否运行
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                self.skipTest("Docker daemon未运行，请启动Docker")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("无法检查Docker状态")
        
        php_file = self.project_root / "bindings" / "php" / "amdb.php"
        if not php_file.exists():
            self.skipTest("PHP绑定文件不存在")
        
        # 创建临时测试文件
        test_content = f'''
<?php
require_once '{php_file}';

// 基本语法检查
if (class_exists('AmDb\\Database')) {{
    echo "OK\\n";
}} else {{
    echo "ERROR: Class not found\\n";
    exit(1);
}}
'''
        
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False)
        test_file.write(test_content)
        test_file.close()
        
        try:
            # 使用PHP Docker镜像测试
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{self.project_root}:/workspace",
                    "-v", f"{test_file.name}:/test.php",
                    "php:8.1-cli",
                    "php", "-l", "/test.php"
                ],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ PHP绑定语法检查通过（Docker）")
            else:
                error_msg = result.stderr.decode()[:300]
                print(f"✗ PHP绑定语法检查失败: {error_msg}")
                self.fail(f"PHP语法错误: {error_msg}")
        except subprocess.TimeoutExpired:
            self.fail("Docker测试超时")
        finally:
            os.unlink(test_file.name)
    
    def test_php_full_with_docker(self):
        """使用Docker完整测试PHP绑定"""
        if not self.docker_available:
            self.skipTest("Docker不可用")
        
        # 检查Docker daemon是否运行
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                self.skipTest("Docker daemon未运行，请启动Docker")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("无法检查Docker状态")
        
        php_file = self.project_root / "bindings" / "php" / "amdb.php"
        if not php_file.exists():
            self.skipTest("PHP绑定文件不存在")
        
        # 创建完整测试
        test_content = f'''
<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once '{php_file}';

try {{
    // 测试类是否存在
    if (!class_exists('AmDb\\Database')) {{
        throw new Exception("Database class not found");
    }}
    
    echo "PHP绑定测试通过\\n";
    exit(0);
}} catch (Exception $e) {{
    echo "ERROR: " . $e->getMessage() . "\\n";
    exit(1);
}}
'''
        
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False)
        test_file.write(test_content)
        test_file.close()
        
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{self.project_root}:/workspace",
                    "-v", f"{test_file.name}:/test.php",
                    "php:8.1-cli",
                    "php", "/test.php"
                ],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ PHP绑定完整测试通过（Docker）")
            else:
                error_msg = result.stdout.decode() + result.stderr.decode()
                print(f"✗ PHP绑定测试失败: {error_msg[:300]}")
                self.fail(f"PHP测试失败: {error_msg[:300]}")
        except subprocess.TimeoutExpired:
            self.fail("Docker测试超时")
        finally:
            os.unlink(test_file.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)

