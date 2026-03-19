# Templates cho Animal Chess Bot

Thư mục này chứa các hình ảnh mẫu để bot nhận diện quân cờ và các nút bấm.

## Danh sách Template cần có

### Quân cờ phe Xanh (Blue)
- `mouse_blue.png` - Chuột xanh (sức mạnh 1)
- `cat_blue.png` - Mèo xanh (sức mạnh 2)
- `dog_blue.png` - Chó xanh (sức mạnh 3)
- `fox_blue.png` - Cáo xanh (sức mạnh 4)
- `wolf_blue.png` - Sói xanh (sức mạnh 5)
- `tiger_blue.png` - Hổ xanh (sức mạnh 6)
- `lion_blue.png` - Sư tử xanh (sức mạnh 7)
- `elephant_blue.png` - Voi xanh (sức mạnh 8)

### Quân cờ phe Đỏ (Red)
- `mouse_red.png` - Chuột đỏ (sức mạnh 1)
- `cat_red.png` - Mèo đỏ (sức mạnh 2)
- `dog_red.png` - Chó đỏ (sức mạnh 3)
- `fox_red.png` - Cáo đỏ (sức mạnh 4)
- `wolf_red.png` - Sói đỏ (sức mạnh 5)
- `tiger_red.png` - Hổ đỏ (sức mạnh 6)
- `lion_red.png` - Sư tử đỏ (sức mạnh 7)
- `elephant_red.png` - Voi đỏ (sức mạnh 8)

### Trạng thái ô
- `unflipped.png` - Ô chưa lật (mặt sau của quân cờ)

### Templates cho Auto Click (tùy chọn)
- `popup_*.png` - Các popup cần tự động click
- `button_*.png` - Các nút bấm cần tự động click

## Cách tạo Template

### Sử dụng công cụ trong ứng dụng

1. Mở ứng dụng Animal Chess Bot
2. Vào tab **Cài đặt**
3. Click nút **📷 Chụp Template**
4. Chọn loại template từ dropdown
5. Click **Chụp vùng màn hình**
6. Kéo chọn vùng chứa quân cờ/nút bấm
7. Click **Lưu Template**

### Tạo thủ công

1. Chụp screenshot game
2. Cắt hình quân cờ (chỉ lấy phần quân cờ, không lấy nền)
3. Lưu vào thư mục `templates/` với tên tương ứng
4. Định dạng: PNG (khuyến nghị), JPG

## Lưu ý quan trọng

1. **Kích thước template**: Nên giữ kích thước gốc của quân cờ trong game
2. **Nền trong suốt**: Nếu có thể, sử dụng nền trong suốt (PNG)
3. **Chất lượng**: Hình ảnh rõ nét, không bị mờ
4. **Độ chính xác**: Cắt sát viền quân cờ để tăng độ chính xác nhận diện

## Quy tắc sức mạnh

```
Chuột (1) > Voi (8) - Quy tắc đặc biệt!
Voi (8) > Sư tử (7) > Hổ (6) > Sói (5) > Cáo (4) > Chó (3) > Mèo (2) > Chuột (1)
```

- Quân mạnh hơn hoặc bằng có thể ăn quân yếu hơn
- Ngoại lệ: Chuột có thể ăn Voi, nhưng Voi không thể ăn Chuột
- Khi 2 quân bằng sức mạnh ăn nhau, cả 2 đều biến mất nhưng điểm vẫn được tính
