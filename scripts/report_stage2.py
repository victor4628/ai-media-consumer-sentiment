"""Summarize historical data and prompt development, without network calls."""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import read_json


def main():
    macro = read_json(ROOT / "reports/vintage_baseline.json")
    news = read_json(ROOT / "reports/news_archive_probe.json")
    coding = read_json(ROOT / "reports/prompt_development.json")
    lines = ["# 第二阶段：历史版本与测量开发", "", "日期：2026-10-16。项目仍在研究数据准备阶段，未完成最终三模型、报告或演示交付。", "",
             "## 宏观历史版本已落地", "",
             f"取得 201 个时点 × 5 个序列，共 1,005 份所需 ALFRED 快照（其中 200 个预测起点，另 1 个评分版本）。构建 {macro['feature_months']} 个月的时点面板，并完成 {macro['evaluation_months']} 个月的共同样本外比较。",
             "", "增长率序列在早期时点有 57 次无档案响应，因此统一改用 GDPC1 同一历史快照的相邻季度水平计算年化增速，未用最新值填补。总体 PCE 同比、实际可支配收入同比也在各自同一快照内计算。", "",
             "训练特征来自各历史预测起点；训练标签只取该次预测时点已公布的信心值。评分使用 2026-10-16 快照，不能倒灌进历史训练。快照证明截止时点可得，不提供精确首次发布日期。", "",
             "| 模型 | MAE | RMSE |", "|---|---:|---:|"]
    for name, values in macro["metrics"].items():
        lines.append(f"| {name} | {values['MAE']:.3f} | {values['RMSE']:.3f} |")
    lines += ["", "这些都是不含媒体的基线；不应将残差直接解释为媒体偏见，也不应把四行基线当作课程要求的最终 M1/M2/M3。", "",
              "## 新闻档案可用，但尚未形成月度语料", "",
              f"免费读取 {news['files']} 个 GDELT 时间片，在指定全国/地方媒体中找到 {news['candidates']} 条关键词标题候选，其中 {news['timestamp_eligible']} 条通过元数据时间检查。缺少发布时间的文本不以抓取时间代替。",
              "", "主要约束是稀疏时间片产量低、标题并非全文、来源和月份覆盖不足。PAGE_TITLE 自 2019-09 才加入 GDELT，因此这条路线的完整月度研究窗最早只能从 2019-10 开始；更早历史不能假装有标题。进一步扩量前需验证更广的来源清单或出版方历史档案。", "",
              "## AI 规则第二版开发复测", "",
              "保留 v1 及全部旧结果；v2 明确非经济文本、当前/未来、数值主张、价格水平/变化和美国相关性定义。两版都使用原 59 条开发文本，因此不是独立测试集评估。", "",
              "| 维度 | v1 一致率 | v2 一致率 |", "|---|---:|---:|"]
    for row in coding["dimensions"]:
        lines.append(f"| {row['dimension']} | {row['v1_agreement']:.1%} | {row['v2_agreement']:.1%} |")
    lines += ["", f"有至少一个维度分歧的文本从 {coding['v1_disagreement_items']}/59 变为 {coding['v2_disagreement_items']}/59。不能据此声称真实准确率提高。仍须独立正式审计、事实证据核查和扰动测试。", "",
              "## 费用与剩余工作", "",
              f"本阶段 ALFRED 和 GDELT 下载免费，未新增 Twitter 调用。跨阶段 DeepSeek 累计按峰时未缓存价格估算上界 ${coding['cumulative_deepseek_cost_upper_usd']:.4f}；Twitter 仍累计估算 $0.108。实际账单可能因折扣不同。", "",
              "1. 解决连续月份的新闻样本覆盖、正文可得性及来源平衡，再确定共同研究窗。",
              "2. 冻结代码本并抽取至少 300 条故事组隔离的正式 AI 审计样本。",
              "3. 构建月度媒体特征并补齐信心分项，执行经济/加媒体/加家庭因素比较与稳健性检验。",
              "4. 制作仪表盘、10–12 页报告、6–8 分钟演示及复现包。", "",
              "## 来源与复现", "",
              "ALFRED：https://fred.stlouisfed.org/docs/api/fred/alfred.html",
              "GDELT 标题字段：https://blog.gdeltproject.org/gkg-2-0-now-includes-page-titles/",
              "GDELT 发布时间元数据：https://blog.gdeltproject.org/new-gkg-2-0-article-metadata-fields/", "",
              "本地复现：scripts/build_vintage_baseline.py → scripts/compare_prompt_versions.py → scripts/report_stage2.py。原始下载、元数据、失败记录和模型响应均保留。"]
    (ROOT / "reports/STAGE2_STATUS.zh-CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    body, table = [], False
    for line in lines:
        if line.startswith("|---"):
            continue
        if line.startswith("|"):
            if not table:
                body.append("<table>")
                table = True
                cell = "th"
            else:
                cell = "td"
            body.append("<tr>" + "".join(f"<{cell}>{html.escape(v.strip())}</{cell}>" for v in line.strip("|").split("|")) + "</tr>")
            continue
        if table:
            body.append("</table>")
            table = False
        if line.startswith("# "):
            body.append("<h1>" + html.escape(line[2:]) + "</h1>")
        elif line.startswith("## "):
            body.append("<h2>" + html.escape(line[3:]) + "</h2>")
        elif line:
            body.append("<p>" + html.escape(line) + "</p>")
    if table:
        body.append("</table>")
    document = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第二阶段进度</title><style>body{margin:0;background:#f5f7f6;color:#202825;font:16px/1.8 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:980px;margin:40px auto;padding:28px;background:white;border-top:7px solid #254C45}h1,h2{color:#254C45;line-height:1.4}h2{margin-top:36px}table{width:100%;border-collapse:collapse;font-size:14px}th{background:#254C45;color:white;text-align:left}td,th{padding:9px;border-bottom:1px solid #dae2df}p{overflow-wrap:anywhere}@media(max-width:650px){main{margin:0;padding:18px}h1{font-size:26px}table{font-size:12px}}</style><main>' + "\n".join(body) + "</main></html>"
    (ROOT / "reports/stage2.html").write_text(document, encoding="utf-8")
    print("reports/stage2.html")


if __name__ == "__main__":
    main()
