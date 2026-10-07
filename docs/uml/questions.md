# Câu hỏi và xung đột — cần Tường trả lời

## Xung đột lint ↔ code

Mục này ghi chỗ lint của skill kiểu ÉP BỎ một phần tử có thật trong code (ví dụ use case/activity/sequence/state/package bắt bỏ một phần tử). KHÔNG dùng cho ERD vẽ từ code: ERD đặt `"source": "code"` và ghi `evidence` (file:dòng) thì chu trình và entity cô lập chỉ là WARN. Không xoá phần tử khỏi model, để nguyên ERROR của lint, và ghi một dòng:

`- <loại>/<tên file model> [<luật lint>]: <phần tử> (file:dòng) — lý do`

`uml.mjs run` đếm các dòng này để tách "xung đột lint↔code đã ghi" khỏi "lỗi khác".

## Câu hỏi nghiệp vụ

Hai câu dưới đây **không** tra được từ code — cần khách quyết. Mọi câu hỏi suy ra
từ code đã tự trả trong [`flows.md`](flows.md) mục 8.

### Q1 — `Record Payment` và `Record Collection` là một hay hai use case? ✅ ĐÃ CHỐT 05/10

**Tường chọn: tách thành 2 use case riêng.**

Cả hai đều nằm trên cùng màn hình và cùng một người thao tác (kế toán), nhưng khác
nhau về bản chất:

| | `recordPayment` | `recordCollection` |
|---|---|---|
| Khai báo hàm | `PaymentService.php:47` | `PaymentService.php:231` |
| Quá số còn phải thu | ném `OverpayRejected` (`:72-74`) | tự chia `applied`/`overflow` (`:274-275`), rồi `recordDeposit` (`:291`) |
| Kỳ đã thu đủ | không có nhánh riêng | ném `ChargeAlreadySettled` (`:270-272`) |

Khác biệt nằm ở **nghiệp vụ**, không chỉ ở giao diện: một bên từ chối, một bên tự phân bổ
tiền dư. Giữ chung một UC sẽ giấu mất chính khác biệt đó trong một nhánh phụ.

Bằng chứng cho thấy hai hàm **lệch nhau cả ở điều kiện đầu vào**, không chỉ ở cách xử lý quá số:

- `recordCollection` **từ chối** kỳ đã thu đủ bằng `ChargeAlreadySettled` (`:270-272`) — chính
  để chặn nguy cơ đẻ khoản đóng trước + phiếu thu thứ hai. `recordPayment` không có nhánh này.
- `recordCollection` **gọi lại** `recordPayment` ở `:281` cho phần vừa đủ, rồi mới
  `recordDeposit` cho phần dư (`:291`).

Nên `recordCollection` là UC bao trùm, còn `recordPayment` là UC bước con của nó — đúng cấu
trúc `«include»`, không phải hai UC ngang hàng. `recordDeposit` là đường thứ ba, tách riêng
khỏi cả hai.

**ĐÃ VẼ LẠI 05/10** — và ba điều chỉnh phát sinh, đều đo được từ code:

- Quan hệ cuối cùng là **`«extend»` chứ không phải `«include»`**: cả hai lời gọi đều nằm
  trong `if ($applied > 0)` (`:280`) và `if ($overflow > 0)` (`:284`) ⇒ **có điều kiện**,
  mà `«include»` theo UML 2.5 là luôn xảy ra. `recordDeposit` còn có nhánh `:287` ném lỗi
  khi charge không có học sinh.
- `Record Payment` **không có actor**: quét toàn repo, không UI nào gọi thẳng — chỉ
  `recordCollection:281`, test và seeder. `Record Deposit` **có** actor: UI gọi thẳng ở
  chế độ `MODE_DEPOSIT` (`app/Filament/Resources/ChargeResource/Pages/ListCharges.php:440`).
