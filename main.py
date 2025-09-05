# main.py

import pynput
import time
import threading
import win32con
import win32api  # <--- 确保导入
import modeswitch
import config_loader
import sys
import argparse
from utool import KEY_TO_VK
from scroll_controller import ScrollController
from win_platform import WinPlatformScroller
from gui import run_gui
from tray_icon import TrayIcon
import traceback


class MouseActionManager:
    # ... (此类无任何变化) ...
    def __init__(self, mouse_controller, mode_switch, mouse_state, config, 
                 active_direction_keys):
        self.mouse_controller = mouse_controller
        self.mouse_state = mouse_state
        self.config = config
        self.mode_switch = mode_switch
        self.active_direction_keys = active_direction_keys
        platform_scroller = WinPlatformScroller()
        self.scroll_controller = ScrollController(config, platform_scroller)

    def handle_left_button_event(self, is_key_down: bool):
        if is_key_down:
            if not self.mouse_state.is_left_mouse_button_held_by_keyboard:
                self.mouse_controller.press(pynput.mouse.Button.left)
                self.mouse_state.is_left_mouse_button_held_by_keyboard = True
        else:
            if self.mouse_state.is_left_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.left)
                self.mouse_state.is_left_mouse_button_held_by_keyboard = False

    def handle_right_button_event(self, is_key_down: bool):
        if is_key_down:
            if not self.mouse_state.is_right_mouse_button_held_by_keyboard:
                self.mouse_controller.press(pynput.mouse.Button.right)
                self.mouse_state.is_right_mouse_button_held_by_keyboard = True
        else:
            if self.mouse_state.is_right_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.right)
                self.mouse_state.is_right_mouse_button_held_by_keyboard = False

    def handle_middle_button_event(self, is_key_down: bool):
        if is_key_down:
            if not self.mouse_state.is_middle_mouse_button_held_by_keyboard:
                self.mouse_controller.press(pynput.mouse.Button.middle)
                self.mouse_state.is_middle_mouse_button_held_by_keyboard = True
        else:
            if self.mouse_state.is_middle_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.middle)
                self.mouse_state.is_middle_mouse_button_held_by_keyboard = False

    def release_sticky_click(self):
        if self.mouse_state.sticky_left_click_active:
            print("粘滞点击已通过按键释放。")
            if self.mouse_state.is_left_mouse_button_held_by_keyboard:
                self.mouse_controller.release(pynput.mouse.Button.left)
                self.mouse_state.is_left_mouse_button_held_by_keyboard = False
            self.mouse_state.sticky_left_click_active = False

    def start_scrolling_down(self):
        self.scroll_controller.start_scroll_down()

    def stop_scrolling_down(self):
        self.scroll_controller.stop_scroll_down()

    def start_scrolling_up(self):
        self.scroll_controller.start_scroll_up()

    def stop_scrolling_up(self):
        self.scroll_controller.stop_scroll_up()

    def mouse_movement_worker(self, stop_event):
        last_time = time.perf_counter()
        while not stop_event.is_set():
            current_time = time.perf_counter()
            delta = current_time - last_time
            last_time = current_time
            
            self.scroll_controller.update(delta)
            dx, dy = 0, 0
            cfg = self.config
            move_speed = cfg.MOUSE_MOVE_SPEED

            if self.mode_switch.mouse_control_mode_active:
                if (self.mouse_state.sticky_left_click_active and 
                    not self.mouse_state.is_left_mouse_button_held_by_keyboard):
                    self.mouse_controller.press(pynput.mouse.Button.left)
                    self.mouse_state.is_left_mouse_button_held_by_keyboard = True
                    print("粘滞点击已激活并按下左键。")

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
    def __init__(self, config, tray_icon=None):
        self.config = config
        self.mouse_controller = pynput.mouse.Controller()
        self.mode_switch = modeswitch.ModeSwitch(self.config, tray_icon)
        self.mouse_state = modeswitch.ControlStateManager()
        self.active_direction_keys = set()
        self.mouse_action = MouseActionManager(
            self.mouse_controller,
            self.mode_switch,
            self.mouse_state,
            self.config,
            self.active_direction_keys
        )

    def on_press(self, key):
        """高层按键事件，只处理与底层过滤器无关的速度状态"""
        if self.mode_switch.mouse_control_mode_active:
            if key == pynput.keyboard.Key.shift_l:
                self.mouse_state.mouse_speed_shift_active = True
            elif key == pynput.keyboard.Key.caps_lock:
                self.mouse_state.mouse_speed_caplock_active = not self.mouse_state.mouse_speed_caplock_active

        if key == self.config.EXIT_PROGRAM_PYNPUT and self.mode_switch.mouse_control_mode_active:
            if self.mode_switch.tray_icon:
                self.mode_switch.tray_icon.on_exit()
            return False

    def on_release(self, key):
        """高层按键事件，只处理与底层过滤器无关的速度状态"""
        if key == pynput.keyboard.Key.shift_l:
            self.mouse_state.mouse_speed_shift_active = False

    def win32_event_filter(self, msg, data):
        """
        终极版事件过滤器：
        1. 正确、稳定地处理 Alt+A 模式切换。
        2. 正确、符合预期地处理"粘滞点击"功能。
        """
        global keyboard_listener
        is_key_down = (msg == win32con.WM_KEYDOWN or msg == win32con.WM_SYSKEYDOWN)
        vk = data.vkCode
        cfg = self.config

        # --- 1. 模式切换热键检测 (最高优先级) ---
        if is_key_down and vk == cfg.HOTKEY_TRIGGER_VK:
            # 检查 Alt 键的状态
            if win32api.GetKeyState(win32con.VK_MENU) < 0:
                self.mode_switch.on_alt_a_activated()
                keyboard_listener.suppress_event()
                return True

        # --- 2. 后续所有逻辑，只在鼠标控制模式激活时执行 ---
        if not self.mode_switch.mouse_control_mode_active:
            return True

        # --- 3. 粘滞点击的取消逻辑 ---
        if is_key_down and self.mouse_state.sticky_left_click_active:
            exempt_keys = {
                cfg.MOVE_UP_VK,
                cfg.MOVE_DOWN_VK,
                cfg.MOVE_LEFT_VK,
                cfg.MOVE_RIGHT_VK,
                cfg.STICKY_LEFT_CLICK_VK,
                cfg.SCROLL_DOWN_VK,
                cfg.SCROLL_UP_VK
            }
            if vk not in exempt_keys:
                self.mouse_action.release_sticky_click()

        # --- 4. 核心功能键处理 ---
        if vk in cfg.MOUSE_CONTROL_VKS:
            if vk == cfg.LEFT_CLICK_VK:
                self.mouse_action.handle_left_button_event(is_key_down)
            elif vk == cfg.RIGHT_CLICK_VK:
                self.mouse_action.handle_right_button_event(is_key_down)
            elif vk == cfg.MIDDLE_CLICK_VK:
                self.mouse_action.handle_middle_button_event(is_key_down)
            elif vk == cfg.TOGGLE_MODE_INTERNAL_VK and is_key_down:
                self.mode_switch.on_alt_a_activated()
            elif vk == cfg.STICKY_LEFT_CLICK_VK and is_key_down:
                self.mouse_state.sticky_left_click_active = not self.mouse_state.sticky_left_click_active
                print(f"粘滞点击模式切换为: {self.mouse_state.sticky_left_click_active}")
                if not self.mouse_state.sticky_left_click_active:
                    self.mouse_action.release_sticky_click()
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
                    cfg.MOVE_RIGHT_VK: cfg.MOVE_RIGHT_CHAR,
                }
                char_key = key_map.get(vk)
                if char_key:
                    if is_key_down:
                        self.active_direction_keys.add(char_key)
                    else:
                        self.active_direction_keys.discard(char_key)

            keyboard_listener.suppress_event()

        return True


