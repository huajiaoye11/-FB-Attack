# datasets/ 数据目录说明

## 目录整体用途

`datasets/` 目录存放 DSSE 泄露滥用攻击项目所需的已处理数据集，包括 Enron 和 Lucene 两个邮件数据集的按月分片数据、关键词字典、以及 Google Trends 关键词热度数据。各攻击模块（FMA、LVIA）在运行时会读取此目录中的 `.pkl` 文件。

**注意：** 此目录中的文件由 `preprocess/` 脚本生成，不建议手动修改或移动。

---

## 子目录说明

### 1. `enron-full/` — Enron 按月分片文档数据

| 属性 | 说明 |
|---|---|
| 文件数量 | 48 个 `.pkl` 文件 |
| 时间范围 | 1999 年 1 月 ~ 2002 年 12 月（共 4 年） |
| 命名规则 | `{YYYY}_{M}.pkl`，月份不补零。示例：`1999_1.pkl`, `2001_10.pkl` |
| 内部结构 | `tuple` 长度 3：`(documents, dates, lengths)` |
| `documents` | `list[list[str]]`，每个内层列表是一篇文档中的词干集合 |
| `dates` | `list`，每条文档的日期信息 |
| `lengths` | `list[int]`，每条文档的原始字节大小 |
| 生成脚本 | `preprocess/process_dataset.py` 或 `preprocess/pro_data_alt.py` 中的按月保存函数 |
| 被读取方 | `FMA/process_dict.py`（`get_size_frompkl`、`delete_get_size_frompkl`）、`LVIA/LVIA.py` |

### 2. `enron-full_dict/` — Enron 关键词字典（按月）

| 属性 | 说明 |
|---|---|
| 文件数量 | 48 个 `.pkl` 文件 |
| 时间范围 | 1999 年 1 月 ~ 2002 年 12 月 |
| 命名规则 | `{YYYY}{M}.pkl`，无下划线、月份不补零。示例：`19991.pkl`, `200110.pkl` |
| 内部结构 | `dict[str, dict]`：`{keyword: {"size": int, "length": [int, ...]}}` |
| `size` | 该关键词在该月的出现次数 |
| `length` | 包含该关键词的所有文档的大小列表 |
| 生成脚本 | 推测由旧版数据预处理脚本生成（输出路径中包含 `_dict/` 的代码位于 `process_dict.py` 的注释中） |
| 被读取方 | **当前无任何代码直接读取此目录**。仅在 `FMA/process_dict.py` 的注释代码中有旧引用 |

### 3. `lucene/` — Lucene 按月分片文档数据

| 属性 | 说明 |
|---|---|
| 文件数量 | 132 个 `.pkl` 文件 |
| 时间范围 | 2002 年 1 月 ~ 2012 年 12 月（共 11 年） |
| 命名规则 | `{YYYY}_{M}.pkl`，与 `enron-full/` 一致。示例：`2002_1.pkl`, `2012_12.pkl` |
| 内部结构 | 与 `enron-full/` 相同：`tuple` 长度 3 → `(documents, dates, lengths)` |
| 被读取方 | `FMA/process_dict.py`、`LVIA/LVIA.py` |

### 4. `lucene_dict/` — Lucene 关键词字典（按月）

| 属性 | 说明 |
|---|---|
| 文件数量 | 132 个 `.pkl` 文件 |
| 时间范围 | 2002 年 1 月 ~ 2012 年 12 月 |
| 命名规则 | `{YYYY}{M}.pkl`，与 `enron-full_dict/` 一致。示例：`20021.pkl`, `201212.pkl` |
| 内部结构 | 与 `enron-full_dict/` 相同：`dict[str, dict]` |
| 被读取方 | **当前无任何代码直接读取此目录** |

### 5. `trends/` — Google Trends 关键词热度数据

| 属性 | 说明 |
|---|---|
| 文件数量 | 10 个 `.pkl` 文件 |
| 命名规则 | `{dataset}_trends_{nkw}.pkl`，其中 `dataset` 为 `enron-full` 或 `lucene`，`nkw` 为关键词数量 |
| nkw 取值 | `100`, `500`, `1000`, `2000`, `3000`（两个数据集各 5 个） |
| 内部结构 | `tuple` 长度 2：`(keyword_list, trends_matrix)` |
| `keyword_list` | `list[str]`，长度为 `nkw`，按频率从高到低排序的词干列表 |
| `trends_matrix` | `np.ndarray`，shape `(nkw, 72)`，dtype `float64`。72 列对应 6 年 × 12 个月（2015-01 ~ 2020-12）的 Google Trends 归一化热度值 |
| 生成脚本 | `preprocess/pro_data_alt.py` → `select_top_nkw_and_save()` |
| 被读取方 | `FMA/enron.py`、`FMA/lucene.py`、`FMA/process_dict.py`、`LVIA/LVIA.py` 中的 `load_stem_trends()` 函数 |

---

## 根目录散文件说明

以下文件直接位于 `datasets/` 根目录，未归入子目录：

