import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys
from config_loader import resource_path
from gui import run_gui 

class TrayIcon:
    def __init__(self, mode_switch):
        self.mode_switch = mode_switch
        self.icon = None
        self.active_icon = self.create_icon(True)
        self.inactive_icon = self.create_icon(False)
        self.thread = None
        self.is_settings_window_open = False


    def create_icon(self, active):
        # 创建一个简单的图标
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # 绘制不同状态的图标
        if active:
            # 活动状态 - 绿色
            dc.rectangle(
                [(8, 8), (width-8, height-8)],
                fill=(0, 180, 0)
            )
            dc.ellipse(
                [(16, 16), (width-16, height-16)],
                fill=(0, 220, 0)
            )
        else:
            # 非活动状态 - 灰色
            dc.rectangle(
                [(8, 8), (width-8, height-8)],
                fill=(100, 100, 100)
            )
            dc.ellipse(
                [(16, 16), (width-16, height-16)],
                fill=(150, 150, 150)
            )
        
        return image
    
    def update_icon(self):
        """更新图标状态"""
        if self.icon:
            self.icon.icon = self.active_icon if self.mode_switch.mouse_control_mode_active else self.inactive_icon
            title = "KeyMouse - 鼠标控制模式已启用" if self.mode_switch.mouse_control_mode_active else "KeyMouse - 普通模式"
            self.icon.title = title
    
    def on_exit(self):
        """退出程序"""
        if self.icon:
            self.icon.stop()
        os._exit(0)
    
    def on_settings_window_closed(self):
        """当设置窗口关闭时调用的回调函数"""
        self.is_settings_window_open = False
        print("设置窗口已关闭。")
    
    def on_settings(self):
        """在单独的线程中打开设置窗口"""
        # 检查是否已有窗口打开
        if self.is_settings_window_open:
            print("设置窗口已打开，请勿重复点击。")
            return

        print("正在打开设置窗口...")
        self.is_settings_window_open = True
        
        # 创建并启动一个新线程来运行GUI
        # target=run_gui, args=(self.on_settings_window_closed,)
        # 将 on_settings_window_closed 方法作为回调传递给 run_gui
        settings_thread = threading.Thread(
            target=run_gui, 
            args=(self.on_settings_window_closed,), 
            daemon=True
        )
        settings_thread.start()
    
    def run(self):
        """在单独的线程中运行托盘图标"""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """托盘图标的主运行函数"""
        menu = pystray.Menu(
            pystray.MenuItem("设置", self.on_settings),
            pystray.MenuItem("退出", self.on_exit)
        )
        
        self.icon = pystray.Icon(
            "keymouse",
            self.inactive_icon,
            "KeyMouse",
            menu
        )
        
        # 设置图标更新回调
        def mode_changed():
            self.update_icon()
        
        # 替换模式切换函数
        original_mode_switch = self.mode_switch.on_alt_a_activated
        
        def new_mode_switch():
            original_mode_switch()
            self.update_icon()
        
        self.mode_switch.on_alt_a_activated = new_mode_switch
        
        # 运行图标
        self.icon.run()

# 在main.py中使用:
# from tray_icon import TrayIcon
# tray = TrayIcon(mouse_control.mode_switch)
# tray.run()