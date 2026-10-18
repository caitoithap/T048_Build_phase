# M22 – Plan thực hiện chi tiết

Đi kèm `M22_DE_XUAT.md`. File kia trả lời "làm gì và vì sao"; file này trả lời "làm thế nào, theo thứ tự nào, ai làm, xong là thế nào".

## 0. Tóm tắt

**Flow:** đọc issue → hiểu lỗi → tìm lỗi lặp lại → quy nguồn → đề xuất sửa → áp dụng có người duyệt → đo lại.

**Thời gian:** 2 tuần, 4 người. Phần lõi và bản vá sinh từ comment nằm trong phạm vi; dự đoán frame rủi ro và fine-tune là tuỳ chọn.

**Các chặng:**

| Chặng | Nội dung | Người chính | Ngày |
|---|---|---|---|
| 0 | Chuẩn bị và chốt hợp đồng | Cả nhóm | 1 |
| A | Sinh dữ liệu | Analytics + AI/Agent | 2–4 |
| B | Đẩy lên CVAT | Data/Backend | 4–5 |
| C | Ingest và làm giàu | Data/Backend + AI/Agent | 5–7 |
| D | Analytics mart | Analytics | 6–8 |
| E | Dashboard | Dashboard | 2–10 |
| F | Agent quy nguồn | AI/Agent + Analytics | 8–11 |
| G | Can thiệp | AI/Agent + Data/Backend | 9–12 |
| H | Pilot và đo lại | Cả nhóm | 12–13 |
| I | Dự đoán frame rủi ro (tuỳ chọn) | Analytics | nếu dư |
| J | Đóng gói | Cả nhóm | 13–14 |

**Mốc kiểm tra:**

- Cuối ngày 4: có file issue của lô 1 trên đĩa.
- Cuối ngày 7: dữ liệu đi thông từ CVAT đến một biểu đồ.
- Cuối ngày 10: dashboard đủ trang, agent quy nguồn chạy được.
- Cuối ngày 12: bản vá ghi được vào CVAT.
- Ngày 13: có số baseline → pilot.

## Chặng 0. Chuẩn bị (ngày 1)

**Mục tiêu:** gỡ các điểm chặn và thống nhất hợp đồng để bốn người làm song song.

**Các bước:**

1. Hỏi mentor: dữ liệu bán tổng hợp (lỗi thật của model, comment và thời gian mô phỏng) có được chấp nhận không.
2. Dựng CVAT bằng Docker trên một máy, ghi lại phiên bản. Tạo tài khoản: 6 annotator ảo, 3 reviewer ảo, 1 admin.
3. Tạo repo git mới, chia thư mục theo chặng: `datagen/`, `cvat_io/`, `enrich/`, `mart/`, `dashboard/`, `agent/`, `eval/`, `data/`.
4. Chốt ba hợp đồng: schema issue (mục 3 của `M22_DE_XUAT.md`), taxonomy kèm định nghĩa một dòng cho mỗi nhãn, công thức KPI (chặng D).
5. Viết tay một file JSON mẫu 20–30 issue đúng schema.
6. Thử nhanh ba thao tác trên CVAT: tạo một issue bằng tài khoản reviewer; tạo một box có `source = auto` rồi đọc lại; sửa một box qua API.

**Đầu ra:** CVAT chạy được, repo, ba hợp đồng, file JSON mẫu, ghi chú kết quả ba thao tác thử.

**Xong khi:** cả bốn người chạy được code của mình trên file JSON mẫu.

**Gợi ý:**

- Dùng thư viện `cvat-sdk` thay cho gọi `requests` thô; nó bám theo phiên bản server và có sẵn kiểu dữ liệu.
- Bước 6 là quan trọng nhất của ngày 1. Nếu tạo issue cần job ở giai đoạn review hoặc cần quyền riêng thì phải biết ngay, vì chặng B phụ thuộc hoàn toàn vào nó.

## Chặng A. Sinh dữ liệu (ngày 2–4)

**Mục tiêu:** tạo nhãn "đã nộp" của 6 annotator và danh sách issue có đáp án, không gán nhãn tay.

**A1. Chọn ảnh**

