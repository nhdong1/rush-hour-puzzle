# Animal Chess Bot - Cờ Thú Tự Động

Bot tự động chơi game Cờ Thú (Animal Chess) cho phe xanh trên giả lập Android.

## Yêu cầu

- Python 3.8+
- Windows OS
- LDPlayer hoặc giả lập Android khác

## Cài đặt

```bash
cd animal_chess_bot
pip install -r requirements.txt
```

## Sử dụng

### 1. Chạy bot

```bash
python main.py
```

### 2. Cấu hình (Tab Cài đặt)

1. **Chọn vùng game**: Click "Chọn vùng chơi" và kéo chọn vùng bàn cờ 4x4 trên màn hình
2. **Pick màu ô cờ**: Click "Chọn màu" và click vào một ô cờ trên game
3. Click "Lưu cấu hình" để lưu

### 3. Thêm template quân cờ

Để bot nhận diện quân cờ chính xác, bạn cần thêm hình ảnh mẫu vào thư mục `templates/`:

**Quân xanh:**
- `mouse_blue.png`, `cat_blue.png`, `dog_blue.png`, `fox_blue.png`
- `wolf_blue.png`, `tiger_blue.png`, `lion_blue.png`, `elephant_blue.png`

**Quân đỏ:**
- `mouse_red.png`, `cat_red.png`, `dog_red.png`, `fox_red.png`
- `wolf_red.png`, `tiger_red.png`, `lion_red.png`, `elephant_red.png`

**Trạng thái ô:**
- `unflipped.png` - Ô chưa lật

**Cách tạo template:**
1. Trong ứng dụng, vào tab "Cài đặt"
2. Click "📷 Chụp Template"
3. Chọn loại template và chụp vùng màn hình

### 4. Chạy bot (Tab Điều khiển)

1. Điều chỉnh tốc độ di chuyển (Move delay)
2. Click "Bắt đầu" hoặc nhấn F5 để bắt đầu
3. Click "Tạm dừng" hoặc nhấn F6 để tạm dừng
4. Click "Dừng" hoặc nhấn F7 để dừng hoàn toàn

### 5. Xem trước Detection (Tab Xem trước)

- Click "📷 Chụp một lần" để xem kết quả nhận diện
- Bật "Xem trực tiếp" để theo dõi liên tục

### 6. Xem log (Tab Nhật ký)

- Xem lịch sử các nước đi
- Xuất log ra file nếu cần

## Cấu trúc thư mục

```
animal_chess_bot/
├── main.py              # Entry point
├── config.py            # Quản lý cấu hình
├── requirements.txt     # Dependencies
├── gui/                 # Giao diện
│   ├── main_window.py
│   ├── setup_tab.py
│   ├── control_tab.py
│   ├── log_tab.py
│   ├── preview_tab.py
│   ├── region_selector.py
│   ├── color_picker.py
│   ├── condition_editor.py
│   └── template_capture.py
├── core/                # Logic chính
│   ├── screen_capture.py
│   ├── board_detector.py
│   ├── cell_detector.py
│   ├── piece_detector.py
│   ├── ai_player.py
│   ├── button_detector.py
│   └── mouse_controller.py
└── templates/           # Hình ảnh mẫu quân cờ
```

## Luật chơi Cờ Thú

### Bàn cờ
- Lưới 4x4 với 16 ô
- 2 phe: Xanh (người chơi) và Đỏ (đối thủ)
- 8 loại quân mỗi phe

### Sức mạnh quân cờ

| Quân | Điểm | Ghi chú |
|------|------|---------|
| Chuột | 1 | Ăn được Voi! |
| Mèo | 2 | |
| Chó | 3 | |
| Cáo | 4 | |
| Sói | 5 | |
| Hổ | 6 | |
| Sư tử | 7 | |
| Voi | 8 | Không ăn được Chuột |

### Quy tắc
1. Phe xanh đi trước
2. Bắt đầu: tất cả ô đều chưa lật
3. Click ô chưa lật → lật lên, xuất hiện quân ngẫu nhiên
4. Click quân xanh → chọn quân để di chuyển
5. Di chuyển: 4 hướng (trên/dưới/trái/phải), 1 ô mỗi lượt
6. Ăn quân: quân mạnh hơn hoặc bằng ăn được quân yếu hơn
7. Đặc biệt: Chuột ăn được Voi, Voi không ăn được Chuột
8. Khi 2 quân bằng sức mạnh: cả 2 biến mất, điểm vẫn được tính
9. Kết thúc: sau 40 lượt hoặc 1 phe hết quân

## Chiến lược AI

Bot sử dụng thuật toán Minimax với Alpha-Beta Pruning để:

1. **Tính trước 3 bước** - Đánh giá kết quả sau 3 nước đi
2. **Phân loại nước đi** - An toàn vs Nguy hiểm
3. **Ưu tiên an toàn** - Chọn nước không bị ăn lại trước
4. **Tối ưu điểm** - Ăn quân có điểm cao nhất khi an toàn
5. **Tránh thiệt điểm** - Không ăn quân nếu bị ăn lại với thiệt hại lớn hơn

## Điều kiện Auto Click

Chức năng tự động click khi phát hiện template (popup, button):

1. Vào tab "Cài đặt"
2. Click "➕ Thêm điều kiện"
3. Chụp template trigger (ví dụ: popup kết thúc game)
4. Thêm chuỗi click (vị trí các nút cần click)
5. Lưu điều kiện

## Lưu ý

- Đảm bảo cửa sổ game không bị che khuất
- Điều chỉnh color tolerance nếu nhận diện không chính xác
- Thêm đủ template quân cờ để bot hoạt động tốt
- Sử dụng chế độ "Không chiếm chuột" để vẫn dùng được chuột khi bot chạy

## Hotkeys

- **F5**: Bắt đầu
- **F6**: Tạm dừng / Tiếp tục
- **F7**: Dừng
