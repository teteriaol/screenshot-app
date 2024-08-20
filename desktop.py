import tkinter as tk
from PIL import Image
import pystray
from pystray import MenuItem as item
import threading
from main import ScreenshotApp


def exit_app(icon, item):
    icon.stop()
    app.exit()


def icon_thread(icon):
    icon.run()


def about():
    about_window = tk.Toplevel()
    about_window.geometry('400x300')
    about_window.title('About')

    heading_label = tk.Label(about_window, text="Hotkeys", font=("Helvetica", 12, "bold"))
    heading_label.pack(pady=20)
    
    hotkeys = {
        'Prt Sc': 'General hotkey',
        'Ctrl+S': 'Save',
        'Ctrl+C': 'Copy',
        'Ctrl+A': 'Select All',
        'Ctrl+Z': 'Undo',
        'Ctrl+': 'Increase cursor size',
        'Ctrl-': 'Decrease cursor size',
        'Esc': 'Close',
        'P': 'Pop Up',
        'L': 'Line',
        'C': 'Color',
        'T': 'Text',
        'B': 'Brush',
        'D': 'Delete',
    }

    hotkeys_frame = tk.Frame(about_window)
    hotkeys_frame.pack(padx=10)

    for row, (key, value) in enumerate(hotkeys.items()):
        col = 0 if row < len(hotkeys) / 2 else 1
        display_row = row if col == 0 else row - len(hotkeys) // 2
        label_key = tk.Label(hotkeys_frame, text=f'{key}', font=('Helvetica', 10, 'bold'))
        label_value = tk.Label(hotkeys_frame, text=f' - {value}', font=('Helvetica', 10))
        label_key.grid(row=display_row, column=col * 2, sticky='w')
        label_value.grid(row=display_row, column=col * 2 + 1, sticky='w')

    ok_button = tk.Button(about_window, text="OK", command=about_window.destroy)
    ok_button.pack(pady=10)
    root.wait_window(about_window)


root = tk.Tk()
root.attributes('-alpha', 0)
root.overrideredirect(True)
app = ScreenshotApp(root)


image_path = 'icons/icon.png'
icon_image = Image.open(image_path)
icon = pystray.Icon("test_icon", icon_image)


icon.menu = pystray.Menu(
    item('Take a screenshot', lambda: root.after(0, app.create_canvas), default=True),
    item('About', lambda: root.after(0, about)),
    item('Exit', lambda: exit_app(icon, None)),
)


icon_thread = threading.Thread(target=icon_thread, args=(icon,))
icon_thread.start()


root.mainloop()