- Nguồn: COCO val2017. Chỉ cần file annotation; ảnh tải lẻ theo trường `coco_url`, không cần tải cả bộ.
- Class: car, bus, truck, person, bicycle, motorcycle, traffic light.
- Lọc ảnh có từ 3 đến 25 vật thuộc các class trên. Lấy 400 ảnh, chia ngẫu nhiên có seed thành lô 1 và lô 2, mỗi lô 200.
- Vùng `iscrowd` và vật có cạnh dưới 10px đánh dấu "bỏ qua".

**A2. Viết guideline v1**

Một trang: định nghĩa từng class và các quy ước (vật bị che vẽ phần nào, vật nhỏ đến mức nào thì bỏ, người ngồi trên xe máy gán thế nào). Viết như một bản nháp thật, không cố ý cài chỗ mơ hồ.

**A3. Chạy annotator**

| Annotator | Model | Cấu hình | Sửa lỗi |
|---|---|---|---|
| A | `yolov8n` | 640px, ngưỡng thấp | Không |
| B | `yolov8n` | 320px, ngưỡng cao | Không |
| C | `yolov8s` | 640px | 90% lỗi class, 30% lỗi sót |
| D | `rtdetr-l` | mặc định | Không |
| E | `yolov8m` | 640px | 80% mọi loại (đối chứng) |
| F | YOLO-World | class lấy từ guideline | Không |

Lưu kết quả predict của từng annotator ra đĩa theo định dạng COCO, cố định seed.

**A4. So với ground truth**

Ghép box theo IoU từ cao xuống thấp, một-một, chưa xét class.

| Tình huống | Loại lỗi |
|---|---|
| IoU ≥ 0.75, đúng class | Không lỗi |
| IoU ≥ 0.5, khác class | Wrong Class |
| IoU 0.5–0.75, bao trùm và rộng hơn 20% | Too Large |
| IoU 0.5–0.75, nằm trong và hụt từ hai cạnh | Too Small |
| IoU 0.5–0.75, nằm trong và hụt một cạnh | Truncated |
| IoU 0.5–0.75, còn lại | Misaligned |
| Ground truth không có box ghép | Missing Object |
| Box thừa trùng một ground truth đã ghép | Duplicate Object |
| Box thừa không trùng gì | False Positive |

Mỗi lỗi lưu kèm ngữ cảnh: cỡ vật, sát mép ảnh, chồng lấn với vật khác, vị trí trong ảnh.

**A5. Mô phỏng người sửa**

Với mỗi lỗi ở A4, annotator sửa theo xác suất của mình. Box đã sửa lấy từ ground truth cộng nhiễu 1–3px. Gán `source`: `auto` (không đụng), `semi-auto` (đã sửa), `manual` (thêm mới). Sau đó chạy lại A4 trên nhãn đã sửa để ra danh sách lỗi cuối cùng.

**A6. Reviewer mô phỏng**

Ba reviewer: khó tính, trung bình, dễ tính. Mỗi người có tỷ lệ bắt lỗi theo loại, ngưỡng IoU riêng, tỷ lệ báo nhầm 2–5%, và gộp khoảng 10% lỗi gần nhau vào một issue. Phân công xoay vòng theo job để mỗi annotator gặp ít nhất hai reviewer.

**A7. Comment**

LLM viết từ dữ liệu có cấu trúc, theo bảy tiêu chí: không lộ tên nhãn; ba mức rõ ràng (khoảng 60% / 25% / 15%); giọng cố định theo reviewer; không bịa chi tiết; có yêu cầu sửa cụ thể ở mức rõ; dài 5–30 từ; không lặp khuôn. Khoảng 20–30% issue có thread trả lời, phản biện rơi nhiều vào ca sát ngưỡng và ca báo nhầm.

**A8. Thời gian mô phỏng**

Sinh thời điểm tạo và resolve theo phân bố tuỳ loại lỗi, để 10–15% issue chưa resolve. Lưu vào một file riêng theo mã issue.

**A9. Comment viết tay**

Mỗi người xem 20–30 lỗi và tự viết comment, thay cho comment của LLM ở các issue đó. Đánh dấu `is_handwritten`.

