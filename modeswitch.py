"""模式切换模块

该模块负责管理应用程序的不同操作模式，包括普通模式、鼠标控制模式和区域选择模式。
同时提供了键盘钩子的控制功能。
"""

from enum import Enum, auto
from typing import Optional


class AppMode(Enum):
    """应用程序模式枚举类"""
    NORMAL = auto()
    MOUSE_CONTROL = auto()
    REGION_SELECT = auto()


class ControlStateManager:
    """控制状态管理类"""
    def __init__(self):
        self.mouse_speed_caplock_active: bool = False
        self.mouse_speed_shift_active: bool = False
        self.is_left_mouse_button_held_by_keyboard: bool = False
        self.is_right_mouse_button_held_by_keyboard: bool = False
        self.is_middle_mouse_button_held_by_keyboard: bool = False
        self.sticky_left_click_active: bool = False


class ModeSwitch:
    """模式切换管理类"""
    def __init__(self, config: dict, tray_icon: Optional[object] = None) -> None:
        """初始化模式切换管理器

        Args:
            config: 配置字典
            tray_icon: 托盘图标对象
        """
        self.config = config
        self.tray_icon = tray_icon
        self.current_mode: AppMode = AppMode.NORMAL
        self.previous_mode_before_region_select: AppMode = AppMode.NORMAL
        # --- 核心修复：新增一个状态，用于控制 pynput 钩子是否激活 ---
        self.keyboard_hook_active: bool = True

    def is_mouse_control_mode(self) -> bool:
        """检查是否处于鼠标控制模式"""
        return self.current_mode == AppMode.MOUSE_CONTROL

    def is_region_select_mode(self) -> bool:
        """检查是否处于区域选择模式"""
        return self.current_mode == AppMode.REGION_SELECT

    def toggle_mouse_control_mode(self) -> None:
        """切换鼠标控制模式"""
        if self.current_mode == AppMode.NORMAL:
            self.set_mode(AppMode.MOUSE_CONTROL)
        elif self.current_mode == AppMode.MOUSE_CONTROL:
            self.set_mode(AppMode.NORMAL)

    def set_mode(self, new_mode: AppMode) -> None:
        """设置应用程序模式

        Args:
            new_mode: 新的应用程序模式
        """
        if self.current_mode == new_mode:
            return

        if new_mode == AppMode.REGION_SELECT:
            self.previous_mode_before_region_select = self.current_mode

        self.current_mode = new_mode
        print(f"模式切换：>>> 进入 {self.current_mode.name} 模式 <<<")

        if hasattr(self.tray_icon, 'update_icon'):
            self.tray_icon.update_icon()

    def return_from_region_select(self) -> None:
        """从区域选择模式返回到之前的模式"""
        self.set_mode(self.previous_mode_before_region_select)

    # --- 核心修复：新增两个方法来控制钩子状态 ---
    def pause_keyboard_hook(self) -> None:
        """暂停键盘钩子，让事件可以传递给其他窗口（如tkinter）"""
        print("主程序键盘钩子已暂停。")
        self.keyboard_hook_active = False

    def resume_keyboard_hook(self) -> None:
        """恢复键盘钩子"""
        print("主程序键盘钩子已恢复。")
        self.keyboard_hook_active = True