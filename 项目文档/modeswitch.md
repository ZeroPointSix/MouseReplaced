# modeswitch 模块介绍

## 概述

`modeswitch.py` 模块负责管理应用程序的不同操作模式，包括普通模式、鼠标控制模式和区域选择模式。它还提供了对键盘钩子的控制功能，确保在不同模式下键盘事件的正确处理。

## 核心组件

### `AppMode` 枚举类

- **功能**: 定义了应用程序的三种主要操作模式。
- **成员**:
    - `NORMAL`: 普通模式，应用程序处于非活动状态。
    - `MOUSE_CONTROL`: 鼠标控制模式，键盘输入被用于控制鼠标移动和点击。
    - `REGION_SELECT`: 区域选择模式，用于选择屏幕上的特定区域。

### `ControlStateManager` 类

- **功能**: 管理与鼠标控制相关的各种状态标志。
- **属性**:
    - `mouse_speed_caplock_active`: Caps Lock 键是否激活鼠标加速。
    - `mouse_speed_shift_active`: Shift 键是否激活鼠标加速。
    - `is_left_mouse_button_held_by_keyboard`: 左键是否被键盘按住。
    - `is_right_mouse_button_held_by_keyboard`: 右键是否被键盘按住。
    - `is_middle_mouse_button_held_by_keyboard`: 中键是否被键盘按住。
    - `sticky_left_click_active`: 粘滞左键点击是否激活。

### `ModeSwitch` 类

- **功能**: 负责应用程序模式的切换和管理，以及键盘钩子的暂停与恢复。
- **初始化方法 `__init__(self, config: dict, tray_icon: Optional[object] = None)`**:
    - **参数**:
        - `config`: 应用程序的配置字典。
        - `tray_icon`: 托盘图标对象，用于更新图标以反映当前模式。
    - **属性**:
        - `current_mode`: 当前的应用程序模式。
        - `previous_mode_before_region_select`: 进入区域选择模式之前的模式，用于返回。
        - `keyboard_hook_active`: 控制 `pynput` 键盘钩子是否激活的状态。

- **方法**:
    - `is_mouse_control_mode(self) -> bool`: 检查当前是否处于鼠标控制模式。
    - `is_region_select_mode(self) -> bool`: 检查当前是否处于区域选择模式。
    - `toggle_mouse_control_mode(self) -> None`: 在普通模式和鼠标控制模式之间切换。
    - `set_mode(self, new_mode: AppMode) -> None`: 设置应用程序的当前模式，并更新托盘图标（如果存在）。
    - `return_from_region_select(self) -> None`: 从区域选择模式返回到之前的模式。
    - `pause_keyboard_hook(self) -> None`: 暂停键盘钩子，允许事件传递给其他窗口。
    - `resume_keyboard_hook(self) -> None`: 恢复键盘钩子。

## 技术实现

该模块通过枚举类 `AppMode` 清晰地定义了应用程序的运行状态。`ModeSwitch` 类作为核心控制器，维护了当前模式和键盘钩子的状态，并通过 `set_mode` 方法实现了模式间的平滑切换。`pause_keyboard_hook` 和 `resume_keyboard_hook` 方法的引入，解决了 `pynput` 钩子可能阻塞其他 GUI 框架事件的问题，增强了程序的兼容性和用户体验。