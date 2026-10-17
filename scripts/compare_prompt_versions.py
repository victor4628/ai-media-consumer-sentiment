"""Development comparison only: do not interpret reuse as held-out validation."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, read_json, read_jsonl, write_json
from sentiment_project.ai_validation import compare_labels, usage_cost_upper_estimate


def main():
    items = read_jsonl(ROOT / "data/private/validation_pilot_v1.jsonl")
    prompt = (ROOT / "prompts/economic_coding_v2.txt").read_text(encoding="utf-8")
    old_id, new_id = digest(items)[:12], digest({"items": items, "prompt": prompt})[:12]
    old = compare_labels(*[read_jsonl(ROOT / f"labels/runs/{old_id}_{role}.jsonl") for role in ["A", "B"]])
    new = compare_labels(*[read_jsonl(ROOT / f"labels/runs/{new_id}_{role}.jsonl") for role in ["A", "B"]])
    write_json(ROOT / "reports/pilot_v2_agreement.json", new)
    cfg = read_json(ROOT / "configs/deepseek.json")
    cost = 0
    for path in (ROOT / "labels/runs/cache").glob("*.json"):
        record = read_json(path)
        if "response" in record:
            cost += usage_cost_upper_estimate(record["response"], cfg, record["model_requested"], record.get("estimated_reserved_usd", 0))
    rows = [{"dimension": name, "v1_agreement": old["dimensions"][name]["agreement"], "v2_agreement": value["agreement"], "v2_kappa": value["kappa"]} for name, value in new["dimensions"].items()]
    report = {"scope": "Same development set reused to revise definitions; NOT held-out accuracy or proof of improvement", "items": len(items), "v2_run_id": new_id, "dimensions": rows, "v1_disagreement_items": len(old["disagreements"]), "v2_disagreement_items": len(new["disagreements"]), "cumulative_deepseek_cost_upper_usd": cost}
    write_json(ROOT / "reports/prompt_development.json", report)
    lines = ["# AI 代码本开发复测", "", "原 59 条开发文本复用；没有动用正式冻结审计集。结果是模型间一致性，不是真实准确率。v2 明确经济实质、时间框架、数值主张、价格框架及美国相关性，仍为开发候选版。", "", "| 维度 | v1 一致率 | v2 一致率 | v2 kappa |", "|---|---:|---:|---:|"]
    for row in rows:
        k = "未定义" if row["v2_kappa"] is None else f"{row['v2_kappa']:.3f}"
        lines.append(f"| {row['dimension']} | {row['v1_agreement']:.1%} | {row['v2_agreement']:.1%} | {k} |")
    lines += ["", f"至少一个维度分歧：v1 {len(old['disagreements'])}/59；v2 {len(new['disagreements'])}/59。", "", f"所有阶段 DeepSeek 缓存响应累计按峰时未缓存价格估算上界 ${cost:.4f}。", "", "定义修订会改变测量对象，不能只追求一致率升高。正式审计仍需新抽取、故事组隔离的样本；此次结果不得计入正式审计的准确性证据。v1/v2 提示词、标签与缓存分别保留。"]
    (ROOT / "reports/prompt_development.zh-CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
