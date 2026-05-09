# 针对前向隐私和后向隐私可搜索对称加密的泄露滥用攻击

本仓库包含论文中提出的动态可搜索对称加密（DSSE）查询恢复攻击的评估代码：

> Lei Xu, Leqian Zheng, Chengzhi Xu, Xingliang Yuan, and Cong Wang. "*Leakage-Abuse Attacks Against Forward and Backward Private Searchable Symmetric Encryption.*" (CCS 2023).

---

## 目录结构

```
├── README.md
├── requirements.txt
├── .gitignore
│
├── preprocess/                         # 数据预处理脚本
│   ├── config.py                       # 路径配置
│   ├── process_dataset.py              # 原始预处理流程
│   ├── pro_data_alt.py                 # 改进版预处理流程
│   └── utils.py                        # 文件大小工具函数
│
├── FMA/                                # 频率匹配攻击 (Frequency Matching Attack)
│   ├── enron.py                        # Enron 数据集 FMA（输出 .txt 和 fusion JSON）
│   ├── lucene.py                       # Lucene 数据集 FMA（仅输出 .txt）
│   ├── process_dict.py                 # 数据集字典辅助函数
│   └── results/                        # FMA 实验结果 (.txt)
│
├── LVIA/                               # 长度-体积信息攻击 (Length-Volume Information Attack)
│   ├── LVIA.py                         # 原始 LVIA 实现
│   ├── LVIA_with_fusion_output.py      # 带 fusion JSON 输出的增强版本
│   └── *.txt                           # LVIA 实验结果
│
├── PVIA_Enron/                         # 部分体积信息攻击 — Enron 数据集
│   ├── enron_partial_500.py            # PVIA（500 个关键词）
│   ├── enron_partial_1000.py           # PVIA（1000 个关键词）
│   ├── enron_partial_1000_with_fusion_output.py  # PVIA（1000 关键词，含 fusion 输出）
│   ├── enron_partial_2000.py           # PVIA（2000 个关键词）
│   ├── enron_partial_3000.py           # PVIA（3000 个关键词）
│   ├── enron_partial_5000.py           # PVIA（5000 个关键词）
│   ├── utils.py                        # 文件大小工具函数
│   ├── edb/                            # EDB 加密数据库 JSON 数据
│   ├── partial/                        # 部分知识 JSON 数据
│   └── results/                        # PVIA 实验结果
│
├── PVIA_Lucene/                        # 部分体积信息攻击 — Lucene 数据集
│   ├── lucene_partial_500.py           # PVIA（500 个关键词）
│   ├── lucene_partial_1000.py          # PVIA（1000 个关键词）
│   ├── lucene_partial_2000.py          # PVIA（2000 个关键词）
│   ├── lucene_partial_3000.py          # PVIA（3000 个关键词）
│   ├── utils.py                        # 文件大小工具函数
│   ├── edb/                            # EDB JSON 数据
│   ├── partial/                        # 部分知识 JSON 数据
│   └── results/                        # PVIA 实验结果
│
├── fusion/                             # 融合模块（结合 FMA + PVIA + LVIA 结果）
│   ├── weighted_fusion.py              # 加权融合主逻辑
│   ├── evaluate_modules.py             # 各模块对比评估脚本
│   ├── check_ground_truth.py           # 数据一致性检查脚本
│   ├── input/                          # 输入候选 JSON 文件
│   └── output/                         # 融合输出结果和指标
│
├── datasets/                           # 已处理的数据集（不建议手动修改）
│   ├── enron-full/                     # Enron 按月分片数据
│   ├── enron-full_dict/                # Enron 关键词字典（按月）
│   ├── lucene/                         # Lucene 按月分片数据
│   ├── lucene_dict/                    # Lucene 关键词字典（按月）
│   ├── trends/                         # Google Trends 数据
│   └── ...                             # 其他处理后数据文件
│
└── Archive/                            # 已归档的非核心文件
    ├── FMA/enron_with_fusion_output.py # 已合并到 enron.py 的旧版脚本
    ├── LVIA/Untitled.md
    ├── preprocess/pro_data_alt.md
    ├── preprocess/process_dataset.md
    ├── fusion/PVIA.txt
    ├── PVIA_Enron/test.py
    └── PVIA_Lucene/test/
```

---

## 各模块说明

### 1. 数据预处理 (`preprocess/`)