if __name__ == "__main__":
    # ... (main 部分无变化) ...
    try:
        parser = argparse.ArgumentParser(description="KeyMouse")
        parser.add_argument("--gui", "-g", action="store_true",
                          help="启动GUI配置界面")
        args = parser.parse_args()

        if args.gui:
            try:
                from gui import run_gui
                print("正在以GUI模式启动...")
                run_gui()
                sys.exit(0)
            except ImportError as e:
                print(f"无法启动GUI: {e}")
                sys.exit(1)

        print("--------------------------------------------------")
        print("             KeyMouse")
        print("--------------------------------------------------")
        config = config_loader.AppConfig()
        print("配置已成功加载。")

        mouse_control = MouseControl(config)
        stop_event = threading.Event()
        keyboard_listener = pynput.keyboard.Listener(
            on_press=mouse_control.on_press,
            on_release=mouse_control.on_release,
            win32_event_filter=mouse_control.win32_event_filter,
            suppress=False
        )

        tray = None
        try:
            from tray_icon import TrayIcon
            tray = TrayIcon(mouse_control.mode_switch, keyboard_listener, stop_event)
        except ImportError as e:
            print(f"无法加载托盘图标: {e}")

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
        keyboard_listener.join()

        print("程序已安全退出。")
    except Exception as e:
        print("\n[致命错误] 程序意外终止。")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键退出...")
