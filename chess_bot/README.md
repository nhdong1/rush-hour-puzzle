# Chess Bot - Auto Player

Bot tự động chơi game cờ puzzle trên giả lập Android (LDPlayer).

## Yêu cầu

- Python 3.8+
- Windows OS
- LDPlayer hoặc giả lập Android khác

## Cài đặt

```bash
cd chess_bot
pip install -r requirements.txt
```

## Sử dụng

### 1. Chạy bot

```bash
python main.py
```

### 2. Cấu hình (Tab Setup)

1. **Chọn vùng game**: Click "Select Game Region" và kéo chọn vùng bàn cờ trên màn hình
2. **Pick màu ô cờ**: 
   - Click "Pick Color" cho ô sáng -> Click vào ô sáng trên game
   - Click "Pick Color" cho ô tối -> Click vào ô tối trên game
3. **Chọn vị trí nút Hồi sinh** (tùy chọn): Click "Select Revive Button Position" -> Click vào nút hồi sinh trên game
4. Click "Save Configuration" để lưu

### 3. Thêm template quân cờ

Để bot nhận diện quân cờ chính xác, bạn cần thêm hình ảnh mẫu vào thư mục `templates/`:

- `rook_white.png` - Quân Xe trắng (người chơi)
- `pawn_black.png` - Quân Tốt đen
- `bishop_black.png` - Quân Tượng đen
- `knight_black.png` - Quân Mã đen
- `rook_black.png` - Quân Xe đen
- `queen_black.png` - Quân Hậu đen
- `king_black.png` - Quân Vua đen

**Cách tạo template:**
1. Chụp screenshot game
2. Cắt hình quân cờ (chỉ lấy phần quân cờ, không lấy nền)
3. Lưu vào thư mục `templates/` với tên tương ứng

### 4. Chạy bot (Tab Control)

1. Điều chỉnh tốc độ di chuyển (Move delay)
2. Bật/tắt Auto revive nếu cần
3. Click "Start" để bắt đầu
4. Click "Pause" để tạm dừng
5. Click "Stop" để dừng hoàn toàn

### 5. Xem log (Tab Log)

- Xem lịch sử các nước đi
- Xuất log ra file nếu cần

## Cấu trúc thư mục

```
chess_bot/
├── main.py              # Entry point
├── config.py            # Quản lý cấu hình
├── requirements.txt     # Dependencies
├── gui/                 # Giao diện
│   ├── main_window.py
│   ├── setup_tab.py
│   ├── control_tab.py
│   ├── log_tab.py
│   ├── region_selector.py
│   └── color_picker.py
├── core/                # Logic chính
│   ├── screen_capture.py
│   ├── board_detector.py
│   ├── piece_detector.py
│   ├── ai_player.py
│   └── mouse_controller.py
└── templates/           # Hình ảnh mẫu quân cờ
```

## Chiến lược AI

Bot sử dụng các tiêu chí sau để chọn nước đi:

1. **Tránh ô nguy hiểm** (ưu tiên cao nhất)
2. **Ăn quân có điểm cao** (Vua > Hậu > Xe > Tượng/Mã > Tốt)
3. **Ưu tiên ăn an toàn** (không bị ăn lại)
4. **Giữ nhiều đường thoát**
5. **Ưu tiên vị trí trung tâm**
6. **Tránh lặp lại vị trí**

## Lưu ý

- Đảm bảo cửa sổ game không bị che khuất
- Điều chỉnh color tolerance nếu nhận diện không chính xác
- Thêm đủ template quân cờ để bot hoạt động tốt
- Có thể cần điều chỉnh threshold trong piece_detector.py nếu nhận diện sai
