# State Machine Diagram — LMSERP OneWorld

Vòng đời trạng thái của các thực thể nghiệp vụ, vẽ **từ chỗ GÁN trạng thái thật trong code**, không từ enum.

## Kết quả kiểm

| File | Enum | State | Transition | `state.mjs check` |
|---|---|---|---|---|
| `chargestatus` | `ChargeStatus` (4 case) | 3 | 8 | 0 lỗi, 2 cảnh báo |
| `sessionstatus` | `SessionStatus` (3 case) | 3 | 5 | **0 lỗi, 0 cảnh báo** |
| `chargeproposalstatus` | `ChargeProposalStatus` (3 case) | 3 | 5 | **0 lỗi, 0 cảnh báo** |

2 cảnh báo của `chargestatus` là nhãn self-loop đè lên state — xem mục *Bẫy layout* bên dưới.

---

## Phát hiện quan trọng — `ChargeStatus::VOIDED` là trạng thái chết

Enum khai 4 case (`app/Enums/ChargeStatus.php:10-14`) nhưng **không có đường vào nào**:

| Nơi kiểm tra | Kết luận |
|---|---|
| `grep -rn "VOIDED" app/ database/` | 6 chỗ, **tất cả đều là ĐỌC** |
| `ChargeService` | có `remainingAmount()`, `cancel()`, `void()` — **không method nào gán `VOIDED`** |
| `database/seeders/`, `database/factory/` | không seeder nào sinh `VOIDED` |
| `create_charges_table.php:28` | chỉ là comment liệt kê giá trị |

Toàn bộ 6 chỗ đọc đều dùng nó để **loại trừ**: `whereNotIn('status', [VOIDED])` (`CreditPoolService.php:157`), `!= VOIDED` (`DebtCalculationService.php:148`), `reject(...)` (`MonthlyCharges.php:151,208,289`), ẩn nút thu tiền (`ChargeResource.php:488-492`), chặn sửa/xuất phiếu (`ChargeService.php:462`, `PaymentService.php:59,259`).

→ **Vẽ mũi tên tới `VOIDED` là bịa.** Diagram chỉ có 3 state dù enum có 4 case. Đây là ứng viên số 1 cho danh sách phát hiện gửi khách: *"enum khai nhưng code không gán được — hoặc là tính năng chưa làm, hoặc là đường gán bị mất khi refactor."*

Điều này lặp lại đúng bài học của vòng trước (activity `take-attendance` sai 3 chỗ so với code): **đọc `file:line` trước khi vẽ, không tin rằng enum = vòng đời.**

---

## Transition thật của từng enum

### `ChargeStatus` — 4 chỗ gán

| Từ | Đến | Guard | Nguồn |
|---|---|---|---|
| — | `PENDING` | tổng = 0 thì sang `PAID` | `ChargeService.php:206` (tạo charge theo kỳ) |
| `PENDING`/`PARTIAL` | `PAID` hoặc `PARTIAL` | số còn phải thu = 0 ? | `ChargeService.php:348` (tiêu quỹ) |
| `PENDING`/`PARTIAL` | `PAID` hoặc `PARTIAL` | số còn phải thu = 0 ? | `PaymentService.php:98` (thu tiền mặt) |
| `PENDING`/`PARTIAL` | `PAID` hoặc `PARTIAL` | số còn phải thu = 0 ? | `CreditPoolService.php:215` (trừ quỹ học phí) |

Cả 3 chỗ gán "suy ra" đều viết **cùng một biểu thức** `$remaining === 0 ? PAID : PARTIAL` — đây là quy tắc nghiệp vụ *"đã trả đủ số còn phải thu"*, không phải quyết định của từng nghiệp vụ riêng. Diagram gộp thành transition có guard `[part payment]` / `[paid in full]`.

### `SessionStatus` — 3 chỗ gán

| Từ | Đến | Guard | Nguồn |
|---|---|---|---|
| — | `SCHEDULED` | sinh từ lịch | `ScheduleGenerator` |
| `SCHEDULED` | `COMPLETED` | ngày buổi ≤ hôm | `SessionCompletion.php:141` (job đêm), `DemoDataSeeder.php:224` |
| `SCHEDULED` | `CANCELLED` | **buổi chưa có điểm danh** | `HolidayCancelService.php:53` |

Điều kiện "chưa có điểm danh" là chi tiết đáng vẽ nhất: `HolidayCancelService.php:17-19` nêu rõ thao tác hàng loạt nên **không throw cho cả mẻ**, chỉ báo số bị bỏ qua để admin gỡ điểm danh rồi chạy lại (TASK-03).

### `ChargeProposalStatus` — 3 chỗ gán

| Từ | Đến | Guard | Nguồn |
|---|---|---|---|
| — | `PENDING` | đề xuất cuối kỳ | `ChargeProposalService.php:84` |
| `PENDING` | `APPROVED` | **điều kiện chưa đổi** | `ChargeProposalService.php:115` |
| `PENDING` | `DISMISSED` | chưa quyết định | `ChargeProposalService.php:165` |

