"""
该文件负责封装win平台的相关函数,目前主要是封装关于鼠标滚动效果相关的函数
"""
# win_platform.py

import ctypes
import ctypes.wintypes

# 定义Windows API中需要的常量
INPUT_MOUSE = 0
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120  # 标准的滚轮滚动单位，我们这里不用它，但SendInput内部可能参考

# 定义SendInput函数需要的C语言结构体
# 详情请参阅Microsoft文档: https://docs.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-mouseinput
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.wintypes.LONG),
                ("dy", ctypes.wintypes.LONG),
                ("mouseData", ctypes.wintypes.DWORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))]

class INPUT_I(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD),
                ("ii", INPUT_I)]

class WinPlatformScroller:
    """
    一个封装了Windows平台底层滚动API的控制器。
    它使用ctypes和Win32 SendInput函数来发送像素级的滚轮事件，
    从而绕过pynput.scroll()的操作系统单位限制。
    """
    def scroll_vertical(self, distance: int):
        """
        以像素为单位执行垂直滚动。

        Args:
            distance (int): 滚动的像素距离。
                           正数表示向上滚动（远离用户）。
                           负数表示向下滚动（朝向用户）。
        """
        if distance == 0:
            return
            
        # 准备输入事件结构体
        inp = INPUT_I()
        # MOUSEEVENTF_WHEEL 表示这是一个滚轮事件
        # mouseData 字段携带了滚动的距离信息
        inp.mi = MOUSEINPUT(0, 0, distance, MOUSEEVENTF_WHEEL, 0, None)
        
        # 将MOUSEINPUT封装在通用的INPUT结构体中
        command = INPUT(INPUT_MOUSE, inp)
        
        # 调用SendInput API发送事件
        # 第一个参数是要发送的事件数量
        # 第二个参数是指向事件数组的指针
        # 第三个参数是每个事件结构体的大小
        ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))