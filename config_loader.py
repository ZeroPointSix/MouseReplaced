import configparser
from utool import KEY_TO_VK,NAME_TO_PYNPUT_KEY
import sys
import os

def resource_path(relative_path):
    """ 获取资源的绝对路径, 兼容开发模式和 PyInstaller 打包后的模式 """
    try:
        # PyInstaller 创建一个临时文件夹 _MEIPASS 并把资源放在那里
        base_path = sys._MEIPASS
    except Exception:
        # 在开发模式下, base_path 就是当前文件所在的目录
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class AppConfig:
    """
    加载并持有从config.ini中读取的应用程序配置。
    """
    def __init__(self, config_file='config.ini'):
        config = configparser.ConfigParser()
        config_path = resource_path(config_file)
        config.read(config_path,encoding='utf-8')

        # 从配置文件加载键位设置
        keybindings = config['Keybindings']

        # --- 加载虚拟键码 (for win32_event_filter) ---
        self.MOVE_UP_VK = KEY_TO_VK[keybindings.get('move_up')]
        self.MOVE_DOWN_VK = KEY_TO_VK[keybindings.get('move_down')]
        self.MOVE_LEFT_VK = KEY_TO_VK[keybindings.get('move_left')]
        self.MOVE_RIGHT_VK = KEY_TO_VK[keybindings.get('move_right')]
        self.SCROLL_DOWN_VK = KEY_TO_VK[keybindings.get('scroll_down')]
        self.SCROLL_UP_VK = KEY_TO_VK[keybindings.get('scroll_up')]
        
        self.LEFT_CLICK_VK = KEY_TO_VK[keybindings.get('left_click')]
        self.RIGHT_CLICK_VK = KEY_TO_VK[keybindings.get('right_click')]
        self.MIDDLE_CLICK_VK = KEY_TO_VK[keybindings.get('middle_click')]

        self.TOGGLE_MODE_INTERNAL_VK = KEY_TO_VK[keybindings.get('toggle_mode_internal')]

        # --- 加载字符映射 (for active_direction_keys) ---
        self.MOVE_UP_CHAR = keybindings.get('move_up')
        self.MOVE_DOWN_CHAR = keybindings.get('move_down')
        self.MOVE_LEFT_CHAR = keybindings.get('move_left')
        self.MOVE_RIGHT_CHAR = keybindings.get('move_right')
        self.SCROLL_DOWN_CHAR = keybindings.get('scroll_down')
        self.SCROLL_UP_CHAR = keybindings.get('scroll_up')

        # --- 加载pynput特定键 (for on_press) ---
        exit_key_name = keybindings.get('exit_program')
        self.EXIT_PROGRAM_PYNPUT = NAME_TO_PYNPUT_KEY[exit_key_name]
        
        # --- 加载热键字符串 (for pynput.HotKey) ---
        self.TOGGLE_MODE_HOTKEY = keybindings.get('toggle_mode_hotkey')
        
        # 动态生成所有受控制的虚拟键码集合
        self.MOUSE_CONTROL_VKS = {
            self.MOVE_UP_VK, self.MOVE_DOWN_VK, self.MOVE_LEFT_VK, self.MOVE_RIGHT_VK,
            self.SCROLL_DOWN_VK, self.SCROLL_UP_VK, self.LEFT_CLICK_VK,
            self.RIGHT_CLICK_VK, self.MIDDLE_CLICK_VK, self.TOGGLE_MODE_INTERNAL_VK
        }
        
        
        
        # --- 2. 加载 [Settings] 节 ---
        settings = config['Settings']
        
        # 使用 getint 和 getfloat 来自动转换数据类型
        self.MOUSE_MOVE_SPEED = settings.getint('mouse_move_speed')
        self.MOUSE_SPEED_SHIFT = settings.getfloat('mouse_speed_shift_multiplier')
        self.MOUSE_SPEED_CAPLOCK = settings.getfloat('mouse_speed_capslock_multiplier')
        self.MOUSE_SCROLL_AMOUNT = settings.getint('mouse_scroll_amount')
        self.DELAY_PER_STEP = settings.getfloat('delay_per_step')