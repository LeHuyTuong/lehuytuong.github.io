# Component diagram — `system.drawio`

6 component, 10 dependency. Kết quả `gen`: **0 lỗi, 8 cảnh báo** (xem mục "8 cảnh báo" bên dưới —
đã phân loại, không phải lỗi nội dung).

## Vì sao KHÔNG vẽ interface / port / assembly connector

UML 2.5 cho phép component gắn interface (provided = lollipop, required = socket) và nối bằng
assembly connector. Ở repo này **không có interface nào để vẽ**:

- `inventory.json` ghi nhận **34 chỗ tiêm phụ thuộc (DI), tất cả đều class → class.**
- Không có binding interface nào trong container.
- Vẽ lollipop/socket lúc này là **bịa** một tầng trừu tượng mà code không có — đúng cái lỗi đã
  mắc ở các diagram khác (xem `state/README.md` về `ChargeStatus::VOIDED`).

Theo nguyên tắc chung của bộ skill: chỉ vẽ cấu trúc mà code thật sự có. Nếu khách muốn thấy
tầng interface, đó là **khuyến nghị refactor**, nên đưa vào báo cáo chứ không vẽ vào sơ đồ
hiện trạng.

## Component và dependency

| Component | Nguồn code |
|---|---|
| WebApp | lớp cơ sở của toàn bộ màn hình |
| FilamentAdminPanel | Filament v3 + Livewire |
| FinanceServiceGroup | nhóm service nghiệp vụ tài chính (charge, payment, receipt) |
| AttendanceServiceGroup | nhóm service điểm danh |
| ScheduleServiceGroup | nhóm service lịch học |
| EloquentModels | tất cả model Eloquent |

10 cạnh nối: web hiển thị panel; panel gọi service tài chính (duyệt đề xuất thu), điểm danh
(mở phiếu), lịch học (sửa TKB); web gọi service tài chính (thu tiền) và điểm danh (điểm danh);
service lịch học kiểm tra điểm danh; cả ba nhóm service đọc/ghi qua EloquentModels.

## 8 cảnh báo: giới hạn bố trí, đã đo

Đã thử **6 phương án bố trí**, đo bằng `gen` thật chứ không đoán:

| Phương án | Kết quả |
|---|---|
| A | 0 lỗi, **8 cảnh báo** ← dùng bản này |
| B | 1 lỗi, 9 cảnh báo |
| C | 1 lỗi, 8 cảnh báo |
| D | 2 lỗi, 15 cảnh báo |
| E | 3 lỗi, 13 cảnh báo |
| F | 3 lỗi, 13 cảnh báo |

Cảnh báo còn lại là giới hạn của **bố trí tự động** (cạnh bị cắt qua vùng trống, nhãn chồng),
không phải nội dung sai. Giữ phương án A vì 0 lỗi là bằng chứng rõ nhất.

Trước đó từng có 1 lỗi `[path]` — cạnh `webapp → attendance` cắt qua `FinanceServiceGroup`;
sửa bằng cách xếp `AttendanceServiceGroup` ngay dưới `FinanceServiceGroup` (liền kề theo chiều dọc).