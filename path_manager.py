# path_manager.py

import sys
import os

def get_base_path():
    """
    获取应用程序的根目录。
    这是在任何环境（源代码、PyInstaller、Nuitka）下都可靠的终极方法。
    """
    # sys.argv[0] 是启动程序的脚本或可执行文件的路径
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def get_main_executable_path():
    """获取主程序 exe 的路径。"""
    if getattr(sys, 'frozen', False):
        # 在打包后，sys.executable 通常指向主程序本身
        return sys.executable
    else:
        # 在开发时，是 python 解释器
        return sys.executable

def get_python_interpreter_path():
    """获取用于运行子脚本的 Python 解释器路径。"""
    base_path = get_base_path()
    # Nuitka 在 standalone 模式下会把 python.exe 放在根目录
    packaged_python_path = os.path.join(base_path, "python.exe")
    
    if os.path.exists(packaged_python_path):
        return packaged_python_path
    else:
        # 如果找不到内置的，就回退到系统 python (用于开发)
        return sys.executable

def get_region_selector_script_path():
    """获取 region_selector.py 脚本的路径。"""
    return os.path.join(get_base_path(), "region_selector.py")