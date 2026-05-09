# FB-Attack 项目整理会话记录

> 导出时间: 2026-05-09 | 项目: DSSE 泄露滥用攻击 (CCS 2023)

---

## 1. 项目初始整理

### 1.1 项目结构分析

项目基于 CCS 2023 论文 *"Leakage-Abuse Attacks Against Forward and Backward Private Searchable Symmetric Encryption"*，实现三种 DSSE 查询恢复攻击（FMA/LVIA/PVIA）及融合模块。

原始目录结构：

```text
FB-Attack-copy/
├── preprocess/          # 数据预处理
├── FMA/                 # 频率匹配攻击
├── LVIA/                # 长度-体积信息攻击
├── PVIA_Enron/          # 部分体积信息攻击-Enron
├── PVIA_Lucene/         # 部分体积信息攻击-Lucene
├── fusion/              # 融合模块
├── fusion - 副本/       # 重复目录
├── datasets/            # 已处理数据集
└── README.md
```

识别的主要问题：

| 问题 | 详情 |
|---|---|
| `_backup.py` 命名混乱 | 实际是增强版（含fusion输出），不是备份 |
| `fusion - 副本/` 完全重复 | 与 `fusion/` 内容相同，代码版本略旧 |
| `FMA/results(1)/` 重复 | 与 `FMA/results/` 内容相同 |
| PVIA 参数脚本高度重复 | 仅 `word_size` 不同，其余代码完全一致 |
| 三个相同 `utils.py` | `preprocess/`、`PVIA_Enron/`、`PVIA_Lucene/` 中内容相同 |
| 非代码文件散落 | `LVIA/Untitled.md`、`preprocess/*.md`、`fusion/PVIA.txt` 等 |
| 缺少 `requirements.txt` | 依赖未文档化 |

### 1.2 全局整理执行

| 操作 | 详情 |
|---|---|
| 直接删除 | `fusion - 副本/` |
| 目录重命名 | `FMA/results(1)/` → `FMA/results/`（旧 `results/` 先删除） |
| 文件重命名 | `*_backup.py` → `*_with_fusion_output.py`（3个） |
| 归档 | `LVIA/Untitled.md`、`preprocess/*.md`、`fusion/PVIA.txt`、`PVIA_Enron/test.py`、`PVIA_Lucene/test/` |
| 新增 | `requirements.txt`（numpy, pandas, nltk, pytrends, gtab, tqdm） |
| 更新 | `README.md`（英文版） |

**明确禁止处理的内容：**
- `datasets/` 中任何文件
- PVIA 参数脚本合并
- FMA 脚本合并
- 预处理脚本合并
- `utils.py` 合并
- `__init__.py` 新增/删除/修改

---

## 2. FMA 模块处理记录

### 2.1 处理目标

将 `FMA/enron.py`（原版）和 `FMA/enron_with_fusion_output.py`（增强版）合并为单一主脚本，同时为 `FMA/lucene.py` 补充 `.txt` 输出能力。

### 2.2 路径修复

| 文件 | 修复内容 |
|---|---|
| `FMA/enron.py` | 全部路径改为 `__file__`-based（`BASE_DIR`/`PROJECT_ROOT`/`RESULTS_DIR`/`FUSION_INPUT_DIR`/`DATASETS_DIR`） |
| `FMA/lucene.py` | 同上 |
| `FMA/process_dict.py` | 新增 `DATASETS_DIR`，修复三处路径拼接（`load_stem_trends`、`get_size_frompkl`、`delete_get_size_frompkl`） |

真实数据集路径确认：
- `datasets/enron-full/1999_1.pkl`（子目录结构，`dataset_name/YYYY_M.pkl`）
- `datasets/trends/enron-full_trends_500.pkl`（扁平结构）

### 2.3 Enron 脚本合并

**合并后的 `FMA/enron.py` 功能：**

| 输出类型 | 详情 |
|---|---|
| `.txt` 结果 | `FMA/results/enron_delete_20.txt`，格式严格匹配已有文件 |
| Fusion JSON | `fusion/input/fma_candidates_nkw{val}_query{val}_month{val}_del{val}.json` |

