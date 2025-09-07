import tkinter as tk

try:
    root = tk.Tk()
    root.title("PyInstaller Tkinter Test")
    tk.Label(root, text="如果能看到这个窗口，说明打包环境正常！", padx=20, pady=20).pack()
    root.mainloop()
except Exception as e:
    # 如果有任何错误，写入一个文件，方便我们查看
    with open("test_error.log", "w") as f:
        f.write(str(e))