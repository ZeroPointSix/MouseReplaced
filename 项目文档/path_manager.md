# path_manager 模块介绍

## 概述
`path_manager.py` 模块提供了一系列实用函数，用于在不同运行环境下（源代码、PyInstaller 打包、Nuitka 打包）准确获取应用程序的各种路径，包括根目录、主可执行文件路径、Python 解释器路径以及特定脚本的路径。这确保了程序在部署和开发阶段都能正确地定位资源。

## 核心组件

### 函数

#### `get_base_path()`
- **功能**：获取应用程序的根目录。该函数旨在提供一个在任何环境（源代码、PyInstaller、Nuitka）下都可靠的终极方法来确定程序的基准路径。
- **用途**：作为所有其他路径获取函数的基础，确保无论程序如何打包或运行，都能找到正确的相对路径。
- **实现细节**：通过 `sys.argv[0]` 获取启动程序的脚本或可执行文件的路径，并使用 `os.path.dirname(os.path.abspath())` 来解析其所在目录。

#### `get_main_executable_path()`
- **功能**：获取主程序可执行文件的路径。
- **用途**：在打包后的应用程序中，通常需要知道主可执行文件的确切位置。
- **实现细节**：通过检查 `sys.frozen` 属性判断是否为打包环境。如果是，则返回 `sys.executable`（指向主程序本身）；否则，返回 Python 解释器的路径。

#### `get_python_interpreter_path()`
- **功能**：获取用于运行子脚本的 Python 解释器路径。
- **用途**：当程序需要启动独立的 Python 脚本时，确保使用正确的解释器。
- **实现细节**：首先尝试在 `get_base_path()` 返回的目录下查找名为 `python.exe` 的文件（Nuitka 在 standalone 模式下会将解释器放在根目录）。如果找到，则使用该路径；否则，回退到 `sys.executable`（用于开发环境）。

#### `get_region_selector_script_path()`
- **功能**：获取 `region_selector.py` 脚本的完整路径。
- **用途**：方便程序定位并执行 `region_selector.py` 脚本。
- **实现细节**：结合 `get_base_path()` 和脚本文件名 `region_selector.py` 来构建完整的路径。

## 技术实现

`path_manager` 模块的核心技术实现在于其对不同 Python 运行环境的路径获取策略。它通过以下方式确保路径的准确性：

1.  **环境检测**：利用 `sys.frozen` 属性来判断程序是否在打包（如 PyInstaller 或 Nuitka）环境中运行，从而采取不同的路径获取逻辑。
2.  **鲁棒性路径解析**：使用 `os.path.abspath()` 和 `os.path.dirname()` 组合，确保获取到的路径是绝对路径且是文件所在的目录，避免了相对路径可能带来的问题。
3.  **Nuitka 兼容性**：特别考虑了 Nuitka 在 standalone 模式下将 `python.exe` 放置在应用程序根目录的情况，提高了在 Nuitka 打包环境下的兼容性。
4.  **统一接口**：提供了一组统一的函数接口，使得其他模块可以方便地获取所需的各种路径，而无需关心底层的环境差异。