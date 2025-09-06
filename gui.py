"""GUI模块,提供图形用户界面功能。"""

import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
import sys
import subprocess
from config_loader import AppConfig, get_base_path
from utool import KEY_TO_VK, NAME_TO_PYNPUT_KEY
import autostart_manager


class FormattedLabel(ttk.Label):
    """格式化标签控件,用于显示数值。"""
    
    def __init__(self, parent, textvariable, precision=1, **kwargs):
        self.var = textvariable
        self.precision = precision
        self.str_var = tk.StringVar()
        super().__init__(parent, textvariable=self.str_var, **kwargs)
        self.var.trace_add("write", self._update_text)
        self._update_text()

    def _update_text(self, *args):
        try:
            self.str_var.set(f"{self.var.get():.{self.precision}f}")
        except (ValueError, tk.TclError):
            self.str_var.set("")


class ScrollableFrame(ttk.Frame):
    """可滚动的Frame控件。"""
    
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
        
        self._bind_mouse_wheel_to_children(self)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mouse_wheel_to_children(self, widget):
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_mouse_wheel_to_children(child)


class KeyMouseGUI:
    """KeyMouse主界面类。"""
    
    def __init__(self, root, tray_icon=None):
        self.root = root
        self.tray_icon = tray_icon
        
        self.root.title("KeyMouse 设置")
        self.root.geometry("600x500")
        self.root.minsize(450, 400)
        self.root.resizable(True, True)
        
        self.config_file_name = 'config.ini'
        self.config_path = os.path.join(get_base_path(), self.config_file_name)
        self.config = AppConfig(self.config_file_name)
        self.config_parser = configparser.ConfigParser()
        self.config_parser.read(self.config_path, encoding='utf-8')
        
        self.main_frame = ttk.Notebook(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.keybindings_frame = ttk.Frame(self.main_frame)
        self.settings_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.keybindings_frame, text="键位设置")
        self.main_frame.add(self.settings_frame, text="通用设置")
        
        self.recording_key = None
        self.recording_entry = None
        self.original_key_value = ""
        self.key_vars = {}
        
        self._create_widgets()

    def _create_widgets(self):
        """创建所有界面控件。"""
        self.create_keybindings_ui()
        self.create_settings_ui()
        
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            self.button_frame,
            text="保存设置",
            command=self.save_settings
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            self.button_frame,
            text="保存为默认",
            command=self.save_current_as_default
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            self.button_frame,
            text="恢复默认",
            command=self.reset_defaults
        ).pack(side=tk.RIGHT, padx=5)
        
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def get_factory_defaults(self):
        """获取出厂默认设置。"""
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
            'exit_program': 'esc',
            'sticky_left_click': 'n'
        }
        
        setting_defaults = {
            'mouse_move_speed': 20,
            'mouse_speed_shift_multiplier': 0.5,
            'mouse_speed_capslock_multiplier': 0.2,
            'delay_per_step': 0.01,
            'initial_velocity': 150.0,
            'max_velocity': 1500.0,
            'acceleration': 700.0
        }
        
        return key_defaults, setting_defaults

    def create_keybindings_ui(self):
        """创建键位设置界面。"""
        scrollable_container = ScrollableFrame(self.keybindings_frame)
        scrollable_container.pack(fill=tk.BOTH, expand=True)
        keybindings_container = scrollable_container.content_frame
        
        # 鼠标移动控制
        move_frame = ttk.LabelFrame(keybindings_container, text="鼠标移动控制")
        move_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.create_key_setting(move_frame, "向上移动", "move_up", 0)
        self.create_key_setting(move_frame, "向下移动", "move_down", 1)
        self.create_key_setting(move_frame, "向左移动", "move_left", 2)
        self.create_key_setting(move_frame, "向右移动", "move_right", 3)
        self.create_key_setting(move_frame, "向上滚动", "scroll_up", 4)
        self.create_key_setting(move_frame, "向下滚动", "scroll_down", 5)
        
        # 鼠标点击控制
        click_frame = ttk.LabelFrame(keybindings_container, text="鼠标点击控制")
        click_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.create_key_setting(click_frame, "左键点击", "left_click", 0)
        self.create_key_setting(click_frame, "右键点击", "right_click", 1)
        self.create_key_setting(click_frame, "中键点击", "middle_click", 2)
        self.create_key_setting(click_frame, "粘滞左键 (切换)", "sticky_left_click", 3)
        
        # 模式控制
        mode_frame = ttk.LabelFrame(keybindings_container, text="模式控制")
        mode_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.create_key_setting(mode_frame, "切换模式热键", "toggle_mode_hotkey", 0)
        self.create_key_setting(mode_frame, "内部模式切换键", "toggle_mode_internal", 1)
        self.create_key_setting(mode_frame, "退出程序", "exit_program", 2)

    def create_key_setting(self, parent, label_text, config_key, row):
        """创建单个键位设置行。"""
        ttk.Label(parent, text=label_text).grid(
            row=row, column=0, padx=5, pady=5, sticky=tk.W
        )
        
        key_var = tk.StringVar()
        key_var.set(self.config_parser.get('Keybindings', config_key, fallback=''))
        self.key_vars[config_key] = key_var
        
        key_entry = ttk.Entry(parent, textvariable=key_var, width=15)
        key_entry.grid(row=row, column=1, padx=5, pady=5)
        
        command = lambda k=config_key, e=key_entry: self.record_key(k, e)
        ttk.Button(
            parent,
            text="设置",
            command=command
        ).grid(row=row, column=2, padx=5, pady=5)

    def create_settings_ui(self):
        """创建通用设置界面。"""
        scrollable_container = ScrollableFrame(self.settings_frame)
        scrollable_container.pack(fill=tk.BOTH, expand=True)
        settings_container = scrollable_container.content_frame
        
        # 系统集成设置
        integration_frame = ttk.LabelFrame(settings_container, text="系统集成")
        integration_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # 开机自启动
        self.autostart_var = tk.BooleanVar(value=autostart_manager.is_enabled())
        autostart_check = ttk.Checkbutton(
            integration_frame,
            text="开机时自动启动",
            variable=self.autostart_var,
            command=self.toggle_autostart
        )
        autostart_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 管理员启动
        self.admin_var = tk.BooleanVar(
            value=self.config_parser.getboolean('Settings', 'run_as_admin', fallback=False)
        )
        admin_check = ttk.Checkbutton(
            integration_frame,
            text="以管理员身份启动 (解决权限问题)",
            variable=self.admin_var
        )
        admin_check.pack(side=tk.LEFT, padx=20, pady=5)
        
        # 鼠标速度设置
        speed_frame = ttk.LabelFrame(settings_container, text="鼠标速度设置")
        speed_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # 基础移动速度
        ttk.Label(speed_frame, text="基础移动速度").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.move_speed_var = tk.IntVar(
            value=self.config_parser.getint('Settings', 'mouse_move_speed')
        )
        ttk.Scale(
            speed_frame,
            from_=1,
            to=50,
            variable=self.move_speed_var,
            orient=tk.HORIZONTAL
        ).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        FormattedLabel(
            speed_frame,
            textvariable=self.move_speed_var,
            precision=0
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Shift速度乘数
        ttk.Label(speed_frame, text="Shift速度乘数").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.shift_mult_var = tk.DoubleVar(
            value=self.config_parser.getfloat('Settings', 'mouse_speed_shift_multiplier')
        )
        ttk.Scale(
            speed_frame,
            from_=0.1,
            to=2.0,
            variable=self.shift_mult_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        FormattedLabel(
            speed_frame,
            textvariable=self.shift_mult_var
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # CapsLock速度乘数
        ttk.Label(speed_frame, text="CapsLock速度乘数").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.caps_mult_var = tk.DoubleVar(
            value=self.config_parser.getfloat('Settings', 'mouse_speed_capslock_multiplier')
        )
        ttk.Scale(
            speed_frame,
            from_=0.1,
            to=2.0,
            variable=self.caps_mult_var,
            orient=tk.HORIZONTAL
        ).grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        FormattedLabel(
            speed_frame,
            textvariable=self.caps_mult_var
        ).grid(row=2, column=2, padx=5, pady=5)
        
        # 平滑滚动设置
        smooth_scroll_frame = ttk.LabelFrame(settings_container, text="平滑滚动设置")
        smooth_scroll_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # 初始速度
        ttk.Label(smooth_scroll_frame, text="初始速度 (px/s)").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.initial_velocity_var = tk.DoubleVar(
            value=self.config_parser.getfloat('SmoothScrolling', 'initial_velocity')
        )
        ttk.Scale(
            smooth_scroll_frame,
            from_=50,
            to=500,
            variable=self.initial_velocity_var,
            orient=tk.HORIZONTAL
        ).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        FormattedLabel(
            smooth_scroll_frame,
            textvariable=self.initial_velocity_var
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # 最大速度
        ttk.Label(smooth_scroll_frame, text="最大速度 (px/s)").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.max_velocity_var = tk.DoubleVar(
            value=self.config_parser.getfloat('SmoothScrolling', 'max_velocity')
        )
        ttk.Scale(
            smooth_scroll_frame,
            from_=500,
            to=6000,
            variable=self.max_velocity_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        FormattedLabel(
            smooth_scroll_frame,
            textvariable=self.max_velocity_var
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # 加速度
        ttk.Label(smooth_scroll_frame, text="加速度 (px/s²)").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.acceleration_var = tk.DoubleVar(
            value=self.config_parser.getfloat('SmoothScrolling', 'acceleration')
        )
        ttk.Scale(
            smooth_scroll_frame,
            from_=100,
            to=2000,
            variable=self.acceleration_var,
            orient=tk.HORIZONTAL
        ).grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        FormattedLabel(
            smooth_scroll_frame,
            textvariable=self.acceleration_var
        ).grid(row=2, column=2, padx=5, pady=5)
        
        # 性能设置
        perf_frame = ttk.LabelFrame(settings_container, text="性能设置")
        perf_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(perf_frame, text="移动延迟(秒)").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.delay_var = tk.DoubleVar(
            value=self.config_parser.getfloat('Settings', 'delay_per_step')
        )
        ttk.Scale(
            perf_frame,
            from_=0.001,
            to=0.05,
            variable=self.delay_var,
            orient=tk.HORIZONTAL
        ).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        FormattedLabel(
            perf_frame,
            textvariable=self.delay_var,
            precision=3
        ).grid(row=0, column=2, padx=5, pady=5)

    def toggle_autostart(self):
        """切换开机自启动状态。"""
        try:
            if self.autostart_var.get():
                autostart_manager.enable()
                self.status_var.set("开机自启动已启用")
            else:
                autostart_manager.disable()
                self.status_var.set("开机自启动已禁用")
        except Exception as e:
            self.status_var.set("操作失败: 无法写入注册表")
            messagebox.showerror(
                "操作失败",
                f"无法修改启动项，请检查权限。\n错误: {e}"
            )
            self.autostart_var.set(not self.autostart_var.get())

    def record_key(self, config_key, entry):
        """记录键位。"""
        if self.recording_entry:
            self.cancel_recording()
            
        self.recording_key = config_key
        self.recording_entry = entry
        self.original_key_value = self.key_vars[config_key].get()
        
        entry.config(state='readonly')
        entry.delete(0, tk.END)
        entry.insert(0, "按下任意键...")
        entry.focus_set()
        
        self.root.bind('<Key>', self.on_key_press)
        self.root.bind('<Button-1>', self.cancel_recording)

    def cancel_recording(self, event=None):
        """取消键位记录。"""
        if not self.recording_key:
            return
            
        self.key_vars[self.recording_key].set(self.original_key_value)
        self.status_var.set("录制已取消")
        
        self.recording_entry.config(state='normal')
        self.root.unbind('<Key>')
        self.root.unbind('<Button-1>')
        
        self.recording_key = None
        self.recording_entry = None
        self.original_key_value = ""

    def on_key_press(self, event):
        """处理按键事件。"""
        if not self.recording_key:
            return
            
        keysym = event.keysym
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
        
        final_key_str = key_map.get(keysym, keysym.lower())
        self.key_vars[self.recording_key].set(final_key_str)
        self.status_var.set(f"键位已设置: {final_key_str}")
        
        self.recording_entry.config(state='normal')
        self.root.unbind('<Key>')
        self.root.unbind('<Button-1>')
        
        self.recording_key = None
        self.recording_entry = None
        self.original_key_value = ""

    def save_settings(self):
        """保存设置到配置文件。"""
        try:
            # 验证键位
            invalid_keys = []
            key_values = {}
            
            for key, var in self.key_vars.items():
                key_value = var.get()
                key_values[key] = key_value
                if '+' not in key_value and key_value not in KEY_TO_VK:
                    invalid_keys.append(f"{key}: {key_value}")
                    
            if invalid_keys:
                messagebox.showerror(
                    "保存失败",
                    "以下键位设置无效:\n" + "\n".join(invalid_keys)
                )
                return False
            
            # 写入键位
            for key, value in key_values.items():
                self.config_parser.set('Keybindings', key, value)
            
            # 写入通用设置
            self.config_parser.set('Settings', 'mouse_move_speed',
                                 str(self.move_speed_var.get()))
            self.config_parser.set('Settings', 'mouse_speed_shift_multiplier',
                                 f"{self.shift_mult_var.get():.1f}")
            self.config_parser.set('Settings', 'mouse_speed_capslock_multiplier',
                                 f"{self.caps_mult_var.get():.1f}")
            self.config_parser.set('Settings', 'delay_per_step',
                                 f"{self.delay_var.get():.3f}")
            self.config_parser.set('Settings', 'run_as_admin',
                                 str(self.admin_var.get()).lower())
            
            # 写入平滑滚动设置
            self.config_parser.set('SmoothScrolling', 'initial_velocity',
                                 f"{self.initial_velocity_var.get():.1f}")
            self.config_parser.set('SmoothScrolling', 'max_velocity',
                                 f"{self.max_velocity_var.get():.1f}")
            self.config_parser.set('SmoothScrolling', 'acceleration',
                                 f"{self.acceleration_var.get():.1f}")
            
            # 保存到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config_parser.write(f)
            
            self.status_var.set("设置已保存")
            
            if messagebox.askyesno("应用设置",
                                 "设置已保存。是否立即应用新设置？\n(程序将会重启)"):
                self.apply_settings()
            else:
                messagebox.showinfo("保存成功",
                                  "设置已成功保存到配置文件。\n将在下次启动时应用新设置。")
            
            return True
            
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存设置: {str(e)}")
            return False

    def save_current_as_default(self):
        """将当前设置保存为默认配置。"""
        if messagebox.askyesno("确认", "确定要将当前设置保存为默认配置吗？"):
            if self.save_settings():
                messagebox.showinfo("成功", "当前设置已成功保存为默认配置。")

    def apply_settings(self):
        """应用设置并重启程序。"""
        try:
            print("准备重启...")
            params = sys.argv[1:]
            if getattr(sys, 'frozen', False):
                restart_target = [sys.executable]+params
            else:
                main_script = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "main.py")
                ) 
                restart_target = [sys.executable, main_script]
                
            subprocess.Popen(restart_target)
            print(f"新进程已启动: {' '.join(restart_target)}")
            
            if self.tray_icon:
                self.tray_icon.on_exit()
            else:
                self.root.destroy()
                
        except Exception as e:
            messagebox.showerror("重启失败", f"无法重启程序: {str(e)}")

    def refresh_config(self):
        """刷新配置。"""
        try:
            self.config_parser.read(self.config_path, encoding='utf-8')
            self.config = AppConfig(self.config_file_name)
            
            # 刷新键位设置
            for key, var in self.key_vars.items():
                var.set(self.config_parser.get('Keybindings', key, fallback=''))
            
            # 刷新通用设置
            self.move_speed_var.set(
                self.config_parser.getint('Settings', 'mouse_move_speed')
            )
            self.shift_mult_var.set(
                self.config_parser.getfloat('Settings', 'mouse_speed_shift_multiplier')
            )
            self.caps_mult_var.set(
                self.config_parser.getfloat('Settings', 'mouse_speed_capslock_multiplier')
            )
            self.delay_var.set(
                self.config_parser.getfloat('Settings', 'delay_per_step')
            )
            self.admin_var.set(
                self.config_parser.getboolean('Settings', 'run_as_admin', fallback=False)
            )
            
            # 刷新平滑滚动设置
            self.initial_velocity_var.set(
                self.config_parser.getfloat('SmoothScrolling', 'initial_velocity')
            )
            self.max_velocity_var.set(
                self.config_parser.getfloat('SmoothScrolling', 'max_velocity')
            )
            self.acceleration_var.set(
                self.config_parser.getfloat('SmoothScrolling', 'acceleration')
            )
            
            self.status_var.set("配置已刷新")
            
        except Exception as e:
            messagebox.showerror("刷新失败", f"无法刷新配置: {str(e)}")

    def reset_defaults(self):
        """恢复默认设置。"""
        if messagebox.askyesno("确认", "确定要恢复所有设置到出厂默认值吗？"):
            key_defaults, setting_defaults = self.get_factory_defaults()
            
            # 重置键位
            for key, value in key_defaults.items():
                if key in self.key_vars:
                    self.key_vars[key].set(value)
            
            # 重置通用设置
            self.move_speed_var.set(setting_defaults['mouse_move_speed'])
            self.shift_mult_var.set(setting_defaults['mouse_speed_shift_multiplier'])
            self.caps_mult_var.set(setting_defaults['mouse_speed_capslock_multiplier'])
            self.delay_var.set(setting_defaults['delay_per_step'])
            self.admin_var.set(False)  # 管理员模式默认关闭
            
            # 重置平滑滚动设置
            self.initial_velocity_var.set(setting_defaults['initial_velocity'])
            self.max_velocity_var.set(setting_defaults['max_velocity'])
            self.acceleration_var.set(setting_defaults['acceleration'])
            
            self.status_var.set("已恢复出厂默认设置（尚未保存）")


def run_gui(on_close_callback=None, tray_icon=None):
    """运行GUI程序。"""
    root = tk.Tk()
    app = KeyMouseGUI(root, tray_icon)
    
    def on_closing():
        if on_close_callback:
            on_close_callback()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

  
if __name__ == "__main__":
    run_gui()