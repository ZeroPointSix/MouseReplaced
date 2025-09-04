import pynput
import time
import threading
import win32con
import modeswitch
import config_loader
import sys
import argparse
from utool import KEY_TO_VK

class MouseActionManager:
    """作为MouseControl类当中的鼠标动作类,封装win32过滤器当中的移动动作"""
    def __init__(self, mouse_controller, mode_switch, mouse_state, config, active_direction_keys):
        self.mouse_controller = mouse_controller
        self.mouse_state = mouse_state
        self.config = config
        self.mode_switch = mode_switch
        self.active_direction_keys = active_direction_keys

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

    def mouse_movement_worker(self, stop_event):
        """在一个独立的线程中运行，持续检查按下的方向键并移动鼠标和滚动。"""
        while not stop_event.is_set():
            dx, dy, dz = 0, 0, 0
            
            cfg = self.config
            move_speed = cfg.MOUSE_MOVE_SPEED
            scroll_amount = cfg.MOUSE_SCROLL_AMOUNT
            shift_multiplier = cfg.MOUSE_SPEED_SHIFT
            caps_multiplier = cfg.MOUSE_SPEED_CAPLOCK
            delay = cfg.DELAY_PER_STEP            

            if self.mode_switch.mouse_control_mode_active:
                if cfg.MOVE_UP_CHAR in self.active_direction_keys: dy -= move_speed
                if cfg.MOVE_DOWN_CHAR in self.active_direction_keys: dy += move_speed
                if cfg.MOVE_LEFT_CHAR in self.active_direction_keys: dx -= move_speed
                if cfg.MOVE_RIGHT_CHAR in self.active_direction_keys: dx += move_speed
                if cfg.SCROLL_DOWN_CHAR in self.active_direction_keys: dz -= scroll_amount
                if cfg.SCROLL_UP_CHAR in self.active_direction_keys: dz += scroll_amount

                speed_multiplier = 1.0
                if self.mouse_state.mouse_speed_shift_active: speed_multiplier *= shift_multiplier
                if self.mouse_state.mouse_speed_caplock_active: speed_multiplier *= caps_multiplier
                
                dx, dy = int(dx * speed_multiplier), int(dy * speed_multiplier)
                dz *= speed_multiplier
                
                if dx != 0 or dy != 0: self.mouse_controller.move(dx, dy)
                if dz != 0: self.mouse_controller.scroll(0, dz)
            
            time.sleep(delay)

class MouseControl:
    """主控制类，负责整合所有模块"""
    def __init__(self, config, tray_icon=None):
        self.config = config
        self.mouse_controller = pynput.mouse.Controller()
        self.mode_switch = modeswitch.ModeSwitch(self.config, tray_icon)
        self.mouse_state = modeswitch.ControlStateManager()
        self.active_direction_keys = set()
        self.mouse_action = MouseActionManager(self.mouse_controller, self.mode_switch, self.mouse_state, self.config, self.active_direction_keys)
        
        # --- 手动热键状态 ---
        self.hotkey_modifiers = set()
        self.HOTKEY_TRIGGER_KEY = 'a'

    def on_press(self, key):
        """全局按键按下事件，主要用于监听热键修饰键"""
        # --- 手动热键逻辑 ---
        if key in (pynput.keyboard.Key.alt_l, pynput.keyboard.Key.alt_r):
            self.hotkey_modifiers.add('alt')
        
        try:
            key_char = key.char.lower()
            if key_char == self.HOTKEY_TRIGGER_KEY and 'alt' in self.hotkey_modifiers:
                self.mode_switch.on_alt_a_activated()
        except AttributeError:
            pass

        # --- 速度控制键 ---
        if self.mode_switch.mouse_control_mode_active:
            if key == pynput.keyboard.Key.shift_l: self.mouse_state.mouse_speed_shift_active = True
            elif key == pynput.keyboard.Key.caps_lock: self.mouse_state.mouse_speed_caplock_active = not self.mouse_state.mouse_speed_caplock_active
        
        # --- 退出键 ---
        if key == self.config.EXIT_PROGRAM_PYNPUT and self.mode_switch.mouse_control_mode_active:
            if self.mode_switch.tray_icon:
                self.mode_switch.tray_icon.on_exit()
            return False
    
    def on_release(self, key):
        """全局按键释放事件，用于更新热键修饰键状态"""
        # --- 手动热键逻辑 ---
        if key in (pynput.keyboard.Key.alt_l, pynput.keyboard.Key.alt_r):
            self.hotkey_modifiers.discard('alt')
        
        # --- 速度控制键 ---
        if key == pynput.keyboard.Key.shift_l:
            self.mouse_state.mouse_speed_shift_active = False
    
    def win32_event_filter(self, msg, data):
        """Win32底层事件过滤器，用于拦截和处理控制模式下的按键"""
        global keyboard_listener
        is_key_down = (msg == win32con.WM_KEYDOWN or msg == win32con.WM_SYSKEYDOWN)
         
        if data.vkCode in self.config.MOUSE_CONTROL_VKS and self.mode_switch.mouse_control_mode_active:
            vk = data.vkCode
            cfg = self.config
            
            if vk == cfg.LEFT_CLICK_VK: self.mouse_action.handle_left_button_event(is_key_down)
            elif vk == cfg.RIGHT_CLICK_VK: self.mouse_action.handle_right_button_event(is_key_down)
            elif vk == cfg.MIDDLE_CLICK_VK: self.mouse_action.handle_middle_button_event(is_key_down)
            elif vk == cfg.TOGGLE_MODE_INTERNAL_VK and is_key_down: self.mode_switch.on_alt_a_activated()
            
            elif vk in {cfg.MOVE_UP_VK, cfg.MOVE_DOWN_VK, cfg.MOVE_LEFT_VK, cfg.MOVE_RIGHT_VK, cfg.SCROLL_UP_VK, cfg.SCROLL_DOWN_VK}:
                key_map = {
                    cfg.MOVE_UP_VK: cfg.MOVE_UP_CHAR, cfg.MOVE_DOWN_VK: cfg.MOVE_DOWN_CHAR,
                    cfg.MOVE_LEFT_VK: cfg.MOVE_LEFT_CHAR, cfg.MOVE_RIGHT_VK: cfg.MOVE_RIGHT_CHAR,
                    cfg.SCROLL_UP_VK: cfg.SCROLL_UP_CHAR, cfg.SCROLL_DOWN_VK: cfg.SCROLL_DOWN_CHAR,
                }
                char_key = key_map.get(vk)
                if char_key:
                    if is_key_down: self.active_direction_keys.add(char_key)
                    else: self.active_direction_keys.discard(char_key)
            
            keyboard_listener.suppress_event()
        return True

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="KeyMouse - 键盘控制鼠标工具")
        parser.add_argument("--gui", "-g", action="store_true", help="启动GUI配置界面")
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
        
        # 创建停止信号和监听器
        stop_event = threading.Event()
        keyboard_listener = pynput.keyboard.Listener(
            on_press=mouse_control.on_press, 
            on_release=mouse_control.on_release, 
            win32_event_filter=mouse_control.win32_event_filter,
            suppress=False # 全局suppress关闭，由filter内部控制
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