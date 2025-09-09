"""区域选择器模块

这个模块提供了一个基于tkinter的区域选择器界面,用于通过键盘选择屏幕上的特定区域。

典型用法:
    layout_data = load_layout()  # 加载布局配置
    coords_file = "coords.txt"   # 指定坐标输出文件
    selector = RegionSelector(layout_data, coords_file)
    selector.mainloop()
"""

import tkinter as tk
import sys
import json
import os
import traceback
from typing import Dict, Set, List

def log_to_file(message: str) -> None:
    """记录日志到文件。
    
    Args:
        message: 要记录的日志消息
    """
    try:
        log_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_file = os.path.join(log_dir, "region_selector_runtime.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{os.getpid()}] {message}\n")
    except Exception:
        pass

class RegionSelector(tk.Tk):
    """区域选择器的主窗口类。"""
    
    def __init__(self, layout_data: List[List[str]], coords_file_path: str) -> None:
        """初始化区域选择器。

        Args:
            layout_data: 网格布局数据,二维列表
            coords_file_path: 坐标输出文件路径
        """
        super().__init__()
        
        # 基础配置数据
        self.layout_data = layout_data
        self.coords_file_path = coords_file_path
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        # 状态变量
        self.current_level: int = 0
        self.macro_bounds = None
        self.grid_rects: Dict[str, tuple] = {}
        self.valid_keys: Set[str] = {key for row in self.layout_data for key in row}
        
        # 初始化界面
        self._setup_overlay_window()
        self.start()

    def _setup_overlay_window(self):
        self.withdraw()
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-alpha", 0.75)
        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.wm_attributes("-transparentcolor", 'black')
        self.bind('<Key>', self._on_key_press)
        self.bind('<Escape>', lambda e: self.stop())
        self.bind('<Button-1>', lambda e: self.stop())

    def start(self):
        self.current_level = 1
        self._draw_grid((0, 0, self.screen_width, self.screen_height), self.layout_data)
        self.deiconify()
        self.focus_force()
        self.after(100, self.focus_force)

    def _on_key_press(self, event):
        key = event.keysym.lower()
        if key == 'semicolon': key = ';'
        if key in self.valid_keys:
            if self.current_level == 1:
                self.macro_bounds = self.grid_rects[key]
                self.canvas.delete("all")
                self.current_level = 2
                self._draw_grid(self.macro_bounds, self.layout_data)
                self.focus_force()
            elif self.current_level == 2:
                micro_bounds = self.grid_rects[key]
                target_x = micro_bounds[0] + (micro_bounds[2] - micro_bounds[0]) / 2
                target_y = micro_bounds[1] + (micro_bounds[3] - micro_bounds[1]) / 2
                try:
                    with open(self.coords_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"{target_x},{target_y}")
                    log_to_file(f"坐标成功写入: {self.coords_file_path}")
                except Exception as e:
                    log_to_file(f"!!! 写入坐标文件失败: {e} !!!")
                self.stop()
        else:
            self.stop()
        return "break"

    def _draw_grid(self, bounds, layout):
        x1, y1, x2, y2 = bounds; region_width, region_height = x2 - x1, y2 - y1; grid_size_y = len(layout); grid_size_x = len(layout[0]); cell_width, cell_height = region_width / grid_size_x, region_height / grid_size_y; self.grid_rects.clear(); font_size = max(8, int(cell_height * 0.6)); cell_bg_color = "#333333"; outline_color = "#FFD700"; text_color = "black"; grid_line_color = "#FFD700"
        for row_index, row in enumerate(layout):
            for col_index, key in enumerate(row):
                cell_x1, cell_y1 = x1 + col_index * cell_width, y1 + row_index * cell_height; cell_x2, cell_y2 = cell_x1 + cell_width, cell_y1 + cell_height; self.canvas.create_rectangle(cell_x1, cell_y1, cell_x2, cell_y2, fill=cell_bg_color, outline=grid_line_color, width=1); center_x, center_y = cell_x1 + cell_width / 2, cell_y1 + cell_height / 2; text = key.upper(); offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
                for ox, oy in offsets: self.canvas.create_text(center_x + ox, center_y + oy, text=text, font=("Consolas", font_size, "bold"), fill=outline_color)
                self.canvas.create_text(center_x, center_y, text=text, font=("Consolas", font_size, "bold"), fill=text_color)
                self.grid_rects[key] = (cell_x1, cell_y1, cell_x2, cell_y2)

    def stop(self):
        self.destroy()

if __name__ == '__main__':
    try:
        log_to_file("\n--- region_selector.exe started ---")
        if len(sys.argv) < 3:
            log_to_file("!!! 致命错误: 未提供布局文件和坐标文件路径。")
            sys.exit(1)
        
        layout_file_path = sys.argv[1]
        coords_file_path = sys.argv[2]
        
        with open(layout_file_path, 'r', encoding='utf-8') as f:
            layout = json.load(f)
        
        app = RegionSelector(layout, coords_file_path)
        app.mainloop()
        
        log_to_file("Exiting cleanly.")
        sys.exit(0)
    except Exception as e:
        log_to_file(f"!!! 致命错误 !!!\nError: {e}\n{traceback.format_exc()}")
        sys.exit(1)