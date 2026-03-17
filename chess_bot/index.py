#!/usr/bin/env python3
"""
Chess Bot - Auto player for Android chess puzzle game
"""

import sys
import os


def get_base_path():
    """Get base path for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_PATH = get_base_path()
sys.path.insert(0, BASE_PATH)

os.chdir(BASE_PATH)

from gui.main_window import MainWindow


def main():
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
