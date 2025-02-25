
## 项目简介

本项目旨在通过爬取和分析小红书、微博、抖音三大平台关于哈尔滨冰雪大世界的相关数据，深入了解其自媒体营销策略效果。通过数据分析，我们可以洞察用户行为、内容表现和营销效果。

## 功能特性

1. 多平台数据爬取
   - 小红书：笔记内容、点赞数、收藏数、评论数
   - 微博：博文内容、转发数、评论数、点赞数
   - 抖音：视频数据、点赞数、评论数、收藏数

2. 数据分析功能
   - 互动数据统计分析
   - 热门内容主题分析
   - 用户情感分析
   - 营销效果评估

## 项目结构

```
project/
├── scrapers/
│   ├── xiaohongshu_scraper.py   # 小红书爬虫
│   ├── weibo_scraper.py         # 微博爬虫
│   └── douyin_scraper.py        # 抖音爬虫
├── analysis/
│   ├── data_processor.py        # 数据处理
│   └── data_analyzer.py         # 数据分析
├── utils/
│   ├── database.py             # 数据库操作
│   └── helpers.py              # 辅助函数
├── data/                       # 存储爬取的数据
├── results/                    # 存储分析结果
└── requirements.txt            # 项目依赖
```

## 技术栈

Python 3.8+
数据爬取：requests, selenium, fake_useragent
数据处理：pandas, numpy
数据分析：matplotlib, seaborn
文本分析：jieba, snownlp
数据存储：Excel, CSV
微博爬虫说明
项目提供了两个版本的微博爬虫：
基础版微博爬虫 (weibo_scraper.py)
默认爬取最多10页数据
适合快速测试和小规模数据采集
简单的错误处理
完整版微博爬虫 (weibo_scraper_full.py)
支持爬取全部可用数据，不限页数
智能终止机制：通过多种方式检测爬取终点
增强的错误处理和重试机制（最多5次重试）
定期保存中间数据，防止长时间爬取中断导致数据丢失
反爬增强：随机User-Agent、智能延迟策略
更详细的日志记录，便于监控爬取过程
同时保存Excel和CSV格式，便于后续处理

# 微博爬虫说明

项目提供了两个版本的微博爬虫：
基础版微博爬虫 (weibo_scraper.py)
默认爬取最多10页数据
适合快速测试和小规模数据采集
简单的错误处理
完整版微博爬虫 (weibo_scraper_full.py)
支持爬取全部可用数据，不限页数
智能终止机制：通过多种方式检测爬取终点
增强的错误处理和重试机制（最多5次重试）
定期保存中间数据，防止长时间爬取中断导致数据丢失
反爬增强：随机User-Agent、智能延迟策略
更详细的日志记录，便于监控爬取过程
同时保存Excel和CSV格式，便于后续处理

## 使用说明

1. 安装依赖：

```bash
pip install -r requirements.txt
```

# 网络请求和爬虫相关

requests>=2.28.1
selenium>=4.8.0
fake-useragent>=1.1.1
beautifulsoup4>=4.11.1
lxml>=4.9.2
webdriver-manager>=3.8.5

# 数据处理和分析

pandas>=1.5.3
numpy>=1.23.5
openpyxl>=3.1.0  # Excel支持
matplotlib>=3.7.0
seaborn>=0.12.2
scikit-learn>=1.2.1  # 机器学习支持

# 文本处理

jieba>=0.42.1
snownlp>=0.12.3
wordcloud>=1.8.2.2  # 词云生成

# 日期时间处理

python-dateutil>=2.8.2

# 辅助工具

tqdm>=4.64.1  # 进度条
colorama>=0.4.6  # 终端彩色输出
pyyaml>=6.0  # 配置文件处理

2. 运行爬虫：

```bash
python main.py --platform all  # 爬取所有平台
python main.py --platform xiaohongshu  # 只爬取小红书
```

3. 数据分析：

```bash
python analyze.py
```

## 注意事项

- 请遵守各平台的爬虫规范和速率限制
- 建议使用代理IP池避免被封禁
- 定期更新 User-Agent
