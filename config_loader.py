# config_loader.py

import configparser
from utool import KEY_TO_VK, NAME_TO_PYNPUT_KEY
import sys
import os

def get_base_path():
    if getattr(sys, 'frozen', False): return os.path.dirname(sys.executable)
    else: return os.path.dirname(os.path.abspath(__file__))

class AppConfig:
    def __init__(self, config_file='config.ini'):
        base_path = get_base_path()
        self.config_path = os.path.join(base_path, config_file)
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件 '{config_file}' 未找到！")
        config.read(self.config_path, encoding='utf-8')

        # --- 使用一个辅助函数来安全地加载键位 ---
        def get_key(section, option):
            value = section.get(option)
            if value is None:
                raise KeyError(f"在配置文件的 [{section.name}] 节中，未找到必需的键 '{option}'！")
            return value

        keybindings = config['Keybindings']
        self.MOVE_UP_VK = KEY_TO_VK[get_key(keybindings, 'move_up')]
        self.MOVE_DOWN_VK = KEY_TO_VK[get_key(keybindings, 'move_down')]
        self.MOVE_LEFT_VK = KEY_TO_VK[get_key(keybindings, 'move_left')]
        self.MOVE_RIGHT_VK = KEY_TO_VK[get_key(keybindings, 'move_right')]
        self.SCROLL_DOWN_VK = KEY_TO_VK[get_key(keybindings, 'scroll_down')]
        self.SCROLL_UP_VK = KEY_TO_VK[get_key(keybindings, 'scroll_up')]
        self.LEFT_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'left_click')]
        self.RIGHT_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'right_click')]
        self.MIDDLE_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'middle_click')]
        self.STICKY_LEFT_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'sticky_left_click')]
        self.TOGGLE_MODE_INTERNAL_VK = KEY_TO_VK[get_key(keybindings, 'toggle_mode_internal')]
        
        hotkey_str = get_key(keybindings, 'toggle_mode_hotkey')
        parts = hotkey_str.replace('<', '').replace('>', '').lower().split('+')
        self.HOTKEY_MODIFIER = parts[0]
        self.HOTKEY_TRIGGER_KEY = parts[1]
        self.HOTKEY_TRIGGER_VK = KEY_TO_VK[self.HOTKEY_TRIGGER_KEY]
        
        self.ENTER_REGION_SELECT_VK = KEY_TO_VK[get_key(keybindings, 'enter_region_select_mode')]

        self.MOVE_UP_CHAR = get_key(keybindings, 'move_up')
        self.MOVE_DOWN_CHAR = get_key(keybindings, 'move_down')
        self.MOVE_LEFT_CHAR = get_key(keybindings, 'move_left')
        self.MOVE_RIGHT_CHAR = get_key(keybindings, 'move_right')
        
        exit_key_name = get_key(keybindings, 'exit_program')
        self.EXIT_PROGRAM_PYNPUT = NAME_TO_PYNPUT_KEY[exit_key_name]
        
        self.MOUSE_CONTROL_VKS = {
            self.MOVE_UP_VK, self.MOVE_DOWN_VK, self.MOVE_LEFT_VK, self.MOVE_RIGHT_VK,
            self.SCROLL_DOWN_VK, self.SCROLL_UP_VK, self.LEFT_CLICK_VK,
            self.RIGHT_CLICK_VK, self.MIDDLE_CLICK_VK, self.TOGGLE_MODE_INTERNAL_VK,
            self.STICKY_LEFT_CLICK_VK
        }
        
        settings = config['Settings']
        self.MOUSE_MOVE_SPEED = settings.getint('mouse_move_speed')
        self.MOUSE_SPEED_SHIFT = settings.getfloat('mouse_speed_shift_multiplier')
        self.MOUSE_SPEED_CAPLOCK = settings.getfloat('mouse_speed_capslock_multiplier')
        self.DELAY_PER_STEP = settings.getfloat('delay_per_step')
        self.RUN_AS_ADMIN = settings.getboolean('run_as_admin', False)

        scrolling_settings = config['SmoothScrolling']
        self.SCROLL_INITIAL_VELOCITY = scrolling_settings.getfloat('initial_velocity')
        self.SCROLL_MAX_VELOCITY = scrolling_settings.getfloat('max_velocity')
        self.SCROLL_ACCELERATION = scrolling_settings.getfloat('acceleration')