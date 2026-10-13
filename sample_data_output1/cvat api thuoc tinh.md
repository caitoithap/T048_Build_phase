# Các trường dữ liệu đọc được từ API CVAT

Nguồn: bản xuất API CVAT cục bộ (phiên bản 2.75.1). Tài liệu chỉ liệt kê các trường và kiểu dữ liệu quan sát được; không đưa giá trị của từng bản ghi, thông tin đăng nhập hoặc nội dung ảnh.

## Phạm vi

- Đã đọc: thông tin máy chủ, người dùng, dự án, tác vụ, công việc, nhãn, siêu dữ liệu khung hình và dữ liệu gán nhãn.
- Vấn đề (`issue`) và bình luận (`comment`): API trả về thành công nhưng danh sách rỗng, nên chưa thể xác nhận các trường từ bản ghi thực tế.
- Chưa tải dữ liệu điểm ảnh hoặc các gói dữ liệu/khôi phục (`dataset`/`backup`).

## Thông tin máy chủ

Tệp nguồn: `server_about.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `name` | string |
| `description` | string |
| `version` | string |
| `logo_url` | string |
| `subtitle` | string |

## Tài khoản hiện tại

Tệp nguồn: `current_user.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `url` | string |
| `id` | integer |
| `username` | string |
| `first_name` | string |
| `last_name` | string |
| `email` | string |
| `groups` | array |
| `is_staff` | boolean |
| `is_superuser` | boolean |
| `is_active` | boolean |
| `last_login` | string |
| `date_joined` | string |
| `has_analytics_access` | boolean |
| `created_via` | string |

## Danh sách người dùng

Tệp nguồn: `users.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `url` | string |
| `id` | integer |
| `username` | string |
| `first_name` | string |
| `last_name` | string |

## Dự án (Project)

Tệp nguồn: `projects.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `url` | string |
| `id` | integer |
| `name` | string |
| `owner` | object |
| `owner.url` | string |
| `owner.id` | integer |
| `owner.username` | string |
| `owner.first_name` | string |
| `owner.last_name` | string |
| `assignee` | null (chưa xác định kiểu khi có giá trị) |
| `guide_id` | null (chưa xác định kiểu khi có giá trị) |
| `bug_tracker` | string |
| `created_date` | string |
| `updated_date` | string |
| `status` | string |
| `dimension` | string |
| `organization` | null (chưa xác định kiểu khi có giá trị) |
| `organization_id` | null (chưa xác định kiểu khi có giá trị) |
| `target_storage` | object |
| `target_storage.id` | integer |
| `target_storage.location` | string |
| `target_storage.cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |
| `source_storage` | object |
| `source_storage.id` | integer |
| `source_storage.location` | string |
| `source_storage.cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |
| `tasks` | object |
| `tasks.count` | integer |
| `tasks.url` | string |
| `labels` | object |
| `labels.url` | string |
| `assignee_updated_date` | null (chưa xác định kiểu khi có giá trị) |
| `task_subsets` | array |

## Tác vụ (Task)

Tệp nguồn: `tasks.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `url` | string |
| `id` | integer |
| `name` | string |
| `project_id` | integer, null (chưa xác định kiểu khi có giá trị) |
| `project_name` | null (chưa xác định kiểu khi có giá trị), string |
| `owner` | object |
| `owner.url` | string |
| `owner.id` | integer |
| `owner.username` | string |
| `owner.first_name` | string |
| `owner.last_name` | string |
| `assignee` | null (chưa xác định kiểu khi có giá trị) |
| `bug_tracker` | string |
| `created_date` | string |
| `updated_date` | string |
| `overlap` | integer |
| `segment_size` | integer |
| `status` | string |
| `data_chunk_size` | integer |
| `data_original_chunk_type` | string |
| `data_compressed_chunk_type` | string |
| `data_cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |
| `guide_id` | null (chưa xác định kiểu khi có giá trị) |
| `size` | integer |
| `image_quality` | integer |
| `data` | integer |
| `dimension` | string |
| `mode` | string |
| `media_type` | string |
| `subset` | string |
| `organization_id` | null (chưa xác định kiểu khi có giá trị) |
| `organization` | null (chưa xác định kiểu khi có giá trị) |
| `target_storage` | object |
| `target_storage.id` | integer |
| `target_storage.location` | string |
| `target_storage.cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |
| `source_storage` | object |
| `source_storage.id` | integer |
| `source_storage.location` | string |
| `source_storage.cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |
| `jobs` | object |
| `jobs.count` | integer |
| `jobs.completed` | integer |
| `jobs.validation` | integer |
| `jobs.url` | string |
| `labels` | object |
| `labels.url` | string |
| `assignee_updated_date` | null (chưa xác định kiểu khi có giá trị) |
| `validation_mode` | null (chưa xác định kiểu khi có giá trị) |
| `consensus_enabled` | boolean |

## Công việc (Job)

