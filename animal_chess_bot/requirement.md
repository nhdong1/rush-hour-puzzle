Viết bot cho game Cờ thú

1. Thành phần bàn cờ:
   - Là lưới ô vuông 4x4 không liền mạch, giữa hàng và cột cách nhau một khoảng nhất định.
   - Có 2 phe, quân xanh và quân đỏ.
   - Gồm các quân xếp theo sức mạnh Chuột > Voi > Sư tử > Hổ > Sói > Cáo > Chó > Mèo > Chuột.
   - Điểm tương ứng cho các quân là từ 1 đến 8.
2. Luật chơi:
   - Đây là trò chơi theo lượt giữa phe xanh và phe đỏ, phe xanh bắt đầu trước
   - Bắt đầu chơi, trạng thái toàn bộ các ô đều chưa lật.
   - Khi click vào ô chưa lật, ô đó sẽ lật lên và xuất hiện ngẫu nhiên một trong các quân cờ của phe xanh hoặc phe đỏ.
   - Khi click vào ô đã lật là quân đỏ thì sẽ bỏ qua.
   - Khi click vào ô đã lật là quân xanh, thì phe xanh sẽ được di chuyển theo các hướng trên dưới trái phải 1 ô nếu các hướng đó trống. Nếu các hướng đó bị chặn, nếu là quân xanh hoặc quân đỏ mạnh hơn thì không thể di chuyển; Nếu là quân đỏ yếu hơn thì thay thế, nếu quân đỏ bằng sức mạnh thì cả 2 đều biến mất.
   - Mục tiêu ưu tiên cao nhất là kiếm được nhiều điểm nhất.
   - Bàn cờ kết thúc khi hết 40 lượt chơi hoặc 1 trong 2 phe không còn quân. Khi đó sẽ hiện popup kết thúc game.
3. Lưu ý:
   - Để di chuyển 1 quân thì cần click 1 lần vào quân đó và 1 lần ở ô liền kề và chỉ di chuyển quân xanh
   - Nếu ăn quân bằng sức mạnh, cả 2 cùng biến mất nhưng điểm sẽ được cộng cho người đi nước đó.
