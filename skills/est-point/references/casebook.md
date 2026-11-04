---

## document\_id: STORY\_POINT\_ESTIMATION\_REFERENCE title: Story Point Estimation Reference – Practical Casebook version: 1.0 status: baseline\_for\_team\_calibration language: vi point\_scale: \[1, 2, 3, 5, 8, 13, 21\] audience: \[BA, UX\_UI, Frontend, Backend, Mobile, QA, DevOps, TechLead, ProjectManager, AI\_Agent\] last\_updated: 2026-11-02

# STORY POINT ESTIMATION REFERENCE

## Practical Casebook – Version 1.0

**Mục đích:** Thống nhất cách đánh giá quy mô và độ phức tạp của Task trong đội ngũ phát triển phần mềm.

**Phạm vi:** BA, UI/UX Designer, Frontend Developer, Backend Developer, Mobile Developer, QA/Tester, DevOps, Tech Lead, Project Manager và AI Agent.

> **Baseline:** Đây là bộ tham chiếu khởi đầu. Không có bảng Point tuyệt đối áp dụng cho mọi tổ chức. Team phải hiệu chỉnh bằng các Task thực tế sau 3–5 Sprint.

## 1\. Quy ước Point chung

| Point | Phân loại | Mức độ công việc |
| :---- | :---- | :---- |
| 1 | Trivial | Rất nhỏ; phạm vi rõ; gần như không có rủi ro. |
| 2 | Simple | Đơn giản; một chức năng hoặc thay đổi nhỏ. |
| 3 | Standard | Công việc thông thường; có xử lý logic và kiểm thử. |
| 5 | Medium-High | Nhiều thành phần; có tích hợp hoặc xử lý ngoại lệ. |
| 8 | Complex | Nhiều luồng xử lý; phụ thuộc hoặc rủi ro đáng kể. |
| 13 | Very Complex | Phạm vi lớn hoặc nhiều điểm chưa rõ; cần chia nhỏ. |
| 21 | Epic | Không đưa trực tiếp vào Sprint; phải phân tích và chia nhỏ. |

- Không quy đổi Point thành giờ hoặc ngày công.  
- Đánh giá theo phạm vi và độ phức tạp tương đối của Task, không theo tốc độ cá nhân.  
- Chỉ dùng các mức Fibonacci: 1, 2, 3, 5, 8, 13, 21\.  
- Task 13 Point trở lên phải được xem xét phân rã; Task 21 Point không đưa trực tiếp vào Sprint.  
- Point phải bao gồm phần việc cần thiết để đáp ứng Acceptance Criteria và Definition of Done đã thống nhất.

## 2\. Case-by-case theo vai trò

### A. Frontend Development

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Thay đổi text, label | 1 | Không thay đổi layout hoặc logic. |
| 2 | Thay đổi màu, font, border | 1 | Có sẵn Design System. |
| 3 | Điều chỉnh spacing/kích thước component | 1 | Không ảnh hưởng responsive. |
| 4 | Thêm Button theo thiết kế có sẵn | 1 | Tái sử dụng component hiện có. |
| 5 | Thêm Input đơn giản | 2 | Có validation cơ bản. |
| 6 | Xây dựng Modal / Popup | 2 | Có thiết kế và component nền. |
| 7 | Bảng dữ liệu đơn giản | 3 | Có API; phân trang cơ bản. |
| 8 | Form nhập liệu | 3 | Validation, submit, loading và error state. |
| 9 | Trang Listing | 3 | Có API; loading, empty và error state. |
| 10 | Trang Detail | 3 | Có API; hiển thị dữ liệu và trạng thái. |
| 11 | Search UI | 3 | Search API đã có. |
| 12 | Filter nhiều điều kiện | 5 | Kết hợp filter, sort và pagination. |
| 13 | Dashboard nhiều biểu đồ | 5 | API và thư viện chart đã có. |
| 14 | Phân quyền hiển thị UI | 3 | Backend đã cung cấp permission. |
| 15 | Luồng đăng nhập nhiều bước | 5 | Có nhiều trạng thái và validation. |
| 16 | Realtime UI | 8 | WebSocket, reconnect và đồng bộ trạng thái. |
| 17 | Giao diện kéo-thả phức tạp | 8 | Nhiều trạng thái và xử lý dữ liệu. |
| 18 | Refactor toàn bộ Frontend Module | 13 | Phải chia nhỏ theo module. |

