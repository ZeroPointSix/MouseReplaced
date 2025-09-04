# modeswitch.py

"""
    模式切换功能
"""
class ControlStateManager:
    """专门负责对于鼠标移动的当中状态进行管理"""
    mouse_speed_caplock_active = False
    mouse_speed_shift_active = False
    is_left_mouse_button_held_by_keyboard = False
    is_right_mouse_button_held_by_keyboard = False
    is_middle_mouse_button_held_by_keyboard = False

class ModeSwitch:
    """热键管理应该是唯一的实例,负责所有与模式切换的功能"""
    def __init__(self, config, tray_icon=None):
        """构造函数，用于初始化属性。"""
        self.mouse_control_mode_active = False
        self.config = config
        self.tray_icon = tray_icon
    
    def on_alt_a_activated(self):
        """当热键被激活时调用此函数，用于切换鼠标控制模式。"""
        self.mouse_control_mode_active = not self.mouse_control_mode_active
        if self.mouse_control_mode_active:
            print("模式切换：>>> 进入鼠标控制模式 <<<")
        else:
            print("模式切换：>>> 退出鼠标控制模式，回到普通模式 <<<")