# M22 – CVAT Issue Analytics Dashboard: Plan đề xuất

*Phụ đề: quy lỗi lặp lại về đúng nguồn và đo hiệu quả can thiệp.*

Tài liệu để nhóm chốt hướng trước khi build. Phần cần quyết định nằm ở mục 9.

## 1. Đề tài

Hệ thống đọc issue/comment của reviewer trên CVAT, tìm lỗi lặp lại, quy mỗi cụm lỗi về một trong bốn nguồn (model pre-label, annotator, guideline, reviewer), đề xuất hành động tương ứng, rồi đo **issue recurrence** và **resolution time** trước và sau can thiệp.

Đầu ra theo đề: dashboard top lỗi, class khó, annotator cần hỗ trợ. Phần mở rộng: agent quy nguồn có bằng chứng, bản vá sinh từ comment, và số đo baseline → pilot.

## 2. Flow

**Đọc issue → hiểu lỗi → tìm lỗi lặp lại → quy nguồn → đề xuất sửa → áp dụng → đo lại**

1. **Đọc issue:** kéo issue, comment và annotation từ CVAT về database.
2. **Hiểu lỗi:** LLM phân loại comment vào taxonomy, map issue về annotation và class.
3. **Tìm lỗi lặp lại:** gom theo loại lỗi, class, annotator; tính recurrence và resolution time.
4. **Quy nguồn:** agent gom bằng chứng, xác định cụm lỗi do model pre-label, annotator, guideline hay reviewer.
5. **Đề xuất sửa:** mỗi nguồn một hành động, kèm bản vá sinh từ comment để annotator bấm chấp nhận.
6. **Áp dụng:** người duyệt đề xuất rồi mới thực thi.
7. **Đo lại:** chạy lô 2, so recurrence và resolution time với lô 1.

## 3. Kiến trúc

```
[A] Sinh dữ liệu     COCO val + ground truth
                     → 5–6 annotator (model + cấu hình + kiểu sửa lỗi)
                     → reviewer mô phỏng so với ground truth
                     → issue + comment (LLM viết) + timestamp
                            │  đẩy qua API
[B] CVAT             task · job · annotation · issue · comment
                            │  ingest
[C] Database         + map issue → annotation/class
                     + LLM phân loại comment vào taxonomy
                            │
[D] Analytics mart   recurrence · resolution time · class khó · annotator score
                        │                    │
[E] Dashboard        [F] Agent: gom bằng chứng → quy nguồn → khuyến nghị
                                             │
[G] Can thiệp        chỉnh ngưỡng / fine-tune model · coaching
                     vá guideline · bản vá sinh từ comment
                            │
                     Lô ảnh 2 → chạy lại từ [A] → đo baseline → pilot
```

Chia việc:

| Vai trò | Phần phụ trách |
|---|---|
| Data/Backend | [B], [C], khung của [A] |
| Analytics | [D], phép so sánh nhãn với ground truth trong [A] |
| Dashboard | [E] |
| AI/Agent | Sinh comment trong [A], phân loại comment trong [C], [F], [G] |

Điểm nối giữa bốn người là schema của một issue sau khi làm giàu:

```
issue_id, task_id, job_id, frame, batch (lô 1 / lô 2)
annotator, reviewer
created_at, resolved_at, status
comments[]            (nội dung, người viết, thời điểm)
position              (toạ độ reviewer đánh dấu)
annotation_id, class_name, annotation_source   (sau khi map)
error_type, error_subtype                      (LLM phân loại)
root_source                                    (agent quy nguồn)
true_error_type       (đáp án từ phép so sánh, chỉ dùng để chấm)
is_handwritten        (comment do người viết tay)
```

## 4. Dữ liệu

Không gán nhãn tay, không QC tay. Lỗi là lỗi thật của model so với ground truth; comment, danh tính và timestamp là mô phỏng.

**Cách dựng:**

