# Animal Chess Bot - Cờ Thú Tự Động

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
