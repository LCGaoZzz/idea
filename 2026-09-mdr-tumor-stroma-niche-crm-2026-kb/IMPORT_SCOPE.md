# 入库范围与保全说明

## 完整保存的对象

本次上传对象是此前交付的 `MDR_CellReportsMedicine_code_evidence_20260917.zip`，不是论文所有数据或作者完整分析环境。原 ZIP 大小 **70,143 bytes**，SHA-256：

`18974d1fbeeb0eaef1ab5357349bcde47042da4e4013e5ffda7f46fbabb70550`

归档容器改为 `archives/MDR_CellReportsMedicine_complete_evidence_20260917.tar.xz`，大小 **37,408 bytes**，SHA-256：

`5776e22a68766255b9739f02bfa633bf662304afafe279ba554816f4480fecea`

**原交付的 23 个文件全部保留，共 303,116 个未压缩文件字节；内部路径及各文件字节逐一与原 ZIP 比较一致。** 未保留 ZIP 自身的容器字节、压缩参数及时间戳等归档元数据；因此这是无损内容重打包，不是原 ZIP 的二进制副本。没有删减原包日志、大型 manifest、HTML 或测试文件。

完整成员列表和 SHA-256 见 [complete_bundle_manifest.json](integrity/complete_bundle_manifest.json)。在线直接展开的是 5 个逐字节一致的阅读/证据镜像；其余成员在完整归档内。新增 README、AGENTS、knowledge_index、入库清单和完整性脚本仅用于导航与保全，不属于作者分析实现。

## 保留而不升级的科学边界

原包没有取得论文正文、STAR Methods、原图图注、补充材料、患者级信息或受控数据矩阵；没有运行作者 R 工作流。A01–A12 的论文重建保持受阻。原创合成语义检查和结构验证不等于论文结果验证。

作者的 9 个源码文件字节与输入协议源包本来就不在默认交付 ZIP 中；本次完整入库不会凭空补齐它们。原始 acquisition、repository audit、reconstruction manifest 中对这些外部材料的引用属于此前证据记录；要重新运行相应验证，需依据固定来源与哈希恢复所需外部文件。不能为让验证通过而删除缺口、改写状态或把最新 main 当作原快照。

## 与仓库规范的对齐

采用现有月份—主题—期刊—知识库命名方式；归入空间组学/TME 分类并同步根目录 README、CATALOG、catalog.json。保留所有旧目录与链接，不重排其他项目。文章标题、原文入口、固定代码版本和 Figure 1 获取状态写入本目录 README；未获取原图时不猜测图片 URL。

本次校验只确认文件集合、字节与导航结构；不重新评定论文科学质量或完成新的生物学分析。