从原始 Enron / Lucene 邮件数据集中提取关键词，进行词干提取、停用词移除、高频关键词筛选，并结合 Google Trends 数据作为查询频率先验。

- **`process_dataset.py`**: 原始预处理流程（输出到 `datasets_mon/`）。
- **`pro_data_alt.py`**: 改进版预处理流程（输出到 `datasets_mon_alter/`），时间跨度更长（2015–2020），中间结果保存更加模块化。
- **`config.py`**: 两个预处理流程共用的路径配置。
- **`utils.py`**: 文件大小格式化工具。

### 2. FMA — 频率匹配攻击 (`FMA/`)

利用查询结果体积在按月分片中的分布模式，通过 Jaccard 相似度匹配不同月份的查询类，将查询追踪链关联到真实关键词。

- **`enron.py`**: Enron 数据集的最终主脚本。同时输出：
  - `.txt` 结果文件到 `FMA/results/enron_delete_20.txt`
  - Fusion JSON 文件到 `fusion/input/`，使用参数化文件名，例如 `fma_candidates_nkw500_query5000_month6_del20.json` 和 `ground_truth_nkw500_query5000_month6_del20.json`
- **`lucene.py`**: Lucene 数据集的最终主脚本。仅输出 `.txt` 结果到 `FMA/results/lucene_delete_00.txt`。**不**输出 fusion JSON。
- **`process_dict.py`**: 按月份加载关键词-文件大小字典的辅助函数。
- **`results/`**: 不同删除率下的 FMA 准确率结果。

旧的 `FMA/enron_with_fusion_output.py` 已归档至 `Archive/FMA/enron_with_fusion_output.py`。

### 3. LVIA — 长度-体积信息攻击 (`LVIA/`)

将数据划分为多个时间区间，利用各区间内查询体积分布的差异逐步缩小候选关键词集合，结合贪心消歧算法确定最终映射。

- **`LVIA.py`**: 原始 LVIA 实现。
- **`LVIA_with_fusion_output.py`**: 增强版本，额外输出候选分数到 `fusion/input/lvia_candidates.json`。
- **`*.txt`**: 不同参数组合下的实验结果（alpha、threshold、known 条件等）。

### 4. PVIA — 部分体积信息攻击 (`PVIA_Enron/`, `PVIA_Lucene/`)

将数据集分为已知集和攻击目标集，利用 EDB 文件与部分知识文件之间的体积重叠度寻找候选关键词匹配。

各 PVIA 脚本变体（如 `_500.py`、`_1000.py`）对应不同的 `word_size` 参数（选取的 top 关键词数量）。这些变体当前保持独立文件，后续将统一整理。

- **`enron_partial_1000_with_fusion_output.py`**: 增强版本，输出候选分数到 `fusion/input/pvia_candidates.json`。

### 5. 融合模块 (`fusion/`)

将 FMA、PVIA、LVIA 三个攻击模块的候选结果按权重（FMA=0.4, PVIA=0.3, LVIA=0.3）进行加权融合，归一化后通过贪心冲突仲裁得到最终查询-关键词映射。

- **`weighted_fusion.py`**: 加权融合主逻辑，从 `input/` 读取，输出到 `output/`。
- **`evaluate_modules.py`**: 对比各模块及融合后的准确率。
- **`check_ground_truth.py`**: 检查候选文件与 ground truth 的一致性。

**Fusion 输入文件命名说明：** 新版 `FMA/enron.py` 输出参数化 JSON 文件名（如 `fma_candidates_nkw500_query5000_month6_del20.json`），不再输出固定默认名称。已有的默认 `fma_candidates.json` 和 `ground_truth.json`（由旧脚本生成）已按原参数重命名。当前 `weighted_fusion.py` 仍然读取固定默认文件名；在运行 fusion 之前，需要将所选参数文件复制或重命名为默认名称。后续可单独改造 fusion 模块以支持直接选择参数化文件。

---

## 安装依赖

```bash
pip install -r requirements.txt
```

此外，NLTK 需要下载停用词和分词数据：

```python
import nltk
nltk.download('stopwords')
nltk.download('punkt')
```

---

## 使用方式

> 说明：大部分脚本假定处理后数据集已存在于 `datasets/` 目录下。如有需要，请先运行预处理脚本。

### 数据预处理

