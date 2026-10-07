# Use Case Diagram — LMSERP OneWorld

Sinh từ `lmserp.model.json`, mọi use case đều có bằng chứng `file:dòng` trong
[`../flows.md`](../flows.md). Chạy lại:

```bash
node ~/.dsh/skills/use-case-diagram/scripts/usecase.mjs gen lmserp.model.json --role Teacher --out role-teacher.drawio
```

## Kết quả kiểm tra (đo lại 05/10/2026, sau khi tách UC + tách miền)

| File | Nguồn | UC | Actor | Lint | Kết luận |
|---|---|---|---|---|---|
| `role-administrator` | lmserp | 20 | 1 | 0 err / 0 warn | PASS |
| `role-accountant` | lmserp | 11 | 1 | 0 err / 0 warn | PASS |
| `role-manager` | lmserp | 13 | 1 | 0 err / 1 warn | PASS |
| `role-assistant` | lmserp | 7 | 1 | 0 err / 0 warn | PASS |
| `role-teacher` | lmserp | 8 | 1 | 0 err / 0 warn | PASS |
| `finance` | finance | 12 | 4 | 0 err / 25 warn | PASS |
| `lmserp-academic` | academic | 7 | 6 | 0 err / 27 warn | PASS |
| `lmserp-system` | system | 7 | 5 | 0 err / 10 warn | PASS |
| `operations` | operations | 11 | — | 0 err / 83 warn | PASS |
| `service-usecase` | svc/usecase | 10 | 2 | 0 err / 0 warn | PASS — **sơ đồ của CHÍNH dịch vụ bán diagram**, không mô tả LMSERP |

> **Khác biệt:** 9 dòng trên là sơ đồ **case study LMSERP-OneWorld**. Riêng
> `service-usecase` mô tả **chính dịch vụ này** (actor `Student` / `Domain Reviewer`);
> nguồn `svc/usecase.model.json`. Đừng gộp nó vào các con số thống kê của LMSERP.

Cách kiểm: `usecase.mjs check <file.drawio>` — exit 0 **không** đủ, phải đọc dòng
`OK:`/`FAIL:`.

### Tách miền 05/10: `lmserp.drawio` → 3 diagram

Sơ đồ toàn hệ thống `lmserp.drawio` (24 UC, 6 actor) đạt **12 lỗi** (8 `[path]` +
4 `[uml actor-gen]`). Quét 32 tổ hợp `side` không tổ hợp nào đạt 0. Theo luật
SKILL.md — *"nếu không đạt thì **tách diagram**, đừng nới `[path]`"* — đã tách thành:

| Diagram mới | UC | Actor | Lỗi | Cảnh báo |
|---|---|---|---|---|
| `lmserp-academic` | UC04–UC10 (Students, Enrollments, Class Rooms, Attendance) | 6 | **0** | 27 |
| `finance` (đã có) | UC07, UC09, UC11–UC18, UC25–UC26 | 4 | **0** | 25 |
| `lmserp-system` | UC03, UC19–UC24 (Session Journals, Work Logs, Rooms, Holidays, Users, Logs) | 5 | **0** | 10 |

**Nguyên nhân lỗi actor-gen:** RegisteredUser đặt `side: right`, 5 actor con đặt
`side: left` → cạnh generalization dài 1700–3500 px (giới hạn 900 px). **Fix:** bỏ
`side` khỏi cả 6 actor, để engine tự đặt. Finance model không khai `side` và PASS
từ trước — xác nhận cách này đúng.

**Sửa tên UC12:** `Decide Charge Proposals` → `Review Charge Proposals` — engine
báo `[uml usecase-name]`: "Decide" không phải động từ chủ động. Đã sửa trong
`finance.model.json` và `lmserp.model.json`.

File `lmserp.drawio` / `lmserp.png` cũ (12 lỗi) **không còn dùng** — tham chiếu
bởi 3 diagram miền mới. Không xoá file (sandbox cấm delete), đánh dấu deprecated.

## Quyết định nghiệp vụ đã giữ

- **Bỏ `UC05 Create Student` / `UC06 Edit Student` khỏi hình operations**: gộp thành
  `Manage Students` + generalization `«extend»`. Hai thao tác này là chi tiết CRUD
  trong cùng một màn hình, tách riêng làm UC phẳng.
- **Không vẽ `/app/attendances`** dù route tồn tại: `AttendancePolicy.php:10-18` nói
  thẳng đây không phải đường ghi thật, gv/tg gặp 403. Đường thật là `Take Attendance`
  qua `AttendancePermission::canMark()` (`AttendancePermission.php:71-94`).
- **`Run Monthly Charge Cycle`** thuộc Accountant vì `ChargeAutoApproval.php:40-46`
  cho phép tự duyệt khi đủ điều kiện — vai kế toán là vai thao tác chứ không phải
  vai người bấm nút.

## Bằng chứng bổ sung từ 2 activity vẽ sau (05/10/2026)

Hai mục dưới đây lộ ra khi vẽ activity, không phải khi đọc route — nên ghi lại
để bàn giao cho người khác không phải tra lại code.

- **`Collect Payment` không phải một use case đơn giản.** Nó có hai cửa: gọi thẳng
  thì bị chặn overpay (`recordPayment`, `PaymentService.php:47`, ném `OverpayRejected`
  ở `:72-74`), còn qua `recordCollection` (`:231`) thì hệ thống **tự chia** phần dư
  vào quỹ "đóng khóa" (`:274-275`, `recordDeposit` ở `:291`).
- **Q1 đã chốt 05/10: tách thành HAI use case. ĐÃ VẼ LẠI 05/10.**
  - `Record Payment` (`PaymentService.php:47`) — không có actor nào trong UI gọi thẳng;
    chỉ `recordCollection:281` và test/seeder gọi. Vẽ là UC **không** nối actor.
  - `Record Deposit` (`PaymentService.php:134`) — **có** actor: UI gọi thẳng ở
    chế độ `MODE_DEPOSIT` (`ChargeResource/Pages/ListCharges.php:440`).
  - Quan hệ là **`«extend»` chứ không phải `«include»`**: cả hai lời gọi đều nằm trong
    `if ($applied > 0)` / `if ($overflow > 0)` (`:280`, `:284`) ⇒ **có điều kiện**, mà
    `«include»` bắt buộc luôn xảy ra. `recordDeposit` còn có thêm nhánh `:287` ném lỗi.
  - Đổi từ `«include»` sang `«extend»` làm `role-accountant` từ 1 warning → **0 warning**.
- **Lỗi bằng chứng đã sửa:** `questions.md` và README trước đây ghi
  `recordPayment` ở `:59` và phần chia tiền ở `:215-222` — cả hai đều sai. Số dòng
  thật: khai báo hàm `:47` / `:231`; chia `applied`/`overflow` ở `:274-275`.