### B. Backend Development

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Thêm field vào Entity | 1 | Không có migration phức tạp. |
| 2 | API lấy dữ liệu đơn giản | 2 | Một bảng; logic đơn giản. |
| 3 | API CRUD cơ bản | 3 | Có validation và xử lý lỗi. |
| 4 | API Search / Filter | 3 | Truy vấn trên cấu trúc dữ liệu sẵn có. |
| 5 | API Pagination / Sorting | 2 | Không yêu cầu tối ưu đặc biệt. |
| 6 | API upload file | 3 | Có sẵn storage service. |
| 7 | API download file | 2 | Có sẵn cơ chế lưu trữ. |
| 8 | Role / Permission | 5 | Nhiều role và permission. |
| 9 | Đăng nhập JWT | 5 | Access token và refresh token. |
| 10 | Google / Facebook Login | 3 | OAuth provider và SDK đã có. |
| 11 | Email Notification | 3 | Có sẵn email provider. |
| 12 | Notification có trạng thái đọc | 5 | Có lưu trữ và trạng thái đọc/chưa đọc. |
| 13 | Realtime Notification | 8 | WebSocket và quản lý kết nối. |
| 14 | Tích hợp Payment Gateway | 8 | Tài liệu rõ, sandbox hoạt động; scope một provider. |
| 15 | Webhook | 5 | Xác thực chữ ký, idempotency và retry cơ bản. |
| 16 | Referral System | 8 | Có quy tắc thưởng và quan hệ giới thiệu. |
| 17 | Commission Calculation | 8 | Nhiều điều kiện và đối soát. |
| 18 | Tối ưu một truy vấn DB | 3 | Đã xác định query và nguyên nhân. |
| 19 | Thiết kế lại Database Module | 8 | Nhiều bảng và quan hệ. |
| 20 | Queue Processing | 8 | Queue, retry và failure handling. |
| 21 | Pipeline phân tích dữ liệu lớn | 13 | Nhiều nguồn, pipeline và yêu cầu hiệu năng. |

### C. Database Development

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Thêm một column | 1 | Migration đơn giản, tương thích dữ liệu hiện tại. |
| 2 | Thêm index cho một bảng | 1 | Đã xác định index và tác động. |
| 3 | Thêm một bảng mới | 2 | Schema đơn giản. |
| 4 | Tạo quan hệ giữa hai bảng | 2 | Quan hệ rõ, không chuyển đổi dữ liệu lớn. |
| 5 | Migration có chuyển đổi dữ liệu | 3 | Phạm vi giới hạn, có rollback/backup phù hợp. |
| 6 | Schema cho module nhỏ | 3 | Ít bảng, quan hệ đơn giản. |
| 7 | Schema nhiều quan hệ | 5 | Nhiều bảng và ràng buộc. |
| 8 | Tối ưu query nhiều JOIN | 5 | Có query plan và dữ liệu kiểm thử. |
| 9 | Xử lý dữ liệu trùng lặp quy mô lớn | 8 | Cần xác định quy tắc deduplicate và kiểm chứng. |
| 10 | Thay đổi cấu trúc DB đang vận hành | 8 | Cần migration an toàn và tương thích. |
| 11 | Migration nhiều module, bảo toàn dữ liệu | 13 | Chia nhỏ theo module/batch. |

### D. Mobile Development

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Thay text hoặc icon | 1 | Không đổi luồng. |
| 2 | Thay UI component đơn giản | 1 | Component có sẵn. |
| 3 | Màn hình thông tin | 2 | Layout và API đơn giản. |
| 4 | Form nhập liệu | 3 | Validation và trạng thái submit. |
| 5 | Tích hợp API vào một màn hình | 2 | API ổn định, mapping đơn giản. |
| 6 | Luồng đăng nhập | 5 | Token, trạng thái và xử lý lỗi. |
| 7 | Tích hợp Camera | 3 | Dùng API/thư viện chuẩn, không xử lý ảnh phức tạp. |
| 8 | Scan QR / Barcode | 5 | Camera permission, scan state và xử lý kết quả. |
| 9 | Push Notification | 5 | Tích hợp provider và xử lý deep link cơ bản. |
| 10 | GPS / Location | 5 | Permission, lấy vị trí và lỗi thường gặp. |
| 11 | Offline data và đồng bộ | 8 | Local persistence, conflict/retry cơ bản. |
| 12 | Background Processing | 8 | Có giới hạn nền tảng và xử lý vòng đời app. |
| 13 | In-App Purchase | 8 | Một store/platform flow theo scope đã xác định. |
| 14 | Tương thích nhiều phiên bản OS | 5 | Ma trận phiên bản và thiết bị giới hạn rõ. |
| 15 | Tối ưu hiệu năng toàn ứng dụng | 13 | Phải tách theo khu vực đo/triage/fix. |

