import warnings
from functools import wraps
from typing import Callable, Optional, Union, Any

def deprecated(
    message: Optional[str] = None,
    category: type = DeprecationWarning
):
    """
    标记过时 API 的装饰器
    
    Args:
        message: 自定义的警告信息
        category: 警告类别，默认为 DeprecationWarning
    """
    def decorator(func: Callable) -> Callable:
        # 构建警告信息
        warning_msg = f"函数 '{func.__name__}' 已被废弃"
        
        if message:
            warning_msg += f"。{message}"
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 发出警告
            warnings.warn(warning_msg, category=category, stacklevel=2)
            
            # 调用原始函数
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# 使用示例
if __name__ == "__main__":
    
    # 基本用法
    @deprecated()
    def old_function():
        """这是一个旧函数"""
        print("执行旧函数")
    
    # 带自定义信息
    @deprecated(
        message="请使用 new_function() 代替",
    )
    def another_old_function(x: int, y: int) -> int:
        return x + y
    
    # 使用 FutureWarning 类别
    @deprecated(
        message="这个 API 将在未来版本中改变",
        category=FutureWarning
    )
    def soon_to_change():
        print("即将改变的函数")
    
    # 测试调用
    print("=== 测试过时 API 装饰器 ===")
    
    old_function()
    print()
    
    result = another_old_function(3, 4)
    print(f"结果: {result}")
    print()
    
    soon_to_change()
    print()
    
    # 可以捕获警告
    print("=== 捕获警告示例 ===")
    import warnings
    
    # 将警告转换为异常
    warnings.filterwarnings("error", category=DeprecationWarning)
    
    try:
        old_function()
    except DeprecationWarning as e:
        print(f"捕获到警告: {e}")