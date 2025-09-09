"""KeyMouse主程序

这个模块实现了键盘控制鼠标的核心功能。

典型用法:
    python main.py [--gui]

属性:
    region_selector_process: 区域选择器子进程
    keyboard_listener: 键盘监听器实例
"""

import pynput
import time
import threading
import win32con
import win32api
import modeswitch
import config_loader
import os
import sys
import argparse
import traceback
import ctypes
import subprocess
import logging
import json
import tempfile
import queue
from typing import Optional, Set, Dict, Tuple

from utool import KEY_TO_VK
from scroll_controller import ScrollController
from win_platform import WinPlatformScroller
from gui import run_gui
from tray_icon import TrayIcon
from modeswitch import AppMode

try:
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'main.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, 'w', 'utf-8'),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    print(f"初始化日志失败: {e}")

def is_admin() -> bool:
    """检查当前进程是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

region_selector_process: Optional[subprocess.Popen] = None

class MouseActionManager:
    """鼠标动作管理器,处理所有鼠标相关操作"""
    
    def __init__(self, mouse_controller, mode_switch, mouse_state, config, active_direction_keys, action_queue):
        self.mouse_controller = mouse_controller
        self.mouse_state = mouse_state
        self.config = config
        self.mode_switch = mode_switch
        self.active_direction_keys = active_direction_keys
        self.action_queue = action_queue
        platform_scroller = WinPlatformScroller()
        self.scroll_controller = ScrollController(config, platform_scroller)

    def handle_left_button_event(self, is_key_down: bool) -> None:
        """处理左键按下/释放事件"""
        if is_key_down:
            if not self.mouse_state.is_left_mouse_button_held_by_keyboard:
                self.mouse_controller.press(pynput.mouse.Button.left)
                self.mouse_state.is_left_mouse_button_held_by_keyboard = True
        else:
            if self.mouse_state.is_left_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.left)
                self.mouse_state.is_left_mouse_button_held_by_keyboard = False

    def handle_right_button_event(self, is_key_down: bool) -> None:
        """处理右键按下/释放事件"""
        if is_key_down:
            if not self.mouse_state.is_right_mouse_button_held_by_keyboard:
                self.mouse_controller.press(pynput.mouse.Button.right)
                self.mouse_state.is_right_mouse_button_held_by_keyboard = True
        else:
            if self.mouse_state.is_right_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.right)
                self.mouse_state.is_right_mouse_button_held_by_keyboard = False

    def handle_middle_button_event(self, is_key_down: bool) -> None:
        """处理中键按下/释放事件"""
        if is_key_down:
            if not self.mouse_state.is_middle_mouse_button_held_by_keyboard:
                self.mouse_controller.press(pynput.mouse.Button.middle)
                self.mouse_state.is_middle_mouse_button_held_by_keyboard = True
        else:
            if self.mouse_state.is_middle_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.middle)
                self.mouse_state.is_middle_mouse_button_held_by_keyboard = False

    def release_sticky_click(self) -> None:
        """释放粘滞点击状态"""
        if self.mouse_state.sticky_left_click_active:
            if self.mouse_state.is_left_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.left)
                self.mouse_state.is_left_mouse_button_held_by_keyboard = False
            self.mouse_state.sticky_left_click_active = False

    def start_scrolling_down(self) -> None:
        """开始向下滚动"""
        self.scroll_controller.start_scroll_down()

    def stop_scrolling_down(self) -> None:
        """停止向下滚动"""
        self.scroll_controller.stop_scroll_down()

    def start_scrolling_up(self) -> None:
        """开始向上滚动"""
        self.scroll_controller.start_scroll_up()

    def stop_scrolling_up(self) -> None:
        """停止向上滚动"""
        self.scroll_controller.stop_scroll_up()

    def process_action_queue(self) -> None:
        """处理动作队列中的命令"""
        try:
            while not self.action_queue.empty():
                action, data = self.action_queue.get_nowait()
                if action == 'move_mouse_to':
                    self.mouse_controller.position = data
        except queue.Empty:
            pass

    def mouse_movement_worker(self, stop_event: threading.Event) -> None:
        """鼠标移动工作线程"""
        last_time = time.perf_counter()
        
        while not stop_event.is_set():
            self.process_action_queue()
            
            current_time = time.perf_counter()
            delta = current_time - last_time
            last_time = current_time
            
            self.scroll_controller.update(delta)
            dx, dy = 0, 0
            cfg = self.config
            move_speed = cfg.MOUSE_MOVE_SPEED
            
            if self.mode_switch.is_mouse_control_mode():
                if (self.mouse_state.sticky_left_click_active and 
                    not self.mouse_state.is_left_mouse_button_held_by_keyboard):
                    self.mouse_controller.press(pynput.mouse.Button.left)
                    self.mouse_state.is_left_mouse_button_held_by_keyboard = True
                
                if cfg.MOVE_UP_CHAR in self.active_direction_keys:
                    dy -= move_speed
                if cfg.MOVE_DOWN_CHAR in self.active_direction_keys:
                    dy += move_speed
                if cfg.MOVE_LEFT_CHAR in self.active_direction_keys:
                    dx -= move_speed
                if cfg.MOVE_RIGHT_CHAR in self.active_direction_keys:
                    dx += move_speed
                    
                speed_multiplier = 1.0
                if self.mouse_state.mouse_speed_shift_active:
                    speed_multiplier *= cfg.MOUSE_SPEED_SHIFT
                if self.mouse_state.mouse_speed_caplock_active:
                    speed_multiplier *= cfg.MOUSE_SPEED_CAPLOCK
                    
                dx, dy = int(dx * speed_multiplier), int(dy * speed_multiplier)
                if dx != 0 or dy != 0:
                    self.mouse_controller.move(dx, dy)
                    
            time.sleep(cfg.DELAY_PER_STEP)

class MouseControl:
    """鼠标控制类,管理所有鼠标相关功能"""
    
    def __init__(self, config, tray_icon=None):
        self.config = config
        self.mouse_controller = pynput.mouse.Controller()
        self.mode_switch = modeswitch.ModeSwitch(self.config, tray_icon)
        self.mouse_state = modeswitch.ControlStateManager()
        self.active_direction_keys: Set[str] = set()
        self.action_queue: queue.Queue = queue.Queue()
        self.mouse_action = MouseActionManager(
            self.mouse_controller,
            self.mode_switch,
            self.mouse_state,
            self.config,
            self.active_direction_keys,
            self.action_queue
        )

    def on_press(self, key) -> Optional[bool]:
        """处理键盘按下事件"""
        if self.mode_switch.is_mouse_control_mode():
            if key == pynput.keyboard.Key.shift_l:
                self.mouse_state.mouse_speed_shift_active = True
            elif key == pynput.keyboard.Key.caps_lock:
                self.mouse_state.mouse_speed_caplock_active = not self.mouse_state.mouse_speed_caplock_active
                
        if key == self.config.EXIT_PROGRAM_PYNPUT and self.mode_switch.is_mouse_control_mode():
            if self.mode_switch.tray_icon:
                self.mode_switch.tray_icon.on_exit()
            return False
            
    def on_release(self, key) -> None:
        """处理键盘释放事件"""
        if key == pynput.keyboard.Key.shift_l:
            self.mouse_state.mouse_speed_shift_active = False

    def win32_event_filter(self, msg: int, data) -> bool:
        """Windows消息过滤器"""
        global keyboard_listener, region_selector_process
        
        if not self.mode_switch.keyboard_hook_active:
            return True
            
        is_key_down = (msg == win32con.WM_KEYDOWN or msg == win32con.WM_SYSKEYDOWN)
        vk = data.vkCode
        cfg = self.config
        
        if is_key_down:
            if (vk == cfg.HOTKEY_TRIGGER_VK and 
                win32api.GetKeyState(win32con.VK_MENU) < 0):
                self.mode_switch.toggle_mouse_control_mode()
                keyboard_listener.suppress_event()
                return
                
            elif (vk == cfg.ENTER_REGION_SELECT_VK and 
                  self.mode_switch.is_mouse_control_mode()):
                self._handle_region_select()
                keyboard_listener.suppress_event()
                return

        if self.mode_switch.is_mouse_control_mode() and vk in cfg.MOUSE_CONTROL_VKS:
            self._handle_mouse_control_key(vk, is_key_down)
            keyboard_listener.suppress_event()
            
        return True

    def _handle_region_select(self) -> None:
        """处理区域选择功能"""
        global region_selector_process
        
        self.mode_switch.pause_keyboard_hook()
        try:
            if region_selector_process and region_selector_process.poll() is None:
                region_selector_process.terminate()
            self.mode_switch.set_mode(AppMode.REGION_SELECT)
            
            pid = os.getpid()
            temp_dir = tempfile.gettempdir()
            layout_file = os.path.join(temp_dir, f"keymouse_layout_{pid}.tmp")
            coords_file = os.path.join(temp_dir, f"keymouse_coords_{pid}.tmp")

            with open(layout_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.REGION_SELECT_LAYOUT, f)

            base_path = config_loader.get_base_path()
            command = []
            if getattr(sys, 'frozen', False):
                command = [os.path.join(base_path, "RegionSelector.exe"), 
                          layout_file, coords_file]
            else:
                command = [sys.executable, 
                          os.path.join(base_path, "region_selector.py"),
                          layout_file, coords_file]

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            region_selector_process = subprocess.Popen(command, 
                                                     startupinfo=startupinfo)
            
            threading.Thread(target=self.wait_for_region_selector,
                           args=(layout_file, coords_file),
                           daemon=True).start()
                           
        except Exception as e:
            logging.error(f"启动区域选择器时发生致命错误: {e}", exc_info=True)
            self.mode_switch.return_from_region_select()
            self.mode_switch.resume_keyboard_hook()

    def _handle_mouse_control_key(self, vk: int, is_key_down: bool) -> None:
        """处理鼠标控制按键"""
        cfg = self.config
        
        if vk == cfg.TOGGLE_MODE_INTERNAL_VK and is_key_down:
            self.mode_switch.toggle_mouse_control_mode()
        elif vk == cfg.STICKY_LEFT_CLICK_VK and is_key_down:
            self.mouse_state.sticky_left_click_active = not self.mouse_state.sticky_left_click_active
            if not self.mouse_state.sticky_left_click_active:
                self.mouse_action.release_sticky_click()
        elif vk == cfg.LEFT_CLICK_VK:
            self.mouse_action.handle_left_button_event(is_key_down)
        elif vk == cfg.RIGHT_CLICK_VK:
            self.mouse_action.handle_right_button_event(is_key_down)
        elif vk == cfg.MIDDLE_CLICK_VK:
            self.mouse_action.handle_middle_button_event(is_key_down)
        elif vk == cfg.SCROLL_DOWN_VK:
            if is_key_down:
                self.mouse_action.start_scrolling_down()
            else:
                self.mouse_action.stop_scrolling_down()
        elif vk == cfg.SCROLL_UP_VK:
            if is_key_down:
                self.mouse_action.start_scrolling_up()
            else:
                self.mouse_action.stop_scrolling_up()
        elif vk in {cfg.MOVE_UP_VK, cfg.MOVE_DOWN_VK,
                   cfg.MOVE_LEFT_VK, cfg.MOVE_RIGHT_VK}:
            key_map = {
                cfg.MOVE_UP_VK: cfg.MOVE_UP_CHAR,
                cfg.MOVE_DOWN_VK: cfg.MOVE_DOWN_CHAR,
                cfg.MOVE_LEFT_VK: cfg.MOVE_LEFT_CHAR,
                cfg.MOVE_RIGHT_VK: cfg.MOVE_RIGHT_CHAR
            }
            char_key = key_map.get(vk)
            if char_key:
                if is_key_down:
                    self.active_direction_keys.add(char_key)
                else:
                    self.active_direction_keys.discard(char_key)

    def wait_for_region_selector(self, layout_file: str, coords_file: str) -> None:
        """等待区域选择器进程完成"""
        global region_selector_process
        if not region_selector_process:
            return
            
        try:
            region_selector_process.wait()
            if os.path.exists(coords_file):
                with open(coords_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    try:
                        x_str, y_str = content.split(',')
                        target_x, target_y = float(x_str), float(y_str)
                        self.action_queue.put(('move_mouse_to', 
                                             (target_x, target_y)))
                    except Exception as e:
                        logging.error(f"解析坐标文件内容失败: {e}")
        except Exception as e:
            logging.error(f"等待区域选择器时发生错误: {e}", exc_info=True)
        finally:
            for f in [layout_file, coords_file]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        logging.error(f"删除临时文件 {f} 失败: {e}")
            self.mode_switch.return_from_region_select()
            self.mode_switch.resume_keyboard_hook()
            region_selector_process = None

# if __name__ == "__main__": 部分完全不变
if __name__ == "__main__":
    try:
        if '--restarted-as-admin' not in sys.argv:
            try:
                config = config_loader.AppConfig()
            except Exception as e:
                ctypes.windll.user32.MessageBoxW(None,
                    f"无法加载 'config.ini'。\n错误: {e}",
                    "KeyMouse 致命错误", 0x10)
                sys.exit(1)
                
            if config.RUN_AS_ADMIN and not is_admin():
                executable = sys.executable
                params = []
                if not getattr(sys, 'frozen', False):
                    params.append(f'"{sys.argv[0]}"')
                params.extend([f'"{arg}"' for arg in sys.argv[1:]])
                params.append('--restarted-as-admin')
                params_str = " ".join(params)
                
                try:
                    rtn = ctypes.windll.shell32.ShellExecuteW(None, "runas",
                        executable, params_str, None, 1)
                    if rtn <= 32:
                        ctypes.windll.user32.MessageBoxW(None,
                            f"请求管理员权限失败。\n错误代码: {rtn}",
                            "KeyMouse 错误", 0x10)
                    sys.exit(0)
                except Exception as e:
                    ctypes.windll.user32.MessageBoxW(None,
                        f"尝试以管理员身份重启时发生意外错误。\n错误: {e}",
                        "KeyMouse 错误", 0x10)
                    sys.exit(1)
                    
        parser = argparse.ArgumentParser(description="KeyMouse")
        parser.add_argument("--gui", "-g", action="store_true")
        parser.add_argument('--restarted-as-admin', action='store_true',
                          help=argparse.SUPPRESS)
        args = parser.parse_args()
        
        if args.gui:
            try:
                run_gui()
                sys.exit(0)
            except Exception as e:
                logging.error(f"无法启动GUI: {e}", exc_info=True)
                sys.exit(1)
                
        config = config_loader.AppConfig()
        log_file_path = os.path.join(config_loader.get_base_path(), 'main.log')
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [%(levelname)s] - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, 'w', 'utf-8'),
                logging.StreamHandler()
            ]
        )
        
        if is_admin():
            logging.info("程序已在 [管理员权限] 下运行。")
            
        mouse_control = MouseControl(config)
        stop_event = threading.Event()
        keyboard_listener = pynput.keyboard.Listener(
            on_press=mouse_control.on_press,
            on_release=mouse_control.on_release,
            win32_event_filter=mouse_control.win32_event_filter
        )
        
        tray = None
        try:
            tray = TrayIcon(mouse_control.mode_switch,
                           keyboard_listener, stop_event)
        except Exception as e:
            logging.error(f"无法加载托盘图标: {e}", exc_info=True)
            
        if tray:
            mouse_control.mode_switch.tray_icon = tray
            tray.run()
            
        movement_thread = threading.Thread(
            target=mouse_control.mouse_action.mouse_movement_worker,
            args=(stop_event,),
            daemon=True
        )
        
        keyboard_listener.start()
        movement_thread.start()
        
        logging.info("KeyMouse 主程序已启动。")
        
        while not stop_event.is_set():
            time.sleep(1)
            
        logging.info("收到停止事件，程序已安全退出。")
        
    except Exception as e:
        logging.error(f"程序遇到致命错误: {e}", exc_info=True)
        ctypes.windll.user32.MessageBoxW(None,
            f"程序遇到致命错误。\n请查看 main.log。\n\n错误: {e}",
            "KeyMouse 致命错误", 0x10)
        traceback.print_exc()