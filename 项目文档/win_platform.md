# win_platform 模块介绍

## 概述

`win_platform.py` 模块主要负责封装与 Windows 平台相关的底层功能，目前的核心功能是提供精确的鼠标滚轮控制。它通过直接调用 Windows API 来实现像素级的滚动，从而克服了某些高级库（如 `pynput`）在滚动精度上的限制。

## 核心组件

### `WinPlatformScroller` 类

`WinPlatformScroller` 是一个封装了 Windows 平台底层滚动 API 的控制器类。它利用 `ctypes` 库与 Win32 `SendInput` 函数进行交互，以发送像素级的滚轮事件。

#### `scroll_vertical(self, distance: int)` 方法

- **功能**: 以像素为单位执行垂直滚动操作。
- **参数**: 
    - `distance` (int): 指定滚动的像素距离。
        - 正数表示向上滚动（远离用户）。
        - 负数表示向下滚动（朝向用户）。
- **实现细节**: 
    - 该方法通过构造 `MOUSEINPUT` 和 `INPUT` 结构体来准备滚轮事件。
    - `MOUSEEVENTF_WHEEL` 标志用于指示这是一个滚轮事件。
    - `mouseData` 字段承载了具体的滚动距离信息。
    - 最后，调用 `ctypes.windll.user32.SendInput` API 将事件发送到操作系统，实现精确的滚轮控制。

## 技术实现

该模块的关键在于使用了 Python 的 `ctypes` 库来与 Windows API 进行交互。通过定义与 Win32 API 结构体（如 `MOUSEINPUT`, `INPUT_I`, `INPUT`）相对应的 Python 类，可以直接调用底层的 `SendInput` 函数，这使得程序能够发送操作系统级别的输入事件，包括精确到像素的鼠标滚轮事件。这种方法绕过了高级输入库可能存在的抽象层，提供了更细粒度的控制。