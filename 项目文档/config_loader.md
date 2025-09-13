# config_loader 模块介绍

## 概述

`config_loader.py` 模块负责从配置文件中加载和解析应用程序的所有配置信息，包括按键绑定、鼠标移动设置、滚动设置以及区域选择布局等。它确保应用程序能够根据用户的自定义设置正确运行。

## 核心组件

### `get_base_path()` 函数

- **功能**: 获取应用程序的根目录。该函数设计为在源代码运行和打包（frozen）状态下都能可靠地找到正确的路径。
- **返回值**: 应用程序根目录的绝对路径字符串。

### `AppConfig` 类

- **功能**: 应用程序配置的核心类，负责加载、存储和提供所有配置属性。
- **属性**: 包含从配置文件中解析出的各种配置项，例如：
    - `config_path`: 配置文件的完整路径。
    - `MOVE_*_VK`: 移动操作（上、下、左、右）对应的虚拟按键码。
    - `SCROLL_*_VK`: 滚动操作（上、下）对应的虚拟按键码。
    - `*_CLICK_VK`: 鼠标点击操作（左键、右键、中键、粘滞左键）对应的虚拟按键码。
    - `MOUSE_CONTROL_VKS`: 所有鼠标控制相关的虚拟按键码集合。
    - `HOTKEY_MODIFIER`, `HOTKEY_TRIGGER_KEY`, `HOTKEY_TRIGGER_VK`: 热键设置。
    - `MOVE_*_CHAR`: 移动操作对应的字符表示。
    - `EXIT_PROGRAM_PYNPUT`: 退出程序键对应的 `pynput` Key 对象。
    - `MOUSE_MOVE_SPEED`, `MOUSE_SPEED_SHIFT`, `MOUSE_SPEED_CAPLOCK`, `DELAY_PER_STEP`: 鼠标移动速度和延迟设置。
    - `RUN_AS_ADMIN`: 是否以管理员权限运行的布尔值。
    - `SCROLL_INITIAL_VELOCITY`, `SCROLL_MAX_VELOCITY`, `SCROLL_ACCELERATION`: 平滑滚动设置。
    - `REGION_SELECT_LAYOUT`: 区域选择的布局配置。

- **初始化方法 `__init__(self, config_file: str = 'config.ini')`**:
    - **参数**:
        - `config_file`: 配置文件的名称，默认为 `config.ini`。
    - **异常**: 
        - `FileNotFoundError`: 当配置文件未找到时抛出。
        - `KeyError`: 当配置文件中缺少必需的键时抛出。
        - `ValueError`: 当区域选择布局配置无效时抛出。

- **内部加载方法 (私有方法)**:
    - `_load_movement_keys()`: 加载移动相关的按键设置。
    - `_load_mouse_action_keys()`: 加载鼠标动作相关的按键设置。
    - `_load_hotkey_settings()`: 加载热键设置。
    - `_load_character_mappings()`: 加载字符映射设置，并初始化 `MOUSE_CONTROL_VKS`。
    - `_load_general_settings()`: 加载通用设置。
    - `_load_smooth_scrolling_settings()`: 加载平滑滚动设置。
    - `_load_region_select_layout()`: 加载区域选择布局配置，并进行有效性检查。

## 技术实现

`config_loader.py` 使用 Python 内置的 `configparser` 模块来解析 `.ini` 格式的配置文件。通过将配置项分类到不同的内部加载方法中，提高了代码的组织性和可读性。同时，对配置文件中可能出现的缺失键或无效值进行了异常处理，增强了程序的健壮性。`get_base_path` 函数的实现考虑了程序在不同部署环境下的路径兼容性，确保了配置文件的正确加载。