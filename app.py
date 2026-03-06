"""
app.py - Streamlit 入口点
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="科技趋势可视化日报",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧭 科技趋势可视化日报系统")

st.markdown("""
### 欢迎使用信息减压型科技趋势仪表盘

本系统旨在帮助您快速获得技术方向感，而不是被大量信息淹没。
系统每天自动打分聚合：

- 👈 请在左侧侧边栏选择页面：
  - **Today (今日科技罗盘)**：30 秒看懂今天最重要的 3 件事。
  - **Trend (趋势分析)**：观察各个方向最近 7-30 天的冷热变化。
  - **Explore (探索数据)**：按来源和重要性浏览过滤原始数据。

> *提示：如果当前没有任何数据，请运行 `scripts/run_pipeline.py` 进行抓取，或运行 `scripts/backfill_demo_data.py` 生成演示数据。*
""")

st.sidebar.success("请在上方选择页面。")
