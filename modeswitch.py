# modeswitch.py

from enum import Enum, auto

class AppMode(Enum):
    NORMAL = auto()
    MOUSE_CONTROL = auto()
    REGION_SELECT = auto()

class ControlStateManager:
    mouse_speed_caplock_active = False
    mouse_speed_shift_active = False
    is_left_mouse_button_held_by_keyboard = False
    is_right_mouse_button_held_by_keyboard = False
    is_middle_mouse_button_held_by_keyboard = False
    sticky_left_click_active = False

class ModeSwitch:
    """热键管理和主模式状态机"""
    def __init__(self, config, tray_icon=None):
        self.config = config
        self.tray_icon = tray_icon
        self.current_mode = AppMode.NORMAL
        self.previous_mode_before_region_select = AppMode.NORMAL
        
    def is_mouse_control_mode(self):
        return self.current_mode == AppMode.MOUSE_CONTROL
        
    def is_region_select_mode(self):
        return self.current_mode == AppMode.REGION_SELECT

    def toggle_mouse_control_mode(self):
        if self.current_mode == AppMode.NORMAL:
            self.set_mode(AppMode.MOUSE_CONTROL)
        elif self.current_mode == AppMode.MOUSE_CONTROL:
            self.set_mode(AppMode.NORMAL)
            
    def set_mode(self, new_mode: AppMode):
        if self.current_mode == new_mode:
            return
        if new_mode == AppMode.REGION_SELECT:
            self.previous_mode_before_region_select = self.current_mode
        self.current_mode = new_mode
        print(f"模式切换：>>> 进入 {self.current_mode.name} 模式 <<<")
        if hasattr(self.tray_icon, 'update_icon'):
            self.tray_icon.update_icon()

    def return_from_region_select(self):
        print(f"从区域选择返回，恢复到 {self.previous_mode_before_region_select.name} 模式。")
        self.set_mode(self.previous_mode_before_region_select)