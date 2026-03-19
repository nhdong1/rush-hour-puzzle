import numpy as np
from PIL import ImageGrab
import cv2


class ScreenCapture:
    def __init__(self, region):
        self.region = region
        
    def set_region(self, region):
        self.region = region
        
    def capture(self):
        if not self.region:
            return None
            
        try:
            x1, y1, x2, y2 = self.region
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame
        except Exception as e:
            print(f"Screen capture error: {e}")
            return None
            
    def capture_pil(self):
        if not self.region:
            return None
            
        try:
            x1, y1, x2, y2 = self.region
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            return screenshot
        except Exception as e:
            print(f"Screen capture error: {e}")
            return None