```bash
# 原始预处理流程（输出到 datasets_mon/）
cd preprocess
python process_dataset.py

# 改进版预处理流程（输出到 datasets_mon_alter/）
python pro_data_alt.py
```

### 运行各攻击模块

```bash
# FMA — Enron（同时输出 .txt 和 fusion JSON）
cd FMA
python enron.py

# FMA — Lucene（仅输出 .txt）
python lucene.py

# LVIA（原始版本）
cd LVIA
python LVIA.py

# LVIA（含 fusion JSON 输出的增强版本）
python LVIA_with_fusion_output.py

# PVIA — Enron（例如 1000 关键词，含 fusion 输出）
cd PVIA_Enron
python enron_partial_1000_with_fusion_output.py

# PVIA — Lucene（例如 500 关键词）
cd PVIA_Lucene
python lucene_partial_500.py
```

### 运行融合模块

先运行 FMA、PVIA、LVIA 攻击。FMA 的 `enron.py` 会将参数化 JSON 文件输出到 `fusion/input/`。由于 `weighted_fusion.py` 当前读取固定的默认文件名（`fma_candidates.json`、`ground_truth.json`），在运行前需将所选参数文件复制为默认名称：

```bash
# 示例：选取 nkw=500, query=5000, month=6, del=20 的 FMA 结果
cd fusion/input
cp fma_candidates_nkw500_query5000_month6_del20.json fma_candidates.json
cp ground_truth_nkw500_query5000_month6_del20.json ground_truth.json

# 运行融合
cd ..
python weighted_fusion.py
python evaluate_modules.py
```

结果写入 `fusion/output/`。

---

## 注意事项

1. **FMA 模块合并**：`FMA/enron.py` 已将原始 FMA 实验逻辑、`.txt` 结果输出和 fusion JSON 输出（参数化文件名）合并为一个脚本。旧的 `FMA/enron_with_fusion_output.py` 已归档至 `Archive/FMA/`。

2. **FMA fusion JSON 命名规则**：`enron.py` 输出参数化 fusion JSON 文件名，格式为 `fma_candidates_nkw{值}_query{值}_month{值}_del{值}.json`，每组参数独立保存、不会互相覆盖。文件名中不包含 `enron` 数据集名称。`fusion/input/` 中已有默认名称的 JSON 文件已按原参数重命名。

3. **Fusion 兼容性**：`fusion/weighted_fusion.py` 当前仍读取固定默认文件名。运行 fusion 前，请先将目标参数化 JSON 文件复制或重命名为默认名称。具体步骤见上文"运行融合模块"。

4. **`*_backup.py` 重命名**：LVIA 和 PVIA 中原来的 `*_backup.py` 文件已重命名为 `*_with_fusion_output.py`，以更准确表达其为带 fusion JSON 输出的增强版本。原始版本同时保留。

5. **`datasets/` 目录**：存放所有预处理后的 `.pkl` 和趋势数据文件。脚本依赖特定的文件命名约定，不建议手动修改。

6. **PVIA 参数变体**：`enron_partial_{500,1000,2000,3000,5000}.py` 和 `lucene_partial_{500,1000,2000,3000}.py` 仅在 `word_size` 参数上有所区别。当前保持独立文件，后续将统一整理。

7. **FMA 未合并数据集**：`enron.py` 和 `lucene.py` 保持为两个独立脚本，未合并为单一统一脚本。

8. **预处理脚本未合并**：`process_dataset.py` 和 `pro_data_alt.py` 保持独立，各自对应不同的输出路径。

9. **`utils.py` 未去重**：`preprocess/utils.py`、`PVIA_Enron/utils.py`、`PVIA_Lucene/utils.py` 内容相同，为避免破坏各模块的本地 import，暂未合并。

10. **未处理 `__init__.py`**：未新增、删除或修改任何 `__init__.py` 文件。

11. **`Archive/` 目录**：非核心文件（AI 生成文档、测试片段、控制台日志）和已合并的旧脚本已移至 `Archive/`，保留原目录结构。运行攻击无需这些文件。

---

## 数据集来源

### Enron
原始 Enron 数据集为 `enron_mail_20150507.tar.gz`，下载自 https://www.cs.cmu.edu/~enron/。

### Lucene
用户邮件帖子，下载自 http://mail-archives.apache.org/mod_mbox/lucene-java-user。

---

## 免责声明

本代码为研究原型，未针对工程化或生产环境做优化。