**Đầu ra:** cho mỗi lô: ảnh, ground truth, nhãn nộp của từng annotator, danh sách lỗi thật, danh sách issue kèm đáp án, file thời gian.

**Xong khi:** bảng đếm lỗi theo annotator × loại lỗi cho thấy các hồ sơ khác nhau rõ; lô 1 có khoảng 150–300 issue.

**Gợi ý:**

- Xem bằng mắt 30 lỗi ngẫu nhiên (vẽ box ground truth và box nộp lên ảnh) trước khi đi tiếp. Ground truth của COCO cũng thiếu nhãn: một box "False Positive" có thể là vật thật mà COCO không gán. Nếu tỷ lệ này cao thì lọc bớt ảnh hoặc ghi nhận là giới hạn.
- Model viết comment phải khác model phân loại comment.
- Nếu số issue quá ít thì thêm ảnh; quá nhiều thì lấy mẫu, đừng nới ngưỡng cho vừa.
- `rtdetr-l` và YOLO-World chạy CPU có thể chậm; chạy một lần rồi dùng lại kết quả đã lưu.

## Chặng B. Đẩy lên CVAT (ngày 4–5)

**Mục tiêu:** dữ liệu của chặng A nằm trong CVAT đúng như một dự án thật.

**Các bước:**

1. Tạo một project với 7 nhãn.
2. Mỗi cặp (lô, annotator) là một task, chia 8 job, mỗi job 25 ảnh. Gán job cho tài khoản annotator tương ứng.
3. Tạo annotation qua API annotation của job, đặt `source` đúng giá trị.
4. Đăng nhập bằng tài khoản reviewer để tạo issue (frame, vị trí, job, nội dung comment đầu). Comment trả lời tạo bằng tài khoản của người viết.
5. Đặt trạng thái resolved theo file thời gian.
6. Lưu bảng ánh xạ mã nội bộ sang mã CVAT cho annotation và issue.

**Đầu ra:** project trên CVAT, bảng ánh xạ mã.

**Xong khi:** mở giao diện CVAT thấy đúng box, issue, comment, đúng người tạo.

**Gợi ý:**

- Chia nhiều job là bắt buộc: recurrence cần "job trước đó" của cùng annotator để so.
- Không import bằng file XML. `src/cvat_exporter.py` đang ghi `source` là `auto-yolo`, không phải giá trị CVAT nhận; tạo qua API thì kiểm soát được trường này.
- Script phải chạy lại được mà không tạo trùng, và có lệnh "xoá sạch rồi dựng lại". Thử trên 10 ảnh trước.

## Chặng C. Ingest và làm giàu (ngày 5–7)

**Mục tiêu:** issue trong database đã có class, loại lỗi và thao tác reviewer yêu cầu.

**C1. Ingest**

- Kéo qua API ở dạng JSON: task, job, label, user, annotation theo job, issue, comment.
- Lưu vào SQLite. Bảng chính: `users`, `tasks`, `jobs`, `labels`, `annotations`, `issues`, `comments`. Bảng nhóm tự sinh: `issue_enriched`, `issue_classification`, `recommendations`, `patches`, `annotation_history`, `sync_log`.
- Đồng bộ lặp lại theo kiểu cập nhật-hoặc-thêm. Lần đầu thấy một issue chuyển sang resolved thì ghi thời điểm đó.
- Ghép file thời gian mô phỏng vào hai cột riêng, có cấu hình chọn dùng thời gian thật hay mô phỏng.
- Kiểm tra dữ liệu: issue thiếu job, frame ngoài phạm vi, vị trí rỗng đưa vào bảng lỗi dữ liệu.

**C2. Map issue sang annotation**

So vị trí issue với các box cùng job cùng frame bằng IoU. Khớp tốt nhất từ 0.3 trở lên thì map. Hai ứng viên chênh nhau dưới 0.1 thì đánh dấu "chưa rõ". Không có ứng viên thì đánh dấu "không có annotation" (ca thiếu box).

**C3. Phân loại comment**

LLM nhận comment và thread, trả về JSON: nhãn chính, nhãn phụ nếu có, thao tác được yêu cầu kèm tham số, mức rõ ràng, độ tin cậy. Prompt chứa định nghĩa taxonomy và ví dụ. Lưu kèm tên model và phiên bản prompt; cache theo nội dung comment.

