#!/usr/bin/env node
/**
 * TechPulse & Agile Story Point Estimator Helper
 * Standalone tool for matching cases, applying learning curves, and formatting estimation contracts.
 */

const fs = require('fs');
const path = require('path');

const FIBONACCI_SCALE = [1, 2, 3, 5, 8, 13, 21];

const REFERENCE_CASES = {
  frontend: [
    { id: "FE-01", name: "Thay đổi text, label", point: 1, condition: "Không thay đổi layout hoặc logic." },
    { id: "FE-02", name: "Thay đổi màu, font, border", point: 1, condition: "Có sẵn Design System." },
    { id: "FE-03", name: "Điều chỉnh spacing/kích thước component", point: 1, condition: "Không ảnh hưởng responsive." },
    { id: "FE-04", name: "Thêm Button theo thiết kế có sẵn", point: 1, condition: "Tái sử dụng component hiện có." },
    { id: "FE-05", name: "Thêm Input đơn giản", point: 2, condition: "Có validation cơ bản." },
    { id: "FE-06", name: "Xây dựng Modal / Popup", point: 2, condition: "Có thiết kế và component nền." },
    { id: "FE-07", name: "Bảng dữ liệu đơn giản", point: 3, condition: "Có API; phân trang cơ bản." },
    { id: "FE-08", name: "Form nhập liệu", point: 3, condition: "Validation, submit, loading và error state." },
    { id: "FE-09", name: "Trang Listing", point: 3, condition: "Có API; loading, empty và error state." },
    { id: "FE-10", name: "Trang Detail", point: 3, condition: "Có API; hiển thị dữ liệu và trạng thái." },
    { id: "FE-11", name: "Search UI", point: 3, condition: "Search API đã có." },
    { id: "FE-12", name: "Filter nhiều điều kiện", point: 5, condition: "Kết hợp filter, sort và pagination." },
    { id: "FE-13", name: "Dashboard nhiều biểu đồ", point: 5, condition: "API và thư viện chart đã có." },
    { id: "FE-14", name: "Phân quyền hiển thị UI", point: 3, condition: "Backend đã cung cấp permission." },
    { id: "FE-15", name: "Luồng đăng nhập nhiều bước", point: 5, condition: "Có nhiều trạng thái và validation." },
    { id: "FE-16", name: "Realtime UI", point: 8, condition: "WebSocket, reconnect và đồng bộ trạng thái." },
    { id: "FE-17", name: "Giao diện kéo-thả phức tạp", point: 8, condition: "Nhiều trạng thái và xử lý dữ liệu." },
    { id: "FE-18", name: "Refactor toàn bộ Frontend Module", point: 13, condition: "Phải chia nhỏ theo module." }
  ],
  backend: [
    { id: "BE-01", name: "Thêm field vào Entity", point: 1, condition: "Không có migration phức tạp." },
    { id: "BE-02", name: "API lấy dữ liệu đơn giản", point: 2, condition: "Một bảng; logic đơn giản." },
    { id: "BE-03", name: "API CRUD cơ bản", point: 3, condition: "Có validation và xử lý lỗi." },
    { id: "BE-04", name: "API Search / Filter", point: 3, condition: "Truy vấn trên cấu trúc dữ liệu sẵn có." },
    { id: "BE-05", name: "API Pagination / Sorting", point: 2, condition: "Không yêu cầu tối ưu đặc biệt." },
    { id: "BE-06", name: "API upload file", point: 3, condition: "Có sẵn storage service." },
    { id: "BE-07", name: "API download file", point: 2, condition: "Có sẵn cơ chế lưu trữ." },
    { id: "BE-08", name: "Role / Permission", point: 5, condition: "Nhiều role và permission." },
    { id: "BE-09", name: "Đăng nhập JWT", point: 5, condition: "Access token và refresh token." },
    { id: "BE-10", name: "Google / Facebook Login", point: 3, condition: "OAuth provider và SDK đã có." },
    { id: "BE-11", name: "Email Notification", point: 3, condition: "Có sẵn email provider." },
    { id: "BE-12", name: "Notification có trạng thái đọc", point: 5, condition: "Có lưu trữ và trạng thái đọc/chưa đọc." },
    { id: "BE-13", name: "Realtime Notification", point: 8, condition: "WebSocket và quản lý kết nối." },
    { id: "BE-14", name: "Tích hợp Payment Gateway", point: 8, condition: "Tài liệu rõ, sandbox hoạt động; scope một provider." },
    { id: "BE-15", name: "Webhook", point: 5, condition: "Xác thực chữ ký, idempotency và retry cơ bản." },
    { id: "BE-16", name: "Referral System", point: 8, condition: "Có quy tắc thưởng và quan hệ giới thiệu." },
    { id: "BE-17", name: "Commission Calculation", point: 8, condition: "Nhiều điều kiện và đối soát." },
    { id: "BE-18", name: "Tối ưu một truy vấn DB", point: 3, condition: "Đã xác định query và nguyên nhân." },
    { id: "BE-19", name: "Thiết kế lại Database Module", point: 8, condition: "Nhiều bảng và quan hệ." },
    { id: "BE-20", name: "Queue Processing", point: 8, condition: "Queue, retry và failure handling." },
    { id: "BE-21", name: "Pipeline phân tích dữ liệu lớn", point: 13, condition: "Nhiều nguồn, pipeline và yêu cầu hiệu năng." }
  ],
  database: [
    { id: "DB-01", name: "Thêm một column", point: 1, condition: "Migration đơn giản, tương thích dữ liệu hiện tại." },
    { id: "DB-02", name: "Thêm index cho một bảng", point: 1, condition: "Đã xác định index và tác động." },
    { id: "DB-03", name: "Thêm một bảng mới", point: 2, condition: "Schema đơn giản." },
    { id: "DB-04", name: "Tạo quan hệ giữa hai bảng", point: 2, condition: "Quan hệ rõ, không chuyển đổi dữ liệu lớn." },
    { id: "DB-05", name: "Migration có chuyển đổi dữ liệu", point: 3, condition: "Phạm vi giới hạn, có rollback/backup." },
    { id: "DB-06", name: "Schema cho module nhỏ", point: 3, condition: "Ít bảng, quan hệ đơn giản." },
    { id: "DB-07", name: "Schema nhiều quan hệ", point: 5, condition: "Nhiều bảng và ràng buộc." },
    { id: "DB-08", name: "Tối ưu query nhiều JOIN", point: 5, condition: "Có query plan và dữ liệu kiểm thử." },
    { id: "DB-09", name: "Xử lý dữ liệu trùng lặp quy mô lớn", point: 8, condition: "Cần xác định quy tắc deduplicate và kiểm chứng." },
    { id: "DB-10", name: "Thay đổi cấu trúc DB đang vận hành", point: 8, condition: "Cần migration an toàn và tương thích." },
    { id: "DB-11", name: "Migration nhiều module, bảo toàn dữ liệu", point: 13, condition: "Chia nhỏ theo module/batch." }
  ],
  mobile: [
    { id: "MO-01", name: "Thay text hoặc icon", point: 1, condition: "Không đổi luồng." },
    { id: "MO-02", name: "Thay UI component đơn giản", point: 1, condition: "Component có sẵn." },
    { id: "MO-03", name: "Màn hình thông tin", point: 2, condition: "Layout và API đơn giản." },
    { id: "MO-04", name: "Form nhập liệu", point: 3, condition: "Validation và trạng thái submit." },
    { id: "MO-05", name: "Tích hợp API vào một màn hình", point: 2, condition: "API ổn định, mapping đơn giản." },
    { id: "MO-06", name: "Luồng đăng nhập", point: 5, condition: "Token, trạng thái và xử lý lỗi." },
    { id: "MO-07", name: "Tích hợp Camera", point: 3, condition: "Dùng API/thư viện chuẩn, không xử lý ảnh phức tạp." },
    { id: "MO-08", name: "Scan QR / Barcode", point: 5, condition: "Camera permission, scan state và xử lý kết quả." },
    { id: "MO-09", name: "Push Notification", point: 5, condition: "Tích hợp provider và xử lý deep link cơ bản." },
    { id: "MO-10", name: "GPS / Location", point: 5, condition: "Permission, lấy vị trí và lỗi thường gặp." },
    { id: "MO-11", name: "Offline data và đồng bộ", point: 8, condition: "Local persistence, conflict/retry cơ bản." },
    { id: "MO-12", name: "Background Processing", point: 8, condition: "Có giới hạn nền tảng và xử lý vòng đời app." },
    { id: "MO-13", name: "In-App Purchase", point: 8, condition: "Một store/platform flow theo scope đã xác định." },
    { id: "MO-14", name: "Tương thích nhiều phiên bản OS", point: 5, condition: "Ma trận phiên bản và thiết bị giới hạn rõ." },
    { id: "MO-15", name: "Tối ưu hiệu năng toàn ứng dụng", point: 13, condition: "Phải tách theo khu vực đo/triage/fix." }
  ],
  qa: [
    { id: "QA-01", name: "Kiểm tra thay đổi text / UI đơn giản", point: 1, condition: "Một màn hình, một trạng thái." },
    { id: "QA-02", name: "Kiểm tra Button / Component", point: 1, condition: "Một component, luồng chuẩn." },
    { id: "QA-03", name: "Kiểm thử Form cơ bản", point: 2, condition: "Validation và submit." },
    { id: "QA-04", name: "Kiểm thử API đơn giản", point: 2, condition: "Một endpoint, case chuẩn và lỗi phổ biến." },
    { id: "QA-05", name: "Kiểm thử CRUD", point: 3, condition: "Các thao tác và validation chính." },
    { id: "QA-06", name: "Kiểm thử Search / Filter", point: 3, condition: "Các điều kiện lọc đã xác định." },
    { id: "QA-07", name: "Kiểm thử luồng đăng nhập", point: 3, condition: "Happy path và lỗi phổ biến." },
    { id: "QA-08", name: "Kiểm thử nhiều Role", point: 5, condition: "Ma trận quyền và trường hợp trái phép." },
    { id: "QA-09", name: "Kiểm thử thanh toán", point: 5, condition: "Sandbox, callback và trạng thái." },
    { id: "QA-10", name: "Kiểm thử tích hợp nhiều hệ thống", point: 8, condition: "Nhiều điểm tích hợp và lỗi liên hệ thống." },
    { id: "QA-11", name: "Regression một module", point: 5, condition: "Bộ test module đã có." },
    { id: "QA-12", name: "Regression toàn hệ thống", point: 13, condition: "Phải chia theo module/release." }
  ],
  ba: [
    { id: "BA-01", name: "Làm rõ yêu cầu đơn giản", point: 1, condition: "Một vấn đề, stakeholder sẵn sàng." },
    { id: "BA-02", name: "Viết User Story đơn giản", point: 1, condition: "Một actor và một kết quả rõ." },
    { id: "BA-03", name: "Viết Acceptance Criteria", point: 2, condition: "Một story, các trường hợp chính." },
    { id: "BA-04", name: "Flow cho một chức năng", point: 2, condition: "Một luồng chính và nhánh lỗi cơ bản." },
    { id: "BA-05", name: "Phân tích CRUD", point: 2, condition: "Nghiệp vụ chuẩn." },
    { id: "BA-06", name: "Nghiệp vụ nhiều điều kiện", point: 3, condition: "Có rule và ngoại lệ." },
    { id: "BA-07", name: "Quy trình liên phòng ban", point: 5, condition: "Nhiều vai trò và bàn giao." },
    { id: "BA-08", name: "BRD cho một Module", point: 5, condition: "Phạm vi module rõ." },
    { id: "BA-09", name: "Phân tích phân quyền", point: 5, condition: "Nhiều role và ma trận quyền." },
    { id: "BA-10", name: "Phân tích tích hợp bên ngoài", point: 5, condition: "Một hệ thống, tài liệu có sẵn." },
    { id: "BA-11", name: "Payment / Commission nghiệp vụ phức tạp", point: 8, condition: "Đối soát, hoàn tiền, ngoại lệ." },
    { id: "BA-12", name: "Tái cấu trúc toàn bộ nghiệp vụ", point: 13, condition: "Phải chia theo domain/module." }
  ],
  uiux: [
    { id: "UX-01", name: "Thay một icon", point: 1, condition: "Asset có sẵn." },
    { id: "UX-02", name: "Điều chỉnh component", point: 1, condition: "Không đổi interaction." },
    { id: "UX-03", name: "Thiết kế Popup", point: 1, condition: "Một trạng thái chính." },
    { id: "UX-04", name: "Thiết kế Form", point: 2, condition: "Một form, validation cơ bản." },
    { id: "UX-05", name: "Thiết kế màn hình đơn giản", point: 2, condition: "Một viewport chính, component sẵn có." },
    { id: "UX-06", name: "Dashboard", point: 3, condition: "Bố cục và biểu đồ theo yêu cầu rõ." },
    { id: "UX-07", name: "User flow một chức năng", point: 3, condition: "Một luồng chính và nhánh cơ bản." },
    { id: "UX-08", name: "Nhiều trạng thái của chức năng", point: 5, condition: "Loading, empty, error, success, disabled." },
    { id: "UX-09", name: "Module nhiều màn hình", point: 5, condition: "Có flow và design pattern sẵn." },
    { id: "UX-10", name: "Design System", point: 8, condition: "Phạm vi component được giới hạn." },
    { id: "UX-11", name: "Redesign toàn sản phẩm", point: 13, condition: "Phải chia theo module/phase." }
  ],
  devops: [
    { id: "DO-01", name: "Thay Environment Variable", point: 1, condition: "Một môi trường, quy trình sẵn." },
    { id: "DO-02", name: "Cấu hình Nginx đơn giản", point: 1, condition: "Một route/vhost, không đổi kiến trúc." },
    { id: "DO-03", name: "SSL cho một domain", point: 2, condition: "DNS và quyền quản trị sẵn." },
    { id: "DO-04", name: "CI cơ bản", point: 3, condition: "Một repository, build/test cơ bản." },
    { id: "DO-05", name: "CD tự động", point: 3, condition: "Một môi trường, pipeline chuẩn." },
    { id: "DO-06", name: "Docker cho một service", point: 3, condition: "Dockerfile và dependency rõ." },
    { id: "DO-07", name: "Monitoring cơ bản", point: 3, condition: "Một service, metric/alert chuẩn." },
    { id: "DO-08", name: "Backup tự động", point: 3, condition: "Một database/service, retention rõ." },
    { id: "DO-09", name: "Centralized Logging", point: 5, condition: "Một nhóm service, dashboard/search cơ bản." },
    { id: "DO-10", name: "Staging / Production environment", point: 5, condition: "Kiến trúc và hạ tầng đã xác định." },
    { id: "DO-11", name: "Scaling", point: 8, condition: "Một service, có metric và load profile." },
    { id: "DO-12", name: "High Availability", point: 13, condition: "Phải chia theo thành phần hạ tầng." },
    { id: "DO-13", name: "Disaster Recovery", point: 13, condition: "Phải chia theo RPO/RTO và hệ thống." }
  ],
  bugs: [
    { id: "BUG-01", name: "Sai text / label", point: 1, condition: "Nguyên nhân rõ." },
    { id: "BUG-02", name: "Sai màu / CSS", point: 1, condition: "Một component." },
    { id: "BUG-03", name: "Button không hoạt động do thiếu handler", point: 1, condition: "Nguyên nhân đã xác định." },
    { id: "BUG-04", name: "Sai validation một field", point: 2, condition: "Có logic kiểm tra." },
    { id: "BUG-05", name: "API mapping sai một field", point: 2, condition: "Không đổi contract." },
    { id: "BUG-06", name: "Lỗi pagination", point: 2, condition: "Phạm vi một màn hình/API." },
    { id: "BUG-07", name: "Filter nhiều điều kiện lỗi", point: 3, condition: "Có tương tác nhiều điều kiện." },
    { id: "BUG-08", name: "Lỗi tính toán nghiệp vụ", point: 3, condition: "Một rule đã xác định." },
    { id: "BUG-09", name: "Lỗi permission một chức năng", point: 5, condition: "Cần kiểm tra nhiều role." },
    { id: "BUG-10", name: "Lỗi đồng bộ giữa hai module", point: 5, condition: "Có trace dữ liệu." },
    { id: "BUG-11", name: "Payment callback lỗi", point: 8, condition: "Liên quan trạng thái và retry." },
    { id: "BUG-12", name: "Mất dữ liệu trong giao dịch", point: 8, condition: "Cần điều tra và bảo toàn dữ liệu." },
    { id: "BUG-13", name: "Race condition / concurrency", point: 8, condition: "Khó tái hiện và xác minh." },
    { id: "BUG-14", name: "Lỗi kiến trúc ảnh hưởng nhiều module", point: 13, condition: "Phải chia theo phạm vi sửa." }
  ]
};

