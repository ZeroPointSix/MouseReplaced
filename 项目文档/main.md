# main 模块介绍

## 概述

`main.py` 模块是 KeyMouse 应用程序的核心程序，它实现了通过键盘控制鼠标的全部功能。该模块负责处理键盘事件、执行鼠标操作、管理模式切换，并与其他关键模块（如 `config_loader`、`modeswitch`、`scroll_controller`、`win_platform`、`gui` 和 `tray_icon`）进行集成。此外，它还处理管理员权限的检查与提升以及应用程序的日志记录。

## 核心组件

### `MouseActionManager` 类

*   **功能**: 负责管理所有与鼠标相关的操作，包括鼠标按键的按下/释放、粘滞点击以及滚动功能。
*   **关键方法**:
    *   `handle_left_button_event(is_key_down: bool)`: 处理鼠标左键的按下和释放事件。
    *   `handle_right_button_event(is_key_down: bool)`: 处理鼠标右键的按下和释放事件。
    *   `handle_middle_button_event(is_key_down: bool)`: 处理鼠标中键的按下和释放事件。
    *   `release_sticky_click()`: 释放粘滞点击状态。
    *   `start_scrolling_down()`: 开始向下持续滚动。
    *   `stop_scrolling_down()`: 停止向下持续滚动。
    *   `start_scrolling_up()`: 开始向上持续滚动。
    *   `stop_scrolling_up()`: 停止向上持续滚动。
    *   `process_action_queue()`: 处理动作队列中的命令，例如将鼠标移动到指定坐标。
    *   `mouse_movement_worker(stop_event: threading.Event)`: 一个工作线程，根据激活的方向键持续更新鼠标位置并处理滚动。

### `MouseControl` 类

*   **功能**: 管理整体鼠标控制功能，包括键盘事件处理、模式切换以及与 `MouseActionManager` 的交互。
*   **关键方法**:
    *   `on_press(key)`: 处理键盘按键按下事件，包括速度修饰键（Shift、CapsLock）和程序退出。
    *   `on_release(key)`: 处理键盘按键释放事件。
    *   `win32_event_filter(msg: int, data)`: 过滤 Windows 消息，检测模式切换和区域选择的热键，并分发鼠标控制按键事件。
    *   `_handle_region_select()`: 通过启动独立的 `RegionSelector.exe` 或 `region_selector.py` 进程来启动区域选择功能。
    *   `_handle_mouse_control_key(vk: int, is_key_down: bool)`: 根据虚拟键码分发鼠标控制操作（点击、粘滞点击、滚动、移动）。
    *   `wait_for_region_selector(layout_file: str, coords_file: str)`: 等待区域选择器进程完成并处理其输出（鼠标坐标）。

### `is_admin()` 函数

*   **功能**: 检查当前进程是否具有管理员权限。

### 主执行块 (`if __name__ == "__main__":`)

*   **功能**: 处理程序初始化、参数解析（用于 GUI 模式）、管理员权限提升、日志设置，并启动键盘监听和鼠标移动的主线程。
*   **主要功能点**:
    *   使用 `config_loader.AppConfig()` 加载配置。
    *   如果配置中启用了 `RUN_AS_ADMIN`，则检查并请求管理员权限。
    *   如果提供了 `--gui` 参数，则启动图形用户界面。
    *   初始化 `MouseControl`、`pynput.keyboard.Listener` 和 `TrayIcon`。
    *   启动 `keyboard_listener` 和 `mouse_movement_worker` 线程。
    *   管理程序生命周期，直到停止事件被触发。

## 技术实现细节

*   **键盘钩子**: 使用 `pynput.keyboard.Listener` 结合 `win32_event_filter` 在底层拦截键盘事件，实现全局热键和原始按键事件的抑制。
*   **鼠标控制**: 利用 `pynput.mouse.Controller` 实现程序化的鼠标移动和点击。
*   **模式切换**: 与 `modeswitch` 模块集成，管理不同的应用程序模式（例如，鼠标控制模式、区域选择模式）以及暂停/恢复键盘钩子。
*   **配置管理**: 依赖 `config_loader` 从 `config.ini` 文件加载应用程序设置，支持自定义按键绑定、速度和其他行为。
*   **区域选择**: 启动一个独立的进程（`RegionSelector.exe` 或 `region_selector.py`）进行可视化区域选择，并通过临时文件将选定的坐标传回主应用程序。
*   **平滑滚动**: 与 `ScrollController` 和 `WinPlatformScroller` 集成，实现像素级的平滑滚动。
*   **线程管理**: 使用 `threading` 将键盘监听和鼠标移动放在独立的守护线程中运行，确保程序的响应性。
*   **错误处理和日志记录**: 实现健壮的错误处理机制，使用 `try-except` 块捕获异常，并使用 `logging` 模块将程序事件和错误记录到文件和控制台。
*   **管理员权限**: 包含检查和请求管理员权限的逻辑，以支持需要这些权限的功能（例如，全局键盘钩子）。
*   **托盘图标**: 与 `tray_icon` 集成，提供系统托盘功能，为用户提供模式切换和程序退出的界面。