**C4. Chấm bộ phân loại**

Độ chính xác và ma trận nhầm lẫn so với đáp án, tính riêng trên comment viết tay.

**Đầu ra:** database đã làm giàu, báo cáo độ chính xác.

**Xong khi:** đồng bộ hai lần liên tiếp không đổi số dòng; mọi issue hoặc map được hoặc có lý do; có số độ chính xác.

**Gợi ý:**

- Lấy annotation dạng JSON thay vì xuất XML: JSON có mã annotation và `source`, hai thứ chặng F và G cần.
- Trích luôn "thao tác được yêu cầu" ở C3 để chặng G không phải gọi LLM lần nữa.
- Cho phép người sửa nhãn phân loại trên dashboard, lưu riêng với nhãn của LLM.
- `calculate_iou` trong `src/qc_rules.py` nhận `[x, y, w, h]`, còn vị trí issue và box trong JSON của CVAT là `[x1, y1, x2, y2]`; cần đổi trước khi gọi.

## Chặng D. Analytics mart (ngày 6–8)

**Mục tiêu:** mọi con số của dashboard và agent lấy từ một nơi, tính bằng code thuần.

**Bảng:** một bảng sự kiện, mỗi dòng một issue đã làm giàu; các bảng tổng hợp theo loại lỗi, class, annotator, reviewer, và theo cụm (annotator × loại lỗi × class).

**Công thức:**

| Chỉ số | Cách tính |
|---|---|
| Issue rate | Số issue trên 100 annotation |
| Recurrence | Issue là "lặp lại" nếu cùng annotator đã có cùng loại lỗi ở một job trước đó. Tỷ lệ = lặp lại / tổng |
| Recurrence sau can thiệp | Issue rate của cụm đã nhận khuyến nghị, so giữa đối chứng và pilot |
| Resolution time | Trung vị của (resolve − tạo); kèm tỷ lệ chưa resolve |
| Class difficulty | Issue rate theo class, kèm phân bố loại lỗi |
| Annotator cần hỗ trợ | Issue rate cao hơn 1.5 lần trung vị nhóm |
| Chỉ số reviewer | Issue trên 100 annotation đã review; tỷ lệ bị phản biện; tỷ lệ resolve mà annotation không đổi |
| Theo nguồn gốc box | Issue rate tách theo `auto`, `semi-auto`, `manual` |

**Đầu ra:** các bảng mart, bộ kiểm thử trên file JSON mẫu có đáp án tính tay.

**Xong khi:** mọi con số truy ngược được ra danh sách mã issue.

**Gợi ý:**

- Viết kiểm thử cho recurrence trước tiên, đây là công thức dễ sai nhất (thứ tự job, issue đầu tiên của một cặp không tính là lặp lại).
- Ô có dưới 5 issue thì đánh dấu "ít dữ liệu", không tô đỏ và không cho agent kết luận.
- Ngưỡng 1.5 lần là đề xuất; kiểm tra bằng annotator E, nếu E bị gắn cờ thì ngưỡng sai.

## Chặng E. Dashboard (ngày 2–10)

**Mục tiêu:** trả lời ba câu của đề (top lỗi, class khó, annotator cần hỗ trợ) và là nơi người duyệt đề xuất của agent.

**Các trang:**

1. **Tổng quan:** tổng issue, recurrence rate, trung vị resolution time, tỷ lệ chưa resolve, xu hướng theo job.
2. **Top lỗi:** xếp hạng loại lỗi, kèm tỷ lệ lặp lại.
3. **Class khó:** bảng nhiệt class × loại lỗi.
4. **Annotator:** bảng nhiệt annotator × loại lỗi, cờ cần hỗ trợ.
5. **Reviewer:** các chỉ số reviewer.
6. **Chi tiết issue:** ảnh crop có box, thread comment, nhãn phân loại, nguồn được quy.
7. **Agent và hàng chờ:** kết luận quy nguồn, bản vá chờ duyệt.
8. **Pilot:** đối chứng so với pilot.

Bộ lọc chung: lô, annotator, reviewer, class, loại lỗi, trạng thái.

