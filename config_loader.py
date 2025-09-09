"""配置加载模块。

该模块负责从配置文件中加载和解析应用程序的配置信息。
包括按键绑定、鼠标移动设置、滚动设置等。
"""

import configparser
import os
import sys
from typing import List, Set

from utool import KEY_TO_VK, NAME_TO_PYNPUT_KEY


def get_base_path() -> str:
    """
    获取应用程序的根目录。
    这是在任何环境（源代码、打包后）下都绝对可靠的终极方法。
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包状态 (frozen), 根目录就是可执行文件所在的目录
        return os.path.dirname(sys.executable)
    else:
        # 如果是源代码状态, 根目录就是主脚本 (__file__) 所在的目录
        return os.path.dirname(os.path.abspath(__file__))


class AppConfig:
    """应用程序配置类。

    负责加载和存储所有应用程序配置，包括按键绑定、鼠标设置等。

    属性:
        config_path: 配置文件的完整路径
        MOVE_*_VK: 移动相关的虚拟按键码
        SCROLL_*_VK: 滚动相关的虚拟按键码
        *_CLICK_VK: 点击相关的虚拟按键码
        MOUSE_CONTROL_VKS: 所有鼠标控制相关的虚拟按键码集合
        其他各种配置属性
    """

    def __init__(self, config_file: str = 'config.ini') -> None:
        """初始化配置对象。

        Args:
            config_file: 配置文件名，默认为'config.ini'

        Raises:
            FileNotFoundError: 配置文件不存在时抛出
            KeyError: 必需的配置键缺失时抛出
            ValueError: 区域选择布局配置无效时抛出
        """
        base_path = get_base_path()
        self.config_path = os.path.join(base_path, config_file)
        
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件 '{config_file}' 在路径 '{self.config_path}' 未找到！")
        config.read(self.config_path, encoding='utf-8')

        def get_key(section: configparser.SectionProxy, option: str) -> str:
            """获取配置项的值，如果不存在则抛出异常。"""
            value = section.get(option)
            if value is None:
                raise KeyError(f"在配置文件的 [{section.name}] 节中，未找到必需的键 '{option}'！")
            return value

        # 加载按键绑定配置
        keybindings = config['Keybindings']
        self._load_movement_keys(keybindings, get_key)
        self._load_mouse_action_keys(keybindings, get_key)
        self._load_hotkey_settings(keybindings, get_key)
        self._load_character_mappings(keybindings, get_key)
        
        # 加载通用设置
        self._load_general_settings(config['Settings'])
        
        # 加载平滑滚动设置
        self._load_smooth_scrolling_settings(config['SmoothScrolling'])
        
        # 加载区域选择布局
        self.REGION_SELECT_LAYOUT = self._load_region_select_layout(config)

    def _load_movement_keys(self, keybindings: configparser.SectionProxy, get_key: callable) -> None:
        """加载移动相关的按键设置。"""
        self.MOVE_UP_VK = KEY_TO_VK[get_key(keybindings, 'move_up')]
        self.MOVE_DOWN_VK = KEY_TO_VK[get_key(keybindings, 'move_down')]
        self.MOVE_LEFT_VK = KEY_TO_VK[get_key(keybindings, 'move_left')]
        self.MOVE_RIGHT_VK = KEY_TO_VK[get_key(keybindings, 'move_right')]
        self.SCROLL_UP_VK = KEY_TO_VK[get_key(keybindings, 'scroll_up')]
        self.SCROLL_DOWN_VK = KEY_TO_VK[get_key(keybindings, 'scroll_down')]

    def _load_mouse_action_keys(self, keybindings: configparser.SectionProxy, get_key: callable) -> None:
        """加载鼠标动作相关的按键设置。"""
        self.LEFT_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'left_click')]
        self.RIGHT_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'right_click')]
        self.MIDDLE_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'middle_click')]
        self.STICKY_LEFT_CLICK_VK = KEY_TO_VK[get_key(keybindings, 'sticky_left_click')]
        self.TOGGLE_MODE_INTERNAL_VK = KEY_TO_VK[get_key(keybindings, 'toggle_mode_internal')]
        self.ENTER_REGION_SELECT_VK = KEY_TO_VK[get_key(keybindings, 'enter_region_select_mode')]

    def _load_hotkey_settings(self, keybindings: configparser.SectionProxy, get_key: callable) -> None:
        """加载热键设置。"""
        hotkey_str = get_key(keybindings, 'toggle_mode_hotkey')
        parts = hotkey_str.replace('<', '').replace('>', '').lower().split('+')
        self.HOTKEY_MODIFIER = parts[0]
        self.HOTKEY_TRIGGER_KEY = parts[1]
        self.HOTKEY_TRIGGER_VK = KEY_TO_VK[self.HOTKEY_TRIGGER_KEY]

    def _load_character_mappings(self, keybindings: configparser.SectionProxy, get_key: callable) -> None:
        """加载字符映射设置。"""
        self.MOVE_UP_CHAR = get_key(keybindings, 'move_up')
        self.MOVE_DOWN_CHAR = get_key(keybindings, 'move_down')
        self.MOVE_LEFT_CHAR = get_key(keybindings, 'move_left')
        self.MOVE_RIGHT_CHAR = get_key(keybindings, 'move_right')
        exit_key_name = get_key(keybindings, 'exit_program')
        self.EXIT_PROGRAM_PYNPUT = NAME_TO_PYNPUT_KEY[exit_key_name]

        # 初始化鼠标控制虚拟按键集合
        self.MOUSE_CONTROL_VKS: Set[int] = {
            self.MOVE_UP_VK, self.MOVE_DOWN_VK, self.MOVE_LEFT_VK, self.MOVE_RIGHT_VK,
            self.SCROLL_DOWN_VK, self.SCROLL_UP_VK, self.LEFT_CLICK_VK,
            self.RIGHT_CLICK_VK, self.MIDDLE_CLICK_VK, self.TOGGLE_MODE_INTERNAL_VK,
            self.STICKY_LEFT_CLICK_VK
        }

    def _load_general_settings(self, settings: configparser.SectionProxy) -> None:
        """加载通用设置。"""
        self.MOUSE_MOVE_SPEED = settings.getint('mouse_move_speed')
        self.MOUSE_SPEED_SHIFT = settings.getfloat('mouse_speed_shift_multiplier')
        self.MOUSE_SPEED_CAPLOCK = settings.getfloat('mouse_speed_capslock_multiplier')
        self.DELAY_PER_STEP = settings.getfloat('delay_per_step')
        self.RUN_AS_ADMIN = settings.getboolean('run_as_admin', False)

    def _load_smooth_scrolling_settings(self, scrolling_settings: configparser.SectionProxy) -> None:
        """加载平滑滚动设置。"""
        self.SCROLL_INITIAL_VELOCITY = scrolling_settings.getfloat('initial_velocity')
        self.SCROLL_MAX_VELOCITY = scrolling_settings.getfloat('max_velocity')
        self.SCROLL_ACCELERATION = scrolling_settings.getfloat('acceleration')

    def _load_region_select_layout(self, config: configparser.ConfigParser) -> List[List[str]]:
        """加载区域选择布局配置。

        Args:
            config: 配置解析器对象

        Returns:
            包含区域选择布局的二维列表

        Raises:
            ValueError: 布局配置无效时抛出
        """
        if 'RegionSelectLayout' not in config:
            return [['1','2','3','4','5'],['q','w','e','r','t'],['a','s','d','f','g'],['z','x','c','v','b']]
        
        layout = []
        for i in range(1, 10):
            key = f'row{i}'
            if config.has_option('RegionSelectLayout', key):
                layout.append(config.get('RegionSelectLayout', key).split())
            else:
                break
                
        if not layout:
            raise ValueError("配置文件 [RegionSelectLayout] 区域为空!")
            
        first_row_len = len(layout[0])
        if not all(len(row) == first_row_len for row in layout):
            raise ValueError("配置文件 [RegionSelectLayout] 中所有行的键位数必须相同！")
            
        return layout