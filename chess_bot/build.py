#!/usr/bin/env python3
"""
Build script to create standalone executable for Chess Bot
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
    main_script = os.path.join(script_dir, "index.py")
    templates_dir = os.path.join(script_dir, "templates")
    icon_path = os.path.join(script_dir, "icon.ico")
    
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    pyinstaller_args = [
        "pyinstaller",
        "--name=ChessBot",
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
    exe_path = os.path.join(dist_dir, "ChessBot.exe")
    
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
        
        readme_content = """# Chess Bot - Auto Player

## Hướng dẫn sử dụng

1. Chạy file ChessBot.exe
2. Tab Setup:
   - Click "Select Game Region" để chọn vùng bàn cờ
   - Click "Pick Color" để chọn màu ô sáng và ô tối
   - Click "Save Configuration" để lưu cấu hình
3. Tab Control:
   - F5: Start bot
   - F6: Pause/Resume bot
   - F7: Stop bot

## Thêm template quân cờ

Để bot nhận diện quân cờ chính xác, thêm hình ảnh vào thư mục templates/:
- rook_white.png (Xe trắng - quân của bạn)
- pawn_black.png (Tốt đen)
- bishop_black.png (Tượng đen)
- knight_black.png (Mã đen)
- rook_black.png (Xe đen)
- queen_black.png (Hậu đen)
- king_black.png (Vua đen)

## Lưu ý

- Chạy với quyền Administrator nếu gặp lỗi
- Đảm bảo cửa sổ game không bị che khuất
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
    files_to_remove = ["ChessBot.spec"]
    
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
