#!/usr/bin/env node

/**
 * EST-POINT CLI Calculator & Casebook Lookup (TechPulse 2026 Standard)
 * Baseline: 1.0 Point = 1 Standard Working Day
 * Slide Deck: https://docs.google.com/presentation/d/15YZOTSmp-PWgte3DsmVwN01hmZzXV0w32INu84Lt0ug/edit?slide=id.p2#slide=id.p2
 * Usage:
 *   node estimate.js search <keyword>
 *   node estimate.js list [role]
 *   node estimate.js calc <juniorBasePoint> [senior|junior] [repeatCount: 1|2|3]
 *   node estimate.js contract <taskId> <point> <confidence> <summary>
 */

const TECHPULSE_STANDARD_SCALE = [0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0];

const REFERENCE_CASES = {
  benchmark: [
    { id: "TP-01", name: "Fix Bug thường / Refactoring nhỏ / UI-CSS tweak", juniorPoint: 0.5, seniorPoint: 0.25, repeatPoint: 0.2, condition: "Độ phức tạp Thấp (Slide 6)" },
    { id: "TP-02", name: "CRUD API cơ bản / Form đơn giản / 1 Section UI", juniorPoint: 1.0, seniorPoint: 0.5, repeatPoint: 0.35, condition: "Độ phức tạp Thấp - 1 Ngày Standard (Slide 2 & 6)" },
    { id: "TP-03", name: "Tích hợp Cổng thanh toán / Third-party / Multi-flow Feature", juniorPoint: 2.0, seniorPoint: 1.0, repeatPoint: 0.7, condition: "Độ phức tạp Trung bình (Slide 6)" },
    { id: "TP-04", name: "Tối ưu Kiến trúc / Core Service System / Worker Engine", juniorPoint: null, seniorPoint: 2.0, repeatPoint: 1.5, condition: "Độ phức tạp Rất cao - Chỉ phân công Senior (Slide 6)" }
  ],
  frontend: [
    { id: "FE-01", name: "Thay đổi text, label, link, màu, spacing, ẩn scrollbar", juniorPoint: 0.5, seniorPoint: 0.25, repeatPoint: 0.2, condition: "UI tweak nhỏ, không đổi logic" },
    { id: "FE-02", name: "Thêm Button / Input / Pill Tab / Header đồng bộ Figma", juniorPoint: 0.5, seniorPoint: 0.25, repeatPoint: 0.2, condition: "Tái sử dụng Design System" },
    { id: "FE-03", name: "Xây dựng Modal / Popup / Bottom Sheet đơn giản", juniorPoint: 1.0, seniorPoint: 0.5, repeatPoint: 0.3, condition: "Có thiết kế và component nền" },
    { id: "FE-04", name: "Dark Mode cho 1 Section / Component (Home / Profile)", juniorPoint: 1.0, seniorPoint: 0.5, repeatPoint: 0.3, condition: "Lần 1: 0.5pt (Senior); các section lặp lại: 0.3pt" },
    { id: "FE-05", name: "Form nhập liệu hoàn chỉnh / CRUD UI (Create/Edit Alert, Watchlist)", juniorPoint: 1.0, seniorPoint: 0.5, repeatPoint: 0.4, condition: "Validation, submit, loading, error state" },
    { id: "FE-06", name: "Trang Listing / Trang Detail / Bảng dữ liệu kết nối API", juniorPoint: 1.0, seniorPoint: 0.5, repeatPoint: 0.4, condition: "Có API, phân trang, empty/loading state" },
    { id: "FE-07", name: "Chuẩn hóa luồng phức tạp / Multi-Filter / Trang mới hoàn chỉnh + API", juniorPoint: 2.0, seniorPoint: 1.0, repeatPoint: 0.7, condition: "Nhiều trạng thái, filter/sort/routing hoặc tích hợp API" },
    { id: "FE-08", name: "Kiến trúc Realtime UI / WebSocket / Core State Engine", juniorPoint: null, seniorPoint: 2.0, repeatPoint: 1.5, condition: "WebSocket, reconnect, đồng bộ đa luồng" }
  ],
  backend: [
    { id: "BE-01", name: "Thêm field DB / sửa query / fix API mapping hoặc sort/filter nhỏ", juniorPoint: 0.5, seniorPoint: 0.25, repeatPoint: 0.2, condition: "Migration đơn giản, 1 endpoint" },
    { id: "BE-02", name: "API CRUD cơ bản / Event Listener (@mention notification, Watchlist CRUD)", juniorPoint: 1.0, seniorPoint: 0.5, repeatPoint: 0.4, condition: "Validation, unit test, xử lý lỗi đầy đủ" },
    { id: "BE-03", name: "Tích hợp Third-Party / Multi-channel Notification / Aggregation API", juniorPoint: 2.0, seniorPoint: 1.0, repeatPoint: 0.7, condition: "Kết nối đa dịch vụ (In-App/Email/Telegram) hoặc nhiều bảng" },
    { id: "BE-04", name: "Core Service System / Worker Engine / Tối ưu Kiến trúc & Dockerfile", juniorPoint: null, seniorPoint: 2.0, repeatPoint: 1.5, condition: "Kiến trúc lõi, worker matching, hiệu năng cao" }
  ],
  bug: [
    { id: "BUG-01", name: "Fix Bug UI / CSS / Layout / Link / Auto-close modal / Scrollbar", juniorPoint: 0.5, seniorPoint: 0.25, repeatPoint: 0.2, condition: "Phạm vi 1-2 component FE" },
    { id: "BUG-02", name: "Fix Bug logic vừa / API mapping / Zustand cache / Fallback Mozyfin", juniorPoint: 0.7, seniorPoint: 0.3, repeatPoint: 0.25, condition: "Xử lý state hoặc chuẩn hóa dữ liệu FE-API" },
    { id: "BUG-03", name: "Fix Bug Fullstack (FE + BE) / Đồng bộ nhiều module", juniorPoint: 1.0, seniorPoint: 0.5, repeatPoint: 0.4, condition: "Chạm cả FE lẫn BE hoặc đồng bộ đa luồng" },
    { id: "BUG-04", name: "Fix Bug Race Condition / Mất dữ liệu / Kiến trúc Core", juniorPoint: null, seniorPoint: 1.5, repeatPoint: 1.0, condition: "Điều tra sâu và bảo toàn dữ liệu" }
  ]
};

