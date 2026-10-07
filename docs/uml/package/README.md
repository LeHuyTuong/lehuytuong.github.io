# Package diagram — `backend.drawio`

Sinh từ [../inventory.json](../inventory.json) với profile `spring`, khung `Backend`.
Kết quả `gen`: **0 lỗi, 0 cảnh báo**.

## Cảnh báo quan trọng: sơ đồ KHÔNG mô tả code của repo này

Tường chốt ngày 05/10/2026: khi repo **không có** `Repository` và **không có** interface `Service`
thì vẽ đủ 4 tầng chuẩn Spring. Quyết định đó đã thực hiện, nhưng phải nói thẳng hệ quả:

| Tầng trong sơ đồ | Có thật trong repo này không? |
|---|---|
| Controller | **Có** |
| Service | **Có** (nhưng là class cụ thể, không phải interface) |
| Repository | **KHÔNG** — Laravel dùng Eloquent, truy cập dữ liệu qua model |
| Entity | **Có** (model Eloquent đóng vai entity) |

`inventory.json` có **34 chỗ tiêm phụ thuộc (DI), tất cả class → class, không có interface nào**.
Vì vậy:
- Không có bước `Service → Repository` trong code thật.
- Không có bước `Repository → Entity` trong code thật.
- Sơ đồ này là **khuôn chuẩn** để khách đối chiếu, không phải bản mô tả hiện trạng.

Khi dùng cho khách: đây chính là điểm giá trị của dịch vụ — chỉ ra được chỗ thiếu tầng, chứ không
vẽ ra cái đã có rồi.

## Package trong sơ đồ

| Package | Nguồn code |
|---|---|
| Controller | `app/Features/*/Http/Controllers/`, Livewire pages |
| Service | `app/Features/*/Services/`, `app/Services/` |
| Repository | *(không có trong repo)* |
| Entity | `app/Models/`, `app/Features/*/Models/` |

Quy tắc vẽ đã áp dụng (package-diagram): package chỉ hiện **tên ngắn**, không hiện đường dẫn
đầy đủ; mọi dependency mang nhãn `«use»` (gọi hàm lúc chạy) hoặc `«import»` (chỉ dùng kiểu).