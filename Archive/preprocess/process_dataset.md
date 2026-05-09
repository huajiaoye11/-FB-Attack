我来为你详细解释这个文件的代码结构和功能。

📋 文件概述
这是一个数据集预处理脚本，用于为可搜索对称加密(Searchable Symmetric Encryption, SSE)的攻击研究准备数据。主要处理Enron邮件数据集和Lucene邮件存档数据集。

🔍 主要功能模块
1. 数据预处理核心函数
    preprocess_raw_dataset()	
    从原始压缩文件(tar.gz)中提取邮件，转换为文本，提取关键词

    process_pre_dataset()	
    对提取的关键词进行词干提取(stemming)、停用词移除、频率过滤

    extract_words_from_original_dataset()	
    从原始邮件文本中提取单词(仅保留字母，转小写)

2. 数据分组与保存
save_enron_data_bymonth()    # 按年月分组保存Enron数据
save_lucene_data_bymonth()   # 按年月分组保存Lucene数据
load_data_bymonth()          # 加载按月份分组的数据
3. 邮件处理
process_email_enron()  # 提取Enron邮件内容和日期
process_email()        # 提取普通邮件内容(移除退订信息)
4. Google Trends集成
get_keyword_trends()      # 从Google Trends获取关键词热度数据
get_frequencies_from_google_trends() # 批量获取并保存关键词热度
add_frequency_trends_information_to_dataset() # 将热度数据添加到数据集

🔄 主流程(工作流程)
原始邮件数据(tar.gz)
        ↓
preprocess_raw_dataset() ← 提取邮件、转换日期
        ↓
基础预处理数据集(关键词列表)
        ↓
process_pre_dataset() ← 词干提取、停用词移除、选择高频词
        ↓
最终处理数据集(选定的3000个高频词)
        ↓
按年月分组保存 + Google Trends热度

📊 数据转换过程

1.关键词提取

使用正则表达式提取单词
转小写，移除非字母字符
2.词干提取(Stemming)

使用Porter词干提取器
移除停用词(如"the", "a"等)
保留长度2-20字符的单词
3.频率过滤

选择高频出现的3000个词(top keywords)
移除空文档(不含任何关键词的邮件)
4.日期/大小元数据

保留邮件日期用于时间序列分析
保留原始邮件大小信息

📁 输出数据结构
# 保存的pickle文件包含元组:
(
    dataset,              # 二维列表:每个文档对应的词ID列表
    chosen_stems,         # 3000个选定词干
    {
        'stems_to_words': {},  # 词干→原始单词映射
        'trends': array        # Google Trends热度矩阵
    }
)

⚙️ 关键参数

nkw=3000: 选择3000个最高频关键词
timeframe: Google Trends数据时间范围(2020全年)
enron: 1999-2002年数据
lucene: 2002-2012年数据
这个脚本为论文中的前向/后向隐私泄漏滥用攻击(leakage-abuse attacks)研究提供数据基础。