**Fusion JSON 参数化命名规则：**
- 文件名不含 `enron`
- 每组参数独立文件，互不覆盖
- 格式：`fma_candidates_nkw{N}_query{Q}_month{M}_del{D}.json`
- 示例：`fma_candidates_nkw500_query5000_month6_del20.json`

**保持不变的参数：**
- `nkw_list = [500, 1000, 2000, 3000]`
- `query_list = [5000, 10000, 15000, 20000]`
- `query_month = [6, 12, 18, 24]`
- `delete_rate = 0.2`（固定单值）

### 2.4 Lucene 脚本增强

**`FMA/lucene.py` 修改：**
- 路径修复
- 新增 `.txt` 输出到 `FMA/results/lucene_delete_00.txt`
- **不**输出 fusion JSON（无 `import json`、无 `FUSION_INPUT_DIR`）
- 保持 `delete_rate = 0.00`、Jaccard 阈值 `0.6`、起始年月 `2007/1`

### 2.5 已有 Fusion JSON 重命名

根据 `enron_with_fusion_output.py` 原参数（nkw=500, query=5000, month=6, delete_rate=0.05）：

| 旧文件名 | 新文件名 |
|---|---|
| `fma_candidates.json` | `fma_candidates_nkw500_query5000_month6_del05.json` |
| `ground_truth.json` | `ground_truth_nkw500_query5000_month6_del05.json` |

### 2.6 旧脚本归档

`FMA/enron_with_fusion_output.py` → `Archive/FMA/enron_with_fusion_output.py`

### 2.7 `fusion/weighted_fusion.py` 注释更新

- `load_json()` 函数添加 docstring，说明参数化文件命名
- `main()` 函数上方添加注释，说明需要手动复制/重命名参数文件
- 未修改读取逻辑、融合算法、权重或输出格式

---

## 3. README 中文化

将 `README.md` 从英文改写为中文，保留所有信息。主要章节：

1. 论文引用
2. 目录结构（中文注释，路径英文）
3. 各模块说明（预处理、FMA、LVIA、PVIA、Fusion）
4. 安装依赖
5. 使用方式（预处理、各攻击模块、融合模块）
6. 注意事项（11条）
7. 数据集来源
8. 免责声明

修正错别字：候选举果 → 候选结果

---

## 4. datasets/ 分析记录

### 4.1 目录结构

| 目录 | 文件数 | 时间范围 | 命名规则 | 内部结构 |
|---|---|---|---|---|
| `enron-full/` | 48 | 1999-01~2002-12 | `{YYYY}_{M}.pkl` | `tuple(docs_list, dates_list, lengths_list)` |
| `enron-full_dict/` | 48 | 同上 | `{YYYY}{M}.pkl` | `dict{keyword: {size, length}}` |
| `lucene/` | 132 | 2002-01~2012-12 | `{YYYY}_{M}.pkl` | 同 enron-full |
| `lucene_dict/` | 132 | 同上 | `{YYYY}{M}.pkl` | 同 enron-full_dict |
| `trends/` | 10 | — | `{dataset}_trends_{nkw}.pkl` | `tuple(stems_list, ndarray(nkw,72))` |

### 4.2 .pkl 抽样结构

| 样本文件 | 结构 |
|---|---|
| `enron-full/2000_1.pkl` | `tuple` 长度3：`list[list[str]]`（1108条文档）、`list`（日期）、`list[int]`（大小） |
| `enron-full_dict/20011.pkl` | `dict` 3000个key，`{keyword: {"size": int, "length": [int]}}` |
| `trends/enron-full_trends_500.pkl` | `tuple` 长度2：`list[str]`（500词干）、`ndarray(500,72)` float64 |

### 4.3 代码依赖关系

