# Quan he xuyen bounded context

Tach tu `domain.model.json` (83 quan hệ). Moi sơ do context chi ve quan he
noi bo; 31 quan he xuyen context nay khong ve tren sơ do nao, nen duoc ghi day day du
de khong mat thong tin.

| Tu context | Den context | Quan he | Nhan | Card | Evidence |
|---|---|---|---|---|---|
| academic | registry | Attendance Records → Enrollments | enroll | `}o--o{` | `app/Models/Attendance.php:44` |
| academic | registry | Attendance Records → Users | assist | `}o--o{` | `app/Models/Attendance.php:67` |
| academic | registry | Class Room Notes → Users | act as | `}o--o{` | `app/Models/ClassRoomNote.php:187` |
| academic | registry | Class Rooms → Branches | operate in | `}o--o{` | `app/Models/ClassRoom.php:127` |
| academic | registry | Class Rooms → Enrollments | enroll | `}o--o{` | `app/Models/ClassRoom.php:156` |
| academic | registry | Class Rooms → Users | meet in | `}o--o{` | `app/Models/ClassStaff.php:43` |
| academic | registry | Class Sessions → Users | meet in | `}o--o{` | `app/Models/SessionStaff.php:39` |
| academic | registry | Curriculums → Branches | operate in | `}o--o{` | `app/Models/Curriculum.php:96` |
| academic | registry | Curriculums → Centers | belong to | `}o--o{` | `app/Models/Curriculum.php:91` |
| academic | registry | Holidays → Centers | belong to | `}o--o{` | `app/Models/Holiday.php:43` |
| academic | registry | Journal Entries → Users | write | `}o--o{` | `app/Models/JournalEntry.php:103` |
| academic | registry | Rooms → Branches | operate in | `}o--o{` | `app/Models/Room.php:211` |
| academic | registry | Rooms → Centers | belong to | `}o--o{` | `app/Models/Room.php:206` |
| academic | registry | Score Sheets → Users | create | `}o--o{` | `app/Models/ScoreSheet.php:37` |
| academic | registry | Scores → Enrollments | enroll | `}o--o{` | `app/Models/Score.php:50` |
| academic | registry | Session Journals → Users | open | `}o--o{` | `app/Models/SessionJournal.php:145` |
| academic | registry | Teaching Work Logs → Branches | operate in | `}o--o{` | `app/Models/TeachingWorkLog.php:97` |
| academic | registry | Teaching Work Logs → Centers | belong to | `}o--o{` | `app/Models/TeachingWorkLog.php:92` |
| academic | registry | Teaching Work Logs → Users | act as | `}o--o{` | `app/Models/TeachingWorkLog.php:82` |
| finance | academic | Charge Sessions → Class Sessions | meet in | `}o--o{` | `app/Models/ChargeSession.php:53` |
| finance | registry | Charge Proposals → Enrollments | enroll | `}o--o{` | `app/Models/ChargeProposal.php:68` |
| finance | registry | Charge Proposals → Users | decide | `}o--o{` | `app/Models/ChargeProposal.php:95` |
| finance | registry | Charge Sessions → Enrollments | enroll | `}o--o{` | `app/Models/ChargeSession.php:58` |
| finance | registry | Charges → Enrollments | enroll | `}o--o{` | `app/Models/Charge.php:188` |
| finance | registry | Payments → Students | teach | `}o--o{` | `app/Models/Payment.php:130` |
| finance | registry | Payments → Users | receive | `}o--o{` | `app/Models/Payment.php:147` |
| finance | registry | Receipts → Centers | belong to | `}o--o{` | `app/Models/Receipt.php:54` |
| finance | registry | Tax Invoices → Students | teach | `}o--o{` | `app/Models/TaxInvoice.php:92` |
| finance | registry | Tax Invoices → Users | issue | `}o--o{` | `app/Models/TaxInvoice.php:97` |
| registry | academic | Student Notes → Class Sessions | meet in | `}o--o{` | `app/Models/StudentNote.php:147` |
| registry | finance | Students → Charges | raise | `}o--o{` | `app/Models/Student.php:232` |

## Thuc the thuoc context nhung co y khong ve

Cac quan he duoi day thuoc ve thuc the ma khong nen ve len bat ky so do nao.

| Context | Quan he | Nhan | Card | Evidence |
|---|---|---|---|---|
| registry | Media Assets → Branches | operate in | `}o--o{` | `app/Models/MediaAsset.php:180` |
| registry | Media Assets → Centers | belong to | `}o--o{` | `app/Models/MediaAsset.php:175` |
| registry | Qualifications → Media Assets | evidence | `}o--o{` | `app/Models/Qualification.php:67` |
| registry | Student Notes → Media Assets | attach | `}o--o{` | `app/Models/StudentNote.php:179` |
| registry | Media Assets → Users | upload | `}o--o{` | `app/Models/MediaAsset.php:170` |