### E. QA / Tester

> **Lưu ý:** Chỉ dùng bảng QA khi QA là công việc độc lập được quản lý thành Task riêng. Nếu Story đã bao gồm QA trong estimate thì không cộng thêm các Point này lần nữa.

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Kiểm tra thay đổi text / UI đơn giản | 1 | Một màn hình, một trạng thái. |
| 2 | Kiểm tra Button / Component | 1 | Một component, luồng chuẩn. |
| 3 | Kiểm thử Form cơ bản | 2 | Validation và submit. |
| 4 | Kiểm thử API đơn giản | 2 | Một endpoint, case chuẩn và lỗi phổ biến. |
| 5 | Kiểm thử CRUD | 3 | Các thao tác và validation chính. |
| 6 | Kiểm thử Search / Filter | 3 | Các điều kiện lọc đã xác định. |
| 7 | Kiểm thử luồng đăng nhập | 3 | Happy path và lỗi phổ biến. |
| 8 | Kiểm thử nhiều Role | 5 | Ma trận quyền và trường hợp truy cập trái phép. |
| 9 | Kiểm thử thanh toán | 5 | Sandbox, callback và trạng thái giao dịch. |
| 10 | Kiểm thử tích hợp nhiều hệ thống | 8 | Nhiều điểm tích hợp và lỗi liên hệ thống. |
| 11 | Regression một module | 5 | Bộ test module đã có. |
| 12 | Regression toàn hệ thống | 13 | Phải chia theo module hoặc release scope. |
| 13 | Automation Test API | 3 | Framework và môi trường đã có. |
| 14 | Automation một luồng UI | 5 | Framework đã có, một luồng chính. |
| 15 | Xây dựng Automation Framework | 13 | Phải chia theo nền tảng/lớp chức năng. |
| 16 | Performance Test một API | 3 | Có mục tiêu tải và môi trường. |
| 17 | Load Test một hệ thống | 5 | Có kịch bản, dữ liệu và ngưỡng đo. |
| 18 | Security Test một module | 8 | Phạm vi và phương pháp test xác định. |

### F. BA / Business Analysis

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Làm rõ yêu cầu đơn giản | 1 | Một vấn đề, stakeholder sẵn sàng. |
| 2 | Viết User Story đơn giản | 1 | Một actor và một kết quả rõ. |
| 3 | Viết Acceptance Criteria | 2 | Một story, các trường hợp chính. |
| 4 | Flow cho một chức năng | 2 | Một luồng chính và nhánh lỗi cơ bản. |
| 5 | Phân tích CRUD | 2 | Nghiệp vụ chuẩn. |
| 6 | Nghiệp vụ nhiều điều kiện | 3 | Có rule và ngoại lệ. |
| 7 | Quy trình liên phòng ban | 5 | Nhiều vai trò và bàn giao. |
| 8 | BRD cho một Module | 5 | Phạm vi module rõ. |
| 9 | Phân tích phân quyền | 5 | Nhiều role và ma trận quyền. |
| 10 | Phân tích tích hợp bên ngoài | 5 | Một hệ thống, tài liệu có sẵn. |
| 11 | Payment / Commission nghiệp vụ phức tạp | 8 | Đối soát, hoàn tiền, ngoại lệ và quy tắc. |
| 12 | Tái cấu trúc toàn bộ nghiệp vụ | 13 | Phải chia theo domain/module. |

