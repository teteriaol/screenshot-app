import tkinter as tk
from tkinter import filedialog
from tkinter import colorchooser
from PIL import ImageGrab, ImageTk, Image, ImageEnhance, ImageOps
import keyboard
from tktooltip import ToolTip
import io
import win32clipboard


class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.canvas = None
        self.frame_canvas = None

        self.frame_canvas_x = None
        self.frame_canvas_y = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.line_x = None
        self.line_y = None

        self.rect = None
        self.rect_size = None

        self.frame = None
        self.frame_image = None 

        self.app = self
        self.button_panel = None
        self.buttons = {}

        self.color = '#ff0000'
        self.mode = None

        self.last_actions = []

        keyboard.on_press_key("snapshot", self.create_canvas)

        self.cursor_size = 10

        self.cursor_circle = None
        self.entry = None
        self.line = None


    def create_canvas(self, event=None):
        if self.canvas is None:
            self.root.attributes('-alpha', 0)
            self.screenshot = ImageGrab.grab(bbox=(0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
            self.dark_screenshot = self.screenshot.copy()
            self.enhancer = ImageEnhance.Brightness(self.dark_screenshot)
            self.dark_screenshot = self.enhancer.enhance(0.3)
            self.screenshot_tk = ImageTk.PhotoImage(self.dark_screenshot)
            self.canvas = tk.Canvas(self.root, width=self.dark_screenshot.width, height=self.dark_screenshot.height, highlightthickness=0)            
            self.canvas.pack()
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)

            self.root.bind("<Control-a>", self.select_all)
            self.root.bind("<KeyRelease-p>", self.pop_up)
            self.root.bind('<Escape>', self.close)
            self.root.bind("<Control-z>", self.undo)
            self.root.bind("<Control-c>", self.copy_file)
            self.root.bind("<Control-plus>", self.increase_cursor_size)
            self.root.bind("<Control-minus>", self.decrease_cursor_size)

            self.canvas.bind("<Button-1>", self.on_press)
            self.canvas.bind("<B1-Motion>", self.on_move)
            self.canvas.bind("<ButtonRelease-1>", self.on_release)
            self.canvas.bind("<Motion>", self.motion)
  
            self.root.attributes("-topmost", True)
            self.root.attributes("-topmost", False)
            self.root.attributes('-alpha', 1)


    def exit(self, event=None):
        self.root.quit()
        self.root.update()


    def undo(self, event=None):
        if self.last_actions:
            self.last_actions.pop()
            self.redraw()


    def toggle_mode(self, mode, cursor):
        self.mode = mode
        if cursor:
            self.root.config(cursor=cursor)
        else:
            self.root.config(cursor='arrow')
        if self.cursor_circle:
            self.canvas.delete(self.cursor_circle)
        if self.entry:
            self.canvas.delete(self.entry)


    def close(self, event=None):
        if not self.entry:
            self.root.attributes('-alpha', 0)
            self.root.geometry('+0+0')
            if self.canvas:
                self.canvas.destroy()
            if self.frame_canvas:
                self.frame_canvas.destroy()
            if self.button_panel:
                self.button_panel.destroy()
            self.__init__(self.root)
        else:
            self.entry.destroy()
            self.entry = None


    def resize_check(self, event):
        x, y = event.x, event.y
        corner_size = 20
        canvas_width = self.frame_canvas.winfo_width()
        canvas_height = self.frame_canvas.winfo_height()

        if x >= canvas_width - corner_size and y >= canvas_height - corner_size:
            self.frame_canvas.config(cursor="size_nw_se")
        else:
            self.frame_canvas.config(cursor="fleur")

    def delete(self, x, y):

        trashcan = []
        delete_radius = self.cursor_size // 2

        for element in self.last_actions:
            if element[0][-1] == "text":
                ex, ey, text, color, _ = element[0]
                if abs(ex - x) < delete_radius and abs(ey - y) < delete_radius:
                    trashcan.append(element)
            elif element[0][-1] == 'line':
                ex1, ey1, ex2, ey2, width, color, _ = element[0]
                line_length = ((ex2 - ex1) ** 2 + (ey2 - ey1) ** 2) ** 0.5
                distance = abs((ey2 - ey1) * x - (ex2 - ex1) * y + ex2 * ey1 - ey2 * ex1) / line_length
                if distance < delete_radius:
                    trashcan.append(element)
            else:
                for dot in element:
                    ex, ey, color, size = dot
                    if abs(ex - x) < delete_radius and abs(ey - y) < delete_radius:
                        trashcan.append(element)
                        break

        for item in trashcan:
            self.last_actions.remove(item)
        self.redraw()
    

    def on_press(self, event):
        if not self.mode:
            self.canvas.delete("all")
            self.rect_size = None
            self.dark_screenshot = self.enhancer.enhance(0.3)
            self.screenshot_tk = ImageTk.PhotoImage(self.dark_screenshot)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)
            self.start_x = event.x
            self.start_y = event.y
            if self.button_panel:
                self.button_panel.destroy()
        elif self.mode == 'text':
            if self.entry:
                self.entry.destroy()
            self.entry = tk.Entry(self.root, font=('Arial', self.cursor_size), fg=self.color)
            self.entry.config(insertbackground=self.color)
            self.entry.place(x=event.x, y=event.y, width=100)
            self.entry.focus()
            self.entry.bind("<Return>", self.insert_text)
        elif self.mode == 'line':
            if self.line is None:
                self.line_x = event.x
                self.line_y = event.y
            else:
                self.line = None
        elif self.mode == 'delete':
            self.delete(event.x, event.y)
        elif self.mode == 'drawing':
            self.last_actions.append([(event.x, event.y, self.color, self.cursor_size)])
            self.last_draw = (event.x, event.y)


    def on_move(self, event):
        if not self.mode:
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)  
            if self.rect:
                self.canvas.delete(self.rect)
            self.end_x = event.x
            self.end_y = event.y
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="white", width=3, dash=(10, 5))
            self.rect_size = f'{abs(self.end_x-self.start_x)}x{abs(self.end_y-self.start_y)}'
            if min(self.start_y, self.end_y) > 20:
                self.canvas.create_text(max(self.start_x-25, self.end_x-25), min(self.end_y-15, self.start_y-15), text=self.rect_size, fill='white')
            else: 
                self.canvas.create_text(max(self.start_x-40, self.end_x-40), min(self.end_y+15, self.start_y+15), text=self.rect_size, fill='white')
        elif self.mode == 'drawing':
            self.last_actions[-1].append((event.x, event.y, self.color, self.cursor_size))
            self.canvas.create_line(self.last_draw[0], self.last_draw[1], event.x, event.y, fill=self.color, width=self.cursor_size, capstyle=tk.ROUND, smooth=tk.TRUE)
            self.last_draw = (event.x, event.y)
        elif self.mode == 'delete':
            self.delete(event.x, event.y)
        elif self.mode == 'line':
            if self.line_x is not None and self.line_y is not None:
                if self.line is not None:
                    self.canvas.delete(self.line)
                self.line = self.canvas.create_line(self.line_x, self.line_y, event.x, event.y, fill=self.color, width=self.cursor_size)


    def on_release(self, event):
        if not self.mode:
            if self.rect:
                self.canvas.delete(self.rect)
            self.end_x = event.x
            self.end_y = event.y
            end_x, end_y = event.x, event.y
            box = (min(self.start_x, end_x), min(self.start_y, end_y), max(self.start_x, end_x), max(self.start_y, end_y))
            cropped_image = self.screenshot.crop(box)
            self.dark_screenshot.paste(cropped_image, box)
            self.screenshot_tk = ImageTk.PhotoImage(self.dark_screenshot)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)
            self.canvas.image = self.screenshot_tk

            self.rect = self.canvas.create_rectangle(self.start_x - 3, self.start_y - 3, self.end_x + 3, self.end_y + 3, outline="white", width=3, dash=(10, 5))
            self.rect_size = f'{abs(self.end_x-self.start_x)}x{abs(self.end_y-self.start_y)}'
            if min(self.start_y, self.end_y) > 20:
                self.canvas.create_text(max(self.start_x-25, self.end_x-25), min(self.end_y-15, self.start_y-15), text=self.rect_size, fill='white')
            else:
                self.canvas.create_text(max(self.start_x-40, self.end_x-40), min(self.end_y+15, self.start_y+15), text=self.rect_size, fill='white')
            self.show_button_panel()
        elif self.mode == 'line':
            self.last_actions.append([(self.line_x, self.line_y, event.x, event.y, self.cursor_size, self.color, 'line')])
            self.line = None
            self.line_x = None
            self.line_y = None


    def insert_text(self, event):
        text = self.entry.get()
        x = self.entry.winfo_x()
        y = self.entry.winfo_y()
        self.canvas.create_text(x, y, text=text,
                                anchor='nw',
                                font=('Arial', self.cursor_size),
                                fill=self.color)
        self.last_actions.append([(x, y, text, self.color, "text")])
        self.entry.destroy()
        self.entry = None


    def select_all(self, event):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)
        if self.rect:
            self.canvas.delete(self.rect)
        self.start_x, self.start_y = 0, 0
        self.end_x, self.end_y = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.rect = self.canvas.create_rectangle(self.start_x+5, self.start_y+5, self.end_x-5, self.end_y-5, 
                                                outline="white",
                                                width=3,
                                                dash=(10, 5))
        self.rect_size = f'{abs(self.end_x-self.start_x)}x{abs(self.end_y-self.start_y)}'
        self.canvas.create_text(self.start_x+25, self.start_y-15, self.rect_size)
        box = (3,
               3,
               self.dark_screenshot.width-3, 
               self.dark_screenshot.height-3)
        cropped_image = self.screenshot.crop(box)
        self.dark_screenshot.paste(cropped_image, box)
        self.screenshot_tk = ImageTk.PhotoImage(self.dark_screenshot)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)
        self.canvas.image = self.screenshot_tk
        self.rect = self.canvas.create_rectangle(3, 3, self.dark_screenshot.width-3, self.dark_screenshot.height-3, outline="white", width=3, dash=(10, 5))

        self.show_button_panel()


    def pop_up(self, event=None):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
          
            self.root.attributes('-alpha', 0)
            self.frame_image = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            self.frame = ImageTk.PhotoImage(self.frame_image)
            if self.canvas:
                self.canvas.destroy()
            self.frame_canvas = tk.Canvas(self.root, width=self.frame.width(), height=self.frame.height(), highlightthickness=0.5)
            self.frame_canvas.pack()
            self.frame_canvas.create_image(0, 0, anchor=tk.NW, image=self.frame)
            self.root.attributes("-topmost", True)

            self.frame_canvas.bind("<Enter>", self.frame_on_enter)
            self.frame_canvas.bind("<Leave>", self.frame_on_leave)
            self.frame_canvas.bind("<Button-1>", self.frame_on_press)
            self.frame_canvas.bind("<B1-Motion>", self.frame_on_move)
            self.frame_canvas.bind("<ButtonRelease-1>", self.frame_on_release)
            self.frame_canvas.bind("<Motion>", self.resize_check)

            self.close_button = tk.Button(self.frame_canvas, image=self.button_images['Close'], command=self.close)
            self.root.attributes('-alpha', 1)
            self.close_button.bind("<Enter>", self.on_enter_button)
            self.close_button.bind("<Leave>", self.on_leave_button)
            self.redraw()


    def save_file(self, event=None):
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPG files", "*.jpg"), ("All files", "*.*")])
        if file_path:
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
            image = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            image.save(file_path, "JPEG")
            self.close()

    def copy_file(self, event=None):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)

            cropped_image = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            output = io.BytesIO()
            cropped_image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            self.close()

            

    def show_button_panel(self):
        if self.button_panel:
            self.button_panel.destroy()
        self.button_panel = tk.Frame(self.root, bg='#e1e1e1')
        x = min(self.start_x+160, self.end_x+160)
        y = min(self.start_y, self.end_y)
        if y-71 <= 75:
            self.button_panel.place(x=x, y=y, anchor="ne")
        else:
            self.button_panel.place(x=x-5, y=y-71, anchor="ne")
        self.button_images = {}


        buttons = [
            ('Draw', 'icons/pencil.jpg', lambda: self.toggle_mode('drawing', None)),
            ('Text', 'icons/text.jpg', lambda: self.toggle_mode('text', 'xterm')),
            ('Line', 'icons/line.jpg', lambda: self.toggle_mode('line', None)),
            ('Delete', 'icons/delete.jpg', lambda: self.toggle_mode('delete', None)), 
            ('color', 'color', self.choose_color),
            ('Close', 'icons/close.jpg', self.close),
            ('Undo', 'icons/undo.jpg', self.undo),
            ('Save', 'icons/save.jpg', self.save_file),
            ('Pop Up', 'icons/pop-up.jpg', self.pop_up),
            ('Copy', 'icons/copy.jpg', self.copy_file),
        ]

        row = 0
        col = 0
        image_size = (20, 20)

        for name, path, command in buttons:
            if col >= 5:
                row += 1
                col = 0

            if path != 'color':
                image = Image.open(path)
                image = image.resize(image_size, Image.LANCZOS)
                inverted_image = ImageOps.invert(image.convert("RGB"))
                enhancer = ImageEnhance.Contrast(inverted_image)
                enhanced_image = enhancer.enhance(10.0)
                tk_image = ImageTk.PhotoImage(enhanced_image)
                self.button_images[name] = tk_image
                button = tk.Button(self.button_panel, image=tk_image, command=command, width=20, height=20)
            else:
                tk_image = None
                button = tk.Button(self.button_panel, image=tk_image, command=command, width=2, height=1)
            button.grid(row=row, column=col, padx=3, pady=3)
            self.buttons[name] = button
            col += 1
            ToolTip(button, msg=name, delay=0.5)

        self.buttons['color'].config(bg=self.color)

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Choose a color")
        if color_code:
            chosen_color = color_code[1]
            self.color = chosen_color
            self.buttons['color'].config(bg=self.color)

    def frame_on_enter(self, event):
        if self.mode != 'resizing':
            self.close_button.place(x=self.frame_canvas.winfo_width() - 30, y=5)

    def frame_on_leave(self, event):
        self.close_button.place_forget()

    def on_enter_button(self, event):
        self.close_button.config(cursor="hand2")

    def on_leave_button(self, event):
        self.close_button.config(cursor="")

    def frame_on_press(self, event):
        self.frame_canvas_x = event.x
        self.frame_canvas_y = event.y

    def frame_on_move(self, event):
        if self.frame_canvas.cget('cursor') == 'fleur':
            x = self.root.winfo_x() + (event.x - self.frame_canvas_x)
            y = self.root.winfo_y() + (event.y - self.frame_canvas_y)
            self.root.geometry(f'+{x}+{y}')
        elif self.frame_canvas.cget('cursor') != 'fleur':
            self.resizing = 'resizing'
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            new_w = abs(event.x)
            new_h = abs(event.y)
            if new_w >= 100 and new_h >= 100:
                self.root.geometry(f'{new_w}x{new_h}+{x}+{y}')
                self.frame_canvas.config(width=new_w, height=new_h)
                if self.frame_image: 
                    resized_image = self.frame_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    self.frame = ImageTk.PhotoImage(resized_image)
                    self.frame_canvas.create_image(0, 0, anchor=tk.NW, image=self.frame)

    def frame_on_release(self, event):
        self.frame_canvas_x = None
        self.frame_canvas_y = None
        self.mode = None

    def redraw(self):
        canvas = self.frame_canvas if self.frame_canvas else self.canvas
        if not canvas:
            return

        canvas.delete("all")
        image = self.frame if self.frame_canvas else self.screenshot_tk
        canvas.create_image(0, 0, anchor=tk.NW, image=image)

        if not self.frame_canvas:
            self.rect = canvas.create_rectangle(
                self.start_x - 3, self.start_y - 3,
                self.end_x + 3, self.end_y + 3,
                outline="white", width=3, dash=(10, 5)
            )
            if self.rect_size:
                canvas.create_text(
                    max(self.start_x - 15, self.end_x - 15),
                    min(self.start_y - 15, self.end_y - 15),
                    text=self.rect_size, fill='white'
                )

        for elem in self.last_actions:
            if elem[0][-1] == "text":
                x, y, text, color, _ = elem[0]
                canvas.create_text(
                    x - self.start_x if self.frame_canvas else x,
                    y - self.start_y if self.frame_canvas else y,
                    text=text, fill=color, font=("Arial", self.cursor_size)
                )
            elif elem[0][-1] == 'line':
                x, y, x1, y1, width, color, _ = elem[0]
                canvas.create_line(
                    x - self.start_x if self.frame_canvas else x,
                    y - self.start_y if self.frame_canvas else y,
                    x1 - self.start_x if self.frame_canvas else x1,
                    y1 - self.start_y if self.frame_canvas else y1,
                    width=width, fill=color
                )
            else:
                for i in range(1, len(elem)):
                    x1, y1, color, size = elem[i - 1]
                    x2, y2, _, _ = elem[i]
                    canvas.create_line(
                        x1 - self.start_x if self.frame_canvas else x1,
                        y1 - self.start_y if self.frame_canvas else y1,
                        x2 - self.start_x if self.frame_canvas else x2,
                        y2 - self.start_y if self.frame_canvas else y2,
                        fill=color, width=size, capstyle=tk.ROUND, smooth=tk.TRUE
                    )


    def motion(self, event):
        if self.mode == 'drawing':
            if self.cursor_circle:
                self.canvas.delete(self.cursor_circle)
            self.cursor_circle = self.canvas.create_oval(event.x - self.cursor_size // 2, event.y - self.cursor_size // 2, event.x + self.cursor_size // 2, event.y + self.cursor_size // 2, fill=self.color)

    def increase_cursor_size(self, event):
        self.cursor_size += 2
        if self.mode == 'drawing':
            if self.cursor_circle:
                self.canvas.delete(self.cursor_circle)
            self.cursor_circle = self.canvas.create_oval(event.x - self.cursor_size // 2, event.y - self.cursor_size // 2, event.x + self.cursor_size // 2, event.y + self.cursor_size // 2, fill=self.color)

    def decrease_cursor_size(self, event):
        self.cursor_size = max(2, self.cursor_size - 2)
        if self.mode == 'drawing':
            if self.cursor_circle:
                self.canvas.delete(self.cursor_circle)
            self.cursor_circle = self.canvas.create_oval(event.x - self.cursor_size // 2, event.y - self.cursor_size // 2, event.x + self.cursor_size // 2, event.y + self.cursor_size // 2, fill=self.color)
   
