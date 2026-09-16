# 癌症基因型—表型共同演化：研究型知识库

**文章标题：** A single-cell lens into the co-evolution of genotypes and phenotypes in cancer

**文章链接：** [期刊原文](https://www.nature.com/articles/s41568-026-00970-8) · [DOI](https://doi.org/10.1038/s41568-026-00970-8)

**第一张主图（Figure 1）：**

[![论文 Figure 1](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41568-026-00970-8/MediaObjects/41568_2026_970_Fig1_HTML.png)](https://www.nature.com/articles/s41568-026-00970-8/figures/1)

*来源：[Nature Reviews Cancer · Figure 1](https://www.nature.com/articles/s41568-026-00970-8/figures/1)。图片由出版社网站外链展示，版权归原作者及出版方。*

---

**版本：0.9.0｜证据分层版｜核验日期：2026-09-13**

目标文章：Izzo、Prieto、Potenski、Landau，*A single-cell lens into the co-evolution of genotypes and phenotypes in cancer*，Nature Reviews Cancer，2026-09-08，DOI 10.1038/s41568-026-00970-8。[S01]

> **必须先读：本版不是“目标综述全文精读已完成版”。** 本次取得了公开预览、图题、术语表、参考文献及五张低分辨率缩略图，没有取得订阅正文和完整图注。下面的深入方法课件由明确标注的原始研究、固定版本代码审读、独立数学推导与迁移建议构成。绝不把补充文献的细节冒充为综述原文。

## 如何使用

普通阅读：双击 **START_HERE.html**。这是离线单文件阅读器，包含章节、方法卡、来源、全文检索与 Agent 提问提示词；不依赖 CDN，不发送数据。Markdown 位于 `knowledge/`、`methods/`。

Agent 使用：先读 `AGENTS.md` 和 `SKILL.md`，再按需调用 `tools/kb.py`。本库提供本地证据检索、证据包构造和输入能力检查，不捆绑大模型，也不把关键词匹配假装成 LLM。

```bash
python tools/kb.py search "没有突变 reads 能否判定野生型" --json
python tools/kb.py context "PATH 的遗传性是否等于遗传决定性" --limit 5
python tools/kb.py get C032
python tools/kb.py plan --input agent/examples/project_rna_only.json
python tools/kb.py interactive
python tools/kb.py validate
python tools/demo.py
python -m unittest discover -s tests -v
```

Python 核心工具只用标准库，要求 Python 3.10+；本地执行不需要 API key。HTML 已预生成，打开不需要依赖；只有重新生成阅读器时才需要可选的 `markdown-it-py`（见 `requirements-reader.txt` 和 `tools/build_reader.py`）。`tools/tool_server.py` 是 **JSONL stdio 适配器，不是 MCP 服务器**。没有自动注册到任何 Agent 平台；宿主只需转发受支持的工具调用。

## 最值得掌握的主线

不是“找一个更强的聚类方法”，而是分清四个问题：细胞携带什么遗传变化，处于什么表型状态，彼此有何祖先关系，以及哪些动态或机制能由这些观测被识别。只有前三者被恰当地连接，第四者才有可检验的基础。这个表述是本库的教学框架，不是作者原文引语。

先读 `knowledge/01_core_framework.md`，再读测量、时钟、遗传性、动态可识别性和统计设计。最后把自己的数据合同填入 Agent 示例，而不是直接让模型生成一整条看似完整的分析管线。

## 证据层级

| 标签 | 含义 | 不允许的升级 |
|---|---|---|
| REVIEW | 目标综述已公开且核验的有限内容 | 不扩展成未取得的正文细节 |
| PRIMARY | 原始论文已核验摘要或方法片段 | 不自动推广到其他癌种、平台 |
| CODE | 固定提交中真正读到的文件/函数 | 不写成已运行、已复现或论文最终参数 |
| ANALYSIS | 本库独立数学推导与研究逻辑解释 | 不冒充作者定义、方程或因果结论 |
| TRANSFER | 新项目的设计建议、待检验假说 | 不冒充已验证机制或临床方案 |

证据登记：`evidence/sources.json`；原子论断：`evidence/claims.jsonl`；缺口：`evidence/gaps.json`。文中 `[Sxx]` 在离线阅读器中可点到来源记录。完整性清单位于 `audit/SHA256SUMS`。

## 目录导航

`knowledge/`：核心课件；`methods/`：输入—假设—输出—失败模式方法卡；`agent/`：接口合同、问答格式、项目输入实例；`graph/`：概念节点与非因果/假说边；`tools/`：检索和教学程序；`tests/`：工程测试与科学问答评估集；`audit/`：真实运行记录。

不包含出版社全文、原图、受控数据、作者代码副本或任何私人文件。代码与中文课件是本次生成内容，使用边界见 `RIGHTS.md`。本库服务于研究理解与方法设计，不用于个体诊疗决策。