- Phát hiện thêm: `Decide Charge Proposals` trước đây **không có actor nào**. Đã sửa theo
  `app/Policies/ChargeProposalPolicy.php:27,50-52` — quyền `decide` chỉ cho `admin` + `ketoan`.
  Đây là lỗi có sẵn từ trước, không phải do tách UC.

Xem [usecase/README.md](usecase/README.md).

### Q2 — Nhắm mẫu trường nào? ✅ ĐÃ CHỐT 05/10

**Tường chọn: FPT / UIT (APU-style).**

`baseline.md` chốt thị trường là sinh viên năm cuối và đồ án cá nhân. Ba mẫu khác nhau ở
**mẫu hồ sơ bắt buộc**:

- khác nhau ở khối lượng UC kỳ vọng (mỗi khoảng 15–30 UC);
- khác nhau ở việc bắt buộc có ERD hay không;
- khác nhau ở yêu cầu "trang N trong file đóng góp" mà mỗi khoa đặt riêng.

Chọn mẫu FPT/UIT vì: có nhiều tài liệu mẫu công khai để đối chiếu, và là mẫu phổ biến với
dịch vụ freelance — giảm rủi ro ước sai khối lượng bàn giao.

**Hệ quả với giá:** phải ước theo mẫu này. **Đã khảo sát 05/10.**

#### Khảo sát mẫu hồ sơ FPT/UIT (nguồn mở thật, 05/10)

| Mục | FPT | UIT |
|---|---|---|
| Có quy định **số trang** cứng? | **Không** | **Không** |
| Cách chia tài liệu | SRS = Report 3, SDD (không phải SDS) = Report 4 | theo "Mẫu trình bày KLTN" của Khoa |
| Cấu trúc SRS | Overall Description → User Req → Functional Req → Non-Functional Req → Other Req | yêu cầu: phạm vi, tác nhân, chức năng/phi chức năng, UC, quy tắc nghiệp vụ, dữ liệu, tiêu chí chấp nhận |
| Quy mô thực hành | ước **20–40 trang** SRS + 20–40 trang SDD (không tính bìa/mục lục/tài liệu tham khảo/phụ lục) | như vậy, có thể dài hơn do phần kết quả |