1. Lấy 300–500 ảnh COCO val2017, lọc class đường phố (car, bus, truck, person, bicycle, motorcycle, traffic light). Chia làm lô 1 và lô 2.
2. Mỗi annotator là một model cộng cấu hình cộng kiểu sửa lỗi (bảng dưới).
3. Reviewer là phép so sánh nhãn với ground truth, có sai số: bắt sót một phần lỗi, đôi khi báo nhầm, mỗi reviewer một mức khắt khe.
4. LLM viết comment tiếng Việt từ từng lỗi, nhiều giọng, có câu mơ hồ và câu gộp hai lỗi. Timestamp sinh theo phân bố tuỳ loại lỗi.
5. Đẩy tất cả lên CVAT qua API, rồi kéo về bằng pipeline ingest.

**Bộ annotator đề xuất:**

| Annotator | Model | Cấu hình | Vai trò |
|---|---|---|---|
| A | `yolov8n` | 640px, ngưỡng thấp, không sửa | Nhiều box thừa và trùng |
| B | `yolov8n` | 320px, ngưỡng cao | Bỏ sót vật nhỏ; cùng model với A để kiểm tra tách lỗi model với lỗi cấu hình |
| C | `yolov8s` | 640px, sửa 90% lỗi class, 30% lỗi sót | Còn sót vật bị che |
| D | `rtdetr-l` | mặc định, không sửa | Kiến trúc khác họ YOLO |
| E | `yolov8m` | 640px, sửa 80% mọi loại | Đối chứng tốt; không được bị gắn cờ |

Kiểu lỗi ở cột cuối là dự đoán, chưa chạy thử. Model viết comment phải khác model phân loại comment.

**Phần làm tay, khoảng 2–3 giờ cả nhóm:**

- Mỗi người xem 20–30 lỗi máy đã chỉ sẵn và viết comment theo cách của mình. Đây là tập kiểm tra cho bộ phân loại.
- Bấm giờ sửa khoảng 20 issue bằng tay trên CVAT, rồi 20 issue bằng bản vá gợi ý.

## 5. Bốn nguồn lỗi

| Nguồn | Dấu hiệu trong dữ liệu | Hành động | Kiểm chứng được? |
|---|---|---|---|
| Model pre-label | Lỗi chung giữa các annotator dùng cùng model | Chỉnh ngưỡng theo class, gom hard examples, fine-tune | Có |
| Annotator | Lỗi riêng một annotator, người khác không mắc | Coaching đúng loại lỗi | Có |
| Reviewer | Issue resolve mà annotation không đổi; hai reviewer xử lý khác nhau cho ca giống nhau | Hiệu chỉnh reviewer | Có |
| Guideline | Lỗi rải đều mọi người, thread cãi qua lại, issue bị mở lại | Vá guideline kèm ảnh ví dụ | Chỉ định tính |

Với 5–6 annotator và vài trăm issue, kết quả quy nguồn là gợi ý có bằng chứng, chưa phải kết luận thống kê. Agent phải trích ID issue cho mọi kết luận, và người xác nhận trước khi hành động.

## 6. Đo lường

**Baseline → pilot (theo cột chỉ số của đề):**

| KPI | Baseline | Pilot | Loại số đo |
|---|---|---|---|
| Issue recurrence | Lô 1, annotator-model cấu hình gốc | Lô 2, sau khi chỉnh theo khuyến nghị của agent | Đo thật |
| Resolution time | Sửa tay trên CVAT | Chấp nhận bản vá sinh từ comment | Đo thật, bấm giờ |

**Độ tin cậy của hệ thống:**

- Độ chính xác bộ phân loại so với `true_error_type`, tính riêng trên comment viết tay.
- Dashboard có chỉ đúng annotator yếu và không gắn cờ annotator E không.
- Agent có quy đúng nguồn cho các cụm lỗi đã biết đáp án không.

Resolution time hiển thị trên dashboard là số sinh ra, trừ phép đo bấm giờ.

## 7. Hướng làm

