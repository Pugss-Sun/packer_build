import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import platform
from PIL import Image  # 引入 Pillow 库进行图片处理

class PyPackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 独立打包助手 Pro Max (PNG支持版)")
        self.root.geometry("720x650")
        
        # --- 变量存储 ---
        self.project_dir = tk.StringVar()
        self.main_script = tk.StringVar()
        self.exe_name = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # 布尔选项
        self.is_onefile = tk.BooleanVar(value=True)
        self.is_windowed = tk.BooleanVar(value=False)
        self.clean_before = tk.BooleanVar(value=True)
        self.uac_admin = tk.BooleanVar(value=False)
        
        # 高级选项
        self.hidden_imports = tk.StringVar()
        self.exclude_modules = tk.StringVar()
        self.data_files = [] 

        self._build_widgets()

    def _build_widgets(self):
        # 使用 Notebook 实现多标签页布局
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=10, fill='x')

        # === 标签页 1: 基础配置 ===
        self.tab_basic = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_basic, text='🛠️ 基础配置')
        self._build_basic_tab(self.tab_basic)

        # === 标签页 2: 数据与资源 ===
        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text='📂 资源/数据')
        self._build_data_tab(self.tab_data)

        # === 标签页 3: 高级参数 ===
        self.tab_adv = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_adv, text='⚙️ 高级选项')
        self._build_adv_tab(self.tab_adv)

        # === 底部日志与按钮 ===
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        ttk.Label(bottom_frame, text="打包日志:").pack(anchor='w')
        self.log_text = tk.Text(bottom_frame, height=10, state='disabled', bg="#1e1e1e", fg="#00ff00")
        self.log_text.pack(fill='both', expand=True)

        self.btn_run = ttk.Button(bottom_frame, text="🚀 开始一键打包", command=self._start_thread)
        self.btn_run.pack(pady=10, fill='x')

    def _build_basic_tab(self, parent):
        padding = {'padx': 5, 'pady': 5}
        
        # 1. 主程序
        ttk.Label(parent, text="主程序 (.py):").grid(row=0, column=0, sticky='w', **padding)
        ttk.Entry(parent, textvariable=self.main_script, width=55).grid(row=0, column=1, **padding)
        ttk.Button(parent, text="选择文件", command=self._select_file).grid(row=0, column=2, **padding)

        # 2. 图标 (修改提示文字)
        ttk.Label(parent, text="程序图标 (.ico/.png):").grid(row=1, column=0, sticky='w', **padding)
        ttk.Entry(parent, textvariable=self.icon_path, width=55).grid(row=1, column=1, **padding)
        ttk.Button(parent, text="选择图标", command=self._select_icon).grid(row=1, column=2, **padding)

        # 3. 输出名称
        ttk.Label(parent, text="输出EXE名称:").grid(row=2, column=0, sticky='w', **padding)
        ttk.Entry(parent, textvariable=self.exe_name, width=55).grid(row=2, column=1, **padding)
        ttk.Label(parent, text="(留空默认)").grid(row=2, column=2, **padding)

        # 4. 输出目录
        ttk.Label(parent, text="输出目录:").grid(row=3, column=0, sticky='w', **padding)
        ttk.Entry(parent, textvariable=self.output_dir, width=55).grid(row=3, column=1, **padding)
        ttk.Button(parent, text="选择目录", command=lambda: self.output_dir.set(filedialog.askdirectory())).grid(row=3, column=2, **padding)

        # 5. 常用开关
        opts_frame = ttk.LabelFrame(parent, text="打包模式")
        opts_frame.grid(row=4, column=0, columnspan=3, sticky='we', padx=5, pady=10)
        
        ttk.Checkbutton(opts_frame, text="单文件 (-F)", variable=self.is_onefile).pack(side='left', padx=10)
        ttk.Checkbutton(opts_frame, text="无控制台 (-w)", variable=self.is_windowed).pack(side='left', padx=10)
        ttk.Checkbutton(opts_frame, text="管理员权限 (--uac)", variable=self.uac_admin).pack(side='left', padx=10)
        ttk.Checkbutton(opts_frame, text="清理缓存", variable=self.clean_before).pack(side='left', padx=10)

    def _build_data_tab(self, parent):
        desc = ttk.Label(parent, text="添加非代码文件（如图片、配置），格式：源路径 -> 目标路径", foreground="gray")
        desc.pack(anchor='w', padx=5, pady=5)

        self.tree_data = ttk.Treeview(parent, columns=('src', 'dest'), show='headings', height=6)
        self.tree_data.heading('src', text='源文件/文件夹')
        self.tree_data.heading('dest', text='打包后内部路径 (通常为 . )')
        self.tree_data.column('src', width=350)
        self.tree_data.column('dest', width=150)
        self.tree_data.pack(fill='x', padx=5)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(btn_frame, text="➕ 添加文件", command=lambda: self._add_data_item('file')).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="➕ 添加文件夹", command=lambda: self._add_data_item('dir')).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="➖ 删除选中", command=self._remove_data_item).pack(side='left', padx=2)

    def _build_adv_tab(self, parent):
        padding = {'padx': 5, 'pady': 10}
        
        ttk.Label(parent, text="强制隐式导入 (--hidden-import):\n(模块名，用逗号分隔)").grid(row=0, column=0, sticky='nw', **padding)
        ttk.Entry(parent, textvariable=self.hidden_imports, width=60).grid(row=0, column=1, **padding)

        ttk.Label(parent, text="排除模块 (--exclude-module):\n(减少体积)").grid(row=1, column=0, sticky='nw', **padding)
        ttk.Entry(parent, textvariable=self.exclude_modules, width=60).grid(row=1, column=1, **padding)

    # --- 逻辑处理 ---
    def _select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            self.main_script.set(path)
            if not self.exe_name.get():
                self.exe_name.set(os.path.basename(path).split('.')[0])
            if not self.output_dir.get():
                self.output_dir.set(os.path.join(os.path.dirname(path), 'dist'))

    def _select_icon(self):
        # 修改：同时支持 ICO 和 PNG
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.ico *.png"), ("Icon Files", "*.ico"), ("PNG Files", "*.png")])
        if path: self.icon_path.set(path)

    def _add_data_item(self, mode):
        def on_confirm():
            dest = dest_entry.get()
            if not dest: dest = "."
            if mode == 'file':
                src = filedialog.askopenfilename()
            else:
                src = filedialog.askdirectory()
            
            if src:
                self.data_files.append((src, dest))
                self.tree_data.insert('', 'end', values=(src, dest))
                top.destroy()

        top = tk.Toplevel(self.root)
        top.title("添加资源")
        ttk.Label(top, text="打包后的内部位置 (例如 '.' 或 'img'):").pack(padx=10, pady=5)
        dest_entry = ttk.Entry(top)
        dest_entry.pack(padx=10, fill='x')
        dest_entry.insert(0, ".")
        ttk.Button(top, text="选择源文件并确认", command=on_confirm).pack(pady=10)

    def _remove_data_item(self):
        selected = self.tree_data.selection()
        if selected:
            for item in selected:
                values = self.tree_data.item(item, 'values')
                self.data_files = [d for d in self.data_files if not (d[0] == values[0] and d[1] == values[1])]
                self.tree_data.delete(item)

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
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.config(state='disabled')
        
        self._log(">>> 正在初始化构建参数...")
        
        script_path = self.main_script.get()
        work_dir = os.path.dirname(script_path)
        
        # === 新增：处理图标 (PNG 转 ICO) ===
        final_icon_path = None
        temp_icon_created = False
        
        raw_icon_path = self.icon_path.get()
        if raw_icon_path:
            if raw_icon_path.lower().endswith('.png'):
                self._log(f">>> 检测到 PNG 图标: {os.path.basename(raw_icon_path)}")
                self._log(">>> 正在转换 PNG 为 ICO...")
                try:
                    img = Image.open(raw_icon_path)
                    # 转换为 ICO，通常包含多种尺寸以适应 Windows 显示
                    temp_icon_path = os.path.join(work_dir, "temp_icon_build.ico")
                    img.save(temp_icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
                    final_icon_path = temp_icon_path
                    temp_icon_created = True
                    self._log("✅ 图标转换成功！")
                except Exception as e:
                    self._log(f"❌ 图标转换失败: {str(e)}")
                    messagebox.showerror("Error", f"图标转换失败: {str(e)}")
                    self.btn_run.config(state='normal')
                    return
            else:
                final_icon_path = raw_icon_path

        # 构建 PyInstaller 参数
        args = ['--noconfirm']
        
        if self.is_onefile.get(): args.append('--onefile')
        if self.is_windowed.get(): args.append('--windowed')
        if self.clean_before.get(): args.append('--clean')
        if self.uac_admin.get(): args.append('--uac-admin')
        
        if self.exe_name.get(): args.extend(['--name', self.exe_name.get()])
        if final_icon_path: args.extend(['--icon', final_icon_path])
        if self.output_dir.get(): args.extend(['--distpath', self.output_dir.get()])

        sep = ';' if platform.system() == 'Windows' else ':'
        for src, dest in self.data_files:
            args.extend(['--add-data', f'{src}{sep}{dest}'])

        if self.hidden_imports.get():
            imports = self.hidden_imports.get().replace('，', ',').split(',')
            for imp in imports:
                if imp.strip():
                    args.extend(['--hidden-import', imp.strip()])

        if self.exclude_modules.get():
            excludes = self.exclude_modules.get().replace('，', ',').split(',')
            for exc in excludes:
                if exc.strip():
                    args.extend(['--exclude-module', exc.strip()])

        args.append(script_path)

        cmd_str = f"pyinstaller {' '.join(args)}"
        self._log(f">>> 执行命令: {cmd_str}")
        self._log("-" * 40)
        
        try:
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                ["pyinstaller"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False,
                startupinfo=startupinfo,
                cwd=work_dir
            )
            
            for line in process.stdout:
                self._log(line.strip())
            
            process.wait()
            
            # === 清理临时图标文件 ===
            if temp_icon_created and os.path.exists(final_icon_path):
                try:
                    os.remove(final_icon_path)
                    self._log(">>> 已清理临时图标文件")
                except:
                    pass

            if process.returncode == 0:
                dist_path = self.output_dir.get() or os.path.join(work_dir, 'dist')
                self._log("\n✅ 打包成功！")
                messagebox.showinfo("Success", f"打包完成！\n输出目录：{dist_path}")
                try:
                    os.startfile(dist_path)
                except:
                    pass
            else:
                self._log(f"\n❌ 打包失败，错误码: {process.returncode}")
                messagebox.showerror("Error", "打包过程中出现错误，请查看日志。")
        except Exception as e:
            self._log(f"\n❌ 系统异常: {str(e)}")
        
        self.btn_run.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = PyPackerGUI(root)
    root.mainloop()