| 模块 | 读取路径 | 路径方式 |
|---|---|---|
| `FMA/enron.py` | `datasets/enron-full/`, `datasets/trends/` | `__file__`-based ✅ |
| `FMA/lucene.py` | `datasets/lucene/`, `datasets/trends/` | `__file__`-based ✅ |
| `LVIA/LVIA.py` | 同上 | 混合（部分 `__file__`，部分 `"../datasets/"`）⚠️ |
| `PVIA_Enron/*` | **不读取 `datasets/`**，使用 `edb/` 和 `partial/` JSON | 相对路径 ⚠️ |
| `PVIA_Lucene/*` | 同上 | 相对路径 ⚠️ |
| `preprocess/*` | 写入到 `datasets_mon/`、`datasets_mon_alter/`（**不是 `datasets/`**） | 相对路径 ⚠️ |

### 4.4 已知问题

1. 命名不统一：`enron-full/` 用 `YYYY_M.pkl`，`_dict/` 用 `YYYYM.pkl`
2. 月份不补零：`1999_10` < `1999_2`（字符串排序）
3. `*_dict/` 目录（180文件）无代码读取
4. 根目录散文件命名不规范（`enron-fullstems_trends.pkl` 缺分隔符）
5. LVIA 路径未完全修复

### 4.5 改进方案（四阶段）

| 阶段 | 内容 | 风险 |
|---|---|---|
| 1 | 补充说明文档 | 无 |
| 2 | 新增数据完整性校验脚本 | 低 |
| 3 | 统一路径配置为 `__file__`-based | 中（仅代码） |
| 4 | 重命名数据文件、统一命名 | 高 |

### 4.6 已执行

新增 `datasets/README.md` 数据说明文档（148行）。

---

## 5. PVIA 模块处理记录

### 5.1 差异分析

**PVIA_Enron：**

| 文件 | 行数 | 差异 |
|---|---|---|
| `enron_partial_500.py` | 131 | 仅最后一行 `word_size=500` |
| `enron_partial_1000.py` | 130 | `word_size=1000` |
| `enron_partial_2000.py` | 131 | `word_size=2000` |
| `enron_partial_3000.py` | 131 | `word_size=3000` |
| `enron_partial_5000.py` | 244 | **结构明显不同**（倒排索引优化、增强解码、`main()` 函数） |

**PVIA_Lucene：**

| 文件 | 行数 | 差异 |
|---|---|---|
| `lucene_partial_{500,1000,2000,3000}.py` | 137 | 仅最后一行 `word_size` 不同 |

### 5.2 已有结果格式

```
0.9 0.9 containing unique result 495
0.9 0.8 containing unique result 483
...
```

- 每组一行：`{frac1} {frac2} containing unique result {count}`
- tqdm 进度条为控制台输出，不作为稳定写入格式
- 文件名：`enron_{word_size}.txt` / `lucene_{word_size}.txt`

### 5.3 合并决策

| 决策 | 说明 |
|---|---|
| 合并基础 | 1000 版本（**不使用** 5000 版的优化重构） |
| 参数方式 | 顶部 `WORD_SIZE = 1000` 配置变量 |
| Enron 支持 | `[500, 1000, 2000, 3000, 5000]` |
| Lucene 支持 | `[500, 1000, 2000, 3000]` |
| Fusion 脚本 | **不处理** `enron_partial_1000_with_fusion_output.py` |

### 5.4 新增文件

| 文件 | 说明 |
|---|---|
| `PVIA_Enron/enron_partial.py` | Enron 统一脚本，`WORD_SIZE=1000`，`__file__` 路径，`.txt` 输出 |
| `PVIA_Lucene/lucene_partial.py` | Lucene 统一脚本，`WORD_SIZE=1000`，`__file__` 路径，`.txt` 输出 |

### 5.5 归档的旧脚本（9个）