| 文件名 | 内部结构 | 说明 |
|---|---|---|
| `enron-full.pkl` | `tuple`：`(docs_list, stems_list, aux_dict)` | Enron 全量预处理结果（30032 条文档 × 3000 个词干） |
| `enron-full_stems_to_words.pkl` | `dict`：`{stem: [word, ...]}`（3000 条） | Enron 词干到原始单词的映射 |
| `enron-fullstems_trends.pkl` | `tuple`：`(stems_dict, trends_dict)` | Enron 词干趋势数据。**注意：文件名 `full` 和 `stems` 之间缺少 `_` 分隔符** |
| `enron-full_sorted_stems_trends.pkl` | `tuple`：`(sorted_stems_list, trends_ndarray)` shape `(3000, 72)` | 按频率排序后的 Enron 词干趋势 |
| `lucene_stems_to_words.pkl` | `dict`（同 Enron） | Lucene 词干到原始单词的映射 |
| `lucenestems_trends.pkl` | `tuple`（同 Enron） | Lucene 词干趋势数据。**注意：文件名 `lucene` 和 `stems` 之间缺少 `_` 分隔符** |
| `lucene_sorted_stems_trends.pkl` | `tuple`：`(sorted_stems_list, trends_ndarray)` | 按频率排序后的 Lucene 词干趋势 |
| `trends.pkl` | `dict`（14198 条） | Google Trends 原始数据，由 `preprocess/process_dataset.py` 生成 |
| `trends_1.pkl` | `dict`（24487 条） | Google Trends 原始数据补充，由 `preprocess/pro_data_alt.py` 生成 |

---

## 数据命名规则汇总

| 目录 | 格式 | 月份补零 | 有无下划线 | 示例 |
|---|---|---|---|---|
| `enron-full/` | `YYYY_M.pkl` | ❌ | 有 | `1999_1.pkl` |
| `enron-full_dict/` | `YYYYM.pkl` | ❌ | 无 | `19991.pkl` |
| `lucene/` | `YYYY_M.pkl` | ❌ | 有 | `2002_1.pkl` |
| `lucene_dict/` | `YYYYM.pkl` | ❌ | 无 | `20021.pkl` |
| `trends/` | `{dataset}_trends_{nkw}.pkl` | 不适用 | 有 | `enron-full_trends_500.pkl` |

---

## 模块依赖关系

| 模块 | 读取的 `datasets/` 子目录/文件 | 路径方式 |
|---|---|---|
| `FMA/enron.py` | `datasets/enron-full/`, `datasets/trends/` | `__file__`-based（已修复） |
| `FMA/lucene.py` | `datasets/lucene/`, `datasets/trends/` | `__file__`-based（已修复） |
| `FMA/process_dict.py` | `datasets/enron-full/`, `datasets/lucene/`, `datasets/trends/` | `__file__`-based（已修复） |
| `LVIA/LVIA.py` | `datasets/enron-full/`, `datasets/lucene/`, `datasets/trends/` | 混合（部分 `__file__`，部分相对路径） |
| `LVIA/LVIA_with_fusion_output.py` | 同上 | 同上 |
| `PVIA_Enron/` 各脚本 | **不读取 `datasets/`**，使用自身 `edb/` 和 `partial/` 的 JSON 数据 | 相对路径 |
| `PVIA_Lucene/` 各脚本 | **不读取 `datasets/`**，使用自身 `edb/` 和 `partial/` 的 JSON 数据 | 相对路径 |
| `preprocess/` | 写入到 `datasets_mon/` 和 `datasets_mon_alter/`（**不是** `datasets/`） | 相对路径 |
| `fusion/` | 不读取 `datasets/`，从 `fusion/input/` 读取 | `__file__`-based（已修复） |

---

## 已知问题

1. **命名风格不统一**：`enron-full/` 和 `lucene/` 使用 `YYYY_M.pkl`，而 `_dict/` 使用 `YYYYM.pkl`（无下划线），同一月份在两种目录下文件名不同。
2. **月份不补零**：`1999_1.pkl` 而非 `1999_01.pkl`，在按文件名排序时会导致 `1999_10` 排在 `1999_2` 之前。
3. **`*_dict/` 目录未被使用**：`enron-full_dict/` 和 `lucene_dict/` 共 180 个 `.pkl` 文件，当前无代码读取。
4. **根目录散文件命名不规范**：`enron-fullstems_trends.pkl` 和 `lucenestems_trends.pkl` 缺少 `_` 分隔符。`trends.pkl` 和 `trends_1.pkl` 无法从文件名区分内容。
5. **根目录散文件未归类**：9 个 `.pkl` 散文件与子目录平级，结构不够清晰。
6. **LVIA 路径未完全修复**：部分仍使用相对路径 `"../datasets/"`。
7. **缺少 `enron-full.pkl` 的使用说明**：不清楚哪些模块需要这个全量文件。

---

## 后续改进建议

| 阶段 | 内容 | 风险 |
|---|---|---|
| 第一阶段 | 补充本文档，说明数据结构和依赖关系 | 无 |
| 第二阶段 | 新增数据完整性校验脚本（检查文件数量、月份连续性、文件可读性） | 低 |
| 第三阶段 | 统一各模块中 `datasets/` 路径获取方式为 `__file__`-based | 中（只改代码） |
| 第四阶段 | 考虑统一命名（补零、统一 `_dict/` 格式）、清理未使用目录、归类散文件 | 高（需同步改代码和数据） |

---

## 注意事项

- **不建议手动修改、重命名、移动或删除 `datasets/` 中的任何 `.pkl` 文件**，否则可能导致 FMA、LVIA 等模块无法正常运行。
- 如需优化数据结构或清理未使用文件，建议先完成代码路径的统一修复和校验脚本的编写，再逐步进行。
- Enron 数据时间范围为 1999-01 ~ 2002-12（48 个月），Lucene 为 2002-01 ~ 2012-12（132 个月）。如果运行脚本提示缺少某月份文件，请先检查预处理流程是否完整执行。