function snapToFibonacci(val) {
  let closest = FIBONACCI_SCALE[0];
  let minDiff = Math.abs(val - closest);
  for (const f of FIBONACCI_SCALE) {
    const diff = Math.abs(val - f);
    if (diff < minDiff) {
      minDiff = diff;
      closest = f;
    }
  }
  return closest;
}

function searchCases(query) {
  const q = query.toLowerCase();
  const results = [];
  for (const [role, cases] of Object.entries(REFERENCE_CASES)) {
    for (const c of cases) {
      if (c.name.toLowerCase().includes(q) || c.condition.toLowerCase().includes(q) || c.id.toLowerCase().includes(q)) {
        results.push({ role, ...c });
      }
    }
  }
  return results;
}

function applyTechPulseModifier(basePoint, level = 'junior', repeatCount = 1) {
  let modifier = 1.0;
  if (level.toLowerCase() === 'senior') {
    modifier *= 0.5;
  }
  if (repeatCount === 2) {
    modifier *= 0.7;
  } else if (repeatCount >= 3) {
    modifier *= 0.4;
  }
  const adjusted = basePoint * modifier;
  const fibPoint = snapToFibonacci(adjusted);
  return { basePoint, level, repeatCount, adjusted: Math.round(adjusted * 100) / 100, fibPoint };
}

