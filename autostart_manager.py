# autostart_manager.py

"""
管理应用程序在Windows上的开机自启动设置。

此模块通过读写Windows注册表来启用或禁用程序的开机自启动功能。
所有操作均在 HKEY_CURRENT_USER 下进行，因此不需要管理员权限。
"""

import winreg
import sys
import os

# 定义应用程序在注册表中的唯一名称，用于创建和删除键值。
APP_NAME = "KeyMouse"

# 定义Windows启动项在注册表中的标准路径。
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_executable_path():
    """获取程序可执行文件的绝对路径。

    此函数能够智能地区分开发环境和打包后的生产环境。

    Returns:
        str: 指向 python.exe (开发时) 或 KeyMouse.exe (打包后) 的绝对路径。
    """
    return sys.executable


def is_enabled():
    """检查开机自启动是否已经为当前程序启用。

    通过查询注册表，检查是否存在指定的键值，并验证其路径是否
    与当前运行的程序路径一致。

    Returns:
        bool: 如果已启用，则返回 True，否则返回 False。
    """
    try:
        # 尝试以只读模式打开启动项注册表键。
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        
        # 查询名为 APP_NAME 的值。如果存在，它会返回存储的路径和类型。
        stored_path, _ = winreg.QueryValueEx(key, APP_NAME)
        
        winreg.CloseKey(key)
        
        # 规范化路径并进行比较，确保注册表中存储的路径与当前程序路径一致。
        # 这可以防止旧版本的安装残留干扰判断。
        return os.path.normpath(stored_path) == os.path.normpath(get_executable_path())
        
    except FileNotFoundError:
        # 如果注册表项或值不存在，说明未启用，这是正常情况。
        return False
    except Exception as e:
        # 捕获其他潜在错误，例如权限问题。
        print(f"检查自启动状态时出错: {e}")
        return False


def enable():
    """启用开机自启动。

    在注册表中创建一个条目，指向当前程序的可执行文件。

    Raises:
        Exception: 当写入注册表失败时，将异常向上抛出，以便GUI可以捕获。
    """
    try:
        # 获取当前可执行文件的路径。
        exe_path = get_executable_path()
        
        # 以写入模式打开启动项注册表键，如果键不存在则会自动创建。
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        
        # 创建/更新一个名为 APP_NAME 的字符串值(REG_SZ)，其数据为程序的路径。
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        
        winreg.CloseKey(key)
        print(f"开机自启动已启用: {exe_path}")
        
    except Exception as e:
        print(f"启用自启动时出错: {e}")
        raise e


def disable():
    """禁用开机自启动。

    从注册表中删除与当前程序相关的条目。

    Raises:
        Exception: 当删除注册表值失败时，将异常向上抛出。
    """
    try:
        # 以写入模式打开启动项注册表键。
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        
        # 删除名为 APP_NAME 的值。
        winreg.DeleteValue(key, APP_NAME)
        
        winreg.CloseKey(key)
        print("开机自启动已禁用。")
        
    except FileNotFoundError:
        # 如果值本来就不存在，说明已经禁用了，这不是一个错误。
        print("自启动项未找到，无需禁用。")
        pass
    except Exception as e:
        print(f"禁用自启动时出错: {e}")
        raise e