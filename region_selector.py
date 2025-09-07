# region_selector.py
import tkinter as tk
from pynput.mouse import Controller as MouseController
import sys


class RegionSelector:
    KEY_LAYOUT_5x5 = [
        ['q', 'w', 'e', 'r', 't'],
        ['a', 's', 'd', 'f', 'g'],
        ['z', 'x', 'c', 'v', 'b'],
        ['y', 'u', 'i', 'o', 'p'],
        ['h', 'j', 'k', 'l', ';']
    ]

    def __init__(self, root):
        self.root = root
        self.canvas = None
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.current_level = 0
        self.macro_bounds = None
        self.grid_rects = {}
        self.valid_keys = {key for row in self.KEY_LAYOUT_5x5 for key in row}
        self.mouse_controller = MouseController()
        self._setup_overlay_window()

    def _setup_overlay_window(self):
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.75)
        self.root.config(bg='black')
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.root.wm_attributes("-transparentcolor", 'black')
        self.root.focus_force()
        self.root.bind('<Key>', self._on_key_press)
        self.root.bind('<Escape>', lambda e: self.stop())
        self.root.bind('<Button-1>', lambda e: self.stop())

    def start(self):
        self.current_level = 1
        self._draw_grid((0, 0, self.screen_width, self.screen_height),
                       self.KEY_LAYOUT_5x5)
        self.root.deiconify()

    def _on_key_press(self, event):
        key = event.keysym.lower()
        if key == 'semicolon':
            key = ';'

        if key in self.valid_keys:
            if self.current_level == 1:
                self.macro_bounds = self.grid_rects[key]
                self.canvas.delete("all")
                self.current_level = 2
                self._draw_grid(self.macro_bounds, self.KEY_LAYOUT_5x5)
            elif self.current_level == 2:
                micro_bounds = self.grid_rects[key]
                target_x = micro_bounds[0] + (micro_bounds[2] -
                                            micro_bounds[0]) / 2
                target_y = micro_bounds[1] + (micro_bounds[3] -
                                            micro_bounds[1]) / 2
                self.mouse_controller.position = (target_x, target_y)
                self.stop()
        else:
            self.stop()
        return "break"

    def _draw_grid(self, bounds, layout):
        x1, y1, x2, y2 = bounds
        region_width = x2 - x1
        region_height = y2 - y1
        grid_size = len(layout)
        cell_width = region_width / grid_size
        cell_height = region_height / grid_size
        self.grid_rects.clear()
        font_size = max(8, int(cell_height * 0.6))
        cell_bg_color = "#333333"
        outline_color = "#FFD700"
        text_color = "black"
        grid_line_color = "#FFD700"

        for row_index, row in enumerate(layout):
            for col_index, key in enumerate(row):
                cell_x1 = x1 + col_index * cell_width
                cell_y1 = y1 + row_index * cell_height
                cell_x2 = cell_x1 + cell_width
                cell_y2 = cell_y1 + cell_height

                self.canvas.create_rectangle(
                    cell_x1,
                    cell_y1,
                    cell_x2,
                    cell_y2,
                    fill=cell_bg_color,
                    outline=grid_line_color,
                    width=1)

                center_x = cell_x1 + cell_width / 2
                center_y = cell_y1 + cell_height / 2
                text = key.upper()
                offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]

                for ox, oy in offsets:
                    self.canvas.create_text(
                        center_x + ox,
                        center_y + oy,
                        text=text,
                        font=("Consolas", font_size, "bold"),
                        fill=outline_color)

                self.canvas.create_text(
                    center_x,
                    center_y,
                    text=text,
                    font=("Consolas", font_size, "bold"),
                    fill=text_color)

                self.grid_rects[key] = (cell_x1, cell_y1, cell_x2, cell_y2)

    def stop(self):
        self.root.quit()


if __name__ == '__main__':
    try:
        main_root = tk.Tk()
        main_root.withdraw()
        selector = RegionSelector(main_root)
        selector.start()
        main_root.mainloop()
        sys.exit(0)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)
KJ