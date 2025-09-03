import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
from config_loader import AppConfig, resource_path
from utool import KEY_TO_VK, NAME_TO_PYNPUT_KEY

class ScrollableFrame(ttk.Frame):
    """一个可以垂直滚动的、健壮的ttk.Frame容器"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content_frame = ttk.Frame(self.canvas)

        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # <<< 核心修正点：用新的递归绑定方法替换bind_all >>>
        self._bind_mouse_wheel_to_children(self)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_mouse_wheel(self, event):
        """处理鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # <<< 核心修正点：添加这个全新的“递归绑定”辅助方法 >>>
    def _bind_mouse_wheel_to_children(self, widget):
        """递归地将鼠标滚轮事件绑定到widget及其所有子widget上"""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_mouse_wheel_to_children(child)

class KeyMouseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KeyMouse 设置")
        self.root.geometry("600x500")
        self.root.minsize(450, 400)
        self.root.resizable(True, True)
        
        # 加载当前配置
        self.config_file = 'config.ini'
        self.config = AppConfig(self.config_file)
        self.config_parser = configparser.ConfigParser()
        self.config_parser.read(resource_path(self.config_file), encoding='utf-8')
        
        # 创建主框架
        self.main_frame = ttk.Notebook(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页
        self.keybindings_frame = ttk.Frame(self.main_frame)
        self.settings_frame = ttk.Frame(self.main_frame)
        
        self.main_frame.add(self.keybindings_frame, text="键位设置")
        self.main_frame.add(self.settings_frame, text="通用设置")
        
        # 键位录制变量
        self.recording_key = None
        self.recording_entry = None
        self.original_key_value = ""
        self.key_vars = {}
        
        # 创建键位设置界面
        self.create_keybindings_ui()
        
        # 创建通用设置界面
        self.create_settings_ui()
        
        # 底部按钮
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(self.button_frame, text="保存设置", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.button_frame, text="保存为默认", command=self.save_current_as_default).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.button_frame, text="恢复默认", command=self.reset_defaults).pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def get_factory_defaults(self):
        """返回硬编码的出厂默认配置，独立于任何配置文件"""
        key_defaults = {
            'move_up': 'i',
            'move_down': 'k',
            'move_left': 'j',
            'move_right': 'l',
            'scroll_up': 'comma',
            'scroll_down': 'm',
            'left_click': 'semicolon',
            'right_click': 'apostrophe',
            'middle_click': 'rshift',
            'toggle_mode_hotkey': '<alt>+a',
            'toggle_mode_internal': 'q',
            'exit_program': 'esc'
        }
        setting_defaults = {
            'mouse_move_speed': 20,
            'mouse_speed_shift_multiplier': 0.5,
            'mouse_speed_capslock_multiplier': 0.2,
            'mouse_scroll_amount': 2,
            'delay_per_step': 0.01
        }
        return key_defaults, setting_defaults
    
    def create_keybindings_ui(self):
        # 创建一个可滚动的框架，并让它填满整个"键位设置"标签页
        scrollable_container = ScrollableFrame(self.keybindings_frame)
        scrollable_container.pack(fill=tk.BOTH, expand=True)
        
        # 获取可滚动框架内部的那个"内容框架"
        keybindings_container = scrollable_container.content_frame
         
        # 鼠标移动控制
        move_frame = ttk.LabelFrame(keybindings_container, text="鼠标移动控制")
        move_frame.pack(fill=tk.X, pady=5, padx=10) # 建议加上padx让左右也有边距
        
        
        # 创建网格布局
        self.create_key_setting(move_frame, "向上移动", "move_up", 0)
        self.create_key_setting(move_frame, "向下移动", "move_down", 1)
        self.create_key_setting(move_frame, "向左移动", "move_left", 2)
        self.create_key_setting(move_frame, "向右移动", "move_right", 3)
        self.create_key_setting(move_frame, "向上滚动", "scroll_up", 4)
        self.create_key_setting(move_frame, "向下滚动", "scroll_down", 5)
        
        # 鼠标点击控制
        click_frame = ttk.LabelFrame(keybindings_container, text="鼠标点击控制")
        click_frame.pack(fill=tk.X, pady=5)
        
        self.create_key_setting(click_frame, "左键点击", "left_click", 0)
        self.create_key_setting(click_frame, "右键点击", "right_click", 1)
        self.create_key_setting(click_frame, "中键点击", "middle_click", 2)
        
        # 模式控制
        mode_frame = ttk.LabelFrame(keybindings_container, text="模式控制")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.create_key_setting(mode_frame, "切换模式热键", "toggle_mode_hotkey", 0)
        self.create_key_setting(mode_frame, "内部模式切换键", "toggle_mode_internal", 1)
        self.create_key_setting(mode_frame, "退出程序", "exit_program", 2)
    
    def create_key_setting(self, parent, label_text, config_key, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        
        key_var = tk.StringVar()
        key_var.set(self.config_parser.get('Keybindings', config_key))
        self.key_vars[config_key] = key_var
        
        key_entry = ttk.Entry(parent, textvariable=key_var, width=15)
        key_entry.grid(row=row, column=1, padx=5, pady=5)
        
        ttk.Button(parent, text="设置", 
                  command=lambda k=config_key, e=key_entry: self.record_key(k, e)).grid(
                      row=row, column=2, padx=5, pady=5)
    
    def create_settings_ui(self):
        # 创建通用设置界面
        scrollable_container = ScrollableFrame(self.settings_frame)
        scrollable_container.pack(fill=tk.BOTH, expand=True)
        
        settings_container = scrollable_container.content_frame
        
        # 鼠标速度设置
        speed_frame = ttk.LabelFrame(settings_container, text="鼠标速度设置")
        speed_frame.pack(fill=tk.X, pady=5)
        
        # 基础移动速度
        ttk.Label(speed_frame, text="基础移动速度").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.move_speed_var = tk.IntVar(value=self.config_parser.getint('Settings', 'mouse_move_speed'))
        ttk.Scale(speed_frame, from_=1, to=50, variable=self.move_speed_var, 
                 orient=tk.HORIZONTAL).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(speed_frame, textvariable=self.move_speed_var).grid(row=0, column=2, padx=5, pady=5)
        
        # Shift乘数
        ttk.Label(speed_frame, text="Shift速度乘数").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.shift_mult_var = tk.DoubleVar(value=self.config_parser.getfloat('Settings', 'mouse_speed_shift_multiplier'))
        ttk.Scale(speed_frame, from_=0.1, to=2.0, variable=self.shift_mult_var, 
                 orient=tk.HORIZONTAL).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(speed_frame, textvariable=self.shift_mult_var).grid(row=1, column=2, padx=5, pady=5)
        
        # CapsLock乘数
        ttk.Label(speed_frame, text="CapsLock速度乘数").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.caps_mult_var = tk.DoubleVar(value=self.config_parser.getfloat('Settings', 'mouse_speed_capslock_multiplier'))
        ttk.Scale(speed_frame, from_=0.1, to=2.0, variable=self.caps_mult_var, 
                 orient=tk.HORIZONTAL).grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(speed_frame, textvariable=self.caps_mult_var).grid(row=2, column=2, padx=5, pady=5)
        
        # 滚轮设置
        scroll_frame = ttk.LabelFrame(settings_container, text="滚轮设置")
        scroll_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(scroll_frame, text="滚轮滚动量").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.scroll_amount_var = tk.IntVar(value=self.config_parser.getint('Settings', 'mouse_scroll_amount'))
        ttk.Scale(scroll_frame, from_=1, to=10, variable=self.scroll_amount_var, 
                 orient=tk.HORIZONTAL).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(scroll_frame, textvariable=self.scroll_amount_var).grid(row=0, column=2, padx=5, pady=5)
        
        # 性能设置
        perf_frame = ttk.LabelFrame(settings_container, text="性能设置")
        perf_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(perf_frame, text="移动延迟(秒)").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.delay_var = tk.DoubleVar(value=self.config_parser.getfloat('Settings', 'delay_per_step'))
        ttk.Scale(perf_frame, from_=0.001, to=0.05, variable=self.delay_var, 
                 orient=tk.HORIZONTAL).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(perf_frame, textvariable=self.delay_var).grid(row=0, column=2, padx=5, pady=5)
    
    def record_key(self, config_key, entry):
        """开始录制按键，并改变控件状态"""
        # 如果正在录制另一个键，先智能地取消上一个
        if self.recording_entry:
            self.cancel_recording()

        self.recording_key = config_key
        self.recording_entry = entry
        self.original_key_value = self.key_vars[config_key].get()

        # <<< 核心：将输入框设为只读，防止用户输入和修改 >>>
        entry.config(state='readonly')
        
        entry.delete(0, tk.END)
        entry.insert(0, "按下任意键...")
        entry.focus_set()
        
        # 绑定全局按键事件
        self.root.bind('<Key>', self.on_key_press)
        # 绑定失去焦点事件，用于自动取消
        self.recording_entry.bind('<FocusOut>', self.cancel_recording)
    
    def cancel_recording(self, event=None):
        """当用户点击别处（失去焦点）时，取消录制"""
        if not self.recording_key:
            return

        # 恢复输入框的原始值
        self.key_vars[self.recording_key].set(self.original_key_value)
        self.status_var.set("录制已取消")

        # --- 执行与 on_key_press 中完全相同的清理工作 ---
        self.recording_entry.config(state='normal')
        
        self.root.unbind('<Key>')
        self.recording_entry.unbind('<FocusOut>')

        self.recording_key = None
        self.recording_entry = None
        self.original_key_value = ""
    
    
    def on_key_press(self, event):
        """处理按键事件，只录制单个按键，确保100%准确"""
        if not self.recording_key:
            return

        # 1. 直接获取按下的键名
        keysym = event.keysym
        
        # 2. 定义一个从 keysym 到我们标准名称的映射表
        #    这个表包含了所有需要“翻译”的键
        key_map = {
            'Shift_L': 'lshift',
            'Shift_R': 'rshift',
            'Control_L': 'lctrl',
            'Control_R': 'rctrl',
            'Alt_L': 'lalt',
            'Alt_R': 'ralt',
            'Caps_Lock': 'caps_lock',
            'Return': 'enter',
            'Escape': 'esc',
            'BackSpace': 'backspace',
            'space': 'space',
            'semicolon': 'semicolon',
            'apostrophe': 'apostrophe',
            'comma': 'comma',
            'period': 'period',
            'slash': 'slash'
        }

        # 3. 使用映射表进行翻译，如果找不到，就使用原始的小写键名
        final_key_str = key_map.get(keysym, keysym.lower())
        
        # --- 后续的清理流程保持不变 ---
        self.key_vars[self.recording_key].set(final_key_str)
        self.status_var.set(f"键位已设置: {final_key_str}")
        
        self.recording_entry.config(state='normal')
        self.root.unbind('<Key>')
        self.recording_entry.unbind('<FocusOut>')
        
        self.recording_key = None
        self.recording_entry = None
        self.original_key_value = ""
            
        return "break"
    
    def save_settings(self):
        """保存设置到配置文件。返回 True 表示成功，False 表示失败。"""
        try:
            from utool import KEY_TO_VK
            invalid_keys = []
            key_values = {}
            
            for key, var in self.key_vars.items():
                key_value = var.get()
                key_values[key] = key_value


                # 如果字符串中包含'+'，我们就认为它是一个组合键，不进行验证
                # 在目前的v0.0.1当中,还不支持组合键的输入,所有下面的代码实际还没有采用
                if '+' in key_value:
                    continue
                
                # 如果不是组合键，才进行有效性检查
                if key_value not in KEY_TO_VK:
                    invalid_keys.append(f"{key}: {key_value}")
            
           
            if invalid_keys:
                error_message = "以下键位设置无效:\n" + "\n".join(invalid_keys)
                self.status_var.set("保存失败: 存在无效键位")
                messagebox.showerror("保存失败", error_message)
                return False

            for key, value in key_values.items():
                self.config_parser.set('Keybindings', key, value)
            
            self.config_parser.set('Settings', 'mouse_move_speed', str(self.move_speed_var.get()))
            self.config_parser.set('Settings', 'mouse_speed_shift_multiplier', str(self.shift_mult_var.get()))
            self.config_parser.set('Settings', 'mouse_speed_capslock_multiplier', str(self.caps_mult_var.get()))
            self.config_parser.set('Settings', 'mouse_scroll_amount', str(self.scroll_amount_var.get()))
            self.config_parser.set('Settings', 'delay_per_step', str(self.delay_var.get()))
            
            with open(resource_path(self.config_file), 'w', encoding='utf-8') as f:
                self.config_parser.write(f)
            
            self.status_var.set("设置已保存")
            
            if messagebox.askyesno("应用设置", "设置已保存。是否立即应用新设置？"):
                self.apply_settings()
            else:
                messagebox.showinfo("保存成功", "设置已成功保存到配置文件。\n需要重启程序以应用新设置。")
            
            return True

        except Exception as e:
            self.status_var.set(f"保存失败: {str(e)}")
            messagebox.showerror("保存失败", f"无法保存设置: {str(e)}")
            return False
            
            
    def save_current_as_default(self):
        """将当前设置保存为新的默认配置"""
        if messagebox.askyesno("确认", "确定要将当前设置保存为默认配置吗？\n此操作将覆盖当前的默认设置。"):
            # “保存为默认”和“保存设置”在当前逻辑下的功能是相同的，都是写入config.ini
            # 所以直接调用 save_settings 方法即可
            if self.save_settings():
                self.status_var.set("当前设置已保存为默认")
                messagebox.showinfo("成功", "当前设置已成功保存为默认配置。")
    
    def apply_settings(self):
        """应用新设置（重启程序）"""
        try:
            import sys
            import os
            import subprocess
            
            # 获取当前Python解释器路径
            python = sys.executable
            
            # 获取当前脚本路径
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
            
            # 关闭当前GUI窗口
            self.root.destroy()
            
            # 启动新进程
            subprocess.Popen([python, script])
            
            # 退出当前进程
            os._exit(0)
            
        except Exception as e:
            messagebox.showerror("重启失败", f"无法重启程序: {str(e)}")
    
    def refresh_config(self):
        """刷新配置，重新从配置文件加载设置"""
        try:
            # 重新加载配置文件
            self.config_parser = configparser.ConfigParser()
            self.config_parser.read(resource_path(self.config_file), encoding='utf-8')
            self.config = AppConfig(self.config_file)
            
            # 更新键位设置
            for key, var in self.key_vars.items():
                var.set(self.config_parser.get('Keybindings', key))
            
            # 更新通用设置
            self.move_speed_var.set(self.config_parser.getint('Settings', 'mouse_move_speed'))
            self.shift_mult_var.set(self.config_parser.getfloat('Settings', 'mouse_speed_shift_multiplier'))
            self.caps_mult_var.set(self.config_parser.getfloat('Settings', 'mouse_speed_capslock_multiplier'))
            self.scroll_amount_var.set(self.config_parser.getint('Settings', 'mouse_scroll_amount'))
            self.delay_var.set(self.config_parser.getfloat('Settings', 'delay_per_step'))
            
            self.status_var.set("配置已刷新")
            messagebox.showinfo("刷新成功", "已从配置文件重新加载设置。")
        except Exception as e:
            self.status_var.set(f"刷新失败: {str(e)}")
            messagebox.showerror("刷新失败", f"无法刷新配置: {str(e)}")
    
    def reset_defaults(self):
        """恢复所有设置到硬编码的出厂默认值"""
        if messagebox.askyesno("确认", "确定要恢复所有设置到出厂默认值吗？\n(移动: i,j,k,l 等)"):
            # 1. 从新方法中获取真正的出厂设置
            key_defaults, setting_defaults = self.get_factory_defaults()
            
            # 2. 更新UI界面上的键位设置
            for key, value in key_defaults.items():
                if key in self.key_vars:
                    self.key_vars[key].set(value)
            
            # 3. 更新UI界面上的通用设置
            self.move_speed_var.set(setting_defaults['mouse_move_speed'])
            self.shift_mult_var.set(setting_defaults['mouse_speed_shift_multiplier'])
            self.caps_mult_var.set(setting_defaults['mouse_speed_capslock_multiplier'])
            self.scroll_amount_var.set(setting_defaults['mouse_scroll_amount'])
            self.delay_var.set(setting_defaults['delay_per_step'])
            
            self.status_var.set("已恢复出厂默认设置（尚未保存）")

def run_gui(on_close_callback=None):
    root = tk.Tk()
    app = KeyMouseGUI(root)
    
    # 定义窗口关闭时的行为
    def on_closing():
        if on_close_callback:
            on_close_callback()  # 调用回调函数
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing) # 绑定关闭事件
    root.mainloop()

if __name__ == "__main__":
    run_gui()