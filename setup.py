# setup.py

import sys
from cx_Freeze import setup, Executable

# --- 基础配置 ---
base_name = "KeyMouse"
base = "Win32GUI" if sys.platform == "win32" else None

# --- 依赖项和数据文件 ---
packages_to_include = [
    "pynput", 
    "tkinter", 
    "configparser", 
    "threading",
    "queue"
]
# region_selector.py 现在是打包目标，而不是数据文件
files_to_include = ["config.ini"] 

# --- 构建选项 ---
build_exe_options = {
    "packages": packages_to_include,
    "include_files": files_to_include,
    "optimize": 2,
}

# --- 定义要创建的可执行文件 ---
# --- 核心修复：定义两个 Executable 对象 ---
executables = [
    # 第一个：主程序
    Executable(
        "main.py",
        base=base,
        target_name=f"{base_name}.exe",
        # icon="path/to/your/icon.ico"
    ),
    # 第二个：区域选择器
    Executable(
        "region_selector.py",
        base=base, # 同样使用 Win32GUI 来隐藏控制台窗口
        target_name="RegionSelector.exe" # 给它一个唯一的名字
    )
]

# --- 执行 setup ---
setup(
    name=base_name,
    version="1.0",
    description="A tool to control the mouse with the keyboard.",
    options={"build_exe": build_exe_options},
    executables=executables, # 使用包含两个目标的列表
)