Luyện Thi - Trắc nghiệm & Trả lời ngắn

Mô tả
- Web tĩnh nhỏ để luyện trắc nghiệm (MCQ) và xem đáp án ngắn cho các câu hỏi.
- Dữ liệu nằm ở `data/questions.json` (mẫu chứa vài câu). Bạn có thể mở rộng file JSON này.

Chạy
- Cách nhanh nhất: mở `index.html` bằng trình duyệt. Nhưng tùy trình duyệt, fetch từ `file://` có thể bị chặn. Nếu không thấy câu hỏi, chạy server tĩnh:

Windows PowerShell:

```powershell
cd c:\Training\LuyenEVR
python -m http.server 8000
# Mở http://localhost:8000 trong trình duyệt
```

Cập nhật dữ liệu
- Sửa `data/questions.json`. Mỗi mục là đối tượng với các trường: id, type ("mcq" hoặc "short"), question, choices (nếu mcq), answer (chỉ số lựa chọn đúng), shortAnswer (văn bản ngắn).

Yêu cầu tiếp theo
- Nếu bạn muốn, tôi có thể trích xuất toàn bộ các câu từ attachments và nhập tự động vào `data/questions.json`. Hãy xác nhận để tôi thực hiện.