- **Giai đoạn 0 – Chốt hợp đồng.** Schema, taxonomy, công thức KPI. Tạo file JSON mẫu 20–30 issue đúng schema để bốn người làm song song.
- **Giai đoạn 1 – Dữ liệu và đường ống mỏng.** Sinh lô 1, đẩy lên CVAT, ingest về database, ra một KPI và một biểu đồ.
- **Giai đoạn 2 – Làm đầy.** Bộ phân loại LLM, đủ các KPI, dashboard có filter và drill-down đến từng issue.
- **Giai đoạn 3 – Agent.** Tool đọc mart, quy nguồn có trích ID issue, bản vá sinh từ comment.
- **Giai đoạn 4 – Pilot.** Áp dụng khuyến nghị, chạy lô 2, đo recurrence; bấm giờ resolution time.
- **Giai đoạn 5 – Đóng gói.** Viết lại README và REPORT theo M22, dọn code cũ.

## 8. Phạm vi

**Làm:**
- Sinh dữ liệu bán tổng hợp và đẩy lên CVAT
- Ingest, data model, taxonomy, phân loại comment bằng LLM
- KPI: issue recurrence, resolution time, class difficulty, annotator score
- Dashboard: overview, top lỗi, class khó, annotator cần hỗ trợ, drill-down, filter
- Agent quy nguồn có bằng chứng, khuyến nghị theo nguồn
- Bản vá sinh từ comment cho lỗi sửa được một cách xác định (sai class, trùng, tràn viền), người chấp nhận
- Đo baseline → pilot cho hai KPI

**Không làm:**
- Loop multi-agent tự sửa nhãn, agent review agent
- Agent tự sửa vị trí box
- Chấm PASSED/REJECTED cho từng bài nộp
- Đồng bộ realtime qua webhook
- Đăng nhập, phân quyền

**Chỉ làm nếu dư thời gian:**
- Fine-tune model trên hard examples (thay vì chỉ chỉnh ngưỡng)
- Cấy lỗi có chủ đích để đo reviewer
- Dự đoán job nào dễ sinh issue để ưu tiên review

## 9. Câu hỏi cần nhóm chốt

### Câu 1. Mentor có chấp nhận dữ liệu bán tổng hợp không?

Câu này chặn mọi thứ khác, cần hỏi trước.

- **A. Bán tổng hợp hoàn toàn** như mục 4, cộng phần comment viết tay.
- **B. Bán tổng hợp cộng một vòng review chéo thật** quy mô nhỏ (mỗi người gán và review khoảng 20 ảnh).
- **C. Chỉ dữ liệu thật.** Tốn công nhất, số lượng ít, khó đo recurrence.

**Khuyến nghị: A.** Nếu mentor yêu cầu có dữ liệu người thật thì chuyển sang B. Báo cáo phải ghi rõ phần nào thật, phần nào mô phỏng.

### Câu 2. Dùng dataset nào?

- **A. COCO val2017**, lọc class đường phố. Tải dễ, model có sẵn đã cùng bộ class.
- **B. BDD100K.** Sát đề tài xe tự lái, có thuộc tính che khuất và cắt cụt; phải đăng ký tải và map lại class.
- **C. Cả hai.** Kiểm tra được hệ thống trên hai miền dữ liệu, nhưng gấp đôi công dựng.

**Khuyến nghị: A.** Chuyển sang B nếu nhóm cần thuộc tính che khuất để giải thích nguyên nhân bỏ sót.

### Câu 3. "Issue recurrence" định nghĩa thế nào?

- **A. Tần suất theo loại lỗi.** Thực chất là "top lỗi", chưa phải "lặp lại".
- **B. Lặp lại theo người.** Một issue là lặp lại nếu cùng annotator đã mắc cùng loại lỗi ở một job trước đó. Recurrence rate = số issue lặp lại / tổng issue.
- **C. Lặp lại sau can thiệp.** Tỷ lệ một cặp (annotator, loại lỗi) đã nhận khuyến nghị ở lô 1 vẫn xuất hiện ở lô 2.

**Khuyến nghị: B làm KPI trên dashboard, C làm số baseline → pilot.**

### Câu 4. Resolution time đo bằng gì?

- **A. Chỉ số mô phỏng.** Đủ để dashboard có hình, nhưng không chứng minh được gì.
- **B. Mô phỏng trên dashboard, cộng phép đo bấm giờ thật** cho sửa tay và sửa bằng bản vá.
- **C. Đo thật toàn bộ.** Cần người thật xử lý mọi issue, không khả thi.

