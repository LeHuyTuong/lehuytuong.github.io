# Plan vẽ UML từ code — LMSERP-OneWorld

> Khung do `uml.mjs scan` sinh. Đọc FILE THẬT cho từng dòng rồi mới viết model. Use case và actor dưới đây là ĐỀ XUẤT từ tên handler và annotation phân quyền; không đoán nghiệp vụ: chỗ code mơ hồ thì ghi vào `questions.md` và hỏi Tường.

## 0. Hỏi Tường TRƯỚC khi vẽ (bắt buộc; điền câu trả lời, thay mọi "(chưa hỏi)")

| Câu hỏi | Trả lời |
|---|---|
| Repo và phạm vi (toàn repo hay một module) | **Đã chốt:** LMSERP-OneWorld, cả repo (1054 file, 153.417 LOC) |
| Tên hệ thống TIẾNG ANH trên diagram (subject, context) | **Đã chốt:** `LMSERP OneWorld` |
| Danh sách vai (từ quét: ?): giữ / gộp / đổi tên (ví dụ "Authenticated user" → "Student"; ghi vào `actors.json` rồi quét lại) | **Đã chốt (đọc `app/Enums/Role.php:10-14`, 5 vai ngang hàng, không có vai kế thừa vai):** Administrator, Manager, Teacher, Assistant, Accountant |
| Danh sách FLOW nghiệp vụ trong `flows.md` (tài nguyên × actor, flow bàn giao, hành trình tài khoản, việc hệ thống tự chạy, câu hỏi mục 8): Tường xác nhận / sửa TRƯỚC khi vẽ use case | **CHỜ Tường xác nhận.** `flows.md` đã điền từ `app/Policies/*.php` + `canAccess()` + service tài chính. Còn 4 câu hỏi ở mục 8 |
| Bộ diagram (mặc định: context, use case toàn hệ thống + mỗi vai một, activity UC chính, sequence+class từ activity, ERD, state, package, architecture, component) | **CHỐT SƠ BỘ:** context + use case toàn hệ thống + use case theo vai + activity cho UC chính. ERD/state/sequence để sau |
| Số feature chi tiết (activity + sequence/class) | **CHỐT SƠ BỘ:** 3 activity (Take Attendance, Run Monthly Charge Cycle, Collect Payment) |
| Thư mục xuất | **Đã chốt:** `/Volumes/SSD/Dev/active/startup-srs/docs/uml` — KHÔNG ghi vào repo OneWorld (repo đó do session khác phụ trách) |

> Mọi tên trên diagram (hệ thống, actor, use case, nhãn) bằng TIẾNG ANH; `run` báo ERROR `[lang]` khi có dấu tiếng Việt. Plan.md này có thể viết tiếng Việt nhưng tên UC/actor/diagram trong đó phải là tên tiếng Anh sẽ vẽ.

## 0b. Flow nghiệp vụ (đọc `flows.md` trước use case)

Thứ tự bắt buộc: **flows → (Tường xác nhận) → use case → activity → sequence/class**. `flows.json` rút 0 tài nguyên, 0 flow bàn giao giữa actor, 0 biến thể kỹ thuật gom lại, 0 việc hệ thống tự chạy, 17 câu hỏi; 0 mục tiêu actor (use case nháp). Mỗi use case trong model phải khai `routes` (["METHOD /path"]) và `evidence`; `run` đối chiếu model với `flows.json` (`[flow …]`). Mục 1a dưới đây là danh sách theo controller (cũ); khi lệch với mục tiêu ở `flows.md` mục 9 thì `flows.md` thắng.

## 1. Use case ↔ endpoint ↔ file code

> Tên UC dưới đây là TÊN TẠM do máy đặt từ tên handler. Đặt lại theo động từ nghiệp vụ (đọc handler + DTO) trước khi vẽ; không giữ nguyên tên như "View Auth".

### 1a. Tổng quan (danh sách cho use case diagram)

0 UC tổng quan từ 0 UC chi tiết: CRUD cùng feature + cùng nhóm actor gộp "Manage …", hành động nghiệp vụ riêng (approve, share, chat, purchase…) đứng riêng; 0 route hệ thống không tính.

| UC | Actor | Gồm UC chi tiết | Route |
|---|---|---|---|

### 1b. Chi tiết route → UC (chọn feature vẽ activity/sequence)

