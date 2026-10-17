# Media narratives and consumer sentiment

Victor Chen · FRE-GY 7871 · Instructor: Dr. Daniel Rodriguez

研究讨论媒体内容、累计价格压力与美国消费者情绪，围绕六个研究问题展开。姓名、课程、老师和项目 GitHub 链接仅显示在报告与 PPT 的第一页。

## 当前文件

所有主要交付物都在 `output/`：

| 文件 | 内容 |
|---|---|
| [report.pdf](output/report.pdf) | 12 页正式报告 |
| [slides.pptx](output/slides.pptx) | 10 页演示文稿，已保留第 9 页修复 |
| [speaker_notes.md](output/speaker_notes.md) | 纯英文讲稿，与 PPT 备注一致，约 7 分半 |
| [dashboard.html](output/dashboard.html) | 下载后用浏览器打开，离线筛选和导出 |
| [submission.zip](output/submission.zip) | 完整交付和离线复现包 |

报告的 Markdown 源文档为 [reports/report.md](reports/report.md)。当前路径清单为 `reports/CURRENT_DELIVERABLES.json`。旧版文件留在本地归档，不再作为 GitHub 当前交付入口。

## 研究发现

主语料共 1,473 条直接 GPT 判断，其中 230 条新闻和 829 条 X 内容符合主分析条件。DeepSeek V4 仅作既有样本复核；没有人工金标准。精确不可变 GPT 版本未保留。研究截止 2026-10-16，媒体至 7 月，情绪评价至 8 月。

X 的情绪化表达更多。累计价格压力将描述性残差从 28.25 缩至 7.08 点。媒体的预测增益取决于基线和覆盖规则，严格覆盖检查会反转结果。未识别媒体因果效应或个体心理机制。研究版本号保留在数据和审计记录中，以维护可追溯性。

## 离线复现

```powershell
python -m pip install -r requirements.txt
python scripts/reproduce_submission.py
python -m unittest discover -s tests
python scripts/build_dashboard.py
```

从 1,005 份公共宏观快照和最小化标签重算统计结果，不需要密钥或网络，不重新执行私人文本提取或 AI 推理。解压 `submission.zip` 后，在 `submission` 目录运行相同命令。

## 构建与检查

- 报告：`python scripts/build_report.py`，可选依赖在 `requirements-artifacts.txt`。
- PPT：`scripts/build_slides.mjs`，使用 Codex 内置 Artifact Tool；已有输出须以新文件名验证再替换，避免覆盖原稿。
- 检查交付：`python scripts/check_deliverables.py`。
- 检查仪表盘逻辑：`node scripts/check_dashboard.mjs`。
- 打包：`python scripts/package_submission.py`。
- 干净解压复验：`python scripts/verify_submission_package.py`。

PPT 保留 8 个可编辑图表及内嵌数据表。报告和 PPT 已渲染检查；未做原生 PowerPoint 实机核验。仪表盘验证为本地逻辑检查。讲稿时长为估计。密钥和私有原文不进入分享包。报告主题色为 #254C45。