| 原位置 | → 归档位置 |
|---|---|
| `PVIA_Enron/enron_partial_500.py` | `Archive/PVIA_Enron/enron_partial_500.py` |
| `PVIA_Enron/enron_partial_1000.py` | `Archive/PVIA_Enron/enron_partial_1000.py` |
| `PVIA_Enron/enron_partial_2000.py` | `Archive/PVIA_Enron/enron_partial_2000.py` |
| `PVIA_Enron/enron_partial_3000.py` | `Archive/PVIA_Enron/enron_partial_3000.py` |
| `PVIA_Enron/enron_partial_5000.py` | `Archive/PVIA_Enron/enron_partial_5000.py` |
| `PVIA_Lucene/lucene_partial_500.py` | `Archive/PVIA_Lucene/lucene_partial_500.py` |
| `PVIA_Lucene/lucene_partial_1000.py` | `Archive/PVIA_Lucene/lucene_partial_1000.py` |
| `PVIA_Lucene/lucene_partial_2000.py` | `Archive/PVIA_Lucene/lucene_partial_2000.py` |
| `PVIA_Lucene/lucene_partial_3000.py` | `Archive/PVIA_Lucene/lucene_partial_3000.py` |

### 5.6 保留原位的文件

- `PVIA_Enron/enron_partial_1000_with_fusion_output.py`（未处理）
- `PVIA_Enron/utils.py`
- `PVIA_Lucene/utils.py`

---

## 6. 已完成操作总表

### 6.1 已修改文件

| 文件 | 修改内容 |
|---|---|
| `FMA/enron.py` | 合并版 Enron 主脚本（txt + 参数化 fusion JSON） |
| `FMA/lucene.py` | Lucene 主脚本（txt only） |
| `FMA/process_dict.py` | 路径修复（`__file__`-based） |
| `fusion/weighted_fusion.py` | 仅注释更新（load_json docstring + main 上方注释） |
| `README.md` | 中文重写 |

### 6.2 已新增文件

| 文件 | 说明 |
|---|---|
| `requirements.txt` | numpy, pandas, nltk, pytrends, gtab, tqdm |
| `datasets/README.md` | 数据目录完整说明文档 |
| `PVIA_Enron/enron_partial.py` | Enron PVIA 统一脚本 |
| `PVIA_Lucene/lucene_partial.py` | Lucene PVIA 统一脚本 |

### 6.3 已重命名

| 旧名 | → 新名 |
|---|---|
| `FMA/results(1)/` | `FMA/results/` |
| `LVIA/LVIA_backup.py` | `LVIA/LVIA_with_fusion_output.py` |
| `PVIA_Enron/enron_partial_1000_backup.py` | `PVIA_Enron/enron_partial_1000_with_fusion_output.py` |
| `fusion/input/fma_candidates.json` | `fma_candidates_nkw500_query5000_month6_del05.json` |
| `fusion/input/ground_truth.json` | `ground_truth_nkw500_query5000_month6_del05.json` |

### 6.4 已归档文件

| 归档位置 | 说明 |
|---|---|
| `Archive/LVIA/Untitled.md` | AI 分析笔记 |
| `Archive/preprocess/pro_data_alt.md` | AI 文档 |
| `Archive/preprocess/process_dataset.md` | AI 文档 |
| `Archive/fusion/PVIA.txt` | 控制台日志 |
| `Archive/PVIA_Enron/test.py` | 测试片段 |
| `Archive/PVIA_Lucene/test/` | 测试目录 |
| `Archive/FMA/enron_with_fusion_output.py` | 已合并的旧 FMA 脚本 |
| `Archive/PVIA_Enron/enron_partial_{500,1000,2000,3000,5000}.py` | 旧 PVIA 参数脚本（5个） |
| `Archive/PVIA_Lucene/lucene_partial_{500,1000,2000,3000}.py` | 旧 PVIA 参数脚本（4个） |

### 6.5 已删除

| 路径 | 原因 |
|---|---|
| `fusion - 副本/` | 完全重复，直接删除 |
| `FMA/results/`（旧版） | 被 `results(1)/` 重命名替换 |

---

## 7. 当前项目状态

