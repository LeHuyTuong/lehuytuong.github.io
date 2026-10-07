# Flows nghiệp vụ — LMSERP OneWorld

> **Nguồn: đọc file thật.** `uml.mjs scan` trả **0 actor** cho repo này (Laravel 12 + Filament khai báo qua Resource/Panel, không có `routes/web.php` tường minh; engine không đọc `app/Enums/Role.php` — kiểm chứng: staging chỉ chứa `Role.php` vẫn ra 0 actor).
> Mọi dòng dưới đây lấy từ `app/Enums/Role.php`, `app/Policies/*.php`, `canAccess()` của Filament Page và service tài chính. **Không suy đoán vai nào.**
>
> Thứ tự bắt buộc: flows → (Tường xác nhận) → use case → activity → sequence/class.

## 1. Actor và phân cấp

Nguồn: `app/Enums/Role.php:10-14`. Năm vai gốc, không có quan hệ kế thừa.

| Actor | Mã vai | Bằng chứng |
|---|---|---|
| Administrator | `admin` | app/Enums/Role.php:10 |
| Manager | `manager` | app/Enums/Role.php:11 |
| Teacher | `gv` | app/Enums/Role.php:12 |
| Assistant | `tg` | app/Enums/Role.php:13 |
| Accountant | `ketoan` | app/Enums/Role.php:14 |

Không có vai kế thừa vai: cả 5 vai ngang hàng. `Role.php` ghi rõ thêm vai mới phải làm bằng cấu hình, không sửa enum.

## 2. Hành trình tài khoản

| Bước | Ai | Bằng chứng |
|---|---|---|
| Đăng nhập | Tất cả vai | app/Filament/Pages/Auth/Login.php |
| Đổi mật khẩu | Tất cả vai | app/Filament/Pages/Auth/ChangePassword.php |
| Xem dashboard theo vai | Tất cả vai | app/Features/Dashboard/Filament/Pages/Dashboard.php |
| Quản lý người dùng và vai | Administrator | app/Policies/UserPolicy.php, app/Policies/RolePolicy.php |
| Đổi cấu hình hệ thống | Administrator | app/Filament/Pages/SettingsPage.php |

Không có route đăng ký tự do — vai gán bởi Administrator.

## 3. Tài nguyên × actor (ai ghi, ai đọc)

Đọc từ `app/Policies/`. `write` là policy cho phép tạo/sửa.

| Tài nguyên | Write | Read | Bằng chứng |
|---|---|---|---|
| Student | Administrator, Manager, Accountant | Administrator, Manager, Accountant | app/Policies/StudentPolicy.php |
| Enrollment | Administrator, Manager, Accountant | Administrator, Manager, Accountant | app/Policies/EnrollmentPolicy.php |
| Class Room | Administrator, Manager, Teacher, Assistant | Administrator, Manager, Teacher, Assistant | app/Policies/ClassRoomPolicy.php |
| Attendance | Administrator, Manager, Accountant | Administrator, Manager, Accountant, Teacher (chỉ bản ghi mình đánh dấu), Assistant (chỉ buổi mình phụ trách) | app/Policies/AttendancePolicy.php:25,40,51,55,59 |
| Charge | Administrator, Accountant | Administrator, Accountant | app/Policies/ChargePolicy.php |
| Charge Proposal | Administrator, Manager | Administrator, Manager | app/Policies/ChargeProposalPolicy.php |
| Payment | Administrator, Accountant | Administrator, Accountant | app/Policies/PaymentPolicy.php |
| Tax Invoice | Administrator, Accountant | Administrator, Accountant | app/Policies/TaxInvoicePolicy.php |
| Session Journal | Administrator, Manager, Teacher | Administrator, Manager, Teacher | app/Policies/SessionJournalPolicy.php |
| Teaching Work Log | Administrator, Teacher, Assistant | Administrator, Teacher, Assistant | app/Policies/TeachingWorkLogPolicy.php |
| Room | Administrator, Manager | Administrator, Manager | app/Policies/RoomPolicy.php |
| Holiday | Administrator, Manager | Administrator, Manager | app/Policies/HolidayPolicy.php |
| User | Administrator | Administrator | app/Policies/UserPolicy.php |
| Activity Log | Administrator | Administrator | app/Filament/Resources/ActivityLogResource.php |