**Xong khi:** từ bất kỳ biểu đồ nào bấm xuống được danh sách issue, rồi một issue.

**Gợi ý:**

- Dựng trên file JSON mẫu từ ngày 2, không chờ dữ liệu thật.
- Dashboard chỉ đọc mart, không tự tính lại số.
- Các nút ở tab "Human Action" của `app.py` hiện không làm gì; trang 7 thay cho tab đó.

## Chặng F. Agent quy nguồn (ngày 8–11)

**Mục tiêu:** với mỗi cụm lỗi lặp lại, trả lời "do đâu" kèm bằng chứng.

**Luồng:** chọn cụm đứng đầu theo recurrence → gom bằng chứng → quy nguồn → lưu khuyến nghị.

**Công cụ cho agent:** lấy các cụm đứng đầu; lấy issue của một cụm; xem cụm đó phân bố thế nào giữa các annotator và model; lấy chỉ số reviewer; lấy thống kê theo nguồn gốc box; lấy tín hiệu thread (phản biện, mở lại); lưu khuyến nghị.

**Luật quy nguồn (tính bằng code, LLM viết giải thích):**

| Nguồn | Điều kiện |
|---|---|
| Model | Cụm xuất hiện ở các annotator dùng chung model gốc, phần lớn trên box `auto` |
| Annotator | Tỷ lệ của một annotator từ 2 lần trung vị nhóm trở lên; annotator khác cùng model không mắc |
| Reviewer | Phần lớn issue của cụm đến từ một reviewer; hoặc tỷ lệ phản biện và resolve-không-đổi cao |
| Guideline | Rải đều ở các annotator khác model, có thread phản biện, annotator F cũng mắc |
| Chưa đủ bằng chứng | Số issue dưới ngưỡng |

**Đầu ra mỗi cụm:** nguồn, độ chắc chắn, số liệu, tối đa 5 mã issue làm căn cứ, hành động đề xuất.

**Xong khi:** agent quy đúng các ca đã biết đáp án: lỗi chung của A và B về model, lỗi riêng của B về annotator, issue của reviewer khó tính về reviewer.

**Gợi ý:**

- Làm luật trước, agent sau. Luật cho kết quả lặp lại được và vẫn chạy khi LLM lỗi; LLM chọn công cụ, xử lý ca lẫn và viết giải thích.
- Lời gọi Gemini trong `src/qc_agent.py` là REST một lượt, chưa có gọi công cụ; cần chuyển sang SDK có hỗ trợ. Tên model mặc định `gemini-1.5-flash` trong `config.py` cũng cần kiểm tra còn dùng được không.
- Với 6 annotator và vài trăm issue, kết quả là gợi ý có bằng chứng. Giao diện ghi rõ như vậy.

## Chặng G. Can thiệp (ngày 9–12)

**G1. Sửa từng object (bản vá)**

Ba câu hỏi: sửa object nào (từ C2), sửa kiểu gì (từ C3), giá trị mới là gì.

| Thao tác | Giá trị mới | Trong phạm vi 2 tuần |
|---|---|---|
| Đổi class | Từ comment; không có thì phân loại lại vùng crop | Có |
| Xoá box | Không cần | Có |
| Cắt về mép ảnh | Tính trực tiếp | Có |
| Thêm box | Chạy lại detector trên vùng issue | Có |
| Chỉnh box | Chạy lại detector trên vùng crop | Nếu kịp |

Trình tự: kiểm tra hợp lệ → vào hàng chờ → người chấp nhận → kiểm tra annotation chưa bị ai sửa → lưu trạng thái cũ → ghi vào CVAT → comment vào issue → để issue mở cho reviewer.

**G2. Ngăn lặp lại**

| Nguồn | Hành động | Đo được ở pilot? |
|---|---|---|
| Model | Chỉnh ngưỡng confidence theo class | Có |
| Guideline | Guideline v2, annotator F chạy lại với class mới | Có |
| Annotator | Ghi chú coaching kèm issue ví dụ | Không, chỉ sinh tài liệu |
| Reviewer | Ghi chú hiệu chỉnh | Không, chỉ sinh tài liệu |

