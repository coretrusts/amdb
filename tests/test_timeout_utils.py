"""
测试超时工具
为读写测试提供超时控制
"""

import signal
import time
from contextlib import contextmanager
from typing import Callable, Any, Optional
import threading


class TimeoutError(Exception):
    """超时异常"""
    pass


@contextmanager
def timeout_context(seconds: float):
    """
    超时上下文管理器
    
    Args:
        seconds: 超时时间（秒）
    
    Raises:
        TimeoutError: 如果操作超时
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"操作超时（{seconds}秒）")
    
    # 设置信号处理器（仅Unix系统）
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(seconds))
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows系统使用线程方式
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = True
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(seconds)
        
        if thread.is_alive():
            raise TimeoutError(f"操作超时（{seconds}秒）")
        
        if exception[0]:
            raise exception[0]
        
        yield


def with_timeout(seconds: float, operation: Callable[[], Any], 
                 operation_name: str = "操作") -> Any:
    """
    执行带超时的操作
    
    Args:
        seconds: 超时时间（秒）
        operation: 要执行的操作（无参数函数）
        operation_name: 操作名称（用于错误信息）
    
    Returns:
        操作结果
    
    Raises:
        TimeoutError: 如果操作超时
        AssertionError: 如果操作超时（用于测试失败）
    """
    start_time = time.time()
    
    if hasattr(signal, 'SIGALRM'):
        # Unix系统使用信号
        def timeout_handler(signum, frame):
            elapsed = time.time() - start_time
            raise TimeoutError(
                f"{operation_name}超时（{seconds}秒），实际耗时: {elapsed:.2f}秒"
            )
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(seconds) + 1)  # 多给1秒缓冲
        
        try:
            result = operation()
            signal.alarm(0)
            return result
        except TimeoutError:
            raise
        except Exception as e:
            signal.alarm(0)
            raise
        finally:
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows系统使用线程
        result_container = [None]
        exception_container = [None]
        
        def run_operation():
            try:
                result_container[0] = operation()
            except Exception as e:
                exception_container[0] = e
        
        thread = threading.Thread(target=run_operation)
        thread.daemon = True
        thread.start()
        thread.join(seconds)
        
        if thread.is_alive():
            elapsed = time.time() - start_time
            raise TimeoutError(
                f"{operation_name}超时（{seconds}秒），实际耗时: {elapsed:.2f}秒"
            )
        
        if exception_container[0]:
            raise exception_container[0]
        
        return result_container[0]


def assert_performance_with_timeout(operation: Callable[[], Any],
                                    max_seconds: float,
                                    operation_name: str = "操作",
                                    min_throughput: Optional[float] = None,
                                    item_count: Optional[int] = None):
    """
    断言性能测试在超时时间内完成，并可选择检查吞吐量
    
    Args:
        operation: 要执行的操作
        max_seconds: 最大允许时间（秒）
        operation_name: 操作名称
        min_throughput: 最小吞吐量（项/秒），如果提供则检查
        item_count: 操作项数（用于计算吞吐量）
    
    Raises:
        TimeoutError: 如果超时
        AssertionError: 如果吞吐量不达标
    """
    start_time = time.time()
    
    try:
        result = with_timeout(max_seconds, operation, operation_name)
        elapsed = time.time() - start_time
        
        # 检查吞吐量（允许1%的误差）
        if min_throughput is not None and item_count is not None:
            actual_throughput = item_count / elapsed
            if actual_throughput < min_throughput * 0.99:  # 允许1%误差
                raise AssertionError(
                    f"{operation_name}吞吐量不达标: "
                    f"期望 >= {min_throughput:,.0f} 项/秒, "
                    f"实际 {actual_throughput:,.0f} 项/秒"
                )
        
        return result
    except TimeoutError as e:
        # 转换为AssertionError以便测试框架识别
        raise AssertionError(
            f"{operation_name}性能不合格: {str(e)}"
        ) from e

