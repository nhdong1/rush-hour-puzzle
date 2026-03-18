Game giải đố loại cờ vua bằng html và js với những yêu cầu sau:

1. Bàn cờ là 1 lưới ô vuông 8x8 ô
2. Gồm các quân cờ vua
3. Luật chơi:
   - Đây là trò chơi theo lượt giữa người và máy. Bắt đầu chơi, 1 quân xe sẽ đặt ngẫu nhiên trên bàn cờ, người chơi có vai trò di chuyển quân xe này để ăn các quân cờ khác hoặc né tránh để không bị quân cờ khác ăn. Mục tiêu ăn quân cờ khác để kiếm điểm hoặc sống sót lâu hơn. Còn máy có vai trò di chuyển quân cờ của máy hoặc đặt thêm các quân cờ khác nhau, mục đích là ăn được quân xe của người chơi và kết thúc trò chơi.

   - Mô tả chi tiết:
     - Lượt đầu tiên, 1 quân xe được đặt ngẫu nhiên trên bàn cờ, và người chơi được phép di chuyển quân cờ này. Ở lượt này bàn cơ chưa có thêm quân cờ nào khác

     - Lượt 2, máy đặt ngẫu nhiên 1 hoặc 2 quân trong các quân cờ sau: tốt, tượng, mã

     - Từ lượt 3 trở đi, sẽ có 1 số ngẫu nhiên X có ý nghĩa: sau X lượt chơi, máy sẽ đặt thêm 1 hoặc 2 quân ngẫu nhiên trong: tốt, tượng, mã, xe, hậu, vua.

     - Trò chơi kết thúc khi người chơi bị ăn mất quân xe.

     - Các quân tượng, mã, xe, hậu, vua có cách đi và cách ăn như theo luật cờ vua. Quân tốt mỗi lượt có thể di chuyển theo 4 hướng trên dưới trái phải và ăn theo 4 hướng chéo tương ứng.