Tệp nguồn: `jobs.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `url` | string |
| `id` | integer |
| `task_id` | integer |
| `task_name` | string |
| `project_id` | integer, null (chưa xác định kiểu khi có giá trị) |
| `project_name` | null (chưa xác định kiểu khi có giá trị), string |
| `assignee` | null (chưa xác định kiểu khi có giá trị) |
| `guide_id` | null (chưa xác định kiểu khi có giá trị) |
| `dimension` | string |
| `mode` | string |
| `media_type` | string |
| `bug_tracker` | null (chưa xác định kiểu khi có giá trị), string |
| `status` | string |
| `stage` | string |
| `state` | string |
| `frame_count` | integer |
| `start_frame` | integer |
| `stop_frame` | integer |
| `data_chunk_size` | integer |
| `data_compressed_chunk_type` | string |
| `data_original_chunk_type` | string |
| `created_date` | string |
| `updated_date` | string |
| `issues` | object |
| `issues.url` | string |
| `issues.count` | integer |
| `labels` | object |
| `labels.url` | string |
| `type` | string |
| `organization` | null (chưa xác định kiểu khi có giá trị) |
| `target_storage` | object |
| `target_storage.id` | integer |
| `target_storage.location` | string |
| `target_storage.cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |
| `source_storage` | object |
| `source_storage.id` | integer |
| `source_storage.location` | string |
| `source_storage.cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |
| `assignee_updated_date` | null (chưa xác định kiểu khi có giá trị) |
| `parent_job_id` | null (chưa xác định kiểu khi có giá trị) |
| `replicas_count` | integer |
| `consensus_replicas` | integer |

## Nhãn (Label)

Tệp nguồn: `tasks/15/labels.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `id` | integer |
| `name` | string |
| `color` | string |
| `attributes` | array |
| `attributes[].id` | integer |
| `attributes[].name` | string |
| `attributes[].mutable` | boolean |
| `attributes[].input_type` | string |
| `attributes[].default_value` | string |
| `attributes[].values` | array |
| `type` | string |
| `sublabels` | array |
| `task_id` | integer |
| `parent_id` | null (chưa xác định kiểu khi có giá trị) |
| `has_parent` | boolean |

## Siêu dữ liệu ảnh

Tệp nguồn: `tasks/15/frames.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `chapters` | null (chưa xác định kiểu khi có giá trị) |
| `chunks_updated_date` | string |
| `chunk_size` | integer |
| `size` | integer |
| `image_quality` | integer |
| `start_frame` | integer |
| `stop_frame` | integer |
| `frame_filter` | string |
| `frames` | array |
| `frames[].width` | integer |
| `frames[].height` | integer |
| `frames[].name` | string |
| `frames[].related_files` | integer |
| `frames[].has_related_context` | boolean |
| `deleted_frames` | array |
| `included_frames` | null (chưa xác định kiểu khi có giá trị) |
| `storage` | string |
| `cloud_storage_id` | null (chưa xác định kiểu khi có giá trị) |

## Dữ liệu gán nhãn (Annotation)

Tệp nguồn: `tasks/15/annotations.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `version` | integer |
| `tags` | array |
| `shapes` | array |
| `shapes[].id` | integer |
| `shapes[].label_id` | integer |
| `shapes[].type` | string |
| `shapes[].frame` | integer |
| `shapes[].group` | integer |
| `shapes[].source` | string |
| `shapes[].score` | number |
| `shapes[].occluded` | boolean |
| `shapes[].outside` | boolean |
| `shapes[].z_order` | integer |
| `shapes[].rotation` | number |
| `shapes[].points` | array |
| `shapes[].attributes` | array |
| `shapes[].attributes[].spec_id` | integer |
| `shapes[].attributes[].value` | string |
| `shapes[].elements` | array |
| `tracks` | array |
| `intervals` | array |

## Định dạng nhập/xuất (import/export)

Tệp nguồn: `annotation_formats.json`

| Trường | Kiểu dữ liệu quan sát được |
|---|---|
| `importers` | array |
| `importers[].name` | string |
| `importers[].ext` | string |
| `importers[].version` | string |
| `importers[].enabled` | boolean |
| `importers[].dimension` | string |
| `exporters` | array |
| `exporters[].name` | string |
| `exporters[].ext` | string |
| `exporters[].version` | string |
| `exporters[].enabled` | boolean |
| `exporters[].dimension` | string |

## Thuộc tính riêng của bộ dữ liệu BDD100K

| Thuộc tính | Vị trí lưu | Ý nghĩa |
|---|---|---|
| `truncated` | `shapes[].attributes[]` | Vật thể bị cắt ở mép ảnh |
| `trafficLightColor` | `shapes[].attributes[]` | Màu đèn theo nhãn nguồn |
| `occluded` | `shapes[].occluded` | Vật thể bị che khuất |

`attributes[].spec_id` liên kết tới `labels[].attributes[].id`; `label_id` liên kết tới `labels[].id`. Tọa độ hình chữ nhật (`rectangle`) trong `points` có thứ tự `[x1, y1, x2, y2]`.

Nguồn của các khung bao (`box`) quan sát được ở Task 15 là `file`. Loại lỗi, mức độ tái diễn (`recurrence`), nguyên nhân và khuyến nghị M22 chưa có trong bản xuất; cần tạo mới và bổ sung từ dữ liệu `issue`/`comment`.