Điểm đáng chú ý về Attendance: `view` giới hạn theo **quan hệ sở hữu dữ liệu**, không chỉ theo vai — Teacher chỉ xem bản ghi mình đánh dấu (`marked_by_user_id`), Assistant chỉ xem buổi mình phụ trách (`assistant_id`). Đây là điều kiện nghiệp vụ, không phải quyền vai đơn thuần.

## 4. Flow bàn giao giữa actor

| Người ghi | Người đọc | Vật bàn giao | Bằng chứng |
|---|---|---|---|
| Teacher / Assistant | Accountant | Bản ghi điểm danh | app/Policies/AttendancePolicy.php:55,59 |
| Manager | Accountant | Đề xuất thu | app/Enums/ChargeProposalStatus.php:19 |
| Hệ thống | Administrator | Tệp tải lên Drive | app/Jobs/UploadToDriveJob.php |

Chuỗi tài chính là bàn giao dây chuyền: **điểm danh → tổng học kỳ → đề xuất thu → phê duyệt → hóa đơn**. Không vai nào làm hết một mạch.

## 5. Trường trạng thái (enum) và nơi đổi trạng thái

| Entity | Enum (giá trị) | Bằng chứng |
|---|---|---|
| Attendance | AttendanceStatus: PRESENT, ABSENT, LATE | app/Enums/AttendanceStatus.php:12 |
| Charge Proposal | ChargeProposalStatus: PENDING, APPROVED, DISMISSED | app/Enums/ChargeProposalStatus.php:19 |
| Charge | ChargeStatus: PENDING, PARTIAL, PAID, VOIDED | app/Enums/ChargeStatus.php:15 |
| Class Room | ClassStatus: DRAFT, ACTIVE, CLOSED | app/Enums/ClassStatus.php:11 |
| Enrollment | EnrollmentStatus: ACTIVE, PAUSED, ENDED | app/Enums/EnrollmentStatus.php:15 |
| Tax Invoice | InvoiceStatus: PENDING_ISSUE, DEFERRED, ISSUED, NO_ISSUE, VOIDED | app/Enums/InvoiceStatus.php:21 |
| Room | RoomStatus: ACTIVE, MAINTENANCE, RETIRED | app/Enums/RoomStatus.php:11 |
| Class Session | SessionStatus: SCHEDULED, COMPLETED, CANCELLED | app/Enums/SessionStatus.php:14 |
| Student | StudentStatus: ACTIVE, INACTIVE, ARCHIVED | app/Enums/StudentStatus.php:14 |
| User | UserStatus: PENDING, ACTIVE, LOCKED | app/Enums/UserStatus.php:9 |

Tổng cộng **275 chỗ dùng enum trạng thái** trong code — mỗi vòng đời là một state machine riêng cần vẽ.

## 6. Biến thể kỹ thuật đã gom về một việc

| Biến thể | Mô tả | Bằng chứng |
|---|---|---|
| Chu kỳ thu không qua đề xuất | Bỏ bước đề xuất khi đủ điều kiện tự động | app/Features/Finance/Services/ChargeAutoApproval.php |
| Chu kỳ thu chạy thử | Chạy đúng đường thật trong một transaction rồi rollback | app/Features/Finance/Services/ChargeCycleRunner.php:68-91 |

