# tray_icon.py

import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys
import time
from gui import run_gui 
from modeswitch import AppMode # <--- 新增导入

class TrayIcon:
    def __init__(self, mode_switch, listener, stop_event):
        self.mode_switch = mode_switch
        self.listener = listener
        self.stop_event = stop_event
        self.icon = None
        self.active_icon = self.create_icon(True)
        self.inactive_icon = self.create_icon(False)
        self.thread = None
        self.is_settings_window_open = False
        self.is_exiting = False

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
        """根据当前的程序模式，更新托盘图标和标题。"""
        if self.icon:
            is_active = self.mode_switch.is_mouse_control_mode()
            self.icon.icon = self.active_icon if is_active else self.inactive_icon
            self.icon.title = f"KeyMouse - {self.mode_switch.current_mode.name} 模式"
    
    def on_exit(self):
        """执行异步的、健壮的退出序列。"""
        if not self.is_exiting:
            self.is_exiting = True
            print("收到退出请求，启动后台关闭线程...")
            shutdown_thread = threading.Thread(target=self._shutdown_sequence, daemon=True)
            shutdown_thread.start()

    def _shutdown_sequence(self):
        """在后台执行所有实际的关闭操作，以避免死锁。"""
        print("后台关闭序列已启动...")
        if self.icon:
            self.icon.stop()
        
        self.stop_event.set()
        self.listener.stop()
        
        if self.listener.is_alive():
            self.listener.join(timeout=1.0)
        print("所有线程已停止。")
        
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
        """在独立线程中运行pystray的事件循环。"""
        menu = pystray.Menu(
            pystray.MenuItem("设置", self.on_settings),
            pystray.MenuItem("退出", self.on_exit)
        )
        self.icon = pystray.Icon("keymouse", self.inactive_icon, "KeyMouse", menu)
        
        # --- 核心修正点：调用正确的新方法 ---
        # 1. 保存原始的模式切换方法
        original_toggle_method = self.mode_switch.toggle_mouse_control_mode
        
        # 2. 创建一个新的包装方法
        def new_toggle_with_icon_update():
            # 首先，调用原始的切换逻辑
            original_toggle_method()
            # 然后，更新我们的托盘图标
            self.update_icon()

        # 3. 用我们新的包装方法，替换掉原始的切换方法
        #    这样，每当主程序调用 toggle_mouse_control_mode 时，图标都会自动更新
        self.mode_switch.toggle_mouse_control_mode = new_toggle_with_icon_update
        
        # 首次运行时，也更新一次图标
        self.update_icon()
        
        self.icon.run()