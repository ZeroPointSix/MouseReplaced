"""
    模式切换功能并不打算支持配置,所以所有与模式切换与其使用必须的热键功能统一使用硬编码
    模式介绍:
    alt+a: 鼠标控制模式
    alt+m: 指令模式
    待补充...... 
"""
import pynput
  

class ControlStateManager:
    """
        专门负责对于鼠标移动的当中状态进行管理
    """
    mouse_speed_caplock_active =False
    mouse_speed_shift_active =False
    is_left_mouse_button_held_by_keyboard = False
    is_right_mouse_button_held_by_keyboard = False
    is_middle_mouse_button_held_by_keyboard = False

class ModeSwitch:
    """
        热键管理应该是唯一的实例,负责所有与模式切换的功能
    """
    def __init__(self,config,tray_icon=None):
        """
        构造函数，用于初始化属性和设置监听器。
        """
        self.mouse_control_mode_active = False
        self.config = config
        self.tray_icon = tray_icon
        # 将 HotKey 的定义放在构造函数中
        # 此时 self 已经存在，可以安全地引用实例方法
        self.alt_a_hotkey = pynput.keyboard.HotKey(
            pynput.keyboard.HotKey.parse(config.TOGGLE_MODE_HOTKEY),
            self.on_alt_a_activated  # 传递的是方法本身，而不是调用它
        )     
    
    def on_alt_a_activated(self):
        """
        当 Alt + a 快捷键被激活时调用此函数。
        用于切换鼠标控制模式。
        """        
        self.mouse_control_mode_active = not self.mouse_control_mode_active # 切换模式
        if self.mouse_control_mode_active:
            print("模式切换：>>> 进入鼠标控制模式 <<<")
            # print("提示：W/A/S/D 控制鼠标移动，空格键点击，上下箭头控制滚轮。再次按 Alt+A 退出。")
        else:
            print("模式切换：>>> 退出鼠标控制模式，回到普通模式 <<<")
        self.alt_a_hotkey._state.clear()