Ghi chú nghiệp vụ đọc được từ mã nguồn: `ChargeCycleRunner` chủ động **không** đưa dry-run vào scheduler — nó là lệnh gõ tay, và nếu đưa vào cron, luật thật sẽ trôi khỏi mà không ai biết. Ứng dụng cũng bắt mọi tính toán theo **ngữ cảnh từng trung tâm**, không theo tiến trình, vì cron chạy không có phiên đăng nhập (`ChargeCycleRunner.php:107-112`).

## 7. Việc hệ thống tự chạy (không thuộc use case của actor)

| Việc | Bằng chứng |
|---|---|
| Chu kỳ thu hằng tháng | app/Features/Finance/Services/ChargeCycleRunner.php |
| Tự tạm dừng ghi danh khi nợ quá hạn | app/Features/Finance/Alerts/AutoPausedEnrollmentAlert.php |
| Cảnh báo học phí quá hạn | app/Features/Finance/Alerts/OverdueChargeAlert.php |
| Cảnh báo sắp hết buổi học | app/Features/Finance/Alerts/LowRemainingSessionsAlert.php |
| Bản tin tài chính định kỳ | app/Features/Finance/Alerts/FinanceDigestAlert.php |
| Tải tệp lên Drive | app/Jobs/UploadToDriveJob.php |

Không actor nào kích hoạt trực tiếp các việc này.

## 8. Câu hỏi đã tự tra từ code

Ba câu đầu trả lời được bằng cách đọc mã nguồn, không cần hỏi. Câu cuối vẫn cần Tường quyết.

### 8.1 Charge có tự sinh không? — KHÔNG

`Charge` **chỉ được tạo ra bên trong `ChargeProposalService::approve()`**, và hàm này là một đường duy nhất cho cả tay người lẫn máy:

- `approve(ChargeProposal $proposal, ?User $actor, bool $auto = false)` gọi `charges->generateCycle(...)` rồi mới ghi `ChargeProposal::APPROVED` kèm `charge_id` (app/Features/Finance/Services/ChargeProposalService.php:100,107,114-119).
- Máy tự duyệt dùng **cùng một hàm** với cờ `$auto = true`, cố ý không rẽ đường ghi nợ thứ hai — ghi chú tại dòng 95-98 nói rõ: "tự duyệt mà rẽ nhánh riêng là sớm muộn hai đường trôi khỏi nhau".
- Đề xuất đã có người quyết thì không đi vòng lần nữa (`status->isDecided()` chặn tại dòng 102, 159; app/Enums/ChargeProposalStatus.php:41).

→ Vẽ activity: **đề xuất chờ → quyết định → mới ghi nợ**. Không có nhánh "Charge tự sinh".

### 8.2 Điều kiện tự duyệt — 4 điều kiện, tất cả từ settings

`ChargeAutoApproval` chỉ **trả lời có/không**; việc ghi nợ vẫn qua `ChargeProposalService::approve()` (ghi chú dòng 32). Điều kiện tự duyệt khi **cả bốn** đều thoả:

| # | Điều kiện | Mặc định | Bằng chứng |
|---|---|---|---|
| 1 | `finance.auto_approve_enabled` bật | true | ChargeAutoApproval.php:40,60-62 |
| 2 | Kỳ đó **chưa có người quyết** | — | ChargeAutoApproval.php:65-67 |
| 3 | Cho phép kỳ chưa đánh dấu đủ, **hoặc** số buổi chưa đánh dấu bằng 0 | true | ChargeAutoApproval.php:55,69-71 |
| 4 | Số buổi vắng ≤ `finance.auto_approve_max_absences` | 0 | ChargeAutoApproval.php:46,72 |

Lưu ý nghiệp vụ quan trọng: từ 05/09 đề xuất **chỉ sinh cho buổi đã dạy xong** (`ChargeService::…`), và thông báo ngày 05/09 ghi rõ "kỳ nào đã có người quyết thì thôi — không đi vòng sau lưng kế toán".

### 8.3 VOIDED có quay lại được không? — KHÔNG