### G. UI / UX Design

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Thay một icon | 1 | Asset có sẵn. |
| 2 | Điều chỉnh component | 1 | Không đổi interaction. |
| 3 | Thiết kế Popup | 1 | Một trạng thái chính. |
| 4 | Thiết kế Form | 2 | Một form, validation cơ bản. |
| 5 | Thiết kế màn hình đơn giản | 2 | Một viewport chính, component sẵn có. |
| 6 | Dashboard | 3 | Bố cục và biểu đồ theo yêu cầu rõ. |
| 7 | User flow một chức năng | 3 | Một luồng chính và nhánh cơ bản. |
| 8 | Nhiều trạng thái của chức năng | 5 | Loading, empty, error, success, disabled. |
| 9 | Module nhiều màn hình | 5 | Có flow và design pattern sẵn. |
| 10 | Design System | 8 | Phạm vi component được giới hạn. |
| 11 | Redesign toàn sản phẩm | 13 | Phải chia theo module/phase. |

### H. DevOps / System

| \# | Case công việc | Point | Điều kiện / phạm vi chuẩn |
| :---- | :---- | :---- | :---- |
| 1 | Thay Environment Variable | 1 | Một môi trường, quy trình sẵn. |
| 2 | Cấu hình Nginx đơn giản | 1 | Một route/vhost, không đổi kiến trúc. |
| 3 | SSL cho một domain | 2 | DNS và quyền quản trị sẵn. |
| 4 | CI cơ bản | 3 | Một repository, build/test cơ bản. |
| 5 | CD tự động | 3 | Một môi trường, pipeline chuẩn. |
| 6 | Docker cho một service | 3 | Dockerfile và dependency rõ. |
| 7 | Monitoring cơ bản | 3 | Một service, metric/alert chuẩn. |
| 8 | Backup tự động | 3 | Một database/service, retention rõ. |
| 9 | Centralized Logging | 5 | Một nhóm service, dashboard/search cơ bản. |
| 10 | Staging / Production environment | 5 | Kiến trúc và hạ tầng đã xác định. |
| 11 | Scaling | 8 | Một service, có metric và load profile. |
| 12 | High Availability | 13 | Phải chia theo thành phần hạ tầng. |
| 13 | Disaster Recovery | 13 | Phải chia theo RPO/RTO và hệ thống. |

## 3\. Bug fixing: phân biệt Severity và Point

| \# | Tình huống | Point tham khảo | Ghi chú |
| :---- | :---- | :---- | :---- |
| 1 | Sai text / label | 1 | Nguyên nhân rõ. |
| 2 | Sai màu / CSS | 1 | Một component. |
| 3 | Button không hoạt động do thiếu handler | 1 | Nguyên nhân đã xác định. |
| 4 | Sai validation một field | 2 | Có logic kiểm tra. |
| 5 | API mapping sai một field | 2 | Không đổi contract. |
| 6 | Lỗi pagination | 2 | Phạm vi một màn hình/API. |
| 7 | Filter nhiều điều kiện lỗi | 3 | Có tương tác nhiều điều kiện. |
| 8 | Lỗi tính toán nghiệp vụ | 3 | Một rule đã xác định. |
| 9 | Lỗi permission một chức năng | 5 | Cần kiểm tra nhiều role. |
| 10 | Lỗi đồng bộ giữa hai module | 5 | Có trace dữ liệu. |
| 11 | Payment callback lỗi | 8 | Có thể liên quan trạng thái và retry. |
| 12 | Mất dữ liệu trong giao dịch | 8 | Cần điều tra và bảo toàn dữ liệu. |
| 13 | Race condition / concurrency | 8 | Khó tái hiện và xác minh. |
| 14 | Lỗi kiến trúc ảnh hưởng nhiều module | 13 | Phải chia theo phạm vi sửa. |

- Severity đo mức độ ảnh hưởng; Point đo quy mô/độ phức tạp xử lý. Hai khái niệm độc lập.  
- Không mặc định Bug Critical \= 13 Point hoặc Bug Minor \= 1 Point.  
- Chỉ estimate sau khi có đủ thông tin để hiểu phạm vi điều tra và sửa. Nếu chưa rõ nguyên nhân, tạo Spike/Investigation riêng.

## 4\. Các yếu tố ảnh hưởng đến Point