```
FB-Attack-copy/
├── README.md                          (中文版)
├── requirements.txt                   (新增)
├── .gitignore
│
├── preprocess/
│   ├── config.py
│   ├── process_dataset.py
│   ├── pro_data_alt.py
│   └── utils.py
│
├── FMA/
│   ├── enron.py                       (合并版：txt + fusion JSON)
│   ├── lucene.py                      (txt only)
│   ├── process_dict.py                (路径已修复)
│   └── results/
│
├── LVIA/
│   ├── LVIA.py
│   └── LVIA_with_fusion_output.py
│
├── PVIA_Enron/
│   ├── enron_partial.py               (新增统一脚本)
│   ├── enron_partial_1000_with_fusion_output.py
│   ├── utils.py
│   ├── edb/
│   ├── partial/
│   └── results/
│
├── PVIA_Lucene/
│   ├── lucene_partial.py              (新增统一脚本)
│   ├── utils.py
│   ├── edb/
│   ├── partial/
│   └── results/
│
├── fusion/
│   ├── weighted_fusion.py             (注释已更新)
│   ├── evaluate_modules.py
│   ├── check_ground_truth.py
│   ├── input/
│   └── output/
│
├── datasets/
│   ├── README.md                      (新增数据说明)
│   ├── enron-full/
│   ├── enron-full_dict/
│   ├── lucene/
│   ├── lucene_dict/
│   └── trends/
│
├── Archive/
│   ├── FMA/
│   │   └── enron_with_fusion_output.py
│   ├── LVIA/
│   │   └── Untitled.md
│   ├── PVIA_Enron/
│   │   ├── enron_partial_{500,1000,2000,3000,5000}.py
│   │   └── test.py
│   ├── PVIA_Lucene/
│   │   ├── lucene_partial_{500,1000,2000,3000}.py
│   │   └── test/
│   ├── fusion/
│   │   └── PVIA.txt
│   └── preprocess/
│       ├── pro_data_alt.md
│       └── process_dataset.md
│
└── conversation_export/               (本次新增)
    ├── project_cleanup_conversation.json
    ├── project_cleanup_conversation.txt
    └── project_cleanup_conversation.md
```

---

## 8. 后续待处理事项

| # | 事项 | 优先级 | 风险 |
|---|---|---|---|
| 1 | LVIA 路径修复 | 高 | 中 |
| 2 | PVIA 路径修复 | 高 | 中 |
| 3 | `utils.py` 去重 | 中 | 中 |
| 4 | `datasets/_dict/` 评估与归档 | 中 | 低 |
| 5 | `datasets/` 命名统一 | 低 | 高 |
| 6 | `datasets/` 散文件归档 | 低 | 中 |
| 7 | FMA `enron.py`/`lucene.py` 合并评估 | 低 | 中 |
| 8 | PVIA fusion 脚本后续处理 | 低 | 中 |
| 9 | `preprocess/` 脚本合并评估 | 低 | 中 |
| 10 | `fusion/weighted_fusion.py` 参数化文件支持 | 低 | 中 |
| 11 | 新增数据完整性校验脚本 | 中 | 低 |
| 12 | `__init__.py` 按需新增 | 低 | 无 |

---

## 9. 明确禁止处理的内容（汇总）

以下内容在本次会话中经用户明确禁止处理：

- `datasets/` 中任何 `.pkl` 数据文件（不修改、不移动、不重命名、不删除）
- FMA `enron.py` 和 `lucene.py` 合并为单一脚本
- `preprocess/process_dataset.py` 和 `pro_data_alt.py` 合并
- `preprocess/utils.py`、`PVIA_Enron/utils.py`、`PVIA_Lucene/utils.py` 去重合并
- `__init__.py` 文件的新增、删除或修改
- `fusion/weighted_fusion.py` 核心逻辑（仅允许注释）
- PVIA `enron_partial_1000_with_fusion_output.py` 的修改或归档
- PVIA 合并引入 `enron_partial_5000.py` 的重构优化
- 执行完整耗时实验运行
- 删除任何文件（`fusion - 副本/` 和旧 `FMA/results/` 除外）
