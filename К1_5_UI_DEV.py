import tkinter as tk
import re
from tkinter import colorchooser

class OuroMasterEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- ЦВЕТОВАЯ ПАЛИТРА ---
        self.C_WINDOW_BG   = "#464646"  
        self.C_TOPBAR_BG   = "#0F0F0F"  
        self.C_SIDEBAR_BG  = "#151515"  
        self.C_CANVAS_BG   = "#323232"  
        self.C_TEXT_MAIN   = "#FFFFFF"  
        self.C_TEXT_DIM    = "#e2e2e2"  
        self.C_ACCENT      = "#ffffff"  
        self.C_ENTRY_BG    = "#222222"  
        self.C_BTN_DARK    = "#252525"  
        self.C_BTN_TEXT    = "#e1e1e1"  
        self.C_BTN_DANGER  = "#C0392B"  
        self.C_MENU_BG     = "#222222"  
        self.C_MENU_ACTIVE = "#444444"  
        
        self.themes = {
            'O': {"bg": "#FFA500", "px": "#0A0A0A", "inv_bg": "#231600"},
            'W': {"bg": "#E0E0E0", "px": "#0A0A0A", "inv_bg": "#232323"},
            'B': {"bg": "#45b5ff", "px": "#0A0A0A", "inv_bg": "#001e34"}
        }
        
        self.GRID_BRIGHTNESS = 0.9
        self.INV_GRID_BRIGHTNESS = 1.7
        # ------------------------

        self.title("К1&K5 UI EDITOR BY OUROBOROS")
        self.configure(bg=self.C_WINDOW_BG)
        self.geometry("1600x900")
        self.resizable(False, False)
        
        self.WIDTH, self.HEIGHT = 128, 64
        self.SCALE = 8
        self.STRETCH_Y = 1.45
        self.PADDING = 2 
        self.pixels = [[0 for _ in range(self.HEIGHT)] for _ in range(self.WIDTH)]
        
        # --- ИСТОРИЯ (UNDO) ---
        self.history = []
        
        self.work_w, self.work_h = 128, 64
        self.current_theme = 'O'
        self.inverted = False
        self.line_start = None
        self.phantom_line = None 
        self.line_just_finished = False
        self.show_line_grid = False
        
        self.multi_mode = False
        self.pending_chars = None 

        self.theme_buttons = {}
        self.quick_buttons = {} 
        self.action_buttons = []
        
        self.setup_ui()
        self.create_context_menu()
        self.redraw_full()

    # --- МЕТОДЫ ОТМЕНЫ ---
    def save_history(self):
        """Сохраняем текущее состояние перед изменением"""
        state = [row[:] for row in self.pixels]
        self.history.append(state)
        if len(self.history) > 10:
            self.history.pop(0)

    def undo(self, event=None):
        """Возврат к предыдущему состоянию"""
        if self.history:
            self.pixels = self.history.pop()
            self.redraw_full()

    def adjust_color(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        new_rgb = [max(0, min(255, int(c * factor))) for c in rgb]
        return "#{:02x}{:02x}{:02x}".format(*new_rgb)

    def choose_custom_color(self):
        color = colorchooser.askcolor(title="Select color")[1]
        if color:
            self.themes['CUSTOM'] = {"bg": color, "px": "#0A0A0A", "inv_bg": self.adjust_color(color, 0.2)}
            self.btn_palette.config(bg=color) 
            self.set_theme('CUSTOM')

    def set_quick_dim(self, w, h, btn_key):
        self.w_entry.delete(0, tk.END)
        self.w_entry.insert(0, str(w))
        self.h_entry.delete(0, tk.END)
        self.h_entry.insert(0, str(h))
        self.apply_settings()
        self.update_quick_button_highlights(btn_key)

    def update_quick_button_highlights(self, active_key):
        theme_color = self.themes[self.current_theme]['bg']
        for key, btn in self.quick_buttons.items():
            if key == active_key:
                btn.config(bg=theme_color, fg="black")
            else:
                btn.config(bg=self.C_BTN_DARK, fg=self.C_BTN_TEXT)

    def reset_dims(self):
        self.w_entry.delete(0, tk.END)
        self.w_entry.insert(0, "128")
        self.h_entry.delete(0, tk.END)
        self.h_entry.insert(0, "64")
        self.update_quick_button_highlights(None)
        self.apply_settings()

    def get_offsets(self):
        off_x = (self.WIDTH - self.work_w) // 2
        off_y = (self.HEIGHT - self.work_h) // 2
        return off_x, off_y

    def setup_ui(self):
        top = tk.Frame(self, bg=self.C_TOPBAR_BG, height=45)
        top.pack(fill=tk.X, side=tk.TOP)
        top.pack_propagate(False)

        left_box = tk.Frame(top, bg=self.C_TOPBAR_BG)
        left_box.pack(side=tk.LEFT, padx=10)

        tk.Label(left_box, text="SCALE:", fg=self.C_TEXT_DIM, bg=self.C_TOPBAR_BG, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.scale_entry = tk.Entry(left_box, width=3, bg=self.C_ENTRY_BG, fg=self.C_TEXT_MAIN, borderwidth=0, 
                                    highlightthickness=0, insertbackground=self.C_TEXT_MAIN, justify="center")
        self.scale_entry.insert(0, str(self.SCALE))
        self.scale_entry.pack(side=tk.LEFT, padx=5, pady=8)
        self.scale_entry.bind("<Return>", self.apply_settings)

        tk.Label(left_box, text="RATIO:", fg=self.C_TEXT_DIM, bg=self.C_TOPBAR_BG, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(5, 0))
        self.ratio_entry = tk.Entry(left_box, width=4, bg=self.C_ENTRY_BG, fg=self.C_TEXT_MAIN, borderwidth=0, 
                                    highlightthickness=0, insertbackground=self.C_TEXT_MAIN, justify="center")
        self.ratio_entry.insert(0, str(self.STRETCH_Y))
        self.ratio_entry.pack(side=tk.LEFT, padx=5, pady=8)
        self.ratio_entry.bind("<Return>", self.apply_settings)

        tk.Label(left_box, text="W:", fg=self.C_ACCENT, bg=self.C_TOPBAR_BG, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(5, 0))
        self.w_entry = tk.Entry(left_box, width=3, bg=self.C_ENTRY_BG, fg=self.C_TEXT_MAIN, bd=0, highlightthickness=0, justify="center")
        self.w_entry.insert(0, str(self.work_w))
        self.w_entry.pack(side=tk.LEFT, padx=2)

        tk.Label(left_box, text="H:", fg=self.C_ACCENT, bg=self.C_TOPBAR_BG, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(2, 0))
        self.h_entry = tk.Entry(left_box, width=3, bg=self.C_ENTRY_BG, fg=self.C_TEXT_MAIN, bd=0, highlightthickness=0, justify="center")
        self.h_entry.insert(0, str(self.work_h))
        self.h_entry.pack(side=tk.LEFT, padx=2)
        
        q_frame = tk.Frame(left_box, bg=self.C_TOPBAR_BG)
        q_frame.pack(side=tk.LEFT, padx=10)
        
        quick_dims = ["7*16", "10*16", "6*8", "3*5"]
        for dim in quick_dims:
            w, h = map(int, dim.split('*'))
            btn = tk.Button(q_frame, text=dim, bg=self.C_BTN_DARK, fg=self.C_BTN_TEXT, font=("Arial", 8, "bold"),
                             relief="flat", bd=0, width=5,
                             command=lambda _w=w, _h=h, _d=dim: self.set_quick_dim(_w, _h, _d))
            btn.pack(side=tk.LEFT, padx=1)
            self.quick_buttons[dim] = btn

        self.btn_reset = tk.Button(left_box, text="RESET", bg=self.C_BTN_DARK, fg=self.C_ACCENT, font=("Arial", 8, "bold"),
                                    relief="flat", bd=0, command=self.reset_dims, width=6)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        center_box = tk.Frame(top, bg=self.C_TOPBAR_BG)
        center_box.place(relx=0.5, rely=0.5, anchor="center")
        
        self.btn_lgrid = tk.Button(center_box, text="L-GRID", bg=self.C_BTN_DARK, fg=self.C_BTN_TEXT, font=("Arial", 8, "bold"),
                                    relief="flat", bd=0, command=self.toggle_line_grid, padx=5)
        self.btn_lgrid.pack(side=tk.LEFT, padx=5)

        self.pos_label = tk.Label(center_box, text="POS: 0,0", fg=self.C_TEXT_MAIN, bg=self.C_TOPBAR_BG, font=("Consolas", 11, "bold"))
        self.pos_label.pack(side=tk.LEFT, padx=10)
        self.line_label = tk.Label(center_box, text="LINE: ---", fg=self.C_TEXT_MAIN, bg=self.C_TOPBAR_BG, font=("Consolas", 10, "bold"))
        self.line_label.pack(side=tk.LEFT, padx=10)
        self.btn_clear = tk.Button(center_box, text="CLEAN CANVAS", bg=self.C_BTN_DANGER, fg="white", font=("Arial", 9, "bold"), 
                                    relief="flat", command=self.clear_all, padx=10, bd=0)
        self.btn_clear.pack(side=tk.LEFT)

        right_box = tk.Frame(top, bg=self.C_TOPBAR_BG)
        right_box.pack(side=tk.RIGHT, padx=10)
        
        self.btn_palette = tk.Button(right_box, text="🎨", bg=self.C_ENTRY_BG, fg="white", width=3, relief="flat", bd=0,
                                     command=self.choose_custom_color)
        self.btn_palette.pack(side=tk.LEFT, padx=2)

        for t_name in ['B', 'O', 'W']:
            btn_c = self.themes[t_name]['bg']
            b = tk.Button(right_box, text=t_name, bg=self.C_ENTRY_BG, fg=btn_c, width=3, relief="flat", bd=0,
                          font=("Arial", 10, "bold"), command=lambda x=t_name: self.set_theme(x))
            b.pack(side=tk.LEFT, padx=2)
            self.theme_buttons[t_name] = b

        self.btn_inv = tk.Button(right_box, text="INV", bg=self.C_MENU_ACTIVE, fg="white", font=("Arial", 9, "bold"), 
                                 relief="flat", command=self.toggle_invert, width=5, bd=0)
        self.btn_inv.pack(side=tk.LEFT, padx=10)

        main_cont = tk.Frame(self, bg=self.C_WINDOW_BG)
        main_cont.pack(fill=tk.BOTH, expand=True)

        canv_container = tk.Frame(main_cont, bg=self.C_WINDOW_BG)
        canv_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.h_scroll = tk.Scrollbar(canv_container, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(canv_container, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(canv_container, highlightthickness=0, bg=self.C_CANVAS_BG, bd=0,
                                xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)

        self.sidebar = tk.Frame(main_cont, bg=self.C_SIDEBAR_BG, width=500)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        var_top_frame = tk.Frame(self.sidebar, bg=self.C_SIDEBAR_BG)
        var_top_frame.pack(fill=tk.X, padx=15, pady=(15,0))
        
        tk.Label(var_top_frame, text="NAME (VAR):", fg=self.C_TEXT_MAIN, bg=self.C_SIDEBAR_BG, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # --- ПАНЕЛЬ MULTI С ПОЛЕМ ПРОБЕЛА ---
        self.btn_multi = tk.Button(var_top_frame, text="MULTI", bg=self.C_BTN_DARK, fg=self.C_BTN_TEXT, font=("Arial", 8, "bold"),
                                    relief="flat", bd=0, command=self.toggle_multi, padx=10)
        self.btn_multi.pack(side=tk.RIGHT)
        
        self.spacing_entry = tk.Entry(var_top_frame, width=3, bg=self.C_ENTRY_BG, fg=self.C_TEXT_MAIN, bd=0, highlightthickness=0, justify="center")
        self.spacing_entry.insert(0, "1")
        self.spacing_entry.pack(side=tk.RIGHT, padx=5)
        tk.Label(var_top_frame, text="SPACE:", fg=self.C_TEXT_DIM, bg=self.C_SIDEBAR_BG, font=("Arial", 8)).pack(side=tk.RIGHT)

        self.var_entry = tk.Entry(self.sidebar, bg=self.C_ENTRY_BG, font=("Consolas", 12), insertbackground=self.C_TEXT_MAIN, 
                                  borderwidth=0, highlightthickness=0)
        self.var_entry.insert(0, "indicator_x")
        self.var_entry.pack(padx=15, pady=5, fill=tk.X)

        self.input_text = tk.Text(self.sidebar, height=8, bg=self.C_ENTRY_BG, fg=self.C_TEXT_MAIN, font=("Consolas", 11), 
                                  insertbackground=self.C_TEXT_MAIN, highlightthickness=0, borderwidth=0)
        self.input_text.pack(padx=15, pady=5, fill=tk.X)
        self.input_text.bind("<<Paste>>", lambda e: self.after(50, self.parse_and_draw))

        gen_frame = tk.Frame(self.sidebar, bg=self.C_SIDEBAR_BG)
        gen_frame.pack(padx=15, pady=10, fill=tk.X)
        
        self.btn_hex = tk.Button(gen_frame, text="HEX", fg="black", bd=0, font=("Arial", 10, "bold"), command=lambda: self.crop_and_generate("HEX"))
        self.btn_hex.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        self.btn_status = tk.Button(gen_frame, text="STATUS", fg="black", bd=0, font=("Arial", 10, "bold"), command=lambda: self.crop_and_generate("STATUS"))
        self.btn_status.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.btn_bin = tk.Button(gen_frame, text="BINARY", fg="black", bd=0, font=("Arial", 10, "bold"), command=lambda: self.crop_and_generate("BIN"))
        self.btn_bin.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))

        self.output_text = tk.Text(self.sidebar, bg=self.C_ENTRY_BG, fg=self.C_TEXT_MAIN, font=("Consolas", 11), borderwidth=0, highlightthickness=0)
        self.output_text.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)

        self.btn_copy = tk.Button(self.sidebar, text="COPY CODE", fg="black", font=("Arial", 11, "bold"), command=self.copy_to_clip, relief="flat", height=2, bd=0)
        self.btn_copy.pack(padx=15, pady=10, fill=tk.X)
        
        self.action_buttons = [self.btn_hex, self.btn_status, self.btn_bin, self.btn_copy]

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Motion>", self.update_pos)
        self.canvas.bind("<B1-Motion>", lambda e: self.paint(e, 1))
        self.canvas.bind("<Button-3>", lambda e: self.paint(e, 0))
        self.canvas.bind("<B3-Motion>", lambda e: self.paint(e, 0))
        
        self.bind("<KeyPress-w>", lambda e: self.set_theme('W'))
        self.bind("<KeyPress-o>", lambda e: self.set_theme('O'))
        self.bind("<KeyPress-b>", lambda e: self.set_theme('B'))
        self.bind("<KeyPress-i>", lambda e: self.toggle_invert())
        self.bind("<KeyPress-c>", lambda e: self.clear_all())
        
        # --- ГОРЯЧАЯ КЛАВИША ОТМЕНЫ ---
        self.bind("<Control-z>", self.undo)
        
        for widget in (self.input_text, self.output_text, self.var_entry):
            widget.bind("<Button-3>", self.show_menu)
        self.set_theme('O')

    def toggle_line_grid(self):
        self.show_line_grid = not self.show_line_grid
        self.btn_lgrid.config(bg=self.themes[self.current_theme]['bg'] if self.show_line_grid else self.C_BTN_DARK,
                              fg="black" if self.show_line_grid else self.C_BTN_TEXT)
        self.redraw_full()

    def toggle_multi(self):
        self.multi_mode = not self.multi_mode
        if self.multi_mode:
            self.btn_multi.config(bg=self.C_ACCENT, fg="black")
            self.parse_and_draw()
        else:
            self.btn_multi.config(bg=self.C_BTN_DARK, fg=self.C_BTN_TEXT)
            self.pending_chars = None

    def create_context_menu(self):
        self.menu = tk.Menu(self, tearoff=0, bg=self.C_MENU_BG, fg=self.C_TEXT_MAIN, activebackground=self.C_MENU_ACTIVE)
        self.menu.add_command(label="Копировать", command=lambda: self.focus_get().event_generate("<<Copy>>"))
        self.menu.add_command(label="Вставить", command=lambda: self.focus_get().event_generate("<<Paste>>"))
        self.menu.add_command(label="Вырезать", command=lambda: self.focus_get().event_generate("<<Cut>>"))
        self.menu.add_separator()
        self.menu.add_command(label="Очистить", command=self.menu_clear)

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def menu_clear(self):
        w = self.focus_get()
        if isinstance(w, tk.Text): w.delete("1.0", tk.END)
        elif isinstance(w, tk.Entry): w.delete(0, tk.END)

    def set_theme(self, theme): 
        self.current_theme = theme
        t = self.themes[theme]
        color = t['bg']
        if theme != 'CUSTOM': self.btn_palette.config(bg=self.C_ENTRY_BG)
        self.var_entry.config(fg=color)
        for name, btn in self.theme_buttons.items():
            if name == theme: btn.config(bg=color, fg="black")
            else: btn.config(bg=self.C_ENTRY_BG, fg=self.themes[name]['bg'])
        for key, btn in self.quick_buttons.items():
            if btn.cget("bg") != self.C_BTN_DARK: btn.config(bg=color)
        for b in self.action_buttons:
            b.config(bg=color, fg="black", activebackground=self.C_MENU_ACTIVE, activeforeground=color)
        if self.show_line_grid: self.btn_lgrid.config(bg=color)
        self.btn_reset.config(fg=color)
        self.btn_clear.config(bg=color, fg="black") 
        self.redraw_full()

    def apply_settings(self, event=None):
        try:
            self.SCALE = max(1, int(self.scale_entry.get()))
            self.STRETCH_Y = max(0.1, float(self.ratio_entry.get()))
            self.work_w = max(1, min(self.WIDTH, int(self.w_entry.get())))
            self.work_h = max(1, min(self.HEIGHT, int(self.h_entry.get())))
            self.redraw_full()
            self.focus_set()
        except ValueError: pass

    def on_zoom(self, event):
        mx, my = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        old_scale = self.SCALE
        if event.delta > 0: self.SCALE = min(60, self.SCALE + 2)
        else: self.SCALE = max(2, self.SCALE - 2)
        if old_scale == self.SCALE: return
        self.scale_entry.delete(0, tk.END); self.scale_entry.insert(0, str(self.SCALE))
        self.redraw_full()
        ratio = self.SCALE / old_scale
        self.canvas.xview_moveto((mx * ratio - event.x) / (self.WIDTH * self.SCALE))
        self.canvas.yview_moveto((my * ratio - event.y) / (self.HEIGHT * self.SCALE * self.STRETCH_Y))

    def redraw_full(self):
        cw = (self.work_w + self.PADDING * 2) * self.SCALE
        ch = int((self.work_h + self.PADDING * 2) * self.SCALE * self.STRETCH_Y)
        self.canvas.update()
        v_w, v_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, max(cw, v_w), max(ch, v_h)))
        dx = max(0, (v_w - cw) // 2) if v_w > 1 else 0
        dy = max(0, (v_h - ch) // 2) if v_h > 1 else 0
        self.canvas_offset = (dx, dy)
        t = self.themes[self.current_theme]; bg_c = t["inv_bg"] if self.inverted else t["bg"]
        grid_c = self.adjust_color(bg_c, self.INV_GRID_BRIGHTNESS if self.inverted else self.GRID_BRIGHTNESS)
        self.canvas.create_rectangle(dx, dy, dx + cw, dy + ch, fill=bg_c, outline="", tags="bg")
        px_off, py_off = dx + self.PADDING * self.SCALE, dy + int(self.PADDING * self.SCALE * self.STRETCH_Y)
        
        if self.SCALE >= 4:
            for i in range(self.work_w + 1):
                x = px_off + i * self.SCALE
                self.canvas.create_line(x, py_off, x, py_off + int(self.work_h * self.SCALE * self.STRETCH_Y), fill=grid_c, tags="grid")
            for j in range(self.work_h + 1):
                y = py_off + int(j * self.SCALE * self.STRETCH_Y)
                self.canvas.create_line(px_off, y, px_off + self.work_w * self.SCALE, y, fill=grid_c, tags="grid")
        
        if self.show_line_grid:
            l_color = self.adjust_color(grid_c, 1.5 if self.inverted else 0.5)
            for j in range(0, self.work_h + 1, 8):
                y = py_off + int(j * self.SCALE * self.STRETCH_Y)
                self.canvas.create_line(px_off, y, px_off + self.work_w * self.SCALE, y, fill=l_color, width=2, tags="line_grid")
        
        for x in range(self.WIDTH):
            for y in range(self.HEIGHT):
                if self.pixels[x][y]: self.refresh_px(x, y)

    def refresh_px(self, x, y):
        tag = f"p_{x}_{y}"
        self.canvas.delete(tag)
        if not self.pixels[x][y]: return
        t = self.themes[self.current_theme]; px_c = t["bg"] if self.inverted else t["px"]
        dx, dy = getattr(self, 'canvas_offset', (0,0))
        off_x, off_y = self.get_offsets()
        if off_x <= x < off_x + self.work_w and off_y <= y < off_y + self.work_h:
            rel_x, rel_y = x - off_x, y - off_y
            px_off, py_off = dx + self.PADDING * self.SCALE, dy + int(self.PADDING * self.SCALE * self.STRETCH_Y)
            x1, y1 = px_off + rel_x * self.SCALE, py_off + int(rel_y * self.SCALE * self.STRETCH_Y)
            x2, y2 = px_off + (rel_x + 1) * self.SCALE, py_off + int((rel_y + 1) * self.SCALE * self.STRETCH_Y)
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=px_c, outline="", tags=tag)
            self.canvas.tag_raise("grid"); self.canvas.tag_raise("line_grid")

    def on_canvas_click(self, event):
        self.focus_set()
        ex, ey = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        dx, dy = self.canvas_offset
        px_off, py_off = dx + self.PADDING * self.SCALE, dy + int(self.PADDING * self.SCALE * self.STRETCH_Y)
        rel_x, rel_y = int((ex - px_off) // self.SCALE), int((ey - py_off) // (self.SCALE * self.STRETCH_Y))
        off_x, off_y = self.get_offsets()
        x, y = rel_x + off_x, rel_y + off_y
        
        if self.line_just_finished:
            self.line_label.config(text="LINE: ---"); self.line_just_finished = False

        if self.multi_mode and self.pending_chars:
            self.save_history()
            try:
                space = int(self.spacing_entry.get())
            except: space = 1
            
            cur_x = x
            for vals, cw, ch in self.pending_chars:
                # Рисуем конкретный символ
                for i in range(len(vals)):
                    byte_val = vals[i]
                    page_off = (i // cw) * 8
                    col_x = cur_x + (i % cw)
                    for b in range(8):
                        if (byte_val >> b) & 1:
                            tx, ty = col_x, y + page_off + b
                            if 0 <= tx < self.WIDTH and 0 <= ty < self.HEIGHT:
                                self.pixels[tx][ty] = 1
                                self.refresh_px(tx, ty)
                # Сдвигаем X на ширину символа + пробел
                cur_x += cw + space
            
            self.canvas.update_idletasks()
            return

        if event.state & 0x0001: # SHIFT
            if self.line_start: 
                self.save_history()
                self.draw_line(self.line_start[0], self.line_start[1], x, y)
                self.line_just_finished = True; self.line_start = None 
            if self.phantom_line: self.canvas.delete(self.phantom_line)
        else: 
            self.line_start = (x, y)
            self.line_label.config(text=f"LINE: {x},{y} -> ...")
            self.paint(event, 1)

    def on_release(self, event): pass 

    def update_pos(self, event):
        ex, ey = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        dx, dy = self.canvas_offset
        px_off, py_off = dx + self.PADDING * self.SCALE, dy + int(self.PADDING * self.SCALE * self.STRETCH_Y)
        rel_x, rel_y = int((ex - px_off) // self.SCALE), int((ey - py_off) // (self.SCALE * self.STRETCH_Y))
        off_x, off_y = self.get_offsets()
        x, y = rel_x + off_x, rel_y + off_y
        if 0 <= rel_x < self.work_w and 0 <= rel_y < self.work_h:
            self.pos_label.config(text=f"POS: {x},{y}")
            if (event.state & 0x0001) and self.line_start:
                if self.phantom_line: self.canvas.delete(self.phantom_line)
                self.line_label.config(text=f"LINE: {self.line_start[0]},{self.line_start[1]} -> {x},{y}")
                t = self.themes[self.current_theme]; color = t["bg"] if self.inverted else t["px"]
                mx, my = self.SCALE // 2, int(self.SCALE * self.STRETCH_Y) // 2
                lx_s = px_off + (self.line_start[0]-off_x)*self.SCALE + mx
                ly_s = py_off + int((self.line_start[1]-off_y)*self.SCALE*self.STRETCH_Y) + my
                lx_e = px_off + rel_x*self.SCALE + mx
                ly_e = py_off + int(rel_y*self.SCALE*self.STRETCH_Y) + my
                self.phantom_line = self.canvas.create_line(lx_s, ly_s, lx_e, ly_e, fill=color, dash=(4, 4))

    def paint(self, event, mode):
        ex, ey = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        dx, dy = self.canvas_offset
        px_off, py_off = dx + self.PADDING * self.SCALE, dy + int(self.PADDING * self.SCALE * self.STRETCH_Y)
        rel_x, rel_y = int((ex - px_off) // self.SCALE), int((ey - py_off) // (self.SCALE * self.STRETCH_Y))
        if 0 <= rel_x < self.work_w and 0 <= rel_y < self.work_h:
            off_x, off_y = self.get_offsets(); x, y = rel_x + off_x, rel_y + off_y
            if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
                if self.pixels[x][y] != mode: 
                    self.save_history() # СОХРАНЯЕМ ПЕРЕД КАЖДЫМ НОВЫМ ПИКСЕЛЕМ (ИЛИ МАЛКОМ)
                    self.pixels[x][y] = mode; self.refresh_px(x, y)

    def draw_line(self, x0, y0, x1, y1):
        line_dx, line_dy = abs(x1-x0), abs(y1-y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = line_dx - line_dy; off_x, off_y = self.get_offsets()
        while True:
            if off_x <= x0 < off_x + self.work_w and off_y <= y0 < off_y + self.work_h:
                if 0 <= x0 < self.WIDTH and 0 <= y0 < self.HEIGHT: self.pixels[x0][y0] = 1; self.refresh_px(x0, y0)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 > -line_dy: err -= line_dy; x0 += sx
            if e2 < line_dx: err += line_dx; y0 += sy

    def clear_all(self):
        self.save_history() # СОХРАНЯЕМ ПЕРЕД ОЧИСТКОЙ
        self.pixels = [[0 for _ in range(self.HEIGHT)] for _ in range(self.WIDTH)]
        self.input_text.delete("1.0", tk.END); self.line_label.config(text="LINE: ---"); self.redraw_full()

    def copy_to_clip(self):
        self.clipboard_clear(); self.clipboard_append(self.output_text.get("1.0", tk.END).strip())
        self.btn_copy.config(text="COPY OK!"); self.after(1000, lambda: self.btn_copy.config(text="COPY CODE"))

    def toggle_invert(self):
        self.inverted = not self.inverted; self.redraw_full()

    def parse_and_draw(self, event=None):
        raw = self.input_text.get("1.0", tk.END)
        
        # 1. Вытаскиваем имя переменной (информативно)
        var_match = re.search(r'/\s*([a-zA-Z0-9_]+)\s*/', raw) or \
                    re.search(r'gStatusLine\[\s*([a-zA-Z0-9_]+)', raw) or \
                    re.search(r'([a-zA-Z0-9_]+)\s*\[', raw)
        if var_match: 
            self.var_entry.delete(0, tk.END)
            self.var_entry.insert(0, var_match.group(1))

        # 2. Ищем блоки данных
        char_blocks = re.findall(r'\{([^{}]+)\}', raw)
        
        if self.multi_mode:
            # --- РЕЖИМ MULTI: Только собираем данные, холст НЕ ТРОГАЕМ ---
            chars_found = []
            blocks_to_process = char_blocks if char_blocks else [raw]
            
            for block in blocks_to_process:
                found_hex = re.findall(r'0x[0-9A-Fa-f]{2}', block)
                found_bin = re.findall(r'0b[01]{8}', block)
                vals = [int(h, 16) for h in found_hex] if found_hex else [int(b, 2) for b in found_bin]
                
                if vals:
                    # Авто-определение размеров для каждого символа в очереди
                    cw = len(vals) if len(vals) <= 12 else len(vals) // 2
                    ch = 8 if len(vals) <= 12 else 16
                    chars_found.append((vals, cw, ch))
            
            self.pending_chars = chars_found
            # Никаких redraw_full() и затирания пикселей здесь нет!
        else:
            # --- ОБЫЧНЫЙ РЕЖИМ: Старое доброе поведение ---
            clean_raw = re.sub(r'/\*.*?\*/', '', raw)
            hxs = re.findall(r'0x[0-9A-Fa-f]{2}', clean_raw)
            bins = re.findall(r'0b[01]{8}', clean_raw)
            all_vals = [int(h, 16) for h in hxs] if hxs else [int(b, 2) for b in bins]
            
            if all_vals:
                total = len(all_vals)
                if total == 14: cw, ch = 7, 16
                elif total == 20: cw, ch = 10, 16
                else: cw, ch = (total, 8) if total <= 12 else (total // 2, 16)
                
                self.save_history()
                self.work_w, self.work_h = cw, ch
                self.w_entry.delete(0, tk.END); self.w_entry.insert(0, str(cw))
                self.h_entry.delete(0, tk.END); self.h_entry.insert(0, str(ch))
                
                # Очищаем и центрируем
                self.pixels = [[0 for _ in range(self.HEIGHT)] for _ in range(self.WIDTH)]
                sx, sy = self.get_offsets()
                for i in range(len(all_vals)):
                    page_off = (i // cw) * 8 if ch > 8 else 0
                    col_x = i % cw
                    for b in range(8):
                        if (all_vals[i] >> b) & 1: 
                            tx, ty = sx + col_x, sy + page_off + b
                            if tx < self.WIDTH and ty < self.HEIGHT: self.pixels[tx][ty] = 1
                self.redraw_full()

    def crop_and_generate(self, mode):
        raw_template = self.input_text.get("1.0", tk.END).strip()
        clean_tmp = re.sub(r'/\*.*?\*/', '', raw_template)
        hxs_in, bins_in = re.findall(r'0x[0-9A-Fa-f]{2}', clean_tmp), re.findall(r'0b[01]{8}', clean_tmp)
        
        if hxs_in or bins_in:
            found_vals = hxs_in if hxs_in else bins_in
            l = len(found_vals)
            if l == 14: cw, ch = 7, 16
            elif l == 20: cw, ch = 10, 16
            elif l == 6: cw, ch = 6, 8
            else: cw, ch = (l, 8) if l < 10 else (l//2, 16)
            sx, sy = self.get_offsets(); data = []; pages = 1 if ch <= 8 else 2
            for p in range(pages):
                for x_rel in range(cw):
                    byte, tx, ty_base = 0, sx + x_rel, sy + (p * 8)
                    for b in range(8):
                        ty = ty_base + b
                        if 0 <= tx < self.WIDTH and 0 <= ty < self.HEIGHT and self.pixels[tx][ty]: byte |= (1 << b)
                    data.append(byte)
        else:
            min_x, max_x, min_y, max_y, found_px = self.WIDTH, -1, self.HEIGHT, -1, False
            for x in range(self.WIDTH):
                for y in range(self.HEIGHT):
                    if self.pixels[x][y]: min_x, max_x, min_y, max_y, found_px = min(min_x, x), max(max_x, x), min(min_y, y), max(max_y, y), True
            if not found_px: return
            cw, ch_raw = max_x - min_x + 1, max_y - min_y + 1
            pages, data = (1 if ch_raw <= 8 else 2), []
            for p in range(pages):
                for x in range(min_x, max_x + 1):
                    byte = 0
                    for b in range(8):
                        cy = min_y + (p * 8) + b
                        if cy < self.HEIGHT and self.pixels[x][cy]: byte |= (1 << b)
                    data.append(byte)

        self.output_text.delete("1.0", tk.END)
        v_name = self.var_entry.get().strip() or "indicator_x"
        if mode == "STATUS":
            res = [f"gStatusLine[{v_name} + {i}] |= 0x{b:02X};" for i, b in enumerate(data)]
            self.output_text.insert("1.0", "\n".join(res))
        else:
            fmt = "0x{:02X}" if mode == "HEX" else "0b{:08b}"
            pattern = r'0x[0-9A-Fa-f]{2}' if mode == "HEX" else r'0b[01]{8}'
            matches = list(re.finditer(pattern, raw_template))
            if matches and "gStatusLine" not in raw_template:
                t_list = list(raw_template)
                for i in range(min(len(matches), len(data)) - 1, -1, -1):
                    m = matches[i]; t_list[m.start():m.end()] = list(fmt.format(data[i]))
                self.output_text.insert("1.0", "".join(t_list))
            else:
                if mode == "HEX": self.output_text.insert("1.0", "{" + ", ".join([fmt.format(b) for b in data]) + "}")
                else: self.output_text.insert("1.0", ", ".join([fmt.format(b) for b in data]))

if __name__ == "__main__":
    OuroMasterEditor().mainloop()