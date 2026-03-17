import tkinter as tk
from PIL import ImageGrab, ImageTk
import pyautogui


class ColorPicker:
    def __init__(self, callback, pick_position_only=False):
        self.callback = callback
        self.pick_position_only = pick_position_only
        
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor="crosshair")
        
        screenshot = ImageGrab.grab()
        self.screenshot = screenshot
        self.screenshot_image = ImageTk.PhotoImage(screenshot)
        
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.create_image(0, 0, image=self.screenshot_image, anchor=tk.NW)
        
        if pick_position_only:
            instruction = "Click to select position. Press ESC to cancel."
        else:
            instruction = "Click to pick color. Press ESC to cancel."
            
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            30,
            text=instruction,
            fill="white",
            font=("Arial", 16, "bold"),
            tags="instruction"
        )
        
        self.canvas.create_rectangle(
            self.root.winfo_screenwidth() // 2 - 150,
            15,
            self.root.winfo_screenwidth() // 2 + 150,
            45,
            fill="black",
            outline=""
        )
        self.canvas.tag_raise("instruction")
        
        self.zoom_size = 100
        self.zoom_factor = 8
        self.zoom_window = None
        self.zoom_image = None
        self.color_preview = None
        self.color_text = None
        
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.root.bind("<Escape>", self._on_cancel)
        
        self.root.focus_force()
        
    def _on_motion(self, event):
        x, y = event.x, event.y
        
        if self.zoom_window:
            self.canvas.delete(self.zoom_window)
        if self.zoom_image:
            self.canvas.delete(self.zoom_image)
        if self.color_preview:
            self.canvas.delete(self.color_preview)
        if self.color_text:
            self.canvas.delete(self.color_text)
            
        half_size = self.zoom_size // (2 * self.zoom_factor)
        crop_x1 = max(0, x - half_size)
        crop_y1 = max(0, y - half_size)
        crop_x2 = min(self.screenshot.width, x + half_size)
        crop_y2 = min(self.screenshot.height, y + half_size)
        
        cropped = self.screenshot.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        zoomed = cropped.resize(
            (self.zoom_size, self.zoom_size),
            resample=0
        )
        
        self.zoomed_photo = ImageTk.PhotoImage(zoomed)
        
        zoom_x = min(x + 20, self.root.winfo_screenwidth() - self.zoom_size - 20)
        zoom_y = min(y + 20, self.root.winfo_screenheight() - self.zoom_size - 60)
        
        if zoom_x < x + 20:
            zoom_x = x - self.zoom_size - 20
        if zoom_y < y + 20:
            zoom_y = y - self.zoom_size - 60
            
        self.zoom_window = self.canvas.create_rectangle(
            zoom_x - 2, zoom_y - 2,
            zoom_x + self.zoom_size + 2, zoom_y + self.zoom_size + 2,
            outline="white",
            width=2
        )
        
        self.zoom_image = self.canvas.create_image(
            zoom_x, zoom_y,
            image=self.zoomed_photo,
            anchor=tk.NW
        )
        
        center_x = zoom_x + self.zoom_size // 2
        center_y = zoom_y + self.zoom_size // 2
        cross_size = 5
        self.canvas.create_line(
            center_x - cross_size, center_y,
            center_x + cross_size, center_y,
            fill="red", width=2
        )
        self.canvas.create_line(
            center_x, center_y - cross_size,
            center_x, center_y + cross_size,
            fill="red", width=2
        )
        
        if not self.pick_position_only:
            try:
                pixel_color = self.screenshot.getpixel((x, y))
                if len(pixel_color) == 4:
                    pixel_color = pixel_color[:3]
                    
                hex_color = f"#{pixel_color[0]:02x}{pixel_color[1]:02x}{pixel_color[2]:02x}"
                
                self.color_preview = self.canvas.create_rectangle(
                    zoom_x, zoom_y + self.zoom_size + 5,
                    zoom_x + 30, zoom_y + self.zoom_size + 35,
                    fill=hex_color,
                    outline="white"
                )
                
                self.color_text = self.canvas.create_text(
                    zoom_x + 35, zoom_y + self.zoom_size + 20,
                    text=f"RGB: {pixel_color}",
                    fill="white",
                    font=("Arial", 10),
                    anchor=tk.W
                )
            except Exception:
                pass
                
    def _on_click(self, event):
        x, y = event.x, event.y
        
        self.root.destroy()
        
        if self.pick_position_only:
            self.callback((x, y))
        else:
            try:
                pixel_color = self.screenshot.getpixel((x, y))
                if len(pixel_color) == 4:
                    pixel_color = pixel_color[:3]
                self.callback(pixel_color)
            except Exception:
                self.callback(None)
                
    def _on_cancel(self, event):
        self.root.destroy()
        self.callback(None)
