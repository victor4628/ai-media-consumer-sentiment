# Media narratives and consumer sentiment

当前版本 **gpt_core_v3_final，五个阶段已完成**。唯一当前文件清单为 `reports/CURRENT_DELIVERABLES.json`。旧 Flash 报告、PPT、讲稿和旧 ZIP 保留为历史文件，不用于本次提交。

- 报告：`output/report/Consumer_Sentiment_Research_GPT_v3.pdf`，12 页，按六个研究问题组织。
- PPT：`output/presentation/Consumer_Sentiment_Findings_GPT_v3_Page9_Fixed.pptx`，10 页主讲，末页 Key Takeaways，无附录。
- 纯英文讲稿：`reports/final_gpt_v3/SPEAKER_SCRIPT.en.md`，943 词；同一文本已写入逐页备注。
- 离线仪表盘：`reports/dashboard.html`，模型、日期和平台筛选，本地 SVG 图表及 CSV 导出。
- 当前分享包：`output/submission/Consumer_Sentiment_GPT_v3_Submission.zip`。

主语料共 1,473 条直接 GPT 判断，符合美国经济分析条件的新闻 230 条、X 829 条。DeepSeek V4 只作既有 300 条样本复核（150 新闻 / 150 X），293 对有效；不是人工验证，不是准确率。精确不可变 GPT 版本未保留。研究截止 2026-10-16；媒体至 7 月，情绪评价至 8 月。

核心发现：X 的情绪化语言较多；累计价格压力将描述性残差从 28.25 缩至 7.08 点；有历史情绪的基线加入媒体后几乎不变，加入季节/调查方式控制后有改善，但严格覆盖检查反转。不能识别媒体因果效应或个体心理机制。

## Offline reproduction

```powershell
python -m pip install -r requirements.txt
python scripts/reproduce_submission.py
python -m unittest discover -s tests
python scripts/build_dashboard.py
```

从 1,005 份公共宏观快照和最小化标签重算 15 个模型、6 组稳健性检查；不需要密钥或网络。复现不包含私人文本提取、AI 推理或新的独立复核。重复项排除使用冻结 ID。完整说明见 `SUBMISSION_GUIDE.zh-CN.md`。

可选报告重建使用 `python scripts/build_gpt_v3_report.py` 和 `requirements-artifacts.txt`。PPT 源码 `scripts/build_gpt_v3_deck.mjs` 依赖 Codex 的 Artifact Tool 与演示技能运行时；这不是公共统计复现的依赖。图表为可编辑原生 PowerPoint 图表，底层展示值保留六位小数，统计 CSV 保留完整精度。

报告、PPT 已逐页渲染检查；未在原生 PowerPoint 实机打开。仪表盘验证为本地 JavaScript/DOM 逻辑与 SVG 输出检查，不宣称浏览器实机布局检查。演讲预计约 7 分半，实际语速需排练。本次修订无新增付费 API 请求。主题色 #254C45。
