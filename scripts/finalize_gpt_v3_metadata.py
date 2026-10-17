"""Publish local pointers and honest scope notes for the final GPT-core artifacts."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write(p,s):q=ROOT/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s,encoding='utf-8')
def js(p,s):write(p,json.dumps(s,ensure_ascii=False,indent=2)+'\n')
current={'version':'gpt_core_v3_final','status':'All five stages complete; see FINAL_QA for verification boundaries','research_cutoff':'2026-10-16','delivered_date':'2026-10-17',
 'report':'output/report/Consumer_Sentiment_Research_GPT_v3.pdf','report_pages':12,'report_source':'reports/final_gpt_v3/RESEARCH_REPORT.en.md',
 'presentation':'output/presentation/Consumer_Sentiment_Findings_GPT_v3_Page9_Fixed.pptx','presentation_slides':10,'timed_slides':10,'appendix_slides':0,
 'script':'reports/final_gpt_v3/SPEAKER_SCRIPT.en.md','script_configuration':'configs/presentation_gpt_core_v3.json','main_script_words':943,'suggested_script_seconds':445,'script_language':'English only','timing_boundary':'Estimated, not a live rehearsal',
 'dashboard':'reports/dashboard.html','submission':'output/submission/Consumer_Sentiment_GPT_v3_Submission.zip',
 'analysis':'reports/gpt_core_v3/analysis.json','measurement_review':'reports/gpt_core_v3/validation.json','human_validation':False,'primary_coding':'All 1473 direct GPT judgments; exact immutable model versions not retained','review_coding':'Cached DeepSeek V4 sample review, 150 news and 150 X attempted','new_paid_API_calls':0,'older_outputs':'Historical files are retained; use only the paths in this manifest for the current submission.'}
js('reports/CURRENT_DELIVERABLES.json',current)
js('reports/ACTIVE_RESEARCH.json',{'status':'Stages 1–5 complete','version':'gpt_core_v3_final','current_deliverables':'reports/CURRENT_DELIVERABLES.json','analysis':current['analysis'],'validation':current['measurement_review'],'verification':'reports/final_gpt_v3/FINAL_QA.json','primary_labels':'data/private/gpt_core_v3/GPT_primary.jsonl','new_paid_API_calls':0})
write('README.md','''# Media narratives and consumer sentiment

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
''')
write('SUBMISSION_GUIDE.zh-CN.md','''# 当前提交说明 — GPT core v3

请使用 `reports/CURRENT_DELIVERABLES.json` 中的路径。文件名包含 GPT_v3；旧 Six_Research_Questions 文件和旧 Consumer_Sentiment_Submission.zip 均是历史版。

## 内容对应

报告 1 页摘要；2 页 Michigan 指数；3 页 RQ1；4 页 RQ2；5–6 页 RQ3；7 页 RQ4；8 页 RQ5；9 页 RQ6；10 页方法和编码审计；11 页后续设计及金融研究用途；12 页来源与复现。

PPT 1 页引入；2 页指数；3 页 RQ1；4 页 RQ2；5–6 页 RQ3；7 页 RQ4；8 页 RQ5；9 页 RQ6；10 页 Key Takeaways。十页均有英文讲稿，943 词，建议约 7 分半。稿子不需要朗读来源备注，也不需要朗读公式的每个符号。未做真人计时排练。

## 解压后复现

在解压的 Consumer_Sentiment_GPT_v3_Submission 目录运行 README 中的三条验证/重建命令。复现脚本先核对 SHA256SUMS.json，再重算 82 月媒体聚合、200 月宏观起点信息、40 月媒体模型、44 月全宏观预测、15 个模型规格、6 组敏感性及样本一致性。输出 `reproduced/verification.json`。

只复现既有标签的统计计算。原文、引句、理由、API 响应、密钥、`.env.local` 不分享。公开输入元数据与评分记录的原始哈希可互相核对，但没有原文就不能独立重算那个原始哈希。原始封存与最小化导出分别有哈希，不能混用。一次重复项排除是冻结结果，不是公开重提取。

## 需要如实表述的研究边界

- GPT 直接主编码；DeepSeek V4 只复核样本；没有人工金标准。课程原本的人审要求未履行，已在方法页明确。
- 300 条审查是 150 新闻 + 150 X，不是 300 新闻；293 对有效，65.2% tone agreement。
- 多次 GPT 编码会话，不能声称单一精确模型版本。FinBERT/RoBERTa 没有运行。
- 标题和窄时间窗口的方便样本，不等于整体报道或用户实际曝光。
- 无媒体因果效应、心理机制参数、最终竞选周结果；后续实验是建议，未执行。
- 描述性 OLS、40 月媒体预测和 44 月宏观预测是三个不同实验，不能混报。

本次没有新增调用或费用。分享包只写入本机，没有上传、发布或发送给第三方。
''')
write('reports/PROJECT_STATUS.zh-CN.md','''# 项目状态（2026-10-17）

五个阶段已完成：1 全量 GPT 主编码与封存；2 重算研究和稳健性；3 六问叙事及新图；4 十二页报告、十页 PPT 和逐页英文稿；5 仪表盘、复现和提交包。

当前版本入口 `CURRENT_DELIVERABLES.json`。过去的阶段交接与 Flash 文件是历史记录。没有新增数据或付费 API 调用。实际演讲时长未排练，原生 PowerPoint 未实机打开；这两项不属于已完成的实机验证。
''')
write('reports/PRESENTATION_STYLE.zh-CN.md','''# 当前演讲风格

参考用户提供的 Reinforcement_Learning_Speaker_Script_Refined.docx，仅学习语言表达，不移用其内容。最新要求优先：自然短句、单语英文、用词与画面一致，直接分享发现与证据，不强行写每页过渡，不在前页结尾和后页开头重复。

当前配置 `configs/presentation_gpt_core_v3.json`；讲稿 `reports/final_gpt_v3/SPEAKER_SCRIPT.en.md`；943 词，估计 7–8 分钟。购物账单仅是引入与回扣，不冒充访谈资料。六个 RQ 在标题中明确，最后一页 Key Takeaways。模型方法留在报告，仅解释会改变结论的限制。
''')
alignment=['引入：购物账单与六问，回扣仅在最后。','指数：五个问题与公式，对应当前/预期分组。','RQ1：先情绪化，再政治归因，再负面语气；图中三项同序。','RQ2：August actual、economy、media、persistence 四个数一一对应。','RQ3：趋势、44.9 下降、16.7 关联量、28.3→7.1 残差。','RQ3：上图价格水平、下图通胀，27.9%、3.7%、0.5% 一致。','RQ4：四种机制与图中四个 proxy 对应；topic salience 等术语统一。','RQ5：三组基线配对，MAE 与媒体增量、persistence 及 all features 对应。','RQ6：覆盖门槛和增量符号一致；说明月份构成也改变。','Key Takeaways：三条发现与采购力/最近情绪预测用途，无附录。']
write('reports/SLIDE_SCRIPT_ALIGNMENT.zh-CN.md','# 当前十页逐页核对\n\n'+'\n'.join(f'{i}. {t}' for i,t in enumerate(alignment,1))+'\n\n同一配置生成英文稿与备注；每页相邻起止句已人工阅读，无强制翻页衔接语。图表数值按显示精度与冻结结果一致。来源是非口述备注。\n')
codebook=ROOT/'labels/CODEBOOK.md';old=codebook.read_text(encoding='utf-8');old=old.replace('## Current six-question revision: cross_family_v2','## Historical six-question revision: cross_family_v2')
if '## Current primary coding: gpt_core_v3' not in old:
 write('labels/CODEBOOK.md','# Economic narrative coding\n\n## Current primary coding: gpt_core_v3\n\n全体 1,473 条主编码为 GPT 直接判断，协议见 data/shareable/gpt_core_v3/protocol.json。300 条旧 GPT 样本复用，另 1,173 条新直接判断；后者分 540 和 633 条两次会话。精确不可变模型版本未保留。五条封存前修正有日志；封存后没有按研究结果修改标签。\n\nDeepSeek V4 只作为既有 300 条样本复核，不进入主语料打分。没有人工金标准；一致率不是准确率。主分析使用全部 GPT 判断，不再使用旧 Flash 主评分。下面段落只记录历史工作流，不定义当前交付。\n\n'+old.split('\n',1)[1])
js('reports/final_gpt_v3/STAGE_COMPLETION.json',{'completed':[1,2,3,4,5],'deliverables':current,'research_limitations_preserved':True,'data_collection_or_spending_this_revision':False})
print('Current deliverable pointers and documentation updated.')
