"""Rebuild the API pilot report from saved results without network calls."""
import json
import html
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, read_json, read_jsonl, write_json
from sentiment_project.ai_validation import compare_labels, usage_cost_upper_estimate


def main():
    items = read_jsonl(ROOT / "data/private/validation_pilot_v1.jsonl")
    run_id = digest(items)[:12]
    a = read_jsonl(ROOT / f"labels/runs/{run_id}_A.jsonl")
    b = read_jsonl(ROOT / f"labels/runs/{run_id}_B.jsonl")
    agreement = compare_labels(a, b)
    write_json(ROOT / "reports/pilot_ai_agreement.json", agreement)
    lookup = {row["id"]: row for row in items}
    sources = {}
    for platform in ["twitter", "news"]:
        sources[platform] = {role: dict(Counter(r["label"]["us_relevance"] for r in rows if lookup[r["id"]]["platform"] == platform)) for role, rows in [("A", a), ("B", b)]}
    cfg = read_json(ROOT / "configs/deepseek.json")
    cost, calls, states = 0.0, 0, Counter()
    for path in (ROOT / "labels/runs/cache").glob("*.json"):
        row = read_json(path)
        states[row["state"]] += 1
        if "response" in row:
            calls += 1
            cost += usage_cost_upper_estimate(row["response"], cfg, row["model_requested"], row.get("estimated_reserved_usd", 0))
    twitter_cost = sum(read_json(p).get("estimated_usd", 0) for p in (ROOT / "data/raw/twitter_pilot").rglob("*.json"))
    review = ROOT / "data/private/pilot_review_queue.jsonl"
    review_summary = None
    if review.exists():
        selected = read_jsonl(review)
        c_path = ROOT / f"labels/runs/{digest(selected)[:12]}_C.jsonl"
        if c_path.exists():
            c = read_jsonl(c_path)
            cmap = {r["id"]: r for r in c}
            amap, bmap = {r["id"]: r for r in a}, {r["id"]: r for r in b}
            differences = agreement["disagreements"]
            votes = Counter()
            for item in differences:
                for dim in item["dimensions"]:
                    cv, av, bv = [m[item["id"]]["label"][dim] for m in [cmap, amap, bmap]]
                    if dim == "topics":
                        cv, av, bv = set(cv), set(av), set(bv)
                    votes["supports_A" if cv == av else "supports_B" if cv == bv else "third_value"] += 1
            review_summary = {"items": len(c), "disputed_dimension_review": dict(votes),
                              "scope": "Independent C calls, not a truth oracle; no final gold labels"}
    summary = {"scope": "development pilot only", "items": len(items), "sample_sha256": digest(items),
               "platforms": dict(Counter(i["platform"] for i in items)), "us_relevance": sources,
               "disagreement_items": len(agreement["disagreements"]), "C_review": review_summary,
               "deepseek_response_count_including_repairs": calls, "cache_states": dict(states),
               "deepseek_peak_cache_miss_cost_upper_estimate_usd": cost, "twitter_cost_estimate_usd": twitter_cost,
               "format_adjusted_rows": {role: sum(bool(r.get("format_adjustments")) for r in rows) for role, rows in [("A", a), ("B", b)]}}
    write_json(ROOT / "reports/api_pilot_summary.json", summary)
    lines = ["# API 试采与 AI 复核报告", "", "研究截止日：2026-10-16。阶段：开发试验，尚非最终研究结论。", "",
        f"两套 API 已真实接通。固定样本 {len(items)} 条，其中 48 条推文、11 条新闻标题；A/B 均完成全部配对编码。", "",
        "## 采集与质量", "",
        "- 最初日期字符串检索返回 640 条窗口外推文，全部排除；保留原始响应和失败记录，不改写时间戳。",
        "- 改用 UTC Unix 秒的 since_time / until_time 后，四个日期窗各获得 20 条有效推文，共 80 条；日期校验全部通过。遇到整页日期无效时停止该窗分页。",
        "- 从每个年份随机选 12 条，固定种子 20261016；新闻为 NPR 8 条、WUNC 3 条标题。标题不能代表全文，来源也未平衡。",
        "- 推文来自 2020、2022、2024、2026 四个单日，且每窗仅第一页。不能用于月度代表性、历史媒体趋势或因果效应估计。", "",
        "## AI 一致性（仲裁前）", "", "A 为 DeepSeek Flash，B 为 DeepSeek Pro；二者各自读取原文，不互看标签。同一家族存在相关错误，无真人金标准。", "",
        "| 维度 | 一致率 | Cohen kappa |", "|---|---:|---:|"]
    for dim, value in agreement["dimensions"].items():
        kappa = "未定义" if value["kappa"] is None else f"{value['kappa']:.3f}"
        lines.append(f"| {dim} | {value['agreement']:.1%} | {kappa} |")
    lines += ["", f"共 {len(agreement['disagreements'])}/{len(items)} 条至少一个维度存在分歧。以上是模型间一致性，不能称为准确率。", "",
              "## 美国相关性", "", "| 平台 | 编码 | yes | no | uncertain |", "|---|---|---:|---:|---:|"]
    for platform, roles in sources.items():
        for role, values in roles.items():
            lines.append(f"| {platform} | {role} | {values.get('yes', 0)} | {values.get('no', 0)} | {values.get('uncertain', 0)} |")
    lines += ["", "英文关键词不足以定义美国经济语料；hiring 等词也可能出现在无关讽刺或商业推广中。正式语料应增加经济实质相关性筛选，并单独审计 US relevance。", "", "## 第三次独立复核", ""]
    if review_summary:
        votes = review_summary["disputed_dimension_review"]
        lines += [f"C 已完成 {review_summary['items']} 条：全部分歧项加约 10% 全维度一致项。C 不读取 A/B 标签。分歧维度中支持 A 的 {votes.get('supports_A', 0)} 项、支持 B 的 {votes.get('supports_B', 0)} 项、产生第三种答案的 {votes.get('third_value', 0)} 项。", "", "C 与 B 使用同一模型系列，不能将其视为独立真值。保留三方标签及未解决分歧，尚未自动合并成最终标签。"]
    else:
        lines.append("C 尚未完成；不可宣称已完成全部复核。")
    lines += ["", "## 费用与复现", "",
        f"Twitter 累计估算 ${twitter_cost:.4f}（包括排除的数据）；DeepSeek 全部缓存响应按峰时未缓存单价估算上界 ${cost:.4f}，含格式修复调用。实际账单可能因折扣、缓存计价不同。当前低于本轮 Twitter $0.30、DeepSeek $1 的工作上限。", "",
        "格式处理只统一 HTML 实体和截短展示用解释/已验证引句；类别标签不作人工改写。原始响应完整保留。少数无效 JSON 可进行最多一次有记录的模型格式修复，复用已成功缓存，不重复调用。", "",
        "本报告可离线重建：`python scripts/report_api_pilot.py`。私有原文和模型缓存未加入 Git；固定样本、提示词及原始响应均保留 hash。", "",
        "## 后续研究", "",
        "1. 收紧经济实质和美国相关性规则，在开发集改进后冻结提示词。",
        "2. 补齐全国/地方新闻长期档案与来源平衡，再冻结至少 300 条正式 AI 审计样本。",
        "3. 数值事实核查需匹配发表时已发布的官方资料；本试验未提供这些证据，不能判断事实真伪。",
        "4. 获取历史宏观版本与发布日后，才进入月度媒体特征、正式三模型比较、仪表盘及最终报告。", "",
        "接口语法与计价来源：[Twitter 日期检索](https://twitterapi.io/blog/tweet-search-by-date)、[Twitter 计价](https://twitterapi.io/pricing/details)、[DeepSeek 计价](https://api-docs.deepseek.com/quick_start/pricing/)。"]
    (ROOT / "reports/api_pilot.zh-CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    metric_rows = "".join(f"<tr><td>{html.escape(dim)}</td><td>{v['agreement']:.1%}</td><td>{'—' if v['kappa'] is None else format(v['kappa'], '.3f')}</td></tr>" for dim, v in agreement["dimensions"].items())
    relevance_rows = "".join(f"<tr><td>{platform}</td><td>{role}</td><td>{values.get('yes', 0)}</td><td>{values.get('no', 0)}</td><td>{values.get('uncertain', 0)}</td></tr>" for platform, roles in sources.items() for role, values in roles.items())
    review_text = f"第三次独立调用完成 {review_summary['items']} 条复核。三方结果保留，未合并为最终金标准。" if review_summary else "第三次复核尚未完成。"
    page = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>API 试采与 AI 复核</title><style>
:root{{--green:#254C45;--muted:#5d6966}}*{{box-sizing:border-box}}body{{margin:0;background:#f5f7f6;color:#202825;font:16px/1.7 'Segoe UI','Microsoft YaHei',sans-serif}}main{{max-width:1040px;margin:auto;padding:48px 24px}}header{{border-top:7px solid var(--green);padding-top:22px}}h1,h2{{color:var(--green);line-height:1.3}}h1{{font-size:34px}}h2{{font-size:23px;margin-top:35px}}.meta{{color:var(--muted)}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}}.card{{background:white;border:1px solid #d9e1de;border-top:3px solid var(--green);padding:18px}}strong.big{{display:block;font-size:32px;color:var(--green)}}section{{background:white;border:1px solid #d9e1de;padding:22px;margin-top:20px}}table{{width:100%;border-collapse:collapse}}th{{background:var(--green);color:white;text-align:left}}th,td{{padding:9px 12px;border-bottom:1px solid #dce4e1}}td:not(:first-child){{font-variant-numeric:tabular-nums}}.notice{{border-left:4px solid var(--green);background:#e9f0ed;padding:15px 18px}}a{{color:var(--green)}}@media(max-width:640px){{.cards{{grid-template-columns:1fr}}main{{padding:24px 14px}}h1{{font-size:27px}}section{{padding:14px}}}}@media print{{body{{background:white}}main{{padding:0}}section{{break-inside:avoid}}}}
</style><main><header><div class="meta">CONSUMER SENTIMENT · 2026-10-16 · 开发试验</div><h1>API 已接通，测量规则仍需收紧</h1><p>59 条真实文本完成双模型独立编码。原始数据、提示词及响应均留存，可从本地缓存离线复现。</p></header>
<div class="cards"><div class="card">通过时间校验的推文<strong class="big">80</strong>四个年份，各一个日期窗</div><div class="card">固定开发样本<strong class="big">59</strong>48 条推文 + 11 条新闻标题</div><div class="card">估算 API 成本<strong class="big">${twitter_cost + cost:.3f}</strong>Twitter ${twitter_cost:.3f} · DeepSeek ≤约 ${cost:.3f}</div></div>
<div class="notice">这是接口与测量可行性试验。样本不代表月度媒体分布；AI 一致率不等于真实准确率；当前不能估计媒体的因果效应。</div>
<section><h2>一致性结果</h2><p>Flash 主编码与 Pro 独立复核。{len(agreement['disagreements'])}/59 条至少一个维度存在分歧。两者属于同一模型家族，错误可能相关。</p><table><thead><tr><th>维度</th><th>一致率</th><th>Cohen kappa</th></tr></thead><tbody>{metric_rows}</tbody></table><p>{review_text}</p></section>
<section><h2>英文关键词不等于美国经济内容</h2><table><thead><tr><th>平台</th><th>编码</th><th>美国相关</th><th>不相关</th><th>不确定</th></tr></thead><tbody>{relevance_rows}</tbody></table><p>新闻只含 NPR 与 WUNC 的经济标题，未取得平衡的长期全文语料。推文需进一步排除无关讽刺、推广与非美国内容。</p></section>
<section><h2>数据质量与下一步</h2><p>初次日期字符串查询返回的 640 条窗口外记录已全部排除。改用 UTC Unix 秒查询后，80 条结果全部通过日期检查；失败调用成本也计入上方费用。</p><ol><li>修订经济实质、时间框架及数值主张规则，再冻结提示词。</li><li>补齐新闻来源与历史覆盖，构建至少 300 条正式审计样本。</li><li>匹配官方历史版本与发布日期，再进行月度特征和三模型比较。</li></ol><p>格式处理保留原始响应；模型修复请求单独记账。不把缺少官方证据的数值主张自动判真或判假。</p></section>
<footer class="meta"><p>费用为按配置单价计算的估算，DeepSeek 使用峰时未缓存单价；实际账单可能更低。<a href="api_pilot.zh-CN.md">完整方法记录</a> · <a href="api_pilot_summary.json">机器可读汇总</a></p></footer></main></html>"""
    (ROOT / "reports/api_pilot.html").write_text(page, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
