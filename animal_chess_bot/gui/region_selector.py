import tkinter as tk
from PIL import ImageGrab, ImageTk


class RegionSelector:
    def __init__(self, callback):
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor="cross")
        
        screenshot = ImageGrab.grab()
        self.screenshot_image = ImageTk.PhotoImage(screenshot)
        
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            cursor="cross"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.create_image(0, 0, image=self.screenshot_image, anchor=tk.NW)
        
        overlay = self.canvas.create_rectangle(
            0, 0,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
            fill="black",
            stipple="gray50",
            outline=""
        )
        
        instruction_text = "Kéo để chọn vùng game. Nhấn ESC để hủy."
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            30,
            text=instruction_text,
            fill="white",
            font=("Arial", 16, "bold")
        )
        
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Escape>", self._on_cancel)
        
        self.root.focus_force()
        
    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline="red",
            width=2
        )
        
    def _on_drag(self, event):
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.start_x, self.start_y,
                event.x, event.y
            )
            
    def _on_release(self, event):
        end_x = event.x
        end_y = event.y
        
        self.root.destroy()
        
        if self.start_x is not None and self.start_y is not None:
            if abs(end_x - self.start_x) > 10 and abs(end_y - self.start_y) > 10:
                self.callback(self.start_x, self.start_y, end_x, end_y)
            else:
                self.callback(None, None, None, None)
                
    def _on_cancel(self, event):
        self.root.destroy()
        self.callback(None, None, None, None)