| Yếu tố | Cách xem xét |
| :---- | :---- |
| Có component/module tái sử dụng | Có thể giảm độ phức tạp nếu thực sự giảm phạm vi xử lý. |
| Tài liệu API đầy đủ | Giảm uncertainty; không tự động giảm Point nếu logic vẫn phức tạp. |
| Yêu cầu nghiệp vụ chưa rõ | Làm rõ trước hoặc tạo Spike; không đoán Point. |
| Phụ thuộc hệ thống bên ngoài | Đánh giá khả năng tích hợp, sandbox, tài liệu và kiểm soát lỗi. |
| Nhiều trường hợp ngoại lệ | Tăng độ phức tạp xử lý và kiểm thử. |
| Bảo toàn/chuyển đổi dữ liệu | Xem xét backup, migration, rollback, kiểm chứng. |
| Realtime/concurrency | Xem xét reconnect, ordering, duplicate, race condition. |
| Nhiều nền tảng/thiết bị | Đánh giá phạm vi tương thích và ma trận kiểm thử. |
| Yêu cầu bảo mật đặc biệt | Xem xét threat model, permission, audit và test. |

> **Lưu ý:** Không cộng điểm cơ học cho từng yếu tố. Tổng hợp tác động rồi chọn một mức Fibonacci phù hợp.

## 5\. Chia nhỏ Task và tránh tính trùng

Ví dụ Epic/Story: Xây dựng hệ thống đăng ký tài khoản. Có thể phân rã thành các phần độc lập:

| Task con | Point minh họa |
| :---- | :---- |
| Thiết kế Database User | 2 |
| API đăng ký tài khoản | 3 |
| API xác thực Email | 3 |
| UI đăng ký | 3 |
| Validation và xử lý lỗi | 2 |
| QA luồng đăng ký | 3 |

- Các số trên chỉ dùng nếu từng task con được quản lý và estimate độc lập.  
- Nếu estimate Story cha, không cộng đồng thời Point Story cha và Point các Subtask vào tổng.  
- Task nên có một kết quả bàn giao kiểm chứng được; tránh chia nhỏ chỉ để tạo nhiều issue.

## 6\. Quy trình estimation

1. Người tạo Task cung cấp mô tả, mục tiêu, phạm vi và Acceptance Criteria.  
2. Team làm rõ câu hỏi nghiệp vụ/kỹ thuật trước khi estimate.  
3. Người tham gia estimate chọn Point độc lập (Planning Poker hoặc cách tương đương).  
4. Thảo luận các mức chênh lệch lớn; người có estimate cao/thấp giải thích giả định.  
5. Chốt một mức Point chung và ghi lại giả định quan trọng.  
6. Đưa Task vào Sprint khi đạt điều kiện Ready và còn capacity.  
7. Nếu scope thay đổi đáng kể, ghi nhận thay đổi; không sửa Point hồi tố để che sai lệch.

### Definition of Ready (DoR) tối thiểu

- Mục tiêu và phạm vi đủ rõ.  
- Acceptance Criteria có thể kiểm chứng.  
- Dependency đã được nêu; blocker quan trọng đã xử lý hoặc có kế hoạch.  
- Không còn câu hỏi trọng yếu khiến team phải đoán phạm vi.

### Definition of Done (DoD) tối thiểu

- Acceptance Criteria được đáp ứng.  
- Code đã review và merge theo quy trình.  
- Kiểm thử phù hợp đã hoàn thành; kết quả được ghi nhận.  
- Không còn lỗi Blocker/Critical thuộc phạm vi Task.  
- Tài liệu/cấu hình liên quan được cập nhật khi cần.  
- Được nghiệm thu theo quy trình dự án.

## 7\. Quy tắc vận hành và báo cáo

- Point là quy mô tương đối của công việc, không phải giờ công, ngày công hay KPI cá nhân.  
- Velocity chỉ nên so sánh trong cùng team và cùng quy ước estimate tương đối ổn định.  
- Không dùng tổng Point cá nhân để xếp hạng Developer/Tester/Designer.  
- Task chưa Done không được ghi nhận Completed Point; task bị reopen cần xử lý theo quy tắc team thống nhất, tránh ghi nhận hai lần.  
- Story Point chỉ được cộng một lần ở một cấp quản lý (Story hoặc Subtask).  
- Phân loại Product Development, Maintenance, Bug, Spike/Research và Operational Task để phân tích riêng khi cần.  
- Giữ Cycle Time và dữ liệu thời gian thực tế cho dự báo lịch, vận hành và chi phí; không quy đổi ngược thành Point.