`VOIDED` là trạng thái cuối, không đường về:

- `PaymentService` ném `LogicException` khi thu vào charge đã huỷ (app/Features/Finance/Services/PaymentService.php:59-60), và kiểm tra lại cả sau khi khoá dòng (dòng 259-260).
- Mọi phép tính nợ lọc `status != 'VOIDED'` — khoản đã huỷ **không còn là khoản phải thu** (app/Features/Finance/Services/DebtCalculationService.php:148, CreditPoolService.php:157).
- `TaxInvoiceService.php:55` nói rõ: hoá đơn cũ VOIDED + hoá đơn mới cùng kỳ **là hợp lệ** — tức huỷ rồi phát hành lại bằng hoá đơn mới, không sửa hoá đơn cũ.

→ Vẽ state machine `Charge`: PENDING → PARTIAL → PAID, và VOIDED là nhánh kết thúc, không có mũi tên quay về.

### 8.4 Ai được sửa bản ghi điểm danh của vai khác? — theo QUYỀN, không theo sở hữu dữ liệu

Câu hỏi này tự trả lời được từ policy. `view` và `update` dùng **hai tiêu chí khác nhau**, và đó là điểm cần vẽ đúng:

| Hành động | Điều kiện | Bằng chứng |
|---|---|---|
| `viewAny` | Có vai admin, manager hoặc ketoan | app/Policies/AttendancePolicy.php:25-27 |
| `create` | Qua hẳn một nhánh kiểm tra khác (dòng 40-44) | app/Policies/AttendancePolicy.php:40 |
| `view` | Vai admin/manager/ketoan **hoặc** chính người đánh dấu (`marked_by_user_id`), hoặc trợ giảng phụ trách buổi đó (`assistant_id`) | app/Policies/AttendancePolicy.php:45-63 |
| `update` | **Cùng trung tâm** (`sameCenter`, chặn A01-01) **và** có quyền `attendances.update` | app/Policies/AttendancePolicy.php:66-73 |
| `delete` | **Cùng trung tâm** **và** có quyền `attendances.delete` | app/Policies/AttendancePolicy.php:75-82 |

**Kết luận để vẽ:** `view` là giới hạn theo quan hệ dữ liệu — giáo viên chỉ thấy bản ghi mình đánh dấu, trợ giảng chỉ thấy buổi mình phụ trách. Nhưng `update` và `delete` thì **không** có giới hạn đó: chỉ cần cùng trung tâm và có đúng quyền.

→ Nghĩa là một giáo viên có `attendances.update` **vẫn sửa được** bản ghi của trợ giảng trong cùng trung tâm. Đây là hành vi thật của hệ thống, vẽ đúng như vậy — không vẽ theo cảm tính.

→ Vẽ activity `Take Attendance`: bước đọc danh sách dùng quyền `view`, nhưng bước lưu chỉ cần `attendances.update` + cùng trung tâm.

### 8.5 Ai được ghi điểm danh? — KHÔNG phải ai cũng qua Policy

Câu này tôi từng nghĩ cần hỏi bạn. Tra được, và kết quả làm lộ một **khúc đứt thật**.

**Có hai đường ghi điểm danh, và chúng không dùng chung một cơ chế quyền:**

| Đường | Màn hình | Cơ chế kiểm tra | Ai dùng |
|---|---|---|---|
| Bảng thô | `AttendanceResource` (ẩn khỏi menu) | Laravel Policy | chỉ admin ghi, ketoan/manager chỉ xem |
| Màn nghiệp vụ | `SessionAttendance` | `AttendancePermission` (khác) | gv/tg dùng hằng ngày |

Chứng cứ ghi rõ trong chính policy:

- "Policy của bảng THÔ `attendances` … **Màn S05 dùng thật đi qua SessionAttendance + AttendancePermission, không qua policy này**" (app/Policies/AttendancePolicy.php:8-11).
- "Bảng thô liệt kê MỌI dòng điểm danh của center, không lọc 'buổi mình đứng'. DOCS S05: gv/tg chỉ ✏️ buổi mình → không cho vào bảng không lọc này (403)" (app/Policies/AttendancePolicy.php:16-18).

**Quyền thật trong database** (đọc trực tiếp `database/database.sqlite`):

| Vai | Số quyền | Quyền liên quan điểm danh |
|---|---|---|
| admin | 61 | `attendances.create`, `attendances.update`, `attendances.delete` |
| manager | 24 | không có |
| gv | 21 | **không có** — chỉ `session-attendance.view` |
| tg | 21 | **không có** — chỉ `session-attendance.view` |
| ketoan | 9 | không có (xem đối soát qua màn khác) |

**Phát hiện cần đưa vào báo cáo khách:** nếu ai đó cố ghi điểm danh qua bảng thô bằng tài khoản giáo viên hoặc trợ giảng, hệ thống sẽ **từ chối (403)** — đúng thiết kế. Nhưng đường nghiệp vụ `SessionAttendance` dùng cơ chế quyền khác, nên **phải kiểm riêng `AttendancePermission`** mới biết giáo viên có ghi được hay không. Hai cơ chế lệch nhau là chỗ dễ sinh bug khi ai đó đổi vai.

**Đọc tiếp `AttendancePermission::canMark()` — đây mới là luật thật, năm điều kiện theo thứ tự:**

| # | Điều kiện | Ai bị chặn | Bằng chứng |
|---|---|---|---|
| 1 | Buổi `CANCELLED` | mọi vai, kể cả admin | AttendancePermission.php:75-77 |
| 2 | Buổi chưa diễn ra (ngày > hôm nay) | mọi vai | AttendancePermission.php:81-83 |
| 3 | Vai `manager` hoặc `ketoan` | 2 vai này | AttendancePermission.php:85-87,35 |
| 4 | `admin` thì qua luôn — kể cả buổi cũ quá hạn | — | AttendancePermission.php:90-92 |
| 5 | Còn lại: phải **đứng đúng buổi đó** (`session_staff`) **và** còn trong hạn sửa (`EditWindow`) | gv, tg | AttendancePermission.php:94,105-114,121-123 |

Hai điểm đáng đưa vào activity diagram:

- **Điểm 2 có lý do đạo đức dữ liệu**: ghi chú nguyên văn — "'có mặt' ở một buổi tương lai không phải dữ liệu, nó là điều đoán" (dòng 79-80).
- **Điểm 1 có lý do nghiệp vụ**: ghi điểm danh cho buổi huỷ sẽ "đẻ ra giờ dạy ma ở S14" (dòng 74) — vì hóa đơn tính theo số buổi đã dạy.

Điểm cần cảnh báo khách: `staffsSession()` cố ý **không** nới sang `class_staff` — một lớp có thể có nhiều giáo viên thay phiên, nới ra thì giáo viên ca sáng tick được cả ca tối mình không dạy (dòng 100-103).

### 8.6 Ghi thu: vì sao có CÁI CHIA, không chỉ một chặn overpay?

Đây là câu tôi cứ tưởng chỉ cần vẽ `OverpayRejected`. Đọc code thì thấy có **hai
cửa**, và chỉ một cửa mới đúng với việc thật ở quầy.

**Cửa 1 — chặn cứng (`recordPayment`)**

| Kiểm tra | Bằng chứng |
|---|---|
| Số tiền phải > 0 | PaymentService.php:55-57 |
| Charge không ở trạng thái `VOIDED` | PaymentService.php:59-60 |
| Ngày thu nằm trong hạn cho phép | PaymentService.php:65 (`PaymentLimits::assertPaidOn`) |
| Khoá dòng charge rồi **tính lại** số còn phải thu | PaymentService.php:69-70 (`lockForUpdate` → `remainingAmount`) |
| Số tiền > số còn phải thu → `OverpayRejected` | PaymentService.php:72-74 |
| Trần một lần thu (đặt **sau** kiểm overpay) | PaymentService.php:79 |
| Trạng thái là **hệ quả**: còn 0 → `PAID`, còn dư → `PARTIAL` | PaymentService.php:96-99 |