Nhóm theo động từ nghiệp vụ của handler và theo nhóm actor (route khác actor không chung UC), đánh số liên tục. 0 UC chi tiết cho 0 route. 0 route chưa suy được actor (ô actor `?`: code không có annotation/cấu hình bảo mật cho route đó — đọc code hoặc hỏi Tường, đừng bịa).

| UC | Actor (nguồn) | Endpoint | Handler (file:dòng) | Ghi chú |
|---|---|---|---|---|

> **Q1 đã chốt 05/10 và ĐÃ VẼ LẠI 05/10: `Record Payment` và `Record Collection` là HAI use case riêng.**
> Lý do: khác nhau về nghiệp vụ, không chỉ giao diện — `recordPayment` **từ chối** khi quá số
> phải thu (`PaymentService.php:47`, ném `OverpayRejected` ở `:72-74`), còn `recordCollection`
> (`:231`) **tự chia phần dư vào quỹ** (`:274-275`, `recordDeposit` ở `:291`).
>
> Ba điều chỉnh phát sinh khi vẽ lại, đều có bằng chứng:
> - Quan hệ là **`«extend»`**, không phải `«include»` — cả hai lời gọi nằm trong `if` (`:280`, `:284`) ⇒ có điều kiện.
> - `Record Payment` **không** có actor (UI không gọi thẳng); `Record Deposit` **có** actor (`ListCharges.php:440`).
> - `Decide Charge Proposals` trước đây **không có actor** — đã sửa, thêm Administrator + Accountant theo `ChargeProposalPolicy.php:27,50-52`.
>
> Kết quả: 5/6 sơ đồ per-role + `finance` + `operations` đều **0 error**; `role-accountant` 1 warning → **0 warning**.
> Riêng sơ đồ tổng quan `lmserp.drawio` còn 12 lỗi **có sẵn từ trước** (8 [path] + 4 [uml actor-gen]) —
> quét 32 tổ hợp chia phía actor, không tổ hợp nào đạt 0 ⇒ lỗi tải hình học, phải **tách diagram theo miền**. Chưa làm.

### 1c. Giao tiếp hệ thống (không đánh số UC)

Route của service mà chính repo gọi tới qua client HTTP (khác tiến trình), route kỹ thuật (health/config) và refresh token. Không phải use case của actor: vẽ ở sequence/architecture/component (hệ ngoài hoặc tiến trình phụ), không vào use case diagram.

| Route | Loại | Bằng chứng | Handler (file:dòng) |
|---|---|---|---|
| (không có) | | | |

## 2. Diagram định vẽ ↔ nguồn code