`PENDING` là cổng một lối ra: `ChargeProposalService.php:160-161` chặn `isDecided()` nên **không có đường quay lại `PENDING`** từ `APPROVED`/`DISMISSED`. Nếu điều kiện đã đổi giữa lúc đề xuất và lúc duyệt, `generateCycle()` trả `null` và `throw ChargeProposalStale::conditionsChanged()` — rollback, không ghi.

---

## Enum CHƯA vẽ — vì sao

`plan.md` mục 2 liệt kê 10 enum. Đã khảo sát hết, giữ lại 7 cái sau vì **không đủ bằng chứng gán trạng thái**:

| Enum | Tình trạng |
|---|---|
| `StudentStatus` | `ACTIVE`/`INACTIVE`/`ARCHIVED` — grep toàn repo không có chỗ gán nào ngoài cast trong `Student.php:78`. Toàn bộ dữ liệu sinh bằng seeder. |
| `UserStatus` | chỉ `DemoUserSeeder:69`, `AdminUserSeeder:50`, `UserFactory:48` gán `ACTIVE`. Không có luồng `PENDING → LOCKED` trong `app/`. |
| `RoomStatus` | có `Room.php:178` gán `RETIRED` và `ScheduleGrid.php:877` gán `ACTIVE`, nhưng **không có `MAINTENANCE`** trong code. |
| `ClassStatus` | `ScheduleGrid.php:726,833` gán `ACTIVE`; không thấy đường sang `CLOSED`. |
| `EnrollmentStatus` | chỉ `PAUSED` là có chỗ gán (`ChargeProposalService.php:180`, `ChargeCycleRunner.php:318`) và `ACTIVE` lúc tạo (`EnrollmentService.php:72`); **`ENDED` không có chỗ gán**. |
| `InvoiceStatus` | grep `InvoiceStatus::` trong `app/` + `database/` = **0 kết quả**. Cột status có thật nhưng enum không ai dùng. |
| `AttendanceStatus` | `saveBatch()` cố tình **xoá `LATE`** (`if ($status === LATE) $status = null`) — LATE bị gỡ khỏi UI 07/09 nhưng giữ trong enum cho dữ liệu lịch sử. Vẽ 3 state sẽ vẽ thứ mà UI không cho nhập. |

Vẻ mấy cái này bây giờ sẽ ra sơ đồ toàn mũi tên giả. Để dành cho khách hàng có câu chuyện đủ dữ liệu.

---

## Bẫy layout (2 cảnh báo của `chargestatus`)

Nhãn self-loop quanh state bị đặt ngay trên hình state:

```
WARN [label] dòng 15: nhãn "[part payment] Web App collects" đè lên "Partial"
WARN [label] dòng 17: nhãn "[credit used] Credit Pool applies" đè lên "Pending"
```

Đã thử 3 cách, đều **không** hết:

| Cách | Kết quả |
|---|---|
| Đổi thứ tự khai báo node (3 biến thể: đảo cột, gom cột, xen kẽ) | vẫn đúng 2 cảnh báo |
| Rút nhãn còn `[part] Web App collects` (bỏ 2 từ) | vẫn 2 cảnh báo |
| Rút còn `[part]` (bỏ cả actor) | 2 cảnh báo — **và sinh thêm lỗi vì vi phạm nguyên tắc 3** |

Khoảng cách giữa hai state cùng cột do engine đặt cố định; nhãn self-loop dài hơn khoảng đó là chạm. Đây là **giới hạn layout, không phải lỗi nội dung** — nên giữ nhãn đầy đủ (actor + guard + hành động) cho dễ đọc, chấp nhận 2 cảnh báo.

Bài học vận hành: `check` xanh **không** đồng nghĩa hình đẹp, và ngược lại cảnh báo layout **không** phải lý do để cắt nội dung thật. Trước khi "sửa" cảnh báo, hỏi nó là lỗi hay là giới hạn.

---

## Lệnh tái lập

```sh
S=~/.dsh/skills/state-machine-diagram/scripts/state.mjs
cd docs/uml/state
node $S gen chargestatus.model.json        --out chargestatus.drawio
node $S gen sessionstatus.model.json        --out sessionstatus.drawio
node $S gen chargeproposalstatus.model.json --out chargeproposalstatus.drawio
node $S check chargestatus.drawio           # OK: 0 errors, 2 warning(s)
node $S render chargestatus.drawio
```

Actor lấy từ **lane của activity diagram** theo nguyên tắc 4 của skill, không tự đặt:

| State machine | Activity nguồn | Lane lấy được |
|---|---|---|
| `chargestatus` | `charge-cycle.drawio` + `collect-payment.drawio` | Scheduler, Accountant, Web App, Payment Service, Credit Pool |
| `sessionstatus` | `take-attendance.drawio` | Scheduler, Web App, Teacher |
| `chargeproposalstatus` | `charge-cycle.drawio` | Scheduler, Finance Service |