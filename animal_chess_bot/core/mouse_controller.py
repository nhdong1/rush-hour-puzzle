import pyautogui
import time
import random
import ctypes
from ctypes import wintypes

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
MK_LBUTTON = 0x0001

user32 = ctypes.windll.user32


class MouseController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        self.click_delay = 0.05
        self.move_duration = 0.1
        self.randomize = True
        self.use_virtual = True

    def set_click_delay(self, delay: float):
        self.click_delay = delay

    def set_move_duration(self, duration: float):
        self.move_duration = duration

    def set_randomize(self, randomize: bool):
        self.randomize = randomize

    def set_virtual_mode(self, enabled: bool):
        self.use_virtual = enabled

    def click(self, x: int, y: int):
        if self.use_virtual:
            self._virtual_click(x, y)
        else:
            self._real_click(x, y)

    def double_click(self, x: int, y: int):
        if self.use_virtual:
            self._virtual_double_click(x, y)
        else:
            self._real_double_click(x, y)

    def _real_click(self, x: int, y: int):
        if self.randomize:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)

        pyautogui.moveTo(x, y, duration=self.move_duration)
        time.sleep(self.click_delay)
        pyautogui.click(x, y)

    def _real_double_click(self, x: int, y: int):
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

    def _make_lparam(self, x: int, y: int):
        return (y << 16) | (x & 0xFFFF)

    def _get_window_at(self, x: int, y: int):
        return user32.WindowFromPoint(wintypes.POINT(x, y))

    def _virtual_click(self, x: int, y: int, hwnd=None):
        if self.randomize:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)

        if hwnd is None:
            hwnd = self._get_window_at(x, y)

        point = wintypes.POINT(x, y)
        user32.ScreenToClient(hwnd, ctypes.byref(point))

        lparam = self._make_lparam(point.x, point.y)

        user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        time.sleep(self.click_delay)
        user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)

    def _virtual_double_click(self, x: int, y: int, hwnd=None):
        if self.randomize:
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)

        if hwnd is None:
            hwnd = self._get_window_at(x, y)

        point = wintypes.POINT(x, y)
        user32.ScreenToClient(hwnd, ctypes.byref(point))

        lparam = self._make_lparam(point.x, point.y)

        user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        time.sleep(self.click_delay)
        user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)
        time.sleep(0.05)
        user32.PostMessageW(hwnd, WM_LBUTTONDBLCLK, MK_LBUTTON, lparam)
        time.sleep(self.click_delay)
        user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)

    def click_cell(self, cell_info: dict, region_offset: tuple):
        if cell_info is None:
            return False

        center_x = cell_info["center_x"]
        center_y = cell_info["center_y"]

        abs_x = region_offset[0] + center_x
        abs_y = region_offset[1] + center_y

        self.click(abs_x, abs_y)
        return True