function snapToTechPulseScale(val) {
  let closest = TECHPULSE_STANDARD_SCALE[0];
  let minDiff = Math.abs(val - closest);
  for (const s of TECHPULSE_STANDARD_SCALE) {
    const diff = Math.abs(val - s);
    if (diff < minDiff) {
      minDiff = diff;
      closest = s;
    }
  }
  return closest;
}

function searchCases(query) {
  const q = query.toLowerCase();
  const results = [];
  for (const [role, cases] of Object.entries(REFERENCE_CASES)) {
    for (const c of cases) {
      if (
        c.name.toLowerCase().includes(q) ||
        c.condition.toLowerCase().includes(q) ||
        c.id.toLowerCase().includes(q)
      ) {
        results.push({ role, ...c });
      }
    }
  }
  return results;
}

function applyTechPulseModifier(juniorBasePoint, level = 'senior', repeatCount = 1) {
  let levelFactor = level.toLowerCase() === 'senior' ? 0.5 : 1.0;
  let learningFactor = 1.0;
  if (repeatCount === 2) {
    learningFactor = 0.7;
  } else if (repeatCount >= 3) {
    learningFactor = 0.4;
  }
  const rawPoint = juniorBasePoint * levelFactor * learningFactor;
  const standardPoint = snapToTechPulseScale(rawPoint);
  return {
    juniorBasePoint,
    level,
    levelFactor,
    repeatCount,
    learningFactor,
    rawPoint: Math.round(rawPoint * 100) / 100,
    standardPoint
  };
}

const args = process.argv.slice(2);
const cmd = args[0];

if (!cmd || cmd === 'help') {
  console.log(`
Usage (TechPulse 2026 Standard: 1.0 Point = 1 Standard Working Day):
  node estimate.js search <keyword>                                  Search casebook
  node estimate.js list [benchmark|frontend|backend|bug]             List cases
  node estimate.js calc <juniorBasePoint> [senior|junior] [1|2|3]    Calculate with TechPulse modifiers
  node estimate.js contract <taskId> <point> <confidence> <summary>  Print JSON contract
  `);
  process.exit(0);
}

if (cmd === 'search') {
  const query = args.slice(1).join(' ');
  const res = searchCases(query);
  console.log(`Found ${res.length} matches for "${query}":`);
  res.forEach(r => {
    console.log(
      `- [${r.role.toUpperCase()}] ${r.id}: ${r.name} | Junior: ${r.juniorPoint ?? 'N/A'}pt | Senior: ${r.seniorPoint}pt | Repeat(2+): ${r.repeatPoint}pt -> ${r.condition}`
    );
  });
} else if (cmd === 'list') {
  const role = (args[1] || '').toLowerCase();
  if (role && REFERENCE_CASES[role]) {
    console.log(`=== ${role.toUpperCase()} CASES ===`);
    REFERENCE_CASES[role].forEach(c =>
      console.log(
        `${c.id}: ${c.name} | Junior: ${c.juniorPoint ?? 'N/A'}pt | Senior: ${c.seniorPoint}pt | Repeat: ${c.repeatPoint}pt - ${c.condition}`
      )
    );
  } else {
    for (const r of Object.keys(REFERENCE_CASES)) {
      console.log(`\n=== ${r.toUpperCase()} (${REFERENCE_CASES[r].length} cases) ===`);
      REFERENCE_CASES[r].forEach(c =>
        console.log(
          `  ${c.id}: ${c.name} | Junior: ${c.juniorPoint ?? 'N/A'}pt | Senior: ${c.seniorPoint}pt | Repeat: ${c.repeatPoint}pt - ${c.condition}`
        )
      );
    }
  }
} else if (cmd === 'calc') {
  const base = parseFloat(args[1]) || 1.0;
  const level = args[2] || 'senior';
  const repeat = parseInt(args[3], 10) || 1;
  const res = applyTechPulseModifier(base, level, repeat);
  console.log(JSON.stringify(res, null, 2));
} else if (cmd === 'contract') {
  const taskId = args[1] || 'TASK-01';
  const point = parseFloat(args[2]) || 0.5;
  const conf = args[3] || 'high';
  const summary = args.slice(4).join(' ') || 'Standard task';
  const contract = {
    task_id: taskId,
    suggested_point: point,
    confidence: conf,
    rationale: [summary],
    assumptions: ["1.0 Point = 1 Ngày Công Việc Standard (TechPulse 2026)"],
    uncertainty: [],
    comparable_cases: [],
    split_recommendation: point > 3.0 ? ["Cần phân rã task vì điểm > 3.0 Points (Senior)"] : [],
    missing_information: [],
    human_approval_required: true
  };
  console.log(JSON.stringify(contract, null, 2));
}
