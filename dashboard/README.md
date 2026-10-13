# Dashboard M22 – khung giao diện

Khung dashboard cho đề M22 (CVAT Issue Analytics). Chưa có file thật nào thì mọi trang chạy trên
**dữ liệu giả** sinh từ bộ đáp án BDD100K trong `sample_data_output1/`. Pipeline xong chặng nào thì
thả bảng của chặng đó vào `dashboard/data_real/`, không phải sửa code giao diện.

## Chạy

Từ thư mục gốc của project:

```
pip install -r requirements.txt
streamlit run dashboard/app.py --server.address localhost
```

Cần `sample_data_output1/annotations.xml` (để sinh số giả) và `images.zip` (để hiện ảnh).
Đã kiểm tra với Python 3.13, Streamlit 1.55, Altair 6.0.

## Các trang

| Nhóm | Trang | Trả lời câu hỏi |
|---|---|---|
| Theo đề M22 | Tổng quan | Hai KPI của đề đang là bao nhiêu |
| | Top lỗi | Loại lỗi nào nhiều và lặp lại |
| | Class khó | Class nào khó, dính lỗi gì |
| | Annotator | Ai cần hỗ trợ, về lỗi gì |
| Chấm chéo | Annotator chấm annotator | Không có đáp án thì ai lệch khỏi nhóm |
| | Reviewer chấm annotator | Issue nhiều do annotator yếu hay reviewer khó |
| Đề xuất vs sửa | Reviewer yêu cầu vs annotator sửa | Annotator có sửa đúng điều được yêu cầu |
| | Agent đề xuất vs người áp dụng | Đề xuất của agent có đúng, người duyệt có lọc được cái sai |
| | Khuyến nghị vs kết quả pilot | Khuyến nghị nào được áp dụng, lỗi có giảm |
| Tra cứu | Chi tiết issue | Xem một issue: ảnh, comment, cách xử lý |
| | Nguồn dữ liệu | Chế độ đang chạy, bảng nào còn thiếu, bảng mã, hợp đồng cột |

## Cắm dữ liệu thật

Trang **Nguồn dữ liệu** là nơi tra cứu: trạng thái 12 bảng, bảng mã, cột của từng bảng, và nút
tải **bộ CSV mẫu** (12 bảng giả ở đúng dạng hợp đồng) để làm mẫu khi viết phần xuất của pipeline.

Ba quy tắc:

1. **Cột bắt buộc và cột tuỳ chọn.** Mỗi bảng chỉ cần đủ cột bắt buộc là được nhận. Ví dụ `issues`
   cần 13 cột có ngay sau chặng ingest; các cột của chặng sau (cờ lặp lại, nguồn được quy, kết quả
   sửa) bổ sung dần vào chính file đó. Phần giao diện nào cần cột chưa có thì ghi rõ còn chờ cột
   nào, của chặng nào.
2. **Dữ liệu ghi theo mã, không ghi nhãn tiếng Việt.** Ví dụ loại lỗi ghi `missing_object`, lần
   chạy ghi `batch2_control`. Giá trị ngoài bảng mã làm cả bảng bị từ chối, và trang Nguồn dữ liệu
   nêu đúng giá trị lạ. Cột đúng/sai nhận `true`/`false` hoặc `1`/`0`.
3. **Số thật và số giả không trộn.** Có ít nhất một file thật là dashboard chuyển sang chế độ thật:
   bảng nào chưa có thì để trống chứ không lấy số giả lấp vào. Muốn xem giao diện đầy đủ thì bật
   "Xem bằng dữ liệu giả" ở thanh bên; khi đó mọi bảng đều là số giả.

Đặt file ở `dashboard/data_real/<tên bảng>.csv` (hoặc `.parquet`), rồi tải lại trang. Muốn trỏ sang
thư mục khác, ví dụ thư mục xuất của pipeline, thì đặt biến môi trường `M22_REAL_DIR`.

Thứ tự nên nộp: `issues` cùng `workload` trước (bốn trang theo đề chạy được ngay), rồi các bảng so
khớp của chặng A, rồi `patches`, rồi `recommendations`.

## Sửa bảng mã và hợp đồng

- Đổi chữ hiện trên giao diện: sửa nhãn trong `settings.py`. Mã giữ nguyên.
- Thêm một mã mới (ví dụ một loại lỗi): thêm vào bảng `*_LABELS` tương ứng trong `settings.py`.
- Thêm cột hoặc đổi cột từ tuỳ chọn sang bắt buộc: sửa `data_layer/schema.py`.
- Trang dùng cột tuỳ chọn phải hỏi trước: `ui.ready(data, "Tiêu đề thẻ", issues=["tên_cột"])`
  cho một thẻ, hoặc khai báo `requires` trong `META` cho cả trang.

## Cấu trúc

```
dashboard/
  app.py              điểm vào: điều hướng, tiêu đề, hàng lọc, công tắc chế độ
  settings.py         đường dẫn, bảng mã và nhãn, ngưỡng
  data_layer/
    schema.py         hợp đồng 12 bảng: cột bắt buộc, cột tuỳ chọn theo chặng, cột dùng mã
    codec.py          đổi mã sang nhãn và kiểm tra giá trị; mọi bảng đều đi qua đây
    mock.py           sinh số giả từ bộ đáp án, xuất ra đúng dạng hợp đồng
    store.py          chọn chế độ thật hoặc giả, nạp bảng
    metrics.py        đếm và chia theo bộ lọc
  ui/
    theme.py          màu theo chế độ sáng, tối
    charts.py         các dạng biểu đồ dùng lại
    components.py     tiêu đề trang, hàng lọc, thẻ KPI, thẻ biểu đồ, thẻ "chưa có dữ liệu"
    images.py         cắt ảnh và vẽ box
  views/              mỗi trang một file, có META và render()
  data_real/          thả bảng thật vào đây
```

Thêm trang mới: tạo file trong `views/` có `META` và `render()`, rồi thêm vào `SECTIONS` trong `app.py`.

## Lưu ý về số giả

- Mọi xác suất trong `mock.py` là tham số tự đặt để giao diện có số mà vẽ. Không trích số từ
  chế độ giả vào báo cáo.
- Trang reviewer và trang annotator tự sửa chỉ hiện lại tham số mô phỏng. Trang agent cần
  quyết định duyệt của người thật mới có nghĩa.
- Cột ghi "cần đáp án" trong hợp đồng chỉ tính được vì dữ liệu bán tổng hợp có ground truth.
- Mẫu số của mọi tỷ lệ là "vật đã review": annotation đã review cộng vật bị báo thiếu. Dùng riêng
  số annotation thì class bị bỏ sót gần hết (traffic sign với model COCO) có mẫu số gần 0.
