#!/usr/bin/env python3
"""Zero-dependency Offline Agent Harness Eval Gate (+0 tokens/turn)."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import tempfile
from itertools import combinations
from pathlib import Path
from typing import Any

MAX_CONTEXT_TAX_TOKENS = 4000
MIN_TOP3_RECALL = 0.95
COLLISION_JACCARD_THRESHOLD = 0.35

DOCTOR_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their", "this",
    "to", "use", "used", "using", "when", "with", "you", "your", "need", "wants",
    "want", "asks", "any", "all", "also", "can", "should", "will", "skill", "skills",
    "user", "code", "agent", "agents", "file", "files",
})
QUERY_STOPWORDS = DOCTOR_STOPWORDS | frozenset({
    "whenever", "trigger", "triggers", "triggered", "của", "và", "cho", "là", "các",
    "với", "để", "khi", "này", "cái", "một", "trong", "từ", "trên", "vào", "ra",
    "lại", "bằng", "giúp", "hãy", "cần", "làm", "chạy", "viết", "xem", "theo", "bên", "qua", "bị", "về",
})
VI_EN_SYNONYMS = {
    "tối ưu": "optimize optimization performance", "hiệu năng": "performance",
    "bảo mật": "security hardening audit", "kiểm toán": "audit review",
    "song ngữ": "bilingual", "nhật ký": "journal daily", "truy vấn": "query",
    "cơ sở dữ liệu": "database", "đa luồng": "concurrency parallel",
    "song song": "parallel subagents", "tách biệt": "isolated", "tạo task": "create task",
    "tạo sub issue": "sub-issues", "ước lượng": "estimate", "giao diện": "interface ui",
    "trợ năng": "accessibility a11y", "sơ đồ": "diagram visualize", "biểu đồ": "chart diagram",
    "thu thập": "discover harvest scan", "chưng cất": "distill lessons",
    "bài viết": "article blog author", "viết bài": "author blog article",
    "đánh giá": "eval evaluation review", "phân tán": "distributed",
    "kiểm thử": "testing test e2e", "triển khai": "deploy rollout implement",
    "chống": "prevention", "tách nhỏ": "decompose simplify", "đơn giản hóa": "simplify",
    "bộ nhớ": "memory", "hạ tầng": "infrastructure infra", "tinh chỉnh": "tuning",
    "chỉ số": "metrics", "xuất": "generation", "chuẩn": "parseable",
    "tính năng": "features", "kiểm tra": "check audit", "chứng minh": "proofs", "lỗ hổng": "vulnerabilities",
}
SLASH_RE = re.compile(r"(?<![a-z0-9_/-])/[a-z0-9][a-z0-9-]+")
QUOTED_RE = re.compile(r"['\"]([^'\"]{2,60})['\"]")
WORD_RE = re.compile(r"[a-z0-9\u00c0-\u024f\u1e00-\u1eff][a-z0-9\u00c0-\u024f\u1e00-\u1eff_.-]*")


def parse_frontmatter(raw: str) -> dict[str, str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("missing closing frontmatter delimiter") from exc
    fm: dict[str, str] = {}
    current_key: str | None = None
    for line in lines[1:end]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")) and ":" in line:
            key, val = line.split(":", 1)
            current_key = key.strip()
            fm[current_key] = val.strip().strip("'\"")
        elif current_key and line.startswith((" ", "\t")):
            fm[current_key] = f"{fm[current_key]} {line.strip()}".strip()
    return fm


def ordered_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for raw_tok in WORD_RE.findall(text.lower()):
        tok = raw_tok.strip("._-")
        if len(tok) < 2 or tok in QUERY_STOPWORDS:
            continue
        tokens.append(tok)
        if any(sep in tok for sep in ("-", "_", ".")):
            tokens.extend(p for p in re.split(r"[-_.]+", tok) if len(p) >= 2 and p not in QUERY_STOPWORDS)
        if tok.endswith("s") and not tok.endswith(("ss", "is", "us")) and len(tok) > 4:
            tokens.append(tok[:-1])
    return tokens


def load_skills(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    skills_dir = root / "skills"
    errors, skills = [], []
    if not skills_dir.is_dir():
        return skills, [f"missing skills directory: {skills_dir}"]
    for item in sorted(skills_dir.iterdir()):
        if not item.is_dir() or item.name == "drafts" or item.name.startswith("."):
            continue
        skill_md = item / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{item.name}: missing SKILL.md")
            continue
        try:
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"{item.name}: {exc}")
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        if not name or name != item.name:
            errors.append(f"{item.name}: invalid or mismatched frontmatter name {name!r}")
        if not desc:
            errors.append(f"{item.name}: missing frontmatter description")
        elif len(desc) > 1024:
            errors.append(f"{item.name}: description exceeds 1024 chars ({len(desc)})")
        desc_seq, name_seq = ordered_tokens(desc), ordered_tokens(name)
        skills.append({
            "name": name or item.name,
            "description": desc,
            "context_tokens": max(1, round(len(f"{name}: {desc}") / 4)),
            "desc_slashes": set(SLASH_RE.findall(desc.lower())),
            "quoted_triggers": [q.strip(" .,:;!?").lower() for q in QUOTED_RE.findall(desc) if len(q.strip()) >= 3],
            "desc_tokens": set(desc_seq),
            "name_tokens": set(name_seq),
            "desc_bigrams": {f"{a} {b}" for a, b in zip(desc_seq, desc_seq[1:])},
            "doc_tokens": set(desc_seq) | set(name_seq),
            "doctor_words": {w for w in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", desc.lower()) if w not in DOCTOR_STOPWORDS},
        })
    return skills, errors


def find_collisions(skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collisions: list[dict[str, Any]] = []
    for a, b in combinations(skills, 2):
        wa, wb = a["doctor_words"], b["doctor_words"]
        if not wa or not wb:
            continue
        inter = wa & wb
        jaccard = len(inter) / len(wa | wb)
        if jaccard >= COLLISION_JACCARD_THRESHOLD and len(inter) >= 4:
            collisions.append({"skill_a": a["name"], "skill_b": b["name"], "similarity": round(jaccard, 2), "shared_keywords": sorted(inter)[:8]})
    collisions.sort(key=lambda c: c["similarity"], reverse=True)
    return collisions


def compute_idf(skills: list[dict[str, Any]]) -> dict[str, float]:
    n = max(1, len(skills))
    df: dict[str, int] = {}
    for s in skills:
        for tok in s["doc_tokens"]:
            df[tok] = df.get(tok, 0) + 1
    return {tok: math.log(1.0 + (n - cnt + 0.5) / (cnt + 0.5)) for tok, cnt in df.items()}


def rank_skills(prompt: str, skills: list[dict[str, Any]], idf: dict[str, float]) -> list[tuple[float, str]]:
    p_low = prompt.lower()
    p_slashes = set(SLASH_RE.findall(p_low))
    extra_en = [en for vi, en in VI_EN_SYNONYMS.items() if vi in p_low]
    p_seq = ordered_tokens(f"{p_low} {' '.join(extra_en)}" if extra_en else p_low)
    p_tokens = set(p_seq)
    p_bigrams = {f"{a} {b}" for a, b in zip(p_seq, p_seq[1:])}
    scored: list[tuple[float, str]] = []
    for s in skills:
        slash_hit = bool(p_slashes & s["desc_slashes"])
        quote_boost = min(12.0, sum(
            6.5 for phrase in s["quoted_triggers"]
            if re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", p_low)
        ))
        overlap_desc = p_tokens & s["desc_tokens"]
        if not slash_hit and quote_boost == 0.0 and not overlap_desc:
            scored.append((0.0, s["name"]))
            continue
        score = (10.0 if slash_hit else 0.0) + quote_boost
        if re.search(rf"(?<![a-z0-9-]){re.escape(s['name'])}(?![a-z0-9-])", p_low):
            score += 3.0
        score += sum(idf.get(t, 1.0) for t in overlap_desc) / (1.0 + 0.035 * len(s["desc_tokens"]))
        score += 0.35 * sum(idf.get(t, 1.0) for t in (p_tokens & s["name_tokens"]) - overlap_desc)
        score += 1.6 * len(p_bigrams & s["desc_bigrams"])
        scored.append((round(score, 4), s["name"]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored


def eval_rule_case(root: Path, case: dict[str, Any]) -> tuple[bool, str | None]:
    for rel in case.get("files", []):
        fpath = root / rel
        if not fpath.is_file():
            return False, f"missing target file {rel}"
        text = fpath.read_text(encoding="utf-8")
        for pat in case.get("must_match", []):
            if not re.search(pat, text, re.IGNORECASE):
                return False, f"{rel} failed must_match: {pat!r}"
        for pat in case.get("must_not_match", []):
            if re.search(pat, text, re.IGNORECASE):
                return False, f"{rel} matched forbidden pattern: {pat!r}"
    return True, None


def evaluate(root: Path, max_ctx_tokens: int = MAX_CONTEXT_TAX_TOKENS) -> dict[str, Any]:
    cases_file = root / "evals" / "harness_cases.jsonl"
    if not cases_file.is_file():
        return {"decision": "BLOCK_RELEASE", "reasons": [f"missing {cases_file}"]}
    skills, fm_errors = load_skills(root)
    collisions, ctx_tokens, idf = find_collisions(skills), sum(s["context_tokens"] for s in skills), compute_idf(skills)
    cases = [json.loads(line) for line in cases_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    trig_total = trig_top1 = trig_top3 = crit_trig_fail = rule_total = rule_pass = 0
    failures: list[dict[str, Any]] = []
    for case in cases:
        ctype = case.get("type")
        if ctype == "skill_trigger":
            trig_total += 1
            top3 = [name for score, name in rank_skills(case["prompt"], skills, idf)[:3] if score > 0]
            expected = case["expected_skill"]
            trig_top1 += int(bool(top3) and top3[0] == expected)
            if expected in top3:
                trig_top3 += 1
            else:
                crit_trig_fail += int(bool(case.get("critical")))
                failures.append({"id": case["id"], "type": ctype, "expected": expected, "top3": top3})
        elif ctype == "rule_contract":
            rule_total += 1
            ok, reason = eval_rule_case(root, case)
            if ok:
                rule_pass += 1
            else:
                failures.append({"id": case["id"], "type": ctype, "reason": reason})

    top3_recall = (trig_top3 / trig_total) if trig_total else 0.0
    reasons: list[str] = []
    if fm_errors:
        reasons.append(f"frontmatter_errors={len(fm_errors)}")
    if ctx_tokens > max_ctx_tokens:
        reasons.append(f"context_tax={ctx_tokens} > {max_ctx_tokens}")
    if collisions:
        reasons.append(f"trigger_collisions={len(collisions)}")
    if trig_total == 0 or top3_recall < MIN_TOP3_RECALL:
        reasons.append(f"top3_recall={top3_recall:.1%} < {MIN_TOP3_RECALL:.0%}")
    if crit_trig_fail > 0:
        reasons.append(f"critical_trigger_failures={crit_trig_fail}")
    if rule_total == 0 or rule_pass < rule_total:
        reasons.append(f"rule_contract_failures={rule_total - rule_pass}")

    return {
        "decision": "ALLOW_RELEASE" if not reasons else "BLOCK_RELEASE",
        "reasons": reasons,
        "skills_count": len(skills),
        "context_tax_tokens": ctx_tokens,
        "trigger_collisions": collisions,
        "frontmatter_errors": fm_errors,
        "skill_trigger": {"total": trig_total, "top1": trig_top1, "top3": trig_top3, "top3_recall": round(top3_recall, 4), "critical_failures": crit_trig_fail},
        "rule_contract": {"total": rule_total, "passed": rule_pass, "pass_rate": round((rule_pass / rule_total) if rule_total else 0.0, 4)},
        "failures": failures,
    }


def _copy_harness_slice(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / "AGENTS.md", dst / "AGENTS.md")
    for sub in ("rules", "skills", "evals"):
        shutil.copytree(src / sub, dst / sub, symlinks=True)


def run_self_test(root: Path, max_ctx_tokens: int = MAX_CONTEXT_TAX_TOKENS) -> dict[str, Any]:
    live = evaluate(root, max_ctx_tokens)
    mutations: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for label in ("rule_git_push_deleted", "skill_collision_injected", "critical_pattern_trigger_broken"):
            mroot = Path(tmp) / label
            _copy_harness_slice(root, mroot)
            if label == "rule_git_push_deleted":
                core = mroot / "rules" / "core.md"
                core.write_text("\n".join(l for l in core.read_text(encoding="utf-8").splitlines() if "git push" not in l), encoding="utf-8")
            elif label == "skill_collision_injected":
                probe = mroot / "skills" / "collision-probe"
                probe.mkdir(parents=True, exist_ok=True)
                (probe / "SKILL.md").write_text(
                    '---\nname: collision-probe\ndescription: "Use when auditing AI agent skills, diagnosing context token bloat, checking 30-day skill usage telemetry, finding trigger collisions or broken references, or running an environment health check."\n---\n',
                    encoding="utf-8",
                )
            elif label == "critical_pattern_trigger_broken":
                p2p = mroot / "skills" / "pattern-to-prod" / "SKILL.md"
                p2p.write_text('---\nname: pattern-to-prod\ndescription: "Handles unrelated archival text notes."\n---\n', encoding="utf-8")
            res = evaluate(mroot, max_ctx_tokens)
            mutations.append({"mutation": label, "decision": res["decision"], "reasons": res["reasons"]})

    ok = live["decision"] == "ALLOW_RELEASE" and all(m["decision"] == "BLOCK_RELEASE" for m in mutations)
    return {"self_test_passed": ok, "live": live, "mutations": mutations}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline Agent Harness Eval Gate.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="Harness kit root")
    parser.add_argument("--max-context-tokens", type=int, default=MAX_CONTEXT_TAX_TOKENS)
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--self-test", action="store_true", help="Run live check plus 3 seeded regression tests")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.self_test:
        report = run_self_test(root, args.max_context_tokens)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            live = report["live"]
            print(f"live={live['decision']} skills={live['skills_count']} ctx={live['context_tax_tokens']} tok "
                  f"top1={live['skill_trigger']['top1']}/{live['skill_trigger']['total']} "
                  f"top3={live['skill_trigger']['top3']}/{live['skill_trigger']['total']} "
                  f"rules={live['rule_contract']['passed']}/{live['rule_contract']['total']}")
            for m in report["mutations"]:
                print(f"mutation[{m['mutation']}]={m['decision']} ({', '.join(m['reasons'])})")
        return 0 if report["self_test_passed"] else 1

    res = evaluate(root, args.max_context_tokens)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"{res['decision']} skills={res['skills_count']} ctx={res['context_tax_tokens']} tok "
              f"collisions={len(res['trigger_collisions'])} "
              f"top1={res['skill_trigger']['top1']}/{res['skill_trigger']['total']} "
              f"top3={res['skill_trigger']['top3']}/{res['skill_trigger']['total']} ({res['skill_trigger']['top3_recall']:.1%}) "
              f"rules={res['rule_contract']['passed']}/{res['rule_contract']['total']}")
        for f in res["failures"]:
            print(f"  FAIL {f}")
        for r in res["reasons"]:
            print(f"  BLOCK_REASON: {r}")
    return 0 if res["decision"] == "ALLOW_RELEASE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