Trạng thái không được set tay mà suy ra từ số dư — vẽ đúng như vậy. Biên lai cấp
**trong** transaction (PaymentService.php:93), nên "thu tiền xong mà mất biên lai"
là không thể xảy ra.

**Cửa 2 — tự chia (`recordCollection`, mới thêm 12/09)**

Docblock ghi rõ cả câu chuyện gốc (PaymentService.php:207-225): kỳ còn nợ
1.000.000đ, phụ huynh đưa 2.000.000đ, hệ thống chặn — và đó **không** phải luật,
đó là cái bẫt ở cửa quầy. Cách xử lý hiện tại:

- đúng `remainingAmount()` → gọi `recordPayment()` như cửa 1;
- phần dư → `recordDeposit()` vào quỹ "đóng khóa" của chính học sinh đó;
- quỹ đó tự cấn sang kỳ khác còn nợ theo **tháng cũ trước**
  (`CreditPoolService::applyToOpenCharges`, PaymentService.php:185).

→ Bất biến FR-FIN-02 giữ nguyên: **không kỳ nào nhận quá số còn phải thu**. Cái
đổi là chặn ở cửa quầy, không phải bỏ luật. Sơ đồ phải có nhánh "Parent paid
extra?" tách làm hai, không vẽ một nhánh lỗi duy nhất.

**Ba điều kiện phụ đã tra, đủ để vẽ được:**

- Kỳ **đã thu đủ** (`remainingAmount() <= 0`) → `ChargeAlreadySettled`, không tạo
  payment hay biên lai nào (PaymentService.php:224-225).
- Deposit không gắn charge, mà gắn học sinh — `charge_id = null`,
  `student_id = $student->id` (PaymentService.php:167-177). Chiều ngược lại của
  `recordPayment`. Đây là XOR dữ liệu, vẽ đúng để người đọc không tưởng mỗi
  khoản thu đều có một charge.
- Deposit cần biết `branch_id`; học sinh đang học ở nhiều cơ sở thì ném
  `AmbiguousBranchContext` (PaymentService.php:163, 328-351).

**Kết luận để vẽ activity `Collect Payment`:** nhánh lỗi dừng bằng ⊗ (mọi ném
xảy ra **trước** `DB::transaction`, nên bản ghi lỗi không sinh ra dòng thu nào),
còn nhánh hợp lệ đi qua một transaction duy nhất gồm: khoá charge → tạo
payment → cấp biên lai → cập nhật trạng thái → ghi audit.

### 8.7 Vì sao 2 lane của sơ đồ kỳ thu không rỗng?

Lần vẽ đầu, `Scheduler` và `Auto Approval` đều trống — và `gen` báo
`[uml lane-empty]`. Lane rỗng là **thiếu bằng chứng**, không phải lỗi bố cục:

- `Scheduler` có thật: `finance:propose-charges` chạy `dailyAt('06:30')`
  (bootstrap/app.php:136-137), qua `ProposeCharges` → `ChargeCycleRunner::run()`.
  Lệnh này là **transport**, luật nằm trong service (ProposeCharges.php:27).
- `Auto Approval` có thật: `ChargeAutoApproval` đọc settings rồi **chỉ trả lời
  có/không** (ChargeAutoApproval.php:32-33) — nên vẽ đúng một action
  "Read auto approval settings" rồi mới tới 3 decision điều kiện.

### 8.8 Kết luận: không còn câu hỏi nào cần Tường quyết

Toàn bộ mục 8 đã tự tra được từ code. Có thể vẽ.