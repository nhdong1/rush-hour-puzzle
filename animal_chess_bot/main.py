#!/usr/bin/env python3
"""
Animal Chess Bot - Cờ Thú Tự Động

Bot tự động chơi game Cờ Thú cho phe xanh trên giả lập Android.

Sử dụng:
    python main.py

Yêu cầu:
    - Python 3.8+
    - Windows OS
    - Các dependencies trong requirements.txt
"""

import os
import sys


def get_base_path():
    """Get base path for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_PATH = get_base_path()
if BASE_PATH not in sys.path:
    sys.path.insert(0, BASE_PATH)


def main():
    """Main entry point"""
    from gui.main_window import MainWindow
    
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
