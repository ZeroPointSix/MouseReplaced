# tray_icon.py

import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys
import time
from gui import run_gui 

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
        self.is_exiting = False # 新增一个标志，防止重复退出

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
    def _shutdown_sequence(self):
        """
        这个私有方法包含了所有实际的关闭操作。
        它在一个独立的后台线程中运行，以避免阻塞主线程。
        """
        print("后台关闭序列已启动...")
        
        # 1. 停止 pystray 图标的事件循环
        if self.icon:
            self.icon.stop()
        
        # 2. 发送信号，让所有自定义的后台线程（如 movement_worker）停止
        self.stop_event.set()
        
        # 3. 请求 pynput 监听器停止
        self.listener.stop()
        
        # 4. (可选但推荐) 等待监听器线程真正结束
        if self.listener.is_alive():
            self.listener.join(timeout=1.0) # 添加超时以防万一
        print("所有线程已停止。")

        # 5. (关键) 强制终止整个进程，以100%避免PyInstaller的清理警告
        os._exit(0)

    def on_exit(self):
        """
        当用户点击“退出”或程序请求重启时，此方法被调用。
        它的唯一职责是启动一个后台线程来执行真正的关闭操作。
        """
        if not self.is_exiting:
            self.is_exiting = True
            print("收到退出请求，启动后台关闭线程...")
            # 创建并启动一个守护线程来处理关闭，然后立即返回
            shutdown_thread = threading.Thread(target=self._shutdown_sequence, daemon=True)
            shutdown_thread.start()

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