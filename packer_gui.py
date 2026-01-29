import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import PyInstaller.__main__ # 改进：直接调用模块提高兼容性

class PyPackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 独立打包助手 Pro")
        self.root.geometry("650x550")
        
        # --- 变量存储 ---
        self.project_dir = tk.StringVar()
        self.main_script = tk.StringVar()
        self.exe_name = tk.StringVar()
        self.icon_path = tk.StringVar() # 新增：图标路径变量
        self.is_onefile = tk.BooleanVar(value=True)
        self.is_windowed = tk.BooleanVar(value=False)
        self.clean_before = tk.BooleanVar(value=True)

        self._build_widgets()

    def _build_widgets(self):
        padding = {'padx': 10, 'pady': 5}
        
        # 1. 项目路径选择
        ttk.Label(self.root, text="项目根目录:").grid(row=0, column=0, sticky='w', **padding)
        ttk.Entry(self.root, textvariable=self.project_dir, width=50).grid(row=0, column=1, **padding)
        ttk.Button(self.root, text="浏览", command=self._select_dir).grid(row=0, column=2, **padding)

        # 2. 主程序选择
        ttk.Label(self.root, text="主程序 (.py):").grid(row=1, column=0, sticky='w', **padding)
        ttk.Entry(self.root, textvariable=self.main_script, width=50).grid(row=1, column=1, **padding)
        ttk.Button(self.root, text="选择", command=self._select_file).grid(row=1, column=2, **padding)

        # 3. 图标选择 (新增)
        ttk.Label(self.root, text="程序图标 (.ico):").grid(row=2, column=0, sticky='w', **padding)
        ttk.Entry(self.root, textvariable=self.icon_path, width=50).grid(row=2, column=1, **padding)
        ttk.Button(self.root, text="选择图标", command=self._select_icon).grid(row=2, column=2, **padding)

        # 4. EXE 名称
        ttk.Label(self.root, text="输出名称:").grid(row=3, column=0, sticky='w', **padding)
        ttk.Entry(self.root, textvariable=self.exe_name, width=50).grid(row=3, column=1, **padding)

        # 5. 参数勾选区
        options_frame = ttk.LabelFrame(self.root, text="打包配置")
        options_frame.grid(row=4, column=0, columnspan=3, sticky='we', padx=10, pady=10)

        ttk.Checkbutton(options_frame, text="单文件 (-F)", variable=self.is_onefile).pack(side='left', **padding)
        ttk.Checkbutton(options_frame, text="窗口模式 (隐藏控制台)", variable=self.is_windowed).pack(side='left', **padding)
        ttk.Checkbutton(options_frame, text="清理缓存", variable=self.clean_before).pack(side='left', **padding)

        # 6. 日志输出区
        self.log_text = tk.Text(self.root, height=12, state='disabled', bg="#1e1e1e", fg="#00ff00")
        self.log_text.grid(row=5, column=0, columnspan=3, sticky='we', padx=10)

        # 7. 开始按钮
        self.btn_run = ttk.Button(self.root, text="🚀 开始一键打包", command=self._start_thread)
        self.btn_run.grid(row=6, column=0, columnspan=3, pady=15)

    # --- 逻辑处理 ---
    def _select_dir(self):
        path = filedialog.askdirectory()
        if path: self.project_dir.set(path)

    def _select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            self.main_script.set(path)
            if not self.exe_name.get():
                self.exe_name.set(os.path.basename(path).split('.')[0])

    def _select_icon(self):
        # 限制只能选择 .ico 文件，这是 Windows 可执行文件的标准
        path = filedialog.askopenfilename(filetypes=[("Icon Files", "*.ico")])
        if path: self.icon_path.set(path)

    def _log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _start_thread(self):
        if not self.main_script.get():
            messagebox.showerror("错误", "请选择主程序文件！")
            return
        threading.Thread(target=self._execute_pack, daemon=True).start()

    def _execute_pack(self):
        self.btn_run.config(state='disabled')
        self._log(">>> 准备打包环境...")
        
        work_dir = self.project_dir.get() or os.path.dirname(self.main_script.get())
        os.chdir(work_dir)

        # 构建 PyInstaller 参数
        args = ['--noconfirm']
        
        if self.is_onefile.get(): args.append('--onefile')
        if self.is_windowed.get(): args.append('--windowed')
        if self.clean_before.get(): args.append('--clean')
        if self.exe_name.get(): args.extend(['--name', self.exe_name.get()])
        
        # 关键：处理图标参数
        if self.icon_path.get():
            args.extend(['--icon', self.icon_path.get()])

        args.append(self.main_script.get())

        self._log(f">>> 执行命令: pyinstaller {' '.join(args)}")
        
        try:
            # 改进：直接使用 PyInstaller 内核运行，能更好地捕捉输出
            process = subprocess.Popen(
                ["pyinstaller"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                bufsize=1
            )
            
            for line in process.stdout:
                self._log(line.strip())
            
            process.wait()
            if process.returncode == 0:
                self._log("\n✨ 打包成功！文件位于: " + os.path.join(work_dir, "dist"))
                messagebox.showinfo("Success", "打包任务已圆满完成！")
            else:
                self._log("\n⚠️ 打包中止，错误码: " + str(process.returncode))
        except Exception as e:
            self._log(f"\n❌ 发生异常: {str(e)}")
        
        self.btn_run.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = PyPackerGUI(root)
    root.mainloop()