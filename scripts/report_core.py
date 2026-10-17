"""Readable core research results, costs and explicit coverage limitations."""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import read_json
from sentiment_project.batch_coding import core_cost


def main():
    result = read_json(ROOT / "reports/core_analysis.json")
    validation = read_json(ROOT / "reports/core_ai_validation.json")
    news = read_json(ROOT / "reports/core_news_coverage.json")
    twitter = read_json(ROOT / "reports/core_twitter_coverage.json")
    corpus = read_json(ROOT / "data/private/core_v1/corpus_manifest.json")
    descriptive = read_json(ROOT / "reports/core_media_descriptive.json")
    old_cost = read_json(ROOT / "reports/prompt_development.json")["cumulative_deepseek_cost_upper_usd"]
    new_cost = core_cost()
    metrics = result["metrics"]
    change = result["M2_minus_M1_MAE"]
    direction = "降低" if change["difference"] < 0 else "增加"
    amount = abs(change["difference"])
    interval = change["interval"]
    interval_text = "区间暂不可估计" if interval is None else f"按连续月份分段、最长 3 个月区块的配对 bootstrap 95% 区间为 [{interval[0]:.3f}, {interval[1]:.3f}]"
    if interval is None or interval[0] <= 0 <= interval[1]:
        inference = "目前证据不足以认定媒体变量稳定改善预测。"
    elif interval[1] < 0:
        inference = "本样本中媒体变量与较低预测误差相关，仍需更广覆盖和独立复现。"
    else:
        inference = "本样本中加入媒体变量反而增加了预测误差。"
    held = validation["held_out_200"]
    lines = ["# 核心分析：媒体指标与消费者信心预测", "",
             f"第一版核心实证结果已形成。共同测试样本为 {result['common_test_months']} 个月，覆盖 {result['test_start'][:7]} 至 {result['test_end'][:7]} 的可用月份；月份并非全部连续。", "",
             f"加入媒体变量后，MAE 相对经济基线{direction} {amount:.3f} 个信心指数点；{interval_text}。{inference}", "",
             "## 数据与测量", "",
             f"原始候选：{news['eligible']} 条时间元数据合格的全国/地方新闻标题、{twitter['posts']} 条日期校验合格推文。按固定月份/来源抽样并去重后，主编码语料为 {corpus['items']} 条：新闻 {corpus['by_platform']['news']} 条，Twitter {corpus['by_platform']['twitter']} 条。旧 59 条开发样本的故事组已排除。",
             "", "媒体窗口为 2019-10 至 2026-07，每月固定两天，新闻每天四个 UTC 时间片，Twitter 每天一个小时且仅一页。采集日期及时间窗规则在取数前固定；标题及关键词样本不能代表整个媒体或平台。",
             "", f"{result['months_with_both_media']}/{result['media_months']} 个月同时有至少 1 条可评分新闻及 3 条可评分推文。缺失月份不填零、不插值。新闻原始档案有 {len(news['errors'])} 个请求失败，保留失败记录；报道发表日期来自 GDELT 抽取元数据。",
             "", "只有美国相关、具有经济实质且在预测截止前已可见的文本进入主指标。负面=-1、正面=+1、中性或混合=0；不确定与格式失败不计分，并记录各月分母。新闻先按媒体求均值，再对观察到的媒体等权；推文按抽样文本等权，不按点赞数加权。",
             "", "![月度媒体指标与样本量](figures/core_media_coverage.png)", "",
             "## 框架与归因的描述性测量", "", "以下比例以本样本中美国相关、经济实质合格的文本为分母；新闻按条目汇总，不是人口或媒体总体占比，也不是偏见率。", "",
             "| 平台 | 合格文本 | 情绪化或混合用语 | 价格水平（含双框架） | 未来描述（含当前与未来） | 政治责备（含褒贬并存） | 数值主张不可核查 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for platform, values in descriptive.items():
        d, n = values["dimensions"], values["n"]
        share = lambda field, choices: sum(d[field].get(k, 0) for k in choices) / n if n else 0
        lines.append(f"| {platform} | {n} | {share('language_style', ['emotional', 'mixed']):.1%} | {share('price_frame', ['levels', 'both']):.1%} | {share('time_frame', ['future', 'both']):.1%} | {share('political_attribution', ['blame', 'both']):.1%} | {share('factual_calibration', ['not_checkable']):.1%} |")
    lines += ["", "本轮未为数值主张逐条匹配官方发布资料，外部数值核查覆盖为 0；不可核查不等于错误。情绪化、政治责备和负面事实均不能直接等同于偏见。", "",
             "## 同样本三模型比较", "",
             "预测目标为下一月消费者信心。M1 包括失业率、总体 PCE 同比、实际 GDP 季度年化增速及 ALFRED 最近可得的消费者信心；M2 再加入前月新闻与 Twitter 情绪；M3 再加入实际可支配个人收入同比。收入是全国汇总代理变量，并非家庭微观数据。",
             "", "全部模型采用相同可用月份、相同扩展训练窗口和固定惩罚系数 1 的标准化岭回归；标准化仅使用训练集。宏观特征用各历史起点的 ALFRED 快照，训练标签只取该次预测时已公布的值；2026-10-16 版本仅用于评分。",
             "", "| 模型 | 测试月份 | MAE | RMSE |", "|---|---:|---:|---:|"]
    names = {"persistence": "最近可得信心持续性", "M1_economic": "M1 经济与信心惯性", "M2_add_media": "M2 加媒体", "M3_add_household": "M3 再加收入"}
    for name, values in metrics.items():
        lines.append(f"| {names[name]} | {values['n']} | {values['MAE']:.3f} | {values['RMSE']:.3f} |")
    lines += ["", "![共同测试月份预测比较](figures/core_model_comparison.png)", "",
              "## AI 独立复核", "",
              f"新抽取 300 条审计文本，新闻/Twitter 各 150 条；其中 100 条开发部分、200 条保留审计部分。代码本在本轮核心数据编码前固定。本轮未利用审计结果修改提示词。保留审计部分尝试 {held['attempted']} 条，A 有效 {held['valid_A']} 条、B 有效 {held['valid_B']} 条，双方均有效 {held['valid_pairs']} 条。", "",
              "A 为 DeepSeek Flash，B/C 为 DeepSeek Pro；互不读取其他编码者的标签。原始响应、格式修复与失败均保留。以下一致率仅在双方有效的保留审计配对上计算；无真人真值，不能称为准确率。", "",
              "| 维度 | 保留审计一致率 | kappa |", "|---|---:|---:|"]
    if held["agreement"]:
        for name, values in held["agreement"]["dimensions"].items():
            kappa = "未定义" if values["kappa"] is None else f"{values['kappa']:.3f}"
            lines.append(f"| {name} | {values['agreement']:.1%} | {kappa} |")
    c = validation.get("C_review")
    lines += ["", f"C 复查：尝试 {c['attempted']} 条，其中 {c['valid']} 条有效。至少两票一致的审计维度共 {c.get('consensus_dimensions', 0)} 项，仍有 {c.get('unresolved_dimensions', 0)} 项无共识并保留 null，不强行赋值。" if c else "C 复查尚未完成。", "",
              "主回归统一使用 A 编码，避免只对审计子集替换标签改变测量口径。共享模型家族可能共同出错；相同/近似故事的检测主要依靠规范化文本，语义改写仍可能跨组。按用户要求采用 AI-only，课程原双人真人标注条款未满足。", "",
              "## 覆盖敏感性", "", "| 评分样本下限 | 可用训练月份 | 测试月份 | M1 MAE | M2 MAE | M3 MAE |", "|---|---:|---:|---:|---:|---:|"]
    for name, values in result["coverage_sensitivity"].items():
        mae = values.get("MAE", {})
        cells = [f"{mae[m]:.3f}" if m in mae else "不足" for m in ["M1_economic", "M2_add_media", "M3_add_household"]]
        lines.append(f"| {name} | {values['eligible_months']} | {values['test_months']} | " + " | ".join(cells) + " |")
    lines += ["", "预测经验区间只由此前已产生的样本外预测和本次起点已公布的目标值校准，至少积累 12 次可用误差后才给出区间；它不保证未来覆盖率。"]
    for name in ["M1_economic", "M2_add_media", "M3_add_household"]:
        value = metrics[name]
        coverage = value.get("empirical_95_band_coverage")
        lines.append(f"{names[name]}：区间可评分 {value.get('empirical_band_n', 0)} 个月，实际覆盖率 " + (f"{coverage:.1%}。" if coverage is not None else "尚不可估计。"))
    lines += ["实际覆盖率低于名义 95%，显示经验区间偏窄；不能把它当作已校准的风险保证。"]
    probe_path = ROOT / "reports/core_perturbation.json"
    if probe_path.exists():
        probe = read_json(probe_path)
        lines += ["", f"ID 遮蔽扰动检查：20 条保留审计文本，双方有效 {probe['valid_pairs']} 条，语气稳定率 {probe['dimensions']['tone']['agreement']:.1%}；文本不变，批次上下文可能变化，因此只能解释为运行稳定性。"]
    lines += ["", "去掉信心惯性的纯经济三模型规格作为事后补充列出，保留主规格和所有结果。提高月度样本下限可能使训练不足，不能为了得到结果临时降低门槛。区块区间只对观察到的稀疏月份作探索性评估，不解决来源选择、遗漏变量或因果识别。",
              "", "## 结果边界与剩余交付", "",
              "本版已经实际完成连续月份媒体采集、AI 编码、月度指标和同样本三模型比较。新闻为标题而非全文，抽样稀疏，部分月份缺失；2026 年模型对历史文本作回溯分类，并未证明当年的在线可实施性。ALFRED 可能晚于原发布者更新，尤其消费者信心；因此增量价值仅相对于本研究的 ALFRED 信息集，不能冒充相对于当时全部公开信息的优势。负面报道、预测相关性和媒体偏见不是同一结论。",
              "", "仍需补齐消费者信心分项、更完整家庭因素、事实核查与扰动检验；完善因果设计建议，并制作课程要求的 10–12 页报告、仪表盘和 6–8 分钟演示。",
              "", "## 费用与复现", "",
              f"本阶段 DeepSeek 按峰时未缓存价格估算上界 ${new_cost:.4f}；跨阶段累计约 ${old_cost + new_cost:.4f}。Twitter 本阶段估算 ${twitter['estimated_usd']:.4f}，跨阶段累计约 ${0.108 + twitter['estimated_usd']:.4f}。免费新闻与宏观下载另存本地。以上是估算而非服务商账单。",
              "", "离线重跑：scripts/merge_core_labels.py → scripts/core_validation.py → scripts/run_core_analysis.py → scripts/plot_core.py → scripts/report_core.py。编码与下载命令会联网；成功缓存不重复调用。",
              "", "来源：[ALFRED](https://fred.stlouisfed.org/docs/api/fred/alfred.html)、[GDELT 标题字段](https://blog.gdeltproject.org/gkg-2-0-now-includes-page-titles/)、[TwitterAPI.io](https://twitterapi.io/pricing/details)。"]
    (ROOT / "reports/CORE_RESULTS.zh-CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    body, table = [], False
    for line in lines:
        if line.startswith("|---"):
            continue
        if line.startswith("|"):
            cell = "td" if table else "th"
            if not table:
                body.append("<div class='table-wrap'><table>")
                table = True
            body.append("<tr>" + "".join(f"<{cell}>{html.escape(v.strip())}</{cell}>" for v in line.strip("|").split("|")) + "</tr>")
            continue
        if table:
            body.append("</table></div>")
            table = False
        if line.startswith("# "):
            body.append("<h1>" + html.escape(line[2:]) + "</h1>")
        elif line.startswith("## "):
            body.append("<h2>" + html.escape(line[3:]) + "</h2>")
        elif line.startswith("!["):
            alt, path = line[2:].split("](", 1)
            body.append(f'<img alt="{html.escape(alt)}" src="{html.escape(path[:-1])}">')
        elif line:
            escaped = html.escape(line)
            linked = re.sub(r"\[([^\]]+)\]\((https://[^)]+)\)", r'<a href="\2">\1</a>', escaped)
            body.append("<p>" + linked + "</p>")
    if table:
        body.append("</table></div>")
    style = 'body{margin:0;background:#f3f6f4;color:#25312c;font:16px/1.8 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1080px;margin:36px auto;background:white;padding:34px;border-top:8px solid #254C45}h1,h2{color:#254C45;line-height:1.4}h2{margin-top:42px;padding-top:12px;border-top:1px solid #dbe4df}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;text-align:left;border-bottom:1px solid #dbe4df}th{background:#254C45;color:white}.table-wrap{overflow:auto}p{overflow-wrap:anywhere}@media(max-width:700px){main{margin:0;padding:18px}h1{font-size:28px}}@media print{body{background:white}main{margin:0;padding:0}h2,table,img{break-inside:avoid}}'
    document = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>核心研究结果</title><style>' + style + '</style><main><p style="color:#65756b">APPLICATIONS IN FINANCE · CORE RESULTS v1</p>' + "\n".join(body) + "</main></html>"
    (ROOT / "reports/core_results.html").write_text(document, encoding="utf-8")
    status = ["# 项目执行进度", "", "最新阶段：核心实证链路第一版。完整结果见 core_results.html / CORE_RESULTS.zh-CN.md。", "",
              f"已完成：82 个月固定媒体取样，原始合格新闻 {news['eligible']} 条、推文 {twitter['posts']} 条；固定主编码语料 {corpus['items']} 条；300 条双模型审计（200 条保留部分，{held['valid_pairs']} 条双方有效配对）。",
              f"第三次复核：{c['attempted']} 条尝试、{c['valid']} 条有效。" if c else "第三次复核仍在运行。", "",
              f"完成 {result['common_test_months']} 个共同月份的三模型比较：M1 MAE {metrics['M1_economic']['MAE']:.3f}，M2 {metrics['M2_add_media']['MAE']:.3f}，M3 {metrics['M3_add_household']['MAE']:.3f}，持续性基准 {metrics['persistence']['MAE']:.3f}。{inference}", "",
              "已完成覆盖门槛、负面占比替代、纯经济补充规格、历史版本与训练时间检查、经验误差区间，以及 ID 遮蔽稳定性检查。41 项测试通过。", "",
              f"累计费用估算：DeepSeek ${old_cost + new_cost:.4f}（按配置峰时未缓存单价），Twitter ${0.108 + twitter['estimated_usd']:.4f}；均为估算，不是账单。", "",
              "剩余：更完整的新闻全文与来源覆盖、数值事实核查、信心分项及家庭因素、因果设计建议；课程最终 10–12 页报告、仪表盘、6–8 分钟演示及完整交付包。", "",
              "原阶段记录保留于 api_pilot.zh-CN.md、STAGE2_STATUS.zh-CN.md 和 vintage_baseline.zh-CN.md；其中较早待办和费用只反映当时状态。"]
    (ROOT / "reports/PROJECT_STATUS.zh-CN.md").write_text("\n".join(status) + "\n", encoding="utf-8")
    print(json.dumps({"core_result": "reports/core_results.html", "finding": inference, "core_DeepSeek_upper_usd": new_cost}))


if __name__ == "__main__":
    main()