// CLI Routing
const args = process.argv.slice(2);
const cmd = args[0];

if (!cmd || cmd === 'help') {
  console.log(`
Usage:
  node estimate.js search <keyword>           Search casebook
  node estimate.js list [role]                List cases for role (frontend, backend, etc.)
  node estimate.js calc <basePoint> [senior|junior] [repeat 1|2|3]  Calculate with TechPulse modifiers
  node estimate.js contract <taskId> <point> <confidence> <summary>  Print JSON contract
  `);
  process.exit(0);
}

if (cmd === 'search') {
  const query = args.slice(1).join(' ');
  const res = searchCases(query);
  console.log(`Found ${res.length} matches for "${query}":`);
  res.forEach(r => {
    console.log(`- [${r.role.toUpperCase()}] ${r.id}: ${r.name} (${r.point}pt) -> ${r.condition}`);
  });
} else if (cmd === 'list') {
  const role = (args[1] || '').toLowerCase();
  if (role && REFERENCE_CASES[role]) {
    console.log(`=== ${role.toUpperCase()} CASES ===`);
    REFERENCE_CASES[role].forEach(c => console.log(`${c.id}: ${c.name} (${c.point}pt) - ${c.condition}`));
  } else {
    for (const r of Object.keys(REFERENCE_CASES)) {
      console.log(`\n=== ${r.toUpperCase()} (${REFERENCE_CASES[r].length} cases) ===`);
      REFERENCE_CASES[r].forEach(c => console.log(`  ${c.id}: ${c.name} (${c.point}pt) - ${c.condition}`));
    }
  }
} else if (cmd === 'calc') {
  const base = parseFloat(args[1]) || 3;
  const level = args[2] || 'junior';
  const repeat = parseInt(args[3]) || 1;
  const res = applyTechPulseModifier(base, level, repeat);
  console.log(JSON.stringify(res, null, 2));
} else if (cmd === 'contract') {
  const taskId = args[1] || 'TASK-01';
  const point = parseInt(args[2]) || 3;
  const conf = args[3] || 'high';
  const summary = args.slice(4).join(' ') || 'Standard task';
  const contract = {
    task_id: taskId,
    suggested_point: point,
    confidence: conf,
    rationale: [summary],
    assumptions: ["Phạm vi theo tài liệu tham chiếu V1.0"],
    uncertainty: [],
    comparable_cases: [],
    split_recommendation: point >= 13 ? ["Cần phân rã task vì điểm >= 13"] : [],
    missing_information: [],
    human_approval_required: true
  };
  console.log(JSON.stringify(contract, null, 2));
}