| Loại | File model | Nguồn code (file:dòng) | Ghi chú |
|---|---|---|---|
| context | context/system.model.json | thực thể: vai ở mục 1a (?) và dịch vụ BÊN THỨ BA ở mục 3 (API AI, cổng thanh toán, mail, SDK ngoài); KHÔNG đưa DB/kho riêng của hệ thống (MySQL, Postgres, Redis, vector store như Qdrant, S3 của chính hệ thống) vào: kho riêng nằm trong process DFD mức 0 | **XONG 05/10:** 7 entity (5 vai + Google Drive API + GitHub API), 14 mũi tên, 0 lỗi 0 cảnh báo qua cả 3 cổng (`check`, `--flows`, `--repo --model`). 7 hệ ngoài bị loại có lý do ghi trong `excludedExternals`. Chi tiết: `context/README.md` |
| usecase | **svc/usecase.model.json** | 2 actor: `Student` (khách), `Domain Reviewer` | **SƠ ĐỒ CỦA CHÍNH DỊCH VỤ NÀY** (không phải LMSERP): 10 UC, 5 association, 4 «include». Trả lời "khách trả tiền thì nhận được gì". `check`: 0 lỗi 0 cảnh báo |
| activity | **svc/activity.model.json** | `Student`, `System`, `Domain Reviewer` | **SƠ ĐỒ CỦA CHÍNH DỊCH VỤ NÀY** (không phải LMSERP): 3 lane, 8 action, 2 decision, 13 cạnh, `--level system`. `check`: 0 lỗi 0 cảnh báo; `verify_geometry.py`: 0 overlap / 0 xuyên hình / 0 cắt |
| usecase | usecase/system.model.json | MỌI vai và MỌI UC tổng quan ở mục 1a | MỘT diagram toàn hệ thống: "Manage X" là UC cha, thao tác là con (generalization); chức năng chung gom về actor cha (ví dụ "Registered User") |
| erd | erd/{domain,registry,finance,academic}.model.json | Hợp nhất: 33 entity + 83 quan hệ. Đã tách 3 sơ đồ theo bounded context (Tường duyệt 05/10) | **XONG 05/10: cả 3 sơ đồ `OK 0 error`.** `academic` 14 entity/18 quan hệ/**0 crossing**, `finance` 8/8/**0 crossing**, `registry` 10/21/**2 crossing** (ngân sách 3). **Không mất quan hệ:** 47 vẽ + 31 xuyên context + 5 của `Media Assets` (entity có y không vẽ) = 83. Nguồn 86 → 83 sau khi khử 3 quan hệ trùng khai hai nơi. ⚠️ **Đo crossing bằng `gen`, không phải `check`** (`check` không chạy layout nên luôn trả cùng một số). Chi tiết + các hướng đã thử và bị loại: `erd/README.md` |
| package | package/backend.model.json | profile `spring`, khung `Backend`, 6 package, 6 dependency | **XONG 05/10: 0 lỗi, 0 cảnh báo.** ⚠️ **Sơ đồ KHÔNG mô tả code repo này**: Tường chốt vẽ đủ 4 tầng chuẩn Spring khi repo không có `Repository`/interface, nhưng repo Laravel này **không có tầng Repository** và 34 chỗ DI đều class→class. Chỉ `Service` là tồn tại dưới dạng class cụ thể. Chi tiết: `package/README.md` |
| component | component/system.model.json | 6 component, 10 dependency | **XONG 05/10: 0 lỗi, 8 cảnh báo.** 8 cảnh báo là giới hạn bố trí tự động (đã thử **6 phương án**, bảng đo trong `component/README.md`), không phải lỗi nội dung. **KHÔNG vẽ interface/port/assembly connector** vì repo không có interface nào — vẽ lollipop/socket là bịa tầng trừu tượng không tồn tại. Chi tiết: `component/README.md` |
| state | state/attendancestatus.model.json | AttendanceStatus [backend/enum] (app/Enums/AttendanceStatus.php:10): PRESENT, ABSENT, LATE | **BỎ (05/10).** `saveBatch()` cố tình **xoá `LATE`** (`if ($status === LATE) $status = null`) — LATE gỡ khỏi UI 07/09, giữ enum cho dữ liệu lịch sử. Vẽ 3 state là vẽ thứ UI không cho nhập.
| state | state/chargeproposalstatus.model.json | ChargeProposalStatus [backend/enum] (app/Enums/ChargeProposalStatus.php:17): PENDING, APPROVED, DISMISSED | **XONG 05/10.** 3 chỗ gán tại `ChargeProposalService.php:84` (tạo → `PENDING`), `:115` (`APPROVED`, guard **điều kiện chưa đổi** — lệch thì `ChargeProposalStale::conditionsChanged()` rollback), `:165` (`DISMISSED`). `PENDING` là cổng một lối ra: `:160-161` chặn `isDecided()` nên **không có đường quay lại `PENDING`**. Kết quả: **0 lỗi 0 cảnh báo**, 3 state, 5 transition. Chi tiết: `state/README.md`
| state | state/chargestatus.model.json | ChargeStatus [backend/enum] (app/Enums/ChargeStatus.php:10): PENDING, PARTIAL, PAID, VOIDED | **XONG 05/10.** Chỉ 3 state dù enum có 4 case: **`ChargeStatus::VOIDED` là trạng thái chết** — grep `VOIDED` trong `app/`+`database/` ra 6 chỗ và tất cả đều là ĐỌC để loại trừ (`whereNotIn`, `!= VOIDED`, `reject`, ẩn nút thu tiền); không method nào gán, không seeder/factory nào sinh. Vẽ mũi tên tới nó là bịa. 4 chỗ gán thật, trong đó 3 chỗ (`ChargeService.php:348`, `PaymentService.php:98`, `CreditPoolService.php:215`) ghi **cùng biểu thức** `$remaining === 0 ? PAID : PARTIAL` → gộp thành transition có guard `[part payment]` / `[paid in full]`. Kết quả: **0 lỗi, 2 cảnh báo** (nhãn self-loop đè lên state — giới hạn layout đã đo 3 cách, xem `state/README.md`). Chi tiết: `state/README.md`
| state | state/classstatus.model.json | ClassStatus [backend/enum] (app/Enums/ClassStatus.php:9): DRAFT, ACTIVE, CLOSED | **BỎ (05/10).** `ScheduleGrid.php:726,833` gán `ACTIVE`; không thấy đường sang `CLOSED`.
| state | state/enrollmentstatus.model.json | EnrollmentStatus [backend/enum] (app/Enums/EnrollmentStatus.php:12): ACTIVE, PAUSED, ENDED | **BỎ (05/10).** Chỉ `PAUSED` có chỗ gán (`ChargeProposalService.php:180`, `ChargeCycleRunner.php:318`) và `ACTIVE` lúc tạo (`EnrollmentService.php:72`); **`ENDED` không có chỗ gán** → vẽ là bịa nửa vòng đời.
| state | state/invoicestatus.model.json | InvoiceStatus [backend/enum] (app/Enums/InvoiceStatus.php:19): PENDING_ISSUE, DEFERRED, ISSUED, NO_ISSUE, VOIDED | **SỬA LÝ DO 06/10 — lý do cũ SAI.** Bản cũ ghi "grep `InvoiceStatus::` = **0 kết quả**, enum không ai dùng" — **sai**: grep `app/` ra nhiều chỗ thật. `TaxInvoiceService.php:97` tạo hoá đơn với `PENDING_ISSUE`; `:235` gán `NO_ISSUE`; `:259` gán `VOIDED`; `InvoiceIssueDateService.php:50,65` trả `DEFERRED` và `:59,70` trả `ISSUED`; `TaxInvoiceService.php:141,144` đọc `ISSUED`. Enum **có vòng đời đầy đủ**. Vẫn **BỎ**, nhưng vì lý do khác: đây là enum của hệ thống **kế toán/thuế**, thuộc bounded context `finance`, không thuộc 9 diagram lõi của hành trình khách — và `finance` đã có ERD riêng. Vẽ nó là thêm việc ngoài phạm vi khách, **không phải vì "không ai dùng"**.
| state | state/roomstatus.model.json | RoomStatus [backend/enum] (app/Enums/RoomStatus.php:8): ACTIVE, MAINTENANCE, RETIRED | **SỬA LÝ DO 06/10 — lý do cũ SAI.** Bản cũ ghi "**không có `MAINTENANCE`** trong code" — **sai**: `Room.php:175` đọc `RoomStatus::MAINTENANCE` ngay trong guard chuyển sang `RETIRED` (`ACTIVE` **hoặc** `MAINTENANCE` chưa từng dùng → `RETIRED`), `RoomResource.php:73` tô màu cho nó, `:125,:266` cho nó trong dropdown UI. Cả 3 state đều có mặt thật. Vẫn **BỎ**, nhưng vì lý do khác: `Room.php:170-173` ghi rõ phòng "bảo trì" ở dữ liệu mẫu là **rác dữ liệu mẫu**, không phải admin đang sửa điện; vẽ `MAINTENANCE → RETIRED` là vẽ một nhánh mà chính hệ thống thừa nhận là không có tác nhân tạo ra.
| state | state/sessionstatus.model.json | SessionStatus [backend/enum] (app/Enums/SessionStatus.php:10): SCHEDULED, COMPLETED, CANCELLED | **XONG 05/10.** 3 chỗ gán: `SessionCompletion.php:141` (job đêm, ngày buổi ≤ hôm → `COMPLETED`), `DemoDataSeeder.php:224`, và `HolidayCancelService.php:53` → `CANCELLED` **với guard quan trọng: buổi chưa có điểm danh** (`HolidayCancelService.php:17-19` — thao tác hàng loạt nên không throw cho cả mẻ, chỉ báo số bị bỏ qua). Kết quả: **0 lỗi 0 cảnh báo**, 3 state, 5 transition. Chi tiết: `state/README.md`
| state | state/studentstatus.model.json | StudentStatus [backend/enum] (app/Enums/StudentStatus.php:10): ACTIVE, INACTIVE, ARCHIVED | **SỬA LÝ DO 06/10 — lý do cũ SAI.** Bản cũ ghi "Không chỗ gán nào ngoài cast `Student.php:78`" — **sai**: `StudentResource.php:350` khai FormSection "Trạng thái & ghi chú"; `:352-354` khai một `Select::make('status')` **bắt buộc** (`->required()`) trong FormSection "Trạng thái & ghi chú", `->options(self::enumOptions(StudentStatus::cases()))` và mặc định `ACTIVE`. Đó là đường gán thật qua UI, không phải chỉ là cast/seeder. Vẫn **BỎ**, nhưng vì lý do khác và yếu hơn: enum nằm ngoài **hành trình khách** đang vẽ, và các state được gán chỉ chứng minh "người dùng có thể chọn", không chứng minh có **vòng đời** (không tìm thấy luật chuyển nào giữa ACTIVE/INACTIVE/ARCHIVED trong code).
| state | state/userstatus.model.json | UserStatus [backend/enum] (app/Enums/UserStatus.php:5): PENDING, ACTIVE, LOCKED | **BỎ (05/10) — lý do ĐÚNG, nhưng thiếu một transition.** Phần "không có luồng `PENDING → LOCKED`" **chính xác và code tự xác nhận**: `EditUser.php:82` viết thẳng trong mô tả hộp thoại "PENDING → LOCKED bị cấm (chưa từng hoạt động). Mọi đường xoá cứng bị cấm." Phần "chỉ 3 chỗ gán `ACTIVE` trong seeder" thì thiếu: `EditUser.php:86` là **nút bật/tắt thật** — `$to = $record->status === UserStatus::LOCKED->value ? UserStatus::ACTIVE : UserStatus::LOCKED;` (`EditUser.php:86`), rồi `$record->transitionTo($to)` (`EditUser.php:89`) — tức có transition **`LOCKED ↔ ACTIVE` hai chiều**. Nếu sau này vẽ enum này thì phải vẽ cả nhánh khoá/mở khoá; chỉ vẽ 3 state trần là thiếu.
| package | package/backend.model.json | thư mục package trong repo; cạnh phụ thuộc ở inventory.json `packageDeps` (import + FQN) | chỉ tên ngắn; feature repo dùng tên thư mục thật |
| architecture | architecture/system.model.json | FE/BE/DB/dịch vụ ngoài ở mục 3 | |
| component | component/system.model.json | class/interface chính | |

### 2b. Activity ↔ sequence + class (thứ tự bắt buộc: use case → activity → sequence + class)

Mỗi feature seqclass phải có activity tương ứng; sequence viết TỪ activity, không vẽ thẳng từ code. Mỗi action lane System có ít nhất một message mang `step` (đúng nhãn action); decision thành `alt` với guard trùng nhãn nhánh; fork thành `par`. Class diagram chỉ gồm class xuất hiện làm lifeline cộng entity/DTO liên quan. `run` báo ERROR `[xc AF missing]` khi thiếu activity.

| seqclass | activity (điền một) | Ghi chú |
|---|---|---|
| `seqclass/take-attendance.model.json` | take-attendance.drawio | **XONG 05/10 — chốt `level: subsystem`, KHÔNG kèm class diagram.** Lý do giống UC21: `SessionAttendance` là Filament `Page` trên Livewire, không route trong `routes/`, không controller; `AttendanceBoardService.php:35` có DI thật nhưng không có `interface` nào dưới `app/Services/`, và level `software` bắt buộc ≥1 class tên kết thúc `Controller` (`seqclass.mjs:36`) — repo không có. **Quan trọng — activity cũ sai 3 chỗ so với code, đã sửa:** (1) `Closed?` không tồn tại, enum `SessionStatus` chỉ có `SCHEDULED`/`COMPLETED`/`CANCELLED` (`app/Enums/SessionStatus.php:12-14`); (2) `canMark()` có **5** điều kiện chứ không phải 4, activity thiếu luật *buổi tương lai*; (3) nhánh `Raise charge proposal for each absent student` là nhánh bịa — `saveBatch()` không gọi đề xuất phí, `ChargeCycleRunner` đọc `cycle_absences` ở job cron (grep `CycleAttendance` trong `app/` = 0 lời gọi, nó là struct của `CycleAttendanceCounter.php:62`). 4 nhánh từ chối mỗi nhánh một ⊗ riêng (engine chỉ cho 4 đỉnh neo, hội tụ 1 đích luôn chụm nhãn). Kết quả: activity **OK 0/0** + hình học 0/0/0, sequence **OK 0/0** (5 lifeline, 34 message, 3 fragment). Chi tiết: `seqclass/README.md` |
| `activity/charge-cycle.model.json` | charge-cycle.drawio | **XONG 05/10 — activity sai 2 chỗ so với code, đã sửa (bố cục xấu trước đó đang che lỗi nội dung).** (1) `autoPause()` chạy **trước** `propose()` và thoát sớm (`ChargeCycleRunner.php:148-156`), là việc **hệ thống tự làm** (`actor: null` tại :324 + `AutoPausedEnrollmentAlert` :335) — bản cũ vẽ nó thành quyết định "Pause enrollment?" *sau* khi kế toán từ chối, tức bịa cả người lẫn thời điểm. Đã dời lên `dNothing → dLongAbsent → pauseEnr → logPause → ffPaused`. (2) `shouldApprove()` trả false ở **cả 4** điều kiện (`ChargeAutoApproval.php:60-73`) và chỉ khi true mới gọi `autoApprove()` (`:196`) — bản cũ hội tụ 3 nhánh từ chối vào `mApprove`, tức vẽ "tự duyệt" cho cả những trường hợp **không đủ** điều kiện. Đã đổi `mAuto` → `mManual` nối `dDecision`, tách `approve` (kế toán) vs `autoApprove` (hệ thống) qua merge `mApproved` (`[5 edges]` bắt buộc qua merge). Kết quả: **0 error 3 warning**, 29 node, 33 cạnh; hình học 0 nhãn chồn / 0 cạnh xuyên hình / 2 bản ghi cắt (một cặp `e21`×`e31`) do 2 cạnh cùng vào `stop` và 3 cạnh cùng vào `mManual` — engine chỉ cho 4 đỉnh neo, cùng giới hạn đã ghi ở `mReject`. Đổi 5 thứ tự lane, tốt nhất `[Scheduler, Auto Approval, Finance Service, Proposal Service]` → 2 cắt. Chi tiết: `activity/README.md` |
| `seqclass/charge-cycle.model.json` | charge-cycle.drawio | **XONG 05/10 — chốt `level: subsystem` (sequence KHÔNG kèm class diagram), 29 message, 6 fragment.** Điểm dễ vẽ sai nhất và đã chốt được: **duyệt thì Runner gọi, bỏ thì người gọi** — `approve` có hai đường vào (`ChargeCycleRunner.php:273` cron, `ChargeProposalResource.php:290` UI), còn `dismiss` chỉ có đúng một (`ChargeProposalResource.php:345`; grep `dismiss` trong `ChargeCycleRunner.php` = **0** lần) ⇒ nhánh `[No]` phải đi từ `:Web App`, vẽ từ Runner là bịa. **Cổng hỏng KHÔNG tự bỏ đề xuất:** ba quyết định lồng chỉ chặn đường tự duyệt, rút gọn bằng `if ($recounted && shouldApprove(...) && autoApprove(...)) return;` (`ChargeCycleRunner.php:190`) — bản vẽ đầu của tôi đã đặt `dismiss` ở CẢ HAI nhánh của cổng, sai, đã bỏ. `generateCycle()` nằm TRONG `approve()` (`ChargeProposalService.php:107`, lịch sử ghi ở `ChargeCycleRunner.php:23`) nên vẽ là message lồng, không phải ngang hàng; nhánh `Charge created?` là kết quả tranh chấp `ChargeProposalStale` (`ChargeProposalResource.php:291`). `dEnabled`/`dUnmarked` hợp nhất về `mManual` ⇒ **không sinh `alt` nào** (action tới được từ cả hai nhánh bị loại khỏi cả hai tập operand) — đo được, không phải suy đoán. Kết quả: **0 error, 5 warning** (`alt` lồng tới bậc 6, `16.1.2.2.2.1.1`, chờ Tường chốt — cây quyết định thật, không tự rút). **Và phát hiện được bug bộ kiểm:** `check` báo 4 lỗi `[numbering]` trên model đúng vì `operandOf` trong `seqclass.mjs` đếm divider bằng `inside` — divider luôn nằm trong hộp mọi frame cha, nên alt lồng sâu bị đếm nhầm divider của frame CON (đo: `c18@y1742 x=363 w=1278` nằm trọn trong `fr2 x=135 w=1906`). Đã vá 3 chỗ (`dividersOf` lọc theo `x`/`w`), bản gốc `seqclass.mjs.bak-20261005-operandof`; sau khi vá charge-cycle **0 lỗi**, hai sequence cũ chạy lại vẫn **0/0**, không hồi quy. Chi tiết: `seqclass/README.md` |
| `seqclass/collect-payment.model.json` | collect-payment.drawio | **XONG 05/10 — chốt `level: subsystem` (sequence KHÔNG kèm class diagram).** Lý do: không có controller cho nghiệp vụ thu tiền (`app/Http/Controllers/` có 5 file nhưng **không file nào cho nghiệp vụ thu tiền**; `routes/web.php` chỉ 40 dòng với đúng một route redirect), cả hai điểm vào là **action closure ẩn danh** trong Filament (`ChargeResource.php:522`, `ListCharges.php:485`) nên không có bộ class nào để vẽ class diagram đáng tin. Lưu ý khác: thay vì vẽ Controller giả, sequence ghi thẳng `POST /livewire/update` → `:Web App` → `:Payment Service` với stereotype `«in-process»` (đã grep `Http::` / `Guzzle` / `curl_` / `file_get_contents` trong service tài chính = 0 lần, tức không có HTTP ngoài nào trong chuỗi). Kết quả: **0 error 0 warning**, 5 lifeline, 21 message, 3 fragment. Chi tiết: `seqclass/README.md` |

## 3. Hạ tầng đọc từ code

- DB: sqlite (.env.example:25); sqlite (config/database.php:20)
- Dịch vụ ngoài: drive.google.com (app/Jobs/UploadToDriveJob.php:61); fonts.bunny.net (app/Providers/Filament/AdminPanelProvider.php:114); www.googleapis.com (app/Services/GoogleDriveService.php:13); oauth2.googleapis.com (app/Services/GoogleDriveService.php:17); Redis (bootstrap/cache/services.php:22); Redis (config/cache.php:30); Redis (config/database.php:137); Mail/SMTP (config/mail.php:17); Redis (config/queue.php:27); Redis (config/session.php:17); drive.google.com (database/factories/MediaAssetFactory.php:32); drive.google.com (database/factories/QualificationFactory.php:51); js.pusher.com (public/js/filament/filament/echo.js:1); pusher.com (public/js/filament/filament/echo.js:1); github.com (public/js/filament/filament/echo.js:1); filepond.com (public/js/filament/forms/components/file-upload.js:1); github.com (public/js/filament/forms/components/file-upload.js:3); maxcdn.bootstrapcdn.com (public/js/filament/forms/components/markdown-editor.js:40); www.markdownguide.org (public/js/filament/forms/components/markdown-editor.js:40); docx (public/js/ow-docx-preview.min.js:7); stuk.github.io (public/js/ow-jszip.min.js:13); oneworld-dev.carbonx.io.vn (tmp/auth-session-extra.mjs:2); oneworld-dev.carbonx.io.vn (tmp/live-login-probe.mjs:14); oneworld-dev.carbonx.io.vn (tmp/live-role-route-probe.mjs:5); oneworld-dev.carbonx.io.vn (tmp/live-sqli-safe-probe.mjs:2); oneworld-dev.carbonx.io.vn (tmp/logout-probe.mjs:2); oneworld-dev.carbonx.io.vn (tmp/logout-probe2.mjs:2); admin.localhost (tmp/qa/cleanup-sch38b.cjs:21); admin.localhost (tmp/qa/cleanup-sch40.cjs:9); admin.localhost (tmp/qa/cleanup-sch49-classes.cjs:7); admin.localhost (tmp/qa/probe-att17.cjs:5); admin.localhost (tmp/qa/probe-att17c.cjs:5); admin.localhost (tmp/qa/probe-att17d.cjs:5); admin.localhost (tmp/qa/probe-att20.cjs:4); admin.localhost (tmp/qa/probe-hol14.cjs:14); admin.localhost (tmp/qa/probe-hol14b.cjs:35); admin.localhost (tmp/qa/probe-hol19-21.cjs:6); admin.localhost (tmp/qa/probe-hol19.cjs:3); admin.localhost (tmp/qa/probe-hol20-att.cjs:4); admin.localhost (tmp/qa/probe-hol21.cjs:3); gv.localhost (tmp/qa/probe-jnl09.cjs:5); gv.localhost (tmp/qa/probe-jnl24.cjs:5); gv.localhost (tmp/qa/probe-jnl24b.cjs:5); admin.localhost (tmp/qa/probe-sch38c.cjs:7); gv.localhost (tmp/qa/probe-sch44.cjs:11); admin.localhost (tmp/qa/probe-stu23.cjs:26); admin.localhost (tmp/qa/probe-stu23b.cjs:18); admin.localhost (tmp/qa/probe-usr40.php:31); oneworld-dev.carbonx.io.vn (tmp/session-security-probe.mjs:2); manager.t1043.localhost (tmp/team/t1043/append-j3j.py:13); Mail/SMTP (.env.example:54)

## 4. Gán trạng thái (nguồn cho transition) và bất đồng bộ (bằng chứng cho fork/par)

Chỉ chỗ GÁN (`setX`, `x = E.V`, builder, update) làm nguồn transition; chỗ đọc/so sánh (`countByStatus`, `findByStatus`, `==`) là điều kiện/guard, không phải transition.

| Enum.Giá trị | Loại | file:dòng | Dòng code |
|---|---|---|---|
| ChargeProposalStatus.PENDING | assign | tmp/qa/probe5.php:31 | `$ghost->status = ChargeProposalStatus::PENDING;` |
| ChargeProposalStatus.DISMISSED | assign | database/factories/ChargeProposalFactory.php:42 | `'status' => ChargeProposalStatus::DISMISSED,` |
| EnrollmentStatus.ACTIVE | assign | app/Filament/Resources/ClassRoomResource/RelationManagers/StudentsRelationManager.php:233 | `$change('resumeEnrollment', EnrollmentStatus::ACTIVE, 'Đi học lại', 'heroicon-o-play-circle', 'success'),` |
| EnrollmentStatus.PAUSED | assign | app/Filament/Resources/ClassRoomResource/RelationManagers/StudentsRelationManager.php:232 | `$change('pauseEnrollment', EnrollmentStatus::PAUSED, 'Bảo lưu', 'heroicon-o-pause-circle', 'warning'),` |
| EnrollmentStatus.ENDED | assign | app/Filament/Resources/ClassRoomResource/RelationManagers/StudentsRelationManager.php:234 | `$change('endEnrollment', EnrollmentStatus::ENDED, 'Nghỉ', 'heroicon-o-x-circle', 'danger'),` |
| SessionStatus.COMPLETED | assign | app/Services/Schedule/SessionCompletion.php:140 | `'status' => SessionStatus::COMPLETED->value,` |
| SessionStatus.COMPLETED | assign | database/seeders/DemoDataSeeder.php:224 | `->update(['status' => SessionStatus::COMPLETED->value]);` |
| SessionStatus.CANCELLED | assign | app/Services/Schedule/HolidayCancelService.php:56 | `'status' => SessionStatus::CANCELLED->value,` |
| StudentStatus.ARCHIVED | assign | tmp/qa/probe-stu22.php:53 | `$target->status = StudentStatus::ARCHIVED;` |

(93 chỗ dùng enum chưa phân loại gán/đọc — xem `stateRefs` trong inventory.json, loại `other`, đọc tay.)

| Dấu hiệu bất đồng bộ | Chi tiết | file:dòng |
|---|---|---|
| laravel queue/event |  | app/Jobs/UploadToDriveJob.php:18 |
| laravel queue/event |  | app/Livewire/ClassRoomNoteComponent.php:160 |
| laravel queue/event |  | app/Livewire/ClassRoomNoteComponent.php:191 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:73 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:113 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:119 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:136 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:142 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:164 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:178 |
| scheduler | scheduler: khởi chạy độc lập, KHÔNG phải fork trong luồng request | bootstrap/app.php:185 |

Chỉ vẽ fork/join (activity) hay `par` (sequence) khi một dòng ở bảng trên CHỨNG MINH hai việc chạy song song. Listener `@TransactionalEventListener` + `@Async` hay `.subscribe(` non-blocking là "trả lời trước, việc nền chạy sau", không phải nhánh song song trong cùng request. `@Scheduled` là luồng khởi chạy riêng.

## 5. Điểm mơ hồ cần hỏi Tường

Ghi vào `questions.md` (cùng thư mục): câu hỏi nghiệp vụ, và mục "Xung đột lint ↔ code" cho chỗ lint ép bỏ phần tử có thật.

