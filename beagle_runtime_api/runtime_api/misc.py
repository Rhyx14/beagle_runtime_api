def onehot2bin(port):
    """
    将 one-hot 编码格式转换为普通二进制格式
    Args
        port (int): 输入的 ont-hot 格式的编码
    Returns:
        输出的二进制格式的编码
    
    """
    if port == 1:
        return 0
    if port == 2:
        return 1
    if port == 4:
        return 2
    if port == 8:
        return 3
    if port == 16:
        return 4
    return 0