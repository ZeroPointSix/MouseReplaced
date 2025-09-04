# tray_icon.py

import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys
from gui import run_gui 

class TrayIcon:
    # __init__ 保持不变，接收所有需要的参数
    def __init__(self, mode_switch, listener, stop_event):
        self.mode_switch = mode_switch
        self.listener = listener
        self.stop_event = stop_event
        self.icon = None
        self.active_icon = self.create_icon(True)
        self.inactive_icon = self.create_icon(False)
        self.thread = None
        self.is_settings_window_open = False

    def create_icon(self, active):
        width, height = 64, 64
        image = Image.new('RGB', (width, height), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        if active:
            dc.rectangle([(8, 8), (width-8, height-8)], fill=(0, 180, 0))
            dc.ellipse([(16, 16), (width-16, height-16)], fill=(0, 220, 0))
        else:
            dc.rectangle([(8, 8), (width-8, height-8)], fill=(100, 100, 100))
            dc.ellipse([(16, 16), (width-16, height-16)], fill=(150, 150, 150))
        return image
    
    def update_icon(self):
        if self.icon:
            self.icon.icon = self.active_icon if self.mode_switch.mouse_control_mode_active else self.inactive_icon
            self.icon.title = "KeyMouse - 鼠标控制模式已启用" if self.mode_switch.mouse_control_mode_active else "KeyMouse - 普通模式"
    
    # ====================================================================
    # ====================  最终版退出逻辑 ========================
    # ====================================================================
    def on_exit(self):
        """
        执行最终版的强制退出逻辑。
        这将跳过PyInstaller的清理检查，从而100%避免警告弹窗。
        """
        print("正在执行强制退出...")
        
        # 隐藏并停止托盘图标，提供即时反馈
        if self.icon:
            self.icon.visible = False
            self.icon.stop()
        
        # 立即终止整个进程
        os._exit(0)
    
    def on_settings_window_closed(self):
        self.is_settings_window_open = False
        print("设置窗口已关闭。")
    
    def on_settings(self):
        if self.is_settings_window_open:
            print("设置窗口已打开，请勿重复点击。")
            return
        
        print("正在打开设置窗口...")
        self.is_settings_window_open = True
        
        settings_thread = threading.Thread(
            target=run_gui, 
            args=(self.on_settings_window_closed, self),
            daemon=True
        )
        settings_thread.start()
    
    def run(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        menu = pystray.Menu(
            pystray.MenuItem("设置", self.on_settings),
            pystray.MenuItem("退出", self.on_exit)
        )
        self.icon = pystray.Icon("keymouse", self.inactive_icon, "KeyMouse", menu)
        
        original_mode_switch = self.mode_switch.on_alt_a_activated
        def new_mode_switch():
            original_mode_switch()
            self.update_icon()
        self.mode_switch.on_alt_a_activated = new_mode_switch
        
        self.icon.run()