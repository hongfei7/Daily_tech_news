# Tech Trend Dashboard

这是一个面向程序员的信息减压型科技趋势系统，当前版本已经从“固定 topic + 全局 Top N 摘要”升级为：

- `stable_topic` 保证长期趋势可比性
- `emerging_topic` 捕捉最近 3-7 天的新爆点
- 全量条目全部入库并参与趋势统计
- LLM 只精读“分层抽样后的代表样本”，而不是简单全量 Top N

## 升级目标

系统围绕三层结构工作：

1. `Stable Topics`
   用固定主题支撑 7/14/30 天趋势比较。
2. `Emerging Topics`
   从最近 3-7 天的 tags 和短语里发现突增热点。
3. `Representative LLM Analysis`
   用 `top_pool + stable_pool + emerging_pool` 做代表性抽样，兼顾头部、覆盖面和新爆点。

## Stable Topic 与 Emerging Topic 的区别

- `stable_topic` 是长期固定分类，例如 `AI Agents`、`AI Coding Tools`、`Robotics`。
- `emerging_topic` 是动态发现层，例如 `MCP`、`Browser Agents`、`AI IDE Benchmark`。
- `Other` 不是终点。即使 stable 分类落到 `Other`，条目仍会继续参与 emerging discovery。

## 为什么 LLM 不分析全部

全量数据用于统计广度，但不适合直接全部送入 LLM：

- 成本高，时延高
- 容易被单一赛道霸榜
- 对“今天为什么这些摘要有代表性”解释不清

当前策略会按比例抽样：

- `top_pool`: 保证最高价值新闻不漏
- `stable_pool`: 保证主要 stable topics 都有覆盖
- `emerging_pool`: 保证新爆点进入日报

并记录：

- `llm_selected`
- `selection_bucket`
- `selection_reason`
- `llm_selection_stats`

## 数据库结构

`items` 表新增字段：

- `stable_topic`
- `emerging_topic`
- `tags`
- `llm_selected`
- `selection_bucket`
- `selection_reason`

新增表：

- `emerging_topic_stats`
- `llm_selection_stats`

旧库升级通过 `ALTER TABLE` 自动补列，可重复执行，不会清空原有数据。

## 初始化与迁移

初始化数据库：

```bash
python scripts/init_db.py
```

迁移旧数据库：

```bash
python scripts/migrate_db.py
```

## 运行 Pipeline

运行完整流程：

```bash
python scripts/run_pipeline.py --days 1
```

流程顺序：

1. fetch 全量数据
2. clean / dedupe
3. stable topic 分类
4. tags 提取
5. 打分
6. emerging topic 发现
7. 回填 emerging topic
8. LLM 分层选样
9. 对选中条目做摘要增强
10. stable 聚合
11. emerging 聚合
12. 写入 selection stats

## 启动 Streamlit

```bash
streamlit run app.py
```

如果当前环境不方便访问真实数据源，可以先回填 demo 数据：

```bash
python scripts/backfill_demo_data.py
```

## 页面说明

### Today

- `Stable Topics 主方向图`: 今日主赛道热度
- `Stable Topic 一句话卡片`: 每个稳定主题的今日解释和代表链接
- `Emerging Now`: 最近几天的动态爆点
- `代表性覆盖说明`: 今日总条目、LLM 精读条数、stable/emerging 覆盖数、三类池分布

### Trend

- `Stable Trend`: 7/14/30 天稳定主题趋势
- `Emerging Trend`: 动态热点增长趋势
- `Topic × Source 热力图`: 主题主要来自哪里
- `Rising / Falling`: stable 与 emerging 的升降榜

### Explore

支持按这些维度筛选：

- `stable_topic`
- `emerging_topic`
- `source`
- `llm_selected`
- `date`

也会显示：

- `selection_bucket`
- `selection_reason`

方便追踪为什么某条内容被送入 LLM。

## 如何新增 Stable Topic

1. 修改 [src/config.py](/C:/Users/WuHongFei/Desktop/Daily_tec_news/tech_trend_dashboard/src/config.py) 中的 `TOPICS`
2. 在 [src/classifier.py](/C:/Users/WuHongFei/Desktop/Daily_tec_news/tech_trend_dashboard/src/classifier.py) 的 `TOPIC_RULES` 里补对应规则
3. 重新运行 `python scripts/run_pipeline.py --days 7`

## 如何观察 Other 并提升为新 Stable Topic

1. 在 Explore 页筛选 `stable_topic = Other`
2. 观察高频 `emerging_topic` 和重复 tags
3. 如果某个热点持续多天稳定出现，再把它提升到 `TOPICS + TOPIC_RULES`

## 测试

```bash
pytest
```

当前新增测试覆盖：

- stable topic 一定输出
- emerging discovery 能识别增长关键词
- llm selector 能按三类池选样
- 单一 topic 不会完全垄断结果
- coverage summary 能输出可读说明
