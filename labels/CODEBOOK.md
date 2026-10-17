# Economic narrative coding

## Current primary coding: gpt_core_v3

全体 1,473 条主编码为 GPT 直接判断，协议见 data/shareable/gpt_core_v3/protocol.json。300 条旧 GPT 样本复用，另 1,173 条新直接判断；后者分 540 和 633 条两次会话。精确不可变模型版本未保留。五条封存前修正有日志；封存后没有按研究结果修改标签。

DeepSeek V4 只作为既有 300 条样本复核，不进入主语料打分。没有人工金标准；一致率不是准确率。主分析使用全部 GPT 判断，不再使用旧 Flash 主评分。下面段落只记录历史工作流，不定义当前交付。


## Historical six-question revision: cross_family_v2

正式 300 条复核改为 **DeepSeek V4 Pro + 当前 Codex 对话中的 GPT**。V4 使用同一批原始输入的既有独立 B 缓存；GPT 逐条阅读并给出九个分类维度、逐字引句与简短理由。GPT 的 300 条结果在逐条 V4 比较前封存；工具只展开显式简码、验证结构与引句，不通过规则/词典代替 GPT 决策。没有人工标注。

样本保持 150 条新闻、150 条推文；100 条开发与 200 条保留身份不变。V4 293 条有效，GPT 300 条有效；保留部分有效配对 196 条，语气一致率 63.8%，kappa 0.522。该一致率不是准确率，不将分歧强制合并为真值。旧 C 投票仅作历史记录。完整配置见 `configs/verification_v2.json`，结果见 `reports/cross_family_validation.json`。

独立性有限：当前会话此前见过项目汇总和少量示例，不能称为前瞻完全隔离的盲实验。精确不可变 GPT 版本不可见；私有记录保存当前助手身份、封存时间与哈希。主回归仍用冻结的完整 Flash 编码，不选择性地用新复核替换部分月份。以下 v1 工作流段落保留为历史，不是当前审计声明。

## Historical v1 workflow

执行方式：DeepSeek 独立调用交叉检查，无真人金标准。A 为 Flash 主编码；B 为 Pro 独立复核；C 为 Pro 的独立复查。模型家族相关偏差仍然存在，C 也不是金标准。实际模型与计价配置位于 configs/deepseek.json。

## 文本单位

每条记录必须有 id、text、published_at（含时区）、platform 和 source。新闻标题、正文和推文分别保存 text_type；当前新闻试采仅为标题。地理相关性表示文本是否讨论美国经济，不表示作者是美国居民。

重复文本按归一化内容或已有 story_group 处理。近重复、转载故事仍需按正式语料特征进一步聚类；现有精确去重不声称覆盖全部语义重复。

## 维度

| 维度 | 规则 |
|---|---|
| tone | negative / neutral / positive / mixed / uncertain；坏的事实可以是负面语气，但不等于偏见 |
| language_style | factual / emotional / mixed / uncertain，描述用词而不是验证事实真伪 |
| topics | prices / employment / wages / growth / housing / household_finances / other，多选 |
| price_frame | levels / changes / both / neither / uncertain |
| scope_frame | household / national / both / neither / uncertain |
| time_frame | current / future / both / neither / uncertain |
| factual_calibration | matches / conflicts / not_checkable / no_numeric_claim；缺少已发布官方证据时只能不可核查 |
| political_attribution | credit / blame / both / none / uncertain，不推断个人党派 |
| us_relevance | yes / no / uncertain；英文不等于美国相关 |

每条输出提供原文中的 1–3 个证据片段及简短理由。不要求隐藏思维链。引用必须在 HTML 实体解码后是输入的逐字子串（例如 &amp; 与 & 显示等价），不允许近义替换。JSON 与标签值均由代码校验。官方证据日期必须早于文本发表日；同日资料需更精细的时点核实，目前保守拒绝。

接口试验中发现模型可能返回过长解释或引句。只对展示文本作确定性截短：理由最多 400 字符；先验证整个引句确实存在于输入，再截为 160 字符。记录 format_adjustments，原始响应完整保存在私有缓存中。类别标签保持原值，不用本地格式整理更改任何判断。无法通过校验的引句仍拒绝。若本地整理后仍有 JSON/标签/证据格式问题，可在费用预留允许时进行最多一次模型修复请求，另存修复提示词、原始响应和费用，并标记 one_schema_repair_call；修复仍失败则停止，不能默默丢弃文本。网络失败不自动重试。

## 样本与验证

`prepare-audit` 仅在真实语料足够时输出 300 条（100 开发、200 冻结审计）；不使用合成记录凑数。按来源、平台、月份轮转抽样，每个故事组最多一条。该抽样用于检查测量，不是估计自然报道占比的分母，也不保证每平台恰好 150 条。

A/B 分别调用相同输入，不共享标签。使用 `compare-labels` 计算仲裁前一致率、kappa、标签交叉表、来源分组语气一致性。`review-queue` 导出全部分歧及约 10% 一致项，C 只看到原始文本与允许的官方证据。C 的独立结果保留为复核材料；最终逐维仲裁合并、扰动批次和全量月度媒体指标尚待真实试采与验证后完成，不能宣称已完成。

无真人标签，因此不报告真实 precision、recall、F1 或准确率。相同标签不证明事实正确。`uncertain` 与 `not_checkable` 是有效结果；分歧不得在统计时默默丢弃。

## 版本与证据

core_v1 执行协议：以 v2 的原始字节及配置 hash 固定本轮核心测量，旧 59 条开发样本故事组退出正式样本。固定 150 条新闻、150 条推文作双模型审计，其中每平台 50 条归开发部分、100 条归保留审计；选择只依赖种子、文本、来源和月份，不依赖标签。核心代码使用每次 6 条的批量 JSON，标签逐条匹配 ID、内容 hash、枚举和引句。一次模型格式修复后仍无效的条目保留 ID、原始响应、错误原因和 label=null；不制造替代标签，月度特征明确统计无效数量，审计报告明确分母与双方有效配对数。

原文引句校验和确定性展示整理不更改类别判断。共享模型家族复核、分歧复查和 ID 遮蔽扰动用于测量质量记录，均不能代替外部真值。主回归统一使用 A，不因审计结果选择性替换一部分月度标签。标题样本不能宣称为全文语料；严格的数值事实核查仍需官方发布证据。

2026-10-16 开发更新：新增 economic_coding_v2.txt，用原 59 条开发文本复测，正式运行仍默认 v1，不能自动将 v2 认作更优版本。价格/范围等维度一致性改善，语气和主题一致性下降；详见 reports/prompt_development.zh-CN.md。v2 独立输出 hash 避免覆盖 v1。

证据文字校验允许一种有记录的恢复：若引句仅大小写不同，且原文中只有唯一的忽略大小写逐字匹配，恢复为原文大小写并标记 literal_excerpt_case_restored_from_source。不得以语义近似或同义改写补造引句；原始模型响应仍完整保留。

缓存保留输入/提示词 hash、请求模型、API 返回模型名称、运行时间、usage 与原始 JSON 响应。配置里的模型别名可能更新；返回别名不保证精确模型权重版本。若 API 未提供不可变版本，应在报告中说明这一复现限制。

每个包含“matches/conflicts”的结果仍需对照指标、时期、单位、季调与数据版本做事实核查。现有校验器只验证证据记录结构与时间，不把模型的判断自动升级为经过代码验证的事实。