Nguồn: [SWP490 capstone guide](https://www.studocu.vn/vn/document/truong-dai-hoc-fpt/capstone-project/capstone-project-guide-for-fpt-university-students-swp490/141097891) ·
[Capstone Report 3 — SRS](https://www.studocu.vn/vn/document/dai-hoc-fpt-ha-noi/software-requirement/capstone-project-report-3-software-requirements-specification-srs/122635049) ·
[UIT KLTN kỹ thuật phần mềm khóa 19](https://daa.uit.edu.vn/content/cu-nhan-nganh-ky-thuat-phan-mem-ap-dung-tu-khoa-19-2024) ·
[UIT nộp báo cáo KLTN 2025–2026](https://se.uit.edu.vn/vi/tin-t%E1%BB%A9c/10-thong-bao-hoc-vu/2146-th%C3%B4ng-b%C3%A1o-n%E1%BB%99p-b%C3%A1o-c%C3%A1o-kh%C3%B3a-lu%E1%BA%ADn-t%E1%BB%91t-nghi%E1%BB%87p-v%C3%A0-%C4%91%E1%BB%93-%C3%A1n-t%E1%BB%91t-nghi%E1%BB%87p-t%E1%BA%A1i-doanh-nghi%E1%BB%87p-%C4%91%E1%BB%A3t-1-n%C4%83m-h%E1%BB%8Dc-2025-2026.html)

**Phát hiện quan trọng nhất của Q2 — và nó làm đổi cách báo giá:**

**Cả hai trường đều không có số trang cứng.** Nghĩa là khách **không thể** đối chiếu
"2 UC là bao nhiêu trang", cũng **không** có điều kiện nào để mình hứa số trang cho hợp
lệ. Trước khi khảo sát, tôi đang định bán theo trang — đó sẽ là cam kết không có cơ sở.

Hệ quả trực tiếp: **giá phải theo độ lớn repo, không theo số trang và không theo số
diagram.** Lý do đã đo được ở [../baseline.md](../baseline.md): 3h21 cho 9 diagram, trong
đó máy chỉ 14,5s — thời gian nằm ở **đọc code**, không phải vẽ. Repo càng lớn thì càng
tốn thời gian đọc, dù số diagram không đổi.

Hệ quả thứ hai: vì không có chuẩn trang để bám, **không có lý do gì phải bàn giao đủ bộ 11
loại diagram**. Khách muốn 11 thì bàn giao 11; khách chỉ cần UC + ERD + activity thì 3
thứ đó — và giá theo repo, không theo số hình. Đây cũng là câu trả lời cho nỗi lo "cạnh
tranh với AI tự vẽ": AI vẽ nhanh nhưng **suy sai ý định**, mình đọc `file:dòng` nên đúng.

#### Bảng giá đề xuất (dựa trên số đo thật 05/10)

**Cơ sở tính toán — không phải ước tính vời:**

| Thành phần | Số đo |
|---|---|
| LMSERP-OneWorld (1.054 file, 153K LOC) → 9 diagram | **3h21** (12.060s) |
| Trong đó máy (scan + LLM + render) | **14,5s** (0,12%) |
| Trong đó con người (đọc code, chỉnh layout, bàn giao) | **200,8 phút** (99,88%) |
| Token/1 job (~157K input) | $0,05–$0,16 → **gần miễn phí** |
| Nguồn nhân giới hạn | **6,5h/tuần** — nhưng **"50% cho startup" là giả định, KHÔNG có số đo**; cụm này không xuất hiện ở bất kỳ đâu trong `baseline.md`. Xem `docs/baseline.md:60` (CAP-03). |

**→ Ràng buộc thật là thời gian người, không phải API hay render.**

> **BẢNG GIÁ BA GÓI Ở ĐÂY ĐÃ BỊ BỎ (06/10/2026).** Bản cũ có bảng Mini **150.000đ** / Standard
> **450.000đ** / Full **1.200.000đ** dựng trên đơn giá **150k/giờ** — một đơn giá không khớp bất kỳ neo
> nào và đã bị bỏ (`docs/baseline.md:362`, `docs/baseline.md:489` CASE-05). Giá chốt là **hai gói theo
> DỰ ÁN**: **2.000.000đ** (gói GỌN) và **2.500.000đ** (gói ĐẦY ĐỦ) — xem `docs/ke-hoach-startup.md` §4.
> Không bán theo từng hình, không bán theo giờ.

**Quy đổi giờ nội bộ (không phải giá bán):** 2.000.000đ ÷ 3h21 = **597.015đ/giờ** (`docs/baseline.md:92`).

**Lưu ý sống động (chưa kiểm chứng tiếp trên repo thứ hai):** job chính xác hơn theo **tỉ lệ thời gian
đọc code theo LOC**: 153K LOC → 200,8 phút người ⇒ **~1,3 phút/ngàn LOC**. Cập nhật sau job #2.

> **Đoạn này đã bị bỏ 06/10 (trái với §4 của kế hoạch).** Bản cũ ghi "số lượng diagram **không nằm trong
> giá**… thêm state/component thì **tính theo giờ thực tế**". Cả hai vế **sai**: giá chốt là **hai gói theo
> DỰ ÁN**, gói ĐẦY ĐỦ đã gộp **11 loại** và **không bán theo giờ** (`docs/ke-hoach-startup.md` §4).
> Repo lớn hơn mức gói ĐẦY ĐỦ thì **báo giá lại theo dự án**, không chuyển sang tính theo giờ.

**Còn giữ:** chỉ thanh toán khi **đã xong**; khách được xem demo `file:dòng` trước khi trả.

