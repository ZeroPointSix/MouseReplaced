"""
    该文件是分离保存主程序的的工具
"""
import win32con
from pynput.keyboard import Key
        
# 映射人类可读的键名到Windows虚拟键码(vkCode)
KEY_TO_VK = {
    # 字母
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
    'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
    'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
    's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
    'y': 0x59, 'z': 0x5A,

    # 数字
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,

    # 特殊字符
    'semicolon': 0xBA,          # ; (VK_OEM_1)
    'apostrophe': 0xDE,         # ' (VK_OEM_7)
    'comma': 0xBC,              # , (VK_OEM_COMMA)
    'period': 0xBE,             # . (VK_OEM_PERIOD)
    'slash': 0xBF,              # / (VK_OEM_2)
    'backspace': 0x08,          # (VK_BACK)
    'space': 0x20,              # (VK_SPACE)
    'enter': 0x0D,              # (VK_RETURN)

    # 功能键
    'esc': win32con.VK_ESCAPE,
    'f1': win32con.VK_F1, 'f2': win32con.VK_F2, 'f3': win32con.VK_F3,
    'f4': win32con.VK_F4, 'f5': win32con.VK_F5, 'f6': win32con.VK_F6,
    'f7': win32con.VK_F7, 'f8': win32con.VK_F8, 'f9': win32con.VK_F9,
    'f10': win32con.VK_F10, 'f11': win32con.VK_F11, 'f12': win32con.VK_F12,

    # 控制键
    'shift': win32con.VK_SHIFT,
    'lshift': win32con.VK_LSHIFT,
    'rshift': win32con.VK_RSHIFT,
    'shift_r': win32con.VK_RSHIFT,
    'ctrl': win32con.VK_CONTROL,
    'lctrl': win32con.VK_LCONTROL,
    'rctrl': win32con.VK_RCONTROL,
    'alt': win32con.VK_MENU, # Alt key
    'lalt': win32con.VK_LMENU,
    'ralt': win32con.VK_RMENU,
}

# 映射键名到pynput的Key对象，用于on_press/on_release监听器
NAME_TO_PYNPUT_KEY = {
    'esc': Key.esc,
    'shift_l': Key.shift_l,
    'caps_lock': Key.caps_lock,
    'alt': Key.alt,
}

        