**Khuyến nghị: B.** Cần kiểm tra trên CVAT local xem issue có trường thời điểm resolve riêng không; nếu không thì tự ghi nhận lúc đồng bộ thấy trạng thái đổi. Hiển thị trung vị thay vì trung bình.

### Câu 5. Taxonomy lỗi chốt thế nào?

Bản nháp: Missing Object; Bounding Box Error (Too Small, Too Large, Misaligned, Truncated); Classification Error (Wrong Class); Duplicate Object; False Positive; Guideline/Ambiguous.

- **A. Một nhãn cho mỗi issue.**
- **B. Nhiều nhãn cho mỗi issue.**
- **C. Một nhãn chính, một nhãn phụ tuỳ chọn.** KPI tính theo nhãn chính.

**Khuyến nghị: C.** Mỗi nhãn có định nghĩa một dòng và một ví dụ comment; thêm nhãn "Other". Taxonomy phải khớp với các loại lỗi mà phép so sánh với ground truth sinh ra, nếu không sẽ không chấm được bộ phân loại.

### Câu 6. Can thiệp vào annotator-model bằng cách nào?

- **A. Chỉnh ngưỡng confidence theo class** dựa trên cụm lỗi agent chỉ ra. Rẻ, chạy được trên CPU, kết quả có ngay.
- **B. Fine-tune trên hard examples.** Thuyết phục hơn, nhưng chậm trên CPU và có thể không cải thiện rõ với ít ảnh.
- **C. Đổi kiểu sửa lỗi của annotator** (mô phỏng coaching). Hiệu quả do mình tự đặt, không phải số đo.

**Khuyến nghị: A cho bản chính, B nếu kịp.** Không dùng C làm số pilot vì kết quả là giả định.

### Câu 7. Agent làm đến mức nào?

- **A. Quy nguồn và khuyến nghị**, chỉ đọc.
- **B. Như A, thêm bản vá sinh từ comment**, annotator bấm chấp nhận hoặc từ chối.
- **C. Tự áp dụng bản vá** không cần người duyệt.

**Khuyến nghị: B.** C làm mất bước kiểm chứng của người và không đo được resolution time một cách có nghĩa.

## 10. Mặc định kỹ thuật

Không cần họp, ai phản đối thì nêu: SQLite, Streamlit, Gemini, CVAT chạy Docker trên một máy, repo git mới. Annotator score tính bằng số issue trên 100 annotation; ngưỡng "cần hỗ trợ" so tương đối trong nhóm.

## 11. Dùng lại từ code hiện tại

**Giữ:**
- `src/detector.py`: chạy YOLO để tạo nhãn cho annotator-model; cần bổ sung các hằng số cấu hình đang thiếu trong `config.py`
- `src/cvat_exporter.py`, `src/cvat_uploader.py`: xuất và đẩy nhãn lên CVAT cho bước sinh dữ liệu; `cvat_uploader.py` cũng đang thiếu hằng số cấu hình
- `src/model_assisted_qc.py`: logic khớp box bằng IoU để tìm lỗi sót và sai class, dùng lại cho reviewer mô phỏng (đổi thành so nhãn annotator với ground truth)
- `src/cvat_api.py`: hàm gọi API cho task, annotation, issue; bỏ chế độ mock làm mặc định
- `src/qc_rules.py`: `parse_cvat_xml` và `calculate_iou` để map issue sang annotation (đổi `position` từ `[x1, y1, x2, y2]` sang `[x, y, w, h]`)
- `src/qc_agent.py`: lời gọi Gemini và bốn nhóm khuyến nghị trong prompt
- `app.py`: khung Streamlit nhiều tab

**Bỏ:**
- `src/qc_filter.py`
- Điểm PASSED/REJECTED và đoạn nhận xét viết sẵn trong `qc_agent.py`
- Các số viết cứng trong `src/analytics_mart.py` (ví dụ resolution time 2.5 giờ)
