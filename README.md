# 🧭 科技趋势可视化日报系统 (Tech Trend Dashboard)

这是一个面向程序员的“信息减压型”科技趋势仪表盘。它每天自动从高质量源（arXiv、GitHub、科技博客、Hacker News）抓取信息，对其进行主题归类、一句话摘要和智能打分。最终通过 Streamlit 提供一个直观、干净的交互式可视化界面。

**目标**：帮您在 30 秒内获得技术方向感，而不是被海量新闻标题淹没。

---

## 🚀 特性

- **自动抓取**: 自动拉取 arXiv、GitHub 热榜、官方 AI 博客和 Hacker News。
- **智能打分**: 综合计算 **重要性 (Importance)**、**新鲜度 (Novelty)** 和 **温度/趋势 (Momentum)**。
- **直观概览**: “Today” 页面提供今日最高优方向横向条形图及速览卡片。
- **趋势分析**: “Trend” 页面展示 7/14/30 天的热度折线图与来源热力图。
- **探索发现**: “Explore” 页面通过新型散点气泡图帮您发掘高价值/高新鲜度内容。

---

## 🛠️ 技术栈

- **语言**: Python 3.11+
- **后端/数据处理**: `requests`, `feedparser`, `pandas`, `sqlite3`
- **前端/可视化**: `streamlit`, `plotly`
- **辅助库**: `pydantic` (数据建模), `loguru` (日志), `python-dotenv` (环境变量配置)

---

## 📦 快速安装与启动

### 1. 克隆代码并安装依赖

```bash
git clone <your-repo-url>
cd tech_trend_dashboard

# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 用户使用 venv\Scripts\activate

pip install -r requirements.txt
```

### 2. 环境配置

复制演示配置文件并根据需要修改：
```bash
cp .env.example .env
```
*(推荐配置 `GITHUB_TOKEN` 以提高 GitHub API 速率限制。)*

### 3. 初始化数据库

这将会创建 `data/tech_trends.db` SQLite 数据库及相关表。
```bash
python scripts/init_db.py
```

### 4. 获取数据

**选项 A：拉取真实数据**
```bash
# 抓取过去 1 天的数据并进行聚合
python scripts/run_pipeline.py --days 1
```

**选项 B：回填演示数据 (Demo)**
如果处于 API 受限网络环境，运行此命令填充测试数据，以便立刻查看 UI 效果：
```bash
python scripts/backfill_demo_data.py
```

### 5. 启动仪表盘

```bash
streamlit run app.py
```
这会在浏览器中自动打开 `http://localhost:8501`。

---

## ⏱️ 定时任务配置

要实现"每天自动更新"，你有两种方案：

### 方案 1: GitHub Actions (推荐云端部署)
本项目已内置 `.github/workflows/daily_pipeline.yml`。它会在每天 UTC 1:00 自动执行 pipeline。你可以在该文件中取消注释 Git 提交步骤，将数据存入代码库（或其他持久化存储）。

### 方案 2: 本地 Cron Job (Linux / Mac)
运行 `crontab -e` 并添加：
```bash
# 每天早上 8:00 执行抓取 pipeline
0 8 * * * cd /path/to/tech_trend_dashboard && /path/to/venv/bin/python scripts/run_pipeline.py --days 1 >> logs/cron.log 2>&1
```

*(Windows 用户可使用“任务计划程序”指向该 Python 脚本)*

---

## 📁 目录结构

```
tech_trend_dashboard/
├── app.py                      # Streamlit 入口
├── requirements.txt            # 依赖项
├── .env.example                # 环境变量示例
├── .github/workflows/          # GitHub Actions 配置
├── data/                       # 默认的 SQLite 数据存储位置
├── pages/                      # Streamlit 多页面
│   ├── 1_Today.py
│   ├── 2_Trend.py
│   └── 3_Explore.py
├── scripts/                    # 各种实用执行脚本
│   ├── init_db.py
│   ├── run_pipeline.py
│   └── backfill_demo_data.py
├── src/                        # 核心逻辑
│   ├── config.py               # 全部常量的集中地
│   ├── models.py               # Pydantic 数据模型
│   ├── database.py             # SQLite 封装
│   ├── classifier.py           # 主题分类器
│   ├── summarizer.py           # 摘要提取器
│   ├── scoring.py              # 打分逻辑
│   ├── aggregator.py           # 数据聚合器
│   ├── pipeline.py             # 核心工作流
│   └── utils.py                # 日志、解析等杂项
└── tests/                      # 单元测试与集成测试
```

---

## 🔮 后续扩展建议

1. **LLM 赋能**: 用大语言模型替换 `classifier.py` 和 `summarizer.py` 中的基于规则的处理，利用 LLM 进行更精准的聚类与一句话提炼。
2. **更多源**: 增加 Reddit (r/MachineLearning)、X/Twitter 知名技术博主的精选列表等。
3. **数据库升级**: 数据量增大后，可无缝迁移至 PostgreSQL，由于结构清晰，只需调整 `database.py`。
