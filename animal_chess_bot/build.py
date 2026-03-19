#!/usr/bin/env python3
"""
Build script to create standalone executable for Animal Chess Bot
"""

import subprocess
import sys
import os
import shutil


def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_exe():
    """Build the executable using PyInstaller"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    templates_dir = os.path.join(script_dir, "templates")
    icon_path = os.path.join(script_dir, "icon.ico")
    
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    pyinstaller_args = [
        "pyinstaller",
        "--name=AnimalChessBot",
        "--onefile",
        "--windowed",
        "--noconfirm",
        f"--add-data={templates_dir};templates",
        "--hidden-import=pynput.keyboard._win32",
        "--hidden-import=pynput.mouse._win32",
        "--collect-all=pynput",
    ]
    
    if os.path.exists(icon_path):
        pyinstaller_args.append(f"--icon={icon_path}")
    
    pyinstaller_args.append(main_script)
    
    print("Building executable...")
    print(f"Command: {' '.join(pyinstaller_args)}")
    
    subprocess.check_call(pyinstaller_args, cwd=script_dir)
    
    dist_dir = os.path.join(script_dir, "dist")
    exe_path = os.path.join(dist_dir, "AnimalChessBot.exe")
    
    if os.path.exists(exe_path):
        print(f"\nBuild successful!")
        print(f"Executable location: {exe_path}")
        
        release_dir = os.path.join(script_dir, "release")
        if os.path.exists(release_dir):
            shutil.rmtree(release_dir)
        os.makedirs(release_dir)
        
        shutil.copy(exe_path, release_dir)
        
        templates_dest = os.path.join(release_dir, "templates")
        if os.path.exists(templates_dir):
            shutil.copytree(templates_dir, templates_dest)
        else:
            os.makedirs(templates_dest)
        
        readme_content = """# Animal Chess Bot - Cờ Thú Tự Động

## Hướng dẫn sử dụng

1. Chạy file AnimalChessBot.exe
2. Tab Cài đặt:
   - Click "Chọn vùng chơi" để chọn vùng bàn cờ 4x4
   - Click "Chọn màu" để chọn màu ô cờ
   - Click "Lưu cấu hình" để lưu
3. Tab Điều khiển:
   - F5: Bắt đầu bot
   - F6: Tạm dừng/Tiếp tục
   - F7: Dừng bot

## Thêm template quân cờ

Để bot nhận diện quân cờ chính xác, thêm hình ảnh vào thư mục templates/:

Quân xanh (phe người chơi):
- mouse_blue.png (Chuột xanh - sức mạnh 1)
- cat_blue.png (Mèo xanh - sức mạnh 2)
- dog_blue.png (Chó xanh - sức mạnh 3)
- fox_blue.png (Cáo xanh - sức mạnh 4)
- wolf_blue.png (Sói xanh - sức mạnh 5)
- tiger_blue.png (Hổ xanh - sức mạnh 6)
- lion_blue.png (Sư tử xanh - sức mạnh 7)
- elephant_blue.png (Voi xanh - sức mạnh 8)

Quân đỏ (phe đối thủ):
- mouse_red.png, cat_red.png, dog_red.png, fox_red.png
- wolf_red.png, tiger_red.png, lion_red.png, elephant_red.png

Trạng thái ô:
- unflipped.png (Ô chưa lật)

## Quy tắc sức mạnh

Chuột (1) > Voi (8) - Quy tắc đặc biệt!
Voi (8) > Sư tử (7) > Hổ (6) > Sói (5) > Cáo (4) > Chó (3) > Mèo (2) > Chuột (1)

- Quân mạnh hơn hoặc bằng ăn được quân yếu hơn
- Chuột có thể ăn Voi, nhưng Voi không thể ăn Chuột
- Khi 2 quân bằng sức mạnh ăn nhau, cả 2 đều biến mất

## Lưu ý

- Chạy với quyền Administrator nếu gặp lỗi
- Đảm bảo cửa sổ game không bị che khuất
- Sử dụng chế độ "Không chiếm chuột" để vẫn dùng được chuột khi bot chạy
"""
        with open(os.path.join(release_dir, "README.txt"), "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        print(f"\nRelease folder created: {release_dir}")
        print("Contents:")
        for item in os.listdir(release_dir):
            print(f"  - {item}")
    else:
        print("Build failed - executable not found")
        return False
    
    return True


def clean_build():
    """Clean build artifacts"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["AnimalChessBot.spec"]
    
    for dir_name in dirs_to_remove:
        dir_path = os.path.join(script_dir, dir_name)
        if os.path.exists(dir_path):
            print(f"Removing {dir_path}")
            shutil.rmtree(dir_path)
    
    for file_name in files_to_remove:
        file_path = os.path.join(script_dir, file_name)
        if os.path.exists(file_path):
            print(f"Removing {file_path}")
            os.remove(file_path)
    
    print("Clean complete")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "clean":
            clean_build()
            return
        elif sys.argv[1] == "help":
            print("Usage:")
            print("  python build.py        - Build executable")
            print("  python build.py clean  - Clean build artifacts")
            print("  python build.py help   - Show this help")
            return
    
    install_pyinstaller()
    build_exe()


if __name__ == "__main__":
    main()
