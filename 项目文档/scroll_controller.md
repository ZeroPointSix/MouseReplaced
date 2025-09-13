# scroll_controller 模块介绍

## 概述
`scroll_controller.py` 模块负责管理应用程序中的平滑滚动功能。它通过精确的物理模型计算滚动速度和距离，并处理多方向滚动意图的堆栈管理，确保用户在复杂操作下也能获得流畅、准确的滚动体验。该模块是实现鼠标模拟滚动功能的核心组成部分。

## 核心组件

### `ScrollController` 类
<mcsymbol name="ScrollController" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="7" type="class"></mcsymbol>
`ScrollController` 类是本模块的核心，用于管理平滑滚动的状态和物理计算。其主要职责包括：

- **初始化**: 接收配置对象和平台滚动器，设置初始状态变量。
- **状态管理**: 跟踪当前滚动方向和持续时间。
- **物理计算**: 根据配置参数和持续时间动态计算滚动速度和距离。
- **滚动执行**: 将计算出的滚动量传递给平台特定的滚动实现。

#### 属性
- `config`: 应用程序的配置对象，用于获取滚动参数（如初始速度、最大速度、加速度）。
- `platform_scroller`: 平台特定的滚动实现对象，负责实际执行滚动操作。
- `y_wheel_stack`: <mcsymbol name="y_wheel_stack" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="26" type="attribute"></mcsymbol> 使用 `collections.deque` 实现的双端队列，用于跟踪当前生效的滚动方向（'up' 或 'down'）。它允许正确处理用户同时按下向上和向下键的情况。
- `wheel_duration`: <mcsymbol name="wheel_duration" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="32" type="attribute"></mcsymbol> 浮点数，记录按住滚动键的持续时间（秒），用于动态调整滚动速度。
- `scroll_accumulator`: <mcsymbol name="scroll_accumulator" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="37" type="attribute"></mcsymbol> 浮点数，用于累积计算出的带有小数的滚动距离，防止因只能滚动整数像素而丢失精度。

#### 方法
- `is_wheeling()`: <mcsymbol name="is_wheeling" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="44" type="function"></mcsymbol> 检查当前是否处于任何滚动状态。
- `_calculate_velocity()`: <mcsymbol name="_calculate_velocity" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="52" type="function"></mcsymbol> 根据 `wheel_duration` 和配置参数（初始速度、最大速度、加速度）动态计算当前滚动速度。
- `update(delta)`: <mcsymbol name="update" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="70" type="function"></mcsymbol> 主更新方法，由外部高频循环调用。它累积滚动时间，计算当前帧的滚动距离，并调用平台滚动器执行实际滚动。
- `start_scroll_down()`: <mcsymbol name="start_scroll_down" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="109" type="function"></mcsymbol> 注册开始向下滚动的意图，将 'down' 推入 `y_wheel_stack`。
- `stop_scroll_down()`: <mcsymbol name="stop_scroll_down" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="115" type="function"></mcsymbol> 注册停止向下滚动的意图，从 `y_wheel_stack` 中移除 'down'。
- `start_scroll_up()`: <mcsymbol name="start_scroll_up" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="123" type="function"></mcsymbol> 注册开始向上滚动的意图，将 'up' 推入 `y_wheel_stack`。
- `stop_scroll_up()`: <mcsymbol name="stop_scroll_up" filename="scroll_controller.py" path="d:\MouseReplaced\KeyMouse\scroll_controller.py" startline="128" type="function"></mcsymbol> 注册停止向上滚动的意图，从 `y_wheel_stack` 中移除 'up'。

## 技术实现细节

### 平滑滚动物理模型
模块实现了基于时间累积的平滑滚动物理模型。滚动速度不是一个固定值，而是根据用户按住滚动键的持续时间动态变化的。通过 `_calculate_velocity` 方法，速度会从一个初始值开始，随着时间的推移加速，直至达到最大速度。这模拟了真实世界中物体加速运动的特性，提供了更自然的滚动手感。

### 滚动方向管理
`y_wheel_stack`（双端队列）的使用是处理滚动方向的关键。它允许系统正确处理用户同时按下“向上”和“向下”滚动键的情况。当一个方向的滚动键被按下时，对应的方向标志（'up' 或 'down'）被推入栈中；当键释放时，标志被弹出。`update` 方法总是根据栈顶的元素来确定当前的滚动方向，确保即使在快速切换方向时也能保持逻辑的正确性。

### 精度累积
由于屏幕滚动通常只能以整数像素为单位进行，而物理模型计算出的滚动距离可能是浮点数。`scroll_accumulator` 属性用于累积这些小数部分的距离。当累积的距离达到一个整数像素时，才执行实际的滚动操作，并从累加器中减去已滚动的整数部分，保留小数部分继续累积。这种机制有效地防止了因浮点数舍入而导致的精度损失，使得长时间的平滑滚动更加精确和流畅。

### 平台交互
`ScrollController` 模块通过依赖注入的方式与平台特定的滚动实现（`platform_scroller`）解耦。这意味着 `ScrollController` 专注于滚动逻辑的计算和管理，而具体的滚动操作（如模拟鼠标滚轮事件）则由 `platform_scroller` 负责。这种设计提高了模块的可移植性和可测试性，使得在不同操作系统或环境下替换滚动实现变得容易。