**Đầu ra:** bảng `patches` và `recommendations` có trạng thái, cấu hình annotator sau can thiệp, guideline v2.

**Xong khi:** một bản vá đi hết vòng từ đề xuất đến hiện trên CVAT và hoàn tác được.

**Gợi ý:**

- Với dữ liệu mô phỏng, chấm bản vá bằng ground truth: bản vá đúng nếu box sau vá khớp từ 0.75 trở lên và đúng class.
- Ngưỡng theo class chỉ được chỉnh trên lô 1. Chỉnh trên lô 2 rồi đo trên lô 2 là tự chấm bài mình.
- Khi vùng issue trùng hai box gần bằng nhau, đưa cả hai cho người chọn.
- Agent không tự đóng issue và không tự xuất toạ độ.

## Chặng H. Pilot và đo lại (ngày 12–13)

**Recurrence**

- Đối chứng: lô 2 với cấu hình gốc. Pilot: lô 2 với cấu hình sau can thiệp. Cùng ảnh, cùng reviewer mô phỏng, cùng seed.
- Nhánh pilot đi qua toàn bộ pipeline kể cả CVAT. Nhánh đối chứng có thể tính ngoại tuyến để tiết kiệm thời gian.
- Báo cáo theo từng cụm đã nhận khuyến nghị, không chỉ tổng.

**Resolution time**

- 20 issue sửa tay trên CVAT, 20 issue chấp nhận bản vá. Hai người làm, đổi thứ tự cho nhau.

**Độ tin cậy của hệ thống**

- Độ chính xác bộ phân loại (C4), tỷ lệ quy nguồn đúng (F), tỷ lệ bản vá đúng (G1), annotator E có bị gắn cờ không.

**Gợi ý:**

- So lô 1 với lô 2 sẽ lẫn khác biệt về ảnh vào kết quả; vì vậy chạy lô 2 hai lần. Lô 1 chỉ dùng để học.
- Nếu một can thiệp không có tác dụng thì báo đúng như vậy; đó vẫn là kết quả hợp lệ.

## Chặng I. Dự đoán frame rủi ro (tuỳ chọn)

Trả lời câu "dataset mới chưa có đáp án thì biết frame nào dễ dính issue nào".

- **Tín hiệu:** bất đồng giữa các model (đã có sẵn kết quả predict từ A3), đặc điểm ảnh và box, lịch sử issue theo class.
- **Cách làm:** điểm rủi ro cho từng cặp (frame, loại issue), ban đầu bằng luật.
- **Chấm:** học trên lô 1, dự đoán lô 2, báo "review 30% frame rủi ro nhất thì bắt được bao nhiêu phần trăm issue".
- **Giới hạn:** chỉ xếp ưu tiên; luôn review thêm một mẫu ngẫu nhiên.

Làm nếu chặng F xong trước ngày 11. Chi phí thấp vì không cần chạy thêm model.

## Chặng J. Đóng gói (ngày 13–14)

1. Viết lại README và REPORT theo M22; ghi rõ phần nào là dữ liệu thật, phần nào mô phỏng.
2. Dọn code cũ; cập nhật `requirements.txt` (hiện thiếu `python-dotenv`, thêm `cvat-sdk`).
3. Một lệnh dựng lại toàn bộ từ dữ liệu đã lưu.
4. Kịch bản demo 5 phút đi theo flow 7 bước; quay video dự phòng.

## Lịch 2 tuần theo vai trò

| Ngày | Data/Backend | Analytics | Dashboard | AI/Agent |
|---|---|---|---|---|
| 1 | CVAT, tài khoản, thử API | Taxonomy, công thức KPI | Phác trang, JSON mẫu | Guideline v1, prompt nháp |
| 2–4 | Chạy model (A1, A3), script chặng B | So khớp, sửa lỗi, reviewer (A4–A6) | Dashboard trên JSON mẫu | Comment, thời gian, viết tay (A7–A9) |
| 5–7 | Đẩy lô 1, ingest, database | Mart và kiểm thử | Nối mart thật | Phân loại và chấm |
| 8–10 | Đồng bộ lặp, lịch sử annotation | Luật quy nguồn, chỉ số reviewer | Drill-down, trang agent | Công cụ và vòng lặp agent |
| 11–12 | Ghi bản vá vào CVAT | Ngưỡng theo class | Hàng chờ, trang pilot | Bản vá, guideline v2 |
| 13 | Lô 2 qua pipeline | Bảng baseline → pilot | Hoàn thiện | Bấm giờ resolution time |
| 14 | Đóng gói | Số liệu báo cáo | Demo | Báo cáo |

