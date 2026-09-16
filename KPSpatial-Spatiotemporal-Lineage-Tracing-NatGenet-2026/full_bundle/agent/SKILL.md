---
name: kpspatial-evidence-guide
description: Read the KPSpatial 2026 evidence guide, locate source-backed methods and bounded code audits, and separate paper facts from transfer hypotheses.
---

# KPSpatial 证据入口

先读根目录 README.md 与 audit/delivery_scope.json。根据问题只加载相关 docs 章节及其来源；不要一次加载全部参数与历史状态。

事实来源映射见 sources_catalog.json；具体代码位置见 CODE_LOCATORS.md；参数有来源分级，不能把 inherited/default 值当作论文最终运行参数。

作者函数的局部行为已在合成输入测试；原论文分析没有端到端执行。不得把 audit 检查通过、原 notebook 保存输出、结构验证通过或当前仓库提交当作论文复现完成。

社区算法转到 docs/05；谱系、fitness、plasticity 转到 docs/04；实现缺陷转到 docs/06、07；统计/因果转到 docs/08；转移转到 docs/09；分期 Xenium 迁移转到 docs/11。全局证据缺口见 docs/01、12。

任何继续执行需按实际输入、权限和现有工具进行。此知识库不引入后台任务、独立恢复状态机或额外审批流程，不自动访问 GitHub 或修改仓库。优先保留原始证据，再在副本执行局部检查。