| Chỉ số | Ý nghĩa |
| :---- | :---- |
| Committed Points | Tổng Point team dự kiến nhận trong Sprint. |
| Completed Points | Point của item đạt DoD trong Sprint. |
| Velocity | Trung bình Completed Points của các Sprint gần nhất; dùng để dự báo team. |
| Cycle Time | Thời gian từ lúc bắt đầu xử lý đến khi hoàn thành. |
| Bug/Reopen Rate | Theo dõi chất lượng và độ ổn định của đầu ra. |

## 8\. Hiệu chỉnh Casebook

1. Chạy thử trong 3–5 Sprint; không thay thang Fibonacci tùy tiện.  
2. Thu thập 30–50 Task thực tế đã hoàn thành, gồm nhiều loại công việc.  
3. Chọn các Task làm reference case; ghi rõ scope, giả định và Point đã thống nhất.  
4. Xem lại các cặp Task tương đương nhưng bị đánh lệch đáng kể.  
5. Cập nhật điều kiện áp dụng của casebook, không áp đặt một Point cố định cho mọi task cùng tên.  
6. Quản lý phiên bản tài liệu và thông báo thay đổi cho toàn team.

## 9\. Hướng dẫn cho AI Agent

- Đọc toàn bộ tài liệu này trước khi đề xuất Story Point.  
- Không tự suy diễn Point chỉ từ tiêu đề Task; phải đọc description, Acceptance Criteria, dependency và bối cảnh kỹ thuật.  
- Đầu ra đề xuất phải có: suggested\_point, rationale, assumptions, uncertainty, comparable\_cases, split\_recommendation và missing\_information.  
- Chỉ chọn một giá trị trong tập {1, 2, 3, 5, 8, 13, 21}.  
- Không quy đổi Point thành giờ/ngày; không cộng điểm cơ học theo checklist.  
- Nếu thiếu thông tin trọng yếu, hỏi lại hoặc đề xuất Spike; không giả vờ chắc chắn.  
- Nếu đề xuất 13 hoặc 21, phải giải thích vì sao chưa thể chia nhỏ và đề xuất cách phân rã.  
- Không tự thay đổi Point đã được team phê duyệt; chỉ đề xuất điều chỉnh khi scope thay đổi và phải có người có thẩm quyền xác nhận.  
- Không dùng Point để đánh giá/xếp hạng cá nhân.  
- Không cộng Point Story cha và Subtask; phải xác định rõ cấp ghi nhận.

### Output contract gợi ý cho AI Agent

```json
{
  "task_id": "ISSUE-123",
  "suggested_point": 5,
  "confidence": "medium",
  "rationale": [
    "Có nhiều trạng thái nghiệp vụ",
    "Tích hợp một API hiện hữu",
    "Cần xử lý các trường hợp lỗi"
  ],
  "assumptions": [
    "API contract đã ổn định",
    "Không bao gồm thay đổi database lớn"
  ],
  "uncertainty": [
    "Chưa xác nhận giới hạn retry"
  ],
  "comparable_cases": [
    "Backend: API Search / Filter - 3 Point",
    "Backend: Webhook - 5 Point"
  ],
  "split_recommendation": [],
  "missing_information": [
    "Quy tắc retry khi provider timeout"
  ],
  "human_approval_required": true
}
```

## 10\. Nguyên tắc cuối cùng

Story Point dùng để đo quy mô tương đối và hỗ trợ dự báo năng lực hoàn thành của team. Nó không phải phép đo thời gian làm việc, năng suất cá nhân hay giá trị kinh tế của một nhân sự.

Các case trong tài liệu là baseline tham khảo V1.0. Point cuối cùng phải được team thống nhất dựa trên scope thực tế, giả định kỹ thuật và các reference case đã được kiểm chứng.

---

## Appendix A – AI Agent decision checklist

Before suggesting a Point, the agent must verify:

1. Is the task scope explicit?  
2. Are Acceptance Criteria available?  
3. Are dependencies and integration boundaries known?  
4. Is the work comparable to a reference case in this document?  
5. Is uncertainty low enough to estimate, or should a Spike be created?  
6. Is the task too large and should it be decomposed?  
7. Is the Point being recorded at Story level or Subtask level (never both)?

If one or more critical inputs are missing, return `needs_clarification` or recommend a Spike instead of inventing a Point.

## Appendix B – Governance

- Document owner: Engineering / Project Management.  
- Approver: Engineering Lead or designated estimation owner.  
- Changes: Update version, change summary, effective date and affected teams.  
- AI agents may recommend; authorized humans approve and change official Point values.