## Rủi ro và phương án lùi

| Rủi ro | Phương án |
|---|---|
| Mentor không chấp nhận dữ liệu mô phỏng | Thêm một vòng review chéo thật quy mô nhỏ, giữ phần còn lại |
| CVAT chưa thông sau ngày 5 | Ingest thẳng từ file issue của chặng A (cùng schema); CVAT chỉ dùng để demo vài task |
| Hết hạn mức LLM | Cache theo nội dung, chạy theo lô, giảm số issue có thread |
| `rtdetr-l` quá chậm | Thay bằng một model YOLO thế hệ khác |
| YOLO-World không chạy ổn trên CPU | Bỏ annotator F; nguồn guideline chỉ demo định tính |
| Hồ sơ lỗi các annotator quá giống nhau | Tăng khác biệt về độ phân giải và ngưỡng trước khi thêm model |

## Dùng lại từ code hiện tại

| File | Dùng thế nào |
|---|---|
| `src/qc_rules.py` | `calculate_iou` cho C2 (đổi định dạng toạ độ trước) |
| `src/model_assisted_qc.py` | Tham khảo logic khớp box cho A4 |
| `src/cvat_exporter.py` | `export_to_coco_json` để lưu kết quả predict; phần xuất XML không dùng |
| `src/cvat_api.py` | Giữ kiểm tra kết nối, lấy task, lấy issue; bỏ chế độ mock; lấy annotation dạng JSON thay cho XML |
| `src/detector.py` | Tham khảo vòng lặp đọc box; bỏ phần tracking; đang thiếu hằng số trong `config.py` |
| `src/cvat_uploader.py` | Chỉ tham khảo; thay bằng `cvat-sdk` |
| `src/qc_agent.py` | Giữ bốn nhóm khuyến nghị trong prompt; bỏ điểm PASSED/REJECTED và đoạn nhận xét viết sẵn |
| `src/analytics_mart.py`, `app.py` | Giữ khung, viết lại phần tính toán |
| `src/qc_filter.py`, `sample_data/create_sample.py` | Bỏ |

## Đã kiểm chứng trên tài liệu CVAT

- Issue có `created_date`, `updated_date`, `resolved`; không có thời điểm resolve. Các trường thời gian chỉ đọc.
- Khi tạo issue chỉ gửi được frame, vị trí, job, nội dung, người được giao và cờ resolved; người tạo do server đặt theo tài khoản đang đăng nhập.
- Comment có thời điểm tạo và người viết riêng.
- Box có trường `source` với các giá trị manual, auto, semi-auto.
- Có API tạo, cập nhật, xoá annotation theo job.

Nguồn: [IssueRead](https://docs.cvat.ai/docs/api_sdk/sdk/reference/models/issue-read/), [IssueWriteRequest](https://docs.cvat.ai/docs/api_sdk/sdk/reference/models/issue-write-request/), [CommentRead](https://docs.cvat.ai/docs/api_sdk/sdk/reference/models/comment-read/), [JobsApi](https://docs.cvat.ai/docs/api_sdk/sdk/reference/apis/jobs-api/), [Missing SEMI-AUTO source](https://github.com/cvat-ai/cvat/issues/6261).

## Còn phải xác nhận

- Mentor có chấp nhận dữ liệu bán tổng hợp không.
- Phiên bản CVAT nhóm cài có khớp tài liệu trên không (làm ở bước 6 của chặng 0).
- Tài khoản reviewer cần quyền gì, job cần ở giai đoạn nào để tạo được issue.
- YOLO-World chạy trên CPU của nhóm có đủ nhanh không.
- Tên model Gemini còn dùng được và có hỗ trợ gọi công cụ.
- Tỷ lệ ground truth COCO thiếu nhãn trong bộ ảnh đã chọn.
