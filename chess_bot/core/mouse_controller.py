import pyautogui
import time
import random


class MouseController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        self.click_delay = 0.05
        self.move_duration = 0.1
        self.randomize = True
        
    def set_click_delay(self, delay: float):
        self.click_delay = delay
        
    def set_move_duration(self, duration: float):
        self.move_duration = duration
        
    def set_randomize(self, randomize: bool):
        self.randomize = randomize
        
    def click(self, x: int, y: int):
        if self.randomize:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)
            
        pyautogui.moveTo(x, y, duration=self.move_duration)
        
        time.sleep(self.click_delay)
        
        pyautogui.click(x, y)
        
    def double_click(self, x: int, y: int):
        if self.randomize:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)
            
        pyautogui.moveTo(x, y, duration=self.move_duration)
        time.sleep(self.click_delay)
        pyautogui.doubleClick(x, y)
        
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int):
        pyautogui.moveTo(start_x, start_y, duration=self.move_duration)
        time.sleep(self.click_delay)
        pyautogui.drag(
            end_x - start_x,
            end_y - start_y,
            duration=self.move_duration * 2
        )
        
    def move_to(self, x: int, y: int):
        pyautogui.moveTo(x, y, duration=self.move_duration)
        
    def get_position(self):
        return pyautogui.position()
        
    def click_cell(self, cell_info: dict, region_offset: tuple):
        if cell_info is None:
            return False
            
        center_x = cell_info["center_x"]
        center_y = cell_info["center_y"]
        
        abs_x = region_offset[0] + center_x
        abs_y = region_offset[1] + center_y
        
        self.click(abs_x, abs_y)